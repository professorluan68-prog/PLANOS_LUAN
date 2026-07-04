from __future__ import annotations

import re
from pathlib import Path

from core.cdp.gerador_cdp import eh_cdp_contextual_disciplina
from core.lib.classificador import perfil_disciplina
from core.referencias_arte import localizar_docx_referencia_arte, referencia_arte_por_pdf
from core.referencias_biologia import (
    localizar_docx_referencia_biologia,
    referencia_biologia_por_pdf,
)
from core.referencias_cdp_contextual import localizar_docx_referencia_cdp_contextual
from core.referencias_ciencias import (
    localizar_docx_referencia_ciencias,
    referencia_ciencias_por_pdf,
)
from core.referencias_educacao_financeira import (
    localizar_docx_referencia,
    referencia_por_pdf,
)
from core.referencias_geografia import (
    localizar_docx_referencia_geografia,
    referencia_geografia_por_pdf,
)
from core.referencias_historia import (
    localizar_docx_referencia_historia,
    localizar_docx_referencia_historia_cdp,
    referencia_historia_por_pdf,
)
from core.referencias_lideranca_oratoria import (
    localizar_docx_referencia_lideranca_oratoria,
    referencia_lideranca_oratoria_por_pdf,
)
from core.referencias_lingua_inglesa import (
    localizar_docx_referencia_lingua_inglesa,
    referencia_lingua_inglesa_por_pdf,
)
from core.referencias_matematica import (
    localizar_docx_referencia_matematica,
    referencia_matematica_por_pdf,
)
from core.referencias_orientacao_estudos import (
    localizar_docx_referencia_orientacao_estudos,
    referencia_orientacao_estudos_por_pdf,
)
from core.referencias_portugues import (
    localizar_docx_referencia_portugues,
    referencia_portugues_por_pdf,
)
from core.referencias_projeto_vida import (
    localizar_docx_referencia_projeto_vida,
    referencia_projeto_vida_por_pdf,
)

_LOCALIZADORES_REFERENCIA = {
    "educacao_financeira": localizar_docx_referencia,
    "biologia": localizar_docx_referencia_biologia,
    "ciencias_ef": localizar_docx_referencia_ciencias,
    "geografia": localizar_docx_referencia_geografia,
    "matematica": localizar_docx_referencia_matematica,
    "lideranca_oratoria": localizar_docx_referencia_lideranca_oratoria,
    "ingles": localizar_docx_referencia_lingua_inglesa,
    "orientacao_estudos": localizar_docx_referencia_orientacao_estudos,
    "projeto_de_vida": localizar_docx_referencia_projeto_vida,
    "arte": localizar_docx_referencia_arte,
}

_REFERENCIAS_POR_PERFIL = {
    "educacao_financeira": referencia_por_pdf,
    "biologia": referencia_biologia_por_pdf,
    "ciencias_ef": referencia_ciencias_por_pdf,
    "geografia": referencia_geografia_por_pdf,
    "matematica": referencia_matematica_por_pdf,
    "lideranca_oratoria": referencia_lideranca_oratoria_por_pdf,
    "ingles": referencia_lingua_inglesa_por_pdf,
    "orientacao_estudos": referencia_orientacao_estudos_por_pdf,
    "projeto_de_vida": referencia_projeto_vida_por_pdf,
    "arte": referencia_arte_por_pdf,
}

_ORIGENS_METODOLOGIA = {
    "educacao_financeira": "docx_referencia_educacao_financeira",
    "biologia": "docx_referencia_biologia",
    "ciencias_ef": "docx_referencia_ciencias",
    "geografia": "docx_referencia_geografia",
    "matematica": "docx_referencia_matematica",
    "lideranca_oratoria": "docx_referencia_lideranca_oratoria",
    "ingles": "docx_referencia_lingua_inglesa",
    "orientacao_estudos": "docx_referencia_orientacao_estudos",
    "projeto_de_vida": "docx_referencia_projeto_de_vida",
    "arte": "docx_referencia_arte",
}

_PERFIS_PORTUGUES = {
    "lingua_portuguesa_ef",
    "lingua_portuguesa_em",
    "leitura_redacao",
}

_PERFIS_DOCX_SOMENTE_COLUNAS = {
    "lingua_portuguesa_ef",
    "lingua_portuguesa_em",
    "leitura_redacao",
    "matematica",
}

