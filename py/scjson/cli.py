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
from .context import DocumentContext, ExecutionMode
from .safe_eval import SafeExpressionEvaluator
from .events import Event
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


@main.command(help="Create Swift type files for scjson")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file base.")
def swift(output: Path | None):
    """Create Swift structures and enums for scjson."""
    print(f"Convert Scjson type for swift - Path: {output}")
    Gen = JinjaGenPydantic(output=output, lang="swift")
    base_dir = os.path.abspath(output)
    os.makedirs(base_dir, exist_ok=True)
    file_name = "ScjsonTypes.swift"
    file_description = "Generated Swift codable models for scjson"
    Gen.render_to_file(file_name, "scjson_props.swift.jinja2", locals())


@main.command(help="Create Ruby type files for scjson")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file base.")
def ruby(output: Path | None):
    """Create Ruby classes and helpers for scjson."""
    print(f"Convert Scjson type for ruby - Path: {output}")
    Gen = JinjaGenPydantic(output=output, lang="ruby")
    base_dir = os.path.abspath(output)
    os.makedirs(base_dir, exist_ok=True)
    file_name = "types.rb"
    file_description = "Ruby helper types for scjson"
    Gen.render_to_file(file_name, "scjson_props.rb.jinja2", locals())


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


@main.command(help="Emit a standardized JSONL execution trace for a document.")
@click.option(
    "--input",
    "-I",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="SCJSON/SCXML document",
)
@click.option(
    "--events",
    "-e",
    "events_path",
    required=False,
    type=click.Path(exists=False, path_type=Path),
    help="JSONL stream of events; defaults to stdin when omitted",
)
@click.option("--xml", "is_xml", is_flag=True, default=False, help="Input is SCXML")
@click.option(
    "--out",
    "-o",
    "out_path",
    required=False,
    type=click.Path(path_type=Path),
    help="Destination trace file; defaults to stdout",
)
@click.option(
    "--unsafe-eval",
    is_flag=True,
    default=False,
    help="Disable sandboxing and allow Python eval for expressions",
)
@click.option(
    "--expr-preset",
    type=click.Choice(["standard", "minimal"], case_sensitive=False),
    default="standard",
    show_default=True,
    help="Select sandbox preset for expressions (ignored when --unsafe-eval)",
)
@click.option(
    "--expr-allow",
    multiple=True,
    metavar="PATTERN",
    help="Additional allow-list patterns for the sandbox (can be repeated)",
)
@click.option(
    "--expr-deny",
    multiple=True,
    metavar="PATTERN",
    help="Additional deny-list patterns for the sandbox (can be repeated)",
)
@click.option(
    "--max-steps",
    type=click.IntRange(min=1),
    default=None,
    help="Limit the number of processed event steps",
)
@click.option(
    "--lax/--strict",
    "lax_mode",
    default=False,
    help="Use lax execution mode when set (default strict).",
)
@click.option(
    "--advance-time",
    type=float,
    default=0.0,
    show_default=True,
    help="Advance mock time by N seconds before processing events",
)
@click.option(
    "--leaf-only/--full-states",
    "leaf_only",
    default=False,
    help="Restrict configuration/entered/exited sets to leaf states",
)
@click.option(
    "--omit-actions",
    is_flag=True,
    default=False,
    help="Omit actionLog entries from the trace output",
)
@click.option(
    "--omit-delta",
    is_flag=True,
    default=False,
    help="Omit datamodelDelta entries from the trace output",
)
@click.option(
    "--omit-transitions",
    is_flag=True,
    default=False,
    help="Omit firedTransitions entries from the trace output",
)
@click.option(
    "--ordering",
    type=click.Choice(["tolerant", "strict", "scion"], case_sensitive=False),
    default="tolerant",
    show_default=True,
    help="Ordering policy for child→parent emissions (finalize, etc.)",
)
@click.option(
    "--emit-time-steps/--no-emit-time-steps",
    "emit_time_steps",
    is_flag=True,
    default=False,
    help=(
        "When an advance_time control token is seen, emit a synthetic step to flush timers."
        " Disabled by default to keep control tokens from affecting step counts."
    ),
)
def engine_trace(
    input_path: Path,
    events_path: Path | None,
    is_xml: bool,
    out_path: Path | None,
    unsafe_eval: bool,
    expr_preset: str,
    expr_allow: tuple[str, ...],
    expr_deny: tuple[str, ...],
    max_steps: int | None,
    lax_mode: bool,
    leaf_only: bool,
    omit_actions: bool,
    omit_delta: bool,
    omit_transitions: bool,
    advance_time: float,
    ordering: str,
    emit_time_steps: bool,
) -> None:
    """Produce a JSON lines trace of engine steps for comparison harnesses.

    Parameters
    ----------
    input_path: Path
        SCJSON or SCXML chart.
    events_path: Path | None
        Optional JSONL file of events; reads stdin when omitted.
    is_xml: bool
        Treat ``input_path`` as SCXML when ``True``.
    out_path: Path | None
        Optional destination file; writes to stdout when omitted.
    unsafe_eval: bool
        Allow direct Python ``eval`` for expressions when ``True``.
    max_steps: int | None
        Optional maximum number of processed event steps after the initial
        snapshot.
    lax_mode: bool
        Selects lax execution mode when ``True``; strict mode remains default.

    Returns
    -------
    None
        Writes one JSON object per line.
    """

    execution_mode = ExecutionMode.LAX if lax_mode else ExecutionMode.STRICT
    # Configure evaluator unless unsafe is requested
    evaluator = None
    if not unsafe_eval:
        # Minimal preset denies math.* and trims to a smaller surface
        deny: list[str] = list(expr_deny or ())
        allow: list[str] = list(expr_allow or ())
        if (expr_preset or "standard").lower() == "minimal":
            deny.append("math.*")
        evaluator = SafeExpressionEvaluator(allow_patterns=allow or None, deny_patterns=deny or None)
    ctx_kwargs = {
        "allow_unsafe_eval": unsafe_eval,
        "execution_mode": execution_mode,
    }
    if evaluator is not None:
        ctx_kwargs["evaluator"] = evaluator
    ctx = (
        DocumentContext.from_xml_file(input_path, **ctx_kwargs)
        if is_xml
        else DocumentContext.from_json_file(input_path, **ctx_kwargs)
    )
    try:
        ctx.ordering_mode = (ordering or "tolerant").lower()
    except Exception:
        pass

    sink: TextIO
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sink = open(out_path, "w", encoding="utf-8")
    else:
        sink = sys.stdout

    stream_handle: TextIO | None = None
    try:
        # Optional time advance to release delayed sends scheduled during init
        if advance_time and advance_time > 0:
            ctx.advance_time(advance_time)
        # Note: we do not drain queued events at init here; step 0 represents
        # initial configuration after internal (eventless) transitions only.
        # Initial snapshot step (step 0)
        filtered_start = ctx._filter_states(ctx.configuration)
        if leaf_only:
            leaf_ids = ctx.leaf_state_ids()
            filtered_start = [s for s in filtered_start if s in leaf_ids]
        init = {
            "step": 0,
            "event": None,
            "firedTransitions": [] if not omit_transitions else [],
            "enteredStates": sorted(filtered_start, key=ctx._activation_order_key),
            "exitedStates": [],
            "configuration": sorted(filtered_start, key=ctx._activation_order_key),
            "actionLog": [] if not omit_actions else [],
            "datamodelDelta": (
                {} if omit_delta else {k: ctx.data_model[k] for k in sorted(ctx.data_model)}
            ),
        }
        sink.write(dumps(init) + "\n")

        # Event stream
        if events_path:
            stream_handle = open(events_path, "r", encoding="utf-8")
            stream: TextIO = stream_handle
        else:
            stream = sys.stdin

        step_no = 1
        for msg in JsonStreamDecoder(stream):
            # Support control tokens in the event stream to advance time
            # without emitting a trace step. This enables vectors to flush
            # delayed <send> events between external stimuli.
            try:
                adv = msg.get("advance_time") if isinstance(msg, dict) else None
                if isinstance(adv, (int, float)) and adv > 0:
                    ctx.advance_time(float(adv))
                    if emit_time_steps:
                        trace = ctx.trace_step(Event(name="__time__", data=None))
                        if leaf_only:
                            leaf_ids = ctx.leaf_state_ids()
                            for key in ("configuration", "enteredStates", "exitedStates"):
                                vals = trace.get(key)
                                if isinstance(vals, list):
                                    trace[key] = [v for v in vals if v in leaf_ids]
                        if omit_actions and "actionLog" in trace:
                            trace["actionLog"] = []
                        if omit_delta and "datamodelDelta" in trace:
                            trace["datamodelDelta"] = {}
                        if not omit_delta and isinstance(trace.get("datamodelDelta"), dict):
                            dm = trace["datamodelDelta"]
                            trace["datamodelDelta"] = {k: dm[k] for k in sorted(dm)}
                        if omit_transitions and "firedTransitions" in trace:
                            trace["firedTransitions"] = []
                        trace["event"] = None
                        trace["step"] = step_no
                        sink.write(dumps(trace) + "\n")
                        step_no += 1
                    continue
            except Exception:
                # Fall through to normal event handling
                pass
            if max_steps is not None and step_no > max_steps:
                click.echo(
                    f"Reached max step limit ({max_steps}); remaining events skipped.",
                    err=True,
                )
                break
            evt_name = msg.get("event") or msg.get("name")
            if not evt_name:
                continue
            evt_data = msg.get("data")
            trace = ctx.trace_step(Event(name=evt_name, data=evt_data))
            # Post-process filtering and ordering for determinism/size
            if leaf_only:
                leaf_ids = ctx.leaf_state_ids()
                for key in ("configuration", "enteredStates", "exitedStates"):
                    vals = trace.get(key)
                    if isinstance(vals, list):
                        trace[key] = [v for v in vals if v in leaf_ids]
            if omit_actions and "actionLog" in trace:
                trace["actionLog"] = []
            if omit_delta and "datamodelDelta" in trace:
                trace["datamodelDelta"] = {}
            # Ensure reproducible ordering for datamodelDelta keys
            if not omit_delta and isinstance(trace.get("datamodelDelta"), dict):
                dm = trace["datamodelDelta"]
                trace["datamodelDelta"] = {k: dm[k] for k in sorted(dm)}
            if omit_transitions and "firedTransitions" in trace:
                trace["firedTransitions"] = []
            trace["step"] = step_no
            sink.write(dumps(trace) + "\n")
            step_no += 1
    finally:
        if sink is not sys.stdout:
            sink.close()
        if stream_handle is not None:
            stream_handle.close()

