"""公共工具：日志、文件校验、配置加载。"""

import logging
import sys
import yaml
from pathlib import Path
from typing import Any, Dict


def setup_logging(verbose: bool = False) -> logging.Logger:
    """配置日志，返回 root logger。"""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stdout)
    return logging.getLogger("voice-tool")


def load_config(path: str) -> Dict[str, Any]:
    """加载 YAML 配置文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: Path) -> Path:
    """确保目录存在。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_audio_file(path: Path, extensions: list[str]) -> bool:
    """检查文件是否为支持的音频格式且存在。"""
    return path.exists() and path.suffix.lower() in extensions
