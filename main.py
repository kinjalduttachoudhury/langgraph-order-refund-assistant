import os

from dotenv import load_dotenv
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent

from langgraph.graph import StateGraph, START, END

load_dotenv()

# ============================================================
# MODEL
# ============================================================

model = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# ============================================================
# UTIL FUNCTIONS
# ============================================================

def process_refund(orderId):
    # call payment API
    return f"Refund for order {orderId} is processed."

# ============================================================
# TOOLS
# ============================================================

@tool
def get_order_details(orderId: str):
    """Get the details for a orderId. 
    Details include the status of the order, whether dicount is applied, the order amount"""

    if orderId == "123":
        return {
            "discount": True,
            "status": "picked up",
            "amount": 750
        }

    elif orderId == "456":
        return {
            "discount": False,
            "status": "preparing",
            "amount": 300
        }
    
    else:
        return {
            "error": "Order not found"
        }

# ============================================================
# AGENT
# ============================================================

order_agent = create_agent(
    model=model,
    tools=[
        get_order_details
    ]
)

intent_agent = create_agent(
    model=model,
    tools=[]
)

class AgentState(TypedDict):
    user_message: str
    intent: str
    orderId: str
    discount_applied : bool
    final_response: str 

# ============================================================
# NODE DEFINITIONS
# ============================================================

def get_intent_node(state: AgentState):

    print("\n")
    print("=" * 70)
    print("LANGGRAPH → INTENT NODE")
    print("=" * 70)

    prompt = state["user_message"]

    # if state.get("validation_feedback"):
    #     prompt += f"\n\nValidator feedback: {state.get('validation_feedback')}" 

    response = intent_agent.invoke({
        "messages": [
            {
                "role": "system",
                "content": """You are a order/refund assistant for a online food ordering business.
                You have to determine the intent of the user. 
                Should be one of the following :
                - If intent is get order status, return status
                - If intent is get refund, return refund
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    print("\nAGENT FINISHED")

    messages = response["messages"]

    for message in reversed(messages):
        if type(message).__name__ == "AIMessage":
            intent = message.content
            break

    return {
        "intent": intent
    }

def get_order_id_node(state: AgentState):
    print("\n")
    print("=" * 70)
    print("LANGGRAPH → ORDER ID NODE")
    print("=" * 70)

    prompt = state["user_message"]

    response = intent_agent.invoke({
        "messages": [
            {
                "role": "system",
                "content": """You are a order/refund assistant for a online food ordering business.
                You have to get the order id from the user message. 
                
                Return just the order id
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    print("\nAGENT FINISHED")

    messages = response["messages"]

    for message in reversed(messages):
        if type(message).__name__ == "AIMessage":
            orderId = message.content
            break

    return {
        "orderId": orderId
    }

def get_status_node(state: AgentState):
    print("\n")
    print("=" * 70)
    print("LANGGRAPH → STATUS NODE")
    print("=" * 70)

    orderId = state["orderId"]
    prompt = f"Get the status for the order id {orderId}"

    response = order_agent.invoke({
        "messages": [
            {
                "role": "system",
                "content": """You are a order/refund assistant for a online food ordering business.
                You have the following tools available : get_order_details
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    print("\nAGENT FINISHED")

    return {
        "final_response": response
    }

def get_discount_node(state: AgentState):
    print("\n")
    print("=" * 70)
    print("LANGGRAPH → DISCOUNT NODE")
    print("=" * 70)

    orderId = state["orderId"]
    prompt = f"""Get the discount details for the order id {orderId}.

                Based on whether discount is applied on the order or not, return a boolean True/False
            """

    response = order_agent.invoke({
        "messages": [
            {
                "role": "system",
                "content": """You are a order/refund assistant for a online food ordering business.
                You have the following tools available : get_order_details
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    print("\nAGENT FINISHED")

    messages = response["messages"]

    for message in reversed(messages):
        if type(message).__name__ == "AIMessage":
            discount_applied = message.content.strip().lower() == "true"
            break

    return {
        "discount_applied": discount_applied
    }

def not_eligible_node(state: AgentState):
    return {
        "final_response" : f"Order {state['orderId']} is not eligible for a refund "
            "because a discount was applied to the order."
    }

def process_refund_node(state: AgentState):

    response = process_refund(state["orderId"])

    return {
        "final_response" : response
    }

def route_by_intent(state: AgentState):
    intent = state["intent"]

    if intent == "status":
        return "status"
    if intent == "refund":
        return "refund"
    
def route_by_discount(state: AgentState):
    discount_applied = state["discount_applied"]

    if discount_applied:
        return "not eligible"
    
    return "eligible"

# ============================================================
# GRAPH BUILD
# ============================================================

builder = StateGraph(AgentState)

# ============================================================
# NODE CREATION
# ============================================================

builder.add_node(
    "intent",
    get_intent_node
)

builder.add_node(
    "order id",
    get_order_id_node
)

builder.add_node(
    "status",
    get_status_node
)

builder.add_node(
    "discount",
    get_discount_node
)

builder.add_node(
    "not eligible",
    not_eligible_node
)

builder.add_node(
    "process refund",
    process_refund_node
)

# ============================================================
# EDGE CREATION
# ============================================================

builder.add_edge(
    START,
    "intent"
)

builder.add_edge(
    "intent",
    "order id"
)

builder.add_conditional_edges(
    "order id",
    route_by_intent,
    {
        "status": "status",
        "refund": "discount"
    }
)

builder.add_edge(
    "status",
    END
)

builder.add_conditional_edges(
    "discount",
    route_by_discount,
    {
        "not eligible": "not eligible",
        "eligible": "process refund"
    }
)

builder.add_edge(
    "not eligible",
    END
)

builder.add_edge(
    "process refund",
    END
)


# ============================================================
# COMPILE GRAPH
# ============================================================

graph = builder.compile()

result = graph.invoke({
    "user_message": (
        "What is the order of my order 123"
    )
})

print("\n")
print("=" * 70)
print("GRAPH FINISHED")
print("=" * 70)

print(result["intent"])
print(result["final_response"])