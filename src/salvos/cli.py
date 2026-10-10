"""CLI única do pipeline de salvos."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import sys

from salvos.acquire import acquire_zip
from salvos.inspect import inspect_saved_files
from salvos.paths import raw_dir


Command = Callable[[argparse.Namespace], int]


def _acquire(args: argparse.Namespace) -> int:
    try:
        destination = acquire_zip(Path(args.archive), raw_dir())
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(destination)
    return 0


def _inspect(_: argparse.Namespace) -> int:
    try:
        print(inspect_saved_files(raw_dir()))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


def _stub(name: str) -> Command:
    def run(_: argparse.Namespace) -> int:
        print(f"O comando `{name}` ainda não foi implementado.", file=sys.stderr)
        return 2

    return run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="salvos", description="Organize localmente os salvos do Instagram."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    acquire = subparsers.add_parser("acquire", help="Importa uma exportação .zip")
    acquire.add_argument("archive", help="Caminho do arquivo .zip")
    acquire.set_defaults(handler=_acquire)

    inspect = subparsers.add_parser("inspect", help="Inspeciona o schema dos JSONs")
    inspect.set_defaults(handler=_inspect)

    for name, help_text in (
        ("ingest", "Carrega e normaliza os salvos"),
        ("report", "Mostra um raio-x do acervo"),
        ("triage", "Abre a interface local de triagem"),
        ("export", "Exporta itens curados"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.set_defaults(handler=_stub(name))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
