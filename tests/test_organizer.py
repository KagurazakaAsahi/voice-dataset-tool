"""Organizer 模块测试。"""

import tempfile
from pathlib import Path

import pandas as pd

from src.organizer import organize


def test_organize_gpt_sovits_format():
    """验证输出的 metadata 行格式符合 GPT-SoVITS 要求。"""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = Path(tmp)
        (output_root / "wavs" / "小鳥").mkdir(parents=True)

        # 创建测试 WAV
        import numpy as np
        import soundfile as sf
        for i in range(3):
            y = np.random.randn(16000).astype(np.float32) * 0.1
            sf.write(str(output_root / "wavs" / "小鳥" / f"test_{i}.wav"), y, 16000)

        df_clean = pd.DataFrame({
            "file_path": [str(output_root / "wavs" / "小鳥" / f"test_{i}.wav") for i in range(3)],
            "character": ["小鳥"] * 3,
            "text": ["おはよう", "こんにちは", "おやすみ|なさい"],
            "duration_sec": [1.0, 1.0, 1.0],
        })

        config = {
            "output": {"root": str(output_root), "language": "JP"},
        }

        df = organize(df_clean, config)

        assert len(df) == 3
        # 验证 GPT-SoVITS 格式: path|speaker|lang|text
        line = df["metadata_line"].iloc[0]
        parts = line.split("|")
        assert len(parts) == 4, f"格式应为 path|speaker|lang|text，实际: {line}"
        assert parts[1] == "小鳥"
        assert parts[2] == "JP"
        assert "|" not in parts[3], "文本中的 | 应已被替换"

        # 验证 full.list 文件
        full_list = output_root / "metadata" / "full.list"
        assert full_list.exists()
        lines = full_list.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3

        print("[PASS] test_organize_gpt_sovits_format")
        print(f"   Sample line: {lines[0]}")


if __name__ == "__main__":
    test_organize_gpt_sovits_format()
