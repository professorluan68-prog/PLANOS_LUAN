"""
Validador pedagogico expandido para planos de aula.

Valida tema, metodologia, acompanhamento, acessibilidade e aprendizagem.
"""

import re
from collections import Counter

from core.educacao_financeira_validacao import validar_requisitos_educacao_financeira
from core.listas_pedagogicas import (
    itens_lista_pedagogica,
    problemas_lista_exatamente_tres,
)
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
    """Valida a qualidade pedagogica das aulas geradas."""
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
        else:
            primeiro = metodologia[0]
            texto_primeiro = primeiro.get("texto", "") if isinstance(primeiro, dict) else str(primeiro)
            if len(texto_primeiro.strip()) < 40:
                problemas.append(f"Aula {idx}: desenvolvimento muito curto.")

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
        else:
            itens_validos = itens_lista_pedagogica(acompanhamento)
            problemas.extend(
                problemas_lista_exatamente_tres(
                    "acompanhamento da aprendizagem",
                    itens_validos,
                    prefixo=f"Aula {idx}: ",
                )
            )

        acessibilidade = aula.get("acessibilidade") or []
        if not acessibilidade:
            problemas.append(f"Aula {idx}: acessibilidade vazia.")
        else:
            itens_validos = itens_lista_pedagogica(acessibilidade)
            problemas.extend(
                problemas_lista_exatamente_tres(
                    "acessibilidade",
                    itens_validos,
                    prefixo=f"Aula {idx}: ",
                )
            )

        for problema in validar_requisitos_educacao_financeira(aula):
            problemas.append(f"Aula {idx}: {problema}")

    return problemas


def validar_aula_final(aula: dict) -> list[str]:
    """Faz uma checagem semântica detalhada e pedagógica antes do preenchimento do DOCX."""
    avisos = []

    disciplina = normalizar_texto(aula.get("disciplina", ""))
    tema = normalizar_texto(aula.get("tema", ""))
    aprendizagem = normalizar_texto(aula.get("aprendizagem", ""))

    if len(tema) < 8 or tema in {"estudar matematica", "aula de ciencias", "tema da aula"}:
        avisos.append("Tema muito genérico ou vazio.")

    metodologia = aula.get("metodologia", [])
    if len(metodologia) < 3 and _contar_etapas_metodologia(metodologia) < 3:
        avisos.append(
            f"Metodologia com poucas etapas ({len(metodologia)}). "
            "O plano deve apresentar ao menos 3 momentos pedagógicos."
        )

    conteudo_ref = tema + " " + aprendizagem
    conteudo_palavras = {
        palavra
        for palavra in conteudo_ref.split()
        if len(palavra) > 3 and palavra not in {
            "para", "como", "com", "uma", "mais", "sobre", "aula", "conteudo", "tema",
            "estudantes", "alunos", "professor", "ciencias", "matematica", "portugues",
            "atividade", "recurso",
        }
    }

    verbos_professor = {
        "professor", "docente", "mediador", "apresentar", "conduzir", "propor", "solicitar",
        "orientar", "explicar", "retomar", "exibe", "pergunta", "mostra", "lidera", "mediar",
    }
    termos_estudantes = {
        "aluno", "estudante", "turma", "dupla", "grupo", "eles", "compartilhar", "escrever",
        "responder", "resolver", "realizar", "discutir", "escrevem", "respondem", "resolvem", "participa",
    }
    termos_interacao_registro = {
        "caderno", "registro", "respost", "escrev", "dupla", "grupo", "roda", "discussao",
        "debate", "socializ", "cadernos", "anot", "compartilh",
    }

    etapas_textos = []
    for item in metodologia:
        if not isinstance(item, dict):
            continue
        titulo = item.get("titulo", "")
        texto = item.get("texto", "")
        texto_norm = normalizar_texto(texto).lower()
        etapas_textos.append(texto)

        if not any(termo in texto_norm for termo in verbos_professor):
            avisos.append(f"Etapa '{titulo}': não descreve claramente a ação do professor.")
        if not any(termo in texto_norm for termo in termos_estudantes):
            avisos.append(f"Etapa '{titulo}': não descreve claramente a ação dos alunos.")
        if not any(termo in texto_norm for termo in termos_interacao_registro):
            avisos.append(f"Etapa '{titulo}': não prevê momentos de interação ou de registro (ex: caderno, duplas).")
        if conteudo_palavras and not any(termo in texto_norm for termo in conteudo_palavras):
            avisos.append(f"Etapa '{titulo}': não menciona termos específicos do conteúdo da aula.")

    if len(etapas_textos) >= 2:
        palavras_totais = []
        for etapa in etapas_textos:
            palavras_totais.extend([palavra for palavra in normalizar_texto(etapa).split() if len(palavra) > 3])
        if palavras_totais:
            counts = Counter(palavras_totais)
            repetidas = sum(contagem for contagem in counts.values() if contagem > 2)
            if len(palavras_totais) > 20 and (repetidas / len(palavras_totais)) > 0.4:
                avisos.append("Metodologia com alto índice de repetição de termos.")

    acessibilidade = aula.get("acessibilidade") or []
    acompanhamento = aula.get("acompanhamento") or []
    avisos.extend(
        problemas_lista_exatamente_tres(
            "Acompanhamento da aprendizagem",
            itens_lista_pedagogica(acompanhamento),
        )
    )
    avisos.extend(
        problemas_lista_exatamente_tres(
            "Acessibilidade",
            itens_lista_pedagogica(acessibilidade),
        )
    )
    texto_acessibilidade = " ".join(str(item) for item in acessibilidade).lower()
    placeholders_acess = {
        "estrategia generica", "apoio generico", "leitura simples", "informacao do material",
    }
    if any(placeholder in texto_acessibilidade for placeholder in placeholders_acess):
        avisos.append("Acessibilidade contém orientações ou placeholders genéricos.")
    if conteudo_palavras and not any(termo in texto_acessibilidade for termo in conteudo_palavras):
        avisos.append("Acessibilidade genérica sem ligação específica ao conteúdo ou tema da aula.")

    for problema in validar_requisitos_educacao_financeira(aula):
        avisos.append(problema)

    texto_total = " ".join([
        tema,
        aprendizagem,
        " ".join(etapas_textos),
        " ".join(acessibilidade),
        " ".join(str(item) for item in aula.get("acompanhamento", [])),
    ])
    texto_norm = normalizar_texto(texto_total)

    if tem_mojibake(texto_total):
        avisos.append("Texto com possível problema de codificação.")
    if "relacionado a relacionado" in texto_total.lower():
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
