#!/usr/bin/env python3
"""
统计报告生成脚本
根据 task-stats.json 生成可视化的统计报告
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def format_duration(seconds: int) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分钟" if secs == 0 else f"{minutes}分钟{secs}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时" if minutes == 0 else f"{hours}小时{minutes}分钟"


def format_tokens(tokens: int) -> str:
    """格式化Token数量"""
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1000000:
        return f"{tokens / 1000:.1f}K"
    else:
        return f"{tokens / 1000000:.2f}M"


def format_datetime(iso_str: str) -> str:
    """格式化ISO时间为可读格式"""
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


def get_status_emoji(status: str) -> str:
    """获取状态图标"""
    emojis = {
        "completed": "✅",
        "in_progress": "🔄",
        "pending": "⏳",
        "failed": "❌"
    }
    return emojis.get(status, "❓")


def generate_markdown_report(stats: dict, output_path: str) -> str:
    """生成 Markdown 格式的统计报告"""

    project = stats.get("project", "未命名项目")
    summary = stats.get("summary", {})
    tasks = stats.get("tasks", {})

    # 计算总耗时
    total_duration = summary.get("total_duration_seconds", 0)

    # 计算 Agent 统计
    agent_stats = {}
    for task_id, task in tasks.items():
        for agent_name, agent_data in task.get("agents", {}).items():
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_duration": 0,
                    "model": agent_data.get("model", "unknown")
                }
            agent_stats[agent_name]["calls"] += agent_data.get("calls", 0)
            agent_stats[agent_name]["input_tokens"] += agent_data.get("input_tokens", 0)
            agent_stats[agent_name]["output_tokens"] += agent_data.get("output_tokens", 0)
            agent_stats[agent_name]["total_duration"] += agent_data.get("total_duration_seconds", 0)

    # 生成报告
    report = f"""# 任务统计报告

> 项目：{project}
> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 报告类型：自动生成

---

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 总任务数 | {summary.get('total_tasks', 0)} |
| ✅ 已完成 | {summary.get('completed', 0)} |
| 🔄 进行中 | {summary.get('in_progress', 0)} |
| ⏳ 待开始 | {summary.get('pending', 0)} |
| ❌ 已失败 | {summary.get('failed', 0)} |
| ⏱️ 总耗时 | {format_duration(total_duration)} |
| 📥 Token（输入） | {format_tokens(summary.get('total_tokens', {}).get('input', 0))} |
| 📤 Token（输出） | {format_tokens(summary.get('total_tokens', {}).get('output', 0))} |

---

## 🤖 Agent 效率统计

"""

    if agent_stats:
        report += "| Agent | 模型 | 调用次数 | 输入 Token | 输出 Token | 总耗时 |\n"
        report += "|-------|------|---------|-----------|-----------|--------|\n"

        for agent_name, data in sorted(agent_stats.items()):
            avg_duration = data["total_duration"] // data["calls"] if data["calls"] > 0 else 0
            report += f"| {agent_name} | {data['model']} | {data['calls']} | {format_tokens(data['input_tokens'])} | {format_tokens(data['output_tokens'])} | {format_duration(data['total_duration'])} |\n"
    else:
        report += "_暂无 Agent 调用记录_\n"

    report += f"""
---

## 📋 任务详情

"""

    if tasks:
        report += "| 任务ID | 名称 | 状态 | 耗时 | Token | 重试 |\n"
        report += "|--------|------|------|------|-------|------|\n"

        for task_id, task in sorted(tasks.items()):
            status = task.get("status", "unknown")
            emoji = get_status_emoji(status)
            duration = format_duration(task.get("timeline", {}).get("duration_seconds", 0))
            tokens_in = format_tokens(task.get("total_tokens", {}).get("input", 0))
            tokens_out = format_tokens(task.get("total_tokens", {}).get("output", 0))
            retries = task.get("retries", 0)
            retry_str = f"{retries}/5" if retries > 0 else "0"

            report += f"| {task_id} | {task.get('name', '-')[:20]} | {emoji} {status} | {duration} | {tokens_in}/{tokens_out} | {retry_str} |\n"

        report += "\n---\n\n## 📈 任务时间线\n\n"

        for task_id, task in sorted(tasks.items()):
            timeline = task.get("timeline", {})
            started = format_datetime(timeline.get("started_at", ""))
            completed = format_datetime(timeline.get("completed_at", ""))

            report += f"### {task_id}: {task.get('name', '-')}\n\n"
            report += f"- **开始时间**: {started}\n"
            report += f"- **完成时间**: {completed}\n"
            report += f"- **耗时**: {format_duration(timeline.get('duration_seconds', 0))}\n"
            report += f"- **状态**: {get_status_emoji(task.get('status'))} {task.get('status')}\n"

            if task.get("agents"):
                report += f"\n**Agent 调用**:\n"
                for agent_name, agent_data in task.get("agents", {}).items():
                    report += f"- {agent_name}: {agent_data.get('calls', 0)} 次调用, {format_tokens(agent_data.get('input_tokens', 0))}/{format_tokens(agent_data.get('output_tokens', 0))} tokens\n"

            report += "\n"

    else:
        report += "_暂无任务记录_\n"

    # 完成率统计
    total = summary.get('total_tasks', 0)
    completed = summary.get('completed', 0)
    completion_rate = (completed / total * 100) if total > 0 else 0

    report += f"""
