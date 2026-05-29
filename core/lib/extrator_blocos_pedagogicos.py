from __future__ import annotations

import re
from typing import Dict


MARCADORES = [
    "Para comecar",
    "Relembre",
    "Foco no conteudo",
    "Pause e responda",
    "Na pratica",
    "Encerramento",
]


def extrair_blocos_pedagogicos(texto: str) -> Dict[str, str]:
    texto = texto or ""
    blocos = {marcador: "" for marcador in MARCADORES}

    ocorrencias = []
    for marcador in MARCADORES:
        padrao = re.escape(marcador).replace("comecar", "(?:comecar|come\\u00e7ar)")
        padrao = padrao.replace("conteudo", "(?:conteudo|conte\\u00fado)")
        for match in re.finditer(padrao, texto, flags=re.I):
            ocorrencias.append((match.start(), marcador))

    ocorrencias.sort(key=lambda item: item[0])
    if not ocorrencias:
        return blocos

    for indice, (inicio, marcador) in enumerate(ocorrencias):
        fim = ocorrencias[indice + 1][0] if indice + 1 < len(ocorrencias) else len(texto)
        blocos[marcador] = texto[inicio:fim].strip()

    return blocos
