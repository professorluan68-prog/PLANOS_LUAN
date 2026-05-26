from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def extrair_conceito_central(titulo: str) -> str:
    """Remove rotulos administrativos para deixar apenas o foco pedagogico."""
    texto = re.sub(r"\s+", " ", str(titulo or "")).strip(" -:.;")
    if not texto:
        return ""

    texto = re.sub(r"^(?:aula|slide|pagina|página)\s*(?:n[.o]?\s*)?\d{1,3}\s*[-:–—]?\s*", "", texto, flags=re.I)
    texto = re.sub(r"\s*[-:–—]?\s*parte\s+\d+\s*$", "", texto, flags=re.I)
    texto = re.sub(r"\s+(?:[1-4][º°oaª]?)\s*bimestre\b.*$", "", texto, flags=re.I)
    texto = re.sub(r"\s+ensino\s+(?:fundamental|medio|médio)\b.*$", "", texto, flags=re.I)
    return texto.strip(" -:.;")


def titulo_esta_truncado(titulo: str) -> bool:
    texto = re.sub(r"\s+", " ", str(titulo or "")).strip()
    if not texto:
        return True
    if texto.endswith((",", ";", ":", "-", "–", "—", "/")):
        return True
    ultimo = normalizar_texto(texto).split(" ")[-1]
    return ultimo in {"a", "as", "o", "os", "de", "da", "das", "do", "dos", "e", "em", "para", "por", "com"}


def detectar_contexto_metodologico(
    texto_pdf: str = "",
    nome_arquivo: str = "",
    disciplina: str = "",
    turma: str = "",
) -> str:
    base = normalizar_texto(" ".join([texto_pdf[:2000], nome_arquivo, disciplina, turma]))
    if any(termo in base for termo in ["cdp", "eja", "prisional", "penitenciario", "penitenciaria"]):
        return "cdp_eja"
    return "regular"


def detectar_nivel_ensino(turma: str = "", disciplina: str = "", texto_pdf: str = "") -> str:
    base = normalizar_texto(" ".join([turma, disciplina, texto_pdf[:1000]]))
    if "ensino medio" in base or re.search(r"\b[123]\s*(?:ano|serie|em)\b", base):
        return "ensino_medio"
    if "ensino fundamental" in base or re.search(r"\b[6789]\s*(?:ano|serie|ef|[a-e])\b", base):
        return "ensino_fundamental"
    return "nao_identificado"


VERBOS_POR_PERFIL = {
    "matematica": "modelar, calcular, comparar, justificar, verificar e representar",
    "educacao_financeira": "comparar, decidir, simular, calcular, justificar e planejar",
    "lingua_portuguesa_ef": "ler, localizar, inferir, comparar, registrar e revisar",
    "lingua_portuguesa_em": "analisar, interpretar, argumentar, relacionar, revisar e sintetizar",
    "leitura_redacao": "planejar, produzir, revisar, reescrever, argumentar e socializar",
    "ciencias_ef": "observar, comparar, investigar, representar, explicar e concluir",
    "biologia": "observar, classificar, relacionar, explicar, esquematizar e concluir",
    "quimica": "identificar, relacionar, representar, explicar, comparar e aplicar",
    "fisica": "observar, levantar hipoteses, calcular, interpretar, representar e concluir",
    "historia": "contextualizar, analisar fontes, comparar, problematizar e sintetizar",
    "geografia": "localizar, comparar, ler mapas, interpretar paisagens e relacionar escalas",
    "ingles": "reconhecer, escutar, repetir, ler, produzir e interagir",
    "arte": "apreciar, observar, experimentar, criar, registrar e socializar",
    "projeto_de_vida": "acolher, refletir, registrar, dialogar, planejar e sintetizar",
    "orientacao_estudos": "organizar, planejar, monitorar, revisar e consolidar",
    "tecnologia_inovacao": "investigar, planejar, testar, registrar, melhorar e compartilhar",
    "geral": "contextualizar, analisar, orientar, registrar, aplicar e sintetizar",
}


