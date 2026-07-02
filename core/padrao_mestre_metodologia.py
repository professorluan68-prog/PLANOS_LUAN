from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from typing import Any


DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass(frozen=True)
class PadraoMestreMetodologia:
    slug: str
    disciplina: str
    segmento: str
    inclui_habilidade_por_aula: bool
    quantidade_itens_acompanhamento: int = 3
    quantidade_itens_acessibilidade: int = 3
    etapas_preferenciais: tuple[str, ...] = ()
    ponto_de_partida: str = ""


PADRAO_MESTRE_GERAL = PadraoMestreMetodologia(
    slug="geral",
    disciplina="Geral",
    segmento="geral",
    inclui_habilidade_por_aula=False,
    etapas_preferenciais=(
        "Para começar",
        "Relembre",
        "Foco no conteúdo",
        "Na prática",
        "Encerramento",
    ),
    ponto_de_partida="Partir do material real da aula e preservar a ordem efetiva das etapas.",
)


PADROES_MESTRES: dict[str, PadraoMestreMetodologia] = {
    "lingua_portuguesa_fundamental": PadraoMestreMetodologia(
        slug="lingua_portuguesa_fundamental",
        disciplina="Língua Portuguesa",
        segmento="Ensino Fundamental - anos finais",
        inclui_habilidade_por_aula=False,
        etapas_preferenciais=(
            "Para começar",
            "Relembre",
            "Hora da leitura",
            "Foco no conteúdo",
            "Pause e responda",
            "Todo mundo escreve",
            "Na prática",
            "Socialização",
            "Encerramento",
        ),
        ponto_de_partida="Partir sempre de texto, leitura, gênero textual, interpretação, análise linguística, literatura ou produção textual.",
    ),
    "matematica_fundamental": PadraoMestreMetodologia(
        slug="matematica_fundamental",
        disciplina="Matemática",
        segmento="Ensino Fundamental - anos finais",
        inclui_habilidade_por_aula=True,
        etapas_preferenciais=(
            "Para começar",
            "Relembre",
            "Foco no conteúdo",
            "De olho no modelo",
            "Pause e responda",
            "Na prática",
            "Encerramento",
        ),
        ponto_de_partida="Partir de problema, procedimento, representação, justificativa e verificação.",
    ),
    "matematica_medio": PadraoMestreMetodologia(
        slug="matematica_medio",
        disciplina="Matemática",
        segmento="Ensino Médio",
        inclui_habilidade_por_aula=True,
        etapas_preferenciais=(
            "Para começar",
            "Relembre",
            "Foco no conteúdo",
            "De olho no modelo",
            "Pause e responda",
            "Na prática",
            "Encerramento",
        ),
        ponto_de_partida="Partir de conceito, modelagem, procedimento, análise e justificativa matemática.",
    ),
    "ciencias_fundamental_anos_finais": PadraoMestreMetodologia(
        slug="ciencias_fundamental_anos_finais",
        disciplina="Ciências",
        segmento="Ensino Fundamental - anos finais",
        inclui_habilidade_por_aula=False,
        etapas_preferenciais=(
            "Para começar",
            "Relembre",
            "Observação inicial",
            "Hora da leitura",
            "Foco no conteúdo",
            "Análise de dados",
            "Mão na massa",
            "Situação-problema",
            "Pause e responda",
            "Na prática",
            "Socialização",
            "Correção dialogada",
            "Encerramento",
        ),
        ponto_de_partida="Partir de fenômenos, modelos, investigação, evidências, experimentos ou situações-problema.",
    ),
}


MAPA_TITULOS_ETAPAS = {
    "analise de dados": "Análise de dados",
    "compartilhamento": "Compartilhamento",
    "correcao dialogada": "Correção dialogada",
    "de olho no modelo": "De olho no modelo",
    "encerramento": "Encerramento",
    "estudo de caso": "Estudo de caso",
    "foco no conteudo": "Foco no conteúdo",
    "hora da leitura": "Hora da leitura",
    "mao na massa": "Mão na massa",
    "na pratica": "Na prática",
    "observacao inicial": "Observação inicial",
    "para comecar": "Para começar",
    "pause e responda": "Pause e responda",
    "planejamento da apresentacao": "Planejamento da apresentação",
    "relembre": "Relembre",
    "revisao com colega": "Revisão com colega",
    "situacao problema": "Situação-problema",
    "situacao-problema": "Situação-problema",
    "socializacao": "Socialização",
    "todo mundo escreve": "Todo mundo escreve",
    "vocabulario": "Vocabulário",
}


