from __future__ import annotations

import argparse
from pathlib import Path

from core.validacao_sidecars import exportar_relatorio_validacao_sidecars


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida sidecars JSON de planos e gera um relatorio CSV.",
    )
    parser.add_argument(
        "--base",
        default="D:\\PLANOS_LUAN",
        help="Pasta base onde os sidecars JSON serao procurados.",
    )
    parser.add_argument(
        "--saida",
        default="D:\\PLANOS_LUAN\\Auditoria_Estruturas\\relatorio_validacao_sidecars.csv",
        help="Arquivo CSV de saida.",
    )
    args = parser.parse_args()

    total = exportar_relatorio_validacao_sidecars(
        Path(args.base),
        Path(args.saida),
    )
    print(f"Sidecars analisados: {total}")
    print(f"Relatorio CSV: {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
