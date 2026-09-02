from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from psycopg_pool import AsyncConnectionPool
from agent.tools.policy_rag import lookup_policy
from agent.tools.order_tools import get_my_orders, get_order_status, cancel_order
from core.config import settings
from schemas import AgentState

tools = [lookup_policy, get_my_orders, get_order_status, cancel_order]
tool_node = ToolNode(tools)

model = ChatGoogleGenerativeAI(
    model=settings.GOOGLE_MODEL,
    api_key=settings.GOOGLE_API_KEY
).bind_tools(tools)

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

def call_model(state: AgentState):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

# Set up Async Connection Pool
pool = AsyncConnectionPool(
    conninfo=settings.POSTGRES_CHECKPOINT_URL,
    max_size=10,
    open=False,
    kwargs={"autocommit": True}
)

checkpointer = AsyncPostgresSaver(pool)
agent_graph = workflow.compile(checkpointer=checkpointer)