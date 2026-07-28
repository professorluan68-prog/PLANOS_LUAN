"""Componentes compartilhados para leitura de referências pedagógicas em DOCX.

As disciplinas mantêm neste módulo apenas a localização dos seus arquivos e
as particularidades de leitura. A normalização, a pontuação e a seleção são
intencionalmente únicas para evitar divergências entre referências.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


def normalizar_espacos(texto: str, *, remover_espaco_antes_pontuacao: bool = False) -> str:
    texto_normalizado = re.sub(r"\s+", " ", str(texto or "")).strip()
    if remover_espaco_antes_pontuacao:
        return re.sub(r"\s+([.,;:!?])", r"\1", texto_normalizado)
    return texto_normalizado


def normalizar_busca(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def tokens_titulo(texto: str) -> set[str]:
    ignorar = {
        "a", "o", "as", "os", "e", "de", "do", "da", "dos", "das",
        "um", "uma", "para", "por", "que", "em", "no", "na", "nos", "nas",
        "aula", "parte",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalizar_busca(texto))
        if token not in ignorar and len(token) > 1
    }


def parte_titulo(texto: str) -> str:
    match = re.search(r"\bparte\s*(\d{1,2})\b", normalizar_busca(texto))
    return match.group(1) if match else ""


def pontuar_titulo(tema: str, titulo_referencia: str) -> float:
    tokens_tema = tokens_titulo(tema)
    tokens_referencia = tokens_titulo(titulo_referencia)
    if not tokens_tema or not tokens_referencia:
        return 0.0

    pontuacao = len(tokens_tema & tokens_referencia) / len(tokens_tema | tokens_referencia)
    parte_tema = parte_titulo(tema)
    parte_referencia = parte_titulo(titulo_referencia)
    if parte_tema and parte_referencia:
        pontuacao += 0.25 if parte_tema == parte_referencia else -0.25
    return pontuacao


def normalizar_numero_aula(valor: Any, *, max_digitos: int = 2) -> int:
    if isinstance(valor, int):
        return valor
    match = re.search(rf"\d{{1,{max_digitos}}}", str(valor or ""))
    return int(match.group(0)) if match else 0


def paragrafos_docx(
    caminho_docx: str,
    *,
    remover_espaco_antes_pontuacao: bool = False,
) -> list[str]:
    try:
        from docx import Document
        documento = Document(caminho_docx)
    except Exception:
        return []
    return [
        normalizar_espacos(
            paragrafo.text,
            remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
        )
        for paragrafo in documento.paragraphs
        if normalizar_espacos(
            paragrafo.text,
            remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
        )
    ]


def finalizar_aula(
    aula: dict[str, Any] | None,
    aulas: dict[int, dict[str, Any]],
    *,
    max_digitos_numero: int = 2,
) -> None:
    if not aula:
        return
    numero = normalizar_numero_aula(aula.get("numero"), max_digitos=max_digitos_numero)
    if not numero:
        return
    if (
        aula.get("metodologia")
        and len(aula.get("acompanhamento") or []) >= 3
        and len(aula.get("acessibilidade") or []) >= 3
    ):
        aulas[numero] = aula


def carregar_referencias_docx(
    caminho_docx: str,
    *,
    padrao_aula: str = r"^AULA\s+(\d{1,2})\s*[-–—]\s*(.+)$",
    normalizar_secoes: bool = False,
    limite_titulo_etapa: int = 80,
    capturar_habilidade: bool = False,
    max_digitos_numero: int = 2,
    remover_espaco_antes_pontuacao: bool = False,
) -> dict[int, dict[str, Any]]:
    """Lê o formato sequencial comum de referências pedagógicas em DOCX."""
    aulas: dict[int, dict[str, Any]] = {}
    aula_atual: dict[str, Any] | None = None
    secao = ""

    for texto in paragrafos_docx(caminho_docx):
        match_aula = re.match(padrao_aula, texto, flags=re.I)
        if match_aula:
            finalizar_aula(aula_atual, aulas, max_digitos_numero=max_digitos_numero)
            aula_atual = {
                "numero": int(match_aula.group(1)),
                "titulo": normalizar_espacos(
                    match_aula.group(2),
                    remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
                ),
                "metodologia": [],
                "acompanhamento": [],
                "acessibilidade": [],
            }
            secao = ""
            continue

        if not aula_atual:
            continue

        texto_secao = normalizar_busca(texto) if normalizar_secoes else texto.lower()
        if capturar_habilidade and texto_secao.startswith("habilidade"):
            match_habilidade = re.match(r"^habilidade\s*[:\-]?\s*(.+)$", texto, flags=re.I)
            if match_habilidade:
                aula_atual["habilidade"] = normalizar_espacos(
                    match_habilidade.group(1),
                    remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
                )
            continue
        if texto_secao == "metodologia":
            secao = "metodologia"
            continue
        if texto_secao == "acompanhamento da aprendizagem":
            secao = "acompanhamento"
            continue
        if texto_secao == "acessibilidade":
            secao = "acessibilidade"
            continue

        if secao == "metodologia":
            match_etapa = re.match(rf"^([^:]{{2,{limite_titulo_etapa}}}):\s*(.+)$", texto)
            if match_etapa:
                aula_atual["metodologia"].append(
                    {
                        "titulo": normalizar_espacos(
                            match_etapa.group(1),
                            remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
                        ),
                        "texto": normalizar_espacos(
                            match_etapa.group(2),
                            remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
                        ),
                    }
                )
            elif aula_atual["metodologia"]:
                aula_atual["metodologia"][-1]["texto"] = normalizar_espacos(
                    f"{aula_atual['metodologia'][-1]['texto']} {texto}",
                    remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
                )
        elif secao in {"acompanhamento", "acessibilidade"}:
            item = texto if texto.startswith("☑") else f"☑ {texto.lstrip('☑ ').strip()}"
            aula_atual[secao].append(
                normalizar_espacos(
                    item,
                    remover_espaco_antes_pontuacao=remover_espaco_antes_pontuacao,
                )
            )

    finalizar_aula(aula_atual, aulas, max_digitos_numero=max_digitos_numero)
    return aulas


def score_docx_referencia(caminho: Path) -> tuple[int, float, str]:
    nome = normalizar_busca(caminho.name)
    prioridade_nome = int(any(token in nome for token in ("corrigido", "atualizado", "novo", "2026")))
    try:
        modificado = caminho.stat().st_mtime
    except OSError:
        modificado = 0.0
    return prioridade_nome, modificado, caminho.name.lower()


def selecionar_referencia(
    referencias: dict[int, dict[str, Any]],
    numero_aula: int,
    tema: str = "",
) -> dict[str, Any] | None:
    referencia_numerica = referencias.get(numero_aula)
    if not tema:
        return referencia_numerica

    melhor_numero = 0
    melhor_pontuacao = 0.0
    for numero, referencia in referencias.items():
        pontuacao = pontuar_titulo(tema, referencia.get("titulo", ""))
        if pontuacao > melhor_pontuacao:
            melhor_numero = numero
            melhor_pontuacao = pontuacao

    pontuacao_numerica = pontuar_titulo(tema, (referencia_numerica or {}).get("titulo", ""))
    if melhor_numero and melhor_pontuacao >= 0.50 and melhor_pontuacao > pontuacao_numerica + 0.15:
        return referencias.get(melhor_numero)
    return referencia_numerica or (referencias.get(melhor_numero) if melhor_pontuacao >= 0.70 else None)
