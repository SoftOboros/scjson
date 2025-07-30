"""
Agent Name: cli-interface

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

import os
import sys
import logging
from typing import TextIO
import click
from pathlib import Path
from .SCXMLDocumentHandler import SCXMLDocumentHandler
from .context import DocumentContext
from .json_stream import JsonStreamDecoder
from .jinja_gen import JinjaGenPydantic
from importlib.metadata import version, PackageNotFoundError
from json import dumps

def _get_metadata(pkg="scjson"):
    try:
        return {
            "version": version(pkg),
            "progname": pkg,
            "description": "SCJSON: SCXML ↔ JSON converter"
        }
    except PackageNotFoundError:
        return {
            "version": "unknown (not installed)",
            "progname": pkg,
            "description": "SCJSON (not installed)"
        }
md = _get_metadata()
md_str = f"{md['progname']} {md['version']} - {md['description']}"

def _splash() -> None:
    """Display program header."""
    click.echo(md_str)

@click.group(help=md_str, invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Command line interface for scjson conversions."""
    _splash()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command(help="Convert scjson file to SCXML.")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file or directory")
@click.option("--recursive", "-r", is_flag=True, default=False, help="Recurse into subdirectories when PATH is a directory")
@click.option("--verify", "-v", is_flag=True, default=False, help="Verify conversion without writing output")
@click.option("--keep-empty", is_flag=True, default=False, help="Keep null or empty items when producing JSON")
def xml(path: Path, output: Path | None, recursive: bool, verify: bool, keep_empty: bool):
    """Convert a single scjson file or all scjson files in a directory."""
    handler = SCXMLDocumentHandler(omit_empty=not keep_empty)

    def convert_file(src: Path, dest: Path | None):
        try:
            with open(src, "r", encoding="utf-8") as f:
                json_str = f.read()
            xml_str = handler.json_to_xml(json_str)
            if verify:
                handler.xml_to_json(xml_str)
                click.echo(f"Verified {src}")
                return True
        except Exception as e:
            click.echo(f"Failed to convert {src}: {e}", err=True)
            return False
        if dest is None:
            return True
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(xml_str)
        click.echo(f"Wrote {dest}")
        return True

    if path.is_dir():
        out_dir = output if output else path
        pattern = "**/*.scjson" if recursive else "*.scjson"
        for src in path.glob(pattern):
            if src.is_file():
                rel = src.relative_to(path)
                dest = out_dir / rel.with_suffix(".scxml") if not verify else None
                convert_file(src, dest)
    else:
        if output and (output.is_dir() or not output.suffix):
            base = output
        else:
            base = output.parent if output else path.parent
        if base:
            base.mkdir(parents=True, exist_ok=True)
        out_file = (
            output
            if output and output.suffix
            else (base / path.with_suffix(".scxml").name)
        ) if output else path.with_suffix(".scxml")
        dest = None if verify else out_file
        convert_file(path, dest)


@main.command(help="Convert SCXML file to scjson.")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file or directory")
@click.option("--recursive", "-r", is_flag=True, default=False, help="Recurse into subdirectories when PATH is a directory")
@click.option("--verify", "-v", is_flag=True, default=False, help="Verify conversion without writing output")
@click.option("--keep-empty", is_flag=True, default=False, help="Keep null or empty items when producing JSON")
@click.option(
    "--fail-unknown/--skip-unknown",
    "fail_unknown",
    default=True,
    help="Fail on unknown XML elements when converting",
)
def json(
    path: Path,
    output: Path | None,
    recursive: bool,
    verify: bool,
    keep_empty: bool,
    fail_unknown: bool,
):
    """Convert a single SCXML file or all SCXML files in a directory."""
    handler = SCXMLDocumentHandler(omit_empty=not keep_empty, fail_on_unknown_properties=fail_unknown)

    def convert_file(src: Path, dest: Path | None):
        try:
            with open(src, "r", encoding="utf-8") as f:
                xml_str = f.read()
            json_str = handler.xml_to_json(xml_str)
            if verify:
                handler.json_to_xml(json_str)
                click.echo(f"Verified {src}")
                return True
        except Exception as e:
            click.echo(f"Failed to convert {src}: {e}", err=True)
            return False
        if dest is None:
            return True
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(json_str)
        click.echo(f"Wrote {dest}")
        return True

    if path.is_dir():
        out_dir = output if output else path
        pattern = "**/*.scxml" if recursive else "*.scxml"
        for src in path.glob(pattern):
            if src.is_file():
                rel = src.relative_to(path)
                dest = out_dir / rel.with_suffix(".scjson") if not verify else None
                convert_file(src, dest)
    else:
        if output and (output.is_dir() or not output.suffix):
            base = output
        else:
            base = output.parent if output else path.parent
        if base:
            base.mkdir(parents=True, exist_ok=True)
        out_file = (
            output
            if output and output.suffix
            else (base / path.with_suffix(".scjson").name)
        ) if output else path.with_suffix(".scjson")
        dest = None if verify else out_file
        convert_file(path, dest)


