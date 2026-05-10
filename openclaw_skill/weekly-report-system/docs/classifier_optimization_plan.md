# 任务分类器优化方案

## 问题分析

### 当前问题

1. **分类重叠**：CI、内存、资源三个分类占比都超过37%，说明大量任务被重复归类
2. **统计失真**：123个任务，各类别占比之和远超100%
3. **分类不准**：同一个任务出现在多个分类中，无法准确反映工作量

### 根本原因

1. **分类定义重叠**：
   - CI定义："前置各种错误都会在CI打包时发生"
   - 内存定义："为了查内存问题，需要各个平台支持asan"
   - 资源定义："协助修复资源相关问题"

2. **缺少优先级机制**：
   - 任务匹配多个分类时，全部归入
   - 没有"主分类"概念

3. **关键词匹配过于宽松**：
   - 只要包含关键词就匹配
   - 没有区分"核心任务"和"次要影响"

---

## 优化方案

### 方案1：重构分类规则（已完成）

**文件**：`data/config/task_category_v2.md`

**核心改进**：
1. ✅ 明确每个分类的边界，避免重叠
2. ✅ 引入优先级机制（P1 > P2 > P3 > P0）
3. ✅ 基于核心目标分类，而非影响范围
4. ✅ 每个任务只归入一个主分类

---

### 方案2：修改分类器代码

#### 2.1 修改 `task_classifier.py`

**关键改动**：

```python
# 在 TaskClassifier 类中添加优先级属性
@dataclass
class Category:
    id: str
    name: str
    keywords: List[str]
    description: str
    priority: int = 2  # 新增：1=高, 2=中, 3=低, 0=兜底

# 修改分类逻辑
def classify_task(self, task: TaskToClassify) -> ClassificationResult:
    """分类单个任务 - 只返回一个主分类"""
    
    # 1. 尝试LLM分类
    categories = self._classify_with_llm(task)
    
    # 2. 如果LLM失败，使用关键词匹配
    if not categories:
        categories = self._fallback_keyword_match(task)
    
    # 3. 【新增】如果有多个分类，按优先级选择一个
    if len(categories) > 1:
        categories = self._select_primary_category(categories)
    
    # 4. 如果没有匹配，归入other
    if not categories:
        categories = ["other"]
    
    return ClassificationResult(
        task_id=task.task_id,
        categories=categories,  # 只包含一个分类
        confidence=0.8,
        method="llm" if method == "llm" else "keyword"
    )

def _select_primary_category(self, categories: List[str]) -> List[str]:
    """
    从多个分类中选择主分类
    
    规则：
    1. 按优先级排序（P1 > P2 > P3 > P0）
    2. 同优先级按匹配度排序
    3. 返回最高优先级的第一个分类
    """
    # 获取每个分类的优先级
    category_with_priority = []
    for cat_id in categories:
        cat = self._category_map.get(cat_id)
        if cat:
            priority = getattr(cat, 'priority', 2)
            category_with_priority.append((cat_id, priority))
    
    # 按优先级排序（数字越小优先级越高）
    category_with_priority.sort(key=lambda x: x[1])
    
    # 返回最高优先级的分类
    if category_with_priority:
        return [category_with_priority[0][0]]
    
    return categories[:1]  # 默认返回第一个
```

#### 2.2 修改 `category_parser.py`

**关键改动**：

```python
@dataclass
class Category:
    """分类数据结构"""
    id: str
    name: str
    keywords: List[str]
    description: str
    priority: int = 2  # 新增：优先级字段
    examples: List[str] = field(default_factory=list)  # 新增：示例列表

def _parse_category(self, section: str) -> Category:
    """解析分类配置"""
    lines = section.strip().split('\n')
    
    # 解析标题（包含优先级）
    title_match = re.match(r'### (\d+)\. (.+?)（(\w+)）.*?P(\d)', lines[0])
    if title_match:
        priority = int(title_match.group(4))
        name = title_match.group(2)
        cat_id = title_match.group(3)
    else:
        # 兼容旧格式
        priority = 2
        name = lines[0].replace('#', '').strip()
        cat_id = self._extract_id(name)
    
    # ... 其他解析逻辑
    
    return Category(
        id=cat_id,
        name=name,
        keywords=keywords,
        description=description,
        priority=priority,  # 新增
        examples=examples   # 新增
    )
```

#### 2.3 修改 LLM 提示词

```python
def _build_prompt(self, task: TaskToClassify, categories: List[Category]) -> str:
    """构建LLM提示词"""
    
    # 构建分类列表（带优先级）
    categories_desc = []
    for cat in sorted(categories, key=lambda x: x.priority):
        desc = f"{cat.priority}. {cat.id}: {cat.name}"
        if cat.keywords:
            desc += f" (关键词: {', '.join(cat.keywords[:3])})"
        categories_desc.append(desc)
    
    categories_text = "\n".join(categories_desc)
    
    prompt = f"""你是任务分类专家。请根据以下规则对任务进行分类。

**核心原则**：
1. 每个任务有且仅有一个主分类
2. 根据任务的核心目标分类，而非影响范围
3. 优先级：1(高) > 2(中) > 3(低) > 0(兜底)

**分类列表**（按优先级排序）：
{categories_text}

**任务内容**：
{task.content}

**请返回**：只返回一个分类ID（例如：memory）
"""
    
    return prompt
```

---

### 方案3：优化关键词匹配逻辑

#### 3.1 添加负向关键词

```python
@dataclass
class Category:
    id: str
    name: str
    keywords: List[str]
    exclude_keywords: List[str] = field(default_factory=list)  # 新增
    description: str
    priority: int = 2

def _fallback_keyword_match(self, task: TaskToClassify) -> List[str]:
    """关键词匹配（带排除规则）"""
    content = task.content.lower()
    matched_categories = []
    
    for category in sorted(self.config.categories, key=lambda x: x.priority):
        # 检查排除关键词
        if hasattr(category, 'exclude_keywords'):
            for exclude_kw in category.exclude_keywords:
                if exclude_kw.lower() in content:
                    # 匹配到排除关键词，跳过此分类
                    continue
        
        # 检查匹配关键词
        for keyword in category.keywords:
            if keyword.lower() in content:
                matched_categories.append(category.id)
                break
        
        # 如果已经匹配到高优先级分类，停止匹配
        if matched_categories and category.priority == 1:
            break
    
    return matched_categories
```

#### 3.2 在配置文件中定义排除规则

```markdown
### 1. 内存优化（memory）P1
**包含**：...
**不包含**：
- ❌ 普通bug修复
- ❌ 平台移植任务
- ❌ 资源加载优化

**排除关键词**：平台移植, 跨平台, 音频播放
```

---

### 方案4：添加分类验证

#### 4.1 添加分类后验证

```python
def classify_batch(self, tasks: List[TaskToClassify]) -> List[ClassificationResult]:
    """批量分类 - 带验证"""
    results = []
    
    for task in tasks:
        result = self.classify_task(task)
        results.append(result)
    
    # 【新增】验证分类结果
    self._validate_classification_results(results)
    
    return results

def _validate_classification_results(self, results: List[ClassificationResult]):
    """验证分类结果"""
    stats = defaultdict(int)
    
    for result in results:
        for cat_id in result.categories:
            stats[cat_id] += 1
    
    total = len(results)
    
    # 检查是否有分类占比过高（>40%）
    for cat_id, count in stats.items():
        percentage = count / total * 100
        if percentage > 40:
            logger.warning(
                f"分类 {cat_id} 占比过高: {percentage:.1f}%，"
                f"可能存在分类规则问题"
            )
    
    # 检查分类总数是否远超任务总数
    total_classifications = sum(len(r.categories) for r in results)
    if total_classifications > total * 1.2:
        logger.warning(
            f"分类总数 ({total_classifications}) 远超任务总数 ({total})，"
            f"存在重复归类问题"
        )
```

---

### 方案5：添加人工标注机制

#### 5.1 创建标注工具

```python
# scripts/annotate_classifications.py

def annotate_task(task_id: str, correct_category: str):
    """人工标注正确分类"""
    # 1. 加载任务
    # 2. 显示当前分类
    # 3. 接受人工输入
    # 4. 保存标注结果
    # 5. 用于训练/评估
    pass

def export_training_data(output_path: str):
    """导出训练数据"""
    # 导出格式：
    # {"content": "...", "category": "memory"}
    pass
```

#### 5.2 创建评估脚本

```python
# scripts/evaluate_classifier.py

def evaluate_classifier(test_data_path: str):
    """评估分类器准确率"""
    # 1. 加载测试数据（人工标注）
    # 2. 运行分类器
    # 3. 计算准确率、召回率
    # 4. 生成混淆矩阵
    # 5. 输出改进建议
    pass
```

---

## 实施计划

### Phase 1: 立即实施（本周）

1. ✅ 创建新的分类规则文档（`task_category_v2.md`）
2. 🔲 修改 `category_parser.py`，支持优先级字段
3. 🔲 修改 `task_classifier.py`，实现主分类选择
4. 🔲 修改 LLM 提示词，强调"只返回一个分类"

### Phase 2: 优化迭代（下周）

1. 🔲 添加负向关键词和排除规则
2. 🔲 实现分类验证机制
3. 🔲 重新分类历史周报
4. 🔲 对比优化效果

### Phase 3: 长期维护（持续）

1. 🔲 建立人工标注流程
2. 🔲 定期评估分类准确率
3. 🔲 根据反馈优化规则

---

## 预期效果

### 量化指标

| 指标 | 当前 | 目标 |
|------|------|------|
| 分类重叠率 | >100% | ≤100% |
| CI分类占比 | 37.4% | 15-25% |
| 内存分类占比 | 39.0% | 20-30% |
| 资源分类占比 | 47.2% | 25-35% |
| 单任务分类数 | 2-3个 | 1个 |

### 质量提升

1. ✅ 每个任务有且仅有一个主分类
2. ✅ 分类占比总和 = 100%
3. ✅ 分类更准确，反映真实工作量
4. ✅ 便于统计和对比分析

---

## 风险评估

### 风险1：历史数据不一致

**影响**：新旧分类规则导致历史数据无法对比

**缓解**：
- 保留旧分类数据
- 提供分类映射表
- 重新分类历史周报（可选）

### 风险2：LLM分类不稳定

**影响**：同一任务多次分类可能结果不同

**缓解**：
- 强化提示词约束
- 添加缓存机制
- 降级到关键词匹配

### 风险3：分类边界争议

**影响**：某些任务难以归类

**缓解**：
- 建立仲裁机制
- 收集边界案例
- 持续优化规则

---

## 下一步行动

1. **立即**：Review `task_category_v2.md`，确认分类规则
2. **今天**：实施 Phase 1 代码修改
3. **明天**：测试新分类器
4. **本周**：重新生成本周周报，验证效果

---

**维护者**：架构组
**最后更新**：2026-03-08
