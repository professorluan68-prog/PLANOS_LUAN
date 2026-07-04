from __future__ import annotations

import argparse
from pathlib import Path
import sys

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from core.extracao_palavras_chave_pdf import gerar_docx_palavras_chave, processar_pasta_pdfs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrai palavras-chave de uma pasta de PDFs pedagógicos e gera um DOCX de esboços."
    )
    parser.add_argument("--pasta", required=True, help="Pasta com os PDFs da turma.")
    parser.add_argument("--saida", required=True, help="Caminho do DOCX de saída.")
    parser.add_argument("--titulo", default="Esboço de palavras-chave", help="Título principal do DOCX.")
    parser.add_argument("--subtitulo", default="", help="Subtítulo do DOCX.")
    parser.add_argument(
        "--pasta-docx-auxiliares",
        default="",
        help="Pasta opcional para salvar os DOCX auxiliares gerados via pdf2docx.",
    )
    args = parser.parse_args()

    pasta = Path(args.pasta)
    pasta_aux = Path(args.pasta_docx_auxiliares) if str(args.pasta_docx_auxiliares or "").strip() else None
    aulas = processar_pasta_pdfs(pasta, pasta_docx_auxiliares=pasta_aux)
    if not aulas:
        raise FileNotFoundError(f"Nenhum PDF encontrado em {pasta}")

    saida = gerar_docx_palavras_chave(
        aulas,
        args.saida,
        titulo_documento=args.titulo,
        subtitulo=args.subtitulo,
    )

    print(saida)


if __name__ == "__main__":
    main()
