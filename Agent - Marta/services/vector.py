import asyncio
import jieba
import google.genai as genai
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from config import settings
from services.notification import notification_service

class VectorService:
    def __init__(self):
        self.google_client = genai.Client(api_key=settings.GEMINI_KEY)
        self.pc = Pinecone(api_key=settings.PINECONE_KEY)
        self.index = self.pc.Index(settings.INDEX_NAME)
        # 加载 BM25 可能比较慢，实际生产中建议预加载
        self.bm25 = BM25Encoder().load(settings.BM25_PATH)

    def _embed_sync(self, text: str):
        res = self.google_client.models.embed_content(
            model=settings.EMBED_MODEL,
            contents=text.strip(),
            config={"task_type": "RETRIEVAL_QUERY"},
        )
        return res.embeddings[0].values

    async def embed_query_async(self, text: str):
        try:
            return await asyncio.to_thread(self._embed_sync, text)
        except Exception as e:
            print(f"⚠️ [Embedding Fail] Gemini Error: {e} -> 降级处理")
            
            # 🔥 核心修改：触发报警
            # 我们不需要 await 它完成，create_task 会让它在后台跑
            await notification_service.send_alert_async(
                module_name="Gemini Embedding API", 
                error_msg=str(e),
                detail=f"Query Text: {text[:100]}..."
            )
            
            return None

    async def hybrid_search_async(self, text, dense_vec, top_k=3):
        if dense_vec is None:
            # 这里其实是上一步导致的，可以不报警，或者报一个 Info 级别
            return [] 

        try:
            return await asyncio.to_thread(self._hybrid_search_sync, text, dense_vec, top_k)
        except Exception as e:
            print(f"⚠️ [Pinecone Fail] Search Error: {e} -> 降级为 Web Search")
            
            # 🔥 核心修改：触发报警
            await notification_service.send_alert_async(
                module_name="Pinecone Vector DB", 
                error_msg=str(e),
                detail=f"Query: {text}"
            )
            
            return []

vec_service = VectorService()