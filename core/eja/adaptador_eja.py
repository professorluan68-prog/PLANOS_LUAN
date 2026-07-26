import re

from core.lib.extrator_pdf import normalizar_texto


def perfil_suporta_eja(perfil: str) -> bool:
    return perfil in {"biologia", "ingles", "lideranca_oratoria"}


def _anexar_orientacao_unica(texto: str, orientacao: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    orientacao = re.sub(r"\s+", " ", str(orientacao or "")).strip()
    if not orientacao:
        return texto
    if normalizar_texto(orientacao[:80]) in normalizar_texto(texto):
        return texto
    if texto and not texto.endswith((".", "!", "?")):
        texto += "."
    return f"{texto} {orientacao}".strip() if texto else orientacao


def _antepor_orientacao_unica(orientacao: str, texto: str) -> str:
    orientacao = re.sub(r"\s+", " ", str(orientacao or "")).strip()
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not orientacao:
        return texto
    if normalizar_texto(orientacao[:80]) in normalizar_texto(texto):
        return texto
    if orientacao and not orientacao.endswith((".", "!", "?")):
        orientacao += "."
    return f"{orientacao} {texto}".strip() if texto else orientacao


_SUBSTITUICOES_TECNICAS_EJA = {
    "VIREM E CONVERSEM": "conversa breve em duplas",
    "TODO MUNDO ESCREVE": "registro individual",
    "COM SUAS PALAVRAS": "explicacao com linguagem propria",
    "HORA DA LEITURA": "leitura orientada",
    "DE OLHO NO MODELO": "exemplo comentado",
    "PAUSE E RESPONDA": "verificacao da aprendizagem",
    "UM PASSO DE CADA VEZ": "explicacao em etapas",
    "LISTEN AND REPEAT": "repeticao orientada",
    "WRITE AND SHARE": "registro e compartilhamento",
    "SAY IT IN ENGLISH": "producao oral em ingles",
}

_TITULOS_TECNICAS_EJA = {
    normalizado: substituto.capitalize()
    for normalizado, substituto in (
        (normalizar_texto(nome), valor)
        for nome, valor in _SUBSTITUICOES_TECNICAS_EJA.items()
    )
}


def _remover_nomes_tecnicas_eja(texto: str) -> str:
    resultado = str(texto or "")
    for nome, substituto in sorted(
        _SUBSTITUICOES_TECNICAS_EJA.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        resultado = re.sub(rf"\b{re.escape(nome)}\b", substituto, resultado, flags=re.I)
    resultado = re.sub(
        r"\btecnicas?\s+(?=(?:conversa breve em duplas|registro individual|explicacao com linguagem propria|leitura orientada|exemplo comentado|verificacao da aprendizagem|explicacao em etapas|repeticao orientada|registro e compartilhamento|producao oral em ingles)\b)",
        "",
        resultado,
        flags=re.I,
    )
    return re.sub(r"\s+", " ", resultado).strip()


def texto_tecnica_eja(tecnica: str, perfil: str, destino: str = "") -> str:
    tecnica_norm = normalizar_texto(tecnica)
    if "virem e conversem" in tecnica_norm:
        return "Promover uma conversa breve em duplas, incentivando os estudantes da EJA a compartilhar ideias, experiencias e hipoteses relacionadas ao tema."
    if "todo mundo escreve" in tecnica_norm:
        return "Solicitar um registro individual no caderno, garantindo a participacao de todos e a retomada das respostas durante a correcao."
    if "pause e responda" in tecnica_norm:
        return "Realizar perguntas rapidas para verificar a compreensao e retomar os pontos que apresentarem maior dificuldade."
    if "com suas palavras" in tecnica_norm:
        return "Solicitar que os estudantes expliquem o conceito com linguagem propria e exemplos do cotidiano."
    if "de olho no modelo" in tecnica_norm:
        return "Apresentar um exemplo comentado antes da atividade individual."
    if "hora da leitura" in tecnica_norm:
        return "Conduzir uma leitura orientada com pausas para vocabulario, compreensao e relacao com situacoes cotidianas."
    if perfil == "ingles" and ("listen and repeat" in tecnica_norm or "write and share" in tecnica_norm or "say it in english" in tecnica_norm):
        return "Trabalhar a pronuncia e a producao oral com comandos curtos, repeticao orientada e participacao segura dos estudantes da EJA."
    return "Incorporar essa acao de forma contextualizada e acessivel para a turma da EJA."


def consolidar_blocos_eja(metodologia):
    """Limpa blocos EJA sem impor uma quantidade fixa de etapas.

    A ordem e os titulos do PDF/DOCX devem ser preservados. Apenas nomes de
    tecnicas pedagogicas sao convertidos para descricoes de acoes.
    """
    resultado = []
    for item in metodologia or []:
        if isinstance(item, dict):
            titulo_original = str(item.get("titulo", "") or "").strip()
            titulo_norm = normalizar_texto(titulo_original)
            titulo = _TITULOS_TECNICAS_EJA.get(titulo_norm, titulo_original)
            texto = _remover_nomes_tecnicas_eja(item.get("texto", ""))
        else:
            titulo = "Desenvolvimento"
            texto = _remover_nomes_tecnicas_eja(item)
        if texto:
            resultado.append({"titulo": titulo or "Desenvolvimento", "texto": texto})
    return resultado


from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural

def adaptar_metodologia_eja(
    metodologia,
    perfil: str,
    tema: str,
    texto_pdf: str,
    tecnicas_pdf: list[str] | None = None,
    garantir_tecnicas_fn=None,
):
    if not perfil_suporta_eja(perfil):
        return metodologia

    tecnicas_pdf = [tecnica for tecnica in list(tecnicas_pdf or []) if normalizar_texto(tecnica) != "relembre"]
    tem_video = "video" in normalizar_texto(texto_pdf)
    adaptada = []
    usados = set()
    for item in metodologia or []:
        if not isinstance(item, dict):
            adaptada.append(item)
            continue

        novo = dict(item)
        titulo = normalizar_texto(novo.get("titulo", ""))
        texto = re.sub(r"\s+", " ", str(novo.get("texto", "") or "")).strip()

        if titulo in {"para comecar", "relembre", "abertura", "contextualizacao"}:
            complemento = (
                f" Retomar conhecimentos previos sobre {tema} por meio de perguntas simples e contextualizadas, "
                "valorizando experiencias de vida e de trabalho dos estudantes jovens e adultos sem infantilizar a abordagem."
            )
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"foco no conteudo", "conceituacao", "desenvolvimento", "leitura e construcao do conteudo", "leitura"}:
            if perfil == "ingles":
                complemento = (
                    " Explorar vocabulario e estruturas em ingles com exemplos funcionais do cotidiano, "
                    "pronuncia orientada e apoio visual, respeitando diferentes ritmos de leitura e fala da EJA, "
                    "com aplicacoes em comunicacao profissional e servicos."
                )
            else:
                complemento = (
                    " Explicar o conceito com linguagem acessivel e adulta, de forma pausada e dialogada, "
                    "relacionando o conteudo a situacoes praticas do cotidiano e do mundo do trabalho, "
                    "quando essa relacao for pertinente."
                )
            if tem_video:
                complemento += " Exibir o video indicado no material e orientar o registro das principais informacoes observadas."
            texto = _antepor_orientacao_unica(complemento, texto)

        elif titulo in {"pause e responda", "na pratica", "atividade", "atividade principal"}:
            complemento = (
                " Realizar perguntas rapidas para verificar a compreensao, promover correcao coletiva e retomar os pontos "
                "que apresentarem maior dificuldade. Aplicar o que foi estudado a uma situacao concreta da vida ou do trabalho, quando possivel."
            )
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"encerramento", "fechamento", "sistematizacao"}:
            if perfil == "ingles":
                complemento = (
                    " Encerrar retomando expressoes essenciais em ingles e relacionando o uso da lingua a situacoes reais "
                    "de comunicacao, trabalho, servicos, tecnologia ou convivio social."
                )
            else:
                complemento = (
                    f" Encerrar relacionando {tema} a aplicacoes praticas da vida adulta e do trabalho, "
                    "reforcando sua relevancia para a participacao social."
                )
            texto = _anexar_orientacao_unica(texto, complemento)

        texto = corrigir_mojibake(texto)
        texto = limitar_texto_natural(texto, limite=350)
        novo["texto"] = texto
        adaptada.append(novo)

    return consolidar_blocos_eja(adaptada)


