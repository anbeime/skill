#!/usr/bin/env python3
"""
Voice Cloning Script

This script extracts voice characteristics from reference audio
and saves them for use in TTS synthesis.
"""

import argparse
import logging
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import torch
import torchaudio
import librosa
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Clone voice characteristics from reference audio"
    )

    # Input arguments
    parser.add_argument("--reference_audio", type=str, required=True,
                      help="Path to reference audio file")
    parser.add_argument("--voice_name", type=str, required=True,
                      help="Name for the cloned voice")

    # Model selection
    parser.add_argument("--model_name", type=str, default="fish-speech-1.5",
                      choices=["fish-speech-1.5", "chattts", "cosyvoice"],
                      help="TTS model to use")

    # Output arguments
    parser.add_argument("--output_dir", type=str, default="./voices",
                      help="Directory to save voice model")

    # Audio processing
    parser.add_argument("--target_sample_rate", type=int, default=24000,
                      help="Target sample rate")
    parser.add_argument("--segment_duration", type=float, default=10.0,
                      help="Duration of audio segment to use (seconds)")

    # Device
    parser.add_argument("--device", type=str, default=None,
                      help="Device to use (cuda, cpu)")

    return parser.parse_args()


class VoiceCloner:
    """Voice Cloning class"""

    def __init__(self, model_name, device=None):
        """
        Initialize Voice Cloner

        Args:
            model_name: Name of the TTS model
            device: Device to use (cuda, cpu)
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.encoder = None
        self.encoder_loaded = False

        logger.info(f"Initializing Voice Cloner with model: {model_name}")
        logger.info(f"Device: {self.device}")

    def load_audio(self, audio_path, target_sample_rate=24000):
        """
        Load and preprocess audio file

        Args:
            audio_path: Path to audio file
            target_sample_rate: Target sample rate

        Returns:
            Audio data (numpy array)
        """
        logger.info(f"Loading audio from: {audio_path}")

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load audio using librosa
        audio, sr = librosa.load(audio_path, sr=target_sample_rate, mono=True)

        # Validate audio
        if len(audio) == 0:
            raise ValueError("Audio file is empty")

        logger.info(f"Audio loaded: {len(audio) / sr:.2f} seconds, {sr} Hz")

        return audio

    def extract_segment(self, audio, segment_duration, sample_rate):
        """
        Extract a segment of audio for voice cloning

        Args:
            audio: Full audio array
            segment_duration: Duration of segment to extract (seconds)
            sample_rate: Sample rate

        Returns:
            Audio segment
        """
        # Calculate segment length in samples
        segment_length = int(segment_duration * sample_rate)

        # Extract segment (start from middle)
        start_idx = max(0, (len(audio) - segment_length) // 2)
        end_idx = min(len(audio), start_idx + segment_length)

        segment = audio[start_idx:end_idx]

        logger.info(f"Extracted segment: {len(segment) / sample_rate:.2f} seconds")

        return segment

    def extract_voice_embedding(self, audio, model_name):
        """
        Extract voice embedding from audio

        Args:
            audio: Audio data
            model_name: Name of the TTS model

        Returns:
            Voice embedding (numpy array)
        """
        logger.info("Extracting voice embedding...")

        # Placeholder implementation
        # In production, this would:
        # 1. Load the voice encoder model
        # 2. Extract acoustic features (MFCC, mel-spectrogram, etc.)
        # 3. Use the encoder to generate voice embedding

        logger.warning("=" * 80)
        logger.warning("This is a placeholder implementation!")
        logger.warning("In production, this would:")
        logger.warning("  1. Load the voice encoder from the TTS model")
        logger.warning("  2. Extract acoustic features from the audio")
        logger.warning("  3. Generate voice embedding tensor")
        logger.warning("=" * 80)

        # Generate dummy embedding for demonstration
        # In production, this would be the actual embedding from the model
        embedding_dim = 256  # Typical embedding dimension
        embedding = np.random.randn(embedding_dim).astype(np.float32)

        logger.info(f"Voice embedding extracted: dimension {embedding_dim}")

        return embedding

    def save_voice_model(self, voice_name, embedding, reference_audio,
                        output_dir, model_name):
        """
        Save voice model to disk

        Args:
            voice_name: Name of the voice
            embedding: Voice embedding
            reference_audio: Reference audio segment
            output_dir: Output directory
            model_name: TTS model name
        """
        # Create output directory
        model_dir = os.path.join(output_dir, model_name, voice_name)
        os.makedirs(model_dir, exist_ok=True)

        # Save embedding
        embedding_path = os.path.join(model_dir, "speaker_embedding.pt")
        torch.save(torch.from_numpy(embedding), embedding_path)

        # Save reference audio
        audio_path = os.path.join(model_dir, "reference.wav")
        torchaudio.save(audio_path,
                       torch.from_numpy(reference_audio).unsqueeze(0),
                       24000)

        # Save config
        config = {
            "voice_name": voice_name,
            "model_name": model_name,
            "embedding_dim": len(embedding),
            "created_at": str(Path(audio_path).stat().st_mtime),
        }

        config_path = os.path.join(model_dir, "config.json")
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Voice model saved to: {model_dir}")
        logger.info(f"  - Embedding: {embedding_path}")
        logger.info(f"  - Reference audio: {audio_path}")
        logger.info(f"  - Config: {config_path}")

        return model_dir

    def clone_voice(self, reference_audio, voice_name, output_dir,
                   segment_duration=10.0, sample_rate=24000):
        """
        Complete voice cloning pipeline

        Args:
            reference_audio: Path to reference audio file
            voice_name: Name for the cloned voice
            output_dir: Output directory
            segment_duration: Duration of audio segment to use
            sample_rate: Target sample rate

        Returns:
            Path to saved voice model
        """
        # Load audio
        audio = self.load_audio(reference_audio, sample_rate)

        # Validate audio duration
        audio_duration = len(audio) / sample_rate
        if audio_duration < 3.0:
            logger.warning(f"Audio duration ({audio_duration:.2f}s) is too short. "
                          "Recommended: 5-15 seconds")
        elif audio_duration > 30.0:
            logger.warning(f"Audio duration ({audio_duration:.2f}s) is too long. "
                          "Will extract a segment")

        # Extract segment
        segment = self.extract_segment(audio, segment_duration, sample_rate)

        # Extract voice embedding
        embedding = self.extract_voice_embedding(segment, self.model_name)

        # Save voice model
        model_dir = self.save_voice_model(
            voice_name, embedding, segment, output_dir, self.model_name
        )

        logger.info(f"Voice cloning completed successfully!")
        return model_dir


def validate_reference_audio(audio_path):
    """
    Validate reference audio file

    Args:
        audio_path: Path to audio file

    Returns:
        True if valid, False otherwise
    """
    logger.info(f"Validating reference audio: {audio_path}")

    # Check file exists
    if not os.path.exists(audio_path):
        logger.error("File not found")
        return False

    # Check file extension
    valid_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in valid_extensions:
        logger.warning(f"File extension '{ext}' may not be supported")

    # Load and check audio
    try:
        audio, sr = librosa.load(audio_path, sr=None, mono=True)

        # Check duration
        duration = len(audio) / sr
        if duration < 3.0:
            logger.warning(f"Audio duration ({duration:.2f}s) is too short. "
                          "Recommended: 5-15 seconds")
        elif duration > 30.0:
            logger.warning(f"Audio duration ({duration:.2f}s) is too long. "
                          "Will extract a segment")
        else:
            logger.info(f"Audio duration: {duration:.2f}s ✓")

        # Check sample rate
        logger.info(f"Sample rate: {sr} Hz")

        # Check audio quality (basic check)
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.01:
            logger.warning("Audio volume is very low")
        elif rms > 0.95:
            logger.warning("Audio may be clipped")
        else:
            logger.info(f"Audio quality: OK (RMS: {rms:.3f})")

        return True

    except Exception as e:
        logger.error(f"Failed to validate audio: {e}")
        return False


def main():
    """Main function"""
    args = parse_args()

    # Validate reference audio
    if not validate_reference_audio(args.reference_audio):
        logger.error("Reference audio validation failed")
        return 1

    # Initialize voice cloner
    cloner = VoiceCloner(
        model_name=args.model_name,
        device=args.device
    )

    # Clone voice
    try:
        model_dir = cloner.clone_voice(
            reference_audio=args.reference_audio,
            voice_name=args.voice_name,
            output_dir=args.output_dir,
            segment_duration=args.segment_duration,
            sample_rate=args.target_sample_rate
        )

        logger.info("=" * 80)
        logger.info("Voice cloning completed!")
        logger.info(f"Voice model saved to: {model_dir}")
        logger.info(f"You can now use this voice with:")
        logger.info(f"  python scripts/tts_generate.py \\")
        logger.info(f"    --text \"Your text here\" \\")
        logger.info(f"    --voice {args.voice_name} \\")
        logger.info(f"    --voice_path {model_dir}")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
