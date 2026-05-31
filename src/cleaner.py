"""Step 3: 音频清洗 —— 静音修剪 + 质量筛选 + VAD 检测。"""

import logging
from pathlib import Path

import numpy as np
import librosa
import pandas as pd

logger = logging.getLogger("voice-tool.cleaner")


def _compute_silence_ratio(y: np.ndarray, sr: int, threshold_db: float) -> float:
    """计算静音帧占比。"""
    frame_len = int(sr * 0.03)  # 30ms frames
    hop = int(sr * 0.01)        # 10ms hop
    rms = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    silence_frames = np.sum(rms_db < threshold_db)
    return silence_frames / len(rms_db) if len(rms_db) > 0 else 0.0


def _trim_silence(y: np.ndarray, sr: int, threshold_db: float) -> np.ndarray:
    """修剪首尾静音。"""
    intervals = librosa.effects.split(y, top_db=abs(threshold_db))
    if len(intervals) == 0:
        return y
    return np.concatenate([y[start:end] for start, end in intervals])


def clean_file(audio_path: Path, config: dict) -> dict:
    """清洗单个音频文件。

    返回 dict: {path, character, text, duration_sec, status, reason}
    status: "ok" | "rejected"
    """
    vad = config["vad"]
    min_dur = vad["min_duration_sec"]
    max_dur = vad["max_duration_sec"]
    silence_db = vad["silence_threshold_db"]
    max_silence = vad["max_silence_ratio"]

    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    # 静音修剪
    y_trimmed = _trim_silence(y, sr, -abs(silence_db))
    duration = len(y_trimmed) / sr

    # 时长检查
    if duration < min_dur:
        return {"status": "rejected", "reason": f"时长过短 ({duration:.1f}s < {min_dur}s)"}
    if duration > max_dur:
        return {"status": "rejected", "reason": f"时长过长 ({duration:.1f}s > {max_dur}s)"}

    # 静音占比
    silence_ratio = _compute_silence_ratio(y_trimmed, sr, silence_db)
    if silence_ratio > max_silence:
        return {"status": "rejected", "reason": f"静音占比过高 ({silence_ratio:.1%} > {max_silence:.0%})"}

    # 通过 —— 覆盖写入修剪后的音频
    import soundfile as sf
    peak = np.abs(y_trimmed).max()
    if peak > 0:
        y_trimmed = y_trimmed / peak * 0.7
    sf.write(str(audio_path), y_trimmed, sr, subtype="PCM_16")

    return {"status": "ok", "reason": "", "duration_sec": round(duration, 2)}


def clean_all(file_infos: list[dict], df_original, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """批量清洗，返回 (通过的 DataFrame, 被拒的 DataFrame)。"""
    accepted = []
    rejected = []

    for info in file_infos:
        path = Path(info["dst"])
        result = clean_file(path, config)
        result["file_path"] = info["dst"]
        result["character"] = info["character"]
        result["text"] = info["text"]

        if result["status"] == "ok":
            accepted.append(result)
        else:
            rejected.append(result)

    df_ok = pd.DataFrame(accepted)
    df_rej = pd.DataFrame(rejected)

    logger.info("清洗完成：通过 %d，拒绝 %d", len(df_ok), len(df_rej))
    if len(df_rej) > 0:
        logger.info("拒绝原因分布:\n%s", df_rej["reason"].value_counts().to_string())

    return df_ok, df_rej
