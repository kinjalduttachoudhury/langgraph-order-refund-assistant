# LangGraph Order & Refund Assistant

A learning project demonstrating how LangGraph can orchestrate LLM-powered nodes, agents, tools, shared state, and conditional routing.

## What it does

The assistant handles two types of requests:

- Check the status of an order
- Request a refund for an order

The refund workflow applies a business rule:

- If a discount was applied to the order → refund is not eligible
- If no discount was applied → refund is processed

## Architecture

The workflow is built using LangGraph:

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

## LangGraph concepts demonstrated

- `StateGraph`
- Graph state using `TypedDict`
- Nodes
- Conditional edges
- Routing based on state
- `START` and `END`
- LLM agents inside graph nodes
- Tool calling
- Deterministic Python business logic
- Multiple workflow branches

## Agents

The project uses two agents:

### Intent Agent

Determines whether the user wants:

- `status`
- `refund`

It does not have any tools.

### Order Agent

Has access to the `get_order_details` tool and is used when order information needs to be retrieved.

## Example Orders

The demo contains two sample orders:

| Order ID | Status | Discount | Amount |
|----------|--------|----------|--------|
| 123 | picked up | Yes | 750 |
| 456 | preparing | No | 300 |

These are hard-coded mock orders for demonstration purposes.

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd langgraph-order-refund-assistant