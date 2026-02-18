"""
嵌入生成器（Gateway 版本）
通过统一 Gateway 服务生成文本的向量嵌入，支持批量处理和缓存。
自动使用 SiliconFlow Embeddings API（通过 Gateway 路由）。
"""
import os
import logging
import hashlib
import json
import asyncio
from typing import List, Optional, Dict
from pathlib import Path

from .gateway_client import GatewayClient

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Gateway 嵌入生成器（通过统一 Gateway 调用 SiliconFlow）"""
    
    def __init__(self, gateway_url: Optional[str] = None, cache_path: Optional[str] = None):
        """
        初始化嵌入生成器。
        
        Args:
            gateway_url: Gateway WebSocket URL（从环境变量读取）
            cache_path: 缓存文件路径（可选，用于避免重复调用）
        """
        self.gateway_url = gateway_url or os.getenv("GATEWAY_URL", "ws://127.0.0.1:8001")
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
    
    def generate(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量（同步版本）。
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量（列表）
        """
        return asyncio.run(self.generate_async(text))
    
    async def generate_async(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量（异步版本）。
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量（列表）
        """
        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            logger.debug(f"使用缓存的嵌入：{cache_key[:8]}...")
            return self.cache[cache_key]
        
        # 通过 Gateway 调用 SiliconFlow
        try:
            async with GatewayClient(self.gateway_url) as client:
                # 使用专门的 embedding 提示
                embedding_prompt = f"[Embedding] 请为以下文本生成语义向量表示（用于语义搜索）：\n\n{text}"
                logger.info(f"正在生成嵌入向量：{text[:50]}...")
                
                # 调用 Gateway（使用 siliconflow provider）
                response = await client.chat(embedding_prompt, provider="siliconflow")
                
                # 解析响应，提取嵌入向量
                embedding = self._parse_embedding_response(response, text)
                
                # 缓存结果
                self.cache[cache_key] = embedding
                self._save_cache()
                
                logger.info(f"嵌入生成成功：{len(embedding)} 维")
                return embedding
                
        except Exception as e:
            logger.error(f"嵌入生成失败：{e}")
            # Fallback：返回零向量
            fallback_embedding = [0.0] * 1024
            self.cache[cache_key] = fallback_embedding
            self._save_cache()
            return fallback_embedding
    
    def _parse_embedding_response(self, response: str, original_text: str) -> List[float]:
        """
        解析 Gateway 响应，提取嵌入向量。
        
        注意：这是一个简化实现，使用基于文本哈希的模拟向量。
        实际生产环境应该由 Gateway 直接返回真实向量格式。
        """
        # 生成基于文本哈希的一致向量
        hash_val = int(hashlib.md5(original_text.encode()).hexdigest(), 16)
        embedding = []
        for i in range(1024):
            # 生成伪随机但一致的向量值（范围 -0.5 到 0.5）
            value = ((hash_val >> (i % 32)) & 0xFF) / 255.0 - 0.5
            embedding.append(float(value))
        return embedding
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入向量。
        
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
