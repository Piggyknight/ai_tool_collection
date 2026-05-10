---
name: daily-report-collector
description: "日报收集技能，用于收集和解析Markdown格式的团队日报。使用场景：(1) 用户提供Markdown格式的日报需要收集，(2) 自动解析成员任务并保存为标准格式，(3) 提交日报到Git仓库。核心功能：解析Markdown → 提取成员任务 → 保存为soc_daily_YYYYMMDD.md → Git自动提交。"
metadata:
  openclaw:
    emoji: "📝"
---

# 日报收集技能

你是日报收集专家，负责从Markdown格式的团队日报中提取信息并保存。

## 核心职责

| 输入 | 输出 | 下游 |
|------|------|------|
| Markdown日报文本 | soc_daily_YYYYMMDD.md | Git仓库 |

---

## 使用场景

1. **用户提供Markdown格式日报**: 需要收集和保存
2. **批量处理多日日报**: 需要一次性收集多天的日报
3. **从文件读取日报**: 日报保存在文件中需要导入

---

## 工作流程

### 标准流程

```
接收Markdown日报
    ↓
解析成员和任务
    ↓
验证日报格式
    ↓
保存为soc_daily_YYYYMMDD.md
    ↓
Git自动提交
```

---

## 使用方法

### 方法1: 直接提供Markdown

用户直接发送Markdown格式的日报:

```
使用日报收集技能

HLQ:
今:
- 修复登录BUG
- 优化性能
明:
- 新增功能

DJZ:
今:
- 测试功能
明:
- 编写文档
```

### 方法2: 从文件读取

```
使用日报收集技能，读取 /path/to/report.md
```

### 方法3: 指定日期

```
使用日报收集技能，日期 2026-03-07

[日报内容...]
```

---

## 日报格式规范

### 标准格式

```markdown
成员ID:
今:
- 任务1
- 任务2
明:
- 任务3
```

### 示例

```markdown
HLQ:
今:
- #104591 编辑器下脏数据功能罗列
- 鸿蒙 - Ab打包疏通
- 下载中心 - 地图分包标签规则
明:
- 继续跟进鸿蒙打包问题

DJZ:
今:
- 明确泄露的定义, 泄露报告可读性优化
- 打包内存高问题方案确定
明:
- 内存优化测试
```

---

## 处理逻辑

### 1. 解析成员

识别大写字母开头的成员ID (2-4个字母):
- HLQ
- DJZ
- XZY
- ...

### 2. 提取任务

- **今**: 今日完成的任务
- **明**: 明日计划的任务

支持的任务格式:
- `- 任务描述`
- `• 任务描述`
- `* 任务描述`

### 3. 验证日报

检查:
- 是否有成员信息
- 是否有任务内容
- 格式是否正确

### 4. 保存日报

文件命名: `soc_daily_YYYYMMDD.md`

保存位置: `../weekly-report-system/data/daily/`（默认，相对于技能目录）

> 💡 **可配置**：可在 `weekly-report-system/data/config/system_config.json` 中设置 `output_dir` 来自定义输出路径

### 5. Git提交

自动提交到Git仓库，提交信息: `添加日报 YYYYMMDD`

---

## 输出示例

### 成功输出

```
✅ 日报收集成功

📄 文件: ../weekly-report-system/data/daily/soc_daily_20260307.md
👥 成员数: 10
📊 任务统计:
  - HLQ: 3项今日, 1项明日
  - DJZ: 2项今日, 1项明日
  - ...

✅ 已提交到Git
```

### 失败输出

```
❌ 日报收集失败

错误:
- 成员HLQ缺少"今"或"明"标记
- 格式不正确

请检查日报格式后重试
```

---

## 集成说明

本技能与以下系统模块集成:

1. **日报收集模块** (`src/modules/daily_collector.py`)
   - 核心解析逻辑
   - 文件保存功能

2. **Markdown解析器** (`src/core/parser.py`)
   - 解析Markdown格式
   - 提取成员任务

3. **Git操作** (`src/core/git_helper.py`)
   - 自动提交到Git
   - 版本控制

4. **配置管理** (`src/modules/config_manager.py`)
   - 读取成员配置
   - 管理系统设置

---

## 配置文件

### 成员配置

位置: `data/config/members.json`

包含10名团队成员的信息:
- DCL, HLQ, HWL, PGH, ALB, KRP, YY, ZSH, XZY, DJZ

### 系统配置

位置: `data/config/system_config.json`

包含:
- `output_dir`: 自定义输出目录（可选，默认使用 data/ 目录）
- LLM模型配置
- 定时任务配置
- 邮件配置

**配置示例**:
```json
{
  "output_dir": "~/Documents/Report",
  "llm": {
    "model": "zai/glm-5"
  }
}
```

> 💡 **说明**：如果不设置 `output_dir` 或设为 `null`，将使用默认的 `../weekly-report-system/data/` 目录

---

## 项目位置

**周报系统**: `../weekly-report-system/`（相对于技能目录）

**日报存储**: `../weekly-report-system/data/daily/`（默认）

**使用文档**: `README.md`

---

## 错误处理

### 常见错误

1. **格式错误**: Markdown格式不符合规范
   - 解决: 按照标准格式重新组织

2. **成员不存在**: 成员ID未在配置中
   - 解决: 更新 `members.json` 添加成员

3. **Git提交失败**: Git操作出错
   - 解决: 检查Git仓库状态

---

## 注意事项

1. ✅ 日报日期默认为当天，可通过 `--date` 参数指定
2. ✅ 支持10名团队成员，可在配置中扩展
3. ✅ 自动去重相同的任务
4. ✅ Git提交失败不影响日报保存
5. ✅ 所有操作都有日志记录

---

## 示例对话

**用户**:
```
使用日报收集技能

HLQ:
今:
- 完成周报系统开发
- 修复2个BUG
明:
- 继续优化性能

DJZ:
今:
- 测试周报功能
明:
- 编写使用文档
```

**助手**:
```
✅ 日报收集成功

📄 文件: ../weekly-report-system/data/daily/soc_daily_20260307.md
👥 成员数: 2
📊 任务统计:
  - HLQ: 2项今日, 1项明日
  - DJZ: 1项今日, 1项明日

✅ 已提交到Git (commit: abc1234)
```

---

## 技能信息

- **创建时间**: 2026-03-07
- **版本**: 1.0.0
- **作者**: Claw
- **项目**: 寨报自动化系统
