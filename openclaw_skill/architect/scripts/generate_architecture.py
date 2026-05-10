#!/usr/bin/env python3
"""
架构文档生成脚本
根据需求拆分文档自动生成初始架构文档和任务列表
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path


def parse_requirements(requirements_path: str) -> dict:
    """解析需求拆分文档"""

    with open(requirements_path, 'r', encoding='utf-8') as f:
        content = f.read()

    requirements = {
        'project_name': '',
        'features': [],
        'non_functional': {},
        'constraints': [],
        'deliverables': []
    }

    # 提取项目名称
    project_match = re.search(r'项目名称[：:]\s*(.+)', content)
    if project_match:
        requirements['project_name'] = project_match.group(1).strip()

    # 提取功能需求（简化版，实际应更复杂）
    feature_sections = re.findall(r'###\s*\d+\.\d+\s+(.+?)\n(.+?)(?=###|\n##|\Z)', content, re.DOTALL)
    for name, desc in feature_sections:
        requirements['features'].append({
            'name': name.strip(),
            'description': desc.strip()[:200]  # 截取前200字符
        })

    return requirements


def generate_architecture_doc(requirements: dict, output_dir: str) -> str:
    """生成架构文档"""

    project_name = requirements.get('project_name', '未命名项目')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 生成目录结构
    feature_dirs = "\n│       ".join([f"├── {_slugify(f['name'])}/        # {f['name']}" for f in requirements['features'][:3]])
    dir_structure = f"""{project_name}/
