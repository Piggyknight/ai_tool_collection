#!/usr/bin/env python3
"""
错误文档生成脚本
根据测试结果生成标准格式的错误文档
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path


def parse_test_output(test_output: str) -> dict:
    """解析测试输出"""

    result = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'failures': []
    }

    # 解析 Vitest 格式的测试输出
    # 示例: ❌ tests/unit/date-utils.test.ts > formatDate > 应该处理 null

    lines = test_output.split('\n')
    current_file = None
    current_describe = None

    for line in lines:
        # 匹配测试文件
        file_match = re.search(r'(tests/\S+\.test\.ts)', line)
        if file_match:
            current_file = file_match.group(1)

        # 匹配失败的测试
        fail_match = re.search(r'❌\s+(.+)', line)
        if fail_match and current_file:
            test_name = fail_match.group(1).strip()
            result['failures'].append({
                'file': current_file,
                'name': test_name,
                'error': ''
            })

        # 匹配错误信息
        error_match = re.search(r'Error:\s+(.+)', line)
        if error_match and result['failures']:
            result['failures'][-1]['error'] = error_match.group(1)

    # 解析统计信息
    # 示例: Tests  15 passed | 3 failed (18)
    stats_match = re.search(r'Tests\s+(\d+)\s+passed\s*\|\s*(\d+)\s+failed\s*\((\d+)\)', test_output)
    if stats_match:
        result['passed'] = int(stats_match.group(1))
        result['failed'] = int(stats_match.group(2))
        result['total'] = int(stats_match.group(3))
    else:
        # 简单统计
        result['failed'] = len(result['failures'])
        result['total'] = result['passed'] + result['failed']

    return result


def parse_coverage_output(coverage_output: str) -> dict:
    """解析覆盖率输出"""

    coverage = {
        'lines': 0,
        'functions': 0,
        'branches': 0,
        'statements': 0,
        'files': []
    }

    # 解析覆盖率报告
    # 示例: All files | 85.71 | 75.00 | 90.00 | 85.71

    lines = coverage_output.split('\n')
    for line in lines:
        if 'All files' in line or '% Stmts' in line:
            continue

        # 匹配覆盖率数值
        match = re.search(r'(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)', line)
        if match:
            coverage['statements'] = float(match.group(1))
            coverage['branches'] = float(match.group(2))
            coverage['functions'] = float(match.group(3))
            coverage['lines'] = float(match.group(4))

    return coverage


def generate_error_doc(
    task_id: str,
    task_name: str,
    test_result: dict,
    coverage: dict,
    log_files: list,
    output_dir: str
) -> str:
    """生成错误文档"""

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    retry_count = 1  # 从外部传入

    # 生成失败用例详情
    failure_details = ""
    for i, failure in enumerate(test_result['failures'], 1):
        failure_details += f"""
### TC-{i:03d}: {failure['name']}

**文件**: `{failure['file']}`

**错误信息**:
```
{failure['error'] or '未获取到具体错误信息'}
```

**修复建议**:
1. 检查相关代码逻辑
2. 确认输入参数是否正确
3. 添加必要的边界检查

---

"""

    # 生成日志文件列表
    log_list = "\n".join([f"- `{log}`" for log in log_files]) if log_files else "- 无"

    doc = f"""# 错误文档 - {task_id}

> 任务：{task_name}
> 测试时间：{timestamp}
> 测试人员：QA Agent
> 重试次数：{retry_count}/5

## 测试概要

| 指标 | 数量 |
|------|------|
| 总用例 | {test_result['total']} |
| 通过 | {test_result['passed']} |
| 失败 | {test_result['failed']} |
| 跳过 | {test_result.get('skipped', 0)} |
| 覆盖率 | {coverage['lines']:.1f}% |

---

## 失败的测试用例

{failure_details}

## 覆盖率报告

| 文件 | 行覆盖率 | 函数覆盖率 | 分支覆盖率 | 语句覆盖率 |
|------|---------|-----------|-----------|-----------|
| 总计 | {coverage['lines']:.1f}% | {coverage['functions']:.1f}% | {coverage['branches']:.1f}% | {coverage['statements']:.1f}% |

{"**注意:** 覆盖率未达到 80% 阈值" if coverage['lines'] < 80 else "覆盖率达标"}

