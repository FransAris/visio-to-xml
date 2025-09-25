"""parser for visio (.vsdx) files."""

import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from PIL import Image
import io


@dataclass
class VisioShape:
    """represents a shape in a visio diagram."""
    id: str
    text: str
    x: float
    y: float
    width: float
    height: float
    shape_type: str
    has_image: bool = False
    image_data: Optional[bytes] = None


@dataclass
class VisioPage:
    """represents a page in a visio document."""
    id: str
    name: str
    shapes: List[VisioShape]
    connections: List[Dict[str, Any]]


class VisioParser:
    """parser for visio (.vsdx) files."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.pages: List[VisioPage] = []
        self._namespaces = {
            'v': 'http://schemas.microsoft.com/office/visio/2012/main'
        }
    
    def parse(self) -> List[VisioPage]:
        """parse the visio file and extract pages with shapes."""
        try:
            with zipfile.ZipFile(self.file_path, 'r') as vsdx_zip:
                # read document structure
                self._parse_document_structure(vsdx_zip)
                
                # parse each page
                for page_info in self._get_page_list(vsdx_zip):
                    page = self._parse_page(vsdx_zip, page_info)
                    if page:
                        self.pages.append(page)
                        
        except Exception as e:
            raise ValueError(f"failed to parse visio file: {e}")
            
        return self.pages
    
    def _parse_document_structure(self, vsdx_zip: zipfile.ZipFile) -> None:
        """parse the main document structure."""
        try:
            # read document.xml to understand structure
            doc_content = vsdx_zip.read('visio/document.xml')
            self.doc_root = ET.fromstring(doc_content)
        except KeyError:
            raise ValueError("invalid visio file format: missing document.xml")
    
    def _get_page_list(self, vsdx_zip: zipfile.ZipFile) -> List[Dict[str, str]]:
        """get list of pages in the document."""
        pages = []
        
        try:
            # first try to read pages.xml to get page information
            pages_content = vsdx_zip.read('visio/pages/pages.xml')
            pages_root = ET.fromstring(pages_content)
            
            page_elements = pages_root.findall('.//v:Page', self._namespaces)
            
            for i, page_elem in enumerate(page_elements):
                page_id = page_elem.get('ID', f'page_{i}')
                page_name = page_elem.get('Name', f'Page {i+1}')
                
                pages.append({
                    'id': page_id,
                    'name': page_name,
                    'xml_path': f'visio/pages/page{i+1}.xml'
                })
                
        except KeyError:
            # fallback: look for page files directly
            page_files = [name for name in vsdx_zip.namelist() if name.startswith('visio/pages/page') and name.endswith('.xml')]
            
            for i, page_file in enumerate(sorted(page_files)):
                pages.append({
                    'id': str(i),
                    'name': f'Page {i+1}',
                    'xml_path': page_file
                })
            
        return pages
    
    def _parse_page(self, vsdx_zip: zipfile.ZipFile, page_info: Dict[str, str]) -> Optional[VisioPage]:
        """parse a single page from the visio file."""
        try:
            # read page XML
            page_content = vsdx_zip.read(page_info['xml_path'])
            page_root = ET.fromstring(page_content)
            
            shapes = []
            connections = []
            
            # parse shapes from PageContents/Shapes
            shape_elements = page_root.findall('.//v:Shape', self._namespaces)
            for shape_elem in shape_elements:
                shape = self._parse_shape(vsdx_zip, shape_elem)
                if shape:
                    shapes.append(shape)
            
            # parse connections (connectors between shapes)
            connect_elements = page_root.findall('.//v:Connect', self._namespaces)
            for connect_elem in connect_elements:
                connection = self._parse_connection(connect_elem)
                if connection:
                    connections.append(connection)
            
            # also look for connector shapes (shapes with Master='2' seem to be connectors)
            connector_shapes = [s for s in shapes if s.shape_type == 'connector' or 'Master' in str(shape_elem.attrib)]
            
            return VisioPage(
                id=page_info['id'],
                name=page_info['name'],
                shapes=shapes,
                connections=connections
            )
            
        except Exception as e:
            print(f"warning: failed to parse page {page_info['name']}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_shape(self, vsdx_zip: zipfile.ZipFile, shape_elem: ET.Element) -> Optional[VisioShape]:
        """parse a single shape element."""
        try:
            shape_id = shape_elem.get('ID', '')
            shape_type = shape_elem.get('Type', 'shape')
            master = shape_elem.get('Master', '')
            
            # extract text content from Text element
            text_elem = shape_elem.find('.//v:Text', self._namespaces)
            text = ''
            if text_elem is not None:
                # extract all text content, including between child elements
                text_parts = []
                
                # get text directly in the element
                if text_elem.text:
                    text_parts.append(text_elem.text.strip())
                
                # get text from all child elements recursively
                for child in text_elem:
                    if child.text:
                        text_parts.append(child.text.strip())
                    if child.tail:
                        text_parts.append(child.tail.strip())
                
                # also get text after the last child
                if text_elem.tail:
                    text_parts.append(text_elem.tail.strip())
                
                # join and clean up
                text = ' '.join([part for part in text_parts if part])
                text = ' '.join(text.split())  # normalize whitespace
            
            # extract position and size from Cell elements
            x, y, width, height = self._extract_geometry(shape_elem)
            
            # check for embedded images (ForeignData elements)
            has_image = False
            image_data = None
            
            foreign_data_elements = shape_elem.findall('.//v:ForeignData', self._namespaces)
            if foreign_data_elements:
                has_image = True
                # try to extract image data
                image_data = self._extract_image_data(vsdx_zip, foreign_data_elements[0])
            
            # determine if this is a connector shape
            if master == '2' or 'Connect' in shape_type:
                shape_type = 'connector'
            
            return VisioShape(
                id=shape_id,
                text=text,
                x=x,
                y=y,
                width=width,
                height=height,
                shape_type=shape_type,
                has_image=has_image,
                image_data=image_data
            )
            
        except Exception as e:
            print(f"warning: failed to parse shape {shape_id}: {e}")
            return None
    
    def _extract_geometry(self, shape_elem: ET.Element) -> tuple[float, float, float, float]:
        """extract position and size from Cell elements in shape."""
        try:
            # extract position and size from Cell elements
            x = 0.0
            y = 0.0
            width = 100.0
            height = 50.0
            
            # find Cell elements with position/size information
            for cell in shape_elem.findall('.//v:Cell', self._namespaces):
                cell_name = cell.get('N', '')
                cell_value = cell.get('V', '0')
                
                try:
                    value = float(cell_value)
                    if cell_name == 'PinX':
                        x = value
                    elif cell_name == 'PinY':
                        y = value
                    elif cell_name == 'Width':
                        width = value
                    elif cell_name == 'Height':
                        height = value
                except ValueError:
                    continue
            
            return x, y, width, height
            
        except Exception:
            # fallback to default values
            return 0.0, 0.0, 100.0, 50.0
    
    def _extract_image_data(self, vsdx_zip: zipfile.ZipFile, foreign_data_elem: ET.Element) -> Optional[bytes]:
        """extract image data from foreign data element."""
        try:
            # look for Rel element with reference ID
            rel_elem = foreign_data_elem.find('.//r:Rel', {'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'})
            if rel_elem is not None:
                rel_id = rel_elem.get('id', rel_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'))
                if rel_id:
                    # try to find image in media folder with various naming
                    possible_paths = [
                        f'visio/media/{rel_id}',
                        f'visio/media/image{rel_id[3:]}.png',  # rId1 -> image1.png
                        f'visio/media/image{rel_id[3:]}.jpg',
                        f'visio/media/image{rel_id[3:]}.jpeg',
                    ]
                    
                    for media_path in possible_paths:
                        try:
                            return vsdx_zip.read(media_path)
                        except KeyError:
                            continue
            
            # try to extract embedded data
            if foreign_data_elem.text:
                import base64
                return base64.b64decode(foreign_data_elem.text.strip())
                
        except Exception as e:
            print(f"warning: failed to extract image data: {e}")
            
        return None
    
    def _parse_connection(self, connect_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """parse connection between shapes."""
        try:
            from_shape = connect_elem.get('FromSheet')
            to_shape = connect_elem.get('ToSheet')
            
            if from_shape and to_shape:
                return {
                    'from': from_shape,
                    'to': to_shape,
                    'type': 'connector'
                }
                
        except Exception as e:
            print(f"warning: failed to parse connection: {e}")
            
        return None
