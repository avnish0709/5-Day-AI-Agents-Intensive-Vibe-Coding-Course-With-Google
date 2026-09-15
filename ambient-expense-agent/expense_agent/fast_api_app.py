import logging
import os
import base64
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types
from dotenv import load_dotenv

# Load local environment variables/API key
load_dotenv()

# Setup standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("expense_agent_service")

# Setup telemetry: Disable cloud trace
os.environ["OTEL_TO_CLOUD"] = "False"
try:
    from google.adk.cli.api_server import _setup_telemetry
    _setup_telemetry(otel_to_cloud=False)
    logger.info("ADK telemetry setup configured with otel_to_cloud=False.")
except Exception as e:
    logger.warning(f"Could not initialize telemetry configuration manually: {e}")

from expense_agent.agent import root_agent

# Initialize ADK app and runner
adk_app = App(name="expense_app", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)

app = FastAPI(title="Ambient Expense Approval Agent Service")

class PubSubMessage(BaseModel):
    data: str | None = None
    message_id: str | None = None
    publish_time: str | None = None

class PubSubPayload(BaseModel):
    message: PubSubMessage
    subscription: str

class ResumePayload(BaseModel):
    session_id: str
    user_id: str
    decision: str

@app.get("/")
async def root():
    return {
        "message": "Ambient Expense Approval Agent Service is running.",
        "documentation": "/docs",
        "pubsub_endpoint": "POST /pubsub"
    }

@app.post("/pubsub")
@app.post("/apps/expense_agent/trigger/pubsub")
@app.post("/")
async def handle_pubsub(payload: PubSubPayload):
    logger.info(f"Received Pub/Sub message from subscription: {payload.subscription}")
    
    # Gotcha: normalize the subscription path to short name
    short_sub_name = payload.subscription.split("/")[-1]
    logger.info(f"Normalized subscription path to: {short_sub_name}")
    
    # Extract message dict
    msg_dict = payload.message.model_dump()
    
    # Create a new unique session for this event
    session = await runner.session_service.create_session(
        app_name="expense_app", user_id=short_sub_name
    )
    logger.info(f"Created new session: {session.id} for user: {short_sub_name}")
    
    input_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=json.dumps(msg_dict))]
    )
    
    result_events = []
    paused = False
    interrupt_info = None
    
    try:
        async for event in runner.run_async(
            user_id=short_sub_name,
            session_id=session.id,
            new_message=input_content
        ):
            result_events.append(event)
            
        # Inspect session events to check if we paused for HITL approval
        sess = await runner.session_service.get_session(
            app_name="expense_app", session_id=session.id, user_id=short_sub_name
        )
        
        for e in reversed(sess.events):
            if e.long_running_tool_ids:
                interrupt_id = list(e.long_running_tool_ids)[0]
                logger.info(f"Workflow paused. Session ID: {session.id}, Interrupt ID: {interrupt_id}")
                paused = True
                
                prompt_msg = ""
                if e.content and e.content.parts:
                    fc = e.content.parts[0].function_call
                    if fc and fc.args:
                        prompt_msg = fc.args.get("message", "")
                
                interrupt_info = {
                    "interrupt_id": interrupt_id,
                    "message": prompt_msg
                }
                break
                
    except Exception as e:
        logger.exception("Error executing workflow")
        raise HTTPException(status_code=500, detail=str(e))
        
    if paused:
        return {
            "status": "PENDING_APPROVAL",
            "session_id": session.id,
            "user_id": short_sub_name,
            "interrupt": interrupt_info
        }
        
    decision = None
    for event in result_events:
        if event.output:
            decision = event.output
            break
            
    if not decision:
        sess = await runner.session_service.get_session(
            app_name="expense_app", session_id=session.id, user_id=short_sub_name
        )
        decision = sess.state.get("decision")
        
    return {
        "status": "COMPLETED",
        "session_id": session.id,
        "user_id": short_sub_name,
        "decision": decision
    }

@app.post("/resume")
async def resume_workflow(payload: ResumePayload):
    logger.info(f"Resuming session: {payload.session_id} for user: {payload.user_id} with decision: {payload.decision}")
    
    resume_part = types.Part(
        function_response=types.FunctionResponse(
            id="approval",
            name="adk_request_input",
            response={"result": payload.decision}
        )
    )
    resume_message = types.Content(role="user", parts=[resume_part])
    
    result_events = []
    try:
        async for event in runner.run_async(
            user_id=payload.user_id,
            session_id=payload.session_id,
            new_message=resume_message
        ):
            result_events.append(event)
    except Exception as e:
        logger.exception("Error resuming workflow")
        raise HTTPException(status_code=500, detail=str(e))
        
    decision = None
    for event in result_events:
        if event.output:
            decision = event.output
            break
            
    if not decision:
        sess = await runner.session_service.get_session(
            app_name="expense_app", session_id=payload.session_id, user_id=payload.user_id
        )
        decision = sess.state.get("decision")
        
    return {
        "status": "COMPLETED",
        "session_id": payload.session_id,
        "user_id": payload.user_id,
        "decision": decision
    }
