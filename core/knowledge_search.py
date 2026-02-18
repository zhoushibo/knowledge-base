"""
知识搜索模块

混合语义搜索和关键词搜索，支持优雅降级。
"""

import logging
from typing import List, Dict, Optional
from .knowledge_index import KnowledgeIndex

logger = logging.getLogger(__name__)


class KnowledgeSearch:
    """知识搜索器"""
    
    def __init__(self, index: KnowledgeIndex, sqlite_path: Optional[str] = None):
        """
        初始化知识搜索器。
        
        Args:
            index: 知识索引器实例
            sqlite_path: SQLite 数据库路径（用于关键词搜索）
        """
        self.index = index
        self.sqlite_path = sqlite_path
        self.sqlite_conn = None
    
    def search(self, query: str, query_embedding: Optional[List[float]] = None, 
               limit: int = 10, use_hybrid: bool = True) -> List[Dict]:
        """
        搜索知识。
        
        Args:
            query: 搜索查询
            query_embedding: 查询嵌入向量（语义搜索必需）
            limit: 返回结果数量
            use_hybrid: 是否使用混合搜索（语义 + 关键词）
            
        Returns:
            搜索结果列表
        """
        # 限制查询长度
        if len(query) > 1000:
            raise ValueError("查询过长，最大支持 1000 字符")
        
        # 限制返回数量
        limit = min(limit, 100)
        
        try:
            if use_hybrid and query_embedding:
                # 混合搜索：语义 + 关键词
                return self._hybrid_search(query, query_embedding, limit)
            elif query_embedding:
                # 纯语义搜索
                return self._semantic_search(query_embedding, limit)
            else:
                # 纯关键词搜索
                return self._keyword_search(query, limit)
                
        except Exception as e:
            logger.error(f"搜索失败：{e}")
            # 优雅降级：返回友好错误
            return [{
                "content": "搜索服务暂时不可用",
                "metadata": {"error": str(e)},
                "distance": None
            }]
    
    def _hybrid_search(self, query: str, query_embedding: List[float], limit: int) -> List[Dict]:
        """混合搜索：语义 + 关键词"""
        try:
            # 语义搜索
            semantic_results = self._semantic_search(query_embedding, limit // 2 + 1)
        except Exception as e:
            logger.warning(f"语义搜索失败，降级到关键词搜索：{e}")
            semantic_results = []
        
        try:
            # 关键词搜索
            keyword_results = self._keyword_search(query, limit // 2 + 1)
        except Exception as e:
            logger.warning(f"关键词搜索失败，降级到语义搜索：{e}")
            keyword_results = []
        
        # 合并结果（去重）
        seen_ids = set()
        merged_results = []
        
        for result in semantic_results + keyword_results:
            doc_id = result.get("metadata", {}).get("source", "") + str(result.get("content", "")[:50])
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged_results.append(result)
        
        # 限制返回数量
        return merged_results[:limit]
    
    def _semantic_search(self, query_embedding: List[float], limit: int) -> List[Dict]:
        """纯语义搜索"""
        return self.index.search(query_embedding, limit)
    
    def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """
        纯关键词搜索（SQLite FTS5）。
        
        简化版本：实际应实现 SQLite FTS5 全文检索
        """
        # TODO: 实现 SQLite FTS5 关键词搜索
        logger.warning("关键词搜索尚未实现，返回空结果")
        return []
    
    def get_stats(self) -> Dict:
        """获取搜索统计信息"""
        return {
            "index_stats": self.index.get_stats(),
            "sqlite_path": self.sqlite_path,
            "hybrid_search_available": self.sqlite_path is not None
        }
