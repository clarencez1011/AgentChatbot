import jieba
import google.genai as genai
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from typing import List, Dict
from config.settings import Config

class VectorService:
    def __init__(self):
        self.google_client = genai.Client(api_key=Config.GEMINI_KEY)
        self.pc = Pinecone(api_key=Config.PINECONE_KEY)
        self.index = self.pc.Index(Config.INDEX_NAME)
        # 注意：这里需要确保路径存在，或者加个 try-except
        self.bm25 = BM25Encoder().load(Config.BM25_PATH)

    def embed_query(self, text: str) -> List[float]:
        res = self.google_client.models.embed_content(
            model=Config.EMBED_MODEL,
            contents=text.strip(),
            config={"task_type": "RETRIEVAL_QUERY"},
        )
        return res.embeddings[0].values

    def hybrid_search(self, text: str, dense_vec: List[float], top_k: int = 3) -> List[Dict]:
        sparse_query = " ".join(jieba.cut(text))
        sparse_output = self.bm25.encode_queries([sparse_query])
        sparse_vec = sparse_output[0] if isinstance(sparse_output, list) else sparse_output

        res = self.index.query(
            vector=dense_vec,
            sparse_vector=sparse_vec,
            top_k=top_k,
            include_metadata=True
        )
        return res.get("matches", [])

vec_service = VectorService()