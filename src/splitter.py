"""Step 5: 数据集划分 —— 按角色分层 split 为 train/val/test。"""

import logging
from pathlib import Path

import pandas as pd

from .utils import ensure_dir

logger = logging.getLogger("voice-tool.splitter")


def split_dataset(df_organized: pd.DataFrame, config: dict) -> dict[str, Path]:
    """按角色分层划分数据集，输出 train.list / val.list / test.list。

    使用 config.split 中的比例和 seed。
    返回 {"train": path, "val": path, "test": path}。
    """
    split_config = config["split"]
    train_r = split_config["train_ratio"]
    val_r = split_config["val_ratio"]
    test_r = split_config["test_ratio"]
    seed = split_config.get("seed", 42)

    metadata_dir = Path(config["output"]["root"]) / "metadata"

    # 按角色分组后分别 split，保证不会跨集合泄漏
    train_lines = []
    val_lines = []
    test_lines = []

    for character, group in df_organized.groupby("character"):
        n = len(group)
        shuffled = group.sample(frac=1, random_state=seed)

        n_train = max(1, int(n * train_r))
        n_val = max(1, int(n * val_r))

        train = shuffled.iloc[:n_train]
        val = shuffled.iloc[n_train:n_train + n_val]
        test = shuffled.iloc[n_train + n_val:]

        train_lines.extend(train["metadata_line"].tolist())
        val_lines.extend(val["metadata_line"].tolist())
        test_lines.extend(test["metadata_line"].tolist())

    # 写入
    splits = {}
    for name, lines in [("train", train_lines), ("val", val_lines), ("test", test_lines)]:
        path = metadata_dir / f"{name}.list"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        splits[name] = path

    total = len(df_organized)
    logger.info("划分完成：train=%d (%.0f%%) val=%d (%.0f%%) test=%d (%.0f%%)",
                len(train_lines), 100 * len(train_lines) / total if total else 0,
                len(val_lines), 100 * len(val_lines) / total if total else 0,
                len(test_lines), 100 * len(test_lines) / total if total else 0)

    return splits
