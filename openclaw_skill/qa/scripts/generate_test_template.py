#!/usr/bin/env python3
"""
测试用例模板生成脚本
根据源代码自动生成测试用例模板
"""

import os
import sys
import re
from pathlib import Path


def parse_typescript_file(file_path: str) -> dict:
    """解析 TypeScript 文件，提取函数和类信息"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        'functions': [],
        'classes': [],
        'exports': []
    }

    # 提取导出的函数
    func_pattern = r'export\s+(async\s+)?function\s+(\w+)\s*\(([^)]*)\)(\s*:\s*([^{\n]+))?'
    for match in re.finditer(func_pattern, content):
        result['functions'].append({
            'name': match.group(2),
            'params': match.group(3),
            'return_type': match.group(5) or 'unknown',
            'is_async': bool(match.group(1))
        })

    # 提取导出的类
    class_pattern = r'export\s+class\s+(\w+)(?:\s+extends\s+(\w+))?'
    for match in re.finditer(class_pattern, content):
        class_name = match.group(1)
        class_methods = extract_class_methods(content, class_name)
        result['classes'].append({
            'name': class_name,
            'parent': match.group(2),
            'methods': class_methods
        })

    # 提取所有导出
    export_pattern = r'export\s+(?:const|let|var|function|class|interface|type)\s+(\w+)'
    result['exports'] = re.findall(export_pattern, content)

    return result


def extract_class_methods(content: str, class_name: str) -> list:
    """提取类的方法"""

    methods = []

    # 找到类定义的位置
    class_start = content.find(f'class {class_name}')
    if class_start == -1:
        return methods

    # 找到类的结束位置（简化的大括号匹配）
    brace_count = 0
    class_end = class_start
    started = False

    for i, char in enumerate(content[class_start:], class_start):
        if char == '{':
            brace_count += 1
            started = True
        elif char == '}':
            brace_count -= 1
            if started and brace_count == 0:
                class_end = i
                break

    class_content = content[class_start:class_end]

    # 提取方法
    method_pattern = r'(public|private|protected)?\s*(async\s+)?(\w+)\s*\(([^)]*)\)(\s*:\s*([^{\n]+))?'
    for match in re.finditer(method_pattern, class_content):
        method_name = match.group(3)
        # 过滤构造函数和特殊方法
        if method_name in ['constructor', 'toString', 'valueOf']:
            continue
        methods.append({
            'name': method_name,
            'params': match.group(4),
            'return_type': match.group(6) or 'unknown',
            'is_async': bool(match.group(2)),
            'visibility': match.group(1) or 'public'
        })

    return methods


def generate_unit_test_template(source_file: str, parsed: dict) -> str:
    """生成单元测试模板"""

    # 提取模块名
    module_name = Path(source_file).stem
    module_path = source_file.replace('src/', '../../../src/').replace('.ts', '')

    template = f"""import {{ describe, it, expect, beforeEach }} from 'vitest';
import {{ {', '.join(parsed['exports'][:5])} }} from '{module_path}';

