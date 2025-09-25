"""converter for draw.io XML format."""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from pathlib import Path

from ..parsers.visio_parser import VisioPage, VisioShape


class DrawIOConverter:
    """converts visio pages to draw.io XML format."""
    
    def __init__(self):
        self.shape_counter = 2  # start at 2 since 0 and 1 are reserved
        self.page_counter = 0
    
    def convert_pages(self, pages: List[VisioPage]) -> str:
        """convert multiple visio pages to draw.io XML."""
        # create root mxfile element
        root = ET.Element('mxfile', {
            'host': 'app.diagrams.net',
            'modified': '2024-01-01T00:00:00.000Z',
            'agent': 'visio-to-xml',
            'version': '1.0',
            'etag': 'generated'
        })
        
        # convert each page
        for page in pages:
            diagram_elem = self._convert_page(page)
            root.append(diagram_elem)
        
        # format and return XML
        self._indent_xml(root)
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    def _convert_page(self, page: VisioPage) -> ET.Element:
        """convert a single visio page to draw.io diagram."""
        # create diagram element
        diagram = ET.Element('diagram', {
            'id': f'page_{self.page_counter}',
            'name': page.name
        })
        self.page_counter += 1
        
        # create mxGraphModel
        graph_model = ET.SubElement(diagram, 'mxGraphModel', {
            'dx': '1422',
            'dy': '794',
            'grid': '1',
            'gridSize': '10',
            'guides': '1',
            'tooltips': '1',
            'connect': '1',
            'arrows': '1',
            'fold': '1',
            'page': '1',
            'pageScale': '1',
            'pageWidth': '827',
            'pageHeight': '1169',
            'math': '0',
            'shadow': '0'
        })
        
        # create root cell container
        root_cell = ET.SubElement(graph_model, 'root')
        
        # add default cells
        ET.SubElement(root_cell, 'mxCell', {'id': '0'})
        ET.SubElement(root_cell, 'mxCell', {'id': '1', 'parent': '0'})
        
        # convert shapes
        shape_map = {}
        for shape in page.shapes:
            cell_elem = self._convert_shape(shape)
            root_cell.append(cell_elem)
            shape_map[shape.id] = self.shape_counter - 1
        
        # convert connections
        for connection in page.connections:
            conn_elem = self._convert_connection(connection, shape_map)
            if conn_elem is not None:
                root_cell.append(conn_elem)
        
        return diagram
    
    def _convert_shape(self, shape: VisioShape) -> ET.Element:
        """convert a visio shape to draw.io cell."""
        cell_id = str(self.shape_counter)
        self.shape_counter += 1
        
        # determine shape style based on type
        style = self._get_shape_style(shape)
        
        # create cell element
        cell = ET.Element('mxCell', {
            'id': cell_id,
            'value': shape.text,
            'style': style,
            'vertex': '1',
            'parent': '1'
        })
        
        # add geometry
        geometry = ET.SubElement(cell, 'mxGeometry', {
            'x': str(shape.x),
            'y': str(shape.y),
            'width': str(shape.width),
            'height': str(shape.height),
            'as': 'geometry'
        })
        
        return cell
    
    def _get_shape_style(self, shape: VisioShape) -> str:
        """generate draw.io style string for shape."""
        base_style = 'rounded=0;whiteSpace=wrap;html=1;'
        
        # customize based on shape type
        if 'process' in shape.shape_type.lower():
            return base_style + 'fillColor=#dae8fc;strokeColor=#6c8ebf;'
        elif 'decision' in shape.shape_type.lower():
            return base_style + 'rhombus;fillColor=#fff2cc;strokeColor=#d6b656;'
        elif 'start' in shape.shape_type.lower() or 'end' in shape.shape_type.lower():
            return base_style + 'ellipse;fillColor=#d5e8d4;strokeColor=#82b366;'
        elif shape.has_image:
            return base_style + 'shape=image;imageAspect=0;aspect=fixed;'
        else:
            return base_style + 'fillColor=#f8cecc;strokeColor=#b85450;'
    
    def _convert_connection(self, connection: Dict[str, Any], shape_map: Dict[str, int]) -> ET.Element:
        """convert a visio connection to draw.io edge."""
        from_id = shape_map.get(connection['from'])
        to_id = shape_map.get(connection['to'])
        
        if from_id is None or to_id is None:
            return None
        
        edge_id = str(self.shape_counter)
        self.shape_counter += 1
        
        # create edge element
        edge = ET.Element('mxCell', {
            'id': edge_id,
            'style': 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;',
            'edge': '1',
            'parent': '1',
            'source': str(from_id),
            'target': str(to_id)
        })
        
        # add geometry
        geometry = ET.SubElement(edge, 'mxGeometry', {
            'relative': '1',
            'as': 'geometry'
        })
        
        return edge
    
    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """add proper indentation to XML for readability."""
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def save_to_file(self, xml_content: str, output_path: Path) -> None:
        """save draw.io XML to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"draw.io XML saved to: {output_path}")
