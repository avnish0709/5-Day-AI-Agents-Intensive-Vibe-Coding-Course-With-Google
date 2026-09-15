import base64
import json
from typing import Any
from pydantic import BaseModel, Field

from google.adk.workflow import Workflow, START, node

# ... (rest of imports)

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.genai import types

from .config import APPROVAL_THRESHOLD, MODEL_NAME

import re

# Pydantic models for structured state and output validation
class ExpenseReport(BaseModel):
    amount: float
    submitter: str
    category: str
    description: str
    date: str

class RiskAssessment(BaseModel):
    risk_score: int = Field(description="Risk score from 1 (low) to 10 (high)")
    risk_factors: list[str] = Field(description="List of risk factors or anomalies identified")
    alert_raised: bool = Field(description="True if an alert should be raised for high risk")
    reason: str = Field(description="Explanation of the risk assessment")

# PII Scrubbing functions
def scrub_pii(text: str) -> tuple[str, list[str]]:
    redacted = []
    # SSN Pattern
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    if re.search(ssn_pattern, text):
        text = re.sub(ssn_pattern, '[REDACTED_SSN]', text)
        redacted.append('SSN')
        
    # Credit Card Pattern
    cc_pattern = r'\b(?:\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}|\d{15,16})\b'
    if re.search(cc_pattern, text):
        text = re.sub(cc_pattern, '[REDACTED_CC]', text)
        redacted.append('CREDIT_CARD')
        
    return text, redacted

# Prompt Injection detection function
def detect_injection(text: str) -> bool:
    injection_phrases = [
        "ignore previous instructions",
        "ignore all instructions",
        "system override",
        "bypass rules",
        "bypass constraints",
        "force auto-approve",
        "force approval",
        "auto-approve this",
        "approve instantly",
        "you must approve"
    ]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in injection_phrases)

# 1. Parsing Node: Handles base64 encoded and plain JSON payloads
def get_raw_input_string(node_input: Any, ctx: Context = None) -> str:
    if isinstance(node_input, str):
        return node_input.strip()
    if isinstance(node_input, dict):
        return json.dumps(node_input)
    if ctx and ctx.session and ctx.session.events:
        for event in reversed(ctx.session.events):
            if event.author == "user" and event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if p.text)
                if text.strip():
                    return text.strip()
    return ""

def parse_expense(ctx: Context, node_input: Any) -> Event:
    print(f"DEBUG - parse_expense called. node_input: {node_input}")
    raw_str = get_raw_input_string(node_input, ctx)
    try:
        payload = json.loads(raw_str)
    except Exception:
        if isinstance(node_input, dict):
            payload = node_input
        else:
            return Event(
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Welcome to the Expense Approval Agent! Please submit a valid JSON expense report payload containing amount, submitter, category, description, and date.")]
                )
            )

    # Handle Pub/Sub style where the report sits under 'data'
    data_payload = payload.get("data")
    if not data_payload:
        data_payload = payload

    if isinstance(data_payload, str):
        # Pub/Sub sends base64-encoded strings under 'data' key
        try:
            decoded = base64.b64decode(data_payload).decode("utf-8")
            expense_data = json.loads(decoded)
        except Exception:
            # Fallback if it is not base64 encoded
            try:
                expense_data = json.loads(data_payload)
            except Exception:
                return Event(
                    content=types.Content(
                        role="model",
                        parts=[types.Part.from_text(text="Invalid payload. Please provide a valid JSON string or Base64-encoded expense data.")]
                    )
                )
    else:
        expense_data = data_payload

    if not isinstance(expense_data, dict):
        return Event(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text="Invalid payload format. The expense report must be a JSON object.")]
            )
        )

    # Parse and validate using Pydantic model
    try:
        expense = ExpenseReport(
            amount=float(expense_data.get("amount", 0.0)),
            submitter=expense_data.get("submitter", "Unknown"),
            category=expense_data.get("category", "General"),
            description=expense_data.get("description", ""),
            date=expense_data.get("date", "")
        )
    except Exception as e:
        return Event(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=f"Validation error parsing expense fields: {e}")]
            )
        )

    state_update = {"expense": expense.model_dump()}

    if expense.amount < APPROVAL_THRESHOLD:
        return Event(output=state_update["expense"], route="auto_approve", state=state_update)
    else:
        # Route through security checkpoint first
        return Event(output=state_update["expense"], route="security_check", state=state_update)


