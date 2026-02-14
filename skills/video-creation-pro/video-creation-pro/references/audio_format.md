# 音频格式规范

## 概览
本规范定义音频信息的标准化格式，确保背景音乐与场景音效在不同场景下的适配效果。

## 音频信息格式（JSON）

```json
{
  "background_music": {
    "file_path": "./bgm.mp3",
    "start_time": 0.0,
    "volume": 0.7
  },
  "sound_effects": [
    {
      "id": 1,
      "file_path": "./transition_effect.mp3",
      "start_time": 3.5,
      "duration": 0.5,
      "volume": 0.9
    },
    {
      "id": 2,
      "file_path": "./click_sound.mp3",
      "start_time": 7.0,
      "duration": 0.2,
      "volume": 0.8
    }
  ]
}
```

## 字段说明

### 背景音乐（background_music）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| file_path | string | 是 | 音频文件路径 |
| start_time | float | 是 | 开始时间（秒） |
| volume | float | 是 | 音量（0.0-1.0，推荐0.6-0.8） |

### 场景音效（sound_effects）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | int | 是 | 音效序号，从1开始 |
| file_path | string | 是 | 音效文件路径 |
| start_time | float | 是 | 开始时间（秒） |
| duration | float | 是 | 持续时间（秒） |
| volume | float | 是 | 音量（0.0-1.0，推荐0.7-0.9） |

## 约束与注意事项

1. **音量平衡**：
   - 背景音乐比场景音效低10-20 dB
   - 背景音乐音量：0.6-0.8
   - 场景音效音量：0.7-0.9
   - 禁止音效盖过背景音乐

2. **时间同步**：
   - 背景音乐需与画面节奏匹配
   - 场景音效需与对应动作同步（误差≤0.1秒）
   - 音效不得超出对应镜头时长

3. **文件格式**：
   - 推荐格式：MP3、WAV
   - 采样率：44100Hz或48000Hz
   - 比特率：128kbps-320kbps

## 示例

### 示例1：科技风音频（智能手环）
```json
{
  "background_music": {
    "file_path": "./tech_electronic_bgm.mp3",
    "start_time": 0.0,
    "volume": 0.7
  },
  "sound_effects": [
    {
      "id": 1,
      "file_path": "./transition_tech_effect.mp3",
      "start_time": 3.5,
      "duration": 0.3,
      "volume": 0.9
    },
    {
      "id": 2,
      "file_path": "./button_click.mp3",
      "start_time": 7.0,
      "duration": 0.2,
      "volume": 0.8
    }
  ]
}
```

### 示例2：治愈风音频（玻尿酸面膜）
```json
{
  "background_music": {
    "file_path": "./gentle_piano_bgm.mp3",
    "start_time": 0.0,
    "volume": 0.6
  },
  "sound_effects": [
    {
      "id": 1,
      "file_path": "./mask_tear_sound.mp3",
      "start_time": 15.0,
      "duration": 0.5,
      "volume": 0.8
    },
    {
      "id": 2,
      "file_path": "./face_gentle_pat.mp3",
      "start_time": 25.0,
      "duration": 0.8,
      "volume": 0.7
    }
  ]
}
```

### 示例3：复古风音频（复古咖啡机）
```json
{
  "background_music": {
    "file_path": "./lazy_jazz_bgm.mp3",
    "start_time": 0.0,
    "volume": 0.7
  },
  "sound_effects": [
    {
      "id": 1,
      "file_path": "./coffee_machine_start.mp3",
      "start_time": 5.0,
      "duration": 1.0,
      "volume": 0.9
    },
    {
      "id": 2,
      "file_path": "./coffee_extract_sound.mp3",
      "start_time": 15.0,
      "duration": 2.0,
      "volume": 0.8
    },
    {
      "id": 3,
      "file_path": "./cup_clink_sound.mp3",
      "start_time": 40.0,
      "duration": 0.3,
      "volume": 0.9
    }
  ]
}
```
