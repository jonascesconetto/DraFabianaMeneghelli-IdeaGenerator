"""Caminhos do pipeline, sempre relativos ao diretório de execução."""

from pathlib import Path


def data_dir(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / "data"


def raw_dir(root: Path | None = None) -> Path:
    return data_dir(root) / "raw"


def database_path(root: Path | None = None) -> Path:
    return data_dir(root) / "salvos.db"


def export_dir(root: Path | None = None) -> Path:
    return data_dir(root) / "export"
