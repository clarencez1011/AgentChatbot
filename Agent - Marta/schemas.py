from typing import TypedDict, List, Dict, Optional

class AgentState(TypedDict):
    question: str           # 重写后的 Query
    original_question: str  # 原始 Query
    dense_vec: Optional[List[float]]
    documents: List[Dict]
    search_context: str
    generation: str
    route: str
    retrieval_quality: bool
    grade_status: str