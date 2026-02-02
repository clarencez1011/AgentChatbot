import json
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.ALI_KEY, 
            base_url=settings.LLM_BASE_URL
        )

    @retry(stop=stop_after_attempt(3))
    async def generate(self, system_prompt: str, user_prompt: str, temp: float = 0.2) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temp
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            raise e

    async def route_request(self, text: str, system_prompt: str) -> dict:
        """路由/分类专用"""
        try:
            response = await self.client.chat.completions.create(
                model=settings.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except:
            return {"type": "rag", "score": "yes"} # 兜底

    async def rewrite_query(self, text: str, system_prompt: str) -> str:
        """重写专用"""
        try:
            response = await self.client.chat.completions.create(
                model=settings.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except:
            return text

llm_service = LLMService()