"""
知识搜索模块 - SQLite FTS5 全文搜索
使用 SQLite FTS5 实现高性能关键词搜索，支持高亮显示和相关性排名。
与 ChromaDB 语义搜索互补，形成混合搜索能力。
"""
import logging
import sqlite3
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class KnowledgeSearchFTS:
    """SQLite FTS5 全文搜索引擎"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化 FTS5 搜索引擎。
        
        Args:
            db_path: SQLite 数据库路径（默认：./data/knowledge_fts.db）
        """
        self.db_path = Path(db_path) if db_path else Path("./data/knowledge_fts.db")
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """初始化数据库和 FTS5 表"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # 支持字典访问
        
        cursor = self.conn.cursor()
        
        # 创建 FTS5 虚拟表
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                content,
                title,
                tags,
                source
            )
        ''')
        
        # 创建普通表存储元数据（与 FTS5 表关联）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_meta(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rowid INTEGER,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rowid) REFERENCES knowledge_fts(rowid)
            )
        ''')
        
        self.conn.commit()
        logger.info(f"SQLite FTS5 初始化成功：{self.db_path}")
    
    def add_documents(self, documents: List[Dict]) -> int:
        """
        添加文档到 FTS5 索引。
        
        Args:
            documents: 文档列表，格式：
                [
                    {
                        "content": "正文内容",
                        "title": "标题（可选）",
                        "tags": "标签（可选，逗号分隔）",
                        "source": "来源文件",
                        "metadata": {"extra": "data"}  # 额外元数据
                    }
                ]
        
        Returns:
            添加的文档数量
        """
        cursor = self.conn.cursor()
        count = 0
        
        for doc in documents:
            try:
                # 插入 FTS5 表
                cursor.execute('''
                    INSERT INTO knowledge_fts (content, title, tags, source)
                    VALUES (?, ?, ?, ?)
                ''', (
                    doc.get('content', ''),
                    doc.get('title', ''),
                    doc.get('tags', ''),
                    doc.get('source', '')
                ))
                
                rowid = cursor.lastrowid
                
                # 插入元数据
                import json
                metadata_json = json.dumps(doc.get('metadata', {}))
                cursor.execute('''
                    INSERT INTO knowledge_meta (rowid, metadata)
                    VALUES (?, ?)
                ''', (rowid, metadata_json))
                
                count += 1
                
            except Exception as e:
                logger.error(f"添加文档失败：{e}")
                continue
        
        self.conn.commit()
        logger.info(f"FTS5 添加文档：{count}/{len(documents)}")
        return count
    
    def search(self, query: str, limit: int = 10, highlight: bool = True) -> List[Dict]:
        """
        搜索关键词。
        
        Args:
            query: 搜索关键词（支持 FTS5 语法）
            limit: 返回结果数量
            highlight: 是否高亮匹配内容
        
        Returns:
            搜索结果列表，格式：
                [
                    {
                        "content": "匹配内容（含高亮）",
                        "title": "标题",
                        "source": "来源",
                        "tags": "标签",
                        "score": 相关性分数,
                        "metadata": {...}
                    }
                ]
        """
        cursor = self.conn.cursor()
        
        # FTS5 搜索查询（使用 bm25 排名）
        sql = '''
            SELECT 
                fts.rowid,
                fts.content,
                fts.title,
                fts.source,
                fts.tags,
                bm25(knowledge_fts, 0) as score
            FROM knowledge_fts fts
            WHERE knowledge_fts MATCH ?
            ORDER BY score
            LIMIT ?
        '''
        
        cursor.execute(sql, (query, limit))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            result = {
                "content": row["content"],
                "title": row["title"] or "",
                "source": row["source"] or "",
                "tags": row["tags"] or "",
                "score": row["score"],
                "metadata": {}
            }
            
            # 高亮处理
            if highlight:
                result["content"] = self._highlight_matches(result["content"], query)
            
            # 加载元数据
            cursor.execute('SELECT metadata FROM knowledge_meta WHERE rowid = ?', (row["rowid"],))
            meta_row = cursor.fetchone()
            if meta_row:
                import json
                result["metadata"] = json.loads(meta_row["metadata"])
            
            results.append(result)
        
        logger.info(f"FTS5 搜索 '{query}': 找到 {len(results)} 条结果")
        return results
    
    def _highlight_matches(self, text: str, query: str) -> str:
        """
        高亮显示匹配的关键词。
        
        Args:
            text: 原始文本
            query: 搜索关键词
        
        Returns:
            含高亮标记的文本（使用 ** 标记）
        """
        import re
        
        # 提取查询中的关键词（简单分词）
        keywords = query.split()
        
        highlighted = text
        for keyword in keywords:
            # 忽略标点符号
            clean_keyword = keyword.strip('.,!?;:，。！？；：')
            if len(clean_keyword) < 2:
                continue
            
            # 不区分大小写匹配
            pattern = re.compile(re.escape(clean_keyword), re.IGNORECASE)
            highlighted = pattern.sub(lambda m: f"**{m.group()}**", highlighted)
        
        return highlighted
    
    def delete_by_source(self, source: str) -> int:
        """
        根据来源文件删除文档。
        
        Args:
            source: 来源文件路径
        
        Returns:
            删除的文档数量
        """
        cursor = self.conn.cursor()
        
        # 先获取 rowid
        cursor.execute('SELECT rowid FROM knowledge_fts WHERE source = ?', (source,))
        rows = cursor.fetchall()
        count = len(rows)
        
        if count > 0:
            rowids = [row[0] for row in rows]
            placeholders = ','.join('?' * len(rowids))
            
            # 删除 FTS5 表记录
            cursor.execute(f'DELETE FROM knowledge_fts WHERE rowid IN ({placeholders})', rowids)
            
            # 删除元数据
            cursor.execute(f'DELETE FROM knowledge_meta WHERE rowid IN ({placeholders})', rowids)
            
            self.conn.commit()
            logger.info(f"FTS5 删除来源 '{source}': {count} 条文档")
        
        return count
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM knowledge_fts')
        total_docs = cursor.fetchone()[0]
        
        return {
            "total_documents": total_docs,
            "database_path": str(self.db_path),
            "engine": "SQLite FTS5"
        }
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.debug("FTS5 数据库连接已关闭")


# 测试
if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("=" * 80)
        print("🧪 SQLite FTS5 搜索测试")
        print("=" * 80)
        
        # 初始化
        fts = KnowledgeSearchFTS()
        
        # 测试数据
        test_docs = [
            {
                "content": "修仙之路，始于凡人，历经千难万险，方得大道。筑基期是修仙的第二个境界。",
                "title": "修仙等级划分",
                "tags": "修仙，境界，筑基",
                "source": "test.md",
                "metadata": {"chapter": 1}
            },
            {
                "content": "炼气期是修仙的第一个境界，引气入体，淬炼肉身。",
                "title": "炼气期详解",
                "tags": "修仙，境界，炼气",
                "source": "test.md",
                "metadata": {"chapter": 1}
            }
        ]
        
        # 添加文档
        print("\n1️⃣ 添加测试文档...")
        count = fts.add_documents(test_docs)
        print(f" ✅ 添加成功：{count} 条")
        
        # 搜索测试
        print("\n2️⃣ 搜索 '筑基'...")
        results = fts.search("筑基", limit=5)
        for i, result in enumerate(results, 1):
            print(f"\n {i}. {result['title']}")
            print(f"    内容：{result['content'][:100]}...")
            print(f"    分数：{result['score']:.4f}")
            print(f"    来源：{result['source']}")
        
        # 统计
        print("\n3️⃣ 索引统计...")
        stats = fts.get_stats()
        print(f" 总文档数：{stats['total_documents']}")
        
        # 清理
        fts.close()
        
        print("\n✅ 测试完成！")
    
    asyncio.run(main())
