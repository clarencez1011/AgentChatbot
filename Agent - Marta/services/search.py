import asyncio
from tavily import TavilyClient
from config import settings

class SearchService:
    def __init__(self):
        self.client = TavilyClient(api_key=settings.TAVILY_KEY)

    async def web_search_async(self, query: str):
        def _search():
            try:
                res = self.client.search(query, search_depth="basic", max_results=3)
                results = res.get("results", [])
                formatted = []
                for r in results:
                    formatted.append(f"来源: {r.get('title')}\n链接: {r.get('url')}\n摘要: {r.get('content')}")
                return "\n\n".join(formatted)
            except Exception as e:
                print(f"Search API Error: {e}")
                return "网络搜索失败。"
        
        return await asyncio.to_thread(_search)

search_service = SearchService()