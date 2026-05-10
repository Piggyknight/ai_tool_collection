#!/bin/bash
# UE项目编译脚本

# 检查参数
if [ $# -eq 0 ]; then
    echo "🎮 UE项目编译工具"
    echo ""
    echo "用法："
    echo "  $0 <项目路径.uproject> [构建类型]"
    echo ""
    echo "构建类型："
    echo "  Debug        - 调试版本（默认）"
    echo "  Development  - 开发版本"
    echo "  Shipping     - 发布版本"
    echo ""
    echo "示例："
    echo "  $0 MyProject.uproject"
    echo "  $0 MyProject.uproject Development"
    exit 1
fi

PROJECT_PATH=$1
BUILD_TYPE=${2:-Debug}

# 检查项目文件
if [ ! -f "$PROJECT_PATH" ]; then
    echo "❌ 错误：项目文件不存在: $PROJECT_PATH"
    exit 1
fi

# 检查文件扩展名
if [[ ! "$PROJECT_PATH" == *.uproject ]]; then
    echo "❌ 错误：必须是.uproject文件"
    exit 1
fi

echo "🎮 编译UE项目"
echo "📦 项目: $PROJECT_PATH"
echo "🔧 构建类型: $BUILD_TYPE"
echo ""

# 获取UE引擎路径（这里需要根据实际情况修改）
UE_PATH="/opt/UnrealEngine"  # Linux默认路径
if [ ! -d "$UE_PATH" ]; then
    echo "⚠️  警告：未找到UE引擎路径: $UE_PATH"
    echo "请修改脚本中的UE_PATH变量或使用手动编译命令"
    echo ""
    echo "手动编译命令示例："
    echo "  # Linux"
    echo "  ./RunUAT.sh BuildCookRun -project=$PROJECT_PATH -build -cook"
    echo ""
    echo "  # Windows"
    echo "  RunUAT.bat BuildCookRun -project=$PROJECT_PATH -build -cook"
    exit 1
fi

# 执行编译
echo "⏳ 开始编译..."
echo ""

# 使用UnrealAutomationTool
UBT="$UE_PATH/Engine/Binaries/DotNET/UnrealBuildTool.exe"
if [ -f "$UBT" ]; then
    # Windows
    mono "$UBT" "$(basename $PROJECT_PATH .uproject)" Win64 $BUILD_TYPE "$(dirname $PROJECT_PATH)"
else
    # Linux - 使用RunUAT
    UAT="$UE_PATH/Engine/Build/BatchFiles/RunUAT.sh"
    if [ -f "$UAT" ]; then
        "$UAT" BuildCookRun \
            -project="$(realpath $PROJECT_PATH)" \
            -noP4 \
            -platform=Linux \
            -clientconfig=$BUILD_TYPE \
            -cook \
            -build
    else
        echo "❌ 错误：找不到编译工具"
        echo "请手动编译项目或修改脚本中的路径"
        exit 1
    fi
fi

RESULT=$?

echo ""
if [ $RESULT -eq 0 ]; then
    echo "✅ 编译成功"
    exit 0
else
    echo "❌ 编译失败，退出码: $RESULT"
    echo ""
    echo "💡 建议操作："
    echo "  1. 查看上方错误日志"
    echo "  2. 使用 analyze_error.sh 分析错误"
    echo "  3. 查询知识库寻找解决方案"
    echo ""
    echo "示例："
    echo "  ~/openclaw/skills/unreal-developer/scripts/analyze_error.sh build.log"
    exit $RESULT
fi
