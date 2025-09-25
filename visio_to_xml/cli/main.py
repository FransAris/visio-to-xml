"""command-line interface for visio-to-xml converter."""

from pathlib import Path
from typing import Optional
import sys

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core.converter import VisioConverter
from ..core.config import get_config


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """visio-to-xml: convert visio files to XML format for draw.io and mermaid."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--format', '-f',
    type=click.Choice(['drawio', 'mermaid', 'both'], case_sensitive=False),
    default='drawio',
    help='output format: drawio, mermaid, or both (default: drawio)'
)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='output file path (auto-generated if not specified, ignored when format=both)'
)
@click.option(
    '--no-ocr',
    is_flag=True,
    help='skip OCR processing of images'
)
def convert(
    input_file: Path,
    format: str,
    output: Optional[Path],
    no_ocr: bool
) -> None:
    """convert a visio file to XML format."""
    
    try:
        # initialize converter
        config = get_config()
        converter = VisioConverter(config)
        
        # check OCR availability
        if not no_ocr and not converter.is_ocr_available():
            console.print(
                "[yellow]warning: OCR not available. set MISTRAL_API_KEY to enable image text extraction[/yellow]"
            )
        
        # handle different format options
        if format.lower() == 'both':
            # convert to both formats efficiently (parse once)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("converting to both formats...", total=None)
                
                # convert to both formats in one go
                drawio_output, mermaid_output = converter.convert_file_both_formats(input_file)
                
                progress.update(task, completed=1, total=1)
            
            console.print(f"[green]✓[/green] draw.io output: {drawio_output}")
            console.print(f"[green]✓[/green] mermaid output: {mermaid_output}")
        else:
            # single format conversion
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("converting visio file...", total=None)
                
                # perform conversion
                output_path = converter.convert_file(
                    input_file,
                    output_format=format.lower(),
                    output_path=output
                )
                
                progress.update(task, completed=1, total=1)
            
            console.print(f"[green]✓[/green] conversion completed: {output_path}")
        
    except Exception as e:
        console.print(f"[red]error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
def info(input_file: Path) -> None:
    """show information about a visio file."""
    
    try:
        converter = VisioConverter()
        pages = converter.list_pages(input_file)
        
        if not pages:
            console.print("no pages found in visio file")
            return
        
        # create table
        table = Table(title=f"visio file: {input_file.name}")
        table.add_column("page ID", style="cyan")
        table.add_column("page name", style="magenta")
        
        for page_info in pages:
            page_id, page_name = page_info.split(": ", 1)
            table.add_row(page_id, page_name)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]error:[/red] {e}")
        sys.exit(1)


@cli.command()
def check() -> None:
    """check system configuration and dependencies."""
    
    config = get_config()
    converter = VisioConverter(config)
    
    # create status table
    table = Table(title="system status")
    table.add_column("component", style="cyan")
    table.add_column("status", style="bold")
    table.add_column("details")
    
    # check output directory
    if config.output_directory.exists():
        table.add_row("output directory", "[green]✓[/green]", str(config.output_directory))
    else:
        table.add_row("output directory", "[yellow]created[/yellow]", str(config.output_directory))
    
    # check OCR availability
    if converter.is_ocr_available():
        table.add_row("mistral OCR", "[green]✓[/green]", "available")
    else:
        table.add_row("mistral OCR", "[red]✗[/red]", "not configured (set MISTRAL_API_KEY)")
    
    # check config
    table.add_row("output format", "[blue]info[/blue]", config.default_output_format)
    table.add_row("max image size", "[blue]info[/blue]", str(config.max_image_size))
    table.add_row("OCR threshold", "[blue]info[/blue]", str(config.ocr_confidence_threshold))
    
    console.print(table)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    '--format', '-f',
    type=click.Choice(['drawio', 'mermaid', 'both'], case_sensitive=False),
    default='drawio',
    help='output format: drawio, mermaid, or both (default: drawio)'
)
@click.option(
    '--recursive', '-r',
    is_flag=True,
    help='process files recursively'
)
def batch(directory: Path, format: str, recursive: bool) -> None:
    """batch convert all visio files in a directory."""
    
    try:
        # find visio files
        pattern = "**/*.vsdx" if recursive else "*.vsdx"
        visio_files = list(directory.glob(pattern))
        
        vsd_pattern = "**/*.vsd" if recursive else "*.vsd"
        visio_files.extend(directory.glob(vsd_pattern))
        
        if not visio_files:
            console.print("no visio files found in directory")
            return
        
        console.print(f"found {len(visio_files)} visio file(s)")
        
        # initialize converter
        converter = VisioConverter()
        
        # process files with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for i, visio_file in enumerate(visio_files):
                task = progress.add_task(f"processing {visio_file.name}...", total=None)
                
                try:
                    if format.lower() == 'both':
                        # convert to both formats efficiently
                        drawio_output, mermaid_output = converter.convert_file_both_formats(visio_file)
                        progress.update(task, completed=1, total=1)
                        console.print(f"[green]✓[/green] {visio_file.name} → {drawio_output.name}, {mermaid_output.name}")
                    else:
                        # single format
                        output_path = converter.convert_file(
                            visio_file,
                            output_format=format.lower()
                        )
                        progress.update(task, completed=1, total=1)
                        console.print(f"[green]✓[/green] {visio_file.name} → {output_path.name}")
                    
                except Exception as e:
                    console.print(f"[red]✗[/red] {visio_file.name}: {e}")
                    continue
        
        console.print(f"[green]batch conversion completed[/green]")
        
    except Exception as e:
        console.print(f"[red]error:[/red] {e}")
        sys.exit(1)


def main() -> None:
    """entry point for the CLI."""
    cli()
