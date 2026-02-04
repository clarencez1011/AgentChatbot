from langchain_core.tools import tool
from config.settings import Config
from core.prompts import Prompts
from services.vector import vec_service
from services.llm import llm_service
from services.notification import notification_service
# 引入刚才写的服务
from services.rerank import rerank_service 

@tool
async def lookup_internal_knowledge(query: str) -> str:
    """
    当需要回答公司内部IT故障、软件报错、账号问题、政策流程时，必须调用此工具。
    输入query应该是具体的故障描述。
    """
    print(f"\n⚙️ [Tool Call] RAG Search: {query}")
    
    # ---------------------------------------------------
    # 1. 粗排 (Recall) - 把网撒大一点
    # ---------------------------------------------------
    try:
        # 假设 top_k 设为 50，确保包含正确答案
        dense_vec = vec_service.embed_query(query)
        # 注意：这里我们拿 50 条，给重排序模型去挑
        rough_docs = vec_service.hybrid_search(query, dense_vec, top_k=50)
    except Exception as e:
        error_msg = f"Vector DB Error: {str(e)}"
        print(f"❌ {error_msg}")
        notification_service.send_alert("RAG_Retrieval", error_msg, f"Query: {query}")
        return "【系统故障】知识库检索服务不可用。"

    if not rough_docs:
        return "【无结果】知识库中未找到相关文档。"

    print(f"\n🔍 [DEBUG] 混合检索原始 Top 10 (Before Rerank):")
    for i, doc in enumerate(rough_docs[:20]):
        # 注意：这里的 score 是向量相似度 (如 0.75) 或 BM25 分数 (如 12.5)
        raw_score = doc.get("score", 0.0)
        name = doc.get("metadata", {}).get("name", "未命名文档")
        print(f"  -> Rank {i+1}: {name} (Raw Score: {raw_score:.4f})")
    print("-" * 50)

    # ---------------------------------------------------
    # 2. 精排 (Rerank) - BGE 登场
    # ---------------------------------------------------
    try:
        # 这里的 Config.TOP_K 依然是你最终想给 LLM 看的数量 (比如 5)
        final_docs = await rerank_service.rerank(query, rough_docs, top_k=Config.TOP_K)
        print(f"   [Rerank] {len(rough_docs)} -> {len(final_docs)} docs sorted by BGE.")
    except Exception as e:
        print(f"⚠️ Rerank Error: {e}, fallback to top {Config.TOP_K} raw results.")
        # 降级策略：如果显存爆了或者报错，直接截取粗排结果
        final_docs = rough_docs[:Config.TOP_K]

    # ---------------------------------------------------
    # 3. 结果展示与门控
    # ---------------------------------------------------
    source_info_list = []
    for i, doc in enumerate(final_docs):
        score = doc.get("score", 0.0)
        name = doc.get("metadata", {}).get("name", "Unknown")
        # 打印 BGE 打分结果
        source_info_list.append(f"[{i+1}] {name} (BGE Score: {score:.4f})")
    
    source_display_str = "\n".join(source_info_list)
    print(f"   [Sources]\n{source_display_str}")

    # BGE 的 Sigmoid 分数通常非常两极分化
    # 相关的一般 > 0.8，不相关的一般 < 0.1
    # 建议 Config.SCORE_FLOOR 设为 0.35 左右比较安全
    if not final_docs or float(final_docs[0]['score']) < Config.SCORE_FLOOR:
         return f"【无结果】文档相关度不足 (最高分: {final_docs[0]['score']:.2f})。\n\n📊 **参考文档：**\n{source_display_str}"

    # ---------------------------------------------------
    # 4. 生成 (Generation)
    # ---------------------------------------------------
    blocks = []
    for m in final_docs:
        meta = m.get("metadata", {})
        blocks.append(f"【故障场景】{meta.get('name')}\n【处理步骤】{meta.get('steps')}")
    context = "\n\n".join(blocks)
    
    try:
        user_p = Prompts.USER_RAG.format(context=context, question=query)
        answer = await llm_service.generate(Prompts.SYSTEM_RAG, user_p)
    except Exception as e:
        return "【生成故障】答案生成失败。"

    # 5. 阅卷
    grade = await llm_service.route_request(
        f"【文档】\n{context}\n\n【答案】\n{answer}", 
        Prompts.SYSTEM_GRADER
    )
    
    final_output = f"{answer}\n\n----------------\n📊 **BGE精选来源：**\n{source_display_str}"

    if grade.get("score") == "yes":
        return f"【知识库结果】\n{final_output}"
    else:
        return f"【幻觉警告】生成的回答可能不准确。\n{final_output}"