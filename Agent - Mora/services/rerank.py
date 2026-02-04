import torch
import numpy as np
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any

class RerankService:
    def __init__(self):
        # 💡 使用 BGE v1.5 模型，这是目前最推荐的版本
        # 如果显存不够 (小于 4GB)，可以将 large 改为 base: "BAAI/bge-reranker-v1.5-base"
        self.model_name = "BAAI/bge-reranker-base"
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 [Rerank] Loading model: {self.model_name} on {self.device}...")
        
        # max_length=512 是 BGE 的标准窗口，超过会自动截断
        self.model = CrossEncoder(self.model_name, max_length=512, device=self.device)
        print("✅ [Rerank] Model loaded successfully.")

    def _sigmoid(self, x):
        """将 Logits 转换为 0~1 的概率值，方便做阈值过滤"""
        return 1 / (1 + np.exp(-x))

    async def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        执行重排序
        :param query: 用户问题
        :param docs: 粗排文档列表
        :param top_k: 最终保留数量
        """
        if not docs:
            return []

        # 1. 准备模型输入对 [Query, Document Content]
        pairs = []
        for doc in docs:
            meta = doc.get("metadata", {})
            
            # 1. 取出各个字段
            name = meta.get("name", "未知标题")
            steps = meta.get("steps", "")
            
            # 2. 🔥 核心修改：把它们拼在一起！
            # 建议格式： "标题: {name} \n 内容: {steps}"
            # 这样模型既看到了场景，又看到了方案
            rich_content = f"场景标题：{name}\n详细步骤：{steps}"
            
            # 3. 传入模型
            pairs.append([query, rich_content])

        # 2. 推理 (Predict)
        # BGE 返回的是 logits
        scores = self.model.predict(pairs)

        # 3. 如果只有 1 个文档，scores 可能是 scalar，需要转一下
        if len(docs) == 1:
            scores = [scores]

        # 4. 回写分数并归一化
        for i, doc in enumerate(docs):
            # 使用 Sigmoid 归一化，使其变成 0.95, 0.12 这种可读分数
            norm_score = float(self._sigmoid(scores[i]))
            doc['score'] = norm_score

        # 5. 排序：按分数从高到低
        ranked_docs = sorted(docs, key=lambda x: x['score'], reverse=True)

        # 6. 截取 Top K
        return ranked_docs[:top_k]

# 单例导出
rerank_service = RerankService()