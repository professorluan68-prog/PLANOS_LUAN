from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


_PADROES_MOJIBAKE = ("Ã", "Â", "â€", "â€“", "â€”", "�")
_CORRECOES_PONTUAIS_MOJIBAKE = {
    "an?lise": "análise",
    "discuss?o": "discussão",
    "situa??es": "situações",
    "aplica??o": "aplicação",
    "pr?tica": "prática",
    "tecnol?gica": "tecnológica",
}
_FINAIS_CONECTIVOS = {
    "a",
    "as",
    "o",
    "os",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "para",
    "com",
    "e",
    "em",
    "por",
}


def tem_mojibake(texto: str) -> bool:
    texto = str(texto or "")
    return any(padrao in texto for padrao in _PADROES_MOJIBAKE) or any(
        padrao in texto for padrao in _CORRECOES_PONTUAIS_MOJIBAKE
    )


def corrigir_mojibake(texto: str) -> str:
    texto_original = str(texto or "")
    if not texto_original:
        return ""

    candidatos = [texto_original]
    if any(padrao in texto_original for padrao in _PADROES_MOJIBAKE):
        for codec in ("latin1", "cp1252"):
            try:
                candidatos.append(texto_original.encode(codec).decode("utf-8"))
            except Exception:
                continue

    def pontuar(valor: str) -> tuple[int, int]:
        score = sum(valor.count(padrao) for padrao in _PADROES_MOJIBAKE)
        score += sum(valor.count(padrao) for padrao in _CORRECOES_PONTUAIS_MOJIBAKE)
        return score, len(valor)

    melhor = min(candidatos, key=pontuar)
    for errado, certo in _CORRECOES_PONTUAIS_MOJIBAKE.items():
        melhor = melhor.replace(errado, certo)
    return melhor


def limitar_texto_natural(texto: str, limite: int = 220) -> str:
    texto = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip())
    if len(texto) <= limite:
        return texto

    sentencas = re.split(r"(?<=[.!?])\s+", texto)
    acumulado = ""
    for sentenca in sentencas:
        candidato = f"{acumulado} {sentenca}".strip()
        if len(candidato) <= limite:
            acumulado = candidato
        else:
            break

    if acumulado:
        texto = acumulado
    else:
        texto = texto[:limite].rsplit(" ", 1)[0].rstrip(" ,;:-") + "."

    palavras = normalizar_texto(texto).split()
    if palavras and palavras[-1] in _FINAIS_CONECTIVOS:
        base = texto.rsplit(" ", 1)[0].rstrip(" ,;:-")
        if base:
            texto = base + "."
    return texto


def extrair_conceito_central(titulo: str) -> str:
    """Remove rotulos administrativos para deixar apenas o foco pedagogico."""
    texto = corrigir_mojibake(re.sub(r"\s+", " ", str(titulo or "")).strip(" -:.;"))
    if not texto:
        return ""

    texto = re.sub(
        r"^(?:aula|slide|p[aá]gina|p?gina)\s*(?:n[.o]?\s*)?\d{1,3}\s*[-:–—]?\s*",
        "",
        texto,
        flags=re.I,
    )
    texto = re.sub(r"\s*[-:–—]?\s*parte\s+\d+\s*$", "", texto, flags=re.I)
    texto = re.sub(r"\s+(?:[1-4][º°oaª]?)\s*bimestre\b.*$", "", texto, flags=re.I)
    texto = re.sub(r"\s+ensino\s+(?:fundamental|medio|m[eé]dio)\b.*$", "", texto, flags=re.I)
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


