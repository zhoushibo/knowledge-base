"""测试 SiliconFlow Embeddings"""
import asyncio
from core.embedding_generator import SiliconFlowEmbeddingGenerator

async def main():
    print("=" * 80)
    print("🧪 SiliconFlow Embeddings 测试")
    print("=" * 80)
    
    g = SiliconFlowEmbeddingGenerator()
    
    print("\n1️⃣ API Key 检查...")
    if g.api_key:
        print(f" ✅ API Key: {g.api_key[:15]}...")
    else:
        print(f" ❌ API Key 未配置")
        return
    
    print("\n2️⃣ 生成嵌入...")
    emb = await g.generate_async("这是一个测试")
    print(f" ✅ 维度：{len(emb)}")
    print(f" 前 10 值：{emb[:10]}")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