def _normalizar_espacos(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", texto)


def _normalizar_chave(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _eh_turma_fundamental(turma: str) -> bool:
    return bool(re.search(r"\b(?:6|7|8|9)\s*(?:ano|a|b|c|d|e)?\b", _normalizar_chave(turma)))


def _eh_turma_medio(turma: str) -> bool:
    return bool(re.search(r"\b(?:1|2|3)\s*(?:ano|em|a|b|c|d|e)?\b", _normalizar_chave(turma)))


def inferir_turma_de_caminho(caminho: str | Path) -> str:
    caminho_str = str(caminho or "")
    match = re.search(r"([1-9])[_\s-]*ANO", caminho_str, flags=re.I)
    if match:
        return f"{match.group(1)} ano"
    return ""


def resolver_padrao_mestre(disciplina: str = "", turma: str = "") -> PadraoMestreMetodologia:
    chave_disciplina = _normalizar_chave(disciplina)
    turma_inferida = turma or ""

    if "portugues" in chave_disciplina or "lingua portuguesa" in chave_disciplina:
        return PADROES_MESTRES["lingua_portuguesa_fundamental"] if _eh_turma_fundamental(turma_inferida) else PADRAO_MESTRE_GERAL
    if "matematica" in chave_disciplina:
        if _eh_turma_fundamental(turma_inferida):
            return PADROES_MESTRES["matematica_fundamental"]
        if _eh_turma_medio(turma_inferida):
            return PADROES_MESTRES["matematica_medio"]
    if "ciencias" in chave_disciplina or chave_disciplina == "ciencia":
        return PADROES_MESTRES["ciencias_fundamental_anos_finais"]
    return PADRAO_MESTRE_GERAL


def extrair_paragrafos_docx(caminho_docx: str | Path) -> list[str]:
    caminho = str(caminho_docx or "")
    paragrafos = _extrair_paragrafos_docx_python_docx(caminho)
    if paragrafos:
        return paragrafos
    return _extrair_paragrafos_docx_ooxml(caminho)


def _extrair_paragrafos_docx_python_docx(caminho_docx: str) -> list[str]:
    try:
        from docx import Document
    except Exception:
        return []

    try:
        doc = Document(caminho_docx)
    except Exception:
        return []

    return [
        _normalizar_espacos(paragrafo.text)
        for paragrafo in doc.paragraphs
        if _normalizar_espacos(paragrafo.text)
    ]


def _extrair_paragrafos_docx_ooxml(caminho_docx: str) -> list[str]:
    try:
        with zipfile.ZipFile(caminho_docx) as arquivo_docx:
            xml = arquivo_docx.read("word/document.xml")
    except Exception:
        return []

    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return []

    paragrafos: list[str] = []
    for paragrafo in raiz.findall(".//w:body//w:p", DOCX_NS):
        partes = []
        for no_texto in paragrafo.findall(".//w:t", DOCX_NS):
            if no_texto.text:
                partes.append(no_texto.text)
        texto = _normalizar_espacos("".join(partes))
        if texto:
            paragrafos.append(texto)
    return paragrafos


def normalizar_titulo_etapa(titulo: str) -> str:
    titulo_limpo = _normalizar_espacos(titulo)
    chave = _normalizar_chave(titulo_limpo)
    return MAPA_TITULOS_ETAPAS.get(chave, titulo_limpo)


def normalizar_itens_checklist(itens: list[str] | tuple[str, ...], quantidade_esperada: int = 3) -> list[str]:
    normalizados: list[str] = []
    for item in itens or []:
        texto = _normalizar_espacos(str(item or "").lstrip("☑ ").strip())
        if not texto:
            continue
        normalizados.append(f"☑ {texto}")
    return normalizados[:quantidade_esperada]


def alinhar_metodologia_ao_padrao_mestre(
    metodologia: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    disciplina: str = "",
    turma: str = "",
) -> list[dict[str, str]]:
    padrao = resolver_padrao_mestre(disciplina=disciplina, turma=turma)
    etapas_validas = {_normalizar_chave(etapa) for etapa in padrao.etapas_preferenciais}
    alinhada: list[dict[str, str]] = []

    for item in metodologia or []:
        titulo = normalizar_titulo_etapa(str((item or {}).get("titulo") or ""))
        texto = _normalizar_espacos(str((item or {}).get("texto") or ""))
        if not titulo or not texto:
            continue
        if etapas_validas and _normalizar_chave(titulo) not in etapas_validas:
            alinhada.append({"titulo": titulo, "texto": texto})
            continue
        alinhada.append({"titulo": titulo, "texto": texto})
    return alinhada


def normalizar_referencia_pedagogica(
    aula: dict[str, Any],
    disciplina: str = "",
    turma: str = "",
) -> dict[str, Any]:
    padrao = resolver_padrao_mestre(disciplina=disciplina, turma=turma)
    referencia = dict(aula or {})
    referencia["metodologia"] = alinhar_metodologia_ao_padrao_mestre(
        referencia.get("metodologia") or [],
        disciplina=disciplina,
        turma=turma,
    )
    referencia["acompanhamento"] = normalizar_itens_checklist(
        list(referencia.get("acompanhamento") or []),
        quantidade_esperada=padrao.quantidade_itens_acompanhamento,
    )
    referencia["acessibilidade"] = normalizar_itens_checklist(
        list(referencia.get("acessibilidade") or []),
        quantidade_esperada=padrao.quantidade_itens_acessibilidade,
    )
    referencia["padrao_mestre"] = padrao.slug
    return referencia
