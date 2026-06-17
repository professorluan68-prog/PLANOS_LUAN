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
    """Faz uma checagem semântica detalhada e pedagógica antes do preenchimento do DOCX."""
    avisos = []

    disciplina = normalizar_texto(aula.get("disciplina", ""))
    tema = normalizar_texto(aula.get("tema", ""))
    aprendizagem = normalizar_texto(aula.get("aprendizagem", ""))
    
    # 1. Validação de genericidade do Tema
    if len(tema) < 8 or tema in {"estudar matematica", "aula de ciencias", "tema da aula"}:
        avisos.append("Tema muito genérico ou vazio.")
        
    metodologia = aula.get("metodologia", [])
    
    # 2. Validação da metodologia (deve ter exatamente 4 etapas)
    if len(metodologia) != 4:
        avisos.append(f"Metodologia com número incorreto de etapas ({len(metodologia)}). Devem ser exatamente 4.")

    conteudo_ref = tema + " " + aprendizagem
    conteudo_palavras = {w for w in conteudo_ref.split() if len(w) > 3 and w not in {
        "para", "como", "com", "uma", "mais", "sobre", "aula", "conteudo", "tema", "estudantes", "alunos", "professor",
        "ciencias", "matematica", "portugues", "aula", "atividade", "recurso"
    }}

    # Listas de termos para validação das regras de etapas
    verbos_professor = {"professor", "docente", "mediador", "apresentar", "conduzir", "propor", "solicitar", "orientar", "explicar", "retomar", "exibe", "pergunta", "mostra", "lidera", "mediar"}
    termos_estudantes = {"aluno", "estudante", "turma", "dupla", "grupo", "eles", "compartilhar", "escrever", "responder", "resolver", "realizar", "discutir", "escrevem", "respondem", "resolvem", "participa"}
    termos_interacao_registro = {"caderno", "registro", "respost", "escrev", "dupla", "grupo", "roda", "discussao", "debate", "socializ", "cadernos", "anot", "compartilh"}

    etapas_textos = []
    for item in metodologia:
        if isinstance(item, dict):
            titulo = item.get("titulo", "")
            texto = item.get("texto", "")
            texto_norm = normalizar_texto(texto).lower()
            etapas_textos.append(texto)
            
            # Verificação de ação do professor
            if not any(w in texto_norm for w in verbos_professor):
                avisos.append(f"Etapa '{titulo}': não descreve claramente a ação do professor.")
                
            # Verificação de ação dos alunos
            if not any(w in texto_norm for w in termos_estudantes):
                avisos.append(f"Etapa '{titulo}': não descreve claramente a ação dos alunos.")
                
            # Verificação de interação ou registro
            if not any(k in texto_norm for k in termos_interacao_registro):
                avisos.append(f"Etapa '{titulo}': não prevê momentos de interação ou de registro (ex: caderno, duplas).")
                
            # Verificação de conteúdo específico da aula
            if conteudo_palavras and not any(w in texto_norm for w in conteudo_palavras):
                avisos.append(f"Etapa '{titulo}': não menciona termos específicos do conteúdo da aula.")

    # 3. Validação de repetição na Metodologia
    if len(etapas_textos) >= 2:
        from collections import Counter
        palavras_totais = []
        for e in etapas_textos:
            palavras_totais.extend([w for w in normalizar_texto(e).split() if len(w) > 3])
        if palavras_totais:
            counts = Counter(palavras_totais)
            repetidas = sum(count for word, count in counts.items() if count > 2)
            if len(palavras_totais) > 20 and (repetidas / len(palavras_totais)) > 0.4:
                avisos.append("Metodologia com alto índice de repetição de termos.")

    # 4. Validação de Acessibilidade específica
    acessibilidade = aula.get("acessibilidade") or []
    texto_acessibilidade = " ".join(str(i) for i in acessibilidade).lower()
    placeholders_acess = {"estrategia generica", "apoio generico", "leitura simples", "informacao do material", "apoio generico"}
    if any(p in texto_acessibilidade for p in placeholders_acess):
        avisos.append("Acessibilidade contém orientações ou placeholders genéricos.")
    if conteudo_palavras and not any(w in texto_acessibilidade for w in conteudo_palavras):
        avisos.append("Acessibilidade genérica sem ligação específica ao conteúdo ou tema da aula.")

    # 5. Outros alertas legados/técnicos
    texto_total = " ".join([tema, aprendizagem, " ".join(etapas_textos), " ".join(acessibilidade), " ".join(str(item) for item in aula.get("acompanhamento", []))])
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
