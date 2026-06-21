from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

import pdfplumber

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.referencias_projeto_vida import titulos_referencia_projeto_vida_por_docx


BASE_AF_3B = Path(r"D:\PDF novos\PROJETO_DE_VIDA\AF\3_BIMESTRE")


def _normalizar_nome_arquivo(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = re.sub(r"[“”‘’´`]+", " ", texto)
    texto = re.sub(r'[\\/:*?"<>|]+', " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip(" .-_")
    return texto


def _localizar_docx_referencia(pasta: Path) -> Path | None:
    candidatos = sorted(
        [c for c in pasta.glob("Metodologias_Projeto_de_Vida*.docx") if not c.name.startswith("~$")],
        key=lambda c: c.name.lower(),
    )
    return candidatos[0] if candidatos else None


def _numero_aula_no_pdf(caminho_pdf: Path) -> int | None:
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages[:2]:
                texto = pagina.extract_text() or ""
                match = re.search(r"\bAula\s*(\d{1,2})\b", texto, flags=re.I)
                if match:
                    return int(match.group(1))
    except Exception:
        return None
    return None


def _arquivo_padronizado(pasta: Path, numero: int, titulo: str) -> Path:
    return pasta / f"AULA_{numero:02d} - {_normalizar_nome_arquivo(titulo)}.pdf"


def _arquivar_cache_antigo(pasta: Path) -> int:
    destino = pasta / "CACHE_ANTIGO_PRE_PADRONIZACAO"
    movidos = 0
    for caminho in sorted(pasta.glob("*.json")):
        if caminho.name.startswith("AULA_"):
            continue
        destino.mkdir(exist_ok=True)
        alvo = destino / caminho.name
        if alvo.exists():
            continue
        shutil.move(str(caminho), str(alvo))
        movidos += 1
    return movidos


def padronizar_pasta(pasta: Path) -> dict[str, int]:
    pasta = pasta.resolve()
    base_resolvida = BASE_AF_3B.resolve()
    if base_resolvida not in [pasta, *pasta.parents]:
        raise ValueError(f"Pasta fora da base esperada: {pasta}")

    docx = _localizar_docx_referencia(pasta)
    if not docx:
        raise FileNotFoundError(f"Sem DOCX de metodologia em: {pasta}")

    titulos = titulos_referencia_projeto_vida_por_docx(docx)
    if not titulos:
        raise ValueError(f"Sem aulas reconhecidas no DOCX: {docx}")

    renomeados = 0
    ignorados = 0

    for caminho_pdf in sorted(pasta.glob("*.pdf")):
        numero = _numero_aula_no_pdf(caminho_pdf)
        if not numero:
            ignorados += 1
            continue
        titulo = titulos.get(numero)
        if not titulo:
            ignorados += 1
            continue
        destino = _arquivo_padronizado(pasta, numero, titulo)
        if caminho_pdf.resolve() == destino.resolve():
            continue
        if destino.exists():
            ignorados += 1
            continue
        caminho_pdf.rename(destino)
        renomeados += 1

    cache_movido = _arquivar_cache_antigo(pasta)
    return {
        "renomeados": renomeados,
        "cache_movido": cache_movido,
        "ignorados": ignorados,
    }


def main() -> None:
    pastas = [BASE_AF_3B / nome for nome in ("6_ANO", "7_ANO", "8_ANO", "9_ANO")]
    print("Padronizacao de Projeto de Vida AF - 3o bimestre")
    for pasta in pastas:
        resultado = padronizar_pasta(pasta)
        print(f"\nPasta: {pasta}")
        for chave, valor in resultado.items():
            print(f"  {chave}: {valor}")


if __name__ == "__main__":
    main()
