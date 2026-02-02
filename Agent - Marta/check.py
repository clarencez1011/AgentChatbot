import os
from dotenv import load_dotenv

print("="*40)
print("🕵️‍♂️ 环境变量侦探程序开始工作")
print("="*40)

# 1. 检查当前 Python 运行在哪里
current_dir = os.getcwd()
print(f"📍 Python 当前工作目录: {current_dir}")

# 2. 检查 .env 文件是否在当前目录下
expected_env_path = os.path.join(current_dir, ".env")
print(f"🔎 正在寻找文件: {expected_env_path}")

if os.path.exists(expected_env_path):
    print("✅ 文件存在！")
    
    # 3. 检查文件内容（只读取前几行，不打印完整 Key 防止泄露）
    try:
        with open(expected_env_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            lines = content.split('\n')
            print(f"📄 文件行数: {len(lines)}")
            print("👀 内容预览（前 3 行）:")
            for i, line in enumerate(lines[:3]):
                # 简单的脱敏打印
                if '=' in line:
                    key, val = line.split('=', 1)
                    masked_val = val[:4] + "****" if len(val) > 4 else "****"
                    print(f"   Line {i+1}: {key.strip()} = {masked_val}")
                else:
                    print(f"   Line {i+1}: {line} (格式可能不正确)")
    except Exception as e:
        print(f"❌ 文件存在但无法读取: {e}")
else:
    print("❌ 致命错误：找不到 .env 文件！")
    print("📂 当前目录下只有这些文件：")
    for file in os.listdir(current_dir):
        print(f"   - {file}")

print("-" * 40)

# 4. 尝试加载
print("🚀 尝试使用 python-dotenv 加载...")
loaded = load_dotenv(expected_env_path, override=True)
if loaded:
    print("✅ load_dotenv 返回 True (加载成功)")
else:
    print("❌ load_dotenv 返回 False (加载失败)")

# 5. 最终检查环境变量
print("-" * 40)
print("📊 最终检查环境变量 (os.environ):")
keys_to_check = ["ALI_KEY", "PINECONE_KEY", "GEMINI_KEY", "TAVILY_KEY"]
missing_keys = []

for key in keys_to_check:
    value = os.getenv(key)
    if value:
        print(f"   ✅ {key}: 已获取 (长度 {len(value)})")
    else:
        print(f"   ❌ {key}: 未找到")
        missing_keys.append(key)

print("="*40)
if not missing_keys:
    print("🎉 恭喜！环境配置完全正常。")
else:
    print(f"⚠️ 仍然缺失: {missing_keys}")
    print("建议：检查 .env 中的变量名是否拼写正确（大小写敏感）。")