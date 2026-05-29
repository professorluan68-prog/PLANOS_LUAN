from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Tuple


def _norm(txt: str) -> str:
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", txt).strip().lower()


MARCADORES_CANONICOS = [
    "Ponto de partida",
    "Para comecar",
    "Relembre",
    "Foco no conteudo",
    "Construindo o conceito",
    "Pause e responda",
    "Na pratica",
    "Encerramento",
    "Com suas palavras",
    "Virem e conversem",
    "Para refletir",
    "Fica a dica",
]

PADROES_MARCADORES = {
    "Ponto de partida": [r"\bponto\s+de\s+partida\b"],
    "Para comecar": [r"\bpara\s+come[cç]ar\b"],
    "Relembre": [r"\brelembre\b"],
    "Foco no conteudo": [r"\bfoco\s+no\s+conte[uú]do\b"],
    "Construindo o conceito": [r"\bconstruindo\s+o\s+conceito\b"],
    "Pause e responda": [r"\bpause\s+e\s+responda\b"],
    "Na pratica": [r"\bna\s+pr[aá]tica\b"],
    "Encerramento": [r"\bencerramento\b"],
    "Com suas palavras": [r"\bcom\s+suas\s+palavras\b"],
    "Virem e conversem": [r"\bvirem\s+e\s+conversem\b"],
    "Para refletir": [r"\bpara\s+refletir\b"],
    "Fica a dica": [r"\bfica\s+a\s+dica\b"],
}


def _achar_ocorrencias(texto: str) -> List[Tuple[int, str]]:
    ocorrencias: List[Tuple[int, str]] = []
    for marcador, padroes in PADROES_MARCADORES.items():
        for padrao in padroes:
            for match in re.finditer(padrao, texto, flags=re.I):
                ocorrencias.append((match.start(), marcador))
    ocorrencias.sort(key=lambda x: x[0])

    limpas: List[Tuple[int, str]] = []
    ultimo_inicio = -999999
    ultimo_marcador = ""
    for inicio, marcador in ocorrencias:
        if marcador == ultimo_marcador and abs(inicio - ultimo_inicio) < 8:
            continue
        limpas.append((inicio, marcador))
        ultimo_inicio = inicio
        ultimo_marcador = marcador
    return limpas


def extrair_blocos_pedagogicos(texto: str) -> Dict[str, str]:
    texto = texto or ""
    blocos = {m: "" for m in MARCADORES_CANONICOS}
    ocorrencias = _achar_ocorrencias(texto)

    if not ocorrencias:
        return blocos

    for indice, (inicio, marcador) in enumerate(ocorrencias):
        fim = ocorrencias[indice + 1][0] if indice + 1 < len(ocorrencias) else len(texto)
        trecho = texto[inicio:fim].strip()
        if len(trecho) > len(blocos.get(marcador, "")):
            blocos[marcador] = trecho

    return blocos
