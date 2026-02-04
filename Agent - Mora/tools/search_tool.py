# tools/search_tool.py
from langchain_core.tools import tool
from services.search import search_service
from services.notification import notification_service # 👈 引入报警
import traceback

@tool
def search_internet(query: str) -> str:
    """
    当内部知识库(lookup_internal_knowledge)无法解决问题，或者用户明确要求查询外部信息时调用。
    用于查询互联网上的最新技术文档、解决方案或新闻。
    """
    print(f"\n🌍 [Tool Call] Web Search: {query}")
    
    try:
        # 1. 调用搜索服务
        result = search_service.web_search(query)
        
        # 2. 处理空结果
        if not result:
            print("   [Search] 0 results found.")
            return "【搜索无结果】Tavily 未返回相关信息，请尝试更换关键词。"
            
        print(f"   [Search] Success. Result length: {len(result)}")
        return f"【互联网搜索结果】\n{result}"

    except Exception as e:
        error_str = str(e)
        print(f"❌ [Search Failed] {error_str}")
        
        # 🔥 3. 触发报警 (核心部分)
        # 搜索挂了通常意味着 API Key 额度用完，或者 Tavily 服务宕机，必须要知道
        notification_service.send_alert(
            module_name="Search_Tool_Tavily",
            error_msg=error_str,
            detail=f"Query: {query}\nTraceback:\n{traceback.format_exc()}"
        )
        
        # 4. 优雅降级
        # 告诉 Agent 发生了什么，让它不要胡说八道，而是诚实告诉用户
        return "【外部搜索故障】搜索服务暂时不可用（API 连接失败），管理员已收到自动报警。请稍后再试。"