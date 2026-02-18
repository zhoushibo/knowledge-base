# 🌐 知识库 Web UI 使用指南

## 🚀 快速启动

### 1️⃣ 安装依赖
```bash
cd knowledge_base
pip install -r requirements.txt
```

### 2️⃣ 启动 Web UI
```bash
streamlit run app.py
```

### 3️⃣ 访问应用
浏览器打开：**http://localhost:8501**

---

## 📱 功能概览

### 🔍 搜索知识
- **语义搜索**：理解查询意图（如"修仙第二个境界"）
- **关键词搜索**：精确匹配 + 高亮显示（如"筑基期"）
- **高级选项**：调整结果数量、显示元数据

### 📤 导入文件
- 支持 Markdown (.md)、Text (.txt) 格式
- 实时预览文件内容
- 自动建立双索引（ChromaDB + FTS5）
- 显示导入统计

### 📊 统计信息
- ChromaDB 向量索引文档数
- FTS5 关键词索引文档数
- 技术栈信息

### ℹ️ 使用说明
- 快速开始指南
- 搜索技巧
- 常见问题解答

---

## 🎨 界面截图

### 搜索页面
- 左侧导航栏选择"🔍 搜索知识"
- 选择搜索模式（语义/关键词）
- 输入关键词，点击搜索
- 查看结果卡片（含相似度/相关性）

### 导入页面
- 拖拽或选择文件上传
- 预览文件内容
- 点击导入，查看进度
- 显示导入统计

### 统计页面
- 渐变色统计卡片
- 详细信息展示
- 技术栈说明

---

## ⚙️ 配置选项

### 环境变量
```bash
# Gateway 配置
GATEWAY_URL=ws://127.0.0.1:8001

# 数据库路径
CHROMA_PATH=./data/chromadb
SQLITE_PATH=./data/knowledge.db

# 其他配置
MAX_FILE_SIZE_MB=50
DEFAULT_SEARCH_LIMIT=10
```

### Streamlit 配置
创建 `.streamlit/config.toml`：
```toml
[server]
port = 8501
address = "localhost"
headless = true

[browser]
gatherUsageStats = false
```

---

## 🔧 高级用法

### 自定义端口
```bash
streamlit run app.py --server.port=8080
```

### 远程访问
```bash
streamlit run app.py --server.address=0.0.0.0
```

### 生产环境部署
使用 Gunicorn 作为 WSGI 服务器：
```bash
pip install gunicorn
gunicorn -b 0.0.0.0:8501 app:main
```

---

## 📱 移动端适配

Web UI 已适配移动端：
- ✅ 响应式布局
- ✅ 触摸友好的按钮
- ✅ 移动端优化菜单

---

## 🐛 故障排除

### 问题 1：无法访问 http://localhost:8501
**解决：**
1. 检查 Streamlit 是否运行
2. 确认端口未被占用
3. 尝试其他端口：`--server.port=8502`

### 问题 2：导入文件失败
**解决：**
1. 检查文件格式（.md 或 .txt）
2. 确认文件大小（<50MB）
3. 查看错误日志

### 问题 3：搜索无结果
**解决：**
1. 确认已导入相关文件
2. 尝试不同的关键词
3. 切换搜索模式（语义/关键词）

---

## 🎯 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + R` | 刷新页面 |
| `Ctrl + Shift + R` | 清除缓存 |
| `Tab` | 切换输入框 |
| `Enter` | 提交搜索 |

---

## 📊 性能优化

### 缓存策略
- ✅ 嵌入向量缓存（避免重复调用 API）
- ✅ Streamlit 内置缓存（`@st.cache_data`）

### 数据库优化
- ✅ ChromaDB 持久化存储
- ✅ FTS5 索引优化

### 前端优化
- ✅ 懒加载搜索结果
- ✅ 分页显示（大量结果时）

---

## 🚀 未来功能

- [ ] 批量导入
- [ ] 知识图谱可视化
- [ ] 用户认证系统
- [ ] 多用户支持
- [ ] 导出功能（PDF、Markdown）
- [ ] 历史记录
- [ ] 收藏夹
- [ ] 标签管理

---

## 📞 技术支持

如有问题，请：
1. 查看本使用指南
2. 检查日志文件
3. 联系开发团队

---

**最后更新：** 2026-02-18  
**版本：** v0.2.0
