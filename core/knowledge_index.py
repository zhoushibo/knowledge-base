"""
知识索引模块

使用 ChromaDB 构建向量索引，支持嵌入生成和向量存储。
"""

import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)


class KnowledgeIndex:
    """知识索引器"""
    
    def __init__(self, chroma_path: Optional[str] = None, collection_name: str = "knowledge"):
        """
        初始化知识索引器。
        
        Args:
            chroma_path: ChromaDB 数据路径（None 表示内存模式）
            collection_name: 集合名称
        """
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        # 延迟初始化，避免依赖缺失时报错
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保初始化（延迟加载）"""
        if self._initialized:
            return
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 初始化客户端
            if self.chroma_path:
                os.makedirs(self.chroma_path, exist_ok=True)
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.chroma_path
                ))
            else:
                self.client = chromadb.Client()
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "知识库向量索引"}
            )
            
            self._initialized = True
            logger.info(f"ChromaDB 初始化成功：{self.collection_name}")
            
        except ImportError as e:
            logger.error(f"ChromaDB 未安装：{e}")
            raise RuntimeError("请安装 chromadb: pip install chromadb")
        except Exception as e:
            logger.error(f"ChromaDB 初始化失败：{e}")
            raise
    
    def add_documents(self, documents: List[Dict], embeddings: Optional[List[List[float]]] = None) -> int:
        """
        添加文档到索引。
        
        Args:
            documents: 文档列表（包含 content 和 metadata）
            embeddings: 预计算的嵌入向量（None 表示自动计算）
            
        Returns:
            添加的文档数量
        """
        self._ensure_initialized()
        
        if not documents:
            return 0
        
        # 提取内容、元数据和 ID
        ids = [f"doc_{i}" for i in range(len(documents))]
        contents = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        # 如果没有提供嵌入，记录日志（实际应由外部计算）
        if embeddings is None:
            logger.warning("未提供嵌入向量，需要外部计算后添加")
            # 简化版本：实际应该调用嵌入生成 API
            # 这里仅存储文档，不存储向量
            self.collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=ids
            )
        else:
            self.collection.add(
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
                ids=ids
            )
        
        logger.info(f"添加 {len(documents)} 个文档到索引")
        return len(documents)
    
    def search(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """
        向量搜索。
        
        Args:
            query_embedding: 查询嵌入向量
            limit: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        self._ensure_initialized()
        
        # 限制最大返回数量
        limit = min(limit, 100)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        # 格式化结果
        formatted_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                item = {
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                }
                formatted_results.append(item)
        
        return formatted_results
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        self._ensure_initialized()
        
        return {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "chroma_path": self.chroma_path or "memory"
        }