---

## 相关日志文件

{log_list}

---

## 下一步

1. 开发者根据本文档修复问题
2. 修复完成后重新提交 QA
3. 当前重试次数：{retry_count}/5
"""

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 写入文件
    output_path = os.path.join(output_dir, f'错误文档_{task_id}.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc)

    return output_path


def generate_test_report(
    task_id: str,
    task_name: str,
    test_result: dict,
    coverage: dict,
    output_dir: str
) -> str:
    """生成测试通过报告"""

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    doc = f"""# 测试报告 - {task_id}

> 任务：{task_name}
> 测试时间：{timestamp}
> 测试人员：QA Agent
> 状态：✅ 通过

## 测试概要

| 指标 | 数量 |
|------|------|
| 总用例 | {test_result['total']} |
| 通过 | {test_result['passed']} |
| 失败 | {test_result['failed']} |
| 跳过 | {test_result.get('skipped', 0)} |
| 覆盖率 | {coverage['lines']:.1f}% |

## 覆盖率详情

| 指标 | 覆盖率 | 状态 |
|------|-------|------|
| 行覆盖率 | {coverage['lines']:.1f}% | {"✅" if coverage['lines'] >= 80 else "⚠️"} |
| 函数覆盖率 | {coverage['functions']:.1f}% | {"✅" if coverage['functions'] >= 80 else "⚠️"} |
| 分支覆盖率 | {coverage['branches']:.1f}% | {"✅" if coverage['branches'] >= 80 else "⚠️"} |
| 语句覆盖率 | {coverage['statements']:.1f}% | {"✅" if coverage['statements'] >= 80 else "⚠️"} |

## 结论

任务 {task_id} 已通过所有测试用例，可以进入下一阶段。
"""

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f'测试报告_{task_id}.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc)

    return output_path


def main():
    if len(sys.argv) < 4:
        print("用法: python generate_error_doc.py <任务ID> <任务名> <测试输出文件> [覆盖率输出文件] [日志目录]")
        print("")
        print("示例:")
        print("  python generate_error_doc.py TASK-001 '实现工具模块' test_output.txt coverage.txt ./logs")
        sys.exit(1)

    task_id = sys.argv[1]
    task_name = sys.argv[2]
    test_output_file = sys.argv[3]
    coverage_file = sys.argv[4] if len(sys.argv) > 4 else None
    log_dir = sys.argv[5] if len(sys.argv) > 5 else None

    # 读取测试输出
    if not os.path.exists(test_output_file):
        print(f"错误: 测试输出文件不存在 {test_output_file}")
        sys.exit(1)

    with open(test_output_file, 'r', encoding='utf-8') as f:
        test_output = f.read()

    # 解析测试结果
    test_result = parse_test_output(test_output)

    # 解析覆盖率
    coverage = {
        'lines': 0,
        'functions': 0,
        'branches': 0,
        'statements': 0
    }
    if coverage_file and os.path.exists(coverage_file):
        with open(coverage_file, 'r', encoding='utf-8') as f:
            coverage_output = f.read()
        coverage = parse_coverage_output(coverage_output)

    # 查找日志文件
    log_files = []
    if log_dir and os.path.exists(log_dir):
        log_files = [
            os.path.join(log_dir, f)
            for f in os.listdir(log_dir)
            if f.endswith('.log')
        ]

    # 生成文档
    output_dir = 'docs/qa'

    if test_result['failed'] > 0:
        # 有失败，生成错误文档
        output_path = generate_error_doc(
            task_id, task_name, test_result, coverage, log_files, output_dir
        )
        print(f"❌ 测试失败")
        print(f"📄 错误文档已生成: {output_path}")
    else:
        # 全部通过，生成测试报告
        output_path = generate_test_report(
            task_id, task_name, test_result, coverage, output_dir
        )
        print(f"✅ 测试通过")
        print(f"📄 测试报告已生成: {output_path}")

    print(f"\n📊 测试统计:")
    print(f"   总用例: {test_result['total']}")
    print(f"   通过: {test_result['passed']}")
    print(f"   失败: {test_result['failed']}")
    print(f"   覆盖率: {coverage['lines']:.1f}%")


if __name__ == "__main__":
    main()
