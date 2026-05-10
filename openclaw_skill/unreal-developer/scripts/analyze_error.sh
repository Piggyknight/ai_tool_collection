#!/bin/bash
# 编译错误分析脚本

# 检查参数
if [ $# -eq 0 ]; then
    echo "🔍 UE编译错误分析工具"
    echo ""
    echo "用法："
    echo "  $0 <错误日志文件>"
    echo ""
    echo "示例："
    echo "  $0 build.log"
    echo "  $0 compilation_error.log"
    exit 1
fi

ERROR_LOG=$1

# 检查文件
if [ ! -f "$ERROR_LOG" ]; then
    echo "❌ 错误：日志文件不存在: $ERROR_LOG"
    exit 1
fi

echo "🔍 分析编译错误: $ERROR_LOG"
echo ""

# 提取错误类型
echo "📊 错误统计："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 统计错误数量
ERROR_COUNT=$(grep -i "error" "$ERROR_LOG" | wc -l)
WARNING_COUNT=$(grep -i "warning" "$ERROR_LOG" | wc -l)

echo "❌ 错误数: $ERROR_COUNT"
echo "⚠️  警告数: $WARNING_COUNT"
echo ""

# 提取主要错误类型
echo "🎯 错误类型分析："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# C类错误（语法错误）
SYNTAX_ERRORS=$(grep -oP "error C\d+" "$ERROR_LOG" | sort | uniq -c | sort -rn)
if [ ! -z "$SYNTAX_ERRORS" ]; then
    echo "语法错误："
    echo "$SYNTAX_ERRORS"
    echo ""
fi

# 链接错误
LINKER_ERRORS=$(grep -oP "LNK\d+" "$ERROR_LOG" | sort | uniq -c | sort -rn)
if [ ! -z "$LINKER_ERRORS" ]; then
    echo "链接错误："
    echo "$LINKER_ERRORS"
    echo ""
fi

# 提取错误位置
echo "📍 错误位置（前5个）："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ERROR_LOCATIONS=$(grep -oP "[\w/]+\.cpp\(\d+\)" "$ERROR_LOG" | head -5)
if [ ! -z "$ERROR_LOCATIONS" ]; then
    echo "$ERROR_LOCATIONS"
    echo ""
fi

# 提取具体错误信息
echo "📝 错误详情（前3个）："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -i "error" "$ERROR_LOG" | head -3
echo ""

# 根据错误类型生成查询建议
echo "💡 知识库查询建议："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

KNOWLEDGE_BASE=~/Documents/unreal_rag/tools/simple_rag_query.py

# 检测最常见的错误类型
if grep -q "C2065\|undeclared identifier" "$ERROR_LOG"; then
    echo "检测到未声明标识符错误"
    echo "查询命令："
    echo "  python3 $KNOWLEDGE_BASE --query \"undeclared identifier include header\" --max-results 5"
    echo ""
fi

if grep -q "C2338\|GENERATED_BODY" "$ERROR_LOG"; then
    echo "检测到反射宏错误"
    echo "查询命令："
    echo "  python3 $KNOWLEDGE_BASE --query \"GENERATED_BODY UCLASS macro error\" --max-results 5"
    echo ""
fi

if grep -q "LNK2019\|LNK2001\|unresolved external" "$ERROR_LOG"; then
    echo "检测到链接错误"
    echo "查询命令："
    echo "  python3 $KNOWLEDGE_BASE --query \"LNK2019 unresolved external Build.cs module\" --max-results 5"
    echo ""
fi

if grep -q "C2512\|constructor" "$ERROR_LOG"; then
    echo "检测到构造函数错误"
    echo "查询命令："
    echo "  python3 $KNOWLEDGE_BASE --query \"constructor default GENERATED_BODY\" --max-results 5"
    echo ""
fi

# 生成修复报告文件
REPORT_FILE="error_analysis_$(date +%Y%m%d_%H%M%S).txt"
echo ""
echo "📄 生成详细报告..."
cat > "$REPORT_FILE" <<EOF
UE编译错误分析报告
生成时间: $(date)
错误日志: $ERROR_LOG

=== 统计信息 ===
错误数: $ERROR_COUNT
警告数: $WARNING_COUNT

=== 错误类型 ===
$SYNTAX_ERRORS
$LINKER_ERRORS

=== 错误位置 ===
$ERROR_LOCATIONS

=== 原始错误日志 ===
$(grep -i "error" "$ERROR_LOG" | head -10)

=== 建议操作 ===
1. 查看上方错误详情
2. 使用知识库查询解决方案
3. 参考 compilation-errors.md 文档
4. 修复后重新编译验证

EOF

echo "✅ 报告已保存: $REPORT_FILE"
echo ""
echo "🎯 下一步操作："
echo "  1. 查看错误详情和位置"
echo "  2. 使用建议的查询命令查找解决方案"
echo "  3. 实施修复"
echo "  4. 重新编译验证"