def _ajustar_texto_matematica(texto: str) -> str:
    texto_final = str(texto or "")
    substituicoes = [
        (r"\bmaterial impresso,\s*quadro e registro no caderno\s+discada e banda larga\b", "internet discada e banda larga"),
        (r"\bmaterial impresso,\s*quadro e registro no caderno\b", "o material da aula"),
        (r"situa[cç][aã]o do acesso [àa]?\s+o material da aula", "situação do cotidiano apresentada no material"),
        (r"acesso [àa]?\s+o material da aula", "situação do cotidiano apresentada no material"),
        (r"diferen[cç]as entre o material da aula discada e banda larga", "diferenças entre internet discada e banda larga"),
        (r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?Virem e conversem["\']?(?:\s+para)?', "Promover conversa inicial em duplas para"),
        (r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?Todo mundo escreve["\']?(?:\s+para)?', "Solicitar registro individual no caderno para"),
        (r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?Com suas palavras["\']?(?:\s+para)?', "Solicitar síntese oral ou escrita para"),
        (r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?De olho no modelo["\']?(?:\s+para)?', "Apresentar um exemplo comentado para"),
        (r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?Hora da leitura["\']?(?:\s+para)?', "Conduzir leitura orientada para"),
        (r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?Um passo de cada vez["\']?(?:\s+para)?', "Organizar a explicação em etapas para"),
        (r'\b(?:Aplicar|Utilizar|Usar|Incorporar)\s+(?:a\s+)?t[eé]cnica\s+["\']?Pause e responda["\']?(?:\s+para)?', "Realizar uma pausa de checagem para"),
        (r"\bVirem e conversem\b", "conversa inicial em duplas"),
        (r"\bTodo mundo escreve\b", "registro individual no caderno"),
        (r"\bCom suas palavras\b", "síntese oral ou escrita"),
        (r"\bDe olho no modelo\b", "exemplo comentado"),
        (r"\bHora da leitura\b", "leitura orientada"),
        (r"\bUm passo de cada vez\b", "explicação em etapas"),
        (r"\bPause e responda\b", "pausa de checagem"),
        (r"\bum o material da aula\b", "material de estudo"),
        (r"\buma o material da aula\b", "o material da aula"),
        (r"(?:utilizando|usando|com)\s+a\s+t[eé]cnica\s+conversa inicial em duplas", "promovendo uma conversa inicial em duplas"),
        (r"(?:Aplicar|Utilizar|Usar|Incorporar)\s+a\s+t[eé]cnica\s+explica[cç][aã]o em etapas", "Organizar a explicação em etapas"),
        (r"Realizar o momento pausa de checagem", "Realizar uma pausa de checagem"),
        (r"Solicitar s[ií]ntese oral ou escrita para que os estudantes expliquem oralmente ou por escrito o que compreenderam", "Solicitar que os estudantes expliquem, oralmente ou por escrito, o que compreenderam"),
        (r"(?:aplicando|utilizando|empregando|implementando)\s+(?:a\s+)?t[eé]cnica\s+registro individual no caderno", "solicitando registro individual no caderno"),
        (r"(?:aplicando|utilizando|empregando|implementando)\s+(?:a\s+)?t[eé]cnica\s+s[ií]ntese oral ou escrita", "pedindo síntese oral ou escrita"),
        (r"(?:aplicando|utilizando|empregando|implementando)\s+(?:a\s+)?t[eé]cnica\s+explica[cç][aã]o em etapas", "organizando a explicação em etapas"),
        (r"(?:aplicando|utilizando|empregando|implementando)\s+(?:a\s+)?t[eé]cnica\s+exemplo comentado", "apresentando um exemplo comentado"),
        (r"(?:aplicando|utilizando|empregando|implementando)\s+(?:a\s+)?t[eé]cnica\s+leitura orientada", "conduzindo leitura orientada"),
        (r"(?:aplicando|utilizando|empregando|implementando)\s+(?:a\s+)?t[eé]cnica\s+pausa de checagem", "realizando uma pausa de checagem"),
        (r"com a t[eé]cnica explica[cç][aã]o em etapas", "com explicação em etapas"),
        (r"Conduzir leitura orientada para conduzir a leitura orientada do material", "Conduzir leitura orientada do material"),
        (r"Empregar a t[eé]cnica s[ií]ntese oral ou escrita,\s*solicitando", "Solicitar"),
        (r"Apresentar um exemplo comentado para ao desenvolvimento da aula", "Incorporar um exemplo comentado ao desenvolvimento da aula"),
    ]
    for padrao, substituicao in substituicoes:
        texto_final = re.sub(padrao, substituicao, texto_final, flags=re.I)
    texto_final = re.sub(r"\s{2,}", " ", texto_final).strip(" ,;:-")
    return texto_final


def sanitizar_texto_metodologico(
    texto: str,
    perfil: str = "geral",
    tema: str = "",
    contexto: str = "regular",
) -> str:
    texto_final = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip())
    if not texto_final:
        return ""

    texto_final = re.sub(
        r"^(?:aula|slide|p[aá]gina|p?gina)\s*(?:n[.o]?\s*)?\d{1,3}\s*[-:–—]?\s*",
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

    if perfil in {"matematica", "educacao_financeira"}:
        texto_final = _ajustar_texto_matematica(texto_final)

    if perfil == "projeto_de_vida":
        texto_norm = normalizar_texto(texto_final)
        if "exposicao pessoal obrigatoria" in texto_norm:
            texto_final = re.sub(
                r"exposi[cç][aã]o pessoal obrigat[oó]ria",
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
