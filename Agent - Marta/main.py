import asyncio
from graph.workflow import build_graph
from config import settings
from services.notification import notification_service # 👈

async def main():
    app = build_graph()
    
    print("\n" + "="*60)
    print("🚀 Mars IT Agent V4.0 (Async) | Rewrite -> RAG -> Grader -> Search")
    print("="*60)

    while True:
        try:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ["exit", "quit"]: break
            if not user_input: continue

            print("   (Processing...)")
            
            # 使用 await 异步调用
            final_state = await app.ainvoke({"question": user_input})
            
            print("-" * 60)
            print(f"🤖 Agent: {final_state['generation']}")
            print("-" * 60)
            
            # --- 🔥 这里保留了你的详细分数展示区 ---
            route = final_state.get('route', 'N/A')
            
            if route == "rag":
                print(f"   [🔍 RAG Retrieval Stats]")
                docs = final_state.get('documents', [])
                if docs:
                    for i, doc in enumerate(docs):
                        score = doc.get('score', 0.0)
                        name = doc.get('metadata', {}).get('name', 'Unknown Doc') 
                        marker = "⭐" if i == 0 else "  "
                        print(f"      {marker} Rank {i+1}: Score={score:.4f} | {name}")
                else:
                    print("      No documents retrieved.")
            
            # 门控状态
            quality = "PASS" if final_state.get('retrieval_quality') else "FAIL -> Search"
            print(f"   [DEBUG] Route: {route.upper()} | Gate Decision: {quality}")

        except Exception as e:
            # 🔥 捕获未知的致命错误
            print(f"\n❌ System Critical Error: {str(e)}")
            
            await notification_service.send_alert_async(
                module_name="Main Loop Crash",
                error_msg=str(e),
                detail="主程序循环发生未捕获异常，请立即查看日志。"
            )

if __name__ == "__main__":
    asyncio.run(main())