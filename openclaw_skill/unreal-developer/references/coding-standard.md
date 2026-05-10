# Unreal Engine 编码规范

## 命名规范

### 基本原则

1. **每个单词首字母大写** (PascalCase)
2. **不要使用缩写**（标准缩写除外，如AI、UV）
3. **名称要有意义**，清晰表达用途

### 类型前缀规范

| 前缀 | 类型 | 示例 |
|------|------|------|
| A | Actor | `APlayerCharacter` |
| U | UObject派生类 | `UHealthComponent` |
| F | 结构体 | `FDamageInfo` |
| E | 枚举 | `EHealthState` |
| I | 接口 | `IDamageable` |
| T | 模板 | `TArray`, `TMap` |
| S | Slate控件 | `SHealthBar` |
| G | 全局对象 | `GEngine` |

### 变量命名

#### 成员变量
```cpp
// ✅ 正确
UPROPERTY()
float CurrentHealth;

UPROPERTY()
bool bIsDead;

UPROPERTY()
TArray<AActor*> NearbyActors;

// ❌ 错误
UPROPERTY()
float currentHealth;  // 首字母应该大写

UPROPERTY()
bool isDead;  // 布尔值应该有b前缀
```

#### 布尔值命名
```cpp
// ✅ 正确 - b前缀
bool bIsAlive;
bool bCanJump;
bool bHasWeapon;
bool bShouldDie;

// ❌ 错误
bool isAlive;
bool canJump;
```

#### 参数命名
```cpp
// ✅ 正确
void TakeDamage(float DamageAmount, AActor* DamageCauser);

// ❌ 错误
void TakeDamage(float damageAmount, AActor* damageCauser);
```

### 函数命名

```cpp
// ✅ 正确 - PascalCase
void UpdateHealth();
float GetCurrentHealth() const;
bool IsAlive() const;
void ApplyDamage(float Damage);

// ❌ 错误
void updateHealth();  // 首字母应该大写
```

#### 函数命名约定

| 前缀 | 含义 | 示例 |
|------|------|------|
| Get | 获取值 | `GetHealth()` |
| Set | 设置值 | `SetHealth(float Value)` |
| Is/Can/Should | 返回布尔值 | `IsAlive()` |
| On | 事件处理 | `OnDeath()` |
| Apply | 应用效果 | `ApplyDamage()` |
| Calculate | 计算值 | `CalculateDamage()` |

---

## 反射宏使用

### UCLASS - 类定义

```cpp
// 基本用法
UCLASS()
class GAME_API UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
};

// 常用修饰符
UCLASS(ClassGroup = "Health", meta = (BlueprintSpawnableComponent))
class GAME_API UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
};
```

#### UCLASS常用修饰符

| 修饰符 | 说明 | 用途 |
|--------|------|------|
| ClassGroup | 在编辑器中的分组 | 组织组件 |
| Blueprintable | 可创建蓝图子类 | 蓝图继承 |
| BlueprintType | 可作为蓝图变量类型 | 蓝图中使用 |
| NotBlueprintType | 不可作为变量类型 | 限制使用 |
| Abstract | 抽象类 | 不能直接实例化 |
| MinimalAPI | 仅导出类型信息 | 减少导出 |

### UPROPERTY - 属性

```cpp
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
    // EditAnywhere - 可在原型和实例中编辑
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Health")
    float MaxHealth;
    
    // EditDefaultsOnly - 仅可在原型中编辑
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health")
    float Armor;
    
    // VisibleAnywhere - 可在原型和实例中查看（不可编辑）
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health")
    float CurrentHealth;
    
    // VisibleInstanceOnly - 仅可在实例中查看
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Health")
    AActor* LastDamageCauser;
};
```

#### UPROPERTY常用修饰符

**访问控制：**
- `EditAnywhere` - 原型和实例都可编辑
- `EditDefaultsOnly` - 仅原型可编辑
- `EditInstanceOnly` - 仅实例可编辑
- `VisibleAnywhere` - 原型和实例都可查看
- `VisibleDefaultsOnly` - 仅原型可查看
- `VisibleInstanceOnly` - 仅实例可查看

**蓝图交互：**
- `BlueprintReadWrite` - 蓝图可读写
- `BlueprintReadOnly` - 蓝图只读
- `BlueprintSetter` - 指定设置函数
- `BlueprintGetter` - 指定获取函数

**元数据（meta）：**
- `ClampMin` - 最小值
- `ClampMax` - 最大值
- `UIMin` - UI滑块最小值
- `UIMax` - UI滑块最大值

```cpp
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Health",
    meta = (ClampMin = "0.0", ClampMax = "1000.0"))
float MaxHealth;
```

### UFUNCTION - 函数

```cpp
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
    // BlueprintCallable - 蓝图可调用
    UFUNCTION(BlueprintCallable, Category = "Health")
    void TakeDamage(float Damage);
    
    // BlueprintPure - 蓝图纯函数（无执行引脚）
    UFUNCTION(BlueprintPure, Category = "Health")
    float GetCurrentHealth() const { return CurrentHealth; }
    
    // BlueprintImplementableEvent - 蓝图实现
    UFUNCTION(BlueprintImplementableEvent, Category = "Health")
    void OnDeath();
    
    // NativeEvent - C++默认实现，蓝图可覆盖
    UFUNCTION(BlueprintNativeEvent, Category = "Health")
    void OnDamageTaken(float Damage);
    virtual void OnDamageTaken_Implementation(float Damage);
};
```

