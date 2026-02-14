"""Validator exports for lightweight OOXML checks."""

from .docx import DOCXSchemaValidator as DocxValidator
from .pptx import PPTXSchemaValidator as PptxValidator
from .redlining import RedliningValidator as RedlineValidator

DOCXSchemaValidator = DocxValidator
PPTXSchemaValidator = PptxValidator
RedliningValidator = RedlineValidator

__all__ = [
    "DOCXSchemaValidator",
    "PPTXSchemaValidator",
    "RedliningValidator",
]
