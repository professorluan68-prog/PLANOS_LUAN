from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.helpers import arquivo_parece_id_seduc, numero_aula_pdf
from core.referencias_educacao_financeira import titulos_referencia_por_docx


BASE_EM_3B = Path(r"D:\PDF novos\EDUCACAO_FINANCEIRA\EM\3_BIMESTRE")


def _normalizar_nome_arquivo(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = re.sub(r'[\\/:*?"<>|]+', " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip(" .-_")
    return texto


def _localizar_docx_referencia(pasta: Path) -> Path | None:
    candidatos = sorted(
        [c for c in pasta.glob("Metodologias_Educacao_Financeira*.docx") if not c.name.startswith("~$")],
        key=lambda c: c.name.lower(),
    )
    return candidatos[0] if candidatos else None


def _arquivo_padronizado(pasta: Path, numero: int, titulo: str) -> Path:
    return pasta / f"AULA_{numero:02d} - {_normalizar_nome_arquivo(titulo)}.pdf"


def _encontrar_pdf_aula(pasta: Path, numero: int) -> Path | None:
    candidatos = [
        caminho
        for caminho in pasta.glob("*.pdf")
        if not arquivo_parece_id_seduc(caminho) and numero_aula_pdf(caminho) == numero
    ]
    if not candidatos:
        return None
    return sorted(candidatos, key=lambda c: (len(c.name), c.name.lower()))[0]


def _mover_ids_seduc(pasta: Path) -> int:
    destino = pasta / "LEGADO_IDS_SEDUC"
    movidos = 0
    for caminho in sorted(pasta.glob("*.pdf")):
        if not arquivo_parece_id_seduc(caminho):
            continue
        destino.mkdir(exist_ok=True)
        alvo = destino / caminho.name
        if alvo.exists():
            continue
        shutil.move(str(caminho), str(alvo))
        movidos += 1
    return movidos


def _arquivar_cache_antigo(pasta: Path) -> int:
    destino = pasta / "CACHE_ANTIGO_PRE_PADRONIZACAO"
    movidos = 0
    for caminho in sorted(pasta.glob("AULA_*.json")):
        destino.mkdir(exist_ok=True)
        alvo = destino / caminho.name
        if alvo.exists():
            continue
        shutil.move(str(caminho), str(alvo))
        movidos += 1
    return movidos


def padronizar_pasta(pasta: Path) -> dict[str, int]:
    docx = _localizar_docx_referencia(pasta)
    if not docx:
        raise FileNotFoundError(f"Sem DOCX de metodologia em: {pasta}")

    titulos = titulos_referencia_por_docx(docx)
    if not titulos:
        raise ValueError(f"Sem aulas reconhecidas no DOCX: {docx}")

    renomeados = 0
    ignorados = 0

    for numero, titulo in sorted(titulos.items()):
        origem = _encontrar_pdf_aula(pasta, numero)
        if origem is None:
            ignorados += 1
            continue
        destino = _arquivo_padronizado(pasta, numero, titulo)
        if origem.resolve() == destino.resolve():
            continue
        if destino.exists():
            ignorados += 1
            continue
        origem.rename(destino)
        renomeados += 1

    ids_movidos = _mover_ids_seduc(pasta)
    cache_movido = _arquivar_cache_antigo(pasta)
    return {
        "renomeados": renomeados,
        "ids_movidos": ids_movidos,
        "cache_movido": cache_movido,
        "ignorados": ignorados,
    }


def main() -> None:
    pastas = [BASE_EM_3B / "1_ANO", BASE_EM_3B / "2_ANO"]
    print("Padronizacao de Educacao Financeira EM - 3o bimestre")
    for pasta in pastas:
        resultado = padronizar_pasta(pasta)
        print(f"\nPasta: {pasta}")
        for chave, valor in resultado.items():
            print(f"  {chave}: {valor}")


if __name__ == "__main__":
    main()
