"""
Validador pedagogico expandido para planos de aula.

Valida tema, metodologia, acompanhamento, acessibilidade e aprendizagem.
"""

import re
from core.qualidade_metodologica import normalizar_texto, tem_mojibake


_ROTULOS_ETAPAS = (
    "para comecar",
    "disparo inicial",
    "contextualizacao",
    "leitura ou exploracao inicial",
    "leitura compartilhada ou individual",
    "leitura e construcao do conteudo",
    "predicao guiada",
    "analise guiada",
    "foco no conteudo",
    "sistematizacao",
    "producao textual",
    "revisao e fechamento",
    "revisao orientada",
    "escrita da versao final",
    "submissao e socializacao",
    "encerramento",
)


def _normalizar_rotulo(texto: str) -> str:
    texto = (texto or "").strip().lower()
    return re.sub(r"[^a-z\s]", "", texto).strip()


def _contar_etapas_metodologia(metodologia) -> int:
    etapas = set()
    for item in metodologia or []:
        if isinstance(item, dict):
            titulo = _normalizar_rotulo(item.get("titulo", ""))
            texto = str(item.get("texto", "") or "")
        else:
            titulo = ""
            texto = str(item or "")

        if titulo:
            etapas.add(titulo)

        texto_norm = _normalizar_rotulo(texto)
        for rotulo in _ROTULOS_ETAPAS:
            if re.search(rf"\b{re.escape(rotulo)}\b", texto_norm):
                etapas.add(rotulo)

    return len(etapas)


def validar_aulas_geradas(
    aulas,
    permitir_temas_repetidos: bool = False,
    permitir_metodologia_simples: bool = False,
) -> list[str]:
    """
    Valida a qualidade pedagogica das aulas geradas.

    Retorna lista de problemas encontrados (vazia = sem problemas).
    """
    problemas = []
    if not aulas:
        return ["Nenhuma aula foi gerada."]

    temas_vistos = set()

    for idx, aula in enumerate(aulas, start=1):
        tema = str(aula.get("tema", "")).strip()

        if not tema:
            problemas.append(f"Aula {idx}: tema nao identificado.")

        if not permitir_temas_repetidos and tema and tema in temas_vistos:
            problemas.append(
                f"Aula {idx}: tema '{tema}' repetido de aula anterior. "
                "Considere diferenciar com subtema ou continuidade."
            )
        temas_vistos.add(tema)

        metodologia = aula.get("metodologia") or []
        if not metodologia:
            problemas.append(f"Aula {idx}: metodologia vazia.")
            continue

        primeiro = metodologia[0]
        texto_primeiro = primeiro.get("texto", "") if isinstance(primeiro, dict) else str(primeiro)
        if len(texto_primeiro.strip()) < 40:
            problemas.append(f"Aula {idx}: desenvolvimento muito curto.")

        titulos = set()
        for item in metodologia:
            if isinstance(item, dict):
                titulos.add(_normalizar_rotulo(item.get("titulo", "")))

        etapas_identificadas = _contar_etapas_metodologia(metodologia)

        if not permitir_metodologia_simples and etapas_identificadas < 3 and len(metodologia) < 3:
            problemas.append(
                f"Aula {idx}: metodologia com poucas etapas ({etapas_identificadas}). "
                "Um plano completo deve ter pelo menos 3 etapas."
            )

        aprendizagem = str(aula.get("aprendizagem", "")).strip()
        if not aprendizagem:
            problemas.append(f"Aula {idx}: campo de aprendizagem vazio.")
        elif len(aprendizagem) < 20:
            problemas.append(f"Aula {idx}: aprendizagem muito curta ({len(aprendizagem)} chars).")

        acompanhamento = aula.get("acompanhamento") or []
        if not acompanhamento:
            problemas.append(f"Aula {idx}: acompanhamento da aprendizagem vazio.")
        elif isinstance(acompanhamento, list):
            itens_validos = [item for item in acompanhamento if str(item).strip()]
            if len(itens_validos) < 2:
                problemas.append(
                    f"Aula {idx}: acompanhamento com poucos itens ({len(itens_validos)}). "
                    "Recomendado pelo menos 3."
                )

        acessibilidade = aula.get("acessibilidade") or []
        if not acessibilidade:
            problemas.append(f"Aula {idx}: acessibilidade vazia.")
        elif isinstance(acessibilidade, list):
            itens_validos = [item for item in acessibilidade if str(item).strip()]
            if len(itens_validos) < 2:
                problemas.append(
                    f"Aula {idx}: acessibilidade com poucos itens ({len(itens_validos)}). "
                    "Recomendado pelo menos 3."
                )

    return problemas


def validar_aula_final(aula: dict) -> list[str]:
    """Faz uma checagem semântica simples antes do preenchimento do DOCX."""
    avisos = []

    disciplina = normalizar_texto(aula.get("disciplina", ""))
    tema = normalizar_texto(aula.get("tema", ""))
    metodologia = " ".join(
        str(item.get("texto", ""))
        for item in aula.get("metodologia", [])
        if isinstance(item, dict)
    )
    acompanhamento = " ".join(str(item) for item in aula.get("acompanhamento", []))
    acessibilidade = " ".join(str(item) for item in aula.get("acessibilidade", []))
    texto_total = " ".join(
        [
            str(aula.get("tema", "")),
            str(aula.get("aprendizagem", "")),
            metodologia,
            acompanhamento,
            acessibilidade,
        ]
    )
    texto_norm = normalizar_texto(texto_total)

    if tem_mojibake(texto_total):
        avisos.append("Texto com possível problema de codificação.")
    if "relacionado a relacionado" in texto_norm:
        avisos.append("Possível frase artificial ou repetida.")
    if disciplina and "matematica" in disciplina and any(
        termo in texto_norm for termo in ["texto literario", "personagens", "enredo", "cronica"]
    ):
        avisos.append("Possível contaminação: metodologia de leitura literária em Matemática.")
    if disciplina and "geografia" in disciplina and any(
        termo in texto_norm for termo in ["equacao", "incognita", "resolver x", "sistema de equacoes"]
    ):
        avisos.append("Possível contaminação: linguagem algébrica em Geografia.")
    if disciplina and "historia" in disciplina and any(
        termo in texto_norm for termo in ["calculo", "equacao", "porcentagem", "resolver operacoes"]
    ):
        avisos.append("Possível contaminação: cálculo matemático em História.")
    if "producao textual" in tema and not any(
        termo in texto_norm for termo in ["rascunho", "revis", "reescrita", "planejamento"]
    ):
        avisos.append("Produção textual sem etapa clara de planejamento ou revisão.")

    return avisos
