# services/search.py
from tavily import TavilyClient
from config.settings import Config

class SearchService:
    def __init__(self):
        self.client = TavilyClient(api_key=Config.TAVILY_KEY)

    def web_search(self, query: str) -> str:
        """
        执行搜索。如果 API 失败，直接抛出异常，由上层工具捕获并报警。
        """
        # 注意：这里去掉了 try-except，让错误向上冒泡
        response = self.client.search(query, search_depth="basic", max_results=3)
        
        results = response.get("results", [])
        if not results:
            return ""

        formatted_results = []
        for res in results:
            title = res.get("title", "No Title")
            url = res.get("url", "#")
            content = res.get("content", "No Content")
            formatted_results.append(f"来源: {title}\n链接: {url}\n摘要: {content}")
        
        return "\n\n".join(formatted_results)

search_service = SearchService()