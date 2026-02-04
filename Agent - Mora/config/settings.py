import os
from dotenv import load_dotenv

# 1. 加载 .env
load_dotenv(override=True)

# 2. 直接定义变量 (不要放在 class Config 里，这样 import 更方便)
PINECONE_KEY = os.getenv("PINECONE_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")
ALI_KEY = os.getenv("ALI_KEY", "")
TAVILY_KEY = os.getenv("TAVILY_KEY", "")

# 路径配置
INDEX_NAME = os.getenv("INDEX_NAME", "pinecone-study")
BM25_PATH = os.getenv("BM25_PATH", "/Users/clarence/Desktop/RAG项目/RAG Base/bm25_model.json")

# 阈值配置
try:
    TOP_K = int(os.getenv("TOP_K", "3"))
    SCORE_FLOOR = float(os.getenv("SCORE_FLOOR", "0.35"))
    MARGIN_FLOOR = float(os.getenv("MARGIN_FLOOR", "0.03"))
    HIGH_CONFIDENCE = float(os.getenv("HIGH_CONFIDENCE", "0.60"))
except ValueError:
    TOP_K = 5
    SCORE_FLOOR = 0.35
    MARGIN_FLOOR = 0.03
    HIGH_CONFIDENCE = 0.60

# 调试模式
ENABLE_DEBUG = os.getenv("ENABLE_DEBUG", "false").lower() == "true"

# 模型配置
EMBED_MODEL = "text-embedding-004"
REWRITE_MODEL = "qwen-plus"
LLM_MODEL = "qwen3-max"     
ROUTER_MODEL = "qwen-turbo" 
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 邮件配置
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# 为了兼容之前的 import Config 写法，我们在最后加这一行：
class Config:
    pass

# 把模块级别的变量动态绑定到 Config 类上，这样 Config.ALI_KEY 也能用！
# 这是一个为了兼容性的魔法操作
import sys
this_module = sys.modules[__name__]
for attr_name in dir(this_module):
    if not attr_name.startswith("_"):
        setattr(Config, attr_name, getattr(this_module, attr_name))