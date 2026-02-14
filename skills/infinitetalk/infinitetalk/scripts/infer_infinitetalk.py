#!/usr/bin/env python3
"""
InfiniteTalk - Audio-driven Video Generation

This script wraps the core inference logic for audio-driven video generation.
Based on the original InfiniteTalk project: https://github.com/MeiGen-AI/InfiniteTalk
"""

import argparse
import logging
import os
import sys
import json
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

import random
import torch
import torch.distributed as dist
from PIL import Image
import subprocess

# Set no proxy environment variable
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"

# Import InfiniteTalk modules (assumes running in the InfiniteTalk project directory)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wan
from wan.configs import SIZE_CONFIGS, SUPPORTED_SIZES, WAN_CONFIGS
from wan.utils.utils import str2bool, is_video, split_wav_librosa
from wan.utils.multitalk_utils import save_video_ffmpeg

from kokoro import KPipeline
from transformers import Wav2Vec2FeatureExtractor
from src.audio_analysis.wav2vec2 import Wav2Vec2Model

import librosa
import pyloudnorm as pyln
import numpy as np
from einops import rearrange
import soundfile as sf
import re


def _validate_args(args):
    """Validate command line arguments"""
    # Basic check
    assert args.ckpt_dir is not None, "Please specify the checkpoint directory."
    assert args.task in WAN_CONFIGS, f"Unsupported task: {args.task}"

    # Default sampling steps
    if args.sample_steps is None:
        args.sample_steps = 40

    # Default sample shift based on size
    if args.sample_shift is None:
        if args.size == 'infinitetalk-480':
            args.sample_shift = 7
        elif args.size == 'infinitetalk-720':
            args.sample_shift = 11
        else:
            raise NotImplementedError(f'Not supported size: {args.size}')

    # Seed handling
    args.base_seed = args.base_seed if args.base_seed >= 0 else random.randint(0, 99999999)

    # Size check
    assert args.size in SUPPORTED_SIZES[args.task], \
        f"Unsupported size {args.size} for task {args.task}, supported sizes are: {', '.join(SUPPORTED_SIZES[args.task])}"


def _parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate video from audio and image/video using InfiniteTalk"
    )

    # Input arguments
    parser.add_argument("--input_path", type=str, required=True,
                      help="Input image or video path")
    parser.add_argument("--audio_path", type=str, default=None,
                      help="Audio file path for driving the video")
    parser.add_argument("--text", type=str, default=None,
                      help="Text for TTS generation (alternative to audio_path)")
    parser.add_argument("--output_path", type=str, required=True,
                      help="Output video path")

    # Task and size
    parser.add_argument("--task", type=str, default="infinitetalk-14B",
                      choices=list(WAN_CONFIGS.keys()),
                      help="The task to run")
    parser.add_argument("--size", type=str, default="infinitetalk-480",
                      choices=list(SIZE_CONFIGS.keys()),
                      help="The resolution of the generated video")

    # Frame and mode settings
    parser.add_argument("--frame_num", type=int, default=81,
                      help="Number of frames to generate in one clip (must be 4n+1)")
    parser.add_argument("--max_frame_num", type=int, default=1000,
                      help="Maximum frame length for long video generation")
    parser.add_argument("--mode", type=str, default="streaming",
                      choices=['clip', 'streaming'],
                      help="clip: generate one video chunk, streaming: long video generation")
    parser.add_argument("--motion_frame", type=int, default=9,
                      help="Driven frame length used in long video generation mode")

    # Model paths
    parser.add_argument("--ckpt_dir", type=str,
                      default='./weights/Wan2.1-I2V-14B-480P',
                      help="Path to the Wan checkpoint directory")
    parser.add_argument("--infinitetalk_dir", type=str,
                      default='weights/InfiniteTalk/single/infinitetalk.safetensors',
                      help="Path to the InfiniteTalk checkpoint directory")
    parser.add_argument("--wav2vec_dir", type=str,
                      default='./weights/chinese-wav2vec2-base',
                      help="Path to the wav2vec checkpoint directory")
    parser.add_argument("--dit_path", type=str, default=None,
                      help="Path to the Wan checkpoint directory")

    # Sampling parameters
    parser.add_argument("--sample_steps", type=int, default=None,
                      help="Number of sampling steps")
    parser.add_argument("--sample_shift", type=float, default=None,
                      help="Sampling shift factor for flow matching schedulers")
    parser.add_argument("--sample_text_guide_scale", type=float, default=5.0,
                      help="Classifier free guidance scale for text control")
    parser.add_argument("--sample_audio_guide_scale", type=float, default=4.0,
                      help="Classifier free guidance scale for audio control")

    # Optimization parameters
    parser.add_argument("--offload_model", type=str2bool, default=None,
                      help="Whether to offload model to CPU after each forward")
    parser.add_argument("--ulysses_size", type=int, default=1,
                      help="Size of Ulysses parallelism in DiT")
    parser.add_argument("--ring_size", type=int, default=1,
                      help="Size of ring attention parallelism in DiT")
    parser.add_argument("--t5_fsdp", action="store_true", default=False,
                      help="Whether to use FSDP for T5")
    parser.add_argument("--t5_cpu", action="store_true", default=False,
                      help="Whether to place T5 model on CPU")
    parser.add_argument("--dit_fsdp", action="store_true", default=False,
                      help="Whether to use FSDP for DiT")
    parser.add_argument("--quant", type=str, default=None,
                      help="Quantization type, must be 'int8' or 'fp8'")
    parser.add_argument("--num_persistent_param_in_dit", type=int, default=None,
                      help="Maximum parameters retained in video memory")

    # Advanced features
    parser.add_argument("--lora_dir", type=str, nargs='+', default=None,
                      help="Paths to LoRA checkpoint files")
    parser.add_argument("--lora_scale", type=float, nargs='+', default=[1.2],
                      help="LoRA influence scale")
    parser.add_argument("--use_teacache", action="store_true", default=False,
                      help="Enable teacache for video generation")
    parser.add_argument("--teacache_thresh", type=float, default=0.2,
                      help="Threshold for teacache")
    parser.add_argument("--use_apg", action="store_true", default=False,
                      help="Enable adaptive projected guidance")
    parser.add_argument("--apg_momentum", type=float, default=-0.75,
                      help="Momentum used in APG")
    parser.add_argument("--apg_norm_threshold", type=float, default=55,
                      help="Norm threshold used in APG")
    parser.add_argument("--color_correction_strength", type=float, default=1.0,
                      help="Strength for color correction [0.0 -- 1.0]")
    parser.add_argument("--scene_seg", action="store_true", default=False,
                      help="Enable scene segmentation for input video")

    # TTS parameters
    parser.add_argument("--voice1", type=str, default=None,
                      help="Voice model path for TTS (speaker 1)")
    parser.add_argument("--voice2", type=str, default=None,
                      help="Voice model path for TTS (speaker 2)")

    # Misc
    parser.add_argument("--base_seed", type=int, default=42,
                      help="Random seed for generation")
    parser.add_argument("--save_audio_dir", type=str, default='save_audio',
                      help="Path to save audio embeddings")

    args = parser.parse_args()
    _validate_args(args)
    return args


def custom_init(device, wav2vec):
    """Initialize audio encoder"""
    audio_encoder = Wav2Vec2Model.from_pretrained(wav2vec, local_files_only=True).to(device)
    audio_encoder.feature_extractor._freeze_parameters()
    wav2vec_feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(wav2vec, local_files_only=True)
    return wav2vec_feature_extractor, audio_encoder


def loudness_norm(audio_array, sr=16000, lufs=-23):
    """Normalize audio loudness"""
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(audio_array)
    if abs(loudness) > 100:
        return audio_array
    normalized_audio = pyln.normalize.loudness(audio_array, loudness, lufs)
    return normalized_audio


def audio_prepare_single(audio_path, sample_rate=16000):
    """Prepare single audio file"""
    ext = os.path.splitext(audio_path)[1].lower()
    if ext in ['.mp4', '.mov', '.avi', '.mkv']:
        # Extract audio from video
        raw_audio_path = audio_path.split('/')[-1].split('.')[0] + '.wav'
        ffmpeg_command = [
            "ffmpeg", "-y", "-i", str(audio_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "2",
            str(raw_audio_path)
        ]
        subprocess.run(ffmpeg_command, check=True)
        human_speech_array, sr = librosa.load(raw_audio_path, sr=sample_rate)
        human_speech_array = loudness_norm(human_speech_array, sr)
        os.remove(raw_audio_path)
    else:
        human_speech_array, sr = librosa.load(audio_path, sr=sample_rate)
        human_speech_array = loudness_norm(human_speech_array, sr)
    return human_speech_array


def get_embedding(speech_array, wav2vec_feature_extractor, audio_encoder, sr=16000, device='cpu'):
    """Extract audio embedding using wav2vec"""
    audio_duration = len(speech_array) / sr
    video_length = audio_duration * 25  # Assume 25 fps

    # wav2vec feature extractor
    audio_feature = np.squeeze(
        wav2vec_feature_extractor(speech_array, sampling_rate=sr).input_values
    )
    audio_feature = torch.from_numpy(audio_feature).float().to(device=device)
    audio_feature = audio_feature.unsqueeze(0)

    # audio encoder
    with torch.no_grad():
        embeddings = audio_encoder(audio_feature, seq_len=int(video_length), output_hidden_states=True)

    if len(embeddings) == 0:
        print("Failed to extract audio embedding")
        return None

    audio_emb = torch.stack(embeddings.hidden_states[1:], dim=1).squeeze(0)
    audio_emb = rearrange(audio_emb, "b s d -> s b d")
    audio_emb = audio_emb.cpu().detach()
    return audio_emb


def process_tts_single(text, save_dir, voice1):
    """Process single speaker TTS"""
    s1_sentences = []
    pipeline = KPipeline(lang_code='a', repo_id='weights/Kokoro-82M')
    voice_tensor = torch.load(voice1, weights_only=True)
    generator = pipeline(text, voice=voice_tensor, speed=1, split_pattern=r'\n+')
    audios = []
    for i, (gs, ps, audio) in enumerate(generator):
        audios.append(audio)
    audios = torch.concat(audios, dim=0)
    s1_sentences.append(audios)
    s1_sentences = torch.concat(s1_sentences, dim=0)
    save_path1 = f'{save_dir}/s1.wav'
    sf.write(save_path1, s1_sentences, 24000)
    s1, _ = librosa.load(save_path1, sr=16000)
    return s1, save_path1


def _init_logging(rank):
    """Initialize logging"""
    if rank == 0:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s: %(message)s",
            handlers=[logging.StreamHandler(stream=sys.stdout)]
        )
    else:
        logging.basicConfig(level=logging.ERROR)