FRASES_PROBLEMATICAS = {
    "retomar conhecimentos previos da turma sobre": "Contextualizar {tema} por meio de perguntas iniciais e exemplos ligados ao material",
    "promover discussao sobre": "Conduzir dialogo orientado sobre {tema}, solicitando justificativas curtas e registro das ideias principais",
    "orientar a resolucao de atividades": "Acompanhar a atividade em etapas, modelando uma primeira resposta e verificando os registros durante a execucao",
    "realizar atividade sobre": "Propor atividade orientada sobre {tema}, com comandos divididos em etapas e retomada coletiva das respostas",
    "trabalhar o tema": "Explorar {tema} com apoio do material, exemplos e registros organizados no quadro",
    "desenvolver o conteudo": "Desenvolver {tema} de forma progressiva, conectando explicacao, exemplo e atividade guiada",
    "conteudo proposto": "{tema}",
}

PADROES_FRASES_PROBLEMATICAS = {
    "retomar conhecimentos previos da turma sobre": r"retomar conhecimentos pr[eé]vios da turma sobre",
    "promover discussao sobre": r"promover discuss[aã]o sobre",
    "orientar a resolucao de atividades": r"orientar a resolu[cç][aã]o de atividades",
    "realizar atividade sobre": r"realizar atividade sobre",
    "trabalhar o tema": r"trabalhar o tema",
    "desenvolver o conteudo": r"desenvolver o conte[uú]do",
    "conteudo proposto": r"conte[uú]do proposto",
}


RECURSOS_TECNOLOGICOS_CDP = (
    "computador",
    "celular",
    "internet",
    "aplicativo",
    "plataforma digital",
    "link",
    "site",
    "video online",
)


def regras_consolidadas_para_prompt(perfil: str, contexto: str = "regular", nivel: str = "") -> str:
    verbos = VERBOS_POR_PERFIL.get(perfil, VERBOS_POR_PERFIL["geral"])
    regras = [
        "REGRAS METODOLOGICAS CONSOLIDADAS:",
        "- Nao copie o titulo bruto do PDF como metodologia; remova rotulos como AULA 1, bimestre, ano e parte.",
        "- Extraia o conceito central e escreva cada etapa como acao docente concreta.",
        "- Evite frases genericas como 'retomar conhecimentos previos da turma sobre', 'promover discussao sobre' e 'orientar a resolucao de atividades'.",
        f"- Para este perfil, prefira verbos de acao como: {verbos}.",
        "- A metodologia precisa ter progressao: abertura/contextualizacao, desenvolvimento guiado, pratica/aplicacao e fechamento/verificacao.",
        "- Cite tecnicas LEMOV apenas quando elas aparecerem explicitamente no material.",
        "- Nao invente recursos, tempo de aula, etapas ou habilidades que nao estejam sustentados pelo PDF.",
    ]
    if nivel == "ensino_medio":
        regras.append("- Para Ensino Medio, mantenha maior densidade conceitual e linguagem analitica.")
    elif nivel == "ensino_fundamental":
        regras.append("- Para Ensino Fundamental, use comandos mais graduais, exemplos concretos e registros curtos.")
    if contexto == "cdp_eja":
        regras.extend(
            [
                "- Em contexto CDP/EJA, nao dependa de internet, celular, computador ou atividade extraclasse digital.",
                "- Em contexto CDP/EJA, priorize quadro, material impresso, oralidade mediada e registro no caderno.",
            ]
        )
    return "\n".join(regras)


def _substituir_frases_problematicas(texto: str, tema: str) -> str:
    texto_final = str(texto or "")
    tema_limpo = extrair_conceito_central(tema) or "o tema da aula"
    normalizado = normalizar_texto(texto_final)

    for frase, substituicao in FRASES_PROBLEMATICAS.items():
        if frase not in normalizado:
            continue
        padrao = re.compile(PADROES_FRASES_PROBLEMATICAS.get(frase, re.escape(frase)), flags=re.I)
        texto_final = padrao.sub(substituicao.format(tema=tema_limpo), texto_final, count=1)
        normalizado = normalizar_texto(texto_final)

    return texto_final


