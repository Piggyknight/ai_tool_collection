#!/usr/bin/env python3
"""
任务统计数据管理脚本
管理任务的耗时、Token消耗等统计数据
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


DEFAULT_STATS_FILE = "docs/task-stats.json"


class TaskStats:
    """任务统计管理器"""

    def __init__(self, stats_file: str = None, project_dir: str = None):
        self.project_dir = project_dir or os.getcwd()
        self.stats_file = stats_file or os.path.join(self.project_dir, DEFAULT_STATS_FILE)
        self._ensure_stats_file()

    def _ensure_stats_file(self):
        """确保统计文件存在"""
        if not os.path.exists(self.stats_file):
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            self._save(self._create_empty_stats())

    def _create_empty_stats(self) -> dict:
        """创建空的统计结构"""
        project_name = os.path.basename(self.project_dir)
        return {
            "project": project_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tasks": {},
            "summary": {
                "total_tasks": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "failed": 0,
                "total_duration_seconds": 0,
                "total_tokens": {
                    "input": 0,
                    "output": 0
                }
            }
        }

    def _load(self) -> dict:
        """加载统计数据"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._create_empty_stats()

    def _save(self, stats: dict):
        """保存统计数据"""
        stats["updated_at"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    def start_task(self, task_id: str, task_name: str, priority: str = "P0") -> dict:
        """
        开始任务，记录开始时间

        Args:
            task_id: 任务ID，如 "TASK-001"
            task_name: 任务名称
            priority: 优先级，P0/P1/P2

        Returns:
            更新后的任务数据
        """
        stats = self._load()

        stats["tasks"][task_id] = {
            "name": task_name,
            "status": "in_progress",
            "priority": priority,
            "timeline": {
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "duration_seconds": 0
            },
            "agents": {},
            "retries": 0,
            "total_tokens": {
                "input": 0,
                "output": 0
            }
        }

        self._update_summary(stats)
        self._save(stats)

        return stats["tasks"][task_id]

    def record_agent_call(
        self,
        task_id: str,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_seconds: int = 0
    ) -> dict:
        """
        记录 Agent 调用

        Args:
            task_id: 任务ID
            agent_name: Agent名称，如 "developer", "debug", "qa"
            model: 使用的模型
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            duration_seconds: 执行耗时（秒）

        Returns:
            更新后的任务数据
        """
        stats = self._load()

        if task_id not in stats["tasks"]:
            print(f"警告: 任务 {task_id} 不存在")
            return {}

        task = stats["tasks"][task_id]

        if agent_name not in task["agents"]:
            task["agents"][agent_name] = {
                "model": model,
                "input_tokens": 0,
                "output_tokens": 0,
                "calls": 0,
                "total_duration_seconds": 0
            }

        agent = task["agents"][agent_name]
        agent["input_tokens"] += input_tokens
        agent["output_tokens"] += output_tokens
        agent["calls"] += 1
        agent["total_duration_seconds"] += duration_seconds

        # 更新任务总计
        task["total_tokens"]["input"] = sum(a["input_tokens"] for a in task["agents"].values())
        task["total_tokens"]["output"] = sum(a["output_tokens"] for a in task["agents"].values())

        self._update_summary(stats)
        self._save(stats)

        return task

    def complete_task(self, task_id: str) -> dict:
        """
        完成任务

        Args:
            task_id: 任务ID

        Returns:
            更新后的任务数据
        """
        stats = self._load()

        if task_id not in stats["tasks"]:
            print(f"警告: 任务 {task_id} 不存在")
            return {}

        task = stats["tasks"][task_id]
        task["status"] = "completed"
        task["timeline"]["completed_at"] = datetime.now().isoformat()

        # 计算耗时
        started = datetime.fromisoformat(task["timeline"]["started_at"])
        completed = datetime.now()
        task["timeline"]["duration_seconds"] = int((completed - started).total_seconds())

        self._update_summary(stats)
        self._save(stats)

        return task

    def fail_task(self, task_id: str, error: str = None) -> dict:
        """
        标记任务失败

        Args:
            task_id: 任务ID
            error: 错误信息

        Returns:
            更新后的任务数据
        """
        stats = self._load()

        if task_id not in stats["tasks"]:
            print(f"警告: 任务 {task_id} 不存在")
            return {}

        task = stats["tasks"][task_id]
        task["status"] = "failed"
        task["error"] = error

        self._update_summary(stats)
        self._save(stats)

        return task

    def increment_retry(self, task_id: str) -> int:
        """
        增加重试次数

        Args:
            task_id: 任务ID

        Returns:
            当前重试次数
        """
        stats = self._load()

        if task_id not in stats["tasks"]:
            print(f"警告: 任务 {task_id} 不存在")
            return 0

        task = stats["tasks"][task_id]
        task["retries"] += 1

        self._save(stats)
        return task["retries"]

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务统计"""
        stats = self._load()
        return stats["tasks"].get(task_id)

    def get_summary(self) -> dict:
        """获取统计汇总"""
        stats = self._load()
        return stats["summary"]

    def get_all_stats(self) -> dict:
        """获取完整统计数据"""
        return self._load()

    def _update_summary(self, stats: dict):
        """更新汇总统计"""
        tasks = stats["tasks"]

        total = len(tasks)
        completed = sum(1 for t in tasks.values() if t["status"] == "completed")
        in_progress = sum(1 for t in tasks.values() if t["status"] == "in_progress")
        failed = sum(1 for t in tasks.values() if t["status"] == "failed")
        pending = total - completed - in_progress - failed

        total_duration = sum(
            t["timeline"].get("duration_seconds", 0)
            for t in tasks.values()
        )

        total_input = sum(t["total_tokens"]["input"] for t in tasks.values())
        total_output = sum(t["total_tokens"]["output"] for t in tasks.values())

        stats["summary"] = {
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "failed": failed,
            "total_duration_seconds": total_duration,
            "total_tokens": {
                "input": total_input,
                "output": total_output
            }
        }


def format_duration(seconds: int) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分钟{secs}秒" if secs else f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分钟" if minutes else f"{hours}小时"


def format_tokens(tokens: int) -> str:
    """格式化Token数量"""
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1000000:
        return f"{tokens / 1000:.1f}K"
    else:
        return f"{tokens / 1000000:.2f}M"


def main():
    if len(sys.argv) < 2:
        print("用法: python task_stats.py <操作> [参数...]")
        print("")
        print("操作:")
        print("  start <task_id> <task_name> [priority]")
        print("       开始任务，记录开始时间")
        print("")
        print("  record <task_id> <agent> <model> <input_tokens> <output_tokens> [duration]")
        print("       记录Agent调用")
        print("")
        print("  complete <task_id>")
        print("       完成任务")
        print("")
        print("  retry <task_id>")
        print("       增加重试次数")
        print("")
        print("  fail <task_id> [error]")
        print("       标记任务失败")
        print("")
        print("  get <task_id>")
        print("       获取任务统计")
        print("")
        print("  summary")
        print("       显示统计汇总")
        print("")
        print("示例:")
        print("  python task_stats.py start TASK-001 '实现工具模块' P0")
        print("  python task_stats.py record TASK-001 developer zai/glm-5 15000 3500 300")
        print("  python task_stats.py complete TASK-001")
        print("  python task_stats.py summary")
        sys.exit(1)

    operation = sys.argv[1]

    # 尝试从当前目录找到项目
    project_dir = os.getcwd()
    while project_dir != '/' and not os.path.exists(os.path.join(project_dir, 'project.json')):
        project_dir = os.path.dirname(project_dir)

    stats = TaskStats(project_dir=project_dir)

    if operation == "start":
        if len(sys.argv) < 4:
            print("用法: python task_stats.py start <task_id> <task_name> [priority]")
            sys.exit(1)

        task_id = sys.argv[2]
        task_name = sys.argv[3]
        priority = sys.argv[4] if len(sys.argv) > 4 else "P0"

        result = stats.start_task(task_id, task_name, priority)
        print(f"✅ 任务已开始: {task_id}")
        print(f"   名称: {task_name}")
        print(f"   优先级: {priority}")
        print(f"   开始时间: {result['timeline']['started_at']}")

    elif operation == "record":
        if len(sys.argv) < 7:
            print("用法: python task_stats.py record <task_id> <agent> <model> <input_tokens> <output_tokens> [duration]")
            sys.exit(1)

        task_id = sys.argv[2]
        agent = sys.argv[3]
        model = sys.argv[4]
        input_tokens = int(sys.argv[5])
        output_tokens = int(sys.argv[6])
        duration = int(sys.argv[7]) if len(sys.argv) > 7 else 0

        result = stats.record_agent_call(task_id, agent, model, input_tokens, output_tokens, duration)
        print(f"✅ Agent调用已记录: {agent}")
        print(f"   任务: {task_id}")
        print(f"   Token: {format_tokens(input_tokens)} 输入 / {format_tokens(output_tokens)} 输出")
        print(f"   任务总Token: {format_tokens(result['total_tokens']['input'])} / {format_tokens(result['total_tokens']['output'])}")

    elif operation == "complete":
        if len(sys.argv) < 3:
            print("用法: python task_stats.py complete <task_id>")
            sys.exit(1)

        task_id = sys.argv[2]
        result = stats.complete_task(task_id)
        print(f"✅ 任务已完成: {task_id}")
        print(f"   耗时: {format_duration(result['timeline']['duration_seconds'])}")
        print(f"   总Token: {format_tokens(result['total_tokens']['input'])} / {format_tokens(result['total_tokens']['output'])}")

    elif operation == "retry":
        if len(sys.argv) < 3:
            print("用法: python task_stats.py retry <task_id>")
            sys.exit(1)

        task_id = sys.argv[2]
        retries = stats.increment_retry(task_id)
        print(f"⚠️  任务重试: {task_id}")
        print(f"   当前重试次数: {retries}/5")

    elif operation == "fail":
        if len(sys.argv) < 3:
            print("用法: python task_stats.py fail <task_id> [error]")
            sys.exit(1)

        task_id = sys.argv[2]
        error = sys.argv[3] if len(sys.argv) > 3 else None
        result = stats.fail_task(task_id, error)
        print(f"❌ 任务已标记失败: {task_id}")
        if error:
            print(f"   错误: {error}")

    elif operation == "get":
        if len(sys.argv) < 3:
            print("用法: python task_stats.py get <task_id>")
            sys.exit(1)

        task_id = sys.argv[2]
        result = stats.get_task(task_id)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"任务 {task_id} 不存在")

    elif operation == "summary":
        result = stats.get_summary()
        print("📊 统计汇总")
        print("=" * 40)
        print(f"总任务数: {result['total_tasks']}")
        print(f"已完成: {result['completed']}")
        print(f"进行中: {result['in_progress']}")
        print(f"待开始: {result['pending']}")
        print(f"已失败: {result['failed']}")
        print(f"总耗时: {format_duration(result['total_duration_seconds'])}")
        print(f"总Token: {format_tokens(result['total_tokens']['input'])} 输入 / {format_tokens(result['total_tokens']['output'])} 输出")

    else:
        print(f"未知操作: {operation}")
        sys.exit(1)


if __name__ == "__main__":
    main()
