import re
import unicodedata
from core.lib.classificador import normalizar_texto as _normalizar

def _limpar_linhas(texto: str) -> list[str]:
    linhas = []
    for linha in (texto or "").splitlines():
        linha = re.sub(r"\s+", " ", linha).strip()
        if linha:
            linhas.append(linha)
    return linhas

_PADRAO_ROTULO_PERIODO_ENSINO = re.compile(
    r"^(?:[1-4]\s*(?:o|º|°|ª|a)?\s*)?bimestre(?:\s+ensino(?:\s+(?:medio|fundamental))?)?$",
    flags=re.I,
)

def _linha_periodo_ensino(texto: str) -> bool:
    normalizado = _normalizar(texto).strip(" .:-")
    return bool(_PADRAO_ROTULO_PERIODO_ENSINO.fullmatch(normalizado))

def _limpar_titulo_material(linha: str, disciplina: str) -> str:
    titulo = re.sub(r"\s+", " ", linha or "").strip(" -–—")
    disciplina_norm = _normalizar(disciplina)
    titulo_norm = _normalizar(titulo)

    if _linha_periodo_ensino(titulo_norm):
        return ""

    if titulo_norm == disciplina_norm:
        return ""

    if disciplina_norm and titulo_norm.startswith(disciplina_norm):
        titulo = titulo[len(disciplina):].strip(" -–—:")

    titulo = re.sub(r"\s+(?:[1-4][º°oªa]?)\s*bimestre\b.*$", "", titulo, flags=re.I)
    titulo = re.sub(r"\s+ensino\s+(?:fundamental|m[eé]dio)\b.*$", "", titulo, flags=re.I)
    titulo = re.sub(r"\s+anos?\s+(?:iniciais|finais)\b.*$", "", titulo, flags=re.I)
    if _linha_periodo_ensino(titulo):
        return ""
    return titulo.strip(" -–—")

def _linha_generica(linha: str, disciplina: str) -> bool:
    texto = _normalizar(linha)
    disciplina_norm = _normalizar(disciplina)
    genericas = {
        "",
        disciplina_norm,
        "ensino fundamental",
        "ensino medio",
        "anos iniciais",
        "anos finais",
        "material digital",
        "aula digital",
    }
    if texto in genericas:
        return True
    if "gps" in texto and "guia" in texto:
        return True
    if "praticas de sala de aula" in texto:
        return True
    if _linha_periodo_ensino(texto):
        return True
    return bool(re.fullmatch(r"(?:[1-4][oº°]?\s*)?bimestre", texto))

def _linha_rotulo_aula(normalizada: str) -> bool:
    return bool(re.match(r"^aula\s*(?:n[.o]?\s*)?\d{1,3}\b", normalizada or ""))

def _titulo_em_linha_aula(linha: str) -> str:
    texto = re.sub(r"\s+", " ", str(linha or "")).strip(" -:–—")
    match = re.match(r"^aula\s*(?:n[.o]?\s*)?\d{1,3}\s*(?:[|:-]|–|—)?\s*(.+)$", texto, flags=re.I)
    if not match:
        return ""
    titulo = match.group(1).strip(" -:–—")
    if not titulo:
        return ""
    if _linha_generica(titulo, ""):
        return ""
    if _normalizar(titulo).startswith(("ensino fundamental", "ensino medio", "bimestre")):
        return ""
    return titulo

def _linhas_relevantes(texto: str, disciplina: str, tema: str) -> list[str]:
    relevantes = []
    vistos = set()
    for linha in _limpar_linhas(texto):
        linha = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(linha)
        if not linha or normalizada in vistos:
            continue
        if _linha_generica(linha, disciplina) or _normalizar(tema) == normalizada:
            continue
        if _linha_rotulo_aula(normalizada) or normalizada.startswith(("slide ", "pagina ", "página ")):
            continue
        vistos.add(normalizada)
        relevantes.append(linha)
    return relevantes

def _titulo_deve_juntar_continuacao(primeira: str, segunda: str = "") -> bool:
    primeira_limpa = re.sub(r"\s+", " ", str(primeira or "")).strip(" -:")
    segunda_limpa = re.sub(r"\s+", " ", str(segunda or "")).strip(" -:")
    primeira_norm = _normalizar(primeira_limpa)
    segunda_norm = _normalizar(segunda_limpa)
    if not primeira_norm:
        return False
    finais_pendentes = (
        " a", " as", " o", " os", " um", " uma", " de", " da", " do", " das",
        " dos", " e", " em", " para", " por", " com", " sem", " sobre",
    )
    if primeira_norm.endswith(finais_pendentes):
        return True
    if segunda_norm.startswith(("por ", "para ", "com ", "sem ", "em ", "e ", "ou ", "que ", "da ", "de ", "do ")):
        return True
    return False

def _juntar_partes_titulo(partes: list[str]) -> str:
    if not partes:
        return ""
    titulo = str(partes[0] or "").rstrip(" -:")
    for proxima in partes[1:]:
        proxima_limpa = str(proxima or "").lstrip("-: ").strip()
        if not proxima_limpa:
            continue
        titulo_limpo = titulo.rstrip()
        if (
            _titulo_deve_juntar_continuacao(titulo_limpo, proxima_limpa)
            or len(titulo_limpo) <= 28
            or (proxima_limpa[:1].islower() and len(titulo_limpo) <= 70)
            or titulo_limpo.endswith((":", ";", "-", "–", "—"))
        ):
            separador = " - " if _normalizar(proxima_limpa).startswith("parte ") else " "
            titulo = f"{titulo_limpo}{separador}{proxima_limpa}".strip()
            continue
        break
    return titulo

def _extrair_titulo_multilinha(texto: str, disciplina: str) -> str:
    linhas = _limpar_linhas(texto)
    partes = []
    for linha in linhas[:8]:
        titulo = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(titulo)
        if not titulo or _linha_generica(titulo, disciplina) or normalizada == _normalizar(disciplina):
            continue
        if any(token in normalizada for token in ["bimestre", "ensino medio", "ensino fundamental"]):
            break
        if _linha_rotulo_aula(normalizada) or normalizada.startswith(("slide ", "pagina ", "página ")):
            if partes:
                break
            continue
        partes.append(titulo)
        if len(partes) >= 4:
            break

    if not partes:
        return ""

    if len(partes) == 1:
        return _limpar_titulo_material(partes[0], disciplina)

    return _limpar_titulo_material(_juntar_partes_titulo(partes), disciplina)
