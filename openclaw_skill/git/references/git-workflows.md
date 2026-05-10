# Git 工作流参考

## 分支策略详解

### Git Flow

```
                    main
                      │
                      │─────────────────────── v1.0.0 (tag)
                      │                       │
                      │    develop            │
                      │      │                │
                      │      ├─ feature/a     │
                      │      │      │         │
                      │      │      └─────────┤
                      │      │                │
                      │      ├─ feature/b     │
                      │      │      │         │
                      │      │      └─────────┤
                      │      │                │
                      │      └─ release/v1.0 ─┤
                      │                       │
                      └───────────────────────┘
```

### Trunk Based Development

```
main ─────●─────●─────●─────●─────●─────●─────→
          │           │     │
          │           │     └── 短期分支快速合并
          │           │
          └── 特性开关控制发布
```

### GitHub Flow（推荐用于本项目）

```
main ─────●─────●─────●─────●─────●─────→
          │           │
          └─ feature  └─ feature
               │            │
               └──── PR ────┘
```

---

## 常用 Git 命令速查

### 基础操作

```bash
# 初始化仓库
git init

# 克隆仓库
git clone <url>

# 查看状态
git status

# 查看历史
git log --oneline --graph

# 查看差异
git diff
git diff --cached
```

### 分支操作

```bash
# 创建分支
git branch <branch-name>

# 切换分支
git checkout <branch-name>
git switch <branch-name>  # Git 2.23+

# 创建并切换
git checkout -b <branch-name>
git switch -c <branch-name>

# 合并分支
git merge <branch-name>

# 删除分支
git branch -d <branch-name>

# 强制删除
git branch -D <branch-name>

# 查看所有分支
git branch -a
```

### 远程操作

```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin <url>

# 推送
git push origin <branch>

# 拉取
git pull origin <branch>

# 获取（不合并）
git fetch origin
```

### 撤销操作

```bash
# 撤销工作区更改
git checkout -- <file>
git restore <file>  # Git 2.23+

# 撤销暂存
git reset HEAD <file>
git restore --staged <file>  # Git 2.23+

# 撤销提交（保留更改）
git reset --soft HEAD~1

# 撤销提交（丢弃更改）
git reset --hard HEAD~1

# 修改最后一次提交
git commit --amend
```

### Stash 操作

```bash
# 暂存当前更改
git stash

# 暂存并添加消息
git stash save "message"

# 查看暂存列表
git stash list

# 应用暂存
git stash apply

# 应用并删除暂存
git stash pop

# 删除暂存
git stash drop
```

---

## Commit 消息规范

### Conventional Commits

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 类型列表

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat: 添加用户登录功能 |
| `fix` | Bug 修复 | fix: 修复日期格式化错误 |
| `docs` | 文档 | docs: 更新 README |
| `style` | 格式 | style: 格式化代码 |
| `refactor` | 重构 | refactor: 重构订单服务 |
| `perf` | 性能 | perf: 优化查询性能 |
| `test` | 测试 | test: 添加单元测试 |
| `build` | 构建 | build: 更新构建配置 |
| `ci` | CI/CD | ci: 更新 GitHub Actions |
| `chore` | 其他 | chore: 更新依赖 |
| `revert` | 回滚 | revert: 回滚 xxx 提交 |

### 示例

```
feat(auth): 添加 JWT 认证功能

- 实现 JWT 生成和验证
- 添加认证中间件
- 更新用户登录接口

Closes: TASK-123
Breaking change: 需要更新客户端认证方式
```

---

## Git Hooks

### pre-commit

```bash
#!/bin/sh
# .git/hooks/pre-commit

# 运行代码检查
npm run lint

# 运行测试
npm run test

# 检查是否有敏感信息
if git diff --cached --name-only | xargs grep -l "password\|secret\|api_key"; then
  echo "错误: 检测到敏感信息"
  exit 1
fi
```

### commit-msg

```bash
#!/bin/sh
# .git/hooks/commit-msg

# 验证 commit 消息格式
commit_msg=$(cat "$1")
pattern="^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
  echo "错误: Commit 消息格式不正确"
  echo "格式: <type>(<scope>): <description>"
  echo "示例: feat(auth): 添加登录功能"
  exit 1
fi
```

### pre-push

```bash
#!/bin/sh
# .git/hooks/pre-push

# 运行完整测试
npm run test:coverage

# 检查覆盖率
if [ $? -ne 0 ]; then
  echo "错误: 测试未通过"
  exit 1
fi
```

---

## 处理常见问题

### 1. 撤销已推送的提交

```bash
# 方法1: 创建反向提交
git revert <commit-hash>
git push origin <branch>

# 方法2: 强制回滚（谨慎使用）
git reset --hard <commit-hash>
git push --force origin <branch>
```

### 2. 合并多个提交

```bash
# 交互式 rebase
git rebase -i HEAD~3

# 在编辑器中将 pick 改为 squash
# pick abc1234 第一个提交
# squash def5678 第二个提交
# squash ghi9012 第三个提交
```

### 3. 从其他分支摘取提交

```bash
# cherry-pick 单个提交
git cherry-pick <commit-hash>

# cherry-pick 多个提交
git cherry-pick <hash1> <hash2>

# cherry-pick 范围
git cherry-pick <start-hash>..<end-hash>
```

### 4. 解决合并冲突

```bash
# 查看冲突文件
git status

# 使用 ours（保留当前分支）
git checkout --ours <file>

# 使用 theirs（使用远程分支）
git checkout --theirs <file>

# 手动编辑后
git add <file>
git commit
```

### 5. 找回丢失的提交

```bash
# 查看操作历史
git reflog

# 恢复到指定提交
git checkout <commit-hash>

# 创建新分支保存
git branch recovery-branch <commit-hash>
```

---

## Git 别名配置

```bash
# 常用别名
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --oneline --graph --all'
git config --global alias.amend 'commit --amend --no-edit'

# 使用
git co main
git br feature/new
git ci -m "message"
git st
git unstage file.txt
git last
git visual
```

---

## 项目 Git 配置模板

### .gitignore

```gitignore
# 依赖
node_modules/
.pnpm-store/

# 构建
dist/
build/
out/

# 日志
logs/
*.log
npm-debug.log*

# 环境
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.sublime-*
*.swp
*.swo

# 测试
coverage/
.nyc_output/

# 系统文件
.DS_Store
Thumbs.db

# 临时文件
tmp/
temp/
*.tmp

# 敏感文件
*.pem
*.key
secrets/
credentials/
```

### .gitattributes

```gitattributes
# 自动检测文本文件并转换换行符
* text=auto

# 强制 LF 换行符
*.ts text eol=lf
*.js text eol=lf
*.json text eol=lf
*.md text eol=lf

# 二进制文件
*.png binary
*.jpg binary
*.gif binary
*.ico binary
```

### .gitkeep

```bash
# 保留空目录
touch logs/.gitkeep
touch tmp/.gitkeep
```
