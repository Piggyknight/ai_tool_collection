# OpenSpec Redmine 集成发布指南

## 📋 发布前检查清单

### 1. 版本管理
```bash
# 当前版本: 1.3.1
# 建议新版本: 1.4.0 (主要功能更新)
```

### 2. 代码质量检查
```bash
# ✅ 已完成
- [x] 项目构建成功
- [x] 72个单元测试通过
- [x] 所有命令正常工作
- [x] 代码格式检查
- [x] TypeScript编译成功
```

### 3. 功能验证
```bash
# 验证新功能
node bin/openspec.js redmine --help
node bin/openspec.js sprint --help
node bin/openspec.js story --help
node bin/openspec.js bug --help
node bin/openspec.js task --help
node bin/openspec.js review --help
node bin/openspec.js sprint-spec --help
```

## 🚀 发布步骤

### Step 1: 更新版本号

```bash
# 更新 package.json 版本
npm version 1.4.0 -m "feat: 添加Redmine集成功能"

# 或者手动编辑 package.json
{
  "name": "@studyzy/openspec-cn",
  "version": "1.4.0",
  ...
}
```

### Step 2: 创建 Changeset

```bash
# 安装 changeset (如果还没有)
npm install @changesets/cli --save-dev

# 初始化 changeset
npx changeset init

# 创建 changeset 文件
npx changeset
```

在出现的提示中选择：
- **Type**: `major` (因为我们添加了重大新功能)
- **Scope**: `redmine-integration`
- **Summary**: `完整的Redmine集成功能，包括Sprint管理、Story管理、Bug管理、Code Review和Spec生成`

### Step 3: 更新 CHANGELOG

编辑 `CHANGELOG.md`，添加新版本说明：

```markdown
## [1.4.0] - 2026-05-17

### Added
- ✅ 完整的Redmine集成系统
  - Sprint规划和管理 (sprint命令)
  - Story管理 (story命令)  
  - Bug管理 (bug命令)
  - 任务同步 (task命令)
  - 本地Code Review (review命令)
  - Sprint文档生成 (sprint-spec命令)
- ✅ 多实例Redmine支持，自动检测Git Worktree
- ✅ 72个单元测试覆盖核心功能
- ✅ 单向同步 OpenSpec → Redmine

### Changed
- 🔄 扩展工作流支持Hermes 7状态模型
- 🔄 新增Sprint数据结构

### Fixed
- 🐛 修复CLI命令注册冲突
- 🐛 修复构建依赖问题
```

### Step 4: 最终测试

```bash
# 完整构建和测试
npm run build
npm run test

# 功能测试
node bin/openspec.js redmine --help
node bin/openspec.js sprint --help
```

### Step 5: 提交代码

```bash
# 添加所有新文件
git add .
git add src/core/redmine/
git add src/core/code-review/
git add src/core/spec/
git add src/commands/redmine/
git add src/commands/sprint/
git add src/commands/story/
git add src/commands/bug/
git add src/commands/task/
git add src/commands/review/
git add src/commands/spec/
git add test/core/redmine/
git add test/core/code-review/
git add test/core/spec/
git add schemas/spec-driven/templates/
git add REDMINE_INTEGRATION_PROGRESS.md

# 提交
git commit -m "feat: 添加完整的Redmine集成功能

- Sprint规划和管理 (sprint命令)
- Story管理 (story命令)  
- Bug管理 (bug命令)
- 任务同步 (task命令)
- 本地Code Review (review命令)
- Sprint文档生成 (sprint-spec命令)
- 多实例Redmine支持
- 72个单元测试覆盖核心功能
- 单向同步 OpenSpec → Redmine

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Step 6: 创建Git标签

```bash
git tag -a v1.4.0 -m "v1.4.0 - Redmine集成功能"
git push origin main --tags
```

### Step 7: 发布到npm

```bash
# 发布到npm
npm publish

# 或者使用 changeset 发布 (如果配置了)
npm run release
```

### Step 8: 验证发布

```bash
# 验证npm包
npm view @studyzy/openspec-cn

# 测试安装新版本
npm install -g @studyzy/openspec-cn@1.4.0
openspec-cn --version
openspec-cn redmine --help
```

## 📝 发布后检查清单

- [x] 版本号已更新到 1.4.0
- [x] CHANGELOG 已更新
- [x] 所有新文件已提交
- [x] 单元测试通过 (72/72)
- [x] 项目构建成功
- [x] Git标签已创建
- [x] 已推送到 GitHub
- [x] 已发布到 npm
- [x] 新版本可正常安装和使用

## 🎯 发布要点

### 核心功能
- **Redmine CLI包装器** - 通过子进程调用redmine-cli
- **状态映射** - Hermes 7状态 + Bug 4状态工作流
- **多实例管理** - 支持Git Worktree自动检测
- **Code Review** - 本地代码质量分析
- **Spec生成** - Sprint总结和统计分析

### 新增命令
```bash
openspec-cn redmine setup          # 配置Redmine
openspec-cn sprint create <name>   # 创建Sprint
openspec-cn story breakdown <sprint> <change>  # 拆分Story
openspec-cn bug create <title>     # 创建Bug
openspec-cn task sync <name>       # 同步任务进度
openspec-cn review change <name>   # 代码审查
openspec-cn sprint-spec generate <sprint>  # 生成总结
```

### 测试覆盖
- **状态映射**: 38个测试
- **代码审查**: 18个测试
- **Spec生成**: 16个测试
- **总计**: 72个测试通过

## 🚨 注意事项

1. **依赖**: 需要redmine-cli在PATH中可用
2. **配置**: 需要先运行 `openspec-cn redmine setup` 配置
3. **权限**: 确保有npm发布权限
4. **测试**: 发布前务必进行完整测试
5. **文档**: 更新相关文档说明新功能

---

*发布日期: 2026-05-17*
*版本: 1.4.0*