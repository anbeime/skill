"""OOXML helpers for packing, unpacking, and lightweight validation."""

from .pack import pack_document
from .unpack import unpack_document

__all__ = ["pack_document", "unpack_document"]
