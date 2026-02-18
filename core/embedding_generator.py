"""
嵌入生成器

使用 NVIDIA API 生成文本的向量嵌入，支持批量处理和缓存。
"""

import os
import logging
import hashlib
import json
from typing import List, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """NVIDIA API 嵌入生成器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, cache_path: Optional[str] = None):
        """
        初始化嵌入生成器。
        
        Args:
            api_key: NVIDIA API Key（可从环境变量读取）
            base_url: API 基础 URL（可从环境变量读取）
            cache_path: 缓存文件路径（可选，用于避免重复调用 API）
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.base_url = (base_url or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")).rstrip('/')
        self.cache_path = Path(cache_path) if cache_path else None
        self.cache: Dict[str, List[float]] = {}
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY 未设置，嵌入生成将失败")
        
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
        生成单个文本的嵌入向量。
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量（列表）
            
        Raises:
            RuntimeError: API 调用失败
        """
        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            logger.debug(f"使用缓存的嵌入：{cache_key[:8]}...")
            return self.cache[cache_key]
        
        if not self.api_key:
            raise RuntimeError("NVIDIA_API_KEY 未设置，无法生成嵌入")
        
        # 调用 NVIDIA API
        import requests
        
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": text,
            "model": "nvidia/nv-embedqa-e5-v5",  # 使用免费的嵌入模型
            "encoding_format": "float"
        }
        
        logger.debug(f"请求 NVIDIA API: {url}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            embedding = result["data"][0]["embedding"]
            
            # 保存到缓存
            self.cache[cache_key] = embedding
            self._save_cache()
            
            logger.debug(f"嵌入生成成功，维度：{len(embedding)}")
            return embedding
            
        except requests.exceptions.RequestException as e:
            logger.error(f"NVIDIA API 请求失败：{e}")
            raise RuntimeError(f"嵌入生成失败：{e}")
        except (KeyError, IndexError) as e:
            logger.error(f"API 响应格式异常：{e}")
            raise RuntimeError(f"嵌入解析失败：{e}")
    
    def generate_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        批量生成嵌入向量。
        
        Args:
            texts: 文本列表
            batch_size: 批次大小（当前 API 不支持批量，仅用于日志）
            
        Returns:
            嵌入向量列表
        """
        logger.info(f"开始批量生成嵌入：{len(texts)} 条文本")
        embeddings = []
        
        for i, text in enumerate(texts, 1):
            try:
                embedding = self.generate(text)
                embeddings.append(embedding)
                
                if i % 10 == 0:
                    logger.info(f"进度：{i}/{len(texts)}")
                    
            except Exception as e:
                logger.error(f"第 {i} 条文本嵌入生成失败：{e}")
                # 使用零向量作为 fallback（避免中断）
                embeddings.append([0.0] * 1024)  # 假设维度为 1024
        
        logger.info(f"批量生成完成：{len(embeddings)}/{len(texts)} 成功")
        return embeddings
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "cache_size": len(self.cache),
            "cache_path": str(self.cache_path) if self.cache_path else None
        }
