#!/bin/bash
# API快速查询脚本

KNOWLEDGE_BASE=~/Documents/unreal_rag/tools/simple_rag_query.py

# 检查参数
if [ $# -eq 0 ]; then
    echo "🎮 UE API 快速查询工具"
    echo ""
    echo "用法："
    echo "  $0 \"查询关键词\" [最大结果数]"
    echo ""
    echo "示例："
    echo "  $0 \"UActorComponent\""
    echo "  $0 \"UActorComponent include\" 5"
    echo ""
    echo "常用查询："
    echo "  - 类定义: \"UActorComponent class definition\""
    echo "  - 头文件: \"UActorComponent include header\""
    echo "  - 宏使用: \"UCLASS UPROPERTY macro\""
    echo "  - 模块依赖: \"Build.cs module dependency\""
    exit 1
fi

QUERY=$1
MAX_RESULTS=${2:-5}

# 检查知识库是否存在
if [ ! -f "$KNOWLEDGE_BASE" ]; then
    echo "❌ 错误：找不到知识库查询工具"
    echo "   路径：$KNOWLEDGE_BASE"
    echo ""
    echo "请确保unreal_rag已正确安装："
    echo "  cd ~/Documents"
    echo "  git clone <unreal_rag仓库地址>"
    exit 1
fi

# 执行查询
echo "🔎 查询: $QUERY"
echo "📊 最大结果数: $MAX_RESULTS"
echo ""

python3 "$KNOWLEDGE_BASE" --query "$QUERY" --max-results $MAX_RESULTS
