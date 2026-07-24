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
from core.referencias_fisica import (
    localizar_docx_referencia_fisica,
    referencia_fisica_por_pdf,
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
from core.seguranca_upload import nomes_pdf_original_possiveis
from core.referencias_docx_padrao import (
    carregar_referencias_docx_padrao,
    localizar_docx_referencia_padrao,
)

_LOCALIZADORES_REFERENCIA = {
    "educacao_financeira": localizar_docx_referencia,
    "biologia": localizar_docx_referencia_biologia,
    "ciencias_ef": localizar_docx_referencia_ciencias,
    "geografia": localizar_docx_referencia_geografia,
    "fisica": localizar_docx_referencia_fisica,
    "historia": localizar_docx_referencia_historia,
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
    "fisica": referencia_fisica_por_pdf,
    "historia": referencia_historia_por_pdf,
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
    "fisica": "docx_referencia_fisica",
    "historia": "docx_referencia_historia",
    "matematica": "docx_referencia_matematica",
    "lideranca_oratoria": "docx_referencia_lideranca_oratoria",
    "ingles": "docx_referencia_lingua_inglesa",
    "orientacao_estudos": "docx_referencia_orientacao_estudos",
    "projeto_de_vida": "docx_referencia_projeto_de_vida",
    "arte": "docx_referencia_arte",
    "quimica": "docx_referencia_quimica",
    "tecnologia_inovacao": "docx_referencia_tecnologia_inovacao",
    "geral": "docx_referencia_externa",
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


def _resolver_caminho_original(caminho_pdf: str, disciplina: str, turma: str) -> Path | None:
    caminho = Path(caminho_pdf)
    if not (caminho.parent.name.startswith("temp_") or "temp" in caminho.parent.name.lower()):
        return None
    
    try:
        from config import PDF_AULAS_DIR
        from core.helpers import normalizar_para_pasta
        import re
        
        disc_norm = normalizar_para_pasta(disciplina)
        pasta_disc = Path(PDF_AULAS_DIR) / disc_norm
        if not pasta_disc.exists():
            aliases_disciplina = {
                "ORIENTACAO_ESTUDOS": "ORIENTACAO_DE_ESTUDOS",
            }
            pasta_alias = aliases_disciplina.get(disc_norm)
            if pasta_alias:
                candidata = Path(PDF_AULAS_DIR) / pasta_alias
                if candidata.exists():
                    pasta_disc = candidata
        if not pasta_disc.exists():
            for d in Path(PDF_AULAS_DIR).iterdir():
                if d.is_dir() and normalizar_para_pasta(d.name) == disc_norm:
                    pasta_disc = d
                    break
        if not pasta_disc.exists():
            return None

        turma_norm = normalizar_para_pasta(turma)
        ano_str = ""
        m = re.search(r"(\d+)_?ANO", turma_norm)
        if m:
            ano_str = f"{m.group(1)}_ANO"
        
        nomes_originais = {
            nome.casefold() for nome in nomes_pdf_original_possiveis(caminho.name)
        }
        candidatos = [
            arquivo
            for arquivo in pasta_disc.rglob("*")
            if arquivo.is_file() and arquivo.name.casefold() in nomes_originais
        ]

        candidatos_unicos = sorted(
            {arquivo.resolve(): arquivo for arquivo in candidatos}.values(),
            key=lambda arquivo: str(arquivo).casefold(),
        )
        for arquivo in candidatos_unicos:
            if ano_str and ano_str in str(arquivo).upper():
                return arquivo
            if not ano_str:
                return arquivo
    except Exception:
        pass
    return None


def resolver_caminho_pdf_original(
    caminho_pdf: str,
    disciplina: str,
    turma: str = "",
) -> Path | None:
    """Retorna o PDF oficial correspondente a um upload temporario, quando houver.

    A funcao e publica para que o pipeline possa recuperar o contexto da pasta
    (por exemplo, ``CDP_EM``) antes de selecionar referencias pedagogicas.
    """
    return _resolver_caminho_original(caminho_pdf, disciplina, turma)

def localizar_docx_referencia_por_perfil(
    caminho_pdf: str,
    disciplina: str,
    turma: str = "",
):
    perfil = perfil_disciplina(disciplina, turma=turma)
    if not caminho_pdf:
        return None

    caminho_oficial = resolver_caminho_pdf_original(caminho_pdf, disciplina, turma)
    caminho_contexto = str(caminho_oficial or caminho_pdf)
    if caminho_oficial:
        caminho_pdf = caminho_contexto

    # Um PDF em CDP nunca pode herdar a metodologia regular encontrada na
    # pasta-pai. Quando o upload e temporario, ``caminho_oficial`` recupera a
    # pasta real e permite manter a mesma protecao.
    if eh_cdp_contextual_disciplina(caminho_contexto):
        return localizar_docx_referencia_cdp_contextual(caminho_contexto)

    referencia_padrao = localizar_docx_referencia_padrao(caminho_pdf)
    if referencia_padrao and referencia_padrao.name.casefold().startswith("metodologia_"):
        return referencia_padrao

    if eh_cdp_contextual_disciplina(disciplina):
        referencia_especial = localizar_docx_referencia_cdp_contextual(caminho_pdf)
        return referencia_especial or referencia_padrao
    if perfil in _PERFIS_PORTUGUES:
        referencia_especial = localizar_docx_referencia_portugues(caminho_pdf)
        if referencia_especial and _caminho_referencia_aceitavel(referencia_especial):
            return referencia_especial
        return referencia_padrao
    localizador = _LOCALIZADORES_REFERENCIA.get(perfil)
    if not localizador:
        return referencia_padrao
    referencia_especial = localizador(caminho_pdf)
    if referencia_especial and _caminho_referencia_aceitavel(referencia_especial):
        return referencia_especial
    return referencia_padrao


def _caminho_referencia_aceitavel(caminho) -> bool:
    nome = Path(caminho).name.casefold()
    return (
        not nome.startswith("~$")
        and "backup" not in nome
        and "metodologia" in nome
    )


def _numero_aula(valor) -> int:
    match = re.search(r"\d{1,3}", str(valor or ""))
    return int(match.group(0)) if match else 0


def _referencia_padrao_no_arquivo(caminho_docx, numero_aula):
    numero = _numero_aula(numero_aula)
    if not caminho_docx or not numero:
        return None, False
    referencias = carregar_referencias_docx_padrao(caminho_docx)
    if not referencias:
        return None, False
    referencia = referencias.get(numero)
    if not referencia:
        return None, True
    return {
        "numero": referencia.get("numero") or numero,
        "titulo": referencia.get("titulo", ""),
        "habilidade": referencia.get("habilidade", ""),
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(caminho_docx),
        "referencia_pedagogica_aplicada": True,
    }, True


def referencia_docx_por_perfil(
    caminho_pdf: str,
    numero_aula: str,
    tema: str,
    perfil: str,
):
    if not caminho_pdf:
        return None

    caminho_docx = localizar_docx_referencia_por_perfil(
        caminho_pdf,
        perfil,
        "",
    )

    caminho_oficial = resolver_caminho_pdf_original(caminho_pdf, perfil, "")
    caminho_contexto = str(caminho_oficial or caminho_pdf)
    if eh_cdp_contextual_disciplina(caminho_contexto):
        # No contexto CDP, somente a referencia CDP pode ser usada. Se ela
        # nao existir, o chamador seguira para o gerador contextual local/IA;
        # jamais fazemos fallback para o DOCX regular.
        from core.referencias_cdp_contextual import referencia_cdp_contextual_por_pdf

        return referencia_cdp_contextual_por_pdf(
            caminho_contexto,
            numero_aula,
            tema=tema,
        )

    referencia_padrao, estrutura_padrao_encontrada = _referencia_padrao_no_arquivo(
        caminho_docx,
        numero_aula,
    )
    if referencia_padrao:
        return referencia_padrao
    if estrutura_padrao_encontrada:
        return None
    if not caminho_docx:
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
    return _ORIGENS_METODOLOGIA.get(perfil, "docx_referencia_externa")


def perfil_docx_somente_colunas_pedagogicas(perfil: str) -> bool:
    return perfil in _PERFIS_DOCX_SOMENTE_COLUNAS


def perfil_prioriza_docx_sobre_cache_json(perfil: str) -> bool:
    return True


def referencia_docx_sobrescreve_metadados(perfil: str) -> bool:
    return not perfil_docx_somente_colunas_pedagogicas(perfil)


def deve_aplicar_referencia_docx_no_resultado_ia(
    perfil: str,
    plano_ia: dict | None,
) -> bool:
    if perfil_docx_somente_colunas_pedagogicas(perfil):
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
