# OpenSpec-cn 安装指南

## 📋 目录

1. [系统要求](#系统要求)
2. [本地安装](#本地安装)
3. [全局安装](#全局安装)
4. [配置验证](#配置验证)
5. [常见问题](#常见问题)

---

## 💻 系统要求

### 必需环境

- **Node.js**: >= 20.19.0
- **pnpm**: >= 8.0.0
- **PowerShell**: >= 5.1 (Windows) 或 Bash (Linux/macOS)
- **Git**: >= 2.0.0

### 检查环境

```bash
# 检查 Node.js
node --version

# 检查 pnpm
pnpm --version

# 检查 Git
git --version

# 检查 PowerShell (Windows)
$PSVersionTable.PSVersion
```

---

## 🏠 本地安装 (推荐)

本地安装方式适用于需要在不同项目间切换使用，或希望保持项目独立性。

### 方法1: 使用自动安装脚本

这是最简单快捷的安装方式，自动化处理所有依赖构建。

#### Windows PowerShell 安装

```powershell
# 1. 进入 indie_proj 目录
cd path/to/ai_tool_collection/indie_proj

# 2. 运行安装脚本
.\setup.ps1

# 3. 等待安装完成
```

安装脚本会自动完成以下步骤：
1. ✅ 检查 Node.js 环境
2. ✅ 构建 redmine-cli
3. ✅ 安装 OpenSpec-cn 依赖
4. ✅ 构建 OpenSpec-cn
5. ✅ 验证安装结果

#### Linux/macOS Bash 安装

```bash
# 1. 进入 indie_proj 目录
cd path/to/ai_tool_collection/indie_proj

# 2. 确保脚本可执行
chmod +x setup.sh

# 3. 运行安装脚本
./setup.sh
```

### 方法2: 手动安装

如果自动安装脚本出现问题，可以手动按步骤安装。

#### 步骤1: 构建 redmine-cli

```powershell
# Windows PowerShell
cd redmine-cli
.\build.ps1
cd ..

# Linux/macOS Bash
cd redmine-cli
bash build.sh
cd ..
```

#### 步骤2: 安装 OpenSpec-cn 依赖

```bash
# 进入 OpenSpec-cn 目录
cd openspec-cn

# 安装依赖
pnpm install

# 返回上级目录
cd ..
```

#### 步骤3: 构建 OpenSpec-cn

```bash
# 进入 OpenSpec-cn 目录
cd openspec-cn

# 构建项目
pnpm run build

# 返回上级目录
cd ..
```

### 配置环境变量

安装完成后，需要配置环境变量以便在任意位置使用命令。

#### Windows PowerShell

```powershell
# 临时设置 (当前会话有效)
$env:PATH += ";$(pwd)\redmine-cli\bin;$(pwd)\openspec-cn\bin"

# 永久设置 (添加到用户环境变量)
[System.Environment]::SetEnvironmentVariable('Path', $env:Path + ';' + "$((Get-Location).Path)\redmine-cli\bin;$((Get-Location).Path)\openspec-cn\bin", 'User')
```

#### Linux/macOS

```bash
# 临时设置 (当前会话有效)
export PATH="$PATH:$(pwd)/redmine-cli/bin:$(pwd)/openspec-cn/bin"

# 永久设置 (添加到 ~/.bashrc 或 ~/.zshrc)
echo 'export PATH="$PATH:'$(pwd)'/redmine-cli/bin:$(pwd)/openspec-cn/bin"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🌍 全局安装

全局安装方式适用于需要在多个项目中使用相同版本，或希望简化命令调用。

### 全局安装 OpenSpec-cn

```bash
# 使用 npm 全局安装
npm install -g @studyzy/openspec-cn@1.4.0

# 使用 pnpm 全局安装
pnpm add -g @studyzy/openspec-cn@1.4.0
```

### 全局安装 redmine-cli

```bash
# 克隆 redmine-cli 项目
git clone https://github.com/your-repo/redmine-cli.git
cd redmine-cli

# 构建并全局安装
npm install -g .

# 或使用 pnpm
pnpm install -g .
```

### 验证全局安装

```bash
# 检查 OpenSpec-cn 版本
openspec-cn --version

# 检查 redmine-cli 版本
red-cli --version
```

---

## ✅ 配置验证

### 验证 OpenSpec-cn 安装

```bash
# 查看版本信息
openspec-cn --version

# 查看帮助信息
openspec-cn --help

# 列出可用命令
openspec-cn --help
```

### 验证 redmine-cli 安装

```bash
# 查看版本信息
red-cli --version

# 查看帮助信息
red-cli --help
```

### 测试 OpenSpec-cn 功能

```bash
# 测试基本命令
openspec-cn list

# 测试 Schema 列表
openspec-cn schemas list
```

### 验证 Redmine 集成

```bash
# 配置 Redmine (首次使用)
openspec-cn redmine setup

# 测试连接
openspec-cn redmine test

# 查看当前实例
openspec-cn redmine current
```

---

## ❓ 常见问题

### 安装问题

**Q: 安装时提示 Node.js 版本不匹配？**

A: OpenSpec-cn 需要 Node.js >= 20.19.0，请升级 Node.js 版本。

```bash
# 检查 Node.js 版本
node --version

# 使用 nvm 升级
nvm install 20
nvm use 20

# 或下载最新版本
# https://nodejs.org/
```

**Q: pnpm 安装失败？**

A: 确保 pnpm 已正确安装。

```bash
# 安装 pnpm
npm install -g pnpm

# 验证安装
pnpm --version
```

**Q: 构建失败，提示依赖错误？**

A: 清除缓存并重新安装依赖。

```bash
# 清除 pnpm 缓存
pnpm store prune

# 删除 node_modules
rm -rf node_modules

# 重新安装
pnpm install
```

### 配置问题

**Q: 环境变量设置后命令仍然找不到？**

A: 检查环境变量配置是否正确，重新启动终端。

```bash
# 检查当前 PATH
echo $PATH

# Windows PowerShell
$env:PATH -split ';'

# 重新启动终端后验证
openspec-cn --version
```

**Q: 多个项目版本冲突？**

A: 使用项目本地安装，通过相对路径调用命令。

```bash
# 使用完整路径
node /path/to/project/openspec-cn/bin/openspec.js --version

# 或创建项目别名
cd /path/to/project
alias openspec='node openspec-cn/bin/openspec.js'
```

### Redmine 集成问题

**Q: redmine-cli 构建失败？**

A: 检查 redmine-cli 项目的构建脚本。

```bash
# 进入 redmine-cli 目录
cd redmine-cli

# 检查构建脚本
cat build.ps1  # Windows
cat build.sh    # Linux/macOS

# 手动执行构建命令
npm install
npm run build
```

**Q: Redmine 连接测试失败？**

A: 检查网络连接和 API 配置。

```bash
# 测试网络连接
ping your-redmine-server.com

# 检查 API 密钥格式
openspec-cn redmine current

# 重新配置
openspec-cn redmine setup
```

### 权限问题

**Q: 权限不足无法安装？**

A: 使用管理员权限或用户目录安装。

```bash
# Windows: 以管理员身份运行 PowerShell
# 右键点击 PowerShell -> 以管理员身份运行

# Linux/macOS: 使用 sudo (谨慎使用)
sudo npm install -g @studyzy/openspec-cn

# 或使用用户目录安装
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
npm install -g @studyzy/openspec-cn
```

### 更新问题

**Q: 如何更新到新版本？**

A: 根据安装方式选择更新方法。

```bash
# 全局安装更新
npm update -g @studyzy/openspec-cn

# 本地安装更新
cd openspec-cn
git pull origin main
pnpm install
pnpm run build

# 使用新版本部署包
rm -rf openspec-cn
tar -xzf openspec-cn-1.5.0.tar.gz
cd openspec-cn-1.5.0
node bin/openspec.js --version
```

### 卸载问题

**Q: 如何完全卸载？**

A: 根据安装方式选择卸载方法。

```bash
# 全局安装卸载
npm uninstall -g @studyzy/openspec-cn
npm uninstall -g redmine-cli

# 本地安装卸载
rm -rf openspec-cn
rm -rf redmine-cli

# 清除配置文件
rm -rf ~/.openspec
rm -rf ~/.redmine-cli

# 清除环境变量
# 编辑 ~/.bashrc 或环境变量设置，删除相关配置
```

---

## 📞 技术支持

### 获取帮助

```bash
# 查看安装帮助
openspec-cn --help

# 查看特定命令帮助
openspec-cn [command] --help

# 查看配置信息
openspec-cn config
```

### 文档资源

- **安装文档**: [openspec-cn-安装指南.md](openspec-cn-安装指南.md)
- **使用文档**: [openspec-cn-使用说明.md](openspec-cn-使用说明.md)
- **项目README**: [README.md](README.md)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

### 反馈渠道

- **GitHub Issues**: https://github.com/studyzy/OpenSpec-cn/issues
- **技术支持**: openspec-cn-feedback@example.com

---

## 🎉 安装完成

恭喜！OpenSpec-cn 已成功安装。现在可以开始使用了：

```bash
# 查看 Quick Start
openspec-cn --help

# 初始化项目
openspec-cn init

# 配置 Redmine
openspec-cn redmine setup
```

详细信息请参考 [OpenSpec-cn 使用说明.md](openspec-cn-使用说明.md)

---

**版本**: v1.4.0  
**更新日期**: 2026-05-17  
**维护团队**: OpenSpec Contributors