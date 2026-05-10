# 周报分类快速使用指南

## ✅ 当前状态

**最终版本**: v3（已修复音频分类问题）
**文件位置**: `data/weekly/team/team_20260302_classified.md`

---

## 🎯 分类结果

```
| 分类 | 任务数 | 占比 |
|------|--------|------|
| CI/构建系统 | 45 | 36.0% |
| 内存优化 | 37 | 29.6% |
| 资源系统 | 22 | 17.6% |
| 音频系统 | 13 | 10.4% | ⭐ 已修复
| 鸿蒙平台 | 8 | 6.4% |
```

**总计**: 125个任务

---

## 📖 如何使用

### 查看当前周报

```bash
cat ~/Documents/weekly-report-system/data/weekly/team/team_20260302_classified.md
```

### 为下周重新分类

```bash
cd ~/Documents/weekly-report-system

# 修改脚本中的日期
# week_dates = ['20260309', '20260310', '20260311', '20260312', '20260313']

# 运行分类
python3 scripts/reclassify_final.py
```

---

## 🔧 关键配置

### 成员职责配置

在 `scripts/reclassify_final.py` 中修改：

```python
MEMBER_RESPONSIBILITIES = {
    "pgh": {"primary": "audio"},      # 负责音频
    "hwl": {"primary": "memory"},     # 负责mmap/内存
    "zsh": {"primary": "ci"},         # 负责CI
    # ... 其他成员
}
```

### 分类关键词配置

```python
CATEGORY_KEYWORDS = {
    "audio": ["音频", "wwise", "音效", "混响"],
    "memory": ["内存", "mmap", "泄漏", "asan"],
    "ci": ["流水线", "符号服务器", "svn", "hook"],
    # ... 其他分类
}
```

---

## 📝 关键改进

### v3版本改进（当前）

1. ✅ 修复音频分类 - 从2个增加到13个任务
2. ✅ 利用成员职责信息
3. ✅ 保留所有Redmine任务
4. ✅ PGH的12个音频任务全部正确分类

### 历史版本

- **v1**: 基础修复，去除重复归类
- **v2**: 添加成员职责支持
- **v3**: 最终修复，完全解决音频分类问题

---

## 📊 验证方法

### 检查音频任务

```bash
grep "音频系统" -A 20 data/weekly/team/team_20260302_classified.md
```

应该看到13个音频任务，包括：
- #107092 辐射值音效
- #107278 混响效果
- #107453 枪声
- #105305 音频调用接口
- 等等

### 检查分类总和

```bash
grep "|.*|.*|.*%" data/weekly/team/team_20260302_classified.md
```

占比总和应该是100%

---

## 🆘 常见问题

### Q1: 为什么有些任务没有被分类？

A: 可能是关键词匹配不到，可以：
1. 添加更多关键词
2. 检查成员职责配置
3. 手动分类

### Q2: 如何调整分类规则？

A: 编辑 `scripts/reclassify_final.py`：
1. 修改 `MEMBER_RESPONSIBILITIES` 调整成员职责
2. 修改 `CATEGORY_KEYWORDS` 调整关键词
3. 修改 `classify_task` 函数调整逻辑

### Q3: 如何添加新成员？

A: 在 `MEMBER_RESPONSIBILITIES` 中添加：
```python
"new_member": {"primary": "ci", "secondary": []}
```

---

## 📞 联系方式

- **项目负责人**: Claw (project-manager)
- **技术支持**: 架构组
- **文档**: `docs/classifier_optimization_plan.md`

---

**最后更新**: 2026-03-08 00:50
**版本**: v3.0
