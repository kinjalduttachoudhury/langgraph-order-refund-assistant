# LangGraph Order & Refund Assistant

A learning project demonstrating how LangGraph can orchestrate LLM-powered nodes, agents, tools, shared state, and conditional routing.

The project demonstrates how an LLM can be used for tasks such as intent detection and information extraction, while LangGraph controls the overall workflow and deterministic business logic.

## What It Does

The assistant handles two types of requests:

- Check the status of an order
- Request a refund for an order

The refund workflow applies the following business rule:

- If a discount was applied to the order → the order is not eligible for a refund
- If no discount was applied → the refund is processed

## Architecture

```text
User Request
     |
     v
Intent Detection
     |
     v
Extract Order ID
     |
     +------------------+
     |                  |
   Status             Refund
     |                  |
     v                  v
Get Order          Check Discount
Status                 |
                       +----------------+
                       |                |
                   Discount        No Discount
                       |                |
                       v                v
                 Not Eligible      Process Refund
                       |                |
                       +-------+--------+
                               |
                              END
```

## LangGraph Concepts Demonstrated

- `StateGraph`
- Graph state using `TypedDict`
- Nodes
- Conditional edges
- Routing based on graph state
- `START` and `END`
- LLM agents inside graph nodes
- Tool calling
- Deterministic Python business logic
- Multiple workflow branches
- Shared state between nodes
- Separation of LLM reasoning from workflow control

## How the Workflow Works

### 1. Intent Detection

The `intent` node sends the user's message to an LLM agent.

The agent determines whether the user wants:

- `status`
- `refund`

For example:

```text
I want a refund for order 123
```

The agent returns:

```text
refund
```

The result is stored in the LangGraph state.

### 2. Extract Order ID

The `order id` node extracts the order ID from the user's message.

For example:

```text
I want a refund for order 123
```

The node extracts:

```text
123
```

and stores it in the graph state.

At this point, the state contains information produced by multiple nodes:

```python
{
    "user_message": "...",
    "intent": "refund",
    "orderId": "123"
}
```

### 3. Route Based on Intent

LangGraph evaluates the `route_by_intent` function.

If the intent is `status`, the graph follows the status branch.

If the intent is `refund`, the graph follows the refund branch.

## Status Branch

If the intent is `status`, LangGraph executes the Status node.

The node gets the order ID from the shared state and asks the Order Agent to retrieve the order information.

The Order Agent has access to the `get_order_details` tool.

For example, order `123` returns:

```python
{
    "discount": True,
    "status": "picked up",
    "amount": 750
}
```

The agent then produces the final response.

The graph reaches `END`.

## Refund Branch

If the intent is `refund`, LangGraph routes to the Discount node.

### Check Discount

The Discount node retrieves the order information using the Order Agent and the `get_order_details` tool.

For example:

```python
{
    "discount": True,
    "status": "picked up",
    "amount": 750
}
```

The node extracts the discount information and stores it in the graph state:

```python
{
    "discount_applied": True
}
```

### Apply the Business Rule

LangGraph then evaluates `route_by_discount`.

The rule is:

```text
Discount Applied?
       |
   +---+---+
   |       |
  Yes      No
   |       |
   v       v
Reject    Process
Refund    Refund
```

This decision is handled by deterministic Python logic.

The LLM does not decide whether the refund should be processed.

### Discount Applied

If a discount was applied, LangGraph routes to the `not eligible` node.

The node creates a response such as:

```text
Order 123 is not eligible for a refund because a discount was applied to the order.
```

The graph then reaches `END`.

### No Discount

If no discount was applied, LangGraph routes to the `process refund` node.

The node calls:

```python
process_refund(orderId)
```

In this learning project, the function simulates a payment API and returns:

```text
Refund for order 456 is processed.
```

The graph then reaches `END`.

## Agents

The project uses two agents.

### Intent Agent

The Intent Agent is responsible for understanding the user's request.

It has no tools:

```python
intent_agent = create_agent(
    model=model,
    tools=[]
)
```

Its job is to determine whether the intent is:

