"""Scanner 模块测试。"""

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from src.scanner import scan_dataset


def _make_test_audio(path: Path, duration: float = 1.0, sr: int = 16000):
    """生成测试用正弦波 WAV。"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(str(path), y, sr)


def test_scan_from_directory():
    """从目录结构推断角色和文件。"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "raw"
        (root / "chara_a").mkdir(parents=True)
        (root / "chara_b").mkdir(parents=True)

        _make_test_audio(root / "chara_a" / "001.wav")
        _make_test_audio(root / "chara_a" / "002.wav")
        _make_test_audio(root / "chara_b" / "hello.wav")

        config = {
            "input": {
                "dataset_root": str(root),
                "audio_extensions": [".wav"],
                "metadata_file": "",
            },
            "characters": [],
        }

        df = scan_dataset(config)
        assert len(df) == 3
        assert set(df["character"]) == {"chara_a", "chara_b"}
        assert df["text"].tolist() == ["", "", ""]
        print("[PASS] test_scan_from_directory")


def test_scan_from_csv():
    """从 CSV 元数据加载。"""
    import csv
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "raw"
        (root / "chara_a").mkdir(parents=True)
        _make_test_audio(root / "chara_a" / "001.wav")
        _make_test_audio(root / "chara_a" / "002.wav")

        meta_path = Path(tmp) / "meta.csv"
        with open(meta_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["file_path", "character", "text"])
            w.writerow([str(root / "chara_a" / "001.wav"), "小鳥", "おはよう"])
            w.writerow([str(root / "chara_a" / "002.wav"), "小鳥", "こんにちは"])

        config = {
            "input": {
                "dataset_root": str(root),
                "audio_extensions": [".wav"],
                "metadata_file": str(meta_path),
            },
            "characters": [],
        }

        df = scan_dataset(config)
        assert len(df) == 2
        assert df["character"].iloc[0] == "小鳥"
        assert df["text"].iloc[0] == "おはよう"
        print("[PASS] test_scan_from_csv")


if __name__ == "__main__":
    test_scan_from_directory()
    test_scan_from_csv()
