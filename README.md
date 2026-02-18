# 知识库系统 (Knowledge Base System)

**版本：** v0.1.0 (MVP 开发中)  
**创建时间：** 2026-02-18  
**状态：** 🟡 开发中

---

## 🎯 项目目标

构建结构化知识存储、检索、管理系统，支持**语义搜索**和**智能推荐**，实现**60 倍检索效率提升**。

### 核心价值

- **快速查找：** 平均查找时间从 10 分钟 → 10 秒（**60 倍提升**）
- **知识复用：** 复用率从 20% → 80%（**4 倍提升**）
- **智能关联：** 自动发现隐藏的知识联系
- **持续学习：** 积累个人/团队知识库

---

## 🚀 MVP 功能范围 (P0 优先级)

| 功能 | 描述 | 状态 |
|------|------|------|
| **知识导入** | 支持 Markdown、TXT 格式 | 📋 待开发 |
| **语义搜索** | ChromaDB 向量搜索 | 📋 待开发 |
| **关键词搜索** | SQLite FTS5 全文检索 | 📋 待开发 |
| **CLI 交互** | 命令行工具 | 📋 待开发 |

### P1/P2 功能（MVP 后扩展）

- 知识分类与标签系统
- 自动知识关联发现
- PDF/网页导入支持
- Web UI（Streamlit）

---

## 🏗️ 技术架构

```
knowledge_base/
├── core/                  # 核心引擎
│   ├── knowledge_ingest.py    # 知识导入
│   ├── knowledge_index.py     # 索引构建
│   ├── knowledge_search.py    # 智能搜索
│   └── knowledge_link.py      # 知识关联
├── agents/                # Agent 层（复用 MVP JARVIS）
│   └── knowledge_agent.py     # 知识智能体
├── tools/                 # 工具接口
│   └── knowledge_tools.py     # 知识库工具
├── tests/                 # 测试
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
├── data/                  # 数据目录
│   ├── chromadb/              # 向量数据库
│   └── sqlite/                # 结构化数据
├── docs/                  # 文档
├── requirements.txt       # 依赖
├── .env.example           # 环境变量示例
└── README.md              # 本文件
```

### 技术栈

- **向量存储：** ChromaDB（复用 V1 记忆系统）
- **结构化存储：** SQLite + FTS5 全文检索
- **嵌入生成：** NVIDIA API（免费配额）
- **Agent 框架：** 复用 MVP JARVIS KnowledgeAgent
- **超时保护：** OpenClaw Timeout Wrapper

---

## 📦 快速开始

### 1. 安装依赖

```bash
cd knowledge_base
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 NVIDIA_API_KEY
```

### 3. 运行 CLI

```bash
python -m knowledge_base.cli --help
```

---

## 🧪 测试

### 运行单元测试

```bash
pytest tests/unit/ --cov=core --cov-report=html
```

### 运行集成测试

```bash
pytest tests/integration/
```

### 测试覆盖率目标

- **核心模块：** ≥90%
- **整体项目：** ≥80%

---

## 📝 开发规范

### Git 工作流

- 使用 Git Flow（main/develop/feature）
- 提交信息遵循 Conventional Commits
- 所有合并必须经过 Code Review

### 代码质量

- PEP 8 + 类型标注（Type Hints）
- Black + Flake8 + Mypy 检查
- 所有公共函数必须有 docstring

### 测试要求

- 单元测试覆盖率≥80%
- 核心功能必须有集成测试
- 搜索响应时间<1 秒（P95）

---

## 🔒 安全合规

- **禁止硬编码** API Key、密码（使用环境变量）
- **输入验证** 所有外部输入
- **参数化查询** 防止 SQL 注入
- **日志脱敏** 不记录敏感信息

---

## 📊 项目进度

| 阶段 | 任务 | 状态 | 完成度 |
|------|------|------|--------|
| **阶段 1** | 项目初始化 | ✅ 完成 | 100% |
| **阶段 1** | 核心模块框架 | 🟡 进行中 | 0% |
| **阶段 2** | 知识导入功能 | 📋 待开始 | 0% |
| **阶段 2** | 语义搜索功能 | 📋 待开始 | 0% |
| **阶段 2** | 关键词搜索功能 | 📋 待开始 | 0% |
| **阶段 2** | CLI 工具开发 | 📋 待开始 | 0% |
| **阶段 3** | 单元测试编写 | 📋 待开始 | 0% |
| **阶段 3** | 集成测试编写 | 📋 待开始 | 0% |
| **阶段 4** | 文档完善 | 📋 待开始 | 0% |

**总体进度：** 10%（项目初始化完成）

---

## 🎯 成功指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 搜索响应时间 | <1 秒 | TaskLogger |
| 导入速度 | >10 千字/秒 | 基准测试 |
| 语义搜索准确率 | >85% | 人工抽样 |
| 系统可用性 | >99.9% | 健康检查 |
| 测试覆盖率 | ≥80% | pytest-cov |

---

## 📚 相关文档

- [架构设计](docs/architecture.md)（待创建）
- [API 文档](docs/api.md)（待创建）
- [开发指南](docs/development.md)（待创建）
- [部署指南](docs/deployment.md)（待创建）

---

## 🤝 贡献指南

1. Fork 项目
2. 创建 feature 分支 (`git flow feature start xxx`)
3. 提交更改 (`git commit -m 'feat: add xxx'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

---

## 📄 许可证

MIT License

---

**最后更新：** 2026-02-18 14:17  
**维护者：** Claw + 博
