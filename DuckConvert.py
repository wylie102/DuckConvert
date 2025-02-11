#!/usr/bin/env python3
"""
DuckConvert: A conversion tool to convert between popular data storage file types
(CSV/TXT, JSON, Parquet, Excel) using DuckDB's Python API.

Usage example (assuming the script is aliased as "conv"):
    conv path/to/folder -i excel -s 1 -c A2:E7 -o pq

If the input type is not provided, the file extension is used to auto-detect.
For Excel files, if no sheet or range has been provided via the command line,
the tool will prompt for options.
"""

import logging
from pathlib import Path
import duckdb
from typing import Optional

from cli_interface import (
    parse_cli_arguments,
    FILE_TYPE_ALIASES,
    get_file_type_by_extension,
    prompt_for_txt_delimiter,
    prepare_cli_options,
    get_excel_options_for_files,
)
from path_manager import create_path_manager
from conversions import get_conversion_instance
from excel_utils import ExcelUtils

# Mapping of output file extensions for naming purposes.
EXTENSIONS = {
    "csv": ".csv",
    "tsv": ".tsv",
    "txt": ".txt",
    "parquet": ".parquet",
    "json": ".json",
    "excel": ".xlsx",
}


def process_file(
    file: Path,
    in_type: str,
    out_type: str,
    conn: duckdb.DuckDBPyConnection,
    excel_sheet=None,
    excel_range=None,
    output_dir: Optional[Path] = None,
    **kwargs,
) -> None:
    """
    Process a single file conversion:
      1. Construct the output file (ensuring no overwrite).
      2. Instantiate the conversion instance using the factory.
      3. Run the conversion.
    """
    logging.info(f"Processing file: {file.name}")

    # Determine the output file path.
    if output_dir is not None:
        output_file = output_dir / (file.stem + EXTENSIONS[out_type])
    else:
        output_file = file.with_suffix(EXTENSIONS[out_type])

    # Avoid overwriting an existing file.
    if output_file.exists():
        base = output_file.stem
        ext = output_file.suffix
        counter = 1
        candidate = output_file.parent / f"{base}_{counter}{ext}"
        while candidate.exists():
            counter += 1
            candidate = output_file.parent / f"{base}_{counter}{ext}"
        output_file = candidate

    try:
        # Instantiate the proper conversion instance.
        conversion = get_conversion_instance(
            conn,
            src=file,
            dst=output_file,
            input_format=in_type,
            output_format=out_type,
            sheet=excel_sheet,
            range_=excel_range,
            **kwargs,
        )
        conversion.run()
        logging.info(f"Converted to {output_file.name}")
    except Exception as e:
        logging.error(f"Error processing file {file.name}: {e}")


def convert(args):
    # Validate CLI options and get the input path and desired output type.
    input_path, out_type = prepare_cli_options(args)
    # Create a path manager to handle file or directory inputs.
    pm = create_path_manager(input_path, out_type)
    files_to_process, output_dest, source_type = pm.get_conversion_params()

    # Gather Excel options
    if args.sheet is None and args.range is None:
        common_excel_sheet, common_excel_range = get_excel_options_for_files(
            files_to_process
        )
    else:
        common_excel_sheet, common_excel_range = args.sheet, args.range

    extra_kwargs = {}
    if out_type == "txt":
        extra_kwargs = prompt_for_txt_delimiter()

    # Open an in-memory DuckDB connection.
    with duckdb.connect(database=":memory:") as conn:
        if not ExcelUtils.load_extension(conn):
            return
        for f in files_to_process:
            detected = get_file_type_by_extension(f)
            if detected is None:
                logging.info(f"Skipping file with unsupported extension: {f.name}")
                continue
            # Use the CLI input type if provided; otherwise, use auto-detected type.
            in_type = (
                FILE_TYPE_ALIASES[args.input_type.lower()]
                if args.input_type
                else detected
            )
            if in_type == "excel":
                excel_sheet, excel_range = (common_excel_sheet, common_excel_range)
            else:
                excel_sheet, excel_range = args.sheet, args.range
            process_file(
                f,
                in_type,
                out_type,
                conn,
                excel_sheet,
                excel_range,
                output_dir=output_dest,
                **extra_kwargs,
            )


def main():
    try:
        args = parse_cli_arguments()
        convert(args)
    except Exception as e:
        logging.error(f"Conversion failed: {e}")


if __name__ == "__main__":
    main()
