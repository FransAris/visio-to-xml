# Visio-to-xml (and more)

Convert visio files to XML format for draw.io and mermaid diagrams, because I was tired of colleagues using web-based Visio (MS). I am declaring holy war on OOXML and its 'Markup Compatibility Layer'. 
Currently it works a bit crap, but for now I blame OOXML.

## Features

- parse visio (.vsdx) files and extract shapes, text, and connections
- OCR processing of embedded images using mistral API
- convert to draw.io XML format for direct import
- convert to mermaid diagram syntax
- command-line interface with batch processing
- configurable output formats and processing options

## Installation

this project uses uv for python package management. install dependencies:

```bash
# install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# install project dependencies
uv sync

# install in development mode
uv pip install -e .
```

## configuration

copy the example configuration file and set your API keys:

```bash
cp config.env.example .env
```

edit `.env` and set your mistral API key:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Configuration options

- `MISTRAL_API_KEY`: required for OCR functionality
- `MISTRAL_API_URL`: mistral API endpoint (default: https://api.mistral.ai/v1)
- `DEFAULT_OUTPUT_FORMAT`: default output format (drawio or mermaid)
- `OUTPUT_DIRECTORY`: directory for output files (default: output/)
- `MAX_IMAGE_SIZE`: maximum image size for OCR processing (default: 1024)
- `OCR_CONFIDENCE_THRESHOLD`: minimum confidence for OCR results (default: 0.8)

## Usage

### Command line

convert a single visio file:

```bash
# convert to draw.io format (default)
visio2xml convert diagram.vsdx

# convert to mermaid format
visio2xml convert diagram.vsdx --format mermaid

# convert to both formats simultaneously
visio2xml convert diagram.vsdx --format both

# specify output file (single format only)
visio2xml convert diagram.vsdx --output my_diagram.drawio
```

get information about a visio file:

```bash
visio2xml info diagram.vsdx
```

batch convert all visio files in a directory:

```bash
# convert all files in current directory
visio2xml batch ./

# convert recursively including subdirectories
visio2xml batch ./ --recursive

# convert to mermaid format
visio2xml batch ./ --format mermaid

# convert to both formats
visio2xml batch ./ --format both
```

check system configuration:

```bash
visio2xml check
```

### Python API

```python
from pathlib import Path
from visio_to_xml import VisioConverter

# initialize converter
converter = VisioConverter()

# convert file
output_path = converter.convert_file(
    input_path=Path("diagram.vsdx"),
    output_format="drawio"  # or "mermaid"
)

print(f"converted to: {output_path}")
```

## Directory structure

```
visio-to-xml/
├── visio_to_xml/           # main package
│   ├── core/               # core functionality
│   │   ├── config.py       # configuration management
│   │   └── converter.py    # main converter class
│   ├── parsers/            # file format parsers
│   │   └── visio_parser.py # visio file parser
│   ├── ocr/                # OCR integration
│   │   └── mistral_ocr.py  # mistral API client
│   ├── converters/         # output format converters
│   │   ├── drawio_converter.py
│   │   └── mermaid_converter.py
│   └── cli/                # command-line interface
│       └── main.py
├── tests/                  # test suite
├── docs/                   # documentation and examples
├── output/                 # generated output files
└── examples/               # example visio files
```

## Supported formats

### Input formats

- `.vsdx` - visio 2013+ files

### Output formats

- **draw.io**: XML format for direct import into diagrams.net
- **mermaid**: markdown-compatible diagram syntax

## OCR processing

when a mistral API key is configured, the tool automatically:

1. detects embedded images in visio shapes
2. extracts image data from the visio file
3. sends images to mistral's vision model for text extraction
4. appends extracted text to shape labels

this helps preserve information from images that contain text or diagrams.

## Development

run tests:

```bash
uv run pytest
```

code formatting:

```bash
uv run black .
uv run ruff check .
```

type checking:

```bash
uv run mypy visio_to_xml/
```

## Limitations

- visio files use complex internal formats; parsing may not capture all elements
- OCR accuracy depends on image quality and mistral API availability
- some advanced visio features (custom shapes, macros) are not supported
- connection routing information may be simplified in output

## Loicense

don't care