```text
status
```

or:

```text
refund
```

### Order Agent

The Order Agent has access to the order lookup tool:

```python
order_agent = create_agent(
    model=model,
    tools=[
        get_order_details
    ]
)
```

Its job is to retrieve information about an order when required.

## Tools

### `get_order_details`

The project contains a mock `get_order_details` tool.

It returns information about an order:

```python
{
    "discount": True,
    "status": "picked up",
    "amount": 750
}
```

The tool currently contains two sample orders.

## Deterministic Business Logic

The project intentionally separates business rules from LLM reasoning.

For example:

```python
def route_by_discount(state: AgentState):

    discount_applied = state["discount_applied"]

    if discount_applied:
        return "not eligible"

    return "eligible"
```

The LLM determines information such as:

```text
Was a discount applied?
```

Python determines the business decision:

```text
Can this order receive a refund?
```

This distinction is one of the key concepts demonstrated by the project.

## Example Orders

The application currently uses two hard-coded mock orders.

| Order ID | Status | Discount | Amount |
|----------|--------|----------|--------|
| 123      | picked up | Yes | 750 |
| 456      | preparing | No | 300 |

These orders are hard-coded for demonstration purposes.

## Example Flows

### Example 1 — Order Status

Input:

```text
What is the status of my order? The order id is 123
```

Flow:

```text
User Request
     |
     v
Intent Detection
     |
     | status
     v
Extract Order ID
     |
     v
Status Node
     |
     v
Order Agent
     |
     v
get_order_details
     |
     v
Final Response
     |
     v
END
```

### Example 2 — Refund With Discount

Input:

```text
I want a refund for order 123
```

Flow:

```text
User Request
     |
     v
Intent Detection
     |
     | refund
     v
Extract Order ID
     |
     v
Discount Node
     |
     v
get_order_details
     |
     v
Discount = True
     |
     v
Not Eligible
     |
     v
END
```

### Example 3 — Refund Without Discount

Input:

```text
I want a refund for order 456
```

Flow:

```text
User Request
     |
     v
Intent Detection
     |
     | refund
     v
Extract Order ID
     |
     v
Discount Node
     |
     v
get_order_details
     |
     v
Discount = False
     |
     v
Process Refund
     |
     v
END
```

## Project Structure

```text
langgraph-order-refund-assistant/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env
```

> `.env` should never be committed to GitHub.

## Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd langgraph-order-refund-assistant
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the `.env` File

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key
```

The application loads the API key using `python-dotenv`.

### 5. Configure `.gitignore`

Make sure `.gitignore` contains:

```text
.env
.venv/
__pycache__/
*.pyc
```

This prevents your API key and local virtual environment from being committed to GitHub.

### 6. Run the Application

```bash
python main.py
```

The application will execute the LangGraph workflow and print the final state.

## Technologies Used

- Python
- LangChain
- LangGraph
- Groq
- GPT-OSS 20B
- `TypedDict`
- `python-dotenv`

## Project Scope

This is a learning project, not a production-ready customer-support system.

The order database and refund processing are represented by mock Python functions.

There is currently:

- No production database
- No real payment gateway
- No authentication
- No persistent conversation history
- No production error handling
- No real order management system

The purpose of the project is to demonstrate LangGraph concepts.

## Key Takeaway

This project demonstrates the distinction between an AI agent and a workflow orchestrator.

The agents provide LLM-based capabilities such as:

- Understanding natural-language requests
- Extracting information
- Calling tools
- Generating responses

LangGraph provides explicit control over:

- State
- Nodes
- Workflow execution
- Conditional routing
- Branching
- Deterministic business rules

The overall architecture can be summarized as:

```text
                 LLM / Agents
                      |
                      | Reasoning
                      v
              +---------------+
              |   LangGraph   |
              |               |
              | State         |
              | Routing       |
              | Branching     |
              | Workflow      |
              +---------------+
                      |
                      v
             Business Actions
```

This project is intentionally simple and is meant to serve as a foundation for exploring more advanced LangGraph patterns.
