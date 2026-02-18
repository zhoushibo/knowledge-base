"""
知识库系统 - 命令行界面

提供便捷的知识导入、搜索、管理功能。
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加父目录到路径，以便导入核心模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import KnowledgeIngest, KnowledgeIndex, KnowledgeSearch, KnowledgeLink

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
        "chroma_path": os.getenv("CHROMADB_PATH", "./data/chromadb"),
        "sqlite_path": os.getenv("SQLITE_PATH", "./data/knowledge.db"),
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        "default_search_limit": int(os.getenv("DEFAULT_SEARCH_LIMIT", "10")),
    }


def cmd_import(args):
    """导入命令"""
    logger.info(f"开始导入文件：{args.file}")
    
    config = load_config()
    ingest = KnowledgeIngest(max_file_size_mb=config["max_file_size_mb"])
    
    try:
        knowledge_items = ingest.import_file(args.file)
        logger.info(f"✅ 导入成功：{len(knowledge_items)} 个知识条目")
        
        # 打印预览
        print(f"\n导入预览（前 3 条）：")
        for i, item in enumerate(knowledge_items[:3], 1):
            preview = item["content"][:100].replace('\n', ' ')
            print(f"  {i}. {preview}...")
        
        # TODO: 添加到索引
        logger.warning("⚠️  索引功能尚未实现，知识条目未保存")
        
    except Exception as e:
        logger.error(f"❌ 导入失败：{e}")
        sys.exit(1)


def cmd_search(args):
    """搜索命令"""
    logger.info(f"开始搜索：{args.query}")
    
    config = load_config()
    
    # TODO: 初始化索引和搜索
    logger.warning("⚠️  搜索功能尚未实现")
    print("搜索功能开发中，请稍后...")


def cmd_stats(args):
    """统计信息命令"""
    print("\n📊 知识库统计信息")
    print("=" * 50)
    print("状态：开发中")
    print("版本：v0.1.0")
    print("=" * 50)
    
    # TODO: 显示实际统计信息
    print("\n核心模块:")
    print("  ✅ KnowledgeIngest - 知识导入")
    print("  ✅ KnowledgeIndex - 向量索引")
    print("  ✅ KnowledgeSearch - 智能搜索")
    print("  ✅ KnowledgeLink - 知识关联")
    print("\n待实现:")
    print("  ⏳ 索引持久化")
    print("  ⏳ 嵌入生成集成")
    print("  ⏳ SQLite FTS5 关键词搜索")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="知识库系统 - 结构化知识存储与检索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  kb import myfile.md              # 导入 Markdown 文件
  kb search "机器学习"              # 搜索知识
  kb stats                         # 查看统计信息
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # import 命令
    parser_import = subparsers.add_parser("import", help="导入知识文件")
    parser_import.add_argument("file", type=str, help="文件路径")
    parser_import.set_defaults(func=cmd_import)
    
    # search 命令
    parser_search = subparsers.add_parser("search", help="搜索知识")
    parser_search.add_argument("query", type=str, help="搜索查询")
    parser_search.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")
    parser_search.set_defaults(func=cmd_search)
    
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