_PERFIS_PRIORIZAM_DOCX = {
    "ciencias_ef",
}

_PERFIS_APLICAM_DOCX_EM_IA = {
    "educacao_financeira",
    "ciencias_ef",
    "projeto_de_vida",
}


def localizar_docx_referencia_por_perfil(
    caminho_pdf: str,
    disciplina: str,
    turma: str = "",
):
    perfil = perfil_disciplina(disciplina, turma=turma)
    if not caminho_pdf:
        return None
    if eh_cdp_contextual_disciplina(disciplina):
        return localizar_docx_referencia_cdp_contextual(caminho_pdf)
    if perfil in _PERFIS_PORTUGUES:
        return localizar_docx_referencia_portugues(caminho_pdf)
    localizador = _LOCALIZADORES_REFERENCIA.get(perfil)
    if not localizador:
        return None
    return localizador(caminho_pdf)


def referencia_docx_por_perfil(
    caminho_pdf: str,
    numero_aula: str,
    tema: str,
    perfil: str,
):
    if not caminho_pdf:
        return None
    if perfil in _PERFIS_PORTUGUES:
        return referencia_portugues_por_pdf(caminho_pdf, numero_aula, tema=tema)
    resolvedor = _REFERENCIAS_POR_PERFIL.get(perfil)
    if not resolvedor:
        return None
    return resolvedor(caminho_pdf, numero_aula, tema=tema)


def origem_metodologia_por_referencia(perfil: str) -> str:
    if perfil in _PERFIS_PORTUGUES:
        return "docx_referencia_portugues"
    return _ORIGENS_METODOLOGIA.get(perfil, "")


def perfil_docx_somente_colunas_pedagogicas(perfil: str) -> bool:
    return perfil in _PERFIS_DOCX_SOMENTE_COLUNAS


def perfil_prioriza_docx_sobre_cache_json(perfil: str) -> bool:
    return perfil in _PERFIS_PRIORIZAM_DOCX


def referencia_docx_sobrescreve_metadados(perfil: str) -> bool:
    return not perfil_docx_somente_colunas_pedagogicas(perfil)


def deve_aplicar_referencia_docx_no_resultado_ia(
    perfil: str,
    plano_ia: dict | None,
) -> bool:
    if perfil_docx_somente_colunas_pedagogicas(perfil):
        return True
    if perfil in _PERFIS_APLICAM_DOCX_EM_IA:
        return True
    return not plano_ia or not plano_ia.get("metodologia")


def assinatura_docx_referencia(
    caminho_pdf: str,
    disciplina: str,
    turma: str = "",
) -> str:
    if not caminho_pdf:
        return ""
    try:
        docx = localizar_docx_referencia_por_perfil(caminho_pdf, disciplina, turma)
        if not docx:
            return ""
        stat = docx.stat()
        return f"{docx.name}|{stat.st_size}|{stat.st_mtime_ns}"
    except Exception:
        return ""


def itens_referencia_docx(referencia: dict | None, chave: str) -> list[str]:
    if not referencia:
        return []
    itens = []
    for item in list(referencia.get(chave) or [])[:3]:
        texto = str(item or "").strip()
        if not texto:
            continue
        if not texto.startswith("☑"):
            texto = f"☑ {texto.lstrip('☑ ').strip()}"
        itens.append(texto)
    return itens


def habilidade_referencia_docx(referencia: dict | None) -> str:
    if not referencia:
        return ""
    return re.sub(r"\s+", " ", str(referencia.get("habilidade") or "")).strip()


def material_aula_com_titulo(numero_aula: str, titulo: str) -> str:
    titulo = str(titulo or "").strip()
    if not titulo:
        return ""
    match = re.search(r"\d{1,2}", str(numero_aula or ""))
    if match:
        return f"AULA {int(match.group(0))} - {titulo}"
    return titulo


def sobrescrever_listas_pedagogicas_com_referencia(
    referencia: dict | None,
    acompanhamento: list[str],
    acessibilidade: list[str],
) -> tuple[list[str], list[str]]:
    acompanhamento_ref = itens_referencia_docx(referencia, "acompanhamento")
    acessibilidade_ref = itens_referencia_docx(referencia, "acessibilidade")
    if len(acompanhamento_ref) == 3:
        acompanhamento = acompanhamento_ref
    if len(acessibilidade_ref) == 3:
        acessibilidade = acessibilidade_ref
    return acompanhamento, acessibilidade
