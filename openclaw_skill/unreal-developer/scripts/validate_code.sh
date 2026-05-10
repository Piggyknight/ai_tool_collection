#!/bin/bash
# UE代码规范验证脚本

# 检查参数
if [ $# -eq 0 ]; then
    echo "✅ UE代码规范验证工具"
    echo ""
    echo "用法："
    echo "  $0 <源文件或目录>"
    echo ""
    echo "示例："
    echo "  $0 Source/"
    echo "  $0 Source/Game/MyCharacter.h"
    exit 1
fi

TARGET=$1

# 检查目标是否存在
if [ ! -e "$TARGET" ]; then
    echo "❌ 错误：目标不存在: $TARGET"
    exit 1
fi

echo "✅ UE代码规范验证"
echo "📁 目标: $TARGET"
echo ""

ERRORS=0
WARNINGS=0

# 检查命名规范
echo "🔍 检查命名规范..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查类名（应该有前缀）
find "$TARGET" -name "*.h" -type f | while read -r FILE; do
    # 检查UCLASS类是否以U开头
    if grep -q "UCLASS()" "$FILE"; then
        CLASS_NAME=$(grep -oP "class \K\w+(?= : public)" "$FILE" | head -1)
        if [[ ! "$CLASS_NAME" =~ ^U ]]; then
            echo "❌ $FILE: UCLASS类名应该以U开头: $CLASS_NAME"
            ((ERRORS++))
        fi
    fi
    
    # 检查Actor类是否以A开头
    if grep -q "public AActor" "$FILE"; then
        CLASS_NAME=$(grep -oP "class \K\w+(?= : public)" "$FILE" | head -1)
        if [[ ! "$CLASS_NAME" =~ ^A ]]; then
            echo "❌ $FILE: Actor类名应该以A开头: $CLASS_NAME"
            ((ERRORS++))
        fi
    fi
done

# 检查布尔值命名
echo ""
echo "🔍 检查布尔值命名..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

find "$TARGET" -name "*.h" -type f | while read -r FILE; do
    # 检查bool类型变量是否以b开头
    BOOL_VARS=$(grep -oP "bool \K\w+" "$FILE" | grep -v "^b[A-Z]")
    if [ ! -z "$BOOL_VARS" ]; then
        echo "⚠️  $FILE: 布尔值应该以b开头:"
        echo "$BOOL_VARS"
        ((WARNINGS++))
    fi
done

# 检查头文件包含顺序
echo ""
echo "🔍 检查头文件包含顺序..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

find "$TARGET" -name "*.h" -type f | while read -r FILE; do
    # 检查.generated.h是否在最后
    if grep -q "\.generated\.h" "$FILE"; then
        LAST_INCLUDE=$(grep "#include" "$FILE" | tail -1)
        if [[ ! "$LAST_INCLUDE" =~ \.generated\.h ]]; then
            echo "❌ $FILE: .generated.h应该在最后"
            ((ERRORS++))
        fi
    fi
done

# 检查GENERATED_BODY
echo ""
echo "🔍 检查GENERATED_BODY宏..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

find "$TARGET" -name "*.h" -type f | while read -r FILE; do
    if grep -q "UCLASS()\|USTRUCT()" "$FILE"; then
        if ! grep -q "GENERATED_BODY()" "$FILE"; then
            echo "❌ $FILE: 缺少GENERATED_BODY()宏"
            ((ERRORS++))
        fi
    fi
done

# 检查UPROPERTY
echo ""
echo "🔍 检查UPROPERTY使用..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

find "$TARGET" -name "*.h" -type f | while read -r FILE; do
    # 检查成员变量是否有UPROPERTY
    MEMBER_VARS=$(grep -P "^\s+\w+\s+\w+;" "$FILE" | grep -v "UPROPERTY\|private:\|public:\|protected:")
    if [ ! -z "$MEMBER_VARS" ]; then
        echo "⚠️  $FILE: 成员变量可能缺少UPROPERTY宏:"
        echo "$MEMBER_VARS"
        ((WARNINGS++))
    fi
done

# 检查const正确性
echo ""
echo "🔍 检查const正确性..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

find "$TARGET" -name "*.h" -type f | while read -r FILE; do
    # 检查getter函数是否标记const
    GETTER_FUNCS=$(grep -oP "Get\w+\(\)" "$FILE" | grep -v "const")
    if [ ! -z "$GETTER_FUNCS" ]; then
        echo "⚠️  $FILE: Getter函数应该标记const:"
        echo "$GETTER_FUNCS"
        ((WARNINGS++))
    fi
done

# 检查Category使用
echo ""
echo "🔍 检查Category使用..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

find "$TARGET" -name "*.h" -type f | while read -r FILE; do
    # 检查UPROPERTY是否有Category
    if grep -q "UPROPERTY(" "$FILE"; then
        NO_CATEGORY=$(grep "UPROPERTY(" "$FILE" | grep -v "Category")
        if [ ! -z "$NO_CATEGORY" ]; then
            echo "⚠️  $FILE: UPROPERTY应该添加Category:"
            echo "$NO_CATEGORY"
            ((WARNINGS++))
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 验证完成"
echo "❌ 错误: $ERRORS"
echo "⚠️  警告: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ 发现 $ERRORS 个错误，请修复后再提交"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  发现 $WARNINGS 个警告，建议修复"
    exit 0
else
    echo "✅ 代码规范验证通过"
    exit 0
fi
