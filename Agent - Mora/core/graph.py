import asyncio
from typing import TypedDict, Annotated, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI  # 👈 确保导入这个

from config.settings import Config
from core.prompts import Prompts
from services.llm import llm_service
from tools.rag_tool import lookup_internal_knowledge
from tools.search_tool import search_internet

# 1. 定义 State
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    original_question: str

# ============================================================
# 2. 🔥 修复点：先定义 tools 列表，再绑定给 LLM
# ============================================================
tools = [lookup_internal_knowledge, search_internet]

# 3. 初始化 LLM 并绑定工具
llm = ChatOpenAI(
    model=Config.LLM_MODEL,
    api_key=Config.ALI_KEY,
    base_url=Config.LLM_BASE_URL,
    temperature=0
)

# 绑定工具 (现在 python 知道 tools 是什么了)
llm_with_tools = llm.bind_tools(tools)

# ============================================================
# 4. 定义节点 (Async)
# ============================================================

async def node_rewrite(state: AgentState):
    """预处理：优化用户问题"""
    messages = state["messages"]
    last_msg = messages[-1]
    raw_q = last_msg.content
    
    print(f"   [Rewriter] 原始问题: {raw_q}")
    
    # 异步调用重写
    new_q = await llm_service.rewrite_query(raw_q, Prompts.SYSTEM_REWRITE)
 
    
    # 更新消息内容
    last_msg.content = new_q
    return {"messages": [last_msg], "original_question": raw_q}

async def node_agent(state: AgentState):
    """Agent 大脑"""
    messages = state["messages"]
    
    # 注入 System Prompt
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=Prompts.SYSTEM_AGENT)] + messages
        
    # 异步调用 LLM
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """路由逻辑：决定是调工具还是结束"""
    messages = state["messages"]
    last_msg = messages[-1]
    
    if last_msg.tool_calls:
        return "tools"
    return "__end__"

# ============================================================
# 5. 构建图
# ============================================================

def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("rewrite", node_rewrite)
    workflow.add_node("agent", node_agent)
    workflow.add_node("tools", ToolNode(tools)) # 使用 LangGraph 自带的 ToolNode
    
    # 设置连线
    workflow.set_entry_point("rewrite")
    
    workflow.add_edge("rewrite", "agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
    )
    
    workflow.add_edge("tools", "agent") # 形成闭环：工具用完回 Agent
    
    return workflow.compile()