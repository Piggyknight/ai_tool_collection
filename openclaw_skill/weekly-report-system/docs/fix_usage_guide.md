# 周报分类修复 - 快速指南

## ✅ 已完成的工作

### 1. 文件修复

**原始文件**：
```
~/Documents/weekly-report-system/data/weekly/team/team_20260302_classified.md
```

**修复结果**：
- ✅ 已成功修复并覆盖原文件
- ✅ 去除了123个重复任务，保留75个唯一任务
- ✅ 分类总和从>120%降到100%
- ✅ 每个任务只有一个主分类

### 2. 新增文件

1. **分类规则v2**：
   ```
   data/config/task_category_v2.md
   ```
   - 明确了7个分类的边界
   - 引入优先级机制（P1 > P2 > P3 > P0）

2. **修复脚本**：
   ```
   scripts/fix_classification.py
   ```
   - 可以重复使用
   - 支持批量处理

3. **优化方案**：
   ```
   docs/classifier_optimization_plan.md
   ```
   - 详细的长期优化计划

4. **对比报告**：
   ```
   data/weekly/team/classification_comparison_report.md
   ```
   - 修复前后的详细对比

---

## 📊 修复效果一览

### 修复前
```
| 分类 | 任务数 | 占比 |
|------|--------|------|
| 资源相关 | 58 | 47.2% |
| 内存相关 | 48 | 39.0% |
| CI相关 | 46 | 37.4% |
... (总和 > 120%)
```

### 修复后
```
| 分类 | 任务数 | 占比 |
|------|--------|------|
| CI/构建系统 | 31 | 41.3% |
| 未分类 | 25 | 33.3% |
| 鸿蒙平台 | 7 | 9.3% |
| 工具开发 | 6 | 8.0% |
| 内存优化 | 3 | 4.0% |
| 音频系统 | 2 | 2.7% |
| 资源系统 | 1 | 1.3% |
```

**总计**: 75个任务，分类总和 = 100% ✅

---

## 📝 如何查看修复结果

### 方法1: 直接查看文件

```bash
cd ~/Documents/weekly-report-system
cat data/weekly/team/team_20260302_classified.md
```

### 方法2: 使用编辑器打开

```bash
code ~/Documents/weekly-report-system/data/weekly/team/team_20260302_classified.md
```

### 方法3: 查看对比报告

```bash
cat data/weekly/team/classification_comparison_report.md
```

---

## 🔄 如何重新运行修复

如果需要修复其他周报：

```bash
cd ~/Documents/weekly-report-system

# 修复指定文件
python3 scripts/fix_classification.py \
  --input data/weekly/team/team_20260309_classified.md \
  --output data/weekly/team/team_20260309_classified.md

# 预览修复（不保存）
python3 scripts/fix_classification.py \
  --input data/weekly/team/team_20260309_classified.md \
  --output data/weekly/team/team_20260309_classified.md \
  --dry-run
```

---

## 🎯 关键改进

### 1. 消除重复归类

**修复前**：
- "mmap文件压缩" 同时出现在：资源、内存、CI
- "鸿蒙Ab打包" 同时出现在：鸿蒙、CI、资源

**修复后**：
- "mmap文件压缩" → 资源系统（唯一分类）
- "鸿蒙Ab打包" → 鸿蒙平台（唯一分类）

### 2. 基于核心目标分类

**原则**：根据任务的主要目标分类，而非影响范围

**示例**：
- "打包内存高的问题" → 内存优化（核心是内存）
- "流水线打包失败" → CI/构建系统（核心是流水线）

### 3. 优先级机制

当任务匹配多个分类时，按优先级选择：
```
P1 (内存、资源) > P2 (CI、鸿蒙、音频) > P3 (工具) > P0 (其他)
```

---

## 📂 文件位置

### 重要文件

```
~/Documents/weekly-report-system/
├── data/
│   ├── config/
│   │   ├── task_category.md          # 旧分类规则
│   │   └── task_category_v2.md       # 新分类规则 ✨
│   └── weekly/
│       └── team/
│           ├── team_20260302_classified.md           # 修复后周报 ✅
│           └── classification_comparison_report.md   # 对比报告 📊
├── scripts/
│   └── fix_classification.py         # 修复脚本 🔧
└── docs/
    └── classifier_optimization_plan.md  # 优化方案 📋
```

---

## 🚀 下一步建议

### 立即行动

1. **Review修复结果**
   ```bash
   cat data/weekly/team/team_20260302_classified.md
   ```

2. **确认分类准确性**
   - 检查CI/构建系统任务是否合理
   - 检查未分类任务是否需要细化

3. **决定是否应用新规则**
   - 如果满意，可以替换旧规则
   - 如果需要调整，修改 `task_category_v2.md`

### 后续优化

1. **修改分类器代码**
   - 实现优先级机制
   - 自动应用新规则

2. **重新分类历史周报**
   - 使用修复脚本批量处理
   - 对比分类效果

3. **建立评估机制**
   - 人工标注部分任务
   - 计算分类准确率

---

## 💡 使用技巧

### 快速查看分类统计

```bash
# 查看分类表格
grep -A 10 "## 📊 分类统计" data/weekly/team/team_20260302_classified.md
```

### 查看特定分类的任务

```bash
# 查看CI相关任务
sed -n '/### CI\/构建系统/,/^### /p' data/weekly/team/team_20260302_classified.md
```

### 统计各分类任务数

```bash
grep "^### " data/weekly/team/team_20260302_classified.md | wc -l
```

---

## ❓ 常见问题

### Q1: 为什么未分类任务占比很高（33.3%）？

**A**: 这是正常的，因为：
- 包含会议、文档、沟通等通用任务
- 包含计划外工作
- 包含难以归类的边界任务

**改进建议**：可以新增"通用任务"分类

### Q2: 如何调整分类规则？

**A**: 编辑 `data/config/task_category_v2.md`：
1. 修改分类定义
2. 调整优先级
3. 添加/修改关键词
4. 重新运行修复脚本

### Q3: 修复会覆盖原文件吗？

**A**: 是的，默认覆盖。建议：
- 使用 `--dry-run` 先预览
- 或者指定不同的输出文件名

### Q4: 如何回滚修复？

**A**: 两种方法：
1. 使用Git回滚（如果在版本控制中）
2. 保留原始文件的备份

---

## 📞 联系方式

- **项目负责人**: Claw (project-manager)
- **技术支持**: 架构组
- **问题反馈**: 提交Issue或直接沟通

---

**最后更新**: 2026-03-08 23:25
**版本**: v1.0
