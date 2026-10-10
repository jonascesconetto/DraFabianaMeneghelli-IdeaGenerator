"""Importação segura de uma exportação local da Meta."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path, PurePosixPath
import re
import shutil
import zipfile


class UnsafeArchiveError(ValueError):
    """O arquivo contém um caminho que escaparia do diretório de destino."""


def _safe_member_path(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    member = PurePosixPath(normalized)
    if (
        not normalized
        or member.is_absolute()
        or ".." in member.parts
        or re.match(r"^[A-Za-z]:", normalized)
    ):
        raise UnsafeArchiveError(f"Caminho inseguro no zip: {name!r}")
    return member


def acquire_zip(
    archive: Path,
    destination_root: Path,
    *,
    now: datetime | None = None,
) -> Path:
    """Extrai ``archive`` para um novo diretório carimbado em ``destination_root``."""

    archive = archive.expanduser()
    if not archive.is_file():
        raise FileNotFoundError(f"Arquivo zip não encontrado: {archive}")

    timestamp = (now or datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")
    destination = destination_root / timestamp

    with zipfile.ZipFile(archive) as source:
        members = [(info, _safe_member_path(info.filename)) for info in source.infolist()]
        if destination.exists():
            raise FileExistsError(
                f"O destino já existe; tente novamente em outro segundo: {destination}"
            )

        destination.mkdir(parents=True)
        try:
            for info, relative_path in members:
                target = destination.joinpath(*relative_path.parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(info) as incoming, target.open("wb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
        except BaseException:
            shutil.rmtree(destination)
            raise

    return destination
