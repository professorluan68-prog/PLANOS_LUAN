"""
Funções canônicas de normalização de texto para o sistema PLANOS_LUAN.
Todas as outras implementações de normalização devem importar daqui.
"""
from __future__ import annotations

import re
import unicodedata


def normalizar(
    texto: str,
    remover_pontuacao: bool = True,
    lower: bool = True,
) -> str:
    """
    Remove acentos, normaliza espaços e opcionalmente remove pontuação.

    Esta é a implementação canônica. Use esta função em vez de implementações
    locais em outros módulos.

    Args:
        texto: Texto a normalizar
        remover_pontuacao: Se True, remove pontuação (padrão: True)
        lower: Se True, converte para minúsculas (padrão: True)

    Returns:
        Texto normalizado
    """
    resultado = unicodedata.normalize("NFKD", str(texto or ""))
    resultado = "".join(ch for ch in resultado if not unicodedata.combining(ch))
    if remover_pontuacao:
        resultado = re.sub(r"[^\w\s]", " ", resultado, flags=re.UNICODE)
    resultado = re.sub(r"\s+", " ", resultado).strip()
    if lower:
        resultado = resultado.lower()
    return resultado


def normalizar_upper(texto: str) -> str:
    """Normaliza e converte para maiúsculas. Atalho para normalizar(lower=False).upper()"""
    return normalizar(texto, lower=False).upper()


def normalizar_preservar_pontuacao(texto: str) -> str:
    """Normaliza sem remover pontuação. Útil para textos pedagógicos."""
    return normalizar(texto, remover_pontuacao=False)
