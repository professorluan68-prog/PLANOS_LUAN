from __future__ import annotations

import json
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path

import pdfplumber


BASE_DIR = Path(__file__).resolve().parent.parent
GUIA_DIR = Path(r"D:\GUIA_PRIORIZADO")
OUTPUT_DIR = BASE_DIR / "outputs" / "ae_portugues_em_2b"
OUTPUT_JSON = OUTPUT_DIR / "dados_ae_portugues_em_2b.json"
RUNTIME_DIR = BASE_DIR / "assets" / "ae_priorizado"
RUNTIME_JSON = RUNTIME_DIR / "portugues_em_2b.json"

COLS = {
    "ae": (0, 190),
    "habilidade": (190, 360),
    "pratica": (350, 460),
    "aulas": (460, 520),
}


def _normalizar(texto: str = "") -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _limpar_texto(texto: str = "") -> str:
    texto = str(texto or "").replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto).strip(" -|;")
    return texto


def _linhas_coluna(words: list[dict], x0: float, x1: float, top0: float, top1: float, tol: float = 3.5) -> str:
    itens = [
        w
        for w in words
        if w["x0"] >= x0 and w["x1"] <= x1 and w["top"] >= top0 and w["top"] < top1
    ]
    itens.sort(key=lambda w: (w["top"], w["x0"]))

    linhas: list[str] = []
    atual: list[dict] = []
    atual_top: float | None = None

    for item in itens:
        if atual_top is None or abs(item["top"] - atual_top) <= tol:
            atual.append(item)
            if atual_top is None:
                atual_top = item["top"]
        else:
            atual.sort(key=lambda x: x["x0"])
            linhas.append(" ".join(i["text"] for i in atual))
            atual = [item]
            atual_top = item["top"]

    if atual:
        atual.sort(key=lambda x: x["x0"])
        linhas.append(" ".join(i["text"] for i in atual))

    return _limpar_texto(" ".join(linhas))


def _encontrar_pdf_portugues_em() -> Path:
    for pasta in GUIA_DIR.iterdir():
        if pasta.is_dir() and "PORTUG" in pasta.name.upper() and pasta.name.endswith("_EM"):
            arquivos = sorted(pasta.glob("*.pdf"))
            if arquivos:
                return arquivos[0]
    raise FileNotFoundError("Nao encontrei o PDF recortado de PORTUGUES_EM em D:\\GUIA_PRIORIZADO.")


def _pratica_limpa(texto: str) -> str:
    texto = _limpar_texto(texto)
    padroes = [
        r"An[aá]lise lingu[ií]stica/?sem[ií][oó]tica",
        r"Escrita e Oralidade",
        r"Oralidade e Escrita",
        r"Escrita",
        r"Leitura",
        r"Oralidade",
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.I)
        if match:
            valor = match.group(0)
            if _normalizar(valor).startswith("analise"):
                return "Análise linguística/semiótica"
            return valor[:1].upper() + valor[1:]
    return texto


def _codigo_ae(texto: str) -> str:
    match = re.search(r"\bAE\s*(\d+)\b", texto, flags=re.I)
    return f"AE{match.group(1)}" if match else ""


def _texto_ae(texto: str) -> str:
    return _limpar_texto(re.sub(r"^\s*AE\s*\d+\s*-\s*", "", texto, flags=re.I))


def _texto_habilidade(texto: str, codigo: str) -> str:
    texto = _limpar_texto(texto)
    if codigo:
        texto = re.sub(rf"^\s*{re.escape(codigo)}\s*-\s*", "", texto, flags=re.I)
    texto = re.sub(r"^\s*-\s*", "", texto)
    return _limpar_texto(texto)


def _serie_da_pagina(primeira_linha: str) -> str:
    base = _normalizar(primeira_linha)
    match = re.search(r"\b([123])a serie\b.*?\b2o bimestre\b", base)
    if not match:
        return ""
    return f"{match.group(1)}ª Série"


def _lista_aulas(texto: str) -> list[int]:
    return [int(valor) for valor in re.findall(r"\d{1,3}", str(texto or ""))]


def _chave_lookup(serie: str, aula_numero: int) -> str:
    serie_base = _normalizar(serie).replace(" ", "_")
    return f"portugues_em|2|{serie_base}|{aula_numero}"


def _unicos_ordenados(valores: list[str]) -> list[str]:
    vistos = OrderedDict()
    for valor in valores:
        valor_limpo = _limpar_texto(valor)
        if valor_limpo and valor_limpo not in vistos:
            vistos[valor_limpo] = True
    return list(vistos.keys())


