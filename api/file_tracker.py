"""
File Tracking Utility

This module provides functionality to track changes in markdown files for incremental
updates. It computes file hashes, detects changes, and maintains a cache of file metadata
for efficient tracking. The utility is designed for use in systems requiring frequent
document updates, such as retrieval-augmented generation (RAG) systems.
"""

from dataclasses import dataclass
import json
import hashlib
import os
import time
from typing import Dict, Tuple, List
from pathlib import Path


@dataclass
class FileMetadata:
    """
    Represents metadata for a tracked file.

    Attributes:
        file_path (str): The full path of the file.
        hash (str): The MD5 hash of the file content.
        last_modified (float): The last modified timestamp of the file.
        technology (str): The technology associated with the file.
        last_indexed (float): The timestamp of the last indexing.
    """

    file_path: str
    hash: str
    last_modified: float
    technology: str
    last_indexed: float


class FileTracker:
    """
    Tracks changes in files for incremental updates.

    Attributes:
        cache_file (str): Path to the cache file storing file metadata.
        file_metadata (Dict[str, FileMetadata]): A dictionary of file paths to their metadata.
    """

    def __init__(self, cache_file: str = ".rag_cache.json"):
        """
        Initialize the FileTracker.

        Args:
            cache_file (str): The path to the cache file. Defaults to ".rag_cache.json".
        """
        self.cache_file = cache_file
        self.file_metadata = self._load_cache()

    def _load_cache(self) -> Dict[str, FileMetadata]:
        """
        Load file tracking cache from disk.

        Returns:
            Dict[str, FileMetadata]: A dictionary containing file metadata.
        """
        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                return {k: FileMetadata(**v) for k, v in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_cache(self):
        """
        Save file tracking cache to disk.
        """
        with open(self.cache_file, "w") as f:
            data = {k: v.__dict__ for k, v in self.file_metadata.items()}
            json.dump(data, f, indent=2)

    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute the MD5 hash of the file content.

        Args:
            file_path (str): Path to the file to hash.

        Returns:
            str: The MD5 hash of the file content.
        """
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_modified_files(
        self, docs_path: str, technology: str
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Get lists of new, modified, and deleted files.

        Args:
            docs_path (str): The root directory to scan for files.
            technology (str): The technology associated with the files.

        Returns:
            Tuple[List[str], List[str], List[str]]: A tuple containing:
                - new_files: List of newly detected files.
                - modified_files: List of files that were modified.
                - deleted_files: List of files that were deleted.
        """
        current_files = set()
        new_files = []
        modified_files = []

        # Check for new and modified files
        for root, _, files in os.walk(docs_path):
            for file in files:
                if not file.endswith(".md"):
                    continue

                file_path = os.path.join(root, file)
                current_files.add(file_path)

                # Get file stats
                stats = os.stat(file_path)
                file_hash = self.compute_file_hash(file_path)

                if file_path not in self.file_metadata:
                    new_files.append(file_path)
                    self.file_metadata[file_path] = FileMetadata(
                        file_path=file_path,
                        hash=file_hash,
                        last_modified=stats.st_mtime,
                        technology=technology,
                        last_indexed=time.time(),
                    )
                else:
                    metadata = self.file_metadata[file_path]
                    if (
                        metadata.hash != file_hash
                        or metadata.last_modified < stats.st_mtime
                    ):
                        modified_files.append(file_path)
                        metadata.hash = file_hash
                        metadata.last_modified = stats.st_mtime
                        metadata.last_indexed = time.time()

        # Check for deleted files
        deleted_files = [
            f
            for f in self.file_metadata
            if f not in current_files and self.file_metadata[f].technology == technology
        ]

        # Remove deleted files from metadata
        for file_path in deleted_files:
            del self.file_metadata[file_path]

        self._save_cache()
        return new_files, modified_files, deleted_files
