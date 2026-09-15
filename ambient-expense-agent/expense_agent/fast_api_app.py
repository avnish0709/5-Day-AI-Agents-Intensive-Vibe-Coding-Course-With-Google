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

from fastapi.responses import HTMLResponse

@app.get("/")
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def serve_dashboard():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ambient Expense Approval Agent - Manager Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --primary-blue: #38bdf8;
            --accent-purple: #c084fc;
            --success-green: #34d399;
            --warning-amber: #fbbf24;
            --danger-red: #f87171;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(192, 132, 252, 0.08) 0%, transparent 40%);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            background: linear-gradient(135deg, var(--primary-blue), var(--accent-purple));
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(to right, #ffffff, var(--text-muted));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            background: rgba(52, 211, 153, 0.15);
            color: var(--success-green);
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
            border: 1px solid rgba(52, 211, 153, 0.3);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(52, 211, 153, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--primary-blue);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-group {
            margin-bottom: 1rem;
        }

        label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
        }

        input, select, textarea {
            width: 100%;
            padding: 0.75rem 1rem;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-main);
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s ease;
        }

        input:focus, select:focus, textarea:focus {
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }

        .btn {
            width: 100%;
            padding: 0.85rem;
            background: linear-gradient(135deg, var(--primary-blue), #0284c7);
            color: #fff;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s ease, filter 0.2s ease;
        }

        .btn:hover {
            filter: brightness(1.1);
        }

        .btn:active {
            transform: scale(0.99);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--success-green), #059669);
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--danger-red), #dc2626);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .stat-card {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }

        .stat-val {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-main);
        }

        .stat-lbl {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .queue-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-height: 420px;
            overflow-y: auto;
        }

        .queue-item {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .queue-info h4 {
            font-size: 0.95rem;
            margin-bottom: 0.2rem;
        }

        .queue-info p {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .queue-actions {
            display: flex;
            gap: 0.5rem;
        }

        .queue-actions button {
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            width: auto;
        }

        .tag {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-top: 0.3rem;
        }

        .tag-auto { background: rgba(52, 211, 153, 0.2); color: var(--success-green); }
        .tag-hitl { background: rgba(251, 191, 36, 0.2); color: var(--warning-amber); }
        .tag-sec { background: rgba(248, 113, 113, 0.2); color: var(--danger-red); }

        pre {
            background: #090d16;
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.8rem;
            color: var(--primary-blue);
            overflow-x: auto;
            border: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <div class="logo-icon">⚡</div>
                <div>
                    <h1>Ambient Expense Approval Agent</h1>
                    <p style="font-size: 0.8rem; color: var(--text-muted);">ADK 2.0 Web Manager Dashboard & Ingestion Queue</p>
                </div>
            </div>
            <div class="status-badge">
                <div class="pulse-dot"></div>
                Service Active
            </div>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-val" id="stat-processed">0</div>
                <div class="stat-lbl">Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-val" id="stat-auto" style="color: var(--success-green);">0</div>
                <div class="stat-lbl">Auto-Approved</div>
            </div>
            <div class="stat-card">
                <div class="stat-val" id="stat-pending" style="color: var(--warning-amber);">0</div>
                <div class="stat-lbl">Pending Review</div>
            </div>
        </div>

        <div class="grid">
            <!-- Submit Expense Form -->
            <div class="card">
                <div class="card-title">📤 Submit Expense Report (Pub/Sub Simulator)</div>
                <form id="expenseForm">
                    <div class="form-group">
                        <label>Submitter Email</label>
                        <input type="email" id="submitter" value="alice@company.com" required>
                    </div>
                    <div class="form-group">
                        <label>Amount ($ USD)</label>
                        <input type="number" step="0.01" id="amount" value="45.00" required>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select id="category">
                            <option value="office-supplies">Office Supplies (<$100 Auto-Approve)</option>
                            <option value="meals">Meals & Entertainment (<$100 Auto-Approve)</option>
                            <option value="travel">Travel & Flights (>=$100 HITL Review)</option>
                            <option value="hardware">Hardware & Electronics (>=$100 HITL Review)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Description (Supports Security Checks & PII Tests)</label>
                        <textarea id="description" rows="2" required>Wireless mouse and mechanical keyboard combo</textarea>
                    </div>
                    <button type="submit" class="btn">🚀 Trigger Pub/Sub Ingestion</button>
                </form>
            </div>

            <!-- Pending Approvals Queue -->
            <div class="card">
                <div class="card-title">⏳ Manager HITL Approval Queue</div>
                <div class="queue-list" id="queueList">
                    <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; padding: 2rem;">No pending approvals in queue.</p>
                </div>
            </div>
        </div>

        <!-- Activity Log -->
        <div class="card">
            <div class="card-title">🔍 Live Execution Trace Output</div>
            <pre id="outputLog">Ready for incoming transactions. Submit an expense report above to observe workflow behavior.</pre>
        </div>
    </div>

    <script>
        let processedCount = 0;
        let autoApprovedCount = 0;
        let pendingCount = 0;
        const pendingSessions = [];

        document.getElementById('expenseForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitter = document.getElementById('submitter').value;
            const amount = parseFloat(document.getElementById('amount').value);
            const category = document.getElementById('category').value;
            const description = document.getElementById('description').value;

            const payloadData = JSON.stringify({
                amount: amount,
                submitter: submitter,
                category: category,
                description: description,
                date: new Date().toISOString().split('T')[0]
            });

            // Base64 encode for Pub/Sub simulation
            const b64Data = btoa(payloadData);

            const requestBody = {
                message: {
                    data: b64Data,
                    message_id: "msg_" + Math.random().toString(36).substr(2, 9),
                    publish_time: new Date().toISOString()
                },
                subscription: "projects/expense-system/subscriptions/manager-sub"
            };

            logOutput("Sending Pub/Sub Payload to /apps/expense_agent/trigger/pubsub:\\n" + JSON.stringify(requestBody, null, 2));

            try {
                const res = await fetch('/apps/expense_agent/trigger/pubsub', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });
                const data = await res.json();
                logOutput("Response:\\n" + JSON.stringify(data, null, 2));

                processedCount++;
                document.getElementById('stat-processed').innerText = processedCount;

                if (data.status === "COMPLETED") {
                    autoApprovedCount++;
                    document.getElementById('stat-auto').innerText = autoApprovedCount;
                } else if (data.status === "PENDING_APPROVAL") {
                    pendingCount++;
                    document.getElementById('stat-pending').innerText = pendingCount;
                    pendingSessions.push({
                        sessionId: data.session_id,
                        submitter: submitter,
                        amount: amount,
                        category: category,
                        description: description
                    });
                    renderQueue();
                }
            } catch (err) {
                logOutput("Error submitting expense: " + err);
            }
        });

        function renderQueue() {
            const container = document.getElementById('queueList');
            if (pendingSessions.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; padding: 2rem;">No pending approvals in queue.</p>';
                return;
            }

            container.innerHTML = pendingSessions.map((item, idx) => `
                <div class="queue-item">
                    <div class="queue-info">
                        <h4>$${item.amount.toFixed(2)} - ${item.submitter}</h4>
                        <p>${item.description}</p>
                        <span class="tag tag-hitl">PENDING HITL REVIEW</span>
                    </div>
                    <div class="queue-actions">
                        <button class="btn btn-success" onclick="resumeSession(${idx}, 'APPROVE')">Approve</button>
                        <button class="btn btn-danger" onclick="resumeSession(${idx}, 'REJECT')">Reject</button>
                    </div>
                </div>
            `).join('');
        }

        async function resumeSession(idx, decision) {
            const item = pendingSessions[idx];
            logOutput(`Resuming session ${item.sessionId} with decision: ${decision}...`);

            try {
                const res = await fetch('/resume', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: item.sessionId,
                        user_id: "manager-sub",
                        decision: decision
                    })
                });
                const data = await res.json();
                logOutput("Resume Response:\\n" + JSON.stringify(data, null, 2));

                pendingSessions.splice(idx, 1);
                pendingCount--;
                document.getElementById('stat-pending').innerText = pendingCount;
                renderQueue();
            } catch (err) {
                logOutput("Error resuming session: " + err);
            }
        }

        function logOutput(msg) {
            const logEl = document.getElementById('outputLog');
            logEl.innerText = `[${new Date().toLocaleTimeString()}] ${msg}\\n\\n` + logEl.innerText;
        }
    </script>
</body>
</html>
    """)

@app.get("/api/info")
async def info():
    return {
        "message": "Ambient Expense Approval Agent Service is running.",
        "dashboard": "/dashboard",
        "documentation": "/docs",
        "pubsub_endpoint": "POST /pubsub",
        "resume_endpoint": "POST /resume"
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