def extrair() -> dict:
    pdf_path = _encontrar_pdf_portugues_em()
    entradas_base: list[dict] = []

    with pdfplumber.open(str(pdf_path)) as doc:
        for pagina_idx, page in enumerate(doc.pages, start=1):
            texto_pagina = page.extract_text() or ""
            linhas = [linha for linha in texto_pagina.splitlines() if linha.strip()]
            primeira_linha = linhas[0] if linhas else ""
            serie = _serie_da_pagina(primeira_linha)
            if not serie:
                continue

            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            aes = [w for w in words if re.fullmatch(r"AE\d+", w["text"])]
            habilidades = [w for w in words if re.fullmatch(r"EM\d+[A-Z]{2}\d+[A-Z]?", w["text"])]
            aes.sort(key=lambda w: w["top"])
            habilidades.sort(key=lambda w: w["top"])

            if len(aes) != len(habilidades):
                raise ValueError(
                    f"Quantidade diferente de AE e habilidades na pagina {pagina_idx}: "
                    f"{len(aes)} AE(s) e {len(habilidades)} habilidade(s)."
                )

            for idx, (ae_word, hab_word) in enumerate(zip(aes, habilidades)):
                inicio = min(ae_word["top"], hab_word["top"]) - 2
                if idx + 1 < len(aes):
                    proximo_inicio = min(aes[idx + 1]["top"], habilidades[idx + 1]["top"]) - 2
                    fim = proximo_inicio - 4
                else:
                    fim = page.height - 5

                ae_completo = _linhas_coluna(words, *COLS["ae"], inicio, fim)
                habilidade_completa = _linhas_coluna(words, *COLS["habilidade"], inicio, fim)
                pratica = _pratica_limpa(_linhas_coluna(words, *COLS["pratica"], inicio, fim))
                aulas_bloco = _linhas_coluna(words, *COLS["aulas"], inicio, fim)

                codigo_ae = _codigo_ae(ae_completo)
                codigo_habilidade = hab_word["text"].strip()
                lista_aulas = _lista_aulas(aulas_bloco)

                entradas_base.append(
                    {
                        "disciplina": "Português",
                        "etapa": "EM",
                        "serie": serie,
                        "bimestre": "2º",
                        "bimestre_numero": 2,
                        "ae_codigo": codigo_ae,
                        "ae_texto": _texto_ae(ae_completo),
                        "ae_completo": ae_completo,
                        "habilidade_codigo": codigo_habilidade,
                        "habilidade_texto": _texto_habilidade(habilidade_completa, codigo_habilidade),
                        "habilidade_completa": habilidade_completa,
                        "pratica_linguagem": pratica,
                        "aulas_bloco": aulas_bloco,
                        "aulas_lista": lista_aulas,
                        "pagina_origem": pagina_idx,
                        "pdf_origem": str(pdf_path),
                    }
                )

    agrupado: OrderedDict[tuple[str, int], dict] = OrderedDict()
    for entrada in entradas_base:
        for aula_numero in entrada["aulas_lista"]:
            chave = (entrada["serie"], aula_numero)
            if chave not in agrupado:
                agrupado[chave] = {
                    "chave_lookup": _chave_lookup(entrada["serie"], aula_numero),
                    "disciplina": "Português",
                    "etapa": "EM",
                    "serie": entrada["serie"],
                    "bimestre": "2º",
                    "bimestre_numero": 2,
                    "aula_numero": aula_numero,
                    "ae_codigos": [],
                    "ae_textos": [],
                    "usar_ae": [],
                    "habilidade_codigos": [],
                    "habilidade_textos": [],
                    "praticas_linguagem": [],
                    "paginas_origem": [],
                    "pdf_origem": entrada["pdf_origem"],
                }

            item = agrupado[chave]
            item["ae_codigos"].append(entrada["ae_codigo"])
            item["ae_textos"].append(entrada["ae_texto"])
            item["usar_ae"].append(entrada["ae_completo"])
            item["habilidade_codigos"].append(entrada["habilidade_codigo"])
            item["habilidade_textos"].append(entrada["habilidade_texto"])
            item["praticas_linguagem"].append(entrada["pratica_linguagem"])
            item["paginas_origem"].append(str(entrada["pagina_origem"]))

    mapa_por_aula: list[dict] = []
    for _, item in agrupado.items():
        mapa_por_aula.append(
            {
                "chave_lookup": item["chave_lookup"],
                "disciplina": item["disciplina"],
                "etapa": item["etapa"],
                "serie": item["serie"],
                "bimestre": item["bimestre"],
                "bimestre_numero": item["bimestre_numero"],
                "aula_numero": item["aula_numero"],
                "ae_codigos": " | ".join(_unicos_ordenados(item["ae_codigos"])),
                "ae_textos": " | ".join(_unicos_ordenados(item["ae_textos"])),
                "usar_ae": " | ".join(_unicos_ordenados(item["usar_ae"])),
                "habilidade_codigos": " | ".join(_unicos_ordenados(item["habilidade_codigos"])),
                "habilidade_textos": " | ".join(_unicos_ordenados(item["habilidade_textos"])),
                "praticas_linguagem": " | ".join(_unicos_ordenados(item["praticas_linguagem"])),
                "paginas_origem": " | ".join(_unicos_ordenados(item["paginas_origem"])),
                "pdf_origem": item["pdf_origem"],
            }
        )

    return {
        "arquivo_fonte": str(pdf_path),
        "filtro": {
            "disciplina": "Português",
            "etapa": "EM",
            "bimestre": "2º",
        },
        "mapa_por_aula": mapa_por_aula,
        "entradas_base": entradas_base,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    payload = extrair()
    conteudo = json.dumps(payload, ensure_ascii=False, indent=2)
    OUTPUT_JSON.write_text(conteudo, encoding="utf-8")
    RUNTIME_JSON.write_text(conteudo, encoding="utf-8")
    print(OUTPUT_JSON)
    print(RUNTIME_JSON)


if __name__ == "__main__":
    main()
