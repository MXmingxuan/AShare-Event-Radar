# 📈 A股权威买方"事件雷达"投研分析系统

> **Event-Driven Stock Radar Agent** — 一款专为 A 股买方研究员设计的 Map-Reduce 范式事件驱动分析工具

这是一个专门针对"长尾密集型专业金融研报"场景设计的 **Map-Reduce 范式事件驱动分析大模型 Agent**。系统旨在摒弃"媒体二手新闻"的噪音，直接连通交易所官方公告，协助买方研究员完成：**抓取海量公告底稿 → 单源信息提纯降噪 → 事件网聚合 → 高维基本面/估值/情绪拐点提炼** 的全自动化链路。

---

## 🎯 核心痛点与解决方案

在实际行情波动中，仅靠一篇公告标题往往无法研判趋势。如果直接将几十篇长达万字的"混杂型大额财务报表"、"临时股东会通知"等统统丢给 ChatGPT 等长窗口大模型，极易引发严重的 **"注意力失焦 (Attention Dilution)"**，导致模型被大段套话带偏，无法抓取最致命的财务反转数字。

本平台创新执行了彻底的工程化拆解：

| 层级 | 名称 | 核心作用 |
|------|------|---------|
| **第一层 MAP** | 单兵提取 | 强制大模型将单篇上万字的冗长财报结构化为带有"事件暗号(Event Key)"、"数字提取"及"置信度"字段的 JSON 卡片 |
| **第二层 SHUFFLE** | 聚类降噪 | Python 层物理剥离程序文件、噪音、低价值公告，确保进入大模型的数据无一丝杂质 |
| **第三层 REDUCE** | 高管总评 | 基于高度精准定量的数字信息，输出 S/A/B 级战略变动报告 |

---

## 🖥️ Web 可视化终端

系统内置了一套具有 **Glassmorphism (玻璃拟物化)** 效果的深色高端投研终端界面，支持三栏导航：

| 功能模块 | 说明 |
|----------|------|
| **◎ 雷达探测** | 输入股票代码与回溯天数，一键启动全流程 Map-Reduce 分析 |
| **📖 系统白皮书** | 图文介绍系统架构原理与价值 |
| **⚙️ 安全配置** | 自定义 API Key（浏览器 localStorage 加密）与底座模型选择 |

---

## 📦 项目结构

```
stock_skill/
├── app.py                    # FastAPI 后端入口
├── event_radar_agent.py      # 核心 Map-Reduce 三层引擎
├── stock_data_fetcher.py     # 公告数据爬虫（东方财富API）
├── prompt_1_extractor.md     # Map 层：单篇结构化抽取提示词
├── prompt_2_summarizer.md    # Reduce 层：买方研判提示词
├── static/
│   ├── index.html            # 前端页面（三栏导航）
│   ├── style.css             # Glassmorphism 深色主题样式
│   └── app.js                # 前端交互与 localStorage 管理
└── README.md
```

---

## 🛠️ 快速开始

### 1. 安装依赖

```bash
pip install pandas akshare requests beautifulsoup4 anthropic fastapi uvicorn
```

### 2. 配置 API Key

**方式一：环境变量（推荐）**
```powershell
# PowerShell
$env:MINIMAX_API_KEY="您的Token"
```

**方式二：Web 界面配置**
启动后在「安全配置」页面直接填入，自动保存至浏览器本地。

### 3. 启动服务

```bash
python -m uvicorn app:app --port 8080
```

打开浏览器访问：**http://127.0.0.1:8080**

### 4. 命令行模式（可选）

```bash
python event_radar_agent.py 603906
```

---

## 🔧 技术栈

- **后端**: Python + FastAPI + Uvicorn
- **大模型**: MiniMax M2.7 (Anthropic SDK 兼容协议)
- **数据源**: 东方财富官方公告 API (AKShare + 自定义内容抓取)
- **前端**: Vanilla HTML5 + CSS3 (Glassmorphism) + JavaScript
- **Markdown 渲染**: marked.js

---

## ⚠️ 免责声明

本项目仅作为**文本自动化及信息结构化开源示例项目**，所产生或总结的任何针对股票的预期、定调、财报走向皆为基础语料加工而来，**绝不构成任何买卖邀约和投资交易建议**。入市有风险，请保持独立批判验证能力。
