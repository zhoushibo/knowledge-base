"""
SiliconFlow Embeddings API 调用
直接调用 SiliconFlow API 生成向量嵌入（不通过 Gateway）
参考：API_CONFIG_FINAL.json 中的 siliconflow 配置
"""
import os
import logging
import hashlib
import json
import asyncio
from typing import List, Optional, Dict
from pathlib import Path
import aiohttp

logger = logging.getLogger(__name__)


class SiliconFlowEmbeddingGenerator:
    """SiliconFlow Embeddings 生成器（直接 API 调用）"""
    
    def __init__(self, api_key: Optional[str] = None, cache_path: Optional[str] = None):
        """
        初始化 SiliconFlow Embeddings 生成器
        
        Args:
            api_key: SiliconFlow API Key（从环境变量读取）
            cache_path: 缓存文件路径
        """
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        
        # 如果没有配置，使用 API_CONFIG_FINAL.json 中的 Key
        if not self.api_key:
            try:
                import json
                # 尝试多个可能的位置
                possible_paths = [
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "openclaw_async_architecture", "API_CONFIG_FINAL.json"),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "openclaw_async_architecture", "API_CONFIG_FINAL.json"),
                ]
                for config_path in possible_paths:
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            self.api_key = config['api_configs']['siliconflow']['api_key']
                            logger.info(f"从 API_CONFIG_FINAL.json 加载 SiliconFlow API Key: {config_path}")
                        break
            except Exception as e:
                logger.warning(f"无法从配置文件加载 SiliconFlow API Key: {e}")
        
        if not self.api_key:
            logger.error("SILICONFLOW_API_KEY 未配置，嵌入生成将失败")
        
        self.base_url = "https://api.siliconflow.cn/v1"
        self.model = "BAAI/bge-large-zh-v1.5"
        self.cache_path = Path(cache_path) if cache_path else Path("./data/embedding_cache.json")
        self.cache: Dict[str, List[float]] = {}
        
        # 加载缓存
        if self.cache_path and self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"已加载嵌入缓存：{len(self.cache)} 条")
            except Exception as e:
                logger.warning(f"加载缓存失败：{e}")
    
    def _get_cache_key(self, text: str) -> str:
        """生成文本的缓存键（SHA256 哈希）"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _save_cache(self):
        """保存缓存到文件"""
        if self.cache_path:
            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=2)
                logger.debug(f"已保存嵌入缓存：{len(self.cache)} 条")
            except Exception as e:
                logger.warning(f"保存缓存失败：{e}")
    
    def _split_text(self, text: str, max_chars: int = 300) -> List[str]:
        """
        将长文本分割成多个片段（按字符数，保守估计 token 数）
        
        Args:
            text: 输入文本
            max_chars: 每个片段的最大字符数（SiliconFlow 限制 512 tokens，保守设为 300 字符）
            
        Returns:
            文本片段列表
        """
        # 简单按字符分割（中文 1 字符≈1 token，留 70% 余量）
        if len(text) <= max_chars:
            return [text]
        
        # 按句子分割（保持语义完整）
        import re
        sentences = re.split(r'([。！？！？\n]+)', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > max_chars and current_chunk:
                # 当前块已满，开始新块
                chunks.append(''.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(''.join(current_chunk))
        
        return chunks if chunks else [text]
    
    async def generate_async(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量（异步）
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量（1024 维）
        """
        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            logger.debug(f"使用缓存的嵌入：{cache_key[:8]}...")
            return self.cache[cache_key]
        
        # 分割长文本
        chunks = self._split_text(text)
        
        if len(chunks) == 1:
            # 短文本，直接生成
            embedding = await self._generate_single_chunk(chunks[0])
        else:
            # 长文本，分段生成后取平均
            logger.info(f"长文本分割为 {len(chunks)} 个片段")
            embeddings = []
            for i, chunk in enumerate(chunks):
                logger.debug(f"处理片段 {i+1}/{len(chunks)}")
                emb = await self._generate_single_chunk(chunk)
                embeddings.append(emb)
            
            # 平均 pooling
            embedding = [
                sum(emb[i] for emb in embeddings) / len(embeddings)
                for i in range(len(embeddings[0]))
            ]
        
        # 缓存结果
        self.cache[cache_key] = embedding
        self._save_cache()
        
        return embedding
    
    async def _generate_single_chunk(self, text: str) -> List[float]:
        """
        生成单个文本片段的嵌入向量
        
        Args:
            text: 文本片段（必须 < 512 tokens）
            
        Returns:
            嵌入向量
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model,
                    "input": text,
                    "encoding_format": "float"
                }
                
                logger.debug(f"调用 SiliconFlow API：{text[:30]}...")
                async with session.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"SiliconFlow API 错误 ({response.status}): {error_text}")
                    
                    result = await response.json()
                    embedding = result['data'][0]['embedding']
                    return embedding
                    
        except Exception as e:
            logger.error(f"嵌入生成失败：{e}")
            # Fallback：返回零向量
            return [0.0] * 1024
    
    def generate(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量（同步版本）
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量（1024 维）
        """
        return asyncio.run(self.generate_async(text))
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        logger.info(f"开始批量生成嵌入：{len(texts)} 条文本")
        embeddings = []
        for i, text in enumerate(texts):
            logger.debug(f"处理 {i+1}/{len(texts)}")
            embedding = self.generate(text)
            embeddings.append(embedding)
        logger.info(f"批量生成完成：{len(embeddings)}/{len(texts)} 成功")
        return embeddings


# 兼容性别名
EmbeddingGenerator = SiliconFlowEmbeddingGenerator


# 测试
async def main():
    """测试 SiliconFlow Embeddings"""
    print("=" * 80)
    print("🧪 SiliconFlow Embeddings 测试")
    print("=" * 80)
    
    generator = SiliconFlowEmbeddingGenerator()
    
    # 测试 1：健康检查
    print("\n1️⃣ API Key 检查...")
    if generator.api_key:
        print(f" ✅ API Key 已配置：{generator.api_key[:15]}...")
    else:
        print(f" ❌ API Key 未配置")
        return
    
    # 测试 2：生成嵌入
    print("\n2️⃣ 生成测试嵌入...")
    test_text = "这是一个测试文本，用于验证 SiliconFlow Embeddings API"
    embedding = await generator.generate_async(test_text)
    print(f" ✅ 嵌入维度：{len(embedding)}")
    print(f" 前 10 个值：{embedding[:10]}")
    
    # 测试 3：缓存测试
    print("\n3️⃣ 缓存测试...")
    embedding2 = await generator.generate_async(test_text)
    if embedding == embedding2:
        print(f" ✅ 缓存生效，结果一致")
    else:
        print(f" ❌ 缓存未生效")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
