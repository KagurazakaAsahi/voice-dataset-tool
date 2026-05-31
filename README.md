# Voice Dataset Tool

Galgame 角色语音数据集整理工具 —— 将混合格式原始语音数据转换为 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 训练就绪的标准化数据集。

## 管线概览

```
原始数据（WAV/MP3/OGG + 角色文本元数据）
  │
  ▼  Step 1: Scanner    扫描数据集 → 文件清单
  ▼  Step 2: Converter  格式统一 → 16kHz / mono / WAV
  ▼  Step 3: Cleaner    静音修剪 + VAD 质量筛选
  ▼  Step 4: Organizer  按角色重组 + GPT-SoVITS metadata
  ▼  Step 5: Splitter   train / val / test 分层划分
```

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
git clone https://github.com/KagurazakaAsahi/voice-dataset-tool.git
cd voice-dataset-tool
pip install -r requirements.txt
```

### 配置

编辑 `config.yaml`，设置数据集路径和角色信息：

```yaml
input:
  dataset_root: "D:/galgame_voice_data"   # 原始数据根目录
  metadata_file: "D:/galgame_voice_data/metadata.csv"  # 留空则从目录结构推断
  audio_extensions: [".wav", ".mp3", ".ogg"]

output:
  language: "JP"    # GPT-SoVITS 语言标签：JP / ZH / EN

characters:
  - name: "小鳥"
    alias: ["kotori"]
```

### 运行

```bash
# 完整管线
python -m src.pipeline --config config.yaml

# 只跑某一步
python -m src.pipeline --config config.yaml --step convert
python -m src.pipeline --config config.yaml --step organize

# 详细日志
python -m src.pipeline --config config.yaml --verbose
```

## 元数据格式

### 输入（CSV）

```csv
file_path,character,text
./raw/chara_a/001.wav,小鳥,おはようございます
./raw/chara_a/002.ogg,小鳥,今日もよろしくね
```

或留空 `metadata_file`，从 `raw/<角色名>/<音频文件>` 目录结构自动推断。

### 输出（GPT-SoVITS 格式）

```
wavs/小鳥/小鳥_001.wav|小鳥|JP|おはようございます
wavs/小鳥/小鳥_002.wav|小鳥|JP|今日もよろしくね
```

## 项目结构

```
voice-dataset-tool/
├── README.md
├── requirements.txt
├── config.yaml              # 配置文件
├── src/
│   ├── pipeline.py          # 主流程编排 + CLI 入口
│   ├── scanner.py           # 数据集扫描
│   ├── converter.py         # 音频格式转换
│   ├── cleaner.py           # 静音修剪 + 质量筛选
│   ├── organizer.py         # 角色重组 + metadata 生成
│   ├── splitter.py          # train/val/test 划分
│   └── utils.py             # 工具函数
├── tests/
│   ├── test_scanner.py
│   ├── test_converter.py
│   └── test_organizer.py
└── output/                  # 处理输出（gitignored）
    ├── wavs/<角色>/
    └── metadata/
        ├── train.list
        ├── val.list
        └── test.list
```

## 质量筛选规则

| 检测项 | 阈值 | 处理 |
|--------|------|------|
| 时长过短 | < 0.5s | 拒绝 |
| 时长过长 | > 30s | 拒绝 |
| 静音占比 | > 50% | 拒绝 |
| 被拒音频 | —— | 输出至 `output/rejected.csv` |

## 依赖

| 包 | 用途 |
|----|------|
| librosa | 音频加载、重采样、静音检测 |
| soundfile | WAV 读写 |
| pydub | MP3/OGG 解码回退 |
| pandas | 元数据表格处理 |
| pyyaml | 配置文件解析 |
| numpy | 数值计算 |

## License

MIT
