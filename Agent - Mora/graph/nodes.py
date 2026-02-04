from schemas import AgentState
from config import settings
from services.llm import llm_service
from services.vector import vec_service
from services.search import search_service

# --- 移植你的 Prompts 类 ---
class Prompts:
    SYSTEM_REWRITE = """你是一个专业的 IT 搜索优化专家。你的任务是优化用户的输入，以便在 IT 知识库中进行检索。
    规则：
    1. 去除口语化词汇（如“那个”、“请问”、“救命啊”）。
    2. 提取核心关键词，补充隐含的主语（如将“连不上”改为“VPN连接失败”）。
    3. 转化为简练、专业的搜索短语。
    4. 【重要】如果用户是在闲聊（如“你好”、“谢谢”），请原封不动地返回原文，不要修改。
    直接输出优化后的文本，不要包含任何解释。"""

    SYSTEM_ROUTER = """你是一个智能意图分类助手。强制返回 JSON。
    分类标准：
    1. "rag": IT 故障、软件报错、账号问题、设备问题等业务问题。
    2. "chat": 闲聊、问候、无关话题。
    输出格式：{"type": "rag", "reason": "..."}"""

    SYSTEM_RAG = """你是玛氏中国 IT 支持助手。你必须严格基于【知识库】回答。"""
    USER_RAG = """【知识库】\n{context}\n\n【用户问题】\n{question}\n\n【任务】\n仅使用知识库步骤回答。"""

    SYSTEM_SEARCH = """你是玛氏中国 IT 支持助手。当前内部知识库没有相关记录，你正在参考外部互联网搜索结果来辅助用户。
    请整合搜索结果，给出一个清晰、有条理的解决方案。
    注意：必须在回答开头明确标注：“⚠️ 内部知识库未找到记录，以下是基于互联网搜索的建议，仅供参考：”"""
    USER_SEARCH = """【搜索结果】\n{context}\n\n【用户问题】\n{question}"""

    SYSTEM_CHAT = """你是玛氏中国 IT 支持助手。用户在闲聊，请简短友好回应。"""

    SYSTEM_GRADER = """你是一个严格的阅卷老师。评估 AI 生成的答案是否出现了“幻觉”。
    必须返回 JSON：{"score": "yes", "reason": "..."} 或 {"score": "no", "reason": "..."}"""

# --- Nodes 实现 (Async) ---

async def node_rewrite(state: AgentState):
    raw_q = state["question"]
    orig_q = state.get("original_question") or raw_q
    print(f"   [Rewrite] Original: {orig_q}")
    
    new_q = await llm_service.rewrite_query(orig_q, Prompts.SYSTEM_REWRITE)
    print(f"   [Rewrite] Optimized: {new_q}")
    
    return {"question": new_q, "original_question": orig_q}

async def node_router(state: AgentState):
    q = state["question"]
    decision = await llm_service.route_request(q, Prompts.SYSTEM_ROUTER)
    route_type = decision.get("type", "rag")
    print(f"   [Router] Decision: {route_type.upper()}")

    dense_vec = None
    if route_type == "rag":
        # 异步调用 embedding
        dense_vec = await vec_service.embed_query_async(q)
        
    return {"route": route_type, "dense_vec": dense_vec}

async def node_retriever(state: AgentState):
    docs = await vec_service.hybrid_search_async(
        state["question"], 
        state["dense_vec"], 
        top_k=settings.TOP_K
    )
    return {"documents": docs}

async def node_gate(state: AgentState):
    matches = state["documents"]
    
    if not matches:
        print("   [Gate] ❌ No documents retrieved.")
        return {"retrieval_quality": False}
    
    s1 = float(matches[0].get("score", 0.0))
    s2 = float(matches[1].get("score", 0.0)) if len(matches) > 1 else 0.0
    
    print(f"   [Gate] Top1: {s1:.4f} | Top2: {s2:.4f} | Margin: {s1-s2:.4f}")

    # 逻辑保持完全一致
    if s1 < settings.SCORE_FLOOR:
        print(f"   [Gate] 📉 Low Score ({s1:.4f} < {settings.SCORE_FLOOR}) -> Search")
        return {"retrieval_quality": False}
    
    if s1 >= settings.HIGH_CONFIDENCE:
        print(f"   [Gate] 🚀 High Confidence ({s1:.4f} >= {settings.HIGH_CONFIDENCE}) -> PASS")
        return {"retrieval_quality": True}

    if (s1 - s2) < settings.MARGIN_FLOOR:
        print(f"   [Gate] ⚠️ Ambiguous in Mid-Range -> Search")
        return {"retrieval_quality": False}
    
    print(f"   [Gate] ✅ Quality Check Passed")
    return {"retrieval_quality": True}

async def node_generate_rag(state: AgentState):
    blocks = [f"【故障场景】{m['metadata'].get('name')}\n【处理步骤】{m['metadata'].get('steps')}" for m in state["documents"]]
    context = "\n\n".join(blocks)
    
    user_p = Prompts.USER_RAG.format(context=context, question=state["question"])
    ans = await llm_service.generate(Prompts.SYSTEM_RAG, user_p)
    return {"generation": ans}

async def node_grader(state: AgentState):
    print("   [Grader] Checking for hallucinations...")
    answer = state["generation"]
    blocks = [m.get("metadata", {}).get("steps", "") for m in state["documents"]]
    context = "\n".join(blocks)
    
    user_content = f"【参考文档】\n{context}\n\n【生成答案】\n{answer}"
    grade = await llm_service.route_request(user_content, Prompts.SYSTEM_GRADER)
    score = grade.get("score", "yes")
    reason = grade.get("reason", "")
    
    if score == "yes":
        print(f"   [Grader] ✅ Approved. Reason: {reason}")
        return {"grade_status": "useful"}
    else:
        print(f"   [Grader] ❌ Hallucination detected. Reason: {reason}")
        print("   [Grader] 🔄 Falling back to Web Search...")
        return {"grade_status": "not_useful"}

async def node_web_search(state: AgentState):
    print(f"   [Search] Searching Tavily for: {state['question']}...")
    res = await search_service.web_search_async(state["question"])
    return {"search_context": res}

async def node_generate_search(state: AgentState):
    user_p = Prompts.USER_SEARCH.format(context=state["search_context"], question=state["question"])
    ans = await llm_service.generate(Prompts.SYSTEM_SEARCH, user_p)
    return {"generation": ans}

async def node_generate_chat(state: AgentState):
    ans = await llm_service.generate(Prompts.SYSTEM_CHAT, state["question"], temp=0.5)
    return {"generation": ans}