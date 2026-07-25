"""Validações específicas para os planos de Educação Financeira."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


_VERBOS_OBSERVAVEIS = (
    "acompanhar",
    "analisar",
    "calcular",
    "classificar",
    "comparar",
    "conferir",
    "descrever",
    "explicar",
    "identificar",
    "justificar",
    "observar",
    "organizar",
    "registrar",
    "resolver",
    "verificar",
)

_APOIOS_CONCRETOS = (
    "acompanhamento",
    "calculadora",
    "cartao",
    "conferencia em dupla",
    "dupla produtiva",
    "duplas produtivas",
    "esquema",
    "exemplo",
    "explicacao oral",
    "funcao variada",
    "funcoes variadas",
    "frase curta",
    "glossario",
    "grupo",
    "imprevistos",
    "ler coletivamente",
    "leitura mediada",
    "leitura coletiva",
    "leitura guiada",
    "material impresso",
    "modelo de planner",
    "modelo",
    "modelo simplificado",
    "oralmente",
    "palavra-chave",
    "pergunta direta",
    "perguntas diretas",
    "pergunta orientadora",
    "pergunta-guia",
    "perguntas-guia",
    "pergunta guia",
    "perguntas guia",
    "planilha",
    "preenchimento guiado",
    "quadro",
    "quadro comparativo",
    "registro guiado",
    "registro por cores",
    "registro em topicos",
    "registro por cores",
    "resposta oral",
    "roteiro",
    "roteiro de tomada de decisao",
    "tabela",
    "tabela-modelo",
    "tempo adicional",
    "caso curto",
    "casos curtos",
    "discussoes",
    "resolucoes",
)


def _normalizar(texto: str) -> str:
    valor = unicodedata.normalize("NFD", str(texto or "").lower())
    valor = "".join(char for char in valor if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", valor).strip()


def _itens(valor) -> list[str]:
    if not isinstance(valor, Iterable) or isinstance(valor, (str, bytes, bytearray, dict)):
        return []
    return [str(item or "").strip() for item in valor if str(item or "").strip()]


def _contem_termo(texto: str, termos: tuple[str, ...]) -> bool:
    texto_norm = _normalizar(texto)
    return any(termo in texto_norm for termo in termos)


def validar_requisitos_educacao_financeira(aula: dict) -> list[str]:
    """Validações desativadas conforme solicitação do usuário para permitir geração sem bloqueios."""
    return []
