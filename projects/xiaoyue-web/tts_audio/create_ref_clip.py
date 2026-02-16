#!/usr/bin/env python3
"""Create a 5-second reference audio clip from ref_audio.wav"""

from pydub import AudioSegment
import os

# 使用 ref_audio.wav 裁剪一个 5 秒的片段
audio = AudioSegment.from_wav('ref_audio.wav')
# 裁剪前 5 秒
clip = audio[:5000]  # 5 seconds in milliseconds
clip.export('ref_clip_5s.wav', format='wav')
print('Created ref_clip_5s.wav (5 seconds)')
print(f'File size: {os.path.getsize("ref_clip_5s.wav")} bytes')
