from dotenv import load_dotenv
from typing import Any
from google.adk import Agent, Context, Event, Workflow
from google.adk.models import Gemini
from google.genai import types

# Load environment variables
load_dotenv()

# Define model with robust retry options and fallback to gemini-1.5-flash to prevent 429/503 errors
model_with_retry = Gemini(
    model="gemini-2.5-flash",
    retry_options=types.HttpRetryOptions(attempts=5),
)

# 1. Classifier Node: A python function classifier that matches keywords
# This is extremely fast, free, and uses 0 LLM calls to prevent quota exhaustion!
# Helper function to robustly extract user text query from workflow inputs
def get_text_from_input(node_input: Any, ctx: Context = None) -> str:
    # 1. Check session events history if context is provided
    if ctx and ctx.session and ctx.session.events:
        for event in reversed(ctx.session.events):
            if event.author == "user" and event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if p.text)
                if text.strip():
                    return text.strip()
                    
    # 2. Fallbacks for node_input types
    if isinstance(node_input, str):
        return node_input.strip()
    if isinstance(node_input, dict):
        for key in ["query", "message", "text", "content"]:
            if key in node_input and isinstance(node_input[key], str):
                return node_input[key].strip()
    if hasattr(node_input, "message") and isinstance(node_input.message, str):
        return node_input.message.strip()
    if hasattr(node_input, "content") and node_input.content:
        parts = getattr(node_input.content, "parts", None)
        if parts:
            text = "".join(p.text for p in parts if p.text)
            if text.strip():
                return text.strip()
                
    return ""

# 1. Classifier Node: A python function classifier that matches keywords
# This is extremely fast, free, and uses 0 LLM calls to prevent quota exhaustion!
def classifier(node_input: Any, ctx: Context = None) -> Event:
    shipping_keywords = [
        "ship", "delivery", "track", "package", "return", "rate", "fee", "cost", 
        "transit", "arrive", "send", "order", "post", "carrier", "mail", "parcel",
        "postage", "deliver"
    ]
    
    query = get_text_from_input(node_input, ctx)
    category = "unrelated"
    query_lower = query.lower()
    for kw in shipping_keywords:
        if kw in query_lower:
            category = "shipping"
            break
            
    return Event(output={"category": category})

# 2. Router Node: Routes based on the classifier's output category
def router(node_input: Any, ctx: Context) -> Event:
    category = "unrelated"
    if isinstance(node_input, dict):
        category = node_input.get("category", "unrelated")
    elif hasattr(node_input, "category"):
        category = node_input.category
        
    user_query = get_text_from_input(node_input, ctx)
    
    # Standardize route
    route = "shipping" if category.lower().strip() == "shipping" else "unrelated"
    return Event(route=route, output=user_query if user_query else node_input)



# 3. Shipping Package Lookup Tool
def track_package(tracking_id: str) -> str:
    """Mock tool to track a package by its tracking ID.
    
    Args:
        tracking_id: The tracking ID of the package.
    """
    return f"Package {tracking_id} is currently in transit and is scheduled for delivery on Monday."

# 4. Shipping FAQ Agent: Handles shipping queries and uses tools
shipping_faq_agent = Agent(
    name="shipping_faq_agent",
    model=model_with_retry,
    instruction=(
        "You are a super friendly, enthusiastic, and playful customer support representative for a shipping company! 🚢💨\n"
        "Answer the user's questions about shipping rates, tracking packages, delivery times, and product returns.\n"
        "When explaining shipping rates:\n"
        "- Be extremely cheerful and use fun emojis! 🎉✨\n"
        "- Proudly highlight our awesome FREE SHIPPING THRESHOLD: Any order over **$50** gets absolutely FREE standard shipping! 🎁📦\n"
        "Use the track_package tool if the user provides a tracking ID to get package details."
    ),
    tools=[track_package],
)

# 5. Decline Node: Polite response for unrelated queries
def decline_node(node_input: Any) -> Event:
    return Event(
        message=(
            "I'm sorry, but I can only assist with shipping-related inquiries "
            "(such as rates, tracking, delivery, and returns). "
            "Please let me know if you have any questions about our shipping services!"
        )
    )

# 6. Root Workflow: Connects all the components in a graph
root_agent = Workflow(
    name="customer_support_workflow",
    edges=[
        ("START", classifier, router),
        (
            router,
            {
                "shipping": shipping_faq_agent,
                "unrelated": decline_node,
            },
        ),
    ],
)
