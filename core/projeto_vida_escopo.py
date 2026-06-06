from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile

from config import ESCOPO_PROJETO_VIDA_PATH

ESCOPO_PV_PATH = ESCOPO_PROJETO_VIDA_PATH

_NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}


def _normalizar(texto: str = "") -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _repeticoes(elem, attr: str, limite: int = 200) -> int:
    valor = elem.attrib.get(f"{{{_NS['table']}}}{attr}")
    if not valor:
        return 1
    try:
        return min(int(valor), limite)
    except ValueError:
        return 1


def _texto_celula(celula) -> str:
    texto = " ".join("".join(celula.itertext()).split())
    if texto:
        return texto
    for attr in ("string-value", "value"):
        valor = celula.attrib.get(f"{{{_NS['office']}}}{attr}")
        if valor:
            return str(valor).strip()
    return ""


def _linhas_tabela(tabela, max_colunas: int = 14) -> list[list[str]]:
    linhas = []
    for linha in tabela.findall("table:table-row", _NS):
        repeticoes_linha = _repeticoes(linha, "number-rows-repeated", 20)
        celulas = []
        for celula in list(linha):
            if not (
                celula.tag.endswith("table-cell")
                or celula.tag.endswith("covered-table-cell")
            ):
                continue
            texto = _texto_celula(celula)
            for _ in range(_repeticoes(celula, "number-columns-repeated", max_colunas)):
                celulas.append(texto)
                if len(celulas) >= max_colunas:
                    break
            if len(celulas) >= max_colunas:
                break
        if any(celulas):
            for _ in range(repeticoes_linha):
                linhas.append(celulas)
    return linhas


def _normalizar_serie(turma: str = "") -> str:
    texto = _normalizar(turma)
    match = re.search(r"([123])", texto)
    return f"{match.group(1)}a" if match else ""


def _normalizar_bimestre(bimestre: str = "") -> str:
    match = re.search(r"([1-4])", str(bimestre or ""))
    return f"{match.group(1)}o" if match else ""


def _normalizar_aula(aula) -> str:
    match = re.search(r"\b(\d{1,3})\b", str(aula or ""))
    return str(int(match.group(1))) if match else ""


def _compactar_texto(texto: str = "") -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    texto = re.sub(r"\s*â€¢\s*", " â€¢ ", texto)
    return texto.strip(" .;-")


def _itens(texto: str = "") -> list[str]:
    texto = _compactar_texto(texto)
    if not texto:
        return []
    partes = [p.strip(" .;-") for p in re.split(r"\s*â€¢\s*", texto) if p.strip(" .;-")]
    if len(partes) <= 1:
        partes = [p.strip(" .;-") for p in re.split(r"(?<=[.!?])\s+", texto) if p.strip(" .;-")]
    return partes


def _frase_principal(texto: str = "", limite: int = 180) -> str:
    itens = _itens(texto)
    frase = itens[0] if itens else _compactar_texto(texto)
    frase = re.sub(r"\s+", " ", frase).strip(" .;-")
    if len(frase) > limite:
        frase = frase[:limite].rsplit(" ", 1)[0].strip(" .;-")
    while re.search(r"\b(?:a|as|o|os|um|uma|de|da|do|das|dos|em|para|por|com|e)$", frase, flags=re.I):
        frase = frase.rsplit(" ", 1)[0].strip(" .;-")
    return frase


def _habilidade_para_frase(habilidade: str = "") -> str:
    itens = _itens(habilidade)
    if not itens:
        return ""
    itens = [item.strip(" .;-").lower() for item in itens[:2] if item.strip(" .;-")]
    if len(itens) == 1:
        return itens[0]
    return " e ".join(itens)


def _minuscula_inicial(texto: str = "") -> str:
    texto = str(texto or "").strip()
    if not texto:
        return ""
    return texto[:1].lower() + texto[1:]


@lru_cache(maxsize=1)
def carregar_escopo_projeto_vida(caminho: str | None = None) -> list[dict[str, str]]:
    caminho_ods = Path(caminho) if caminho else ESCOPO_PV_PATH
    if not caminho_ods.exists():
        candidatos = sorted(caminho_ods.parent.glob("EM Escopo-sequ*.ods"))
        if candidatos:
            caminho_ods = candidatos[0]
    if not caminho_ods.exists():
        return []

    with ZipFile(caminho_ods) as arquivo:
        raiz = ET.fromstring(arquivo.read("content.xml"))

    tabela_pv = None
    for tabela in raiz.findall(".//table:table", _NS):
        nome = tabela.attrib.get(f"{{{_NS['table']}}}name", "")
        if _normalizar(nome) == "projeto de vida":
            tabela_pv = tabela
            break
    if tabela_pv is None:
        return []

    linhas = _linhas_tabela(tabela_pv)
    if not linhas:
        return []

    cabecalho = [_normalizar(coluna) for coluna in linhas[0]]
    registros = []
    for linha in linhas[1:]:
        item = {cabecalho[i]: linha[i].strip() for i in range(min(len(cabecalho), len(linha)))}
        if item.get("ciclo") and item.get("serie") and item.get("aula"):
            registros.append(
                {
                    "ciclo": item.get("ciclo", ""),
                    "serie": item.get("serie", ""),
                    "bimestre": item.get("bimestre", ""),
                    "aula": item.get("aula", ""),
                    "unidade_tematica": item.get("unidade tematica", ""),
                    "habilidade": item.get("habilidade", ""),
                    "objeto": item.get("objetos do conhecimento", ""),
                    "titulo": item.get("titulo", ""),
                    "conteudo": item.get("conteudo", ""),
                    "objetivos": item.get("objetivos", ""),
                }
            )
    return registros


def buscar_item_projeto_vida(turma: str, bimestre: str, numero_aula: str | int) -> dict[str, str]:
    serie = _normalizar_serie(turma)
    bim = _normalizar_bimestre(bimestre)
    aula = _normalizar_aula(numero_aula)
    if not serie or not bim or not aula:
        return {}

    for item in carregar_escopo_projeto_vida():
        if (
            _normalizar_serie(item.get("serie")) == serie
            and _normalizar_bimestre(item.get("bimestre")) == bim
            and _normalizar_aula(item.get("aula")) == aula
        ):
            return item
    return {}


def montar_aprendizagem_projeto_vida(item: dict[str, str]) -> str:
    habilidade = _habilidade_para_frase(item.get("habilidade", ""))
    objetivo = _frase_principal(item.get("objetivos", ""), limite=145)
    objetivo = re.sub(r",?\s*com o objetivo de\b.*$", "", objetivo, flags=re.I).strip(" .;-")
    objeto = _frase_principal(item.get("objeto", ""), limite=90)
    conteudo = _frase_principal(item.get("conteudo", ""), limite=90)

    foco = objeto or conteudo or item.get("titulo", "")
    partes = []
    if habilidade and objetivo:
        partes.append(f"Desenvolver {habilidade} ao {_minuscula_inicial(objetivo)}")
    elif habilidade:
        partes.append(f"Desenvolver {habilidade}")
    elif objetivo:
        partes.append(f"Desenvolver aprendizagens relacionadas a {_minuscula_inicial(objetivo)}")

    if foco:
        partes.append(f"com foco em {_minuscula_inicial(foco)}")

    texto = ", ".join(partes).strip()
    if not texto:
        return ""
    return texto.rstrip(".") + "."
