from langgraph.graph import StateGraph, END
from schemas import AgentState
from graph.nodes import *

def build_graph():
    workflow = StateGraph(AgentState)
    
    # 1. 注册节点
    workflow.add_node("rewrite", node_rewrite)
    workflow.add_node("router", node_router)
    workflow.add_node("retriever", node_retriever)
    workflow.add_node("gate", node_gate)
    workflow.add_node("rag_gen", node_generate_rag)
    workflow.add_node("grader", node_grader)
    workflow.add_node("web_search", node_web_search)
    workflow.add_node("search_gen", node_generate_search)
    workflow.add_node("chat_gen", node_generate_chat)

    # 2. 设置连线
    workflow.set_entry_point("rewrite")
    workflow.add_edge("rewrite", "router")
    
    workflow.add_conditional_edges(
        "router",
        lambda x: x["route"],
        {"rag": "retriever", "chat": "chat_gen"}
    )
    
    workflow.add_edge("retriever", "gate")
    
    workflow.add_conditional_edges(
        "gate",
        lambda x: "good" if x["retrieval_quality"] else "bad",
        {"good": "rag_gen", "bad": "web_search"}
    )
    
    workflow.add_edge("rag_gen", "grader")
    
    workflow.add_conditional_edges(
        "grader",
        lambda x: x["grade_status"],
        {"useful": END, "not_useful": "web_search"}
    )
    
    workflow.add_edge("web_search", "search_gen")
    workflow.add_edge("search_gen", END)
    workflow.add_edge("chat_gen", END)
    
    return workflow.compile()