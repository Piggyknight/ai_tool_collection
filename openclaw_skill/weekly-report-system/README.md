# 寏与日报自动化系统

自动化的团队日报收集、周报生成、分发系统

## 功能特性

- ✅ 日报Markdown格式解析与存储
- ✅ 团队周报自动汇总（去重+LLM润色）
- ✅ 个人周报自动生成
- ✅ 定时任务自动执行（每周六晚20点）
- ✅ 邮件自动分发
- ✅ Git版本控制

## 技术栈
- **Python 3.8+**
- **OpenClaw GLM模型** (zai/glm-5) - 文本润色
- **OpenClaw Cron** - 定时任务
- **OpenClaw Email** - 邮件发送
- **Git** - 版本控制

## 快速开始

### 1. 安装依赖
```bash
cd ~/Documents/weekly-report-system
pip install -r requirements.txt
```

### 2. 配置团队成员
编辑 `data/config/members.json`：
从已有初版系统的memory中提取10名成员信息：

```json
{
  "version": "1.0",
  "members": {
    "DCL": {"id": "DCL", "name": "邓春雷", "email": "daicl@wooduan.com", "active": true},
    "HLQ": {"id": "HLQ", "name": "黄良强", "email": "hlqiang@wooduan.com", "active": true},
    "HWL": {"id": "HWL", "name": "黄万路", email": "hwanlu@wooduan.com", "active": true},
    "PGH": {"id": "PGH", "name": "裴光辉", "email": "pguangh@wooduan.com", "active": true},
    "ALB": {"id": "ALB", "name": "阿勒拜", email": "alb@wooduan.com", "active": true},
    "KRP": {"id": "KRP", "name": "孔荣平", email": "krongp@wooduan.com", "active": true},
    "YY": {"id": "YY", "name": "杨洋", email": "yyang@wooduan.com", "active": true},
    "ZSH": {"id": "ZSH", "name": "张三华", email": "zsh@wooduan.com", "active": true},
    "XZY": {"id": "XZY", "name": "肖志勇",  "email": "xzyong@wooduan.com", "active": true},
    "DJZ": {"id": "DJZ", "name": "杜建中",  "email": "djz@wooduan.com", "active": true}
  },
  "admin": {
    "name": "Kai",
    "email": "kai@wooduan.com"
  }
}
```

### 3. 生成日报
```bash
python scripts/collect_daily.py --input report.md --date 2026-03-07
```

### 4. 生成周报
```bash
python scripts/generate_weekly.py --week 2026-W10 --send-email
```

### 5. 查看周报
```bash
ls data/weekly/team/
ls data/weekly/members/
```

### 6. 配置定时任务
```bash
python scripts/setup_cron.py --enable
```
定时任务将在每周六晚20点自动执行。

## 目录结构
```
weekly-report-system/
├── src/
│   ├── core/              # 基础工具层（6个模块）
│   └── modules/          # 业务逻辑层（4个模块）
├── data/
│   ├── daily/             # 日报存储
│   ├── weekly/            # 周报存储
│   └── config/            # 配置文件
├── tests/                # 单元测试
├── scripts/              # 入口脚本
└── docs/               # 文档
```

## 使用示例

查看 `tests/integration/` 目录了解集成测试。

```

## 许可证
内部使用
