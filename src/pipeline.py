"""主流程编排器 —— 串联 scanner → converter → cleaner → organizer → splitter。"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from . import utils
from .scanner import scan_dataset
from .converter import convert_all
from .cleaner import clean_all
from .organizer import organize
from .splitter import split_dataset

logger = logging.getLogger("voice-tool.pipeline")

STEPS = ["scan", "convert", "clean", "organize", "split"]


def run_pipeline(config_path: str, stop_at: str = None) -> dict:
    """执行完整管线。

    Args:
        config_path: YAML 配置文件路径
        stop_at: 可选的步骤名，执行到此步骤后停止

    Returns:
        每步产出的字典
    """
    config = utils.load_config(config_path)
    utils.ensure_dir(Path(config["output"]["root"]))

    results = {}

    # Step 1: Scan
    logger.info("=" * 50)
    logger.info("Step 1/5: 扫描数据集")
    logger.info("=" * 50)
    df_scan = scan_dataset(config)
    results["scan"] = df_scan
    if stop_at == "scan":
        return results

    # Step 2: Convert
    logger.info("=" * 50)
    logger.info("Step 2/5: 音频格式转换")
    logger.info("=" * 50)
    converted = convert_all(df_scan, config)
    df_conv = pd.DataFrame(converted)
    results["convert"] = df_conv
    if stop_at == "convert":
        return results

    # Step 3: Clean
    logger.info("=" * 50)
    logger.info("Step 3/5: 音频清洗与质量筛选")
    logger.info("=" * 50)
    df_clean, df_rejected = clean_all(converted, df_scan, config)
    results["clean"] = df_clean
    results["rejected"] = df_rejected

    # 保存 rejected 清单
    if len(df_rejected) > 0:
        rejected_path = Path(config["output"]["root"]) / "rejected.csv"
        df_rejected.to_csv(rejected_path, index=False, encoding="utf-8-sig")
        logger.info("拒绝清单已保存至 %s", rejected_path)

    if stop_at == "clean":
        return results

    # Step 4: Organize
    logger.info("=" * 50)
    logger.info("Step 4/5: 组织输出与 metadata 生成")
    logger.info("=" * 50)
    df_organized = organize(df_clean, config)
    results["organize"] = df_organized
    if stop_at == "organize":
        return results

    # Step 5: Split
    logger.info("=" * 50)
    logger.info("Step 5/5: 数据集划分")
    logger.info("=" * 50)
    splits = split_dataset(df_organized, config)
    results["split"] = splits

    logger.info("=" * 50)
    logger.info("管线完成！输出目录：%s", config["output"]["root"])
    logger.info("=" * 50)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Voice Dataset Tool — Galgame 语音数据预处理管线"
    )
    parser.add_argument("--config", "-c", default="config.yaml", help="YAML 配置文件路径")
    parser.add_argument("--step", "-s", choices=STEPS, help="只执行到指定步骤后停止")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    utils.setup_logging(args.verbose)

    try:
        run_pipeline(args.config, stop_at=args.step)
    except Exception as e:
        logger.error("管线中断: %s", e)
        raise


if __name__ == "__main__":
    main()
