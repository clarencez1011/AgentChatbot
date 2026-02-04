import json
from openai import AsyncOpenAI  # 👈 注意：导入 AsyncOpenAI
from config.settings import Config

class LLMService:
    def __init__(self):
        # 使用异步客户端
        self.client = AsyncOpenAI(api_key=Config.ALI_KEY, base_url=Config.LLM_BASE_URL)

    async def generate(self, system_prompt: str, user_prompt: str, temp: float = 0.2) -> str:
        try:
            # 注意 await
            response = await self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temp
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ [LLM Generate Error] {e}")
            raise e

    async def rewrite_query(self, text: str, prompt: str) -> str:
        try:
            # 注意 await
            response = await self.client.chat.completions.create(
                model=Config.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": prompt}, 
                    {"role": "user", "content": text}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ [LLM Rewrite Error] {e}")
            return text

    async def route_request(self, text: str, prompt: str) -> dict:
        try:
            # 注意 await
            response = await self.client.chat.completions.create(
                model=Config.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": prompt}, 
                    {"role": "user", "content": text}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ [LLM Route Error] {e}")
            return {"score": "yes"}

llm_service = LLMService()