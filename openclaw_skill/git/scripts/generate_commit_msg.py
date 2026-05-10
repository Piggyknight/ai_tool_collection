#!/usr/bin/env python3
"""
Commit 消息生成脚本
根据任务信息生成符合 Conventional Commits 规范的消息
"""

import sys
import re
from datetime import datetime


def infer_type(task_name: str, task_description: str = '') -> str:
    """从任务名称推断 commit 类型"""

    name_lower = task_name.lower()
    desc_lower = task_description.lower()

    # 修复类
    fix_keywords = ['修复', 'fix', 'bug', '错误', '问题', '异常']
    if any(kw in name_lower or kw in desc_lower for kw in fix_keywords):
        return 'fix'

    # 文档类
    doc_keywords = ['文档', 'doc', 'readme', '说明']
    if any(kw in name_lower or kw in desc_lower for kw in doc_keywords):
        return 'docs'

    # 测试类
    test_keywords = ['测试', 'test', '单元测试', '集成测试']
    if any(kw in name_lower or kw in desc_lower for kw in test_keywords):
        return 'test'

    # 重构类
    refactor_keywords = ['重构', 'refactor', '优化', '清理']
    if any(kw in name_lower or kw in desc_lower for kw in refactor_keywords):
        return 'refactor'

    # 默认为新功能
    return 'feat'


def infer_scope(task_name: str, files: list = None) -> str:
    """推断 commit 的 scope"""

    # 从任务名称提取
    name_lower = task_name.lower()

    scopes = {
        '用户': 'user',
        '订单': 'order',
        '支付': 'payment',
        '商品': 'product',
        '工具': 'utils',
        '日志': 'logger',
        '配置': 'config',
        '数据库': 'db',
        'api': 'api',
        '认证': 'auth',
    }

    for cn, en in scopes.items():
        if cn in name_lower:
            return en

    # 从文件路径提取
    if files:
        for file in files:
            if 'modules/' in file:
                match = re.search(r'modules/([^/]+)/', file)
                if match:
                    return match.group(1)
            elif 'core/' in file:
                match = re.search(r'core/([^/]+)/', file)
                if match:
                    return match.group(1)

    return ''


def generate_commit_message(
    task_id: str,
    task_name: str,
    task_description: str = '',
    files: list = None,
    breaking_change: bool = False,
    closes_issues: list = None
) -> str:
    """生成完整的 commit 消息"""

    # 推断类型和范围
    commit_type = infer_type(task_name, task_description)
    scope = infer_scope(task_name, files)

    # 简化任务名称作为描述
    description = task_name
    if len(description) > 50:
        description = description[:47] + '...'

    # 构建标题行
    if scope:
        title = f"{commit_type}({scope}): {description}"
    else:
        title = f"{commit_type}: {description}"

    # 构建 body
    body_parts = []

    if task_description:
        body_parts.append(task_description)

    if files:
        file_list = '\n'.join([f"- {f}" for f in files[:10]])
        if len(files) > 10:
            file_list += f"\n- ... 还有 {len(files) - 10} 个文件"
        body_parts.append(f"修改的文件:\n{file_list}")

    # 构建 footer
    footer_parts = []

    footer_parts.append(f"Task: {task_id}")

    if closes_issues:
        footer_parts.append(f"Closes: {', '.join(closes_issues)}")

    if breaking_change:
        footer_parts.append("Breaking change: 此更改不兼容旧版本")

    # 组合
    message = title

    if body_parts:
        message += "\n\n" + "\n\n".join(body_parts)

    if footer_parts:
        message += "\n\n" + "\n".join(footer_parts)

    return message


def generate_simple_message(task_id: str, task_name: str) -> str:
    """生成简单的 commit 消息"""

    commit_type = infer_type(task_name)
    scope = infer_scope(task_name)

    if scope:
        return f"{commit_type}({scope}): {task_name}"
    else:
        return f"{commit_type}: {task_name}"


def main():
    if len(sys.argv) < 3:
        print("用法: python generate_commit_msg.py <task_id> <task_name> [--description <desc>] [--files <file1,file2>]")
        print("")
        print("示例:")
        print("  python generate_commit_msg.py TASK-001 '实现用户登录功能'")
        print("  python generate_commit_msg.py TASK-002 '修复订单计算错误' --description '修复金额计算时的精度丢失问题'")
        print("  python generate_commit_msg.py TASK-003 '重构日志模块' --files 'src/core/logger/index.ts,src/core/logger/formatter.ts'")
        sys.exit(1)

    task_id = sys.argv[1]
    task_name = sys.argv[2]

    # 解析可选参数
    description = ''
    files = []

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--description' and i + 1 < len(sys.argv):
            description = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--files' and i + 1 < len(sys.argv):
            files = sys.argv[i + 1].split(',')
            i += 2
        else:
            i += 1

    # 生成消息
    message = generate_commit_message(task_id, task_name, description, files)

    print("=" * 60)
    print("生成的 Commit 消息:")
    print("=" * 60)
    print(message)
    print("=" * 60)

    # 同时输出简单版本
    simple = generate_simple_message(task_id, task_name)
    print(f"\n简化版本: {simple}")


if __name__ == "__main__":
    main()
