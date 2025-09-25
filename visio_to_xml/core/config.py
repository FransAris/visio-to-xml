"""configuration management for visio-to-xml."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """application configuration using pydantic settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # mistral API configuration
    mistral_api_key: Optional[str] = Field(default=None, description="mistral API key for OCR")
    mistral_api_url: str = Field(
        default="https://api.mistral.ai/v1",
        description="mistral API base URL"
    )
    
    # optional custom OCR
    custom_ocr_endpoint: Optional[str] = Field(
        default=None,
        description="custom OCR endpoint URL"
    )
    custom_ocr_api_key: Optional[str] = Field(
        default=None,
        description="custom OCR API key"
    )
    
    # output configuration
    default_output_format: str = Field(
        default="drawio",
        description="default output format (drawio or mermaid)"
    )
    output_directory: Path = Field(
        default="output/",
        description="directory for output files"
    )
    
    # processing settings
    max_image_size: int = Field(
        default=1024,
        description="maximum image size for OCR processing"
    )
    ocr_confidence_threshold: float = Field(
        default=0.8,
        description="minimum confidence threshold for OCR results"
    )
    enable_debug_logging: bool = Field(
        default=False,
        description="enable debug logging"
    )
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # ensure output directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """get application configuration instance."""
    return Config()
