from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from core.lib.classificador import normalizar_texto as _normalizar

BASE_DIR = Path(__file__).resolve().parent.parent
AE_PRIORIZADO_JSON_PATH = BASE_DIR / "assets" / "ae_priorizado" / "portugues_em_2b_teste.json"

def _disciplina_portugues(disciplina: str = "") -> bool:
    base = _normalizar(disciplina)
    return "portugues" in base

def _bimestre_numero(bimestre: str = "") -> int:
    match = re.search(r"([1-4])", str(bimestre or ""))
    return int(match.group(1)) if match else 0

def _serie_em_por_turma(turma: str = "") -> str:
    base = _normalizar(turma)

    match = re.search(r"\b([123])\s*(?:a|o)?\s*(?:serie|ano)\b", base)
    if not match:
        match = re.search(r"^\s*([123])\s*[a-z]?\b", base)
    if not match:
        match = re.search(r"([123])", base)

    if not match:
        return ""

    numero = match.group(1)
    if re.search(r"\b(?:6|7|8|9)\b", base):
        return ""

    return f"{numero}a serie"

def disciplina_ae_priorizado_teste(disciplina: str = "") -> bool:
    return _disciplina_portugues(disciplina)

def contexto_ae_priorizado_disponivel(disciplina: str = "", turma: str = "", bimestre: str = "") -> bool:
    return (
        disciplina_ae_priorizado_teste(disciplina)
        and _bimestre_numero(bimestre) == 2
        and bool(_serie_em_por_turma(turma))
        and AE_PRIORIZADO_JSON_PATH.exists()
    )

def _prefixo_chave_contexto(disciplina: str = "", turma: str = "", bimestre: str = "") -> str:
    serie = _serie_em_por_turma(turma)
    if not (disciplina_ae_priorizado_teste(disciplina) and serie and _bimestre_numero(bimestre) == 2):
        return ""
    serie_base = _normalizar(serie).replace(" ", "_")
    return f"portugues_em|2|{serie_base}|"

@lru_cache(maxsize=1)
def carregar_base_ae_priorizado() -> dict:
    if not AE_PRIORIZADO_JSON_PATH.exists():
        return {"mapa_por_aula": []}
    return json.loads(AE_PRIORIZADO_JSON_PATH.read_text(encoding="utf-8"))

@lru_cache(maxsize=1)
def _indice_por_chave() -> dict[str, dict]:
    base = carregar_base_ae_priorizado()
    indice: dict[str, dict] = {}
    for item in base.get("mapa_por_aula", []):
        chave = str(item.get("chave_lookup") or "").strip()
        if chave:
            indice[chave] = dict(item)
    return indice

@lru_cache(maxsize=1)
def _ordem_por_chave() -> dict[str, int]:
    base = carregar_base_ae_priorizado()
    ordem: dict[str, int] = {}
    for posicao, item in enumerate(base.get("mapa_por_aula", [])):
        chave = str(item.get("chave_lookup") or "").strip()
        if chave and chave not in ordem:
            ordem[chave] = posicao
    return ordem

def _numero_aula_item(aula: dict) -> int:
    for valor in (aula.get("numero_aula"), aula.get("material"), aula.get("tema")):
        match = re.search(r"\b(\d{1,3})\b", str(valor or ""))
        if match:
            return int(match.group(1))
    return 0

def _chave_lookup(disciplina: str, turma: str, bimestre: str, aula_numero: int) -> str:
    prefixo = _prefixo_chave_contexto(disciplina, turma, bimestre)
    if not (prefixo and aula_numero):
        return ""
    return f"{prefixo}{int(aula_numero)}"

def sequencia_aulas_ae_priorizado(
    disciplina: str = "",
    turma: str = "",
    bimestre: str = "",
    limite: int | None = None,
) -> list[int]:
    if not contexto_ae_priorizado_disponivel(disciplina, turma, bimestre):
        return []

    prefixo = _prefixo_chave_contexto(disciplina, turma, bimestre)
    if not prefixo:
        return []

    numeros: list[int] = []
    vistos: set[int] = set()
    for item in carregar_base_ae_priorizado().get("mapa_por_aula", []):
        chave = str(item.get("chave_lookup") or "").strip()
        if not chave.startswith(prefixo):
            continue
        try:
            numero = int(item.get("aula_numero") or 0)
        except (TypeError, ValueError):
            numero = 0
        if not numero or numero in vistos:
            continue
        vistos.add(numero)
        numeros.append(numero)
        if limite is not None and limite > 0 and len(numeros) >= int(limite):
            break
    return numeros

def aplicar_ae_priorizado_nas_aulas(
    aulas: list[dict],
    disciplina: str,
    turma: str,
    bimestre: str,
) -> tuple[list[dict], list[str]]:
    if not contexto_ae_priorizado_disponivel(disciplina, turma, bimestre):
        return list(aulas or []), []

    indice = _indice_por_chave()
    ordem = _ordem_por_chave()
    ajustadas: list[dict] = []
    faltantes: list[int] = []

    for ordem_entrada, aula in enumerate(list(aulas or [])):
        aula_ajustada = dict(aula)
        numero_aula = _numero_aula_item(aula_ajustada)
        chave = _chave_lookup(disciplina, turma, bimestre, numero_aula)
        item = indice.get(chave)
        aula_ajustada["_ae_ordem_entrada"] = ordem_entrada
        aula_ajustada["_ae_ordem_guia"] = ordem.get(chave, 10_000 + ordem_entrada)

        if item and item.get("usar_ae"):
            aprendizagem_original = str(aula_ajustada.get("aprendizagem") or "").strip()
            aula_ajustada["aprendizagem_original"] = aprendizagem_original
            aula_ajustada["aprendizagem"] = str(item.get("usar_ae") or "").strip()
            aula_ajustada["ae_priorizado_aplicado"] = True
            aula_ajustada["ae_priorizado_chave"] = chave
            aula_ajustada["ae_priorizado_codigo"] = str(item.get("ae_codigos") or "").strip()
        else:
            aula_ajustada["ae_priorizado_aplicado"] = False
            if numero_aula:
                faltantes.append(numero_aula)

        ajustadas.append(aula_ajustada)

    ajustadas.sort(
        key=lambda aula: (
            int(aula.get("_ae_ordem_guia", 10_000)),
            int(aula.get("_ae_ordem_entrada", 0)),
        )
    )
    for aula in ajustadas:
        aula.pop("_ae_ordem_guia", None)
        aula.pop("_ae_ordem_entrada", None)

    avisos: list[str] = []
    if faltantes:
        faltantes_unicos = sorted(set(faltantes))
        lista = ", ".join(str(valor) for valor in faltantes_unicos)
        avisos.append(
            "Modo AE ativo, mas o guia de teste nao trouxe correspondencia para a(s) aula(s) "
            f"{lista}. Nessas aulas, o sistema manteve a habilidade normal."
        )

    return ajustadas, avisos