describe('{module_name}', () => {{
"""

    # 为每个函数生成测试
    for func in parsed['functions']:
        template += f"""
  describe('{func['name']}', () => {{
    it('应该正确执行 {func['name']}', {'' if not func['is_async'] else 'async '}() => {{
      // TODO: 准备测试数据
      // const input = ...;

      // TODO: 执行测试
      // const result = {func['name']}(input);

      // TODO: 验证结果
      // expect(result).toBe(expected);

      expect(true).toBe(true); // 占位符，请替换
    }});

    it('应该处理边界情况', {'' if not func['is_async'] else 'async '}() => {{
      // TODO: 测试边界情况
      expect(true).toBe(true); // 占位符，请替换
    }});

    it('应该处理异常输入', {'' if not func['is_async'] else 'async '}() => {{
      // TODO: 测试异常输入
      expect(true).toBe(true); // 占位符，请替换
    }});
  }});
"""

    # 为每个类生成测试
    for cls in parsed['classes']:
        template += f"""
  describe('{cls['name']}', () => {{
    let instance: {cls['name']};

    beforeEach(() => {{
      // TODO: 初始化实例
      // instance = new {cls['name']}();
    }});
"""

        for method in cls['methods']:
            if method['visibility'] == 'private':
                continue  # 跳过私有方法

            template += f"""
    describe('{method['name']}', () => {{
      it('应该正确执行 {method['name']}', {'' if not method['is_async'] else 'async '}() => {{
        // TODO: 准备测试数据
        // const result = await instance.{method['name']}(...);

        // TODO: 验证结果
        expect(true).toBe(true); // 占位符，请替换
      }});
    }});
"""

        template += "  });\n"

    template += "});\n"

    return template


def generate_integration_test_template(source_file: str, parsed: dict) -> str:
    """生成集成测试模板"""

    module_name = Path(source_file).stem
    module_path = source_file.replace('src/', '../../../src/').replace('.ts', '')

    # 找到主要类
    main_class = parsed['classes'][0] if parsed['classes'] else None

    if not main_class:
        return "// 没有找到类，无法生成集成测试模板"

    template = f"""import {{ describe, it, expect, beforeAll, afterAll, beforeEach }} from 'vitest';
import {{ {main_class['name']} }} from '{module_path}';

describe('{main_class['name']} 集成测试', () => {{
  let service: {main_class['name']};

  beforeAll(async () => {{
    // TODO: 设置测试环境
    // 例如：启动测试服务器、连接测试数据库
  }});

  afterAll(async () => {{
    // TODO: 清理测试环境
  }});

  beforeEach(() => {{
    // TODO: 初始化服务实例
    // service = new {main_class['name']}();
  }});

  describe('冒烟测试', () => {{
"""

    # 为主要方法生成冒烟测试
    for method in main_class['methods'][:3]:  # 只取前3个方法
        if method['visibility'] == 'private':
            continue

        template += f"""
    it('应该能执行 {method['name']}', {'' if not method['is_async'] else 'async '}() => {{
      // TODO: 基本功能测试
      // const result = await service.{method['name']}(testInput);

      // expect(result).toBeDefined();
      expect(true).toBe(true); // 占位符，请替换
    }});
"""

    template += """  });

  describe('集成场景', () => {
    it('应该完成完整的业务流程', async () => {
      // TODO: 端到端测试
      // 1. 准备数据
      // 2. 执行操作
      // 3. 验证结果
      expect(true).toBe(true); // 占位符，请替换
    });
  });
});
"""

    return template


def main():
    if len(sys.argv) < 2:
        print("用法: python generate_test_template.py <源文件路径> [测试类型]")
        print("")
        print("测试类型:")
        print("  unit        - 单元测试 (默认)")
        print("  integration - 集成测试")
        print("  all         - 生成两种测试")
        print("")
        print("示例:")
        print("  python generate_test_template.py src/modules/user/user-service.ts")
        print("  python generate_test_template.py src/modules/order/order-service.ts integration")
        sys.exit(1)

    source_file = sys.argv[1]
    test_type = sys.argv[2] if len(sys.argv) > 2 else 'unit'

    if not os.path.exists(source_file):
        print(f"错误: 文件不存在 {source_file}")
        sys.exit(1)

    # 解析源文件
    print(f"📖 解析源文件: {source_file}")
    parsed = parse_typescript_file(source_file)
    print(f"   函数: {len(parsed['functions'])} 个")
    print(f"   类: {len(parsed['classes'])} 个")

    # 生成测试文件
    source_path = Path(source_file)
    test_dir = source_path.parent.parent.parent / 'tests'

    if test_type in ['unit', 'all']:
        unit_test = generate_unit_test_template(source_file, parsed)
        unit_test_path = test_dir / 'unit' / f'{source_path.stem}.test.ts'

        os.makedirs(unit_test_path.parent, exist_ok=True)
        with open(unit_test_path, 'w', encoding='utf-8') as f:
            f.write(unit_test)

        print(f"✅ 单元测试模板已生成: {unit_test_path}")

    if test_type in ['integration', 'all']:
        integration_test = generate_integration_test_template(source_file, parsed)
        integration_test_path = test_dir / 'integration' / f'{source_path.stem}.test.ts'

        os.makedirs(integration_test_path.parent, exist_ok=True)
        with open(integration_test_path, 'w', encoding='utf-8') as f:
            f.write(integration_test)

        print(f"✅ 集成测试模板已生成: {integration_test_path}")

    print(f"\n📝 下一步:")
    print(f"   1. 查看生成的测试文件")
    print(f"   2. 替换占位符为实际测试逻辑")
    print(f"   3. 运行 npm run test 验证")


if __name__ == "__main__":
    main()
