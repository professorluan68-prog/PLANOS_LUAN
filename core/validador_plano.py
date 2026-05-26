"""
Validador pedagogico expandido para planos de aula.

Valida tema, metodologia, acompanhamento, acessibilidade e aprendizagem.
"""

import re


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
