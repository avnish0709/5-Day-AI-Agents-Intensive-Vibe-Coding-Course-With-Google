import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load API key / environment variables
load_dotenv()

# Set otel_to_cloud=False to comply with developer checklist
os.environ["OTEL_TO_CLOUD"] = "False"

from expense_agent.agent import root_agent

async def generate_traces():
    dataset_path = Path("tests/eval/datasets/basic-dataset.json")
    output_path = Path("artifacts/traces/generated_traces.json")
    
    print(f"Loading evaluation dataset from {dataset_path}...")
    with open(dataset_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
        
    app = App(name="expense_app", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    
    eval_cases = []
    
    for idx, case in enumerate(scenarios):
        scenario_id = case["id"]
        scenario_name = case["name"]
        payload = case["payload"]
        user_id = f"eval-user-{idx}"
        
        print(f"\n--- Running Scenario {idx+1}/{len(scenarios)}: {scenario_name} ---")
        
        # Create a new unique session
        session = await runner.session_service.create_session(app_name="expense_app", user_id=user_id)
        
        # Initial run
        payload_str = json.dumps(payload)
        new_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=payload_str)]
        )
        
        async for _ in runner.run_async(user_id=user_id, session_id=session.id, new_message=new_message):
            pass
            
        # Inspect for HITL pauses
        sess = await runner.session_service.get_session(app_name="expense_app", session_id=session.id, user_id=user_id)
        interrupt_id = None
        for e in reversed(sess.events):
            if e.long_running_tool_ids:
                interrupt_id = list(e.long_running_tool_ids)[0]
                break
                
        if interrupt_id:
            # Automate human decision: reject malicious (prompt injection), approve clean
            decision_val = "reject" if case.get("is_malicious") else "approve"
            print(f"HITL Pause detected. Automating manager decision: {decision_val}")
            
            resume_part = types.Part(
                function_response=types.FunctionResponse(
                    id=interrupt_id,
                    name="adk_request_input",
                    response={"result": decision_val}
                )
            )
            resume_message = types.Content(role="user", parts=[resume_part])
            
            async for _ in runner.run_async(user_id=user_id, session_id=session.id, new_message=resume_message):
                pass
                
        # Retrieve final session details
        final_sess = await runner.session_service.get_session(app_name="expense_app", session_id=session.id, user_id=user_id)
        
        # Filter events to match Vertex AgentEvent schema (only allowed fields: author, content, event_time, state_delta)
        from datetime import datetime
        filtered_events = []
        for e in final_sess.events:
            filtered_e = {
                "author": e.author
            }
            if e.content:
                content_dict = e.content.model_dump()
                # Strip thought_signature to prevent invalid base64 encoding errors
                if "parts" in content_dict:
                    for part in content_dict["parts"]:
                        if "thought_signature" in part:
                            part["thought_signature"] = None
                filtered_e["content"] = content_dict
            if e.timestamp:
                filtered_e["event_time"] = datetime.fromtimestamp(float(e.timestamp)).isoformat() + "Z"
            if e.actions and e.actions.state_delta:
                filtered_e["state_delta"] = e.actions.state_delta
            filtered_events.append(filtered_e)
        
        final_decision = final_sess.state.get("decision", {})
        
        print(f"Outcome: {json.dumps(final_decision)}")
        
        # Structure the case trace matching agents-cli specifications
        trace_case = {
            "prompt": {
                "role": "user",
                "parts": [
                    {
                        "text": payload_str
                    }
                ]
            },
            "agent_data": {
                "agents": {
                    "expense_approval_workflow": {
                        "agent_id": "expense_approval_workflow",
                        "agent_type": "Workflow",
                        "description": "Ambient expense approval workflow",
                        "tools": []
                    }
                },
                "turns": [
                    {
                        "turn_index": 0,
                        "turn_id": "turn_0",
                        "events": filtered_events
                    }
                ]
            },
            "responses": [
                {
                    "response": {
                        "role": "model",
                        "parts": [
                            {
                                "text": json.dumps(final_decision)
                            }
                        ]
                    }
                }
            ]
        }
        eval_cases.append(trace_case)
        
    # Write the output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"eval_cases": eval_cases}, f, indent=2, default=str)
        
    print(f"\nTrace generation completed. Wrote traces to {output_path}")

if __name__ == "__main__":
    asyncio.run(generate_traces())
