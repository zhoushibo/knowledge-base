"""
知识关联模块

自动发现知识之间的关联，建立知识网络。
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeLink:
    """知识关联器"""
    
    def __init__(self):
        """初始化知识关联器"""
        self.knowledge_graph = defaultdict(list)
    
    def find_links(self, knowledge_items: List[Dict], threshold: float = 0.7) -> Dict[str, List[str]]:
        """
        发现知识之间的关联。
        
        Args:
            knowledge_items: 知识条目列表
            threshold: 关联阈值（0-1）
            
        Returns:
            关联字典 {doc_id: [related_doc_ids]}
        """
        # 简化版本：基于元数据中的标签进行关联
        # 实际应使用向量相似度或图算法
        
        links = defaultdict(list)
        
        # 按标签分组
        tag_groups = defaultdict(list)
        for item in knowledge_items:
            tags = item.get("metadata", {}).get("tags", [])
            for tag in tags:
                tag_groups[tag].append(item)
        
        # 建立关联
        for tag, items in tag_groups.items():
            for i, item1 in enumerate(items):
                for item2 in items[i+1:]:
                    id1 = str(item1.get("metadata", {}).get("source", ""))
                    id2 = str(item2.get("metadata", {}).get("source", ""))
                    if id1 and id2 and id1 != id2:
                        links[id1].append(id2)
                        links[id2].append(id1)
        
        logger.info(f"发现 {sum(len(v) for v in links.values())} 个关联")
        return dict(links)
    
    def get_related(self, doc_id: str, limit: int = 10) -> List[str]:
        """
        获取相关文档 ID。
        
        Args:
            doc_id: 文档 ID
            limit: 返回数量限制
            
        Returns:
            相关文档 ID 列表
        """
        related = self.knowledge_graph.get(doc_id, [])
        return related[:limit]
    
    def add_link(self, doc_id1: str, doc_id2: str):
        """添加两个文档之间的关联"""
        self.knowledge_graph[doc_id1].append(doc_id2)
        self.knowledge_graph[doc_id2].append(doc_id1)
    
    def get_stats(self) -> Dict:
        """获取关联统计信息"""
        total_links = sum(len(v) for v in self.knowledge_graph.values()) // 2  # 除以 2 避免重复
        return {
            "total_documents": len(self.knowledge_graph),
            "total_links": total_links,
            "avg_links_per_doc": total_links / max(len(self.knowledge_graph), 1)
        }
