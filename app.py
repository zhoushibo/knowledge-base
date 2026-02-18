"""
知识库管理系统 - Streamlit Web UI
提供直观的知识导入、搜索、统计功能。
支持 ChromaDB 语义搜索和 SQLite FTS5 关键词搜索（混合搜索）。
"""
import streamlit as st
import sys
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import KnowledgeIngest, KnowledgeIndex, EmbeddingGenerator
from core.knowledge_search_fts import KnowledgeSearchFTS
from core.knowledge_search import KnowledgeSearch

# 页面配置
st.set_page_config(
    page_title="知识库管理系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .search-result {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border-left: 4px solid #4CAF50;
    }
    .highlight {
        background-color: #fff3cd;
        padding: 2px 5px;
        border-radius: 3px;
        font-weight: bold;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/library.png", width=100)
    st.title("📚 知识库管理")
    st.markdown("**版本：** v0.2.0 - 混合搜索")
    st.markdown("---")
    
    # 导航菜单
    menu = st.radio(
        "导航",
        ["🔍 搜索知识", "📤 导入文件", "📊 统计信息", "ℹ️ 使用说明"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("**快速操作**")
    if st.button("🔄 刷新页面"):
        st.rerun()

# 主函数
def main():
    """主应用"""
    
    if menu == "🔍 搜索知识":
        search_page()
    elif menu == "📤 导入文件":
        import_page()
    elif menu == "📊 统计信息":
        stats_page()
    elif menu == "ℹ️ 使用说明":
        help_page()


def search_page():
    """搜索页面"""
    st.title("🔍 搜索知识")
    st.markdown("支持**语义搜索**（理解意图）和**关键词搜索**（精确匹配 + 高亮）")
    
    # 搜索模式选择
    col1, col2 = st.columns(2)
    with col1:
        search_mode = st.radio(
            "搜索模式",
            ["🧠 语义搜索（理解语义）", "🎯 关键词搜索（精确匹配）"],
            horizontal=True
        )
    
    # 搜索框
    query = st.text_input(
        "输入搜索关键词",
        placeholder="例如：筑基期、修仙第二个境界、机器学习...",
        key="search_query"
    )
    
    # 高级选项
    with st.expander("⚙️ 高级选项"):
        limit = st.slider("返回结果数量", 1, 20, 10)
        show_metadata = st.checkbox("显示元数据", value=True)
    
    # 搜索按钮
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        search_btn = st.button("🔍 开始搜索", type="primary", use_container_width=True)
    
    if search_btn and query:
        perform_search(query, search_mode, limit, show_metadata)
    elif search_btn and not query:
        st.warning("请输入搜索关键词！")
    
    # 最近搜索（示例）
    st.markdown("---")
    st.markdown("### 💡 搜索建议")
    st.markdown("- `筑基期` - 精确查找特定境界")
    st.markdown("- `修仙第二个境界` - 语义理解查询")
    st.markdown("- `金丹期特点` - 查找特定信息")


def perform_search(query, search_mode, limit, show_metadata):
    """执行搜索"""
    is_semantic = "语义" in search_mode
    
    with st.spinner("正在搜索..."):
        try:
            # 初始化组件
            embedding_gen = EmbeddingGenerator(cache_path="./data/embedding_cache.json")
            
            if is_semantic:
                # 语义搜索
                index = KnowledgeIndex(
                    chroma_path="./data/chromadb",
                    embedding_generator=embedding_gen
                )
                searcher = KnowledgeSearch(index=index)
                
                # 生成查询嵌入
                query_embedding = embedding_gen.generate(query)
                results = searcher.search(
                    query=query,
                    query_embedding=query_embedding,
                    limit=limit,
                    use_hybrid=True
                )
                
                st.success(f"✅ 找到 {len(results)} 条相关知识")
                
            else:
                # 关键词搜索
                fts = KnowledgeSearchFTS(db_path="./data/knowledge_fts.db")
                results = fts.search(query=query, limit=limit, highlight=True)
                fts.close()
                
                st.success(f"✅ 找到 {len(results)} 条匹配结果")
            
            # 显示结果
            if not results:
                st.info("❌ 未找到相关结果，请尝试其他关键词。")
                return
            
            for i, result in enumerate(results, 1):
                display_search_result(i, result, is_semantic, show_metadata)
        
        except Exception as e:
            st.error(f"❌ 搜索失败：{str(e)}")
            logger.exception("搜索错误")


def display_search_result(index, result, is_semantic, show_metadata):
    """显示搜索结果"""
    title = result.get("title", "")
    content = result.get("content", "")[:500]  # 限制长度
    source = result.get("source", "未知")
    
    # 语义搜索的相似度
    similarity = None
    if is_semantic:
        distance = result.get("distance")
        if distance:
            similarity = 1 - distance
    
    # FTS5 的相关性分数
    score = result.get("score")
    
    # 构建结果卡片
    st.markdown(f"""
    <div class="search-result">
        <h3>{index}. {title if title else "无标题"}</h3>
        <p>{content}...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 元数据
    if show_metadata:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("来源", source)
        with col2:
            if is_semantic and similarity:
                st.metric("相似度", f"{similarity:.4f}")
            elif not is_semantic and score:
                st.metric("相关性", f"{score:.4f}")
            else:
                st.metric("匹配度", "N/A")
        with col3:
            tags = result.get("tags", "")
            st.metric("标签", tags if tags else "无")


def import_page():
    """导入页面"""
    st.title("📤 导入知识文件")
    st.markdown("支持 Markdown (.md)、Text (.txt) 等格式文件")
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "选择文件上传",
        type=["md", "txt", "markdown"],
        help="支持的文件格式：.md, .txt, .markdown"
    )
    
    if uploaded_file:
        st.info(f"📄 已选择：**{uploaded_file.name}** ({uploaded_file.size} 字节)")
        
        # 预览内容
        with st.expander("👀 预览文件内容"):
            content = uploaded_file.read().decode("utf-8")
            st.text(content[:1000] + "..." if len(content) > 1000 else content)
        
        # 导入按钮
        if st.button("🚀 开始导入", type="primary"):
            do_import(uploaded_file)
    
    else:
        st.info("⬆️ 请先选择要导入的文件")
    
    # 批量导入（未来功能）
    st.markdown("---")
    st.markdown("### 📦 批量导入（开发中）")
    st.warning("批量导入功能即将上线，敬请期待！")


def do_import(uploaded_file):
    """执行导入"""
    try:
        # 保存上传文件
        temp_path = Path("./data/temp") / uploaded_file.name
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("正在导入..."):
            # 初始化组件
            ingest = KnowledgeIngest(max_file_size_mb=50)
            embedding_gen = EmbeddingGenerator(cache_path="./data/embedding_cache.json")
            index = KnowledgeIndex(
                chroma_path="./data/chromadb",
                embedding_generator=embedding_gen
            )
            fts = KnowledgeSearchFTS(db_path="./data/knowledge_fts.db")
            
            # 1. 导入文件
            knowledge_items = ingest.import_file(str(temp_path))
            
            # 2. 添加到 ChromaDB
            chroma_count = index.add_documents(knowledge_items, auto_generate=True)
            
            # 3. 添加到 FTS5
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
            fts.close()
            
            # 清理临时文件
            temp_path.unlink()
        
        # 显示成功信息
        st.success("✅ 导入成功！")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("知识条目", len(knowledge_items))
        with col2:
            st.metric("ChromaDB 索引", chroma_count)
        with col3:
            st.metric("FTS5 索引", fts_count)
        
        # 预览
        st.markdown("### 📖 导入预览")
        for i, item in enumerate(knowledge_items[:3], 1):
            preview = item["content"][:200].replace('\n', ' ')
            st.markdown(f"**{i}.** {preview}...")
        
        # 跳转搜索
        if st.button("🔍 去搜索"):
            st.session_state.menu = "🔍 搜索知识"
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ 导入失败：{str(e)}")
        logger.exception("导入错误")


def stats_page():
    """统计页面"""
    st.title("📊 统计信息")
    st.markdown("查看知识库的整体状态和统计信息")
    
    # 加载统计
    try:
        embedding_gen = EmbeddingGenerator()
        index = KnowledgeIndex(embedding_generator=embedding_gen)
        index._ensure_initialized()
        chroma_count = index.collection.count() if index.collection else 0
    except:
        chroma_count = 0
    
    try:
        fts = KnowledgeSearchFTS()
        fts_stats = fts.get_stats()
        fts_count = fts_stats["total_documents"]
        fts.close()
    except:
        fts_count = 0
    
    # 统计卡片
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <h2>🧠 ChromaDB</h2>
            <h1>{chroma_count}</h1>
            <p>向量索引文档</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h2>🎯 FTS5</h2>
            <h1>{fts_count}</h1>
            <p>关键词索引文档</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 详细信息
    st.markdown("---")
    st.markdown("### 📋 详细信息")
    
    st.info("""
    **知识库系统 v0.2.0**
    
    - **语义搜索：** ChromaDB 向量索引，理解查询意图
    - **关键词搜索：** SQLite FTS5 全文索引，精确匹配 + 高亮
    - **嵌入生成：** SiliconFlow BAAI/bge-large-zh-v1.5（1024 维）
    - **自动分段：** 文本超过 300 字符自动分段
    - **缓存机制：** 避免重复调用 API
    """)
    
    # 技术栈
    st.markdown("### 🛠️ 技术栈")
    st.markdown("""
    - **后端：** Python 3.11+
    - **向量数据库：** ChromaDB
    - **全文搜索：** SQLite FTS5
    - **嵌入模型：** SiliconFlow BAAI/bge-large-zh-v1.5
    - **Web 框架：** Streamlit
    - **Gateway：** 统一 API Gateway（6 个 Provider）
    """)


def help_page():
    """帮助页面"""
    st.title("ℹ️ 使用说明")
    st.markdown("知识库管理系统使用指南")
    
    st.markdown("""
    ### 🚀 快速开始
    
    #### 1️⃣ 导入知识
    1. 点击左侧导航栏的 **"📤 导入文件"**
    2. 选择 Markdown (.md) 或文本 (.txt) 文件
    3. 点击 **"🚀 开始导入"**
    4. 系统会自动建立双索引（ChromaDB + FTS5）
    
    #### 2️⃣ 搜索知识
    
    **语义搜索（推荐）：**
    - 适合模糊查询、理解意图
    - 示例：`修仙第二个境界是什么`
    - 优点：不需要精确匹配关键词
    
    **关键词搜索：**
    - 适合精确查询、需要高亮
    - 示例：`筑基期`
    - 优点：速度快，支持高亮显示
    
    #### 3️⃣ 查看统计
    - 点击 **"📊 统计信息"**
    - 查看索引文档数量
    - 了解系统状态
    
    ---
    
    ### 💡 搜索技巧
    
    **语义搜索技巧：**
    - 使用自然语言提问
    - 不需要精确匹配关键词
    - 示例：`如何凝结金丹`、`元婴期有什么能力`
    
    **关键词搜索技巧：**
    - 使用精确的关键词
    - 支持多个关键词（空格分隔）
    - 示例：`筑基期 特点`、`金丹期 寿命`
    
    ---
    
    ### 📚 支持的文件格式
    
    - ✅ Markdown (.md, .markdown)
    - ✅ 纯文本 (.txt)
    - 🔄 HTML (.html) - 开发中
    - 🔄 PDF (.pdf) - 计划中
    
    ---
    
    ### 🛠️ 常见问题
    
    **Q: 为什么搜索不到结果？**
    A: 请检查：
    1. 是否已导入相关文件
    2. 关键词是否正确
    3. 尝试换一种问法（语义搜索）
    
    **Q: 导入失败怎么办？**
    A: 请检查：
    1. 文件格式是否支持
    2. 文件大小是否超过限制（50MB）
    3. 查看错误日志
    
    **Q: 如何批量导入？**
    A: 批量导入功能开发中，敬请期待！
    
    ---
    
    ### 📞 技术支持
    
    如有问题，请联系开发团队或查看 GitHub 仓库。
    """)


if __name__ == "__main__":
    main()
