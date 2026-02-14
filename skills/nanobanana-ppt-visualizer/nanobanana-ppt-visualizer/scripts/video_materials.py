#!/usr/bin/env python3
"""
Video Materials Manager - Manage video materials for PPT presentation.

This module collects and organizes video materials (preview videos,
transition videos) for video composition.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# Constants
# =============================================================================

DEFAULT_OUTPUT_DIR = "outputs"


# =============================================================================
# Video Materials Manager
# =============================================================================

class VideoMaterialsManager:
    """Manager for PPT video materials."""

    def __init__(
        self,
        base_dir: Optional[str] = None,
        auto_collect: bool = True
    ) -> None:
        """
        Initialize video materials manager.

        Args:
            base_dir: Base directory containing materials.
            auto_collect: Whether to automatically collect materials on init.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.videos: Dict[str, List[str]] = {
            'preview': [],
            'transitions': [],
            'images': []
        }

        if auto_collect:
            self.collect_materials()

    # -------------------------------------------------------------------------
    # Materials Collection
    # -------------------------------------------------------------------------

    def collect_materials(self) -> None:
        """Collect all video materials from base directory."""
        print(f"Collecting materials from: {self.base_dir}")

        # Collect preview videos
        preview_pattern = "preview.mp4"
        for preview_file in self.base_dir.glob("*/**/preview.mp4"):
            self.videos['preview'].append(str(preview_file))
            print(f"  Found preview: {preview_file}")

        # Collect transition videos
        for transition_file in self.base_dir.glob("*/**/transition_*.mp4"):
            self.videos['transitions'].append(str(transition_file))
            print(f"  Found transition: {transition_file}")

        # Collect images
        for image_file in self.base_dir.glob("*/**/slide-*.png"):
            self.videos['images'].append(str(image_file))
            print(f"  Found image: {image_file}")

        # Sort transitions by slide number
        self.videos['transitions'].sort()
        self.videos['images'].sort()

        print(f"\nCollected:")
        print(f"  Preview videos: {len(self.videos['preview'])}")
        print(f"  Transition videos: {len(self.videos['transitions'])}")
        print(f"  Images: {len(self.videos['images'])}")

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate_materials(self) -> Dict[str, Any]:
        """
        Validate collected materials.

        Returns:
            Validation result dict with status and errors.
        """
        errors = []

        # Check if we have images
        if not self.videos['images']:
            errors.append("No images found")

        # Check preview video
        if not self.videos['preview']:
            errors.append("No preview video found")

        # Check transition videos
        if not self.videos['transitions']:
            errors.append("No transition videos found")

        # Validate image count matches transition count
        if self.videos['images'] and self.videos['transitions']:
            expected_transitions = len(self.videos['images']) - 1
            actual_transitions = len(self.videos['transitions'])
            if actual_transitions < expected_transitions:
                errors.append(
                    f"Expected {expected_transitions} transition videos, "
                    f"found {actual_transitions}"
                )

        result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'preview': self.videos['preview'][0] if self.videos['preview'] else None,
            'transitions': self.videos['transitions'],
            'images': self.videos['images']
        }

        return result

    # -------------------------------------------------------------------------
    # Material Organization
    # -------------------------------------------------------------------------

    def organize_materials(
        self,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Organize materials into a structured format for composition.

        Args:
            output_dir: Output directory for organized materials.

        Returns:
            Organized materials dict.
        """
        validation = self.validate_materials()

        if not validation['valid']:
            print("⚠ Materials validation failed:")
            for error in validation['errors']:
                print(f"  - {error}")
            return {
                'success': False,
                'error': 'Validation failed',
                'details': validation['errors']
            }

        # Organize materials
        organized = {
            'preview': validation['preview'],
            'transitions': validation['transitions'],
            'images': validation['images'],
            'sequence': self._build_sequence(validation)
        }

        # Save organized materials info
        output_path = Path(output_dir) / "materials_info.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(organized, f, indent=2, ensure_ascii=False)

        print(f"✓ Materials info saved: {output_path}")

        return {
            'success': True,
            'materials': organized
        }

    def _build_sequence(self, validation: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build playback sequence from materials.

        Args:
            validation: Validation result.

        Returns:
            List of sequence items.
        """
        sequence = []

        # Start with preview video
        if validation['preview']:
            sequence.append({
                'type': 'video',
                'path': validation['preview'],
                'index': 0
            })

        # Add transitions and images
        for idx, image_path in enumerate(validation['images'], 1):
            sequence.append({
                'type': 'image',
                'path': image_path,
                'index': idx
            })

            # Add transition after each image (except last)
            if idx < len(validation['images']):
                # Find transition for this slide
                transition_pattern = f"transition_{idx:02d}_to_{idx+1:02d}"
                transition = None
                for t in validation['transitions']:
                    if transition_pattern in t:
                        transition = t
                        break

                if transition:
                    sequence.append({
                        'type': 'video',
                        'path': transition,
                        'index': idx
                    })

        return sequence


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Manage PPT video materials'
    )
    parser.add_argument(
        '--base-dir', '-d',
        default=DEFAULT_OUTPUT_DIR,
        help='Base directory containing materials'
    )
    parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for organized materials'
    )

    args = parser.parse_args()

    # Create manager
    manager = VideoMaterialsManager(base_dir=args.base_dir)

    # Organize materials
    if args.output_dir:
        result = manager.organize_materials(args.output_dir)
        if result['success']:
            print("\n✓ Materials organized successfully")
        else:
            print(f"\n✗ Organization failed: {result['error']}")
    else:
        # Just validate
        validation = manager.validate_materials()
        if validation['valid']:
            print("\n✓ All materials are valid")
        else:
            print("\n✗ Validation failed:")
            for error in validation['errors']:
                print(f"  - {error}")


if __name__ == '__main__':
    main()