def sanitizar_texto_metodologico(
    texto: str,
    perfil: str = "geral",
    tema: str = "",
    contexto: str = "regular",
) -> str:
    texto_final = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto_final:
        return ""

    texto_final = re.sub(
        r"^(?:aula|slide|pagina|p?gina)\s*(?:n[.o]?\s*)?\d{1,3}\s*[-:??]?\s*",
        "",
        texto_final,
        flags=re.I,
    ).strip()
    texto_final = _substituir_frases_problematicas(texto_final, tema)

    if contexto == "cdp_eja" and any(recurso in normalizar_texto(texto_final) for recurso in RECURSOS_TECNOLOGICOS_CDP):
        texto_final = re.sub(
            r"\b(?:computador|celular|internet|aplicativo|plataforma digital|link|site|video online)\b",
            "material impresso, quadro e registro no caderno",
            texto_final,
            flags=re.I,
        )

    if perfil == "projeto_de_vida":
        texto_norm = normalizar_texto(texto_final)
        if "exposicao pessoal obrigatoria" in texto_norm:
            texto_final = re.sub(
                r"exposi[c?][a?]o pessoal obrigat[o?]ria",
                "socializacao voluntaria e mediada",
                texto_final,
                flags=re.I,
            )
        texto_final = re.sub(
            r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?(?:Virem e conversem|Todo mundo escreve|Com suas palavras|Hora da leitura|De olho no modelo|Pause e responda|Um passo de cada vez)["\']?(?:\s+para)?',
            "",
            texto_final,
            flags=re.I,
        )
        texto_final = re.sub(
            r"\b(?:VIREM E CONVERSEM|TODO MUNDO ESCREVE|COM SUAS PALAVRAS|HORA DA LEITURA|DE OLHO NO MODELO|PAUSE E RESPONDA|UM PASSO DE CADA VEZ)\b",
            "",
            texto_final,
            flags=re.I,
        )
        texto_final = re.sub(r"\s{2,}", " ", texto_final).strip(" ,;:-")

    return texto_final

    texto_final = re.sub(
        r"^(?:aula|slide|pagina|página)\s*(?:n[.o]?\s*)?\d{1,3}\s*[-:–—]?\s*",
        "",
        texto_final,
        flags=re.I,
    ).strip()
    texto_final = _substituir_frases_problematicas(texto_final, tema)

    if contexto == "cdp_eja" and any(recurso in normalizar_texto(texto_final) for recurso in RECURSOS_TECNOLOGICOS_CDP):
        texto_final = re.sub(
            r"\b(?:computador|celular|internet|aplicativo|plataforma digital|link|site|video online)\b",
            "material impresso, quadro e registro no caderno",
            texto_final,
            flags=re.I,
        )

    if perfil == "projeto_de_vida":
        texto_norm = normalizar_texto(texto_final)
        if "exposicao pessoal obrigatoria" in texto_norm:
            texto_final = re.sub(
                r"exposi[cç][aã]o pessoal obrigat[oó]ria",
                "socializacao voluntaria e mediada",
                texto_final,
                flags=re.I,
            )

    return texto_final


def naturalizar_texto_metodologico(texto: str) -> str:
    """Deixa a metodologia com voz de plano docente, sem rotulos tecnicos artificiais."""
    texto_final = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto_final:
        return ""
    tecnicas_explicitadas = (
        "VIREM E CONVERSEM",
        "TODO MUNDO ESCREVE",
        "COM SUAS PALAVRAS",
        "HORA DA LEITURA",
        "DE OLHO NO MODELO",
        "PAUSE E RESPONDA",
        "UM PASSO DE CADA VEZ",
    )
    preservar_tecnicas_explicitadas = any(tecnica in texto_final for tecnica in tecnicas_explicitadas)

    substituicoes = [
        (
            r"(?:A atividade inicia|Iniciar a aula|Iniciar|Comecar|Começar)\s+com\s+(?:a\s+)?t[eé?]cnica\s+[\"']?Virem e conversem[\"']?",
            "Promover uma conversa inicial em duplas",
        ),
        (
            r"(?:utilizando|usando|aplicando|por meio da|com)\s+(?:a\s+)?t[eé?]cnica\s+[\"']?Virem e conversem[\"']?",
            "promovendo conversa em duplas",
        ),
        (
            r"Propor\s+[\"']?Virem e conversem[\"']?\s+para",
            "Promover conversa em duplas para",
        ),
        (
            r"Incentivar a discuss[aã?]o em duplas atrav[eé?]s da t[eé?]cnica\s+[\"']?Virem e conversem[\"']?",
            "Promover discussao em duplas",
        ),
        (
            r"No momento\s+[\"']?Virem e conversem[\"']?,?\s*os alunos mobilizam conhecimentos pr[eé?]vios antes da explica[cç?][aã?]o inicial\.?",
            "Promover conversa em duplas para que compartilhem percepcoes, levantem hipoteses e retomem conhecimentos previos.",
        ),
        (
            r"(?:Utilizar|Usar|Aplicar)\s+(?:a\s+)?t[eé?]cnica\s+[\"']?Todo mundo escreve[\"']?",
            "Solicitar registro individual no caderno",
        ),
        (
            r"(?:usando|com)\s+[\"']?Todo mundo escreve[\"']?\s+para garantir registro individual",
            "garantindo registro individual no caderno",
        ),
        (
            r"No momento\s+[\"']?Todo mundo escreve[\"']?,?\s*os alunos (?:registram|organizam por escrito)[^.]+\.?",
            "Solicitar registro individual no caderno com as ideias principais, hipoteses ou respostas construidas na atividade.",
        ),
        (
            r"(?:Utilizar|Usar|Aplicar)\s+(?:a\s+)?t[eé?]cnica\s+[\"']?Hora da leitura[\"']?",
            "Conduzir leitura orientada",
        ),
        (
            r"(?:durante a atividade|na atividade)\s+[\"']?Hora da Leitura[\"']?",
            "durante uma leitura orientada",
        ),
        (
            r"Em\s+[\"']?Hora da leitura[\"']?,?\s*o professor conduz a leitura orientada do material, com pausas para verifica[cç?][aã?]o de compreens[aã?]o\.?",
            "Conduzir leitura orientada do material, realizando pausas para destacar informacoes importantes e verificar a compreensao da turma.",
        ),
        (
            r"(?:Utilizar|Usar|Aplicar)\s+(?:a\s+)?t[eé?]cnica\s+[\"']?Um passo de cada vez[\"']?",
            "Organizar a explicacao em etapas curtas",
        ),
        (
            r"Em\s+[\"']?Um passo de cada vez[\"']?,?\s*o professor organiza a explica[cç?][aã?]o em etapas curtas e vis[ií?]veis\.?",
            "Organizar a explicacao em etapas curtas, retomando cada procedimento antes de avancar para o seguinte.",
        ),
        (
            r"(?:Utilizar|Usar|Aplicar)\s+(?:a\s+)?t[eé?]cnica\s+[\"']?De olho no modelo[\"']?",
            "Apresentar um exemplo comentado",
        ),
        (
            r"Em\s+[\"']?De olho no modelo[\"']?,?\s*o professor explicita um exemplo resolvido antes da atividade individual\.?",
            "Apresentar um exemplo comentado antes da atividade individual, destacando os criterios que orientam a resposta.",
        ),
        (
            r"Em\s+[\"']?Pause e responda[\"']?,?\s*(?:a turma interrompe brevemente a explica[cç?][aã?]o para verificar a compreens[aã?]o do que foi apresentado|o professor verifica a compreens[aã?]o da turma antes de avan[cç?]ar para a etapa seguinte)\.?",
            "Realizar pausas de checagem da compreensao, retomando as respostas da turma e esclarecendo duvidas antes de avancar.",
        ),
        (
            r"No momento\s+[\"']?PAUSE E RESPONDA[\"']?,?\s*(?:a turma interrompe brevemente a explica[cç?][aã?]o para verificar a compreens[aã?]o do que foi apresentado)\.?",
            "Realizar pausas de checagem da compreensao, retomando as respostas da turma e esclarecendo duvidas antes de avancar.",
        ),
        (
            r"Em\s+[\"']?Com suas palavras[\"']?,?\s*os alunos retomam o que compreenderam, sintetizando os pontos principais\.?",
            "Pedir que os estudantes expliquem, com suas proprias palavras, os pontos principais trabalhados.",
        ),
        (
            r"Em\s+[\"']?Com suas palavras[\"']?,?\s*os alunos explicam oralmente ou por escrito o que compreenderam\.?",
            "Pedir que os estudantes expliquem oralmente ou por escrito o que compreenderam.",
        ),
        (
            r"Relacionar a explica[cç?][aã?]o aos registros anteriores para que a turma perceba continuidade, aprofundamento e novos desafios\.?",
            "Retomar registros anteriores quando necessario, ajudando a turma a perceber a continuidade do estudo.",
        ),
        (
            r"Atividade:\s*(?:Mediar|Acompanhar|Conduzir|Orientar)\s+a atividade principal do material,\s*preservando o produto esperado:\s*([^.]+)\.",
            r"Na atividade principal, orientar a producao de \1 com acompanhamento dos registros da turma.",
        ),
        (
            r"Atividade:\s*(?:Mediar|Acompanhar|Conduzir|Orientar)\s+a atividade principal do material para que os estudantes produzam ([^,.]+),\s*acompanhando registros, duvidas e socializacao das respostas\.",
            r"Na atividade principal, orientar a producao de \1, acompanhando registros, duvidas e socializacao das respostas.",
        ),
        (
            r"O desenvolvimento mant[eé]m o momento\s+[\"']?([^\"'.]+)[\"']?\s+como parte da condu[cç][aã]o da aula\.?",
            r"Incorporar esse momento ao desenvolvimento da aula, articulando-o aos exemplos, registros e intervencoes do professor.",
        ),
    ]

    for padrao, substituicao in substituicoes:
        if preservar_tecnicas_explicitadas and any(normalizar_texto(tecnica) in normalizar_texto(padrao) for tecnica in tecnicas_explicitadas):
            continue
        texto_final = re.sub(padrao, substituicao, texto_final, flags=re.I)

    if not preservar_tecnicas_explicitadas:
        texto_final = re.sub(r"\bt[eé?]cnica\s+[\"']([^\"']+)[\"']", r"estrategia de \1", texto_final, flags=re.I)
    texto_final = re.sub(r"\s+", " ", texto_final).strip()
    texto_final = re.sub(r"\s+\.", ".", texto_final)
    texto_final = re.sub(r"\.{2,}", ".", texto_final)
    texto_final = re.sub(r"\bpersonagen\b", "personagens", texto_final, flags=re.I)
    texto_final = re.sub(r"\bD[ií]vida a turma\b", "Dividir a turma", texto_final, flags=re.I)
    texto_final = re.sub(r"\bclasifiquem\b", "classifiquem", texto_final, flags=re.I)
    return texto_final


def naturalizar_metodologia_professor(metodologia: list[Any]) -> list[Any]:
    naturalizada = []
    for item in metodologia or []:
        if isinstance(item, dict):
            novo_item = dict(item)
            novo_item["texto"] = naturalizar_texto_metodologico(novo_item.get("texto", ""))
            naturalizada.append(novo_item)
        else:
            naturalizada.append(naturalizar_texto_metodologico(str(item)))
    return naturalizada


def encontrar_alertas_metodologia(texto: str, contexto: str = "regular") -> list[str]:
    normalizado = normalizar_texto(texto)
    alertas = []
    for frase in FRASES_PROBLEMATICAS:
        if frase in normalizado:
            alertas.append(f"frase_generica:{frase}")
    if re.search(r"\baula\s*\d{1,3}\s*[-:]", normalizado):
        alertas.append("titulo_bruto")
    if titulo_esta_truncado(texto):
        alertas.append("texto_incompleto")
    if len(re.findall(r"\w+", normalizado)) < 12:
        alertas.append("texto_curto")
    if contexto == "cdp_eja" and any(recurso in normalizado for recurso in RECURSOS_TECNOLOGICOS_CDP):
        alertas.append("recurso_tecnologico_cdp")
    return alertas


def revisar_metodologia(
    metodologia: list[Any],
    perfil: str = "geral",
    tema: str = "",
    contexto: str = "regular",
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    revisada: list[dict[str, str]] = []
    alertas: list[str] = []

    for indice, item in enumerate(metodologia or []):
        if isinstance(item, dict):
            titulo = re.sub(r"\s+", " ", str(item.get("titulo", "") or "")).strip() or f"Etapa {indice + 1}"
            texto = item.get("texto", "")
        else:
            titulo = f"Etapa {indice + 1}"
            texto = str(item or "")

        texto_limpo = sanitizar_texto_metodologico(texto, perfil=perfil, tema=tema, contexto=contexto)
        alertas.extend(f"{indice + 1}:{alerta}" for alerta in encontrar_alertas_metodologia(texto_limpo, contexto=contexto))
        if texto_limpo:
            revisada.append({"titulo": titulo, "texto": texto_limpo})

    score = 100
    score -= min(60, 10 * len(alertas))
    if len(revisada) < 3:
        score -= 20

    return revisada, {
        "score": max(0, score),
        "alertas": alertas,
        "aceita": bool(revisada) and score >= 40,
    }
