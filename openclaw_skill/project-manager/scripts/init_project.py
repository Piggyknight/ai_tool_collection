#!/usr/bin/env python3
"""
项目结构初始化脚本
为开发项目创建标准的目录结构和初始文档
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path


def init_project(project_name: str, base_path: str = "."):
    """初始化项目目录结构"""

    project_dir = Path(base_path) / project_name

    # 创建目录结构
    dirs = [
        "docs/qa",
        "docs/archives",
        "src",
        "tests",
        "logs",
        "scripts"
    ]

    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # 创建初始文档
    docs = {
        "docs/需求拆分文档.md": f"""# 需求拆分文档

> 项目名称：{project_name}
> 创建时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
> 项目经理：Claw (project-manager)
> 状态：待填写

## 1. 项目概述

[一句话描述项目目标]

## 2. 功能需求

### 2.1 [模块名称]
- **描述**：[功能描述]
- **优先级**：高/中/低
- **验收标准**：
  - [ ] 标准1
  - [ ] 标准2

## 3. 非功能需求

- **性能**：
- **安全**：
- **兼容性**：

## 4. 约束条件

[列出项目约束]

## 5. 交付物

- [ ] 源代码
- [ ] 测试用例
- [ ] 文档
""",
        "docs/项目开发进度报告.md": f"""# 项目开发进度报告

> 项目名称：{project_name}
> 更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
> 当前状态：等待需求拆分

## 总体进度

| 指标 | 数值 |
|------|------|
| 总任务数 | 0 |
| 已完成 | 0 |
| 进行中 | 0 |
| 待开始 | 0 |
| 阻塞中 | 0 |

## 任务详情

[等待架构师输出开发任务列表]

## 阻塞记录

| 时间 | 任务 | 原因 | 处理状态 |
|------|------|------|---------|
| - | - | - | - |

## 变更日志

- {datetime.now().strftime("%Y-%m-%d %H:%M")} 项目初始化
""",
        "docs/archives/.gitkeep": "",
        "docs/qa/.gitkeep": "",
        "tests/.gitkeep": "",
        "logs/.gitkeep": "",
        "scripts/.gitkeep": ""
    }

    for filepath, content in docs.items():
        file_path = project_dir / filepath
        if content:
            file_path.write_text(content, encoding="utf-8")
        else:
            file_path.touch()

    # 创建项目元数据
    metadata = {
        "project_name": project_name,
        "created_at": datetime.now().isoformat(),
        "status": "initialized",
        "agents": {
            "project_manager": "pending",
            "architect": "pending",
            "developer": "pending",
            "debug": "pending",
            "qa": "pending",
            "git": "pending"
        }
    }

    metadata_path = project_dir / "project.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✅ 项目 '{project_name}' 初始化完成")
    print(f"📁 项目目录: {project_dir.absolute()}")
    print(f"\n目录结构:")
    for d in dirs:
        print(f"  ├── {d}/")
    print(f"  └── project.json")

    return str(project_dir.absolute())


def main():
    if len(sys.argv) < 2:
        print("用法: python init_project.py <项目名称> [基础路径]")
        print("示例: python init_project.py my-awesome-project")
        sys.exit(1)

    project_name = sys.argv[1]
    base_path = sys.argv[2] if len(sys.argv) > 2 else "."

    init_project(project_name, base_path)


if __name__ == "__main__":
    main()
