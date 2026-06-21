from __future__ import annotations

import re
import unicodedata


def normalizar_turma_para_comparacao(turma: str) -> str:
    texto = unicodedata.normalize("NFKD", str(turma or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.upper()
    texto = texto.replace("º", " ").replace("ª", " ").replace("°", " ")
    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def chave_serie_turma(turma: str) -> str:
    texto = normalizar_turma_para_comparacao(turma)
    if not texto:
        return ""

    if "MULTISSERIADO" in texto:
        anos = re.findall(r"\b[1-9]\b", texto)
        return "MULTISSERIADO:" + ",".join(anos) if anos else "MULTISSERIADO"

    padroes = (
        ("ANO", r"\b([1-9])\s*[OA]?\s*ANO\b"),
        ("SERIE", r"\b([1-9])\s*[OA]?\s*SERIE\b"),
        ("TERMO", r"\b([1-9])\s*[OA]?\s*TERMO\b"),
    )
    for rotulo, padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            return f"{rotulo}:{int(match.group(1))}"
    return ""


def letra_turma(turma: str) -> str:
    texto = normalizar_turma_para_comparacao(turma)
    match = re.search(r"\b(?:[1-9]\s*[OA]?\s*(?:ANO|SERIE|TERMO))\s+([A-Z])\b$", texto)
    return match.group(1) if match else ""


def turmas_espelho_mesma_serie(turma_principal: str, turmas_cadastradas: list[str]) -> list[str]:
    chave_principal = chave_serie_turma(turma_principal)
    if not chave_principal:
        return []

    principal_norm = normalizar_turma_para_comparacao(turma_principal)
    letra_principal = letra_turma(turma_principal)
    candidatas = []
    vistas = set()

    for turma in turmas_cadastradas or []:
        turma_limpa = str(turma or "").strip()
        if not turma_limpa:
            continue

        turma_norm = normalizar_turma_para_comparacao(turma_limpa)
        if not turma_norm or turma_norm == principal_norm or turma_norm in vistas:
            continue
        vistas.add(turma_norm)

        if chave_serie_turma(turma_limpa) != chave_principal:
            continue

        letra_candidata = letra_turma(turma_limpa)
        if letra_principal and (not letra_candidata or letra_candidata == letra_principal):
            continue

        candidatas.append(turma_limpa)

    return candidatas
