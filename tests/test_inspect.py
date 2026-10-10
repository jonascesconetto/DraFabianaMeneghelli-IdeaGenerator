import json
from pathlib import Path

import pytest

from salvos.inspect import inspect_saved_files


def test_inspect_lists_nested_files_and_masks_two_examples(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    target = raw / "nested" / "saved_posts.json"
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps(
            {
                "saved_saved_media": [
                    {
                        "username": "usuario_secreto",
                        "href": "https://www.instagram.com/p/ABC123/?igsh=secret",
                        "title": "Texto particular",
                        "timestamp": 1700000000,
                    },
                    {
                        "username": "outra_pessoa",
                        "href": "https://instagram.com/reel/XYZ/",
                        "title": "Outra legenda",
                        "timestamp": 1700000001,
                    },
                    {"username": "terceiro_nao_deve_aparecer"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    output = inspect_saved_files(raw)

    assert "nested/saved_posts.json" in output
    assert '"timestamp": "number"' in output
    assert "usuario_secreto" not in output
    assert "Texto particular" not in output
    assert "ABC123" not in output
    assert "terceiro_nao_deve_aparecer" not in output
    assert "https://www.instagram.com/p/XXXX/" in output


def test_inspect_raises_when_no_saved_json_exists(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Nenhum JSON"):
        inspect_saved_files(tmp_path)
