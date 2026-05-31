"""Converter 模块测试。"""

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from src.converter import convert_file


def test_convert_wav():
    """测试 WAV 转换：重采样 + mono + 16bit。"""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "input.wav"
        # 生成 44.1kHz stereo 测试文件
        sr_orig = 44100
        t = np.linspace(0, 2.0, int(sr_orig * 2.0), endpoint=False)
        y_stereo = np.column_stack([
            0.5 * np.sin(2 * np.pi * 440 * t),
            0.3 * np.sin(2 * np.pi * 880 * t),
        ])
        sf.write(str(src), y_stereo, sr_orig)

        dst = Path(tmp) / "output.wav"
        config = {
            "audio": {
                "target_sample_rate": 16000,
                "target_channels": 1,
            }
        }

        result = convert_file(src, dst, config)
        assert result["sample_rate"] == 16000
        assert dst.exists()

        # 验证输出格式
        info = sf.info(str(dst))
        assert info.samplerate == 16000
        assert info.channels == 1
        # 检查时长合理（±0.1s）
        assert abs(result["duration_sec"] - 2.0) < 0.1
        print("[PASS] test_convert_wav")


if __name__ == "__main__":
    test_convert_wav()
