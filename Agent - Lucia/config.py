import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# 自动计算 .env 的绝对路径（防止 "File Not Found"）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    # === 1. 核心密钥 (必须在 .env 中存在) ===
    ALI_KEY: str
    PINECONE_KEY: str
    GEMINI_KEY: str
    TAVILY_KEY: str

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SENDER_EMAIL: str = ""
    SENDER_PASSWORD: str = ""
    ADMIN_EMAIL: str = ""

    # === 2. 业务参数 (有默认值) ===
    INDEX_NAME: str = "pinecone-study"
    BM25_PATH: str = "/Users/clarence/Desktop/RAG项目/RAG Base/bm25_model.json"
    
    SCORE_FLOOR: float = 0.35
    HIGH_CONFIDENCE: float = 0.60
    MARGIN_FLOOR: float = 0.03
    TOP_K: int = 3
    
    LLM_MODEL: str = "qwen-max"
    ROUTER_MODEL: str = "qwen-turbo"
    EMBED_MODEL: str = "text-embedding-004"
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # === 3. 刚才报错缺失的字段 ===
    ENABLE_DEBUG: bool = False  # 如果 .env 里写 true，这里会自动变成 True

    # === 4. Pydantic V2 新版配置写法 ===
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,           # 强制读绝对路径
        env_file_encoding='utf-8',
        extra='ignore'               # 关键：忽略 .env 里多余的字段，防止报错！
    )

# 实例化
settings = Settings()

if __name__ == "__main__":
    print(f"✅ Config Loaded Successfully!")
    print(f"📂 Reading .env from: {ENV_PATH}")
    print(f"🔑 ALI_KEY: {settings.ALI_KEY[:5]}***")
    print(f"🐛 Debug Mode: {settings.ENABLE_DEBUG}")