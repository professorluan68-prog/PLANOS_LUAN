"""Validações específicas para os planos de Educação Financeira."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


_VERBOS_OBSERVAVEIS = (
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
    "cartao",
    "esquema",
    "exemplo",
    "frase curta",
    "leitura mediada",
    "material impresso",
    "modelo",
    "pergunta orientadora",
    "planilha",
    "quadro",
    "registro guiado",
    "resposta oral",
    "roteiro",
    "tabela",
    "tempo adicional",
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
    """Retorna problemas que devem impedir a geração do Word em Educação Financeira."""
    disciplina = _normalizar(aula.get("disciplina", ""))
    if "educacao financeira" not in disciplina:
        return []

    problemas: list[str] = []
    acompanhamento = _itens(aula.get("acompanhamento"))
    acessibilidade = _itens(aula.get("acessibilidade"))

    if len(acompanhamento) != 3:
        problemas.append("Acompanhamento deve ter exatamente 3 itens.")
    else:
        for indice, item in enumerate(acompanhamento, start=1):
            if not item.startswith("☑"):
                problemas.append(f"Acompanhamento: item {indice} deve iniciar com ☑.")
            if not _contem_termo(item, _VERBOS_OBSERVAVEIS):
                problemas.append(
                    f"Acompanhamento: item {indice} precisa conter verbo observável "
                    "(ex.: observar, verificar, conferir ou identificar)."
                )

    if len(acessibilidade) != 3:
        problemas.append("Acessibilidade deve ter exatamente 3 itens.")
    else:
        for indice, item in enumerate(acessibilidade, start=1):
            if not item.startswith("☑"):
                problemas.append(f"Acessibilidade: item {indice} deve iniciar com ☑.")
            if not _contem_termo(item, _APOIOS_CONCRETOS):
                problemas.append(
                    f"Acessibilidade: item {indice} precisa indicar apoio concreto "
                    "(ex.: quadro, tabela, roteiro, planilha ou resposta oral)."
                )

    return problemas