@main.command(help="Run a chart to quiescence and report outcome (pass/fail/other).")
@click.option(
    "--input",
    "-I",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="SCJSON/SCXML document",
)
@click.option("--xml", "is_xml", is_flag=True, default=False, help="Input is SCXML")
@click.option(
    "--advance-time",
    type=float,
    default=0.0,
    show_default=True,
    help="Advance mock time by N seconds before running (for delayed sends)",
)
@click.option(
    "--max-steps",
    type=click.IntRange(min=1),
    default=2000,
    show_default=True,
    help="Maximum microsteps to process before declaring 'other'",
)
@click.option(
    "--lax/--strict",
    "lax_mode",
    default=True,
    show_default=True,
    help="Use lax execution mode (default true for verification)",
)
def engine_verify(
    input_path: Path,
    is_xml: bool,
    advance_time: float,
    max_steps: int,
    lax_mode: bool,
):
    """Execute chart to quiescence and print outcome summary.

    Outcome is based on presence of 'pass' or 'fail' state IDs in the final
    configuration. Exit codes: 0=pass, 1=fail, 2=other.
    """

    execution_mode = ExecutionMode.LAX if lax_mode else ExecutionMode.STRICT
    ctx = (
        DocumentContext.from_xml_file(input_path, execution_mode=execution_mode)
        if is_xml
        else DocumentContext.from_json_file(input_path, execution_mode=execution_mode)
    )
    if advance_time > 0:
        ctx.advance_time(advance_time)
    ctx.run(steps=max_steps)
    config = set(ctx.configuration)
    if "pass" in config:
        click.echo("outcome: pass")
        raise SystemExit(0)
    if "fail" in config:
        click.echo("outcome: fail")
        raise SystemExit(1)
    click.echo("outcome: other")
    raise SystemExit(2)

if __name__ == "__main__":
    main()
