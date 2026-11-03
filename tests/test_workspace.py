import os
import pytest
from agent_code_sandbox.workspace import EphemeralWorkspace, WorkspaceDiff


def test_ephemeral_workspace_lifecycle_and_diff():
    with EphemeralWorkspace() as ws:
        workspace_dir = ws.workspace_dir
        assert os.path.exists(workspace_dir)

        # Write initial file
        ws.write_file("config.json", '{"version": 1}')
        ws.snapshot_initial_state()

        # Mutate workspace: add one file, modify one file
        ws.write_file("output.txt", "Generated content")
        ws.write_file("config.json", '{"version": 2}')

        diff = ws.compute_diff()
        assert "output.txt" in diff.added_files
        assert "config.json" in diff.modified_files
        assert len(diff.deleted_files) == 0
        assert len(diff.state_hash) == 64

    # Workspace directory should be cleaned up upon context exit
    assert not os.path.exists(workspace_dir)
