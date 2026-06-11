from __future__ import annotations

from pathlib import Path

from config import TEMPLATES_DOCX_DIR
from core.disciplinas import eh_cdp, eh_cdp_contextual


TEMPLATE_EGLE = "egle"
TEMPLATE_PADRE = "padre"
TEMPLATE_CDP = "cdp"
TEMPLATE_PADRAO = TEMPLATE_EGLE

ARQUIVOS_TEMPLATES = {
    TEMPLATE_EGLE: "MODELOEGLE.docx",
    TEMPLATE_PADRE: "MODELOPADRE.docx",
    TEMPLATE_CDP: "MODELOCDP.docx",
}


def normalizar_template_id(template_id: str = "") -> str:
    valor = str(template_id or "").strip().lower()
    if valor in ARQUIVOS_TEMPLATES:
        return valor
    if "padre" in valor:
        return TEMPLATE_PADRE
    if "cdp" in valor or "eja" in valor:
        return TEMPLATE_CDP
    return TEMPLATE_PADRAO


def template_id_por_contexto(
    disciplina: str = "",
    componente_curricular: str = "",
    escola: str = "",
    arquivo_modelo: str = "",
) -> str:
    texto = " ".join(
        [
            str(disciplina or ""),
            str(componente_curricular or ""),
            str(escola or ""),
            str(arquivo_modelo or ""),
        ]
    ).lower()
    if eh_cdp_contextual(disciplina):
        return TEMPLATE_PADRE if "padre" in texto else TEMPLATE_EGLE
    if eh_cdp(disciplina) or "cdp - ciclo i" in texto or "cdp- multisseriada" in texto:
        return TEMPLATE_CDP
    if "cdp" in texto or "eja" in texto:
        return TEMPLATE_CDP
    if "padre" in texto:
        return TEMPLATE_PADRE
    return TEMPLATE_EGLE


def resolver_template_id_geracao(
    template_id: str = "",
    disciplina: str = "",
    componente_curricular: str = "",
    escola: str = "",
    arquivo_modelo: str = "",
) -> str:
    explicito = str(template_id or "").strip()
    if eh_cdp_contextual(disciplina):
        if normalizar_template_id(explicito) == TEMPLATE_CDP:
            return template_id_por_contexto(
                disciplina=disciplina,
                componente_curricular=componente_curricular,
                escola=escola,
                arquivo_modelo=arquivo_modelo,
            )
        if explicito:
            return normalizar_template_id(explicito)
        return template_id_por_contexto(
            disciplina=disciplina,
            componente_curricular=componente_curricular,
            escola=escola,
            arquivo_modelo=arquivo_modelo,
        )

    if explicito:
        return normalizar_template_id(explicito)
    return template_id_por_contexto(
        disciplina=disciplina,
        componente_curricular=componente_curricular,
        escola=escola,
        arquivo_modelo=arquivo_modelo,
    )


def caminho_template_central(template_id: str = "") -> Path:
    template_id = normalizar_template_id(template_id)
    return TEMPLATES_DOCX_DIR / ARQUIVOS_TEMPLATES[template_id]


def caminho_template_por_contexto(
    disciplina: str = "",
    componente_curricular: str = "",
    escola: str = "",
    arquivo_modelo: str = "",
) -> Path:
    return caminho_template_central(
        template_id_por_contexto(
            disciplina=disciplina,
            componente_curricular=componente_curricular,
            escola=escola,
            arquivo_modelo=arquivo_modelo,
        )
    )
