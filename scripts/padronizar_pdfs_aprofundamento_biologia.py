from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


BASE_APROF_BIO_3B = Path(r"D:\PDF novos\APROFUNDAMENTO_EM_BIOLOGIA\EM\3_BIMESTRE")


def _normalizar_nome_arquivo(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = re.sub(r"[“”‘’´`]+", " ", texto)
    texto = re.sub(r'[\\/:*?"<>|]+', " ", texto)
    return re.sub(r"\s+", " ", texto).strip(" .-_")


def _dados_json(caminho_json: Path) -> dict:
    try:
        return json.loads(caminho_json.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _numero_aula(valor) -> int:
    match = re.search(r"\d{1,2}", str(valor or ""))
    return int(match.group(0)) if match else 0


def _destino_para_pdf(caminho_pdf: Path) -> tuple[Path, Path] | None:
    caminho_json = caminho_pdf.with_suffix(".json")
    dados = _dados_json(caminho_json)
    numero = _numero_aula(dados.get("numero_aula") or caminho_pdf.stem)
    titulo = str(dados.get("tema") or "").strip()
    if not numero or not titulo:
        return None
    nome_base = f"AULA_{numero:02d} - {_normalizar_nome_arquivo(titulo)}"
    return caminho_pdf.with_name(f"{nome_base}.pdf"), caminho_pdf.with_name(f"{nome_base}.json")


def _renomear_seguro(origem: Path, destino: Path) -> bool:
    if not origem.exists() or origem.resolve() == destino.resolve():
        return False
    if destino.exists():
        raise FileExistsError(f"Destino ja existe: {destino}")
    origem.rename(destino)
    return True


def padronizar_pasta(pasta: Path) -> dict[str, int]:
    pasta = pasta.resolve()
    base = BASE_APROF_BIO_3B.resolve()
    if base not in [pasta, *pasta.parents]:
        raise ValueError(f"Pasta fora da base esperada: {pasta}")

    renomeados_pdf = 0
    renomeados_json = 0
    ignorados = 0

    for caminho_pdf in sorted(pasta.glob("*.pdf")):
        destino = _destino_para_pdf(caminho_pdf)
        if not destino:
            ignorados += 1
            continue
        destino_pdf, destino_json = destino
        caminho_json = caminho_pdf.with_suffix(".json")

        if _renomear_seguro(caminho_pdf, destino_pdf):
            renomeados_pdf += 1
        if caminho_json.exists() and _renomear_seguro(caminho_json, destino_json):
            renomeados_json += 1

    return {
        "renomeados_pdf": renomeados_pdf,
        "renomeados_json": renomeados_json,
        "ignorados": ignorados,
    }


def main() -> None:
    print("Padronizacao de Aprofundamento em Biologia EM - 3o bimestre")
    for pasta in sorted(caminho for caminho in BASE_APROF_BIO_3B.iterdir() if caminho.is_dir()):
        resultado = padronizar_pasta(pasta)
        print(f"\nPasta: {pasta}")
        for chave, valor in resultado.items():
            print(f"  {chave}: {valor}")


if __name__ == "__main__":
    main()
