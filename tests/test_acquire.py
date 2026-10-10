from datetime import datetime
from pathlib import Path
import zipfile

import pytest

from salvos.acquire import UnsafeArchiveError, acquire_zip


def _make_zip(path: Path, members: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def test_acquire_extracts_to_timestamped_directory(tmp_path: Path) -> None:
    archive = tmp_path / "export.zip"
    _make_zip(archive, {"activity/saved_posts.json": "[]"})

    destination = acquire_zip(
        archive,
        tmp_path / "raw",
        now=datetime(2026, 10, 8, 12, 34, 56),
    )

    assert destination == tmp_path / "raw" / "20261008-123456"
    assert (destination / "activity" / "saved_posts.json").read_text() == "[]"


@pytest.mark.parametrize("name", ["../../outside.txt", "/absolute.txt", "C:\\escape.txt"])
def test_acquire_rejects_unsafe_paths_without_extracting(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "malicious.zip"
    _make_zip(archive, {"safe.txt": "safe", name: "bad"})
    raw = tmp_path / "raw"

    with pytest.raises(UnsafeArchiveError):
        acquire_zip(archive, raw, now=datetime(2026, 10, 8, 12, 34, 56))

    assert not raw.exists()
