# 输出目录配置说明

## 默认行为

如果不设置 `output_dir`，日报和周报将保存在项目目录中：
- 日报: `weekly-report-system/data/daily/`
- 周报: `weekly-report-system/data/weekly/`

## 自定义输出目录

编辑 `system_config.json` 文件，添加 `output_dir` 配置：

```json
{
  "version": "1.0",
  "output_dir": "~/Documents/Report",
  "llm": {
    "model": "zai/glm-5",
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "cron": {
    "weekly_time": "0 20 * * 6",
    "timezone": "Asia/Shanghai"
  },
  "email": {
    "enabled": true,
    "retry_times": 3
  }
}
```

### 输出目录结构

设置 `output_dir` 后，文件将保存到：

```
~/Documents/Report/
├── daily/                    # 日报
│   ├── soc_daily_20260307.md
│   └── soc_daily_20260308.md
└── weekly/                   # 周报
    ├── team/
    │   └── team_weekly_20260302.md
    └── members/
        ├── soc_weekly_20260302_20260307_HLQ.md
        └── soc_weekly_20260302_20260307_DJZ.md
```

## 路径格式

支持以下格式：
- 绝对路径: `/Users/kai/Documents/Report`
- 用户目录: `~/Documents/Report`
- 相对路径: `../Report` (相对于 weekly-report-system 目录)

## 示例配置

### macOS/Linux
```json
{
  "output_dir": "~/Documents/Report"
}
```

### Windows
```json
{
  "output_dir": "C:\\Users\\Kai\\Documents\\Report"
}
```

### 使用默认目录
```json
{
  "output_dir": null
}
```

或者直接删除 `output_dir` 配置项。

## 注意事项

1. **目录权限**: 确保程序有权限在指定的目录创建文件
2. **自动创建**: 如果目录不存在，程序会自动创建
3. **Git 提交**: 日报和周报仍会提交到 Git 仓库（在项目目录中），只是文件保存在自定义位置
