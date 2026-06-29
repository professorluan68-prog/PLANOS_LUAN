from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from core.lib.classificador import normalizar_texto as _normalizar

BASE_DIR = Path(__file__).resolve().parent.parent
AE_PRIORIZADO_DIR = BASE_DIR / "assets" / "ae_priorizado"
AE_PRIORIZADO_JSON_PATH = AE_PRIORIZADO_DIR / "portugues_em_2b.json"

DISCIPLINA_ALIASES = {
    "arte": "arte",
    "artes": "arte",
    "biologia": "biologia",
    "ciencias": "ciencias",
    "geografia": "geografia",
    "historia": "historia",
    "ingles": "ingles",
    "lingua inglesa": "ingles",
    "matematica": "matematica",
    "quimica": "quimica",
    "sociologia": "sociologia",
    "lingua portuguesa": "portugues",
    "portugues": "portugues",
}


def _disciplina_chave(disciplina: str = "") -> str:
    base = _normalizar(disciplina)
    if "portugues" in base:
        return "portugues"
    return DISCIPLINA_ALIASES.get(base, base.replace(" ", "_"))

def _bimestre_numero(bimestre: str = "") -> int:
    match = re.search(r"([1-4])", str(bimestre or ""))
    return int(match.group(1)) if match else 0

def _serie_chave_por_turma(turma: str = "") -> str:
    base = _normalizar(turma)

    match = re.search(r"\b([1-9])\s*(?:a|o)?\s*(?:serie|ano)\b", base)
    if not match:
        match = re.search(r"^\s*([1-9])\s*[a-z]?\b", base)
    if not match:
        match = re.search(r"([1-9])", base)

    if not match:
        return ""

    numero = match.group(1)
    return f"{numero}a_serie"


def _etapa_chave_por_turma(turma: str = "") -> str:
    base = _normalizar(turma)
    serie = _serie_chave_por_turma(turma)
    if not serie:
        return ""

    match = re.match(r"([1-9])a_serie", serie)
    numero = int(match.group(1)) if match else 0
    if numero in {6, 7, 8, 9}:
        return "af"
    if numero in {1, 2, 3}:
        return "em"
    if "ensino medio" in base or re.search(r"\bserie\b", base):
        return "em"
    return ""

def _serie_em_por_turma(turma: str = "") -> str:
    serie = _serie_chave_por_turma(turma)
    etapa = _etapa_chave_por_turma(turma)
    if etapa != "em":
        return ""
    return serie.replace("_", " ")

def disciplina_ae_priorizado_disponivel(disciplina: str = "") -> bool:
    chave = _disciplina_chave(disciplina)
    return any(str(item.get("chave_lookup") or "").startswith(f"{chave}_") for item in carregar_base_ae_priorizado().get("mapa_por_aula", []))


# Compatibilidade com nome antigo durante a transição.
disciplina_ae_priorizado_teste = disciplina_ae_priorizado_disponivel

def _normalizar_cabecalho_coluna(valor: str = "") -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.strip().lower()


