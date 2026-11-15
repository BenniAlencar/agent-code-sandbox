"""
Ephemeral Workspace Isolation and Atomic File Mutation Diff Engine.
Tracks file creation, modifications, and deletions in a sandboxed scratchpad.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkspaceDiff:
    added_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    deleted_files: List[str] = field(default_factory=list)
    unified_diffs: Dict[str, str] = field(default_factory=dict)
    state_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "added_files": self.added_files,
            "modified_files": self.modified_files,
            "deleted_files": self.deleted_files,
            "unified_diffs": self.unified_diffs,
            "state_hash": self.state_hash,
        }


class EphemeralWorkspace:
    """
    Manages an isolated temporary directory for code execution.
    Calculates deterministic file diffs and state hashes.
    """

    def __init__(self, prefix: str = "benni_sandbox_") -> None:
        self.workspace_dir = tempfile.mkdtemp(prefix=prefix)
        self._initial_snapshot: Dict[str, str] = {}

    def __enter__(self) -> EphemeralWorkspace:
        self.snapshot_initial_state()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()

    def snapshot_initial_state(self) -> None:
        self._initial_snapshot = self._scan_files()

    def _hash_file(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _scan_files(self) -> Dict[str, str]:
        files_map: Dict[str, str] = {}
        for root, _, files in os.walk(self.workspace_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, self.workspace_dir)
                try:
                    files_map[rel_path] = self._hash_file(abs_path)
                except OSError:
                    pass
        return files_map

    def compute_diff(self) -> WorkspaceDiff:
        final_snapshot = self._scan_files()

        initial_keys = set(self._initial_snapshot.keys())
        final_keys = set(final_snapshot.keys())

        added = sorted(list(final_keys - initial_keys))
        deleted = sorted(list(initial_keys - final_keys))
        modified = []

        common = initial_keys.intersection(final_keys)
        for k in sorted(list(common)):
            if self._initial_snapshot[k] != final_snapshot[k]:
                modified.append(k)

        # Compute state hash
        hasher = hashlib.sha256()
        for k in sorted(list(final_keys)):
            hasher.update(f"{k}:{final_snapshot[k]}".encode("utf-8"))
        state_hash = hasher.hexdigest()

        return WorkspaceDiff(
            added_files=added,
            modified_files=modified,
            deleted_files=deleted,
            unified_diffs={},
            state_hash=state_hash,
        )

    def write_file(self, rel_path: str, content: str) -> str:
        target_path = os.path.join(self.workspace_dir, rel_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return target_path

    def read_file(self, rel_path: str) -> Optional[str]:
        target_path = os.path.join(self.workspace_dir, rel_path)
        if not os.path.exists(target_path):
            return None
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def cleanup(self) -> None:
        if os.path.exists(self.workspace_dir):
            try:
                shutil.rmtree(self.workspace_dir)
            except OSError:
                pass