def main():
    """Main inference function"""
    args = _parse_args()

    # Initialize distributed training if needed
    if 'RANK' in os.environ and 'WORLD_SIZE' in os.environ:
        dist.init_process_group(backend="nccl")
        rank = int(os.environ["RANK"])
        world_size = int(os.environ['WORLD_SIZE'])
    else:
        rank = 0
        world_size = 1

    _init_logging(rank)
    logger = logging.getLogger(__name__)

    # Set device
    device = f"cuda:{rank}" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    # Create save directory for audio embeddings
    os.makedirs(args.save_audio_dir, exist_ok=True)

    # Initialize audio encoder
    logger.info("Initializing audio encoder...")
    wav2vec_feature_extractor, audio_encoder = custom_init(device, args.wav2vec_dir)

    # Prepare audio
    if args.text is not None:
        # Use TTS to generate audio
        logger.info(f"Generating audio from text: {args.text[:50]}...")
        if args.voice1 is None:
            logger.warning("No voice model specified for TTS. Using default.")
            args.voice1 = "weights/Kokoro-82M/voices/female_01.pt"

        if "(s1)" in args.text or "(s2)" in args.text:
            # Dual speaker dialogue (not fully implemented in this simplified version)
            logger.warning("Dual speaker TTS not fully implemented. Using single speaker.")
            # Strip speaker markers
            text = re.sub(r'\(s\d+\)\s*', '', args.text)

        audio_array, _ = process_tts_single(args.text, args.save_audio_dir, args.voice1)
    else:
        # Use provided audio file
        if args.audio_path is None:
            raise ValueError("Either --audio_path or --text must be provided")
        logger.info(f"Loading audio from: {args.audio_path}")
        audio_array = audio_prepare_single(args.audio_path)

    logger.info(f"Audio loaded: {len(audio_array)} samples ({len(audio_array)/16000:.2f}s)")

    # Extract audio embedding
    logger.info("Extracting audio embedding...")
    audio_emb = get_embedding(audio_array, wav2vec_feature_extractor, audio_encoder, device=device)
    if audio_emb is None:
        logger.error("Failed to extract audio embedding")
        return

    # Save audio embedding
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    emb_save_path = os.path.join(args.save_audio_dir, f"audio_emb_{timestamp}.pt")
    torch.save(audio_emb, emb_save_path)
    logger.info(f"Audio embedding saved to: {emb_save_path}")

    # Prepare input image/video
    logger.info(f"Loading input: {args.input_path}")
    if is_video(args.input_path):
        # For video input, extract first frame
        logger.info("Detected video input, extracting first frame...")
        # This is a simplified version - full implementation would use decord
        # For now, assume we're working with images
        input_image = Image.open(args.input_path)
    else:
        input_image = Image.open(args.input_path)

    # Cache input
    from wan.utils.utils import cache_image
    input_path = cache_image(input_image)
    logger.info(f"Input cached at: {input_path}")

    # Prepare input JSON
    input_data = {
        "input_path": input_path,
        "audio_emb_path": emb_save_path,
        "task": args.task
    }

    input_json_path = os.path.join(args.save_audio_dir, f"input_{timestamp}.json")
    with open(input_json_path, 'w') as f:
        json.dump([input_data], f, indent=2)
    logger.info(f"Input JSON saved to: {input_json_path}")

    # This is a simplified wrapper - the actual generation logic is complex
    # and would require the full InfiniteTalk pipeline implementation
    logger.info("=" * 80)
    logger.info("NOTE: This is a simplified wrapper script.")
    logger.info("The actual video generation requires the full InfiniteTalk pipeline")
    logger.info("which is implemented in the original project.")
    logger.info("=" * 80)
    logger.info("\nFor complete functionality, please use the original scripts:")
    logger.info("  - For CLI: python generate_infinitetalk.py [args]")
    logger.info("  - For Web UI: python app.py")
    logger.info("\nPrepared files:")
    logger.info(f"  - Input: {input_path}")
    logger.info(f"  - Audio embedding: {emb_save_path}")
    logger.info(f"  - Input JSON: {input_json_path}")


if __name__ == "__main__":
    main()
