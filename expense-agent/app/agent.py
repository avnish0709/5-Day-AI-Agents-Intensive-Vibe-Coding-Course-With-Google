# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any
import re
import os
import google.auth

from google.adk import Context, Event, Workflow
from google.adk.apps import App
from google.adk.events import RequestInput
from google.adk.workflow import node
from google.adk.models import Gemini
from google.genai import types

# Set up standard Google Cloud credentials configuration
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    pass

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# Define default model in case it is queried/used
model_with_retry = Gemini(
    model="gemini-2.5-flash",
    retry_options=types.HttpRetryOptions(attempts=3),
)

# 1. Input Parsing Node
def parse_expense_input(node_input: Any, ctx: Context) -> Event:
    """Parses input query/message to extract the dollar amount and description."""
    # Check if it's already a dict with amount
    if isinstance(node_input, dict) and "amount" in node_input:
        return Event(output={
            "amount": float(node_input["amount"]),
            "description": node_input.get("description", "expense")
        })

    # Otherwise, extract the text/query
    query = ""
    if isinstance(node_input, str):
        query = node_input
    elif isinstance(node_input, dict):
        if "text" in node_input:
            query = node_input["text"]
        elif "parts" in node_input and node_input["parts"]:
            part = node_input["parts"][0]
            if isinstance(part, dict):
                query = part.get("text") or ""
        else:
            query = node_input.get("query") or node_input.get("message") or ""
    elif hasattr(node_input, "parts") and node_input.parts:
        part = node_input.parts[0]
        if hasattr(part, "text") and part.text:
            query = part.text
        elif isinstance(part, dict):
            query = part.get("text") or ""
    elif hasattr(node_input, "text") and node_input.text:
        query = node_input.text
    else:
        query = str(node_input)

    # Parse amount using regex
    amount = 0.0
    amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', query)
    if amount_match:
        amount = float(amount_match.group(1))

    print(f"parse_expense_input received node_input={node_input} (type={type(node_input)}) -> query={query}, amount={amount}", flush=True)

    return Event(output={
        "amount": amount,
        "description": query if query else "expense"
    })

# 2. Router Node
def router(node_input: Any, ctx: Context) -> Event:
    """Routes based on the expense amount (< $100 vs >= $100)."""
    amount = 0.0
    if isinstance(node_input, dict):
        amount = node_input.get("amount", 0.0)
    elif hasattr(node_input, "amount"):
        amount = getattr(node_input, "amount", 0.0)

    route = "auto_approve" if amount < 100.0 else "review"
    return Event(route=route, output=node_input)

# 3. Auto Approve Node
def auto_approve(node_input: Any) -> Event:
    """Instantly approves claim under $100."""
    amount = 0.0
    description = ""
    if isinstance(node_input, dict):
        amount = node_input.get("amount", 0.0)
        description = node_input.get("description", "")

    return Event(
        message=(
            f"APPROVED: Claim of ${amount:.2f} for '{description}' is under $100 "
            "and has been automatically approved! ✅"
        )
    )

# 4. Review Agent Node (with Human-in-the-loop pause)
@node(rerun_on_resume=True)
def review_agent(node_input: Any, ctx: Context) -> Any:
    """Triggers a human-in-the-loop review for claims $100 or more."""
    interrupt_id = "expense_approval_review"
    print(f"review_agent entered. node_input={node_input}, resume_inputs={getattr(ctx, 'resume_inputs', None)}", flush=True)
    
    amount = 0.0
    description = ""
    if isinstance(node_input, dict):
        amount = node_input.get("amount", 0.0)
        description = node_input.get("description", "")

    # Check if we have the user response from resume_inputs
    if ctx.resume_inputs and interrupt_id in ctx.resume_inputs:
        user_response = ctx.resume_inputs[interrupt_id]
        result_text = ""
        if isinstance(user_response, dict):
            result_text = user_response.get("result", "")
        elif isinstance(user_response, str):
            result_text = user_response

        # Determine decision based on response
        if any(kw in result_text.lower() for kw in ["approve", "yes", "y", "ok"]):
            return Event(
                message=(
                    f"APPROVED: Claim of ${amount:.2f} for '{description}' has been "
                    f"manually approved by reviewer! (Reason: {result_text}) ✅"
                )
            )
        else:
            return Event(
                message=(
                    f"REJECTED: Claim of ${amount:.2f} for '{description}' has been "
                    f"manually rejected by reviewer. (Reason: {result_text}) ❌"
                )
            )

    # Pause and request input
    return RequestInput(
        interrupt_id=interrupt_id,
        message=f"Expense of ${amount:.2f} for '{description}' requires manual review. Do you approve? (yes/no)",
    )

# 5. Root Workflow definition
root_agent = Workflow(
    name="expense_reporting_workflow",
    edges=[
        ("START", parse_expense_input, router),
        (
            router,
            {
                "auto_approve": auto_approve,
                "review": review_agent,
            },
        ),
    ],
)

from google.adk.apps import ResumabilityConfig

app = App(
    root_agent=root_agent,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True),
)
