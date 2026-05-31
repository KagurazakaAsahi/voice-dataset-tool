# Voice Dataset Tool

Galgame 角色语音数据集整理工具。将混合格式（WAV/MP3/OGG）原始语音数据转换为 GPT-SoVITS 训练就绪的标准化数据集。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 编辑配置
# 修改 config.yaml 中的 input.dataset_root 和 input.metadata_file

# 运行完整管线
python -m src.pipeline --config config.yaml

# 只跑某一步
python -m src.pipeline --config config.yaml --step convert
python -m src.pipeline --config config.yaml --step organize
```

## 管线步骤

| 步骤 | 模块 | 输入 | 输出 |
|------|------|------|------|
| scan | `scanner.py` | 原始音频目录 | 文件清单 DataFrame |
| convert | `converter.py` | 文件清单 | 标准化 WAV（16kHz/mono） |
| clean | `cleaner.py` | 标准化 WAV | 过滤后文件 + rejected.csv |
| organize | `organizer.py` | 清洗后文件 | 角色目录 + GPT-SoVITS metadata |
| split | `splitter.py` | metadata | train/val/test.list |

## 元数据输入格式

支持 CSV 或从目录结构推断。CSV 格式：

```csv
file_path,character,text
./raw/chara_a/001.wav,小鳥,おはようございます
```

## GPT-SoVITS 输出格式

```
output/wavs/<角色名>/<角色名>_<序号>.wav|<角色名>|JP|<文本>
```

## 依赖

- Python 3.10+
- librosa, soundfile, pydub — 音频处理
- webrtcvad — 语音活动检测
- pandas — 元数据处理
- pyyaml — 配置解析
