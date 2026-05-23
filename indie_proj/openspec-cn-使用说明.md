# OpenSpec-cn 使用说明

## 📖 目录

1. [项目简介](#项目简介)
2. [安装指南](#安装指南)
3. [首次配置](#首次配置)
4. [基础概念](#基础概念)
5. [Redmine集成](#redmine集成)
6. [Sprint管理](#sprint管理)
7. [Story管理](#story管理)
8. [Bug管理](#bug管理)
9. [任务同步](#任务同步)
10. [代码审查](#代码审查)
11. [Sprint总结](#sprint总结)
12. [工作流程示例](#工作流程示例)
13. [常见问题](#常见问题)
14. [最佳实践](#最佳实践)

---

## 📖 项目简介

OpenSpec-cn是一个面向AI编程助手的规范驱动开发框架的简体中文汉化版本。v1.4.0版本新增了完整的Redmine集成功能，支持Sprint管理、Story拆分、Bug跟踪、代码审查和项目总结。

### 主要功能

- 🔗 **Redmine集成** - 无缝连接Redmine项目管理系统
- 📅 **Sprint管理** - 规划、跟踪和总结Sprint
- 📋 **Story管理** - 拆分和管理用户故事
- 🐛 **Bug管理** - 跟踪和管理缺陷
- 🔍 **代码审查** - 本地代码质量分析
- 📊 **项目总结** - 自动生成Sprint总结文档

### 版本信息

**当前版本**: v1.4.0  
**发布日期**: 2026-05-17  
**Node.js要求**: >=20.19.0

---

## 📥 安装指南

### 快速安装 (推荐)

OpenSpec-cn 推荐使用本地安装方式，详细安装步骤请参考：

**📖 [OpenSpec-cn 安装指南](openspec-cn-安装指南.md)**

### 快速安装命令

如果您已经下载了项目文件，可以使用快速安装脚本：

```powershell
# Windows PowerShell
cd indie_proj
.\setup.ps1
```

```bash
# Linux/macOS
cd indie_proj
chmod +x setup.sh
./setup.sh
```

### 验证安装

安装完成后，验证安装是否成功：

```bash
# 检查版本
openspec-cn --version

# 查看帮助
openspec-cn --help
```

### 安装方式对比

| 安装方式 | 优点 | 缺点 | 适用场景 |
|---------|------|------|---------|
| **本地安装** (推荐) | 项目独立、版本灵活、无需管理员权限 | 需要配置路径 | 开发环境、多项目开发 |
| **全局安装** | 命令简捷、全局可用 | 版本固定、需要管理员权限 | 单一项目、个人使用 |

---

## 🚀 首次配置

### 初始化项目

```bash
# 初始化新项目
openspec-cn init

# 指定项目目录
openspec-cn init my-project

# 使用特定 Schema
openspec-cn init my-project --schema openspec
```

### 配置Redmine

```bash
# 交互式配置
openspec-cn redmine setup

# 配置过程会提示输入：
# - 服务器地址
# - API密钥
# - 项目ID
# - 实例名称
```

### 查看帮助

```bash
# 总帮助
openspec-cn --help

# 特定命令帮助
openspec-cn [command] --help
```

---

## 📚 基础概念

### OpenSpec工作流

OpenSpec采用规范驱动开发(SDD)的工作流：

```
Proposal → Specs → Design → Tasks → Apply → Archive
```

### Hermes工作流 (Redmine集成)

扩展的7状态工作流：

```
Plan → Propose → Applying → Done → Code Review → Testing → Archiving
```

### 数据结构

```
openspec/
├── sprints/          # Sprint目录
│   ├── sprint-v1.4/
│   │   ├── sprint.md
│   │   ├── .openspec.yaml
│   │   └── stories/
├── changes/          # Change目录
│   ├── user-auth/
│   │   ├── proposal.md
│   │   ├── specs/
│   │   ├── design.md
│   │   ├── tasks.md
│   │   └── .openspec.yaml
├── bugs/            # Bug目录
│   ├── bug-123/
│   │   ├── bug.md
│   │   └── .openspec.yaml
└── specs/           # 主规范目录
```

---

## 🔗 Redmine集成

### 配置Redmine

#### 交互式配置

```bash
openspec-cn redmine setup
```

配置过程中需要提供：
- **服务器地址**: Redmine服务器URL
- **API密钥**: Redmine API访问密钥
- **项目ID**: 对应的Redmine项目ID
- **实例名称**: 自定义实例名称 (如: dev, staging, production)

#### 验证配置

```bash
# 测试连接
openspec-cn redmine test

# 查看当前实例
openspec-cn redmine current

# 列出所有配置的实例
openspec-cn redmine list
```

### 多实例管理

支持配置多个Redmine实例，自动根据Git Worktree切换：

```bash
# 切换到不同的Git Worktree
cd /path/to/dev-worktree
openspec-cn redmine current  # 自动使用dev实例

cd /path/to/prod-worktree
openspec-cn redmine current  # 自动使用prod实例
```

---

## 📅 Sprint管理

### 创建Sprint

```bash
# 基本创建
openspec-cn sprint create sprint-v1.4

# 指定截止日期
openspec-cn sprint create sprint-v1.4 --due-date 2026-06-30

# 添加描述
openspec-cn sprint create sprint-v1.4 --due-date 2026-06-30 --description "主要功能开发"
```

### 规划Sprint

```bash
# 规划Story (从现有提案拆分)
openspec-cn sprint plan sprint-v1.4
```

这个过程会：
1. 读取openspec/changes/目录中的proposal
2. AI分析并拆分为可执行的stories
3. 生成stories/目录下的story文档
4. 同步创建Redmine Story issues

### 查看Sprint

```bash
# 列出所有Sprint
openspec-cn sprint list

# 查看特定Sprint
openspec sprint show sprint-v1.4
```

### 关闭Sprint

```bash
# 关闭并归档Sprint
openspec-cn sprint close sprint-v1.4
```

这会：
1. 更新Redmine Version状态
2. 生成Sprint总结文档
3. 归档Sprint到archived/目录

---

## 📋 Story管理

### 拆分Story

```bash
# 从Sprint中拆分Story
openspec-cn story breakdown sprint-v1.4 user-auth

# 从特定proposal拆分
openspec-cn story breakdown sprint-v1.4 --from-proposal ./openspec/changes/auth-proposal/proposal.md
```

### 完善Story

```bash
# 添加验收标准
openspec-cn story refine user-auth

# 生成更详细的Story文档
openspec-cn story refine user-auth --detailed
```

### 查看Story

```bash
# 列出Sprint中的所有Story
openspec-cn story list sprint-v1.4

# 查看特定Story
openspec-cn story show user-auth
```

---

## 🐛 Bug管理

### 创建Bug

```bash
# 基本创建
openspec-cn bug create "用户无法登录"

# 指定严重程度
openspec-cn bug create "登录失败" --severity critical

# 关联Story
openspec-cn bug create "数据丢失" --related user-auth

# 完整创建
openspec-cn bug create "密码重置失败" --severity high --related user-auth --description "用户点击重置密码后没有收到邮件"
```

### 更新Bug状态

```bash
# 更新状态
openspec-cn bug update 123 --status fixed

# 添加说明
openspec-cn bug update 123 --status fixed --note "已修复问题，等待验证"

# 更新严重程度
openspec-cn bug update 123 --priority high
```

### 查看Bug

```bash
# 列出所有Bug
openspec-cn bug list

# 按状态过滤
openspec-cn bug list --status new

# 按严重程度过滤
openspec-cn bug list --severity critical

# 查看特定Bug
openspec-cn bug show 123
```

---

## 🔄 任务同步

### 拆分任务

```bash
# 从Story拆分任务
openspec-cn task breakdown user-auth

# 生成任务列表
```

这会：
1. 读取Story的proposal和design文档
2. AI分析并拆分为可执行的任务
3. 生成tasks.md文件 (checkbox格式)
4. 创建Redmine Task issues

### 同步进度

```bash
# 同步任务进度到Redmine
openspec-cn task sync user-auth
```

同步逻辑：
1. 解析tasks.md中的checkbox状态
2. 计算完成百分比
3. 更新Redmine issue的done_ratio
4. 如果全部完成，更新状态为Done

### 查看任务状态

```bash
# 查看任务状态
openspec-cn task status user-auth

# 查看详细进度
openspec-cn task status user-auth --verbose
```

### 任务格式

```markdown
# tasks.md

## 开发任务

- [ ] 1.1 创建认证模块
- [x] 1.2 实现登录API
- [ ] 1.3 添加token验证
- [x] 1.4 编写单元测试

## 测试任务

- [ ] 2.1 集成测试
- [ ] 2.2 端到端测试
```

---

## 🔍 代码审查

### 审查单个变更

```bash
# 基本审查
openspec-cn review change user-auth

# 保存审查报告
openspec-cn review change user-auth --save

# 指定输出文件
openspec-cn review change user-auth --save -o review-results.md

# 同步到Redmine
openspec-cn review change user-auth --sync
```

### 审查整个Sprint

```bash
# 审查Sprint中的所有变更
openspec-cn review sprint sprint-v1.4

# 失败时退出
openspec-cn review sprint sprint-v1.4 --fail-on-issues

# 详细输出
openspec-cn review sprint sprint-v1.4 --verbose
```

### 审查评分

代码审查会生成0-100分的评分：
- **80-100分**: ✅ 通过
- **60-79分**: ⚠️ 需要改进
- **0-59分**: ❌ 失败

评分标准：
- **Critical问题**: -20分/个
- **Major问题**: -10分/个
- **Minor问题**: -3分/个
- **Info问题**: -1分/个
- **合理代码量**: +5分

### 审查内容

代码审查会检查：
1. **安全问题**: SQL注入、eval使用、硬编码密钥、console语句
2. **错误处理**: 空catch块、异常处理
3. **性能问题**: 循环效率、字符串拼接、复杂算法
4. **代码风格**: 魔法数字、行长限制、TODO注释

### 审查报告

审查报告包含：
- 总体评分和状态
- 统计数据 (文件数、代码行数、问题数)
- 问题描述和建议
- 正面发现
- 详细的问题列表

---

## 📊 Sprint总结

### 生成Sprint总结

```bash
# 基本生成
openspec-cn sprint-spec generate sprint-v1.4

# 包含代码统计
openspec-cn sprint-spec generate sprint-v1.4 --code-stats

# 包含时间统计
openspec-cn sprint-spec generate sprint-v1.4 --time-stats

# 指定输出路径
openspec-cn sprint-spec generate sprint-v1.4 -o summary.md

# 详细输出
openspec-cn sprint-spec generate sprint-v1.4 --verbose
```

### 总结内容

生成的总结文档包含：

#### 概览
- Sprint期间
- 总Story/完成Story
- 总Task/完成Task
- Bug修复情况
- 进度百分比

#### Stories
- 所有Story的完成情况

#### Tasks
- 所有Task的完成情况

#### Bug修复
- 已修复和未修复的Bug统计

#### 文档位置
- Proposals路径
- Specs路径
- Designs路径
- Tasks路径

#### 相关代码
- 修改的文件
- 相关的Git提交
- 相关的分支

#### 时间统计
- 每个Story/Task的预估工时 vs 实际工时
- 工时偏差分析

#### 未完成分析
- 未完成的Stories和Tasks
- 阻塞项
- 延期项
- 未完成原因分析

#### 经验总结
- 做得好的地方
- 需要改进的地方
- 可复用的模板

### 上传到Redmine

```bash
# 上传到Redmine Wiki
openspec-cn sprint-spec upload sprint-v1.4

# 指定Wiki页面名称
openspec-cn sprint-spec upload sprint-v1.4 --page "Sprint总结-v1.4"

# 指定格式
openspec-cn sprint-spec upload sprint-v1.4 --format markdown
```

### 查看所有Spec

```bash
# 列出所有Spec文档
openspec-cn sprint-spec list

# 显示详细路径
openspec-cn sprint-spec list --verbose
```

---

## 🔄 工作流程示例

### 完整的Sprint开发流程

```bash
# Phase 1: Sprint规划
openspec-cn sprint create sprint-v1.5 --due-date 2026-06-15
openspec-cn sprint plan sprint-v1.5

# Phase 2: Story开发
openspec-cn story breakdown sprint-v1.5 user-auth
openspec-cn task breakdown user-auth

# Phase 3: 开发过程
# (进行代码开发...)
# 编辑 tasks.md 勾选完成项
openspec-cn task sync user-auth

# Phase 4: 代码审查
openspec-cn review change user-auth --save
openspec-cn review change user-auth --sync

# Phase 5: Bug处理
openspec-cn bug create "登录超时" --severity critical
# (修复Bug...)
openspec-cn bug update 789 --status fixed

# Phase 6: Sprint总结
openspec-cn sprint-spec generate sprint-v1.5

# Phase 7: 归档
openspec-cn sprint close sprint-v1.5
```

### Bug处理工作流

```bash
# 1. 发现Bug
openspec-cn bug create "数据不一致" --severity major --related user-auth

# 2. 分配和修复
# (开发人员进行修复...)

# 3. 更新状态
openspec-cn bug update 123 --status in-progress --note "正在修复"

# 4. 完成修复
openspec-cn bug update 123 --status fixed --note "修复完成，等待测试"

# 5. 测试验证
openspec-cn bug update 123 --status verified --note "测试通过"
```

### 代码审查工作流

```bash
# 1. 开发完成代码
git add .
git commit -m "feat: implement user authentication"

# 2. 运行代码审查
openspec-cn review change user-auth

# 3. 查看审查报告
cat openspec/changes/user-auth/review.md

# 4. 修复问题
# (根据审查报告修复代码...)

# 5. 重新审查
openspec-cn review change user-auth --sync

# 6. 审查通过后进入测试阶段
```

---

## ❓ 常见问题

### 安装问题

**Q: 安装时提示Node.js版本不匹配？**

A: OpenSpec-cn需要Node.js >=20.19.0，请升级Node.js版本。

```bash
# 检查Node.js版本
node --version

# 升级到最新版本
nvm install 20
nvm use 20
```

**Q: 命令找不到？**

A: 请确保已正确安装OpenSpec-cn。详细安装步骤请参考：

**📖 [OpenSpec-cn 安装指南](openspec-cn-安装指南.md)**

常见解决方法：

```bash
# 方法1: 使用完整路径
node /path/to/openspec-cn/bin/openspec.js --version

# 方法2: 配置环境变量
export PATH="$PATH:/path/to/openspec-cn/bin"

# 方法3: 重新运行安装脚本
cd indie_proj
./setup.ps1  # Windows
./setup.sh   # Linux/macOS
```

### Redmine集成问题

**Q: Redmine连接失败？**

A: 检查redmine-cli是否可用，配置是否正确。

```bash
# 检查redmine-cli
red-cli --version

# 测试配置
openspec-cn redmine test

# 查看当前配置
openspec-cn redmine current
```

**Q: 多实例切换不生效？**

A: 确保在正确的Git Worktree目录中。

```bash
# 检查当前Git工作目录
git rev-parse --show-toplevel

# 检查当前实例
openspec-cn redmine current

# 手动指定实例
openspec-cn redmine current --instance staging
```

### Sprint管理问题

**Q: Sprint规划失败？**

A: 检查openspec/changes/目录中是否有proposal文件。

```bash
# 查看可用的提案
ls openspec/changes/

# 确保proposal文件存在
ls openspec/changes/*/proposal.md
```

**Q: 任务同步失败？**

A: 检查tasks.md文件格式和Redmine连接。

```bash
# 检查tasks.md格式
cat openspec/changes/user-auth/tasks.md

# 测试Redmine连接
openspec-cn redmine test
```

### 代码审查问题

**Q: 代码审查报告为空？**

A: 检查是否有代码变更和Git配置。

```bash
# 检查Git状态
git status

# 查看代码变更
git diff

# 检查是否有提交
git log --oneline -5
```

**Q: 审查评分不合理？**

A: 可以调整评分权重或添加自定义规则。

```bash
# 查看审查报告
cat openspec/changes/user-auth/review.md

# 根据需要调整代码或配置
```

### Sprint总结问题

**Q: 总结生成缺少某些信息？**

A: 检查Sprint元数据和文档是否完整。

```bash
# 检查Sprint元数据
cat openspec/sprints/sprint-v1.4/.openspec.yaml

# 检查Story文档
ls openspec/changes/*/tasks.md

# 重新生成
openspec-cn sprint-spec generate sprint-v1.4
```

---

## 💡 最佳实践

### Sprint规划

1. **提前规划**: 在Sprint开始前完成规划，避免中期变更
2. **合理估算**: 基于历史数据估算Story和Task时间
3. **明确目标**: 每个Sprint有清晰的目标和成功标准
4. **团队参与**: 让团队成员参与Sprint规划

### Story管理

1. **最小可行**: Story应该是最小可测试单元
2. **独立完成**: Story应该尽可能独立完成
3. **清晰描述**: Story描述应该清晰明确，便于理解
4. **验收标准**: 每个Story都应有明确的验收标准

### Bug管理

1. **及时记录**: 发现Bug立即记录，不要遗漏
2. **详细描述**: Bug描述应该包含复现步骤和环境信息
3. **优先级明确**: 根据严重程度合理设置优先级
4. **跟踪状态**: 及时更新Bug状态，避免遗忘

### 代码审查

1. **定期审查**: 定期进行代码审查，保持代码质量
2. **客观评价**: 审查应该基于标准，避免主观偏见
3. **建设性反馈**: 提供具体的改进建议
4. **持续改进**: 根据审查结果持续改进代码质量

### Sprint总结

1. **及时总结**: Sprint结束后立即生成总结，趁热打铁
2. **数据驱动**: 基于实际数据进行分析，避免主观臆断
3. **经验积累**: 总结经验教训，形成团队知识库
4. **持续优化**: 根据总结结果持续优化工作流程

---

## 🎓 进阶使用

### 自定义配置

```bash
# 查看当前配置
openspec-cn config

# 设置AI工具
openspec-cn config set ai-tool "claude"

# 设置输出目录
openspec-cn config set output-dir "./openspec"
```

### 工作流自定义

```bash
# 查看可用Schema
openspec-cn schemas list

# 查看Schema详情
openspec-cn schemas show openspec

# 使用自定义Schema
openspec-cn new my-project --schema openspec
```

### 集成到CI/CD

```bash
# 在CI脚本中使用
openspec-cn review change ${CHANGE_NAME} --save
openspec-cn task sync ${CHANGE_NAME}

# 检查审查结果
if [ $? -ne 0 ]; then
  echo "代码审查失败"
  exit 1
fi
```

### 团队协作

1. **统一配置**: 团队使用统一的配置文件
2. **标准化流程**: 建立标准化的开发流程
3. **知识共享**: 通过Sprint总结共享经验
4. **持续改进**: 定期评估和改进工作流程

---

## 📞 技术支持

### 文档资源

- **安装指南**: [openspec-cn-安装指南.md](openspec-cn-安装指南.md)
- **项目README**: [README.md](README.md)
- **API文档**: [命令参考](INSTALL.md)
- **开发文档**: [REDMINE_INTEGRATION_PROGRESS.md](REDMINE_INTEGRATION_PROGRESS.md)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

### 获取帮助

```bash
# 命令行帮助
openspec-cn --help
openspec-cn [command] --help

# 查看特定命令详情
openspec-cn sprint --help
openspec-cn review --help
```

### 反馈渠道

- **GitHub Issues**: https://github.com/studyzy/OpenSpec-cn/issues
- **反馈命令**: `openspec-cn feedback "您的建议"`

---

## 🚀 快速参考

### 常用命令速查

```bash
# 项目管理
openspec-cn init                    # 初始化项目
openspec-cn list                    # 列出变更
openspec-cn view                    # 查看仪表板

# Redmine集成
openspec-cn redmine setup          # 配置Redmine
openspec-cn redmine test            # 测试连接
openspec-cn redmine current         # 查看当前实例

# 更多安装相关命令请参考: openspec-cn-安装指南.md

# Sprint管理
openspec-cn sprint create <name>    # 创建Sprint
openspec-cn sprint plan <name>      # 规划Sprint
openspec-cn sprint close <name>     # 关闭Sprint
openspec-cn sprint list             # 列出Sprint

# Story管理
openspec-cn story breakdown <sprint> <change>  # 拆分Story
openspec-cn story refine <name>     # 完善Story
openspec-cn story list             # 列出Story

# Bug管理
openspec-cn bug create <title>      # 创建Bug
openspec-cn bug update <id>         # 更新Bug
openspec-cn bug list               # 列出Bug

# 任务管理
openspec-cn task breakdown <name>  # 拆分任务
openspec-cn task sync <name>        # 同步进度
openspec-cn task status <name>      # 查看状态

# 代码审查
openspec-cn review change <name>    # 审查变更
openspec-cn review sprint <name>    # 审查Sprint

# Sprint总结
openspec-cn sprint-spec generate <sprint>  # 生成总结
openspec-cn sprint-spec upload <sprint>    # 上传到Redmine
openspec-cn sprint-spec list                # 列出Spec

# 帮助
openspec-cn --help                    # 总帮助
openspec-cn [command] --help          # 命令帮助
```

---

**版本**: v1.4.0  
**更新日期**: 2026-05-17  
**维护团队**: OpenSpec Contributors

🎉 **享受高效的规范驱动开发体验！**