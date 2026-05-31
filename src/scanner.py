"""Step 1: 数据集扫描 —— 生成文件清单 DataFrame。"""

import logging
from pathlib import Path

import pandas as pd

from .utils import validate_audio_file

logger = logging.getLogger("voice-tool.scanner")


def _infer_from_directory(root: Path, extensions: list[str]) -> pd.DataFrame:
    """从目录结构推断：root/<角色名>/<音频文件>，文本标记为空。"""
    records = []
    for char_dir in sorted(root.iterdir()):
        if not char_dir.is_dir():
            continue
        character = char_dir.name
        for audio_file in sorted(char_dir.iterdir()):
            if validate_audio_file(audio_file, extensions):
                records.append({
                    "file_path": str(audio_file.resolve()),
                    "character": character,
                    "text": "",
                    "format": audio_file.suffix.lower(),
                })
    logger.info("从目录结构推断：发现 %d 个角色，%d 个音频文件",
                len({r["character"] for r in records}), len(records))
    return pd.DataFrame(records, columns=["file_path", "character", "text", "format"])


def _load_metadata_csv(metadata_path: Path, extensions: list[str]) -> pd.DataFrame:
    """从 CSV 加载元数据，列名为 file_path, character, text。"""
    df = pd.read_csv(metadata_path, encoding="utf-8")
    required = {"file_path", "character", "text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"元数据 CSV 缺少必要列: {missing}")

    df["format"] = df["file_path"].apply(lambda p: Path(p).suffix.lower())
    # 过滤不支持的格式
    before = len(df)
    df = df[df["format"].isin(extensions)]
    logger.info("从 CSV 加载：%d 条记录（过滤掉 %d 条不支持的格式）",
                len(df), before - len(df))
    return df


def scan_dataset(config: dict) -> pd.DataFrame:
    """扫描数据集，返回文件清单 DataFrame。

    DataFrame 列：file_path | character | text | format
    """
    root = Path(config["input"]["dataset_root"])
    extensions = config["input"]["audio_extensions"]
    metadata_file = config["input"].get("metadata_file", "")

    if metadata_file:
        df = _load_metadata_csv(Path(metadata_file), extensions)
    else:
        df = _infer_from_directory(root, extensions)

    if df.empty:
        raise RuntimeError(f"在 {root} 中未发现支持的音频文件（{extensions}）")

    # 应用角色别名映射
    char_map = _build_char_map(config.get("characters", []))
    if char_map:
        df["character"] = df["character"].apply(
            lambda c: char_map.get(c.lower(), c)
        )

    logger.info("扫描完成：共 %d 个音频文件，%d 个角色",
                len(df), df["character"].nunique())
    return df


def _build_char_map(characters: list[dict]) -> dict:
    """构建角色别名 → 标准名映射。"""
    char_map = {}
    for entry in characters:
        name = entry["name"]
        char_map[name.lower()] = name
        for alias in entry.get("alias", []):
            char_map[alias.lower()] = name
    return char_map
