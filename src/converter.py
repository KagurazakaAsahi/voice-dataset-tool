"""Step 2: 音频格式转换 —— MP3/OGG → WAV，统一采样率/声道/位深。"""

import logging
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from .utils import ensure_dir

logger = logging.getLogger("voice-tool.converter")


def convert_file(src_path: Path, dst_path: Path, config: dict) -> dict:
    """转换单个音频文件，返回转换信息。

    使用 soundfile 写 WAV，优先用 pydub 解码 MP3/OGG，
    回退到 librosa 加载 + soundfile 写出。
    """
    audio_config = config["audio"]
    target_sr = audio_config["target_sample_rate"]
    target_channels = audio_config["target_channels"]

    # 加载音频（librosa 可处理 WAV/OGG/MP3 via audioread）
    try:
        y, sr = librosa.load(str(src_path), sr=target_sr, mono=(target_channels == 1))
    except Exception:
        # librosa 失败则尝试 pydub
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(src_path))
        audio = audio.set_frame_rate(target_sr).set_channels(target_channels).set_sample_width(2)
        y = np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
        sr = target_sr

    # 归一化峰值到 -3dB
    peak = np.abs(y).max()
    if peak > 0:
        y = y / peak * 0.7

    duration = len(y) / sr
    ensure_dir(dst_path.parent)
    sf.write(str(dst_path), y, sr, subtype="PCM_16")

    return {
        "src": str(src_path),
        "dst": str(dst_path),
        "duration_sec": round(duration, 2),
        "sample_rate": sr,
    }


def convert_all(df, config: dict) -> list[dict]:
    """批量转换所有音频。

    输出到 output/wavs/<角色>/<原名>.wav
    返回转换结果列表。
    """
    output_root = Path(config["output"]["root"]) / "wavs"
    results = []
    failures = []

    for _, row in df.iterrows():
        src = Path(row["file_path"])
        character = row["character"]
        dst_dir = output_root / character
        dst = dst_dir / f"{src.stem}.wav"

        try:
            info = convert_file(src, dst, config)
            info["character"] = character
            info["text"] = row.get("text", "")
            results.append(info)
        except Exception as e:
            logger.error("转换失败 %s: %s", src, e)
            failures.append({"file": str(src), "error": str(e)})

    logger.info("转换完成：成功 %d，失败 %d", len(results), len(failures))
    if failures:
        logger.warning("失败列表: %s", failures)

    return results
