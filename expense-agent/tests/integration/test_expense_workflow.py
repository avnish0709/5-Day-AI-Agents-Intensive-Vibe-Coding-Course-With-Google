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

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import app

@pytest.mark.asyncio
async def test_expense_auto_approve() -> None:
    """Tests that expenses under $100 are automatically approved without pauses."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="test_user", app_name="app")
    runner = Runner(app=app, session_service=session_service)

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Please approve my $50 lunch claim")]
    )

    events = []
    async for event in runner.run_async(
        new_message=message,
        user_id="test_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        events.append(event)

    assert len(events) > 0
    # The last event or messages should contain the approval message
    combined_message = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    combined_message += part.text

    assert "APPROVED" in combined_message
    assert "lunch" in combined_message.lower() or "claim" in combined_message.lower()
    assert "automatically approved" in combined_message

@pytest.mark.asyncio
async def test_expense_manual_review_approve() -> None:
    """Tests that expenses $100 or more trigger a review pause and can be manually approved."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="test_user", app_name="app")
    runner = Runner(app=app, session_service=session_service)

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Please approve my $150 travel claim")]
    )

    # 1. Run the initial claim - it should trigger an interrupt pause
    events = []
    async for event in runner.run_async(
        new_message=message,
        user_id="test_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        events.append(event)

    # Confirm that it paused and returned a long_running_tool_id for the interrupt
    last_event = events[-1]
    assert last_event.long_running_tool_ids is not None
    assert "expense_approval_review" in last_event.long_running_tool_ids
    invocation_id = last_event.invocation_id

    # 2. Resume the session with a manual "yes" approval response
    resume_message = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id="expense_approval_review",
                    name="adk_request_input",
                    response={"result": "yes, approved by manager"},
                )
            )
        ]
    )

    resume_events = []
    async for event in runner.run_async(
        new_message=resume_message,
        user_id="test_user",
        session_id=session.id,
        invocation_id=invocation_id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        resume_events.append(event)

    # Check the final output
    combined_message = ""
    for event in resume_events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    combined_message += part.text

    assert "APPROVED" in combined_message
    assert "manually approved" in combined_message
    assert "approved by manager" in combined_message

@pytest.mark.asyncio
async def test_expense_manual_review_reject() -> None:
    """Tests that expenses $100 or more trigger a review pause and can be manually rejected."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="test_user", app_name="app")
    runner = Runner(app=app, session_service=session_service)

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Please approve my $200 flight claim")]
    )

    # 1. Run the initial claim
    events = []
    async for event in runner.run_async(
        new_message=message,
        user_id="test_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        events.append(event)

    # Confirm pause
    last_event = events[-1]
    assert last_event.long_running_tool_ids is not None
    assert "expense_approval_review" in last_event.long_running_tool_ids
    invocation_id = last_event.invocation_id

    # 2. Resume the session with a manual "no" rejection response
    resume_message = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id="expense_approval_review",
                    name="adk_request_input",
                    response={"result": "no, too expensive"},
                )
            )
        ]
    )

    resume_events = []
    async for event in runner.run_async(
        new_message=resume_message,
        user_id="test_user",
        session_id=session.id,
        invocation_id=invocation_id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        resume_events.append(event)

    # Check the final output
    combined_message = ""
    for event in resume_events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    combined_message += part.text

    assert "REJECTED" in combined_message
    assert "manually rejected" in combined_message
    assert "too expensive" in combined_message
