#!/usr/bin/env python3
"""
周报与日报自动化系统

自动化的团队日报收集、周报生成和分发系统。
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="weekly-report-system",
    version="1.0.0",
    author="Claw",
    author_email="claw@openclaw.ai",
    description="自动化的团队日报收集、周报生成和分发系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openclaw/weekly-report-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "collect-daily=scripts.collect_daily:main",
            "generate-weekly=scripts.generate_weekly:main",
            "setup-cron=scripts.setup_cron:main",
        ],
    },
)
