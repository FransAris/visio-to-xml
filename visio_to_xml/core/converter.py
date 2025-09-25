"""main converter orchestrating the visio to XML conversion process."""

from pathlib import Path
from typing import Optional, List
import asyncio

from .config import Config, get_config
from ..parsers.visio_parser import VisioParser, VisioPage
from ..ocr.mistral_ocr import MistralOCR
from ..converters.drawio_converter import DrawIOConverter
from ..converters.mermaid_converter import MermaidConverter


class VisioConverter:
    """main converter class for visio to XML conversion."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.ocr_client = None
        
        # initialize OCR if API key is available
        if self.config.mistral_api_key:
            self.ocr_client = MistralOCR(self.config)
    
    def convert_file(
        self, 
        input_path: Path, 
        output_format: str = "drawio",
        output_path: Optional[Path] = None
    ) -> Path:
        """convert a visio file to the specified format."""
        
        # validate input
        if not input_path.exists():
            raise FileNotFoundError(f"input file not found: {input_path}")
        
        if input_path.suffix.lower() not in ['.vsdx', '.vsd']:
            raise ValueError(f"unsupported file format: {input_path.suffix}")
        
        # parse visio file
        print(f"parsing visio file: {input_path}")
        parser = VisioParser(input_path)
        pages = parser.parse()
        
        if not pages:
            raise ValueError("no pages found in visio file")
        
        print(f"found {len(pages)} page(s)")
        
        # process images with OCR if available
        if self.ocr_client:
            print("processing images with OCR...")
            self._process_images_with_ocr(pages)
        
        # determine output path
        if output_path is None:
            output_name = input_path.stem
            if output_format == "drawio":
                output_path = self.config.output_directory / f"{output_name}.drawio"
            elif output_format == "mermaid":
                output_path = self.config.output_directory / f"{output_name}.md"
            else:
                raise ValueError(f"unsupported output format: {output_format}")
        
        # convert to specified format
        print(f"converting to {output_format} format...")
        
        if output_format == "drawio":
            converter = DrawIOConverter()
            xml_content = converter.convert_pages(pages)
            converter.save_to_file(xml_content, output_path)
        elif output_format == "mermaid":
            converter = MermaidConverter()
            mermaid_content = converter.convert_pages(pages)
            converter.save_to_file(mermaid_content, output_path)
        else:
            raise ValueError(f"unsupported output format: {output_format}")
        
        print(f"conversion completed: {output_path}")
        return output_path
    
    def convert_file_both_formats(self, input_path: Path) -> tuple[Path, Path]:
        """convert a visio file to both draw.io and mermaid formats efficiently."""
        
        # validate input
        if not input_path.exists():
            raise FileNotFoundError(f"input file not found: {input_path}")
        
        if input_path.suffix.lower() not in ['.vsdx', '.vsd']:
            raise ValueError(f"unsupported file format: {input_path.suffix}")
        
        # parse visio file once
        print(f"parsing visio file: {input_path}")
        parser = VisioParser(input_path)
        pages = parser.parse()
        
        if not pages:
            raise ValueError("no pages found in visio file")
        
        print(f"found {len(pages)} page(s)")
        
        # process images with OCR if available
        if self.ocr_client:
            print("processing images with OCR...")
            self._process_images_with_ocr(pages)
        
        # determine output paths
        output_name = input_path.stem
        drawio_path = self.config.output_directory / f"{output_name}.drawio"
        mermaid_path = self.config.output_directory / f"{output_name}.md"
        
        # convert to both formats
        print("converting to draw.io format...")
        drawio_converter = DrawIOConverter()
        drawio_xml = drawio_converter.convert_pages(pages)
        drawio_converter.save_to_file(drawio_xml, drawio_path)
        
        print("converting to mermaid format...")
        mermaid_converter = MermaidConverter()
        mermaid_content = mermaid_converter.convert_pages(pages)
        mermaid_converter.save_to_file(mermaid_content, mermaid_path)
        
        print(f"conversion completed: {drawio_path}, {mermaid_path}")
        return drawio_path, mermaid_path
    
    def _process_images_with_ocr(self, pages: List[VisioPage]) -> None:
        """process images in pages using OCR to extract text."""
        total_images = sum(
            1 for page in pages 
            for shape in page.shapes 
            if shape.has_image and shape.image_data
        )
        
        if total_images == 0:
            print("no images found for OCR processing")
            return
        
        print(f"processing {total_images} images with OCR...")
        processed = 0
        
        for page in pages:
            for shape in page.shapes:
                if shape.has_image and shape.image_data:
                    try:
                        ocr_text = self.ocr_client.extract_text(shape.image_data)
                        if ocr_text:
                            # append OCR text to existing shape text
                            if shape.text:
                                shape.text += f" [OCR: {ocr_text}]"
                            else:
                                shape.text = f"[OCR: {ocr_text}]"
                            
                            print(f"OCR extracted: {ocr_text[:50]}...")
                        
                        processed += 1
                        print(f"processed {processed}/{total_images} images")
                        
                    except Exception as e:
                        print(f"error processing image in shape {shape.id}: {e}")
                        continue
    
    def list_pages(self, input_path: Path) -> List[str]:
        """list pages in a visio file without full conversion."""
        parser = VisioParser(input_path)
        pages = parser.parse()
        return [f"{page.id}: {page.name}" for page in pages]
    
    def is_ocr_available(self) -> bool:
        """check if OCR functionality is available."""
        return self.ocr_client is not None and self.ocr_client.is_available()
