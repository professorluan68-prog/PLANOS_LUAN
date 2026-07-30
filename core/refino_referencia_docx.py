"""Contrato de preservacao quando a IA aprimora uma referencia em DOCX."""

from __future__ import annotations

import re

from core.estrutura_metodologia import validar_etapas_obrigatorias
from core.lib.classificador import normalizar_texto


_TITULOS_ABERTURA = frozenset({"para comecar", "relembre"})
_PADRAO_RETORNO_GENERICO = re.compile(
    r"^(?:retomar|revisitar|dar continuidade|recuperar aprendizagens|reativar)"
    r"\b",
    flags=re.IGNORECASE,
)
_ANCORAS_CONCRETAS_ABERTURA = frozenset(
    {
        "video",
        "reportagem",
        "entrevista",
        "imagem",
        "mapa",
        "grafico",
        "tabela",
        "infografico",
        "podcast",
        "leitura",
        "situacao",
        "problema",
        "estudo",
        "caso",
        "experimento",
        "jogo",
        "desafio",
        "documentario",
        "musica",
        "cartaz",
        "roteiro",
    }
)


def _etapas_validas(valor: object) -> list[dict]:
    return [item for item in (valor or []) if isinstance(item, dict)]


def _abertura(etapas: list[dict]) -> str:
    for etapa in etapas:
        titulo = normalizar_texto(str(etapa.get("titulo") or ""))
        texto = re.sub(r"\s+", " ", str(etapa.get("texto") or "")).strip()
        if titulo in _TITULOS_ABERTURA and texto:
            return texto
    return ""


def _ancoras_concretas(texto: str) -> set[str]:
    palavras = set(re.findall(r"[a-z0-9]+", normalizar_texto(texto)))
    return palavras & _ANCORAS_CONCRETAS_ABERTURA


def _validar_abertura_refinada(abertura_docx: str, abertura_ia: str) -> tuple[bool, str]:
    if not abertura_docx or not abertura_ia:
        return True, ""

    docx_normalizado = normalizar_texto(abertura_docx)
    ia_normalizada = normalizar_texto(abertura_ia)
    ancoras_docx = _ancoras_concretas(abertura_docx)
    if (
        ancoras_docx
        and not _PADRAO_RETORNO_GENERICO.search(docx_normalizado)
        and _PADRAO_RETORNO_GENERICO.search(ia_normalizada)
    ):
        return (
            False,
            "A abertura da IA introduziu uma retomada generica que nao existe no DOCX.",
        )

    if ancoras_docx and not (ancoras_docx & _ancoras_concretas(abertura_ia)):
        lista_ancoras = ", ".join(sorted(ancoras_docx))
        return (
            False,
            f"A abertura da IA deixou de mencionar a acao ou recurso do DOCX: {lista_ancoras}.",
        )
    return True, ""


def validar_refino_ia_do_docx(
    referencia_docx: dict | None,
    plano_ia: dict | None,
) -> tuple[bool, str]:
    """Valida o refino da IA sem impor a ordem ou a contagem do DOCX."""
    etapas_docx = _etapas_validas((referencia_docx or {}).get("metodologia"))
    etapas_ia = _etapas_validas((plano_ia or {}).get("metodologia"))
    if not etapas_docx:
        return True, ""
    valido, motivo = validar_etapas_obrigatorias(etapas_ia)
    if not valido:
        return valido, motivo
    return _validar_abertura_refinada(
        _abertura(etapas_docx),
        _abertura(etapas_ia),
    )