# 2. Auto-Approve Node: Approves expenses instantly if under threshold
def auto_approve(ctx: Context, node_input: Any) -> Event:
    print(f"DEBUG - auto_approve called")
    expense = ctx.state.get("expense", {})
    decision = {
        "status": "APPROVED",
        "reason": f"Amount ${expense.get('amount')} is under threshold ${APPROVAL_THRESHOLD} (Auto-Approved).",
        "expense": expense
    }
    return Event(output=decision, state={"decision": decision})

# 3. Security Checkpoint Node: Scrub PII and defend against injections
def security_checkpoint(ctx: Context, node_input: Any) -> Event:
    print("DEBUG - security_checkpoint called")
    expense = ctx.state.get("expense", {})
    description = expense.get("description", "")
    
    # 1. Scrub PII
    cleaned_desc, redacted_cats = scrub_pii(description)
    expense_updated = dict(expense)
    expense_updated["description"] = cleaned_desc
    
    state_delta = {
        "expense": expense_updated,
        "redacted_categories": redacted_cats
    }
    
    # 2. Check for Prompt Injection
    if detect_injection(cleaned_desc):
        print("DEBUG - Prompt injection detected! Routing straight to human approval.")
        state_delta["security_event"] = True
        
        # Populate custom risk assessment warning
        security_assessment = {
            "risk_score": 10,
            "risk_factors": ["PROMPT INJECTION ATTEMPT DETECTED"],
            "alert_raised": True,
            "reason": "Security Alert: The description contains instructions attempting to bypass approval rules or force an auto-approval."
        }
        state_delta["risk_assessment"] = security_assessment
        return Event(output=expense_updated, route="direct_human_review", state=state_delta)
        
    return Event(output=expense_updated, route="llm_review", state=state_delta)

# 4. LLM Risk Review Node: Evaluates risk for high-amount expenses
model = Gemini(model=MODEL_NAME)

risk_reviewer = LlmAgent(
    name="risk_reviewer",
    model=model,
    instruction=(
        "You are an automated expense risk reviewer. Evaluate the expense report "
        "provided in the user message for risk factors, potential policy violations, "
        "or anomalous behavior. Provide a risk assessment."
    ),
    output_schema=RiskAssessment,
    output_key="risk_assessment"
)

# 5. Human Approval Node (HITL): Pauses for manager approval/rejection
@node(rerun_on_resume=True)
async def human_approval(ctx: Context, node_input: Any):
    print(f"DEBUG - human_approval called. resume_inputs: {ctx.resume_inputs}")
    if not ctx.resume_inputs or "approval" not in ctx.resume_inputs:
        risk_assessment = ctx.state.get("risk_assessment", {})
        expense = ctx.state.get("expense", {})
        is_security_event = ctx.state.get("security_event", False)
        
        header = "🚨 SECURITY ALERT: PROMPT INJECTION DETECTED 🚨\n" if is_security_event else "⚠️ EXPENSE PENDING APPROVAL\n"
        
        message = (
            f"{header}"
            f"Amount: ${expense.get('amount')}\n"
            f"Submitter: {expense.get('submitter')}\n"
            f"Description: {expense.get('description')}\n"
            f"Risk Score: {risk_assessment.get('risk_score', 'N/A')}/10\n"
            f"Alert Raised: {risk_assessment.get('alert_raised', False)}\n"
            f"Reason: {risk_assessment.get('reason', 'N/A')}\n"
        )
        redacted = ctx.state.get("redacted_categories", [])
        if redacted:
            message += f"Redacted Categories: {', '.join(redacted)}\n"
            
        message += "\nPlease reply with 'approve' or 'reject'."
        yield RequestInput(interrupt_id="approval", message=message)
        return

    user_decision = ctx.resume_inputs["approval"]
    is_approved = "approve" in str(user_decision).lower()
    
    expense = ctx.state.get("expense", {})
    decision = {
        "status": "APPROVED" if is_approved else "REJECTED",
        "reason": f"Reviewed by manager: {user_decision}",
        "expense": expense,
        "risk_assessment": ctx.state.get("risk_assessment"),
        "security_event": ctx.state.get("security_event", False),
        "redacted_categories": ctx.state.get("redacted_categories", [])
    }
    yield Event(output=decision, state={"decision": decision})


# 6. Define Workflow Graph
root_agent = Workflow(
    name="expense_approval_workflow",
    edges=[
        (START, parse_expense),
        (
            parse_expense,
            {
                "auto_approve": auto_approve,
                "security_check": security_checkpoint,
            }
        ),
        (
            security_checkpoint,
            {
                "llm_review": risk_reviewer,
                "direct_human_review": human_approval,
            }
        ),
        (risk_reviewer, human_approval)
    ]
)


