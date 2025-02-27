#!/usr/bin/env python3
"""
Module that defines conversion functions for DuckConvert.

This module maps (input_type, output_type) pairs to functions that perform
file conversions using DuckDB's Python API. Excel-specific conversions use
helpers from excel_utils.
"""

from pathlib import Path
from typing import Callable, Any, Dict, Tuple
import duckdb
import excel_utils as ex


# --- Helper functions for generic exports ---


def export_txt_generic(
    conn: duckdb.DuckDBPyConnection,
    read_func: Callable[[str], Any],
    file: Path,
    out_file: Path,
    **kwargs,
) -> None:
    """
    Generic exporter for TXT files.
    Prompts for a delimiter if one is not provided.
    """
    delimiter = kwargs.get("delimiter")
    if delimiter is None:
        answer = (
            input(
                "For TXT export, choose t for tab separated or c for comma separated: "
            )
            .strip()
            .lower()
        )
        delimiter = "\t" if answer == "t" else ","
    read_func(str(file.resolve())).write_csv(str(out_file.resolve()), sep=delimiter)


def export_tsv_generic(
    conn: duckdb.DuckDBPyConnection,
    read_func: Callable[[str], Any],
    file: Path,
    out_file: Path,
    **kwargs,
) -> None:
    """
    Generic exporter for TSV files.
    Uses tab as the delimiter.
    """
    read_func(str(file.resolve())).write_csv(str(out_file.resolve()), sep="\t")


# --- CSV conversions ---


def csv_to_parquet(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    relation = conn.read_csv(str(file.resolve()))
    relation.to_parquet(str(out_file.resolve()))


def csv_to_json(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    conn.read_csv(str(file.resolve())).sql(
        f"COPY (SELECT * FROM read_csv_auto('{file.resolve()}')) TO '{out_file.resolve()}'"
    )


def csv_to_excel(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    ex.export_excel(conn, f"SELECT * FROM read_csv_auto('{file.resolve()}')", out_file)


def csv_to_tsv(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    export_tsv_generic(conn, conn.read_csv, file, out_file, **kwargs)


def csv_to_txt(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    export_txt_generic(conn, conn.read_csv, file, out_file, **kwargs)


# --- JSON conversions ---


def json_to_csv(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    conn.read_json(str(file.resolve())).write_csv(str(out_file.resolve()))


def json_to_parquet(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    conn.read_json(str(file.resolve())).write_parquet(str(out_file.resolve()))


def json_to_excel(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    ex.export_excel(conn, f"SELECT * FROM read_json('{file.resolve()}')", out_file)


def json_to_tsv(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    export_tsv_generic(conn, conn.read_json, file, out_file, **kwargs)


def json_to_txt(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    export_txt_generic(conn, conn.read_json, file, out_file, **kwargs)


# --- Parquet conversions ---


def parquet_to_csv(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    conn.from_parquet(str(file.resolve())).write_csv(str(out_file.resolve()))


def parquet_to_json(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    conn.from_parquet(str(file.resolve())).sql(
        f"COPY (SELECT * FROM read_parquet('{file.resolve()}')) TO '{out_file.resolve()}'"
    )


def parquet_to_excel(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    ex.export_excel(conn, f"SELECT * FROM read_parquet('{file.resolve()}')", out_file)


def parquet_to_tsv(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    export_tsv_generic(conn, conn.from_parquet, file, out_file, **kwargs)


def parquet_to_txt(
    conn: duckdb.DuckDBPyConnection, file: Path, out_file: Path, **kwargs
) -> None:
    export_txt_generic(conn, conn.from_parquet, file, out_file, **kwargs)


# --- Excel conversions ---


def excel_to_csv(
    conn: duckdb.DuckDBPyConnection,
    file: Path,
    out_file: Path,
    sheet=None,
    range_=None,
    **kwargs,
) -> None:
    query = (
        f"SELECT * FROM read_xlsx('{str(file.resolve())}', all_varchar = 'true'"
        f"{ex._build_excel_options(sheet, range_)})"
    )
    conn.sql(query).write_csv(str(out_file.resolve()))


def excel_to_parquet(
    conn: duckdb.DuckDBPyConnection,
    file: Path,
    out_file: Path,
    sheet=None,
    range_=None,
    **kwargs,
) -> None:
    ex.export_excel_with_inferred_types(
        conn, file, out_file, sheet=sheet, range_=range_, fmt="parquet", **kwargs
    )


def excel_to_json(
    conn: duckdb.DuckDBPyConnection,
    file: Path,
    out_file: Path,
    sheet=None,
    range_=None,
    **kwargs,
) -> None:
    ex.export_excel_with_inferred_types(
        conn, file, out_file, sheet=sheet, range_=range_, fmt="json", **kwargs
    )


def excel_to_tsv(
    conn: duckdb.DuckDBPyConnection,
    file: Path,
    out_file: Path,
    sheet=None,
    range_=None,
    **kwargs,
) -> None:
    query = (
        f"SELECT * FROM read_xlsx('{str(file.resolve())}', all_varchar = 'true'"
        f"{ex._build_excel_options(sheet, range_)})"
    )
    conn.sql(query).write_csv(str(out_file.resolve()), sep="\t")


def excel_to_txt(
    conn: duckdb.DuckDBPyConnection,
    file: Path,
    out_file: Path,
    sheet=None,
    range_=None,
    **kwargs,
) -> None:
    delimiter = kwargs.get("delimiter")
    if delimiter is None:
        answer = (
            input(
                "For TXT export, choose T for tab separated or C for comma separated: "
            )
            .strip()
            .lower()
        )
        delimiter = "\t" if answer == "t" else ","
    query = (
        f"SELECT * FROM read_xlsx('{str(file.resolve())}', all_varchar = 'true'"
        f"{ex._build_excel_options(sheet, range_)})"
    )
    conn.sql(query).write_csv(str(out_file.resolve()), sep=delimiter)


# --- Conversion lookup dictionary ---
CONVERSION_FUNCTIONS: Dict[Tuple[str, str], Callable[..., Any]] = {
    # CSV conversions
    ("csv", "parquet"): csv_to_parquet,
    ("csv", "json"): csv_to_json,
    ("csv", "excel"): csv_to_excel,
    ("csv", "tsv"): csv_to_tsv,
    ("csv", "txt"): csv_to_txt,
    # JSON conversions
    ("json", "csv"): json_to_csv,
    ("json", "parquet"): json_to_parquet,
    ("json", "excel"): json_to_excel,
    ("json", "tsv"): json_to_tsv,
    ("json", "txt"): json_to_txt,
    # Parquet conversions
    ("parquet", "csv"): parquet_to_csv,
    ("parquet", "json"): parquet_to_json,
    ("parquet", "excel"): parquet_to_excel,
    ("parquet", "tsv"): parquet_to_tsv,
    ("parquet", "txt"): parquet_to_txt,
    # Excel conversions
    ("excel", "csv"): excel_to_csv,
    ("excel", "parquet"): excel_to_parquet,
    ("excel", "json"): excel_to_json,
    ("excel", "tsv"): excel_to_tsv,
    ("excel", "txt"): excel_to_txt,
}