---

## 📉 统计图表

### 完成率

```
总任务: {total}
已完成: {completed} ({completion_rate:.1f}%)
{'█' * int(completion_rate / 5)}{'░' * (20 - int(completion_rate / 5))}
```

### Token 消耗分布

```
输入 Token: {format_tokens(summary.get('total_tokens', {}).get('input', 0))}
输出 Token: {format_tokens(summary.get('total_tokens', {}).get('output', 0))}
比例: {summary.get('total_tokens', {}).get('output', 0) / summary.get('total_tokens', {}).get('input', 1) * 100:.1f}%
```

---

## 💡 建议

"""

    suggestions = []

    if completion_rate < 50:
        suggestions.append("- 项目进度较慢，建议检查是否有阻塞任务")

    avg_retries = sum(t.get("retries", 0) for t in tasks.values()) / len(tasks) if tasks else 0
    if avg_retries > 2:
        suggestions.append("- 平均重试次数较高，建议加强代码质量检查")

    if summary.get("failed", 0) > 0:
        suggestions.append("- 有任务失败，建议优先处理")

    if not suggestions:
        suggestions.append("- 项目进展顺利，继续保持！")

    report += "\n".join(suggestions)

    report += f"""

---

> 报告由 OpenClaw 项目经理 Agent 自动生成
> 数据文件: docs/task-stats.json
"""

    # 写入文件
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return output_path


def generate_json_export(stats: dict, output_path: str) -> str:
    """导出为纯 JSON 格式（便于其他工具处理）"""

    export_data = {
        "project": stats.get("project"),
        "exported_at": datetime.now().isoformat(),
        "summary": stats.get("summary"),
        "tasks": stats.get("tasks")
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    return output_path


def generate_csv_export(stats: dict, output_path: str) -> str:
    """导出为 CSV 格式"""

    import csv

    tasks = stats.get("tasks", {})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # 写入表头
        writer.writerow([
            "task_id", "name", "status", "priority",
            "started_at", "completed_at", "duration_seconds",
            "input_tokens", "output_tokens", "retries"
        ])

        # 写入数据
        for task_id, task in sorted(tasks.items()):
            timeline = task.get("timeline", {})
            tokens = task.get("total_tokens", {})

            writer.writerow([
                task_id,
                task.get("name", ""),
                task.get("status", ""),
                task.get("priority", ""),
                timeline.get("started_at", ""),
                timeline.get("completed_at", ""),
                timeline.get("duration_seconds", 0),
                tokens.get("input", 0),
                tokens.get("output", 0),
                task.get("retries", 0)
            ])

    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法: python generate_stats_report.py <操作> [项目目录]")
        print("")
        print("操作:")
        print("  markdown    生成 Markdown 报告")
        print("  json        导出 JSON 格式")
        print("  csv         导出 CSV 格式")
        print("  all         生成所有格式")
        print("")
        print("示例:")
        print("  python generate_stats_report.py markdown")
        print("  python generate_stats_report.py all /path/to/project")
        sys.exit(1)

    operation = sys.argv[1]
    project_dir = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()

    # 查找 stats 文件
    stats_file = os.path.join(project_dir, "docs", "task-stats.json")

    if not os.path.exists(stats_file):
        print(f"错误: 找不到统计文件 {stats_file}")
        print("请先运行任务以生成统计数据")
        sys.exit(1)

    # 加载统计数据
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)

    docs_dir = os.path.join(project_dir, "docs")

    if operation == "markdown" or operation == "all":
        output_path = os.path.join(docs_dir, "任务统计报告.md")
        result = generate_markdown_report(stats, output_path)
        print(f"✅ Markdown 报告已生成: {result}")

    if operation == "json" or operation == "all":
        output_path = os.path.join(docs_dir, "task-stats-export.json")
        result = generate_json_export(stats, output_path)
        print(f"✅ JSON 导出已完成: {result}")

    if operation == "csv" or operation == "all":
        output_path = os.path.join(docs_dir, "task-stats-export.csv")
        result = generate_csv_export(stats, output_path)
        print(f"✅ CSV 导出已完成: {result}")

    # 显示摘要
    summary = stats.get("summary", {})
    print(f"\n📊 统计摘要:")
    print(f"   总任务: {summary.get('total_tasks', 0)}")
    print(f"   已完成: {summary.get('completed', 0)}")
    print(f"   总耗时: {format_duration(summary.get('total_duration_seconds', 0))}")
    print(f"   总Token: {format_tokens(summary.get('total_tokens', {}).get('input', 0))} / {format_tokens(summary.get('total_tokens', {}).get('output', 0))}")


if __name__ == "__main__":
    main()