├── src/
│   ├── core/              # 下层：基础工具层
│   │   ├── utils/         # 通用工具函数
│   │   ├── types/         # 类型定义
│   │   ├── errors/        # 错误处理
│   │   └── config/        # 配置管理
│   │
│   └── modules/           # 上层：业务逻辑层
│       ├── shared/        # 共享业务逻辑
│       {feature_dirs}
│
├── tests/
│   ├── unit/              # 单元测试
│   └── integration/       # 集成测试
│
├── docs/                  # 文档
├── scripts/               # 脚本
└── logs/                  # 日志"""

    # 生成模块设计
    module_design = ""
    for i, feature in enumerate(requirements['features'][:5], 1):
        slug = _slugify(feature['name'])
        module_design += f"""
### 4.2.{i} {feature['name']}
- **职责**：{feature['description'][:100]}
- **文件**：`src/modules/{slug}/`
- **依赖**：core/utils, core/types
- **接口协议**：

```typescript
interface {_pascal_case(feature['name'])}Input {{
  // 待定义
}}

interface {_pascal_case(feature['name'])}Output {{
  success: boolean;
  data?: unknown;
  error?: ErrorCode;
}}
```
"""

    doc = f"""# 架构文档

> 项目名称：{project_name}
> 版本：1.0.0
> 创建时间：{timestamp}
> 架构师：Claw (architect)
> 状态：设计中

## 1. 系统概述

{project_name} 系统架构设计文档，基于两层结构原则。

## 2. 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 语言 | TypeScript | 5.x | 类型安全 |
| 运行时 | Node.js | 20.x | 后端运行环境 |
| 测试 | Vitest | latest | 单元测试框架 |
| 日志 | Pino | latest | 高性能日志 |

## 3. 目录结构

```
{dir_structure}
```

## 4. 模块设计

### 4.1 下层：基础工具层

#### 4.1.1 utils
- **职责**：通用工具函数
- **文件**：`src/core/utils/`
- **导出接口**：
  - `formatDate(date: Date): string` — 日期格式化
  - `generateId(): string` — 唯一ID生成
  - `deepClone<T>(obj: T): T` — 深拷贝

#### 4.1.2 types
- **职责**：类型定义
- **文件**：`src/core/types/`
- **导出类型**：
  - `Result<T, E>` — 通用结果类型
  - `AsyncResult<T, E>` — 异步结果类型

#### 4.1.3 errors
- **职责**：错误处理
- **文件**：`src/core/errors/`
- **导出接口**：
  - `AppError` — 应用错误类型
  - `handleError(error: unknown): AppError` — 错误处理

### 4.2 上层：业务逻辑层
{module_design}

## 5. 通信协议

### 5.1 模块间通信

| 调用方 | 被调用方 | 协议 | 数据格式 |
|--------|---------|------|---------|
| 业务层 | 工具层 | 函数调用 | TypeScript 对象 |

### 5.2 错误码规范

| 错误码 | 含义 | 处理建议 |
|--------|------|---------|
| E1000 | 未知错误 | 记录日志，人工排查 |
| E1001 | 输入无效 | 检查输入参数 |
| E1002 | 资源未找到 | 检查资源ID |

## 6. 数据模型

[待根据具体需求补充]

## 7. 非功能性设计

### 7.1 性能
- 响应时间 < 200ms (P95)
- 支持并发请求

### 7.2 安全
- 输入验证
- 错误不暴露敏感信息

### 7.3 可扩展性
- 模块化设计
- 插件式架构

## 8. 部署架构

[待根据具体需求补充]

## 9. 迭代记录

| 版本 | 日期 | 变更内容 | 原因 |
|------|------|---------|------|
| 1.0.0 | {timestamp} | 初始版本 | 需求拆分完成 |
"""

    output_path = os.path.join(output_dir, '架构文档.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc)

    return output_path


def generate_task_list(requirements: dict, output_dir: str) -> str:
    """生成开发任务列表"""

    project_name = requirements.get('project_name', '未命名项目')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 生成基础工具层任务
    tool_tasks = """
## 第一阶段：基础工具层

### TASK-001: utils 工具模块
- **优先级**：P0
- **类型**：工具开发
- **预估工时**：2h
- **依赖**：无
- **文件**：`src/core/utils/`
- **描述**：
  - 实现日期格式化函数
  - 实现唯一ID生成函数
  - 实现深拷贝函数
- **验收标准**：
  - [ ] 单元测试覆盖率 ≥ 80%
  - [ ] 所有测试用例通过
  - [ ] 代码符合规范

### TASK-002: types 类型定义
- **优先级**：P0
- **类型**：工具开发
- **预估工时**：1h
- **依赖**：无
- **文件**：`src/core/types/`
- **描述**：
  - 定义 Result 类型
  - 定义 AsyncResult 类型
- **验收标准**：
  - [ ] 类型定义完整
  - [ ] 类型测试通过

### TASK-003: errors 错误处理
- **优先级**：P0
- **类型**：工具开发
- **预估工时**：1h
- **依赖**：TASK-002
- **文件**：`src/core/errors/`
- **描述**：
  - 定义 AppError 类型
  - 实现 handleError 函数
- **验收标准**：
  - [ ] 单元测试覆盖率 ≥ 80%
  - [ ] 所有测试用例通过
"""

    # 生成业务层任务
    business_tasks = "\n## 第二阶段：业务逻辑层\n"
    task_num = 4

    for feature in requirements['features'][:5]:
        slug = _slugify(feature['name'])
        business_tasks += f"""
### TASK-{task_num:03d}: {feature['name']}
- **优先级**：P0
- **类型**：业务开发
- **预估工时**：4h
- **依赖**：TASK-001, TASK-002, TASK-003
- **文件**：`src/modules/{slug}/`
- **描述**：
  - 实现 {feature['name']} 核心功能
- **验收标准**：
  - [ ] 集成测试通过
  - [ ] 冒烟测试通过
  - [ ] 符合架构文档定义的接口协议
"""
        task_num += 1

    # 生成集成任务
    integration_tasks = f"""
## 第三阶段：集成与优化

### TASK-{task_num:03d}: 整体集成
- **优先级**：P0
- **类型**：集成
- **预估工时**：2h
- **依赖**：所有业务模块完成
- **描述**：
  - 模块联调
  - 端到端测试
- **验收标准**：
  - [ ] 所有模块正常协作
  - [ ] 无性能瓶颈
"""

    doc = f"""# 开发任务列表

> 项目名称：{project_name}
> 创建时间：{timestamp}
> 架构师：Claw (architect)
> 来源文档：架构文档 v1.0.0

## 任务优先级说明

- P0：核心功能，必须完成
- P1：重要功能，应完成
- P2：增强功能，可延后

---

{tool_tasks}
{business_tasks}
{integration_tasks}
---

## 任务统计

| 指标 | 数量 |
|------|------|
| 总任务数 | {task_num} |
| P0 任务 | {task_num} |
| P1 任务 | 0 |
| P2 任务 | 0 |
"""

    output_path = os.path.join(output_dir, '开发任务列表.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc)

    return output_path


def _slugify(text: str) -> str:
    """将文本转换为 slug 格式"""
    # 简单实现，实际应处理中文等
    return text.lower().replace(' ', '-').replace('_', '-')


def _pascal_case(text: str) -> str:
    """将文本转换为 PascalCase"""
    words = text.replace('-', ' ').replace('_', ' ').split()
    return ''.join(word.capitalize() for word in words)


def main():
    if len(sys.argv) < 2:
        print("用法: python generate_architecture.py <需求拆分文档路径> [输出目录]")
        print("示例: python generate_architecture.py docs/需求拆分文档.md docs/")
        sys.exit(1)

    requirements_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "docs"

    if not os.path.exists(requirements_path):
        print(f"错误: 找不到需求文档 {requirements_path}")
        sys.exit(1)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 解析需求
    print(f"📖 解析需求文档: {requirements_path}")
    requirements = parse_requirements(requirements_path)
    print(f"   项目名称: {requirements['project_name']}")
    print(f"   功能模块: {len(requirements['features'])} 个")

    # 生成架构文档
    print("\n🏗️  生成架构文档...")
    arch_path = generate_architecture_doc(requirements, output_dir)
    print(f"   ✅ 已生成: {arch_path}")

    # 生成任务列表
    print("\n📋 生成开发任务列表...")
    task_path = generate_task_list(requirements, output_dir)
    print(f"   ✅ 已生成: {task_path}")

    print(f"\n✨ 完成! 请查看 {output_dir} 目录")


if __name__ == "__main__":
    main()
