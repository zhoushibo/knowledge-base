"""
知识库系统 - 命令行界面
提供便捷的知识导入、搜索、管理功能。
支持 ChromaDB 语义搜索和 SQLite FTS5 关键词搜索（混合搜索）。
"""
import argparse
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加父目录到路径，以便导入核心模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import KnowledgeIngest, KnowledgeIndex, KnowledgeSearch, KnowledgeLink, EmbeddingGenerator
from core.knowledge_search_fts import KnowledgeSearchFTS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """加载配置"""
    # 加载 .env 文件
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"已加载配置文件：{env_path}")
    else:
        logger.warning(f"配置文件不存在：{env_path}，使用默认配置")
    
    return {
        "chroma_path": os.getenv("CHROMA_PATH", "./data/chromadb"),
        "sqlite_path": os.getenv("SQLITE_PATH", "./data/knowledge.db"),
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        "default_search_limit": int(os.getenv("DEFAULT_SEARCH_LIMIT", "10")),
    }


def cmd_import(args):
    """导入命令"""
    logger.info(f"开始导入文件：{args.file}")
    config = load_config()
    
    # 初始化组件
    ingest = KnowledgeIngest(max_file_size_mb=config["max_file_size_mb"])
    embedding_gen = EmbeddingGenerator(
        cache_path="./data/embedding_cache.json"
    )
    index = KnowledgeIndex(
        chroma_path=config["chroma_path"],
        embedding_generator=embedding_gen
    )
    fts = KnowledgeSearchFTS(db_path="./data/knowledge_fts.db")
    
    try:
        # 1. 导入文件
        knowledge_items = ingest.import_file(args.file)
        logger.info(f"✅ 导入成功：{len(knowledge_items)} 个知识条目")
        
        # 2. 添加到 ChromaDB 索引（自动生成嵌入）
        count = index.add_documents(knowledge_items, auto_generate=True)
        logger.info(f"✅ ChromaDB 索引成功：{count} 个文档")
        
        # 3. 添加到 FTS5 索引
        fts_docs = [
            {
                "content": item["content"],
                "title": item.get("metadata", {}).get("title", ""),
                "tags": item.get("metadata", {}).get("tags", ""),
                "source": item.get("metadata", {}).get("source", ""),
                "metadata": item.get("metadata", {})
            }
            for item in knowledge_items
        ]
        fts_count = fts.add_documents(fts_docs)
        logger.info(f"✅ FTS5 索引成功：{fts_count} 个文档")
        
        # 打印预览
        print(f"\n✅ 导入完成！")
        print(f" - 知识条目：{len(knowledge_items)} 个")
        print(f" - ChromaDB 索引：{count} 个文档")
        print(f" - FTS5 索引：{fts_count} 个文档")
        print(f"\n导入预览（前 3 条）：")
        for i, item in enumerate(knowledge_items[:3], 1):
            preview = item["content"][:100].replace('\n', ' ')
            print(f" {i}. {preview}...")
        
    except Exception as e:
        logger.error(f"❌ 导入失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        fts.close()


def cmd_search(args):
    """语义搜索命令"""
    logger.info(f"开始搜索：{args.query}")
    config = load_config()
    
    try:
        # 初始化组件
        embedding_gen = EmbeddingGenerator(
            cache_path="./data/embedding_cache.json"
        )
        index = KnowledgeIndex(
            chroma_path=config["chroma_path"],
            embedding_generator=embedding_gen
        )
        searcher = KnowledgeSearch(index=index)
        
        # 生成查询嵌入
        print(f"🔍 正在搜索：{args.query}")
        logger.info("正在生成查询嵌入...")
        query_embedding = embedding_gen.generate(args.query)
        
        # 执行搜索
        results = searcher.search(
            query=args.query,
            query_embedding=query_embedding,
            limit=args.limit,
            use_hybrid=True
        )
        
        # 显示结果
        if not results or (len(results) == 1 and results[0].get("metadata", {}).get("error")):
            print("\n❌ 未找到相关知识")
            return
        
        print(f"\n✅ 找到 {len(results)} 条相关知识：\n")
        for i, result in enumerate(results, 1):
            content = result.get("content", "")[:200].replace('\n', ' ')
            source = result.get("metadata", {}).get("source", "未知")
            distance = result.get("distance")
            
            print(f"**{i}.** {content}...")
            print(f" - 来源：{source}")
            if distance is not None:
                print(f" - 相似度：{1 - distance:.4f}（距离：{distance:.4f}）")
            print()
        
    except Exception as e:
        logger.error(f"❌ 搜索失败：{e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ 搜索失败：{e}")
        sys.exit(1)


def cmd_search_fts(args):
    """FTS5 关键词搜索命令"""
    logger.info(f"开始 FTS5 搜索：{args.query}")
    config = load_config()
    
    try:
        # 初始化 FTS5 搜索引擎
        fts = KnowledgeSearchFTS(db_path="./data/knowledge_fts.db")
        
        # 执行搜索
        print(f"🔍 FTS5 关键词搜索：{args.query}")
        results = fts.search(
            query=args.query,
            limit=args.limit,
            highlight=True
        )
        
        # 显示结果
        if not results:
            print("\n❌ 未找到匹配结果")
            fts.close()
            return
        
        print(f"\n✅ 找到 {len(results)} 条匹配结果：\n")
        for i, result in enumerate(results, 1):
            title = result.get("title", "")
            content = result.get("content", "")
            source = result.get("source", "未知")
            tags = result.get("tags", "")
            score = result.get("score", 0)
            
            # 显示标题
            if title:
                print(f"**{i}. {title}**")
            else:
                print(f"**{i}.**")
            
            # 显示内容（含高亮）
            print(f"    {content}")
            
            # 显示元数据
            if tags:
                print(f"    标签：{tags}")
            print(f"    来源：{source}")
            print(f"    相关性：{score:.4f}")
            print()
        
        # 统计
        stats = fts.get_stats()
        print(f"📊 索引统计：共 {stats['total_documents']} 条文档")
        
        fts.close()
        
    except Exception as e:
        logger.error(f"❌ FTS5 搜索失败：{e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ FTS5 搜索失败：{e}")
        sys.exit(1)


def cmd_stats(args):
    """统计信息命令"""
    print("\n📊 知识库统计信息")
    print("=" * 60)
    print("版本：v0.2.0 - 混合搜索（语义 + 关键词）")
    print("=" * 60)
    
    # 统计 ChromaDB
    try:
        from core import KnowledgeIndex, EmbeddingGenerator
        embedding_gen = EmbeddingGenerator()
        index = KnowledgeIndex(embedding_generator=embedding_gen)
        index._ensure_initialized()
        chroma_count = index.collection.count() if index.collection else 0
        print(f"\n✅ ChromaDB 向量索引：{chroma_count} 条文档")
    except Exception as e:
        print(f"\n⚠️ ChromaDB 统计失败：{e}")
    
    # 统计 FTS5
    try:
        from core.knowledge_search_fts import KnowledgeSearchFTS
        fts = KnowledgeSearchFTS()
        stats = fts.get_stats()
        print(f"✅ SQLite FTS5 关键词索引：{stats['total_documents']} 条文档")
        fts.close()
    except Exception as e:
        print(f"⚠️ FTS5 统计失败：{e}")
    
    print("\n" + "=" * 60)
    print("核心功能:")
    print(" ✅ 知识导入（Markdown 支持）")
    print(" ✅ ChromaDB 语义搜索（理解语义）")
    print(" ✅ SQLite FTS5 关键词搜索（精确匹配 + 高亮）")
    print(" ✅ 自动嵌入生成（SiliconFlow 1024 维）")
    print(" ✅ 文本自动分段（<300 字符/段）")
    print(" ✅ 缓存机制（避免重复调用）")
    print("\n使用方法:")
    print(" kb import <file.md>          # 导入知识文件")
    print(" kb search \"<query>\"         # 语义搜索")
    print(" kb search-ft \"<keyword>\"    # 关键词搜索（高亮）")
    print(" kb stats                     # 查看统计")
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="知识库系统 - 结构化知识存储与检索（支持混合搜索）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  kb import myfile.md              # 导入 Markdown 文件
  kb search "机器学习是什么"       # 语义搜索（理解语义）
  kb search-ft "机器学习"          # 关键词搜索（精确匹配 + 高亮）
  kb stats                         # 查看统计信息

混合搜索说明:
  - 语义搜索：适合模糊查询、理解意图（如"修仙第二个境界"）
  - 关键词搜索：适合精确查询、需要高亮（如"筑基期"）
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # import 命令
    parser_import = subparsers.add_parser("import", help="导入知识文件")
    parser_import.add_argument("file", type=str, help="文件路径")
    parser_import.set_defaults(func=cmd_import)
    
    # search 命令（语义搜索）
    parser_search = subparsers.add_parser("search", help="语义搜索知识（理解语义）")
    parser_search.add_argument("query", type=str, help="搜索查询")
    parser_search.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")
    parser_search.set_defaults(func=cmd_search)
    
    # search-ft 命令（FTS5 关键词搜索）
    parser_search_fts = subparsers.add_parser("search-ft", help="FTS5 关键词搜索（精确匹配 + 高亮）")
    parser_search_fts.add_argument("query", type=str, help="搜索关键词")
    parser_search_fts.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")
    parser_search_fts.set_defaults(func=cmd_search_fts)
    
    # stats 命令
    parser_stats = subparsers.add_parser("stats", help="查看统计信息")
    parser_stats.set_defaults(func=cmd_stats)
    
    # 解析参数
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # 执行命令
    args.func(args)


if __name__ == "__main__":
    main()