#### UFUNCTION常用修饰符

| 修饰符 | 说明 | 用途 |
|--------|------|------|
| BlueprintCallable | 蓝图可调用 | 暴露给蓝图 |
| BlueprintPure | 蓝图纯函数 | 获取数据 |
| BlueprintImplementableEvent | 蓝图实现 | 蓝图事件 |
| BlueprintNativeEvent | C++默认+蓝图覆盖 | 可覆盖逻辑 |
| Category | 分类 | 组织蓝图节点 |
| Server | 服务器执行 | 网络同步 |
| Client | 客户端执行 | 网络同步 |
| NetMulticast | 广播给所有客户端 | 网络同步 |
| Reliable | 可靠传输 | 网络同步 |

---

## 头文件包含

### 包含顺序

```cpp
// 1. 项目头文件
#include "GameFramework/Actor.h"
#include "Components/ActorComponent.h"
#include "HealthComponent.h"

// 2. 引擎核心头文件
#include "CoreMinimal.h"
#include "Engine.h"

// 3. 第三方库（如有）

// 4. 生成的头文件（必须最后！）
#include "HealthComponent.generated.h"
```

**重要规则：**
- `.generated.h` **必须**是最后一个包含
- 顺序：项目 → 引擎 → 第三方 → generated.h

### 前向声明

```cpp
// ✅ 优先使用前向声明（减少依赖）
class AActor;
class UHealthComponent;

// 在.cpp中包含完整头文件
#include "GameFramework/Actor.h"
#include "HealthComponent.h"
```

---

## 代码格式

### 花括号

```cpp
// ✅ Allman风格（推荐）
void TakeDamage(float Damage)
{
    if (bIsDead)
    {
        return;
    }
    
    CurrentHealth -= Damage;
}

// ❌ K&R风格（避免）
void TakeDamage(float Damage) {
    if (bIsDead) {
        return;
    }
}
```

### 缩进和空格

```cpp
// ✅ 使用Tab缩进（UE4标准）
if (bIsDead)
{
	return;
}

// ✅ 运算符周围加空格
float Result = Damage + Armor;
if (CurrentHealth <= 0.0f)

// ❌ 不要过度空格
float Result=Damage+Armor;
```

### 注释

```cpp
/**
 * 生命值组件
 * 负责管理角色的生命值状态
 */
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
    /**
     * 最大生命值
     * 编辑器中可配置，运行时不可更改
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    float MaxHealth;
    
    // 当前生命值（运行时状态）
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    float CurrentHealth;
    
    /**
     * 应用伤害
     * @param Damage - 伤害数值
     * @param DamageType - 伤害类型
     * @param Causer - 伤害来源
     */
    void ApplyDamage(float Damage, TSubclassOf<UDamageType> DamageType, AActor* Causer);
};
```

---

## 常见错误

### 错误1：命名不符合规范

```cpp
// ❌ 错误
class healthComponent;  // 应该有U前缀，首字母大写
bool isAlive;           // 应该有b前缀
void update_health();   // 不应该用下划线

// ✅ 正确
class UHealthComponent;
bool bIsAlive;
void UpdateHealth();
```

### 错误2：宏使用错误

```cpp
// ❌ 错误 - 缺少GENERATED_BODY
UCLASS()
class UHealthComponent : public UActorComponent
{
    // 缺少 GENERATED_BODY()
};

// ❌ 错误 - .generated.h不在最后
#include "HealthComponent.generated.h"
#include "CoreMinimal.h"  // 应该在前面

// ✅ 正确
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
};
```

### 错误3：头文件包含错误

```cpp
// ❌ 错误 - 缺少必要的包含
class UHealthComponent : public UActorComponent  // UActorComponent未定义
{
    GENERATED_BODY()
};

// ✅ 正确
#include "Components/ActorComponent.h"
#include "HealthComponent.generated.h"

class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
};
```

---

## 最佳实践

### 1. 属性分类

```cpp
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health|Config")
    float MaxHealth;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health|Config")
    float Armor;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health|State")
    float CurrentHealth;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health|State")
    bool bIsDead;
};
```

### 2. const正确性

```cpp
// ✅ 不修改成员变量的函数应该标记const
UFUNCTION(BlueprintPure, Category = "Health")
float GetCurrentHealth() const { return CurrentHealth; }

UFUNCTION(BlueprintPure, Category = "Health")
bool IsAlive() const { return !bIsDead; }

// ✅ 参数如果不修改，使用const引用
void ApplyDamage(const FDamageInfo& DamageInfo);
```

### 3. 使用UE类型

```cpp
// ✅ 使用UE容器和字符串
TArray<AActor*> Actors;
TMap<FName, float> Values;
FString Name;

// ❌ 避免使用STL
std::vector<AActor*> Actors;  // 不要使用
std::map<std::string, float> Values;  // 不要使用
```

---

## 参考资源

- **知识库查询**：`python3 ~/Documents/unreal_rag/tools/simple_rag_query.py --query "coding standard"`
- **完整文档**：~/Documents/unreal_rag/docs/raw/markdown/Runtime_AIModule_AICodingStandard.md
