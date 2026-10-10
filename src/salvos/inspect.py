"""Inspeção genérica e anonimizada dos JSONs de salvos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def find_saved_json_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.json")
        if "saved" in path.name.lower() and path.is_file()
    )


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _merge_shapes(values: list[Any]) -> Any:
    types = sorted({_type_name(value) for value in values})
    if types == ["object"]:
        keys = sorted({key for value in values for key in value})
        return {
            key: _merge_shapes([value[key] for value in values if key in value])
            for key in keys
        }
    if types == ["array"]:
        items = [item for value in values for item in value]
        return [_merge_shapes(items)] if items else ["unknown"]
    return " | ".join(types)


def describe_structure(data: Any) -> Any:
    return _merge_shapes([data])


def _mask_string(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/p/XXXX/"
    if not value:
        return value
    visible = value[:2]
    return f"{visible}***"


def mask_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: mask_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_value(item) for item in value]
    if isinstance(value, str):
        return _mask_string(value)
    return value


def example_records(data: Any, limit: int = 2) -> list[Any]:
    if isinstance(data, list):
        return data[:limit]
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value:
                return value[:limit]
        return [data]
    return [data]


def inspect_saved_files(root: Path) -> str:
    files = find_saved_json_files(root)
    if not files:
        raise FileNotFoundError(
            "Nenhum JSON de salvos foi encontrado. Baixe a exportação JSON da Meta "
            "e importe o zip com `salvos acquire <arquivo.zip>`."
        )

    sections: list[str] = []
    for path in files:
        with path.open(encoding="utf-8") as source:
            data = json.load(source)
        relative = path.relative_to(root)
        structure = json.dumps(
            describe_structure(data), ensure_ascii=False, indent=2, sort_keys=True
        )
        examples = json.dumps(
            [mask_value(item) for item in example_records(data)],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        sections.append(
            f"Arquivo: {relative}\nEstrutura de chaves/tipos:\n{structure}\n"
            f"Exemplos anonimizados:\n{examples}"
        )
    return "\n\n".join(sections)