def _extrair_codigo_ae(texto_ae: str = "") -> str:
    match = re.search(r"\b(AE\d+)\b", str(texto_ae or ""), flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _extrair_numero_aula_planilha(valor) -> int:
    match = re.search(r"\b(\d{1,3})\b", str(valor or ""))
    return int(match.group(1)) if match else 0


def _selecionar_coluna_planilha(colunas, *termos: str) -> str:
    termos_norm = [_normalizar_cabecalho_coluna(termo) for termo in termos if str(termo or "").strip()]
    for coluna in colunas:
        coluna_norm = _normalizar_cabecalho_coluna(coluna)
        if all(termo in coluna_norm for termo in termos_norm):
            return str(coluna)
    return ""


@lru_cache(maxsize=32)
def carregar_base_ae_planilha(caminho_planilha: str = "") -> dict:
    path = Path(str(caminho_planilha or "").strip())
    if not caminho_planilha or not path.exists() or path.suffix.lower() not in {".xlsx", ".xls"}:
        return {"arquivo_fonte": "", "mapa_por_aula": []}

    try:
        import pandas as pd

        df = pd.read_excel(path)
    except Exception:
        return {"arquivo_fonte": str(path), "mapa_por_aula": []}

    if df.empty:
        return {"arquivo_fonte": str(path), "mapa_por_aula": []}

    col_aula = _selecionar_coluna_planilha(df.columns, "aula")
    col_ae = (
        _selecionar_coluna_planilha(df.columns, "aprendizagem", "essencial")
        or _selecionar_coluna_planilha(df.columns, "ae")
    )
    col_habilidade = _selecionar_coluna_planilha(df.columns, "habilidade")
    col_titulo = _selecionar_coluna_planilha(df.columns, "titulo") or _selecionar_coluna_planilha(
        df.columns, "título"
    )

    if not col_aula or not col_ae:
        return {"arquivo_fonte": str(path), "mapa_por_aula": []}

    mapa_por_aula: list[dict] = []
    vistos: set[int] = set()
    for _, row in df.iterrows():
        numero_aula = _extrair_numero_aula_planilha(row.get(col_aula))
        texto_ae = str(row.get(col_ae) or "").strip()
        if not numero_aula or not texto_ae or texto_ae.lower() == "nan" or numero_aula in vistos:
            continue
        vistos.add(numero_aula)
        mapa_por_aula.append(
            {
                "aula_numero": numero_aula,
                "usar_ae": texto_ae,
                "ae_codigos": _extrair_codigo_ae(texto_ae),
                "habilidade_textos": str(row.get(col_habilidade) or "").strip() if col_habilidade else "",
                "titulo": str(row.get(col_titulo) or "").strip() if col_titulo else "",
            }
        )

    return {"arquivo_fonte": str(path), "mapa_por_aula": mapa_por_aula}


@lru_cache(maxsize=32)
def carregar_base_habilidades_planilha(caminho_planilha: str = "") -> dict:
    path = Path(str(caminho_planilha or "").strip())
    if not caminho_planilha or not path.exists() or path.suffix.lower() not in {".xlsx", ".xls"}:
        return {"arquivo_fonte": "", "mapa_por_aula": []}

    try:
        import pandas as pd

        df = pd.read_excel(path)
    except Exception:
        return {"arquivo_fonte": str(path), "mapa_por_aula": []}

    if df.empty:
        return {"arquivo_fonte": str(path), "mapa_por_aula": []}

    col_aula = _selecionar_coluna_planilha(df.columns, "aula")
    col_habilidade = _selecionar_coluna_planilha(df.columns, "habilidade")
    col_ae = (
        _selecionar_coluna_planilha(df.columns, "aprendizagem", "essencial")
        or _selecionar_coluna_planilha(df.columns, "ae")
    )
    col_titulo = _selecionar_coluna_planilha(df.columns, "titulo") or _selecionar_coluna_planilha(
        df.columns, "título"
    )

    if not col_aula or not col_habilidade:
        return {"arquivo_fonte": str(path), "mapa_por_aula": []}

    mapa_por_aula: list[dict] = []
    vistos: set[int] = set()
    for _, row in df.iterrows():
        numero_aula = _extrair_numero_aula_planilha(row.get(col_aula))
        habilidade = str(row.get(col_habilidade) or "").strip()
        texto_ae = str(row.get(col_ae) or "").strip() if col_ae else ""
        if not numero_aula or not habilidade or habilidade.lower() == "nan" or numero_aula in vistos:
            continue
        vistos.add(numero_aula)
        mapa_por_aula.append(
            {
                "aula_numero": numero_aula,
                "habilidade_textos": habilidade,
                "usar_ae": texto_ae if texto_ae.lower() != "nan" else "",
                "ae_codigos": _extrair_codigo_ae(texto_ae),
                "titulo": str(row.get(col_titulo) or "").strip() if col_titulo else "",
            }
        )

    return {"arquivo_fonte": str(path), "mapa_por_aula": mapa_por_aula}


def contexto_ae_priorizado_disponivel(
    disciplina: str = "",
    turma: str = "",
    bimestre: str = "",
    caminho_planilha: str = "",
) -> bool:
    if caminho_planilha:
        return bool(carregar_base_ae_planilha(caminho_planilha).get("mapa_por_aula"))
    prefixo = _prefixo_chave_contexto(disciplina, turma, bimestre)
    if not prefixo:
        return False
    return any(str(item.get("chave_lookup") or "").startswith(prefixo) for item in carregar_base_ae_priorizado().get("mapa_por_aula", []))

def _prefixo_chave_contexto(disciplina: str = "", turma: str = "", bimestre: str = "") -> str:
    disciplina_chave = _disciplina_chave(disciplina)
    etapa_chave = _etapa_chave_por_turma(turma)
    serie_chave = _serie_chave_por_turma(turma)
    bimestre_numero = _bimestre_numero(bimestre)
    if not (disciplina_chave and etapa_chave and serie_chave and bimestre_numero):
        return ""
    return f"{disciplina_chave}_{etapa_chave}|{bimestre_numero}|{serie_chave}|"

@lru_cache(maxsize=1)
def carregar_base_ae_priorizado() -> dict:
    paths = sorted(AE_PRIORIZADO_DIR.glob("*.json")) if AE_PRIORIZADO_DIR.exists() else []
    if not paths and AE_PRIORIZADO_JSON_PATH.exists():
        paths = [AE_PRIORIZADO_JSON_PATH]
    if not paths:
        return {"mapa_por_aula": []}

    mapa_por_aula: list[dict] = []
    entradas_base: list[dict] = []
    fontes: list[str] = []
    chaves_vistas: set[str] = set()
    for path in paths:
        try:
            base = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        fontes.append(str(path))
        entradas_base.extend(
            dict(item) for item in base.get("entradas_base", []) if isinstance(item, dict)
        )
        for item in base.get("mapa_por_aula", []):
            if not isinstance(item, dict):
                continue
            chave = str(item.get("chave_lookup") or "").strip()
            if not chave or chave in chaves_vistas:
                continue
            chaves_vistas.add(chave)
            mapa_por_aula.append(dict(item))
    return {"arquivos_fonte": fontes, "mapa_por_aula": mapa_por_aula, "entradas_base": entradas_base}

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
    posicao = 0

    for entrada in base.get("entradas_base", []):
        disciplina = str(entrada.get("disciplina") or "").strip()
        serie = str(entrada.get("serie") or "").strip()
        bimestre = str(entrada.get("bimestre") or "2º").strip()
        aulas_bloco = str(entrada.get("aulas_lista") or entrada.get("aulas_bloco") or "")
        for valor in re.findall(r"\d{1,3}", aulas_bloco):
            chave = _chave_lookup(disciplina, serie, bimestre, int(valor))
            if chave and chave not in ordem:
                ordem[chave] = posicao
                posicao += 1

    for item in base.get("mapa_por_aula", []):
        chave = str(item.get("chave_lookup") or "").strip()
        if chave and chave not in ordem:
            ordem[chave] = posicao
            posicao += 1
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
    caminho_planilha: str = "",
) -> list[int]:
    if caminho_planilha:
        itens_planilha = carregar_base_ae_planilha(caminho_planilha).get("mapa_por_aula", [])
        numeros_planilha: list[int] = []
        vistos_planilha: set[int] = set()
        for item in itens_planilha:
            try:
                numero = int(item.get("aula_numero") or 0)
            except (TypeError, ValueError):
                numero = 0
            if not numero or numero in vistos_planilha:
                continue
            vistos_planilha.add(numero)
            numeros_planilha.append(numero)
            if limite is not None and limite > 0 and len(numeros_planilha) >= int(limite):
                break
        return numeros_planilha

    if not contexto_ae_priorizado_disponivel(disciplina, turma, bimestre):
        return []

    prefixo = _prefixo_chave_contexto(disciplina, turma, bimestre)
    if not prefixo:
        return []

    numeros: list[int] = []
    vistos: set[int] = set()
    ordem = _ordem_por_chave()
    itens_ordenados = sorted(
        (
            item
            for item in carregar_base_ae_priorizado().get("mapa_por_aula", [])
            if str(item.get("chave_lookup") or "").strip().startswith(prefixo)
        ),
        key=lambda item: ordem.get(str(item.get("chave_lookup") or "").strip(), 10_000),
    )

    for item in itens_ordenados:
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
    caminho_planilha: str = "",
) -> tuple[list[dict], list[str]]:
    if caminho_planilha:
        base_planilha = carregar_base_ae_planilha(caminho_planilha).get("mapa_por_aula", [])
        if not base_planilha:
            return list(aulas or []), []

        indice_planilha = {
            int(item.get("aula_numero") or 0): dict(item)
            for item in base_planilha
            if int(item.get("aula_numero") or 0)
        }
        ordem_planilha = {
            int(item.get("aula_numero") or 0): posicao
            for posicao, item in enumerate(base_planilha)
            if int(item.get("aula_numero") or 0)
        }

        ajustadas_planilha: list[dict] = []
        faltantes_planilha: list[int] = []
        for ordem_entrada, aula in enumerate(list(aulas or [])):
            aula_ajustada = dict(aula)
            numero_aula = _numero_aula_item(aula_ajustada)
            item = indice_planilha.get(numero_aula)
            aula_ajustada["_ae_ordem_entrada"] = ordem_entrada
            aula_ajustada["_ae_ordem_guia"] = ordem_planilha.get(numero_aula, 10_000 + ordem_entrada)

            if item and item.get("usar_ae"):
                aprendizagem_original = str(aula_ajustada.get("aprendizagem") or "").strip()
                aula_ajustada["aprendizagem_original"] = aprendizagem_original
                aula_ajustada["aprendizagem"] = str(item.get("usar_ae") or "").strip()
                aula_ajustada["ae_priorizado_aplicado"] = True
                aula_ajustada["ae_priorizado_codigo"] = str(item.get("ae_codigos") or "").strip()
            else:
                aula_ajustada["ae_priorizado_aplicado"] = False
                if numero_aula:
                    faltantes_planilha.append(numero_aula)

            ajustadas_planilha.append(aula_ajustada)

        ajustadas_planilha.sort(
            key=lambda aula: (
                int(aula.get("_ae_ordem_guia", 10_000)),
                int(aula.get("_ae_ordem_entrada", 0)),
            )
        )
        for aula in ajustadas_planilha:
            aula.pop("_ae_ordem_guia", None)
            aula.pop("_ae_ordem_entrada", None)

        avisos_planilha: list[str] = []
        if faltantes_planilha:
            faltantes_unicos = sorted(set(faltantes_planilha))
            lista = ", ".join(str(valor) for valor in faltantes_unicos)
            avisos_planilha.append(
                "Modo AE ativo, mas a planilha do guia priorizado nao trouxe correspondencia para a(s) aula(s) "
                f"{lista}. Nessas aulas, o sistema manteve a habilidade normal."
            )

        return ajustadas_planilha, avisos_planilha

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
            "Modo AE ativo, mas o guia priorizado nao trouxe correspondencia para a(s) aula(s) "
            f"{lista}. Nessas aulas, o sistema manteve a habilidade normal."
        )

    return ajustadas, avisos