@main.command(help="Validate scjson or SCXML files by round-tripping them in memory.")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--recursive", "-r", is_flag=True, default=False, help="Recurse into subdirectories when PATH is a directory")
def validate(path: Path, recursive: bool):
    """Check that files can be converted to the opposite format and back."""
    handler = SCXMLDocumentHandler()

    def validate_file(src: Path) -> bool:
        try:
            data = src.read_text(encoding="utf-8")
            if src.suffix == ".scxml":
                json_str = handler.xml_to_json(data)
                handler.json_to_xml(json_str)
            elif src.suffix == ".scjson":
                xml_str = handler.json_to_xml(data)
                handler.xml_to_json(xml_str)
            else:
                return True
        except Exception as e:
            click.echo(f"Validation failed for {src}: {e}", err=True)
            return False
        return True

    success = True
    if path.is_dir():
        pattern = "**/*" if recursive else "*"
        for src in path.glob(pattern):
            if src.is_file() and src.suffix in {".scxml", ".scjson"}:
                if not validate_file(src):
                    success = False
    else:
        if path.suffix in {".scxml", ".scjson"}:
            success = validate_file(path)
        else:
            click.echo("Unsupported file type", err=True)
            success = False

    if not success:
        raise SystemExit(1)


@main.command(help="Create typescrupt Type files for scjson")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file base.")
def typescript(output: Path | None):
    """Create typescrupt Type files for scjson."""
    print(f"Convert Scjson type for typescript - Path: {output}")
    Gen = JinjaGenPydantic(output=output)
    base_dir = os.path.abspath(output)
    os.makedirs(base_dir, exist_ok=True)
    is_runtime = True
    file_name = "scjsonProps.ts"
    file_description = "Properties runtime file for scjson types"
    Gen.render_to_file(file_name, "scjson_props.ts.jinja2", locals())
    #is_runtime = False
    #file_name = "scjsonProps.d.ts"
    #file_description = "Properties definition file for scjson types"
    #Gen.render_to_file(f"types/{file_name}", "scjson_props.ts.jinja2", locals())


@main.command(help="Create Rust type files for scjson")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file base.")
def rust(output: Path | None):
    """Create Rust structs and enums for scjson."""
    print(f"Convert Scjson type for rust - Path: {output}")
    Gen = JinjaGenPydantic(output=output, lang="rust")
    base_dir = os.path.abspath(output)
    os.makedirs(base_dir, exist_ok=True)
    file_name = "scjson_props.rs"
    file_description = "Properties file for scjson types"
    Gen.render_to_file(file_name, "scjson_props.rs.jinja2", locals())


@main.command(help="Export scjson.schema.json")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file base.")
def schema(output: Path | None):
    """Export scjson.schema.json."""
    Gen = JinjaGenPydantic(output=output)
    base_dir = os.path.abspath(output)
    outname = os.path.join(base_dir, "scjson.schema.json")
    os.makedirs(base_dir, exist_ok=True)
    with open(outname, "w") as schemafile:
        schemafile.write(dumps(Gen.schemas["Scxml"], indent=4))
    print(f'Generated: {outname}')


@main.command(help="Run a document using the demo engine.")
@click.option(
    "--input",
    "-I",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="SCJSON/SCXML document",
)
@click.option(
    "--output",
    "-o",
    "workdir",
    type=click.Path(path_type=Path),
    help="Working directory",
)
@click.option("--xml", "is_xml", is_flag=True, default=False, help="Input is SCXML")
def run(input_path: Path, workdir: Path | None, is_xml: bool) -> None:
    """Execute a document with the demo engine.

    Args:
        input_path: Path to the SCJSON or SCXML document.
        workdir: Directory used for runtime output and event logs.
        is_xml: Treat ``input_path`` as SCXML when ``True``.

    Returns:
        ``None``
    """

    sink: TextIO = sys.stdout
    if workdir:
        workdir.mkdir(parents=True, exist_ok=True)
        sink_path = workdir / "events.log"
        sink = open(sink_path, "w", encoding="utf-8")

    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sink, force=True)
    ctx = (
        DocumentContext.from_xml_file(input_path)
        if is_xml
        else DocumentContext.from_json_file(input_path)
    )
    ctx.enqueue("start")
    ctx.run()
    for msg in JsonStreamDecoder(sys.stdin):
        evt = msg.get("event") or msg.get("name")
        data = msg.get("data")
        if evt:
            ctx.enqueue(evt, data)
            ctx.run()
    if sink is not sys.stdout:
        sink.close()

if __name__ == "__main__":
    main()
