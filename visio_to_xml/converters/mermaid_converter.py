"""converter for mermaid diagram format."""

from typing import List, Dict, Any
from pathlib import Path

from ..parsers.visio_parser import VisioPage, VisioShape


class MermaidConverter:
    """converts visio pages to mermaid diagram format."""
    
    def __init__(self):
        self.node_counter = 1
        self.node_map = {}
    
    def convert_pages(self, pages: List[VisioPage]) -> str:
        """convert multiple visio pages to mermaid format."""
        mermaid_content = []
        
        for i, page in enumerate(pages):
            if len(pages) > 1:
                mermaid_content.append(f"## {page.name}")
                mermaid_content.append("")
            
            page_mermaid = self._convert_page(page)
            mermaid_content.append(page_mermaid)
            
            if i < len(pages) - 1:
                mermaid_content.append("")
                mermaid_content.append("---")
                mermaid_content.append("")
        
        return "\n".join(mermaid_content)
    
    def _convert_page(self, page: VisioPage) -> str:
        """convert a single visio page to mermaid diagram."""
        lines = []
        
        # determine diagram type based on shapes and connections
        diagram_type = self._detect_diagram_type(page)
        lines.append(f"{diagram_type}")
        
        # reset node mapping for each page
        self.node_map = {}
        self.node_counter = 1
        
        # convert shapes to nodes
        for shape in page.shapes:
            node_def = self._convert_shape_to_node(shape, diagram_type)
            if node_def:
                lines.append(f"    {node_def}")
        
        # convert connections
        for connection in page.connections:
            conn_def = self._convert_connection_to_edge(connection, diagram_type)
            if conn_def:
                lines.append(f"    {conn_def}")
        
        return "\n".join(lines)
    
    def _detect_diagram_type(self, page: VisioPage) -> str:
        """detect the most appropriate mermaid diagram type."""
        # analyze shapes and connections to determine type
        has_connections = len(page.connections) > 0
        has_decision_shapes = any(
            'decision' in shape.shape_type.lower() or 
            'diamond' in shape.shape_type.lower()
            for shape in page.shapes
        )
        
        if has_decision_shapes and has_connections:
            return "flowchart TD"
        elif has_connections:
            return "graph TD"
        else:
            return "flowchart TD"
    
    def _convert_shape_to_node(self, shape: VisioShape, diagram_type: str) -> str:
        """convert a visio shape to mermaid node."""
        # create unique node ID
        node_id = f"node{self.node_counter}"
        self.node_map[shape.id] = node_id
        self.node_counter += 1
        
        # clean text for mermaid
        text = self._clean_text_for_mermaid(shape.text)
        if not text:
            text = f"Shape {node_id}"
        
        # format complete mermaid node with proper syntax
        return self._format_mermaid_node(node_id, shape, text)
    
    def _format_mermaid_node(self, node_id: str, shape: VisioShape, text: str) -> str:
        """format complete mermaid node with proper syntax."""
        shape_type = shape.shape_type.lower()
        
        # Text is already cleaned by _clean_text_for_mermaid, just use it directly
        # For safety, ensure no remaining problematic characters
        safe_text = text.replace('"', "'").replace('\\', '/')
        
        if 'decision' in shape_type or 'diamond' in shape_type:
            return f'{node_id}{{"{"}"}{safe_text}"{"}}"}'  # Diamond: node{text}
        elif 'start' in shape_type or 'end' in shape_type or 'oval' in shape_type:
            return f'{node_id}["{safe_text}"]'  # Use square brackets for consistency
        else:
            return f'{node_id}["{safe_text}"]'  # Rectangle: node["text"]
    
    def _convert_connection_to_edge(self, connection: Dict[str, Any], diagram_type: str) -> str:
        """convert a visio connection to mermaid edge."""
        from_node = self.node_map.get(connection['from'])
        to_node = self.node_map.get(connection['to'])
        
        if not from_node or not to_node:
            return ""
        
        # basic arrow connection
        return f"{from_node} --> {to_node}"
    
    def _clean_text_for_mermaid(self, text: str) -> str:
        """clean text to be safe for mermaid syntax."""
        if not text:
            return ""
        
        # remove or escape problematic characters for mermaid
        text = text.replace('\\n', ' ')  # handle escaped newlines first
        text = text.replace('\n', ' ')   # replace newlines with spaces
        text = text.replace('\r', ' ')   # replace carriage returns
        text = text.replace('#', 'hash') # replace hash symbols
        text = text.replace('&', 'and')  # replace ampersands
        text = text.replace('[', '(')    # replace brackets that could break syntax
        text = text.replace(']', ')')
        text = text.replace('{', '(')    # replace braces
        text = text.replace('}', ')')
        text = text.replace('<', 'lt')   # replace angle brackets
        text = text.replace('>', 'gt')
        text = text.replace('"', "'")    # replace double quotes with single quotes
        text = text.replace('`', "'")    # replace backticks with single quotes
        text = text.replace('|', '-')    # replace pipes with dashes
        text = ' '.join(text.split())    # normalize whitespace
        
        # preserve full content - users want to see complete OCR text
        # no truncation applied here
        
        return text
    
    def save_to_file(self, mermaid_content: str, output_path: Path) -> None:
        """save mermaid diagram to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mermaid_content)
        
        print(f"mermaid diagram saved to: {output_path}")
