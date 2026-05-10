"""
Git操作封装

封装Git命令，提供版本控制接口
"""

import os
import logging
from typing import List, Optional, Dict
from datetime import datetime

try:
    from git import Repo, GitCommandError, InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    Repo = None
    GitCommandError = Exception
    InvalidGitRepositoryError = Exception


logger = logging.getLogger(__name__)


class GitHelper:
    """Git操作辅助类"""

    def __init__(self, repo_path: str):
        """
        初始化Git仓库

        Args:
            repo_path: Git仓库路径

        Raises:
            ValueError: 路径不存在
            RuntimeError: GitPython未安装
        """
        if not GIT_AVAILABLE:
            raise RuntimeError("GitPython未安装，请运行: pip install gitpython")

        if not os.path.exists(repo_path):
            raise ValueError(f"路径不存在: {repo_path}")

        self.repo_path = repo_path
        self.repo: Optional[Repo] = None

        # 尝试打开现有仓库
        try:
            self.repo = Repo(repo_path)
            logger.info(f"已打开现有Git仓库: {repo_path}")
        except InvalidGitRepositoryError:
            logger.info(f"路径不是Git仓库，将在init_repo()时初始化: {repo_path}")

    def init_repo(self) -> bool:
        """
        初始化Git仓库

        Returns:
            True if 成功, False otherwise

        Example:
            >>> helper = GitHelper("/path/to/repo")
            >>> helper.init_repo()
            True
        """
        try:
            if self.repo is not None:
                logger.warning("仓库已存在，跳过初始化")
                return True

            self.repo = Repo.init(self.repo_path)
            logger.info(f"成功初始化Git仓库: {self.repo_path}")
            return True
        except Exception as e:
            logger.error(f"初始化Git仓库失败: {e}")
            return False

    def commit(
        self,
        message: str,
        files: Optional[List[str]] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> bool:
        """
        提交文件到Git

        Args:
            message: 提交消息
            files: 要提交的文件列表，None表示提交所有更改
            author_name: 作者名称（可选）
            author_email: 作者邮箱（可选）

        Returns:
            True if 成功, False otherwise

        Example:
            >>> helper.commit("添加新功能", ["src/new_feature.py"])
            True
        """
        if self.repo is None:
            logger.error("仓库未初始化")
            return False

        try:
            # 添加文件到暂存区
            if files is None:
                # 提交所有更改
                self.repo.git.add(A=True)
            else:
                # 提交指定文件
                for file in files:
                    file_path = os.path.join(self.repo_path, file)
                    if os.path.exists(file_path):
                        self.repo.git.add(file)
                    else:
                        logger.warning(f"文件不存在，跳过: {file}")

            # 检查是否有更改需要提交
            if not self.repo.is_dirty(untracked_files=True):
                logger.info("没有更改需要提交")
                return True

            # 设置作者信息（如果提供）
            if author_name and author_email:
                with self.repo.config_writer() as config:
                    config.set_value("user", "name", author_name)
                    config.set_value("user", "email", author_email)

            # 执行提交
            commit_obj = self.repo.index.commit(message)
            logger.info(f"成功提交: {commit_obj.hexsha[:8]} - {message}")
            return True

        except GitCommandError as e:
            logger.error(f"Git提交失败: {e}")
            return False
        except Exception as e:
            logger.error(f"提交过程出错: {e}")
            return False

    def push(
        self,
        remote: str = "origin",
        branch: str = "main",
        set_upstream: bool = False
    ) -> bool:
        """
        推送到远程仓库

        Args:
            remote: 远程仓库名称
            branch: 分支名称
            set_upstream: 是否设置上游分支

        Returns:
            True if 成功, False otherwise

        Example:
            >>> helper.push("origin", "main")
            True
        """
        if self.repo is None:
            logger.error("仓库未初始化")
            return False

        try:
            # 检查远程仓库是否存在
            if remote not in [r.name for r in self.repo.remotes]:
                logger.warning(f"远程仓库 '{remote}' 不存在，跳过推送")
                return False

            # 推送
            if set_upstream:
                self.repo.git.push('--set-upstream', remote, branch)
            else:
                self.repo.remotes[remote].push(branch)

            logger.info(f"成功推送到 {remote}/{branch}")
            return True

        except GitCommandError as e:
            logger.error(f"推送失败: {e}")
            return False
        except Exception as e:
            logger.error(f"推送过程出错: {e}")
            return False

    def get_commit_history(self, limit: int = 10) -> List[Dict]:
        """
        获取提交历史

        Args:
            limit: 最大返回数量

        Returns:
            提交历史列表，每项包含:
            {
                "sha": "提交哈希",
                "message": "提交消息",
                "author": "作者",
                "date": "提交时间"
            }

        Example:
            >>> history = helper.get_commit_history(5)
            >>> len(history) <= 5
            True
        """
        if self.repo is None:
            logger.error("仓库未初始化")
            return []

        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commits.append({
                    "sha": commit.hexsha,
                    "short_sha": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "date": datetime.fromtimestamp(commit.committed_date).isoformat()
                })

            logger.info(f"获取到 {len(commits)} 条提交记录")
            return commits

        except Exception as e:
            logger.error(f"获取提交历史失败: {e}")
            return []

    def get_current_branch(self) -> Optional[str]:
        """
        获取当前分支名称

        Returns:
            分支名称，如果仓库未初始化则返回None

        Example:
            >>> helper.get_current_branch()
            'main'
        """
        if self.repo is None:
            return None

        try:
            return self.repo.active_branch.name
        except Exception as e:
            logger.error(f"获取当前分支失败: {e}")
            return None

    def get_status(self) -> Dict:
        """
        获取仓库状态

        Returns:
            仓库状态信息:
            {
                "branch": "当前分支",
                "modified": ["修改的文件"],
                "untracked": ["未跟踪的文件"],
                "staged": ["已暂存的文件"]
            }

        Example:
            >>> status = helper.get_status()
            >>> isinstance(status, dict)
            True
        """
        if self.repo is None:
            return {
                "branch": None,
                "modified": [],
                "untracked": [],
                "staged": []
            }

        try:
            status = {
                "branch": self.get_current_branch(),
                "modified": [],
                "untracked": self.repo.untracked_files,
                "staged": []
            }

            # 获取修改的文件
            try:
                status["modified"] = [item.a_path for item in self.repo.index.diff(None)]
            except Exception:
                pass  # 如果没有HEAD，会抛出异常

            # 获取已暂存的文件
            try:
                status["staged"] = [item.a_path for item in self.repo.index.diff("HEAD")]
            except Exception:
                pass  # 如果没有提交，会抛出异常

            return status
        except Exception as e:
            logger.error(f"获取仓库状态失败: {e}")
            return {
                "branch": None,
                "modified": [],
                "untracked": [],
                "staged": []
            }

    def commit_with_retry(
        self,
        message: str,
        files: Optional[List[str]] = None,
        max_retries: int = 3
    ) -> bool:
        """
        带重试机制的提交

        Args:
            message: 提交消息
            files: 要提交的文件列表
            max_retries: 最大重试次数

        Returns:
            True if 成功, False otherwise

        Example:
            >>> helper.commit_with_retry("提交", max_retries=3)
            True
        """
        for attempt in range(max_retries):
            if self.commit(message, files):
                return True

            logger.warning(f"提交失败，重试 {attempt + 1}/{max_retries}")

        logger.error(f"提交失败，已达到最大重试次数 {max_retries}")
        return False

    def add_remote(self, name: str, url: str) -> bool:
        """
        添加远程仓库

        Args:
            name: 远程仓库名称（如"origin"）
            url: 远程仓库URL

        Returns:
            True if 成功, False otherwise

        Example:
            >>> helper.add_remote("origin", "https://github.com/user/repo.git")
            True
        """
        if self.repo is None:
            logger.error("仓库未初始化")
            return False

        try:
            self.repo.create_remote(name, url)
            logger.info(f"成功添加远程仓库: {name} -> {url}")
            return True
        except Exception as e:
            logger.error(f"添加远程仓库失败: {e}")
            return False

    def get_last_commit_message(self) -> Optional[str]:
        """
        获取最后一次提交消息

        Returns:
            提交消息，如果没有提交则返回None

        Example:
            >>> msg = helper.get_last_commit_message()
            >>> isinstance(msg, str) or msg is None
            True
        """
        if self.repo is None:
            return None

        try:
            commits = list(self.repo.iter_commits(max_count=1))
            if commits:
                return commits[0].message.strip()
            return None
        except Exception as e:
            logger.error(f"获取最后提交消息失败: {e}")
            return None
