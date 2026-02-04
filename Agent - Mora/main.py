import asyncio
import traceback
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from core.graph import build_agent_graph
from services.notification import notification_service

# --- 辅助函数：美化打印 ---
def print_step(title, content, color="white"):
    print("\n" + "="*60)
    print(f"🧩 [NODE: {title.upper()}]")
    print("-" * 60)
    print(content)
    print("=" * 60 + "\n")

async def main():
    print("正在初始化 Agent (Debug Mode)...")
    app = build_agent_graph()
    
    print("\n" + "#"*60)
    print("🚀 Mars IT Agent | 全链路监控模式")
    print("#"*60)

    config = {"configurable": {"thread_id": "debug_user_1"}}

    while True:
        try:
            user_input = input("\n👤 User: ").strip()
            if user_input.lower() in ["exit", "quit"]: break
            if not user_input: continue

            # 构造输入
            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            # 🔥 核心监控循环
            async for event in app.astream(inputs, config=config):
                
                # event 是一个字典，key 是节点名，value 是该节点更新的状态
                for node_name, state_update in event.items():
                    
                    # 1. 监控 [Rewrite] 节点
                    if node_name == "rewrite":
                        msgs = state_update.get("messages", [])
                        if msgs:
                            original = state_update.get("original_question", "N/A")
                            rewritten = msgs[-1].content
                            print_step("REWRITE", 
                                       f"📥 原始输入: {original}\n"
                                       f"📤 优化输出: {rewritten}")

                    # 2. 监控 [Agent] 节点 (最关键的决策点)
                    elif node_name == "agent":
                        msg = state_update["messages"][0]
                        
                        # 情况 A: Agent 决定调用工具
                        if msg.tool_calls:
                            calls_info = []
                            for t in msg.tool_calls:
                                args_str = json.dumps(t['args'], ensure_ascii=False)
                                calls_info.append(f"🛠️ 调用的工具: {t['name']}\n⚙️ 传入的参数: {args_str}")
                            
                            print_step("AGENT (THINKING)", 
                                       f"🤔 思考结果: 需要获取更多信息。\n" + "\n".join(calls_info))
                        
                        # 情况 B: Agent 决定直接回答 (没有工具调用)
                        else:
                            print_step("AGENT (FINAL ANSWER)", 
                                       f"💡 思考结果: 信息充足，准备输出。\n"
                                       f"🗣️ 回复内容: {msg.content}")

                    # 3. 监控 [Tools] 节点 (工具执行结果)
                    elif node_name == "tools":
                        msgs = state_update.get("messages", [])
                        tool_outputs = []
                        for m in msgs:
                            if isinstance(m, ToolMessage):
                                # 截取前200个字符防止刷屏，想看全量可以去掉切片
                                content_preview = m.content[:300] + "..." if len(m.content) > 300 else m.content
                                tool_outputs.append(f"📦 工具({m.name}) 返回:\n{content_preview}")
                        
                        print_step("TOOLS OUTPUT", "\n\n".join(tool_outputs))

        except KeyboardInterrupt:
            break
        except Exception as e:
            err_str = str(e)
            print(f"\n❌ [CRITICAL ERROR]: {err_str}")
            print(traceback.format_exc())
            await notification_service.send_alert_async("Main_Loop", err_str, traceback.format_exc())
            continue 

if __name__ == "__main__":
    asyncio.run(main())