"""visio-to-xml: convert visio files to XML format for draw.io and mermaid."""

__version__ = "0.1.0"
__author__ = "fransaris"

from .core.converter import VisioConverter
from .core.config import Config

__all__ = ["VisioConverter", "Config"]
