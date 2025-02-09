#!/usr/bin/env python3
# /// script
# dependencies = [
#     "duckdb",
# ]
# ///

"""
Module for managing file and directory paths for file conversions.

This module defines classes to:
    - Detect if a given path is a file or a directory.
    - Infer the file type (for processing and for naming) from the file extension.
    - Generate an output file path (by changing the extension) or output directory name
      (by replacing the file‐type "alias" in the directory name) while preserving
      common capitalization conventions.

Special handling is provided for .txt files: they are processed like CSV files,
but when naming directories the literal "txt" is used.
"""

import re
from pathlib import Path
from typing import Optional, Dict
from collections import Counter


class BasePathManager:
    """
    Base class for path management.
    """

    # Mapping for processing: treat .txt as CSV so that conversion code works uniformly.
    ALLOWED_EXT_MAP: Dict[str, str] = {
        ".csv": "csv",
        ".txt": "csv",  # processing: treat txt like csv
        ".json": "json",
        ".parquet": "parquet",
        ".parq": "parquet",
        ".pq": "parquet",
        ".xlsx": "excel",
    }

    # Mapping for naming: keep the literal extension for naming purposes.
    NAMING_EXT_MAP: Dict[str, str] = {
        ".csv": "csv",
        ".txt": "txt",  # naming: keep txt as txt
        ".json": "json",
        ".parquet": "parquet",
        ".parq": "parquet",
        ".pq": "parquet",
        ".xlsx": "excel",
    }

    def __init__(self, input_path: Path, output_ext: str):
        self.input_path: Path = input_path
        self.output_ext: str = output_ext

        self.input_name: str = self.input_path.name
        self.input_dir: Path = self.input_path.parent

    @staticmethod
    def _replace_alias_in_string(text: str, old_alias: str, new_alias: str) -> str:
        """
        Replace all occurrences of old_alias in text with new_alias while preserving capitalization.
        If no occurrence is found, appends the new alias to the text.
        """
        pattern = re.compile(re.escape(old_alias), re.IGNORECASE)

        def replacer(match: re.Match) -> str:
            orig = match.group()
            if orig.isupper():
                return new_alias.upper()
            elif orig.islower():
                return new_alias.lower()
            elif orig[0].isupper() and orig[1:].islower():
                return new_alias.capitalize()
            else:
                return new_alias

        result, count = pattern.subn(replacer, text)
        if count == 0:
            result = f"{text} {new_alias}"
        return result


class FilePathManager(BasePathManager):
    """
    Class for managing file paths.

    For files, the output path is created by changing the file extension.
    """

    def __init__(self, input_path: Path, output_ext: str):
        super().__init__(input_path, output_ext)
        # Get the original extension without the dot (preserving its case)
        self.file_ext: str = self.input_path.suffix.lstrip(".")
        self.output_path: Path = self._generate_output_path()

    def _generate_output_path(self) -> Path:
        """
        Generate the output file path by changing the file's extension to the output_ext.
        """
        return self.input_path.with_suffix(f".{self.output_ext}")


class DirectoryPathManager(BasePathManager):
    """
    Class for managing directory paths.

    The output directory name is generated by searching the input directory name
    for the file-type alias (derived from the majority of files) and replacing it with
    the provided output extension (while preserving capitalization). If no alias is found,
    the output extension is appended.
    """

    def __init__(self, input_path: Path, output_ext: str):
        super().__init__(input_path, output_ext)
        self.input_alias: Optional[str] = self._infer_majority_alias()
        self.output_name: str = self._generate_output_name()
        self.output_path: Path = self.input_dir / self.output_name

    def _infer_majority_alias(self) -> Optional[str]:
        """
        Infer the majority file-type alias for naming from files in the directory using NAMING_EXT_MAP.
        Returns:
            The most common alias (e.g., 'csv' or 'txt') or None if no valid files are found.
        """
        if not self.input_path.is_dir():
            return None

        aliases = []
        for file_path in self.input_path.iterdir():
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in self.NAMING_EXT_MAP:
                    aliases.append(self.NAMING_EXT_MAP[suffix])
        if not aliases:
            return None
        counter = Counter(aliases)
        majority_alias, _ = counter.most_common(1)[0]
        return majority_alias

    def _generate_output_name(self) -> str:
        """
        Generate the output directory name by replacing the input alias with the output extension.
        Uses the helper method _replace_alias_in_string to preserve capitalization.
        """
        if self.input_alias:
            return self._replace_alias_in_string(
                self.input_name, self.input_alias, self.output_ext
            )
        else:
            return f"{self.input_name} {self.output_ext}"


def create_path_manager(input_path: Path, output_ext: str) -> BasePathManager:
    """
    Factory function that returns an instance of FilePathManager or DirectoryPathManager
    based on whether input_path is a file or directory.

    Args:
        input_path: The Path object for the input file or directory.
        output_ext: The desired output extension or alias.

    Returns:
        An instance of FilePathManager (if input_path is a file) or
        DirectoryPathManager (if input_path is a directory).
    """
    if input_path.is_file():
        return FilePathManager(input_path, output_ext)
    else:
        return DirectoryPathManager(input_path, output_ext)
