"""Validacao defensiva de PDFs no modo automatico, sem uso de IA."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from core.helpers import numero_aula_pdf
from core.lib.classificador import normalizar_texto, perfil_disciplina
from core.seletor_referencias import referencia_docx_por_perfil


@dataclass(frozen=True)
class ResultadoValidacaoPDF:
    caminho: Path
    valido: bool
    motivos: tuple[str, ...]
    numero_pdf: int | None = None
    score: int = 0


@dataclass(frozen=True)
class ResultadoValidacaoLotePDF:
    validos: tuple[ResultadoValidacaoPDF, ...]
    suspeitos: tuple[ResultadoValidacaoPDF, ...]


_STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "ensino",
    "medio",
    "fundamental",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "para",
    "por",
    "que",
    "serie",
    "sobre",
    "um",
    "uma",
}

_ALIASES_PERFIL = {
    "arte": ("arte", "artes"),
    "biologia": ("biologia",),
    "ciencias_ef": ("ciencias",),
    "educacao_financeira": ("educacao financeira", "financeira"),
    "fisica": ("fisica",),
    "geografia": ("geografia",),
    "historia": ("historia",),
    "ingles": ("lingua inglesa", "ingles", "english"),
    "leitura_redacao": ("redacao", "leitura"),
    "lideranca_oratoria": ("lideranca", "oratoria"),
    "lingua_portuguesa_ef": ("lingua portuguesa", "portugues"),
    "lingua_portuguesa_em": ("lingua portuguesa", "portugues"),
    "matematica": ("matematica",),
    "orientacao_estudos": ("orientacao de estudos", "orientacao estudos"),
    "projeto_de_vida": ("projeto de vida",),
    "quimica": ("quimica",),
    "sociologia": ("sociologia",),
    "tecnologia_inovacao": ("tecnologia e inovacao", "tecnologia", "inovacao"),
}


def _extrair_amostra_texto_pdf(caminho_pdf: Path, limite_paginas: int = 2, limite_chars: int = 4000) -> str:
    try:
        import pdfplumber

        partes = []
        with pdfplumber.open(str(caminho_pdf)) as pdf:
            for pagina in pdf.pages[:limite_paginas]:
                partes.append(pagina.extract_text() or "")
                if sum(len(parte) for parte in partes) >= limite_chars:
                    break
        return "\n".join(partes)[:limite_chars]
    except Exception:
        return ""


def _tokens_relevantes(texto: str) -> set[str]:
    normalizado = normalizar_texto(texto)
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalizado)
        if len(token) > 2 and token not in _STOPWORDS
    }


def _numero_bimestre(bimestre: str) -> int | None:
    match = re.search(r"[1-4]", str(bimestre or ""))
    return int(match.group(0)) if match else None


def _bimestre_esta_no_contexto(contexto_norm: str, numero: int) -> bool:
    return any(
        padrao in contexto_norm
        for padrao in (
            f"{numero} bimestre",
            f"{numero}o bimestre",
            f"{numero} b",
            f"b{numero}",
            f"bimestre {numero}",
        )
    )


def _contexto_tem_outro_bimestre(contexto_norm: str, numero: int) -> bool:
    return any(
        outro != numero and _bimestre_esta_no_contexto(contexto_norm, outro)
        for outro in range(1, 5)
    )


def _serie_esperada(turma: str) -> int | None:
    match = re.search(r"(?<!\d)([1-9])\s*(?:o|a|º|ª)?\s*(?:ano|serie|série)\b", str(turma or ""), flags=re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"(?<!\d)([1-9])\s*(?:o|a|º|ª)?\b", str(turma or ""), flags=re.I)
    return int(match.group(1)) if match else None


def _serie_esta_no_contexto(contexto_norm: str, serie: int) -> bool:
    return any(
        padrao in contexto_norm
        for padrao in (
            f"{serie} ano",
            f"{serie} serie",
            f"{serie}_ano",
            f"{serie}ano",
        )
    )


def _contexto_tem_outra_serie(contexto_norm: str, serie: int) -> bool:
    return any(
        outra != serie and _serie_esta_no_contexto(contexto_norm, outra)
        for outra in range(1, 10)
    )


def _referencia_para_pdf(caminho_pdf: Path, numero: int | None, disciplina: str, turma: str) -> dict | None:
    if not numero:
        return None
    perfil = perfil_disciplina(disciplina, turma=turma)
    try:
        return referencia_docx_por_perfil(str(caminho_pdf), str(numero), "", perfil)
    except Exception:
        return None


def _texto_referencia(referencia: dict | None) -> tuple[str, str]:
    if not referencia:
        return "", ""
    return (
        str(referencia.get("titulo") or "").strip(),
        str(referencia.get("habilidade") or "").strip(),
    )


def validar_pdf_contexto_sem_ia(
    caminho_pdf,
    *,
    disciplina: str,
    turma: str = "",
    bimestre: str = "",
    texto_pdf: str | None = None,
) -> ResultadoValidacaoPDF:
    """Confere se um PDF automatico parece pertencer ao contexto selecionado."""
    caminho = Path(caminho_pdf)
    numero = numero_aula_pdf(caminho)
    motivos: list[str] = []
    score = 0

    if numero is None:
        motivos.append("sem numero de aula reconhecivel no nome")
    else:
        score += 25

    texto = texto_pdf if texto_pdf is not None else _extrair_amostra_texto_pdf(caminho)
    if not texto.strip():
        motivos.append("nao foi possivel ler texto do PDF")

    contexto_original = f"{caminho.name} {texto}"
    contexto_norm = normalizar_texto(contexto_original)
    perfil = perfil_disciplina(disciplina, turma=turma)
    aliases = _ALIASES_PERFIL.get(perfil) or tuple(_tokens_relevantes(disciplina))
    if aliases and any(normalizar_texto(alias) in contexto_norm for alias in aliases):
        score += 25
    else:
        motivos.append("disciplina do PDF nao confere com o cadastro")

    bimestre_num = _numero_bimestre(bimestre)
    if bimestre_num:
        if _bimestre_esta_no_contexto(contexto_norm, bimestre_num):
            score += 15
        elif _contexto_tem_outro_bimestre(contexto_norm, bimestre_num):
            motivos.append("bimestre do PDF nao confere com o selecionado")

    serie = _serie_esperada(turma)
    if serie:
        if _serie_esta_no_contexto(contexto_norm, serie):
            score += 10
        elif _contexto_tem_outra_serie(contexto_norm, serie):
            motivos.append("serie/turma do PDF nao confere com o cadastro")

    referencia = _referencia_para_pdf(caminho, numero, disciplina, turma)
    titulo_ref, habilidade_ref = _texto_referencia(referencia)
    tokens_titulo = _tokens_relevantes(titulo_ref)
    tokens_habilidade = _tokens_relevantes(habilidade_ref)
    tokens_contexto = _tokens_relevantes(contexto_original)

    if tokens_titulo:
        intersecao_titulo = tokens_titulo & tokens_contexto
        if intersecao_titulo:
            score += 20
        elif len(tokens_titulo) >= 2 and score < 65:
            motivos.append("titulo da aula nao aparece no PDF")
    elif tokens_habilidade:
        intersecao_habilidade = tokens_habilidade & tokens_contexto
        if len(intersecao_habilidade) >= min(2, len(tokens_habilidade)):
            score += 10
        elif score < 65:
            motivos.append("habilidade da referencia nao aparece no PDF")

    valido = not motivos
    return ResultadoValidacaoPDF(
        caminho=caminho,
        valido=valido,
        motivos=tuple(motivos),
        numero_pdf=numero,
        score=score,
    )


def validar_lote_pdfs_contexto_sem_ia(
    arquivos,
    *,
    disciplina: str,
    turma: str = "",
    bimestre: str = "",
) -> ResultadoValidacaoLotePDF:
    validos: list[ResultadoValidacaoPDF] = []
    suspeitos: list[ResultadoValidacaoPDF] = []
    for arquivo in arquivos or []:
        resultado = validar_pdf_contexto_sem_ia(
            arquivo,
            disciplina=disciplina,
            turma=turma,
            bimestre=bimestre,
        )
        if resultado.valido:
            validos.append(resultado)
        else:
            suspeitos.append(resultado)

    return ResultadoValidacaoLotePDF(tuple(validos), tuple(suspeitos))
