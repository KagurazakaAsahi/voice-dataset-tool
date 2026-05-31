"""Step 4: 组织输出 —— 按角色重命名 + 生成 GPT-SoVITS metadata。"""

import logging
from pathlib import Path

import pandas as pd

from .utils import ensure_dir

logger = logging.getLogger("voice-tool.organizer")


def organize(df_clean: pd.DataFrame, config: dict) -> pd.DataFrame:
    """按角色重命名音频文件，生成 GPT-SoVITS metadata。

    重命名规则：<角色>_<3位序号>.wav
    按角色分组，按原始文件名排序以保证确定性。

    返回带 output_path 列的 DataFrame。
    """
    output_root = Path(config["output"]["root"])
    wavs_dir = output_root / "wavs"
    language = config["output"].get("language", "JP")

    records = []
    metadata_lines = []

    for character, group in df_clean.groupby("character"):
        char_dir = ensure_dir(wavs_dir / character)
        sorted_group = group.sort_values("file_path")

        for idx, (_, row) in enumerate(sorted_group.iterrows(), start=1):
            new_name = f"{character}_{idx:03d}.wav"
            new_path = char_dir / new_name

            # 重命名（如果源文件和目标不同）
            src = Path(row["file_path"])
            if src != new_path:
                src.rename(new_path)

            relative_path = f"wavs/{character}/{new_name}"
            text = row["text"].replace("|", " ").replace("\n", " ").strip()
            line = f"{relative_path}|{character}|{language}|{text}"
            metadata_lines.append(line)

            records.append({
                "file_path": str(new_path),
                "character": character,
                "text": text,
                "metadata_line": line,
                "duration_sec": row.get("duration_sec", 0),
            })

    # 写入 metadata 文件
    metadata_dir = ensure_dir(output_root / "metadata")
    full_meta_path = metadata_dir / "full.list"
    with open(full_meta_path, "w", encoding="utf-8") as f:
        f.write("\n".join(metadata_lines) + "\n")

    logger.info("组织完成：%d 个角色，%d 条数据 → %s",
                df_clean["character"].nunique(), len(records), full_meta_path)

    return pd.DataFrame(records)
