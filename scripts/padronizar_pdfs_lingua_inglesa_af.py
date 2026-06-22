from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

import pdfplumber

sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.referencias_lingua_inglesa import titulos_referencia_lingua_inglesa_por_docx


BASE_AF_3B = Path(r"D:\PDF novos\LINGUA_INGLESA\AF\3_BIMESTRE")


def _normalizar_nome_arquivo(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = re.sub(r"[“”‘’´`]+", " ", texto)
    texto = re.sub(r'[\\/:*?"<>|]+', " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip(" .-_")
    return texto


def _localizar_docx_referencia(pasta: Path) -> Path | None:
    candidatos = sorted(
        [c for c in pasta.glob("Metodologias_Lingua_Inglesa*.docx") if not c.name.startswith("~$")],
        key=lambda c: c.name.lower(),
    )
    return candidatos[0] if candidatos else None


def _texto_pdf(caminho_pdf: Path) -> str:
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            return "\n".join((pagina.extract_text() or "") for pagina in pdf.pages[:2])
    except Exception:
        return ""


def _numero_aula_no_pdf(caminho_pdf: Path) -> int | None:
    texto = _texto_pdf(caminho_pdf)
    match = re.search(r"\bAula\s*(\d{1,2})\b", texto, flags=re.I)
    if match:
        return int(match.group(1))
    match_nome = re.search(r"\bAULA[_\s-]*(\d{1,2})\b", caminho_pdf.stem, flags=re.I)
    if match_nome:
        return int(match_nome.group(1))
    return None


def _eh_pdf_trilha(caminho_pdf: Path) -> bool:
    texto = re.sub(r"\s+", " ", _texto_pdf(caminho_pdf))
    return "Trilha de aprendizagem individual" in texto


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


def _renomear_pdf(caminho_pdf: Path, destino: Path) -> bool:
    if caminho_pdf.resolve() == destino.resolve():
        return False
    if destino.exists():
        return False
    caminho_pdf.rename(destino)
    return True


def padronizar_pasta(pasta: Path) -> dict[str, int]:
    pasta = pasta.resolve()
    base_resolvida = BASE_AF_3B.resolve()
    if base_resolvida not in [pasta, *pasta.parents]:
        raise ValueError(f"Pasta fora da base esperada: {pasta}")

    docx = _localizar_docx_referencia(pasta)
    if not docx:
        raise FileNotFoundError(f"Sem DOCX de metodologia em: {pasta}")

    titulos = titulos_referencia_lingua_inglesa_por_docx(docx)
    if not titulos:
        raise ValueError(f"Sem aulas reconhecidas no DOCX: {docx}")

    numeros_trilha = [
        numero
        for numero, titulo in sorted(titulos.items())
        if re.sub(r"\s+", " ", titulo).strip().lower() == "trilha de aprendizagem individual"
    ]

    pdfs = sorted(pasta.glob("*.pdf"))
    trilhas = [pdf for pdf in pdfs if _eh_pdf_trilha(pdf)]
    trilhas_por_pdf = dict(zip(trilhas, numeros_trilha))

    renomeados = 0
    ignorados = 0

    for caminho_pdf in pdfs:
        if caminho_pdf in trilhas_por_pdf:
            numero = trilhas_por_pdf[caminho_pdf]
        else:
            numero = _numero_aula_no_pdf(caminho_pdf)
        if not numero:
            ignorados += 1
            continue
        titulo = titulos.get(numero)
        if not titulo:
            ignorados += 1
            continue
        destino = _arquivo_padronizado(pasta, numero, titulo)
        if _renomear_pdf(caminho_pdf, destino):
            renomeados += 1

    cache_movido = _arquivar_cache_antigo(pasta)
    return {
        "renomeados": renomeados,
        "cache_movido": cache_movido,
        "ignorados": ignorados,
        "trilhas_detectadas": len(trilhas),
        "trilhas_no_docx": len(numeros_trilha),
    }


def main() -> None:
    print("Padronizacao de Lingua Inglesa AF - 3o bimestre")
    for pasta in sorted(p for p in BASE_AF_3B.iterdir() if p.is_dir()):
        resultado = padronizar_pasta(pasta)
        print(f"\nPasta: {pasta}")
        for chave, valor in resultado.items():
            print(f"  {chave}: {valor}")


if __name__ == "__main__":
    main()
