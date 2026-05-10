"""
Git操作封装单元测试
"""

import pytest
import os
import tempfile
import shutil
from src.core.git_helper import GitHelper


class TestGitHelper:
    """测试 GitHelper 类"""

    @pytest.fixture
    def temp_repo(self):
        """创建临时Git仓库"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_init_repo(self, temp_repo):
        """测试初始化仓库"""
        helper = GitHelper(temp_repo)
        result = helper.init_repo()

        assert result is True
        assert helper.repo is not None
        assert os.path.exists(os.path.join(temp_repo, ".git"))

    def test_init_repo_already_exists(self, temp_repo):
        """测试初始化已存在的仓库"""
        helper1 = GitHelper(temp_repo)
        helper1.init_repo()

        helper2 = GitHelper(temp_repo)
        result = helper2.init_repo()

        assert result is True  # 应该跳过初始化

    def test_commit_all(self, temp_repo):
        """测试提交所有文件"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        # 创建测试文件
        test_file = os.path.join(temp_repo, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        # 提交
        result = helper.commit("Initial commit")
        assert result is True

        # 检查提交历史
        history = helper.get_commit_history(1)
        assert len(history) == 1
        assert "Initial commit" in history[0]["message"]

    def test_commit_specific_files(self, temp_repo):
        """测试提交指定文件"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        # 创建测试文件
        test_file = os.path.join(temp_repo, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        # 提交指定文件
        result = helper.commit("Add test file", files=["test.txt"])
        assert result is True

    def test_commit_no_changes(self, temp_repo):
        """测试没有更改时提交"""
        helper = GitHelper(temp_repo)
        helper.init_repo()
        helper.commit("Initial commit")

        # 再次提交（没有更改）
        result = helper.commit("Empty commit")
        assert result is True  # 应该跳过

    def test_commit_with_retry_success(self, temp_repo):
        """测试带重试的提交（成功）"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        # 创建文件
        test_file = os.path.join(temp_repo, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        result = helper.commit_with_retry("Test commit", max_retries=3)
        assert result is True

    def test_get_commit_history(self, temp_repo):
        """测试获取提交历史"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        # 创建多个提交
        for i in range(3):
            test_file = os.path.join(temp_repo, f"test{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"content {i}")
            helper.commit(f"Commit {i}")

        # 获取历史
        history = helper.get_commit_history(10)
        assert len(history) == 3

    def test_get_commit_history_limit(self, temp_repo):
        """测试限制提交历史数量"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        # 创建5个提交
        for i in range(5):
            test_file = os.path.join(temp_repo, f"test{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"content {i}")
            helper.commit(f"Commit {i}")

        # 获取历史（限制2个）
        history = helper.get_commit_history(2)
        assert len(history) == 2

    def test_get_current_branch(self, temp_repo):
        """测试获取当前分支"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        branch = helper.get_current_branch()
        # Git默认分支可能是main或master
        assert branch in ["main", "master"]

    def test_get_status(self, temp_repo):
        """测试获取仓库状态"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        status = helper.get_status()
        assert "branch" in status
        assert "modified" in status
        assert "untracked" in status
        assert "staged" in status

    def test_get_status_untracked_files(self, temp_repo):
        """测试获取未跟踪文件"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        # 创建未跟踪文件
        test_file = os.path.join(temp_repo, "untracked.txt")
        with open(test_file, "w") as f:
            f.write("untracked")

        status = helper.get_status()
        assert "untracked.txt" in status["untracked"]

    def test_get_last_commit_message(self, temp_repo):
        """测试获取最后提交消息"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        # 创建提交
        test_file = os.path.join(temp_repo, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        helper.commit("Test message")

        message = helper.get_last_commit_message()
        assert message == "Test message"

    def test_get_last_commit_message_no_commits(self, temp_repo):
        """测试没有提交时获取消息"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        message = helper.get_last_commit_message()
        assert message is None

    def test_add_remote(self, temp_repo):
        """测试添加远程仓库"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        result = helper.add_remote("origin", "https://github.com/test/repo.git")
        assert result is True

    def test_push_no_remote(self, temp_repo):
        """测试推送到不存在的远程仓库"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        result = helper.push("nonexistent", "main")
        assert result is False

    def test_invalid_repo_path(self):
        """测试无效的仓库路径"""
        with pytest.raises(ValueError):
            GitHelper("/nonexistent/path")

    def test_commit_before_init(self, temp_repo):
        """测试未初始化时提交"""
        helper = GitHelper(temp_repo)

        result = helper.commit("Test")
        assert result is False


class TestGitHelperEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def temp_repo(self):
        """创建临时Git仓库"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_commit_nonexistent_file(self, temp_repo):
        """测试提交不存在的文件"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        result = helper.commit("Add file", files=["nonexistent.txt"])
        assert result is True  # 会跳过不存在的文件

    def test_multiple_commits_same_file(self, temp_repo):
        """测试多次提交同一文件"""
        helper = GitHelper(temp_repo)
        helper.init_repo()

        test_file = os.path.join(temp_repo, "test.txt")

        # 第一次提交
        with open(test_file, "w") as f:
            f.write("version 1")
        helper.commit("Version 1")

        # 第二次提交
        with open(test_file, "w") as f:
            f.write("version 2")
        helper.commit("Version 2")

        history = helper.get_commit_history(10)
        assert len(history) == 2