def adaptar_listas_eja(
    acompanhamento,
    acessibilidade,
    tema: str,
    perfil: str,
):
    """Adapta e fecha as duas listas pedagógicas no contrato de três itens."""
    tema_limpo = re.sub(r"\s+", " ", str(tema or "conteudo da aula")).strip()

    acompanhamento_fallback = [
        f"Verificar se os estudantes compreendem os pontos principais de {tema_limpo}.",
        f"Observar se relacionam {tema_limpo} a uma situacao do cotidiano ou do trabalho, quando pertinente.",
        f"Analisar os registros e as explicacoes produzidas sobre {tema_limpo}, retomando duvidas individualmente.",
    ]
    acessibilidade_fallback = [
        "Usar linguagem simples, exemplos adultos e explicacao dos termos essenciais.",
        "Relacionar o conteudo a experiencias de vida e de trabalho dos estudantes, sem infantilizar a abordagem.",
        "Permitir resposta oral, escrita ou em topicos, com tempo ampliado e apoio individual quando necessario.",
    ]

    def preparar(itens, fallback):
        saida = []
        for item in list(itens or []):
            texto = _remover_nomes_tecnicas_eja(item)
            if not texto:
                continue
            if not any(
                termo in normalizar_texto(texto)
                for termo in ("trabalho", "profissional", "cotidiano", "vida adulta")
            ):
                texto = _anexar_orientacao_unica(
                    texto,
                    " Relacionar a observacao a situacoes da vida adulta e do trabalho, quando pertinente.",
                )
            saida.append(texto)
        for item in fallback:
            if len(saida) >= 3:
                break
            saida.append(item)
        return saida[:3]

    return (
        preparar(acompanhamento, acompanhamento_fallback),
        preparar(acessibilidade, acessibilidade_fallback),
    )
