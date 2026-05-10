"""
配置管理模块

管理团队成员配置和系统配置
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
        self.members_file = self.config_dir / "members.json"
        self.system_file = self.config_dir / "system_config.json"

        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 缓存配置
        self._members_cache: Optional[Dict] = None
        self._system_cache: Optional[Dict] = None

        logger.info(f"配置管理器初始化: {config_dir}")

    def load_members(self) -> Dict:
        """
        加载团队成员配置

        Returns:
            成员配置字典

        Example:
            >>> config = ConfigManager("/path/to/config")
            >>> members = config.load_members()
        """
        if self._members_cache is not None:
            return self._members_cache

        if not self.members_file.exists():
            logger.warning(f"成员配置文件不存在: {self.members_file}")
            return {}

        try:
            with open(self.members_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._members_cache = data.get("members", {})
                logger.info(f"已加载 {len(self._members_cache)} 个成员配置")
                return self._members_cache
        except Exception as e:
            logger.error(f"加载成员配置失败: {e}")
            return {}

    def get_member_email(self, member_id: str) -> Optional[str]:
        """
        获取成员邮箱

        Args:
            member_id: 成员ID

        Returns:
            邮箱地址

        Example:
            >>> email = config.get_member_email("HLQ")
        """
        members = self.load_members()
        member = members.get(member_id)
        return member.get("email") if member else None

    def get_admin_email(self) -> Optional[str]:
        """
        获取管理员邮箱

        Returns:
            管理员邮箱

        Example:
            >>> admin_email = config.get_admin_email()
        """
        if not self.members_file.exists():
            return None

        try:
            with open(self.members_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                admin = data.get("admin", {})
                return admin.get("email")
        except Exception as e:
            logger.error(f"获取管理员邮箱失败: {e}")
            return None

    def get_member_info(self, member_id: str) -> Optional[Dict]:
        """
        获取成员完整信息

        Args:
            member_id: 成员ID

        Returns:
            成员信息字典

        Example:
            >>> info = config.get_member_info("HLQ")
        """
        members = self.load_members()
        return members.get(member_id)

    def get_all_active_members(self) -> List[str]:
        """
        获取所有活跃成员ID列表

        Returns:
            成员ID列表

        Example:
            >>> members = config.get_all_active_members()
        """
        members = self.load_members()
        return [
            mid for mid, info in members.items()
            if info.get("active", True)
        ]

    def add_member(self, member_id: str, info: Dict) -> bool:
        """
        添加成员

        Args:
            member_id: 成员ID
            info: 成员信息

        Returns:
            True if 成功

        Example:
            >>> config.add_member("NEW", {"name": "新成员", "email": "new@example.com"})
        """
        members = self.load_members()

        if member_id in members:
            logger.warning(f"成员已存在: {member_id}")
            return False

        members[member_id] = {
            "id": member_id,
            **info,
            "active": info.get("active", True)
        }

        return self._save_members(members)

    def update_member(self, member_id: str, info: Dict) -> bool:
        """
        更新成员信息

        Args:
            member_id: 成员ID
            info: 新的成员信息

        Returns:
            True if 成功

        Example:
            >>> config.update_member("HLQ", {"email": "new@example.com"})
        """
        members = self.load_members()

        if member_id not in members:
            logger.warning(f"成员不存在: {member_id}")
            return False

        members[member_id].update(info)
        return self._save_members(members)

    def _save_members(self, members: Dict) -> bool:
        """保存成员配置"""
        try:
            # 读取完整的配置文件
            if self.members_file.exists():
                with open(self.members_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"version": "1.0", "members": {}, "admin": {}}

            data["members"] = members

            with open(self.members_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 清除缓存
            self._members_cache = None
            logger.info("成员配置已保存")
            return True

        except Exception as e:
            logger.error(f"保存成员配置失败: {e}")
            return False

    def load_system_config(self) -> Dict:
        """
        加载系统配置

        Returns:
            系统配置字典

        Example:
            >>> system_config = config.load_system_config()
        """
        if self._system_cache is not None:
            return self._system_cache

        if not self.system_file.exists():
            logger.warning(f"系统配置文件不存在: {self.system_file}")
            return {}

        try:
            with open(self.system_file, 'r', encoding='utf-8') as f:
                self._system_cache = json.load(f)
                return self._system_cache
        except Exception as e:
            logger.error(f"加载系统配置失败: {e}")
            return {}

    def get_llm_config(self) -> Dict:
        """
        获取LLM配置

        Returns:
            LLM配置

        Example:
            >>> llm_config = config.get_llm_config()
        """
        system_config = self.load_system_config()
        return system_config.get("llm", {
            "model": "zai/glm-5",
            "max_tokens": 2000,
            "temperature": 0.7
        })

    def get_cron_config(self) -> Dict:
        """
        获取定时任务配置

        Returns:
            定时任务配置

        Example:
            >>> cron_config = config.get_cron_config()
        """
        system_config = self.load_system_config()
        return system_config.get("cron", {
            "weekly_time": "0 20 * * 6",
            "timezone": "Asia/Shanghai"
        })

    def initialize_default_config(self) -> bool:
        """
        初始化默认配置文件

        Returns:
            True if 成功

        Example:
            >>> config.initialize_default_config()
        """
        try:
            # 初始化成员配置
            if not self.members_file.exists():
                default_members = {
                    "version": "1.0",
                    "members": {
                        "HLQ": {
                            "id": "HLQ",
                            "name": "黄良强",
                            "email": "hlqiang@wooduan.com",
                            "active": True
                        }
                    },
                    "admin": {
                        "name": "Kai",
                        "email": "kai@wooduan.com"
                    }
                }

                with open(self.members_file, 'w', encoding='utf-8') as f:
                    json.dump(default_members, f, ensure_ascii=False, indent=2)

                logger.info("已创建默认成员配置文件")

            # 初始化系统配置
            if not self.system_file.exists():
                default_system = {
                    "version": "1.0",
                    "llm": {
                        "model": "zai/glm-5",
                        "max_tokens": 2000,
                        "temperature": 0.7
                    },
                    "cron": {
                        "weekly_time": "0 20 * * 6",
                        "timezone": "Asia/Shanghai"
                    },
                    "email": {
                        "enabled": True,
                        "retry_times": 3
                    }
                }

                with open(self.system_file, 'w', encoding='utf-8') as f:
                    json.dump(default_system, f, ensure_ascii=False, indent=2)

                logger.info("已创建默认系统配置文件")

            return True

        except Exception as e:
            logger.error(f"初始化默认配置失败: {e}")
            return False
