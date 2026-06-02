import re

from core.lib.extrator_pdf import normalizar_texto


def perfil_suporta_eja(perfil: str) -> bool:
    return perfil in {"biologia", "ingles"}


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


def texto_tecnica_eja(tecnica: str, perfil: str, destino: str = "") -> str:
    tecnica_norm = normalizar_texto(tecnica)
    if "virem e conversem" in tecnica_norm:
        return "Aplicar a tecnica VIREM E CONVERSEM, incentivando os estudantes da EJA a compartilhar ideias, experiencias e hipoteses relacionadas ao tema."
    if "todo mundo escreve" in tecnica_norm:
        return "Utilizar a tecnica TODO MUNDO ESCREVE para garantir registro individual, participacao de todos e retomada das respostas durante a correcao."
    if "pause e responda" in tecnica_norm:
        return "Realizar perguntas rapidas no momento PAUSE E RESPONDA, verificando a compreensao e retomando pontos que apresentarem maior dificuldade."
    if "com suas palavras" in tecnica_norm:
        return "Aplicar a tecnica COM SUAS PALAVRAS para que os estudantes expliquem o conceito com linguagem propria e exemplos do cotidiano."
    if "de olho no modelo" in tecnica_norm:
        return "Utilizar a tecnica DE OLHO NO MODELO, apresentando um exemplo comentado antes da atividade individual."
    if "hora da leitura" in tecnica_norm:
        return "Conduzir a tecnica HORA DA LEITURA com pausas para vocabulario, compreensao e relacao com situacoes cotidianas."
    if perfil == "ingles" and ("listen and repeat" in tecnica_norm or "write and share" in tecnica_norm or "say it in english" in tecnica_norm):
        return f"Utilizar a tecnica {tecnica.upper()} com comandos curtos, repeticao orientada e participacao segura dos estudantes da EJA."
    return f"Incorporar a tecnica {tecnica.upper()} de forma contextualizada e acessivel para a turma da EJA."


def consolidar_blocos_eja(metodologia):
    grupos = [
        ("Para comecar", {"para comecar", "relembre", "abertura", "contextualizacao"}),
        ("Foco no conteudo", {"foco no conteudo", "leitura", "leitura e construcao do conteudo", "conceituacao", "desenvolvimento"}),
        ("Pause e responda", {"pause e responda", "na pratica", "atividade", "atividade principal", "socializacao", "socializacao e correcao"}),
        ("Encerramento", {"encerramento", "fechamento", "sistematizacao"}),
    ]
    saida = {titulo: [] for titulo, _ in grupos}
    extras = []

    for item in metodologia or []:
        if not isinstance(item, dict):
            extras.append(str(item))
            continue
        titulo_norm = normalizar_texto(item.get("titulo", ""))
        texto = re.sub(r"\s+", " ", str(item.get("texto", "") or "")).strip()
        if not texto:
            continue
        encaixado = False
        for titulo, aliases in grupos:
            if titulo_norm in aliases:
                saida[titulo].append(texto)
                encaixado = True
                break
        if not encaixado:
            extras.append(texto)

    if extras:
        saida["Foco no conteudo"].extend(extras)

    consolidada = []
    for titulo, _ in grupos:
        textos = saida[titulo]
        if textos:
            consolidada.append({"titulo": titulo, "texto": " ".join(textos)})
    return consolidada


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
    texto_existente = normalizar_texto(
        " ".join(str(item.get("texto", "") if isinstance(item, dict) else item) for item in metodologia or [])
    )
    usados = {tecnica for tecnica in tecnicas_pdf if normalizar_texto(tecnica) in texto_existente}

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
                "valorizando experiencias dos estudantes jovens e adultos sem infantilizar a abordagem."
            )
            for tecnica in tecnicas_pdf:
                if normalizar_texto(tecnica) in {"virem e conversem", "com suas palavras"} and tecnica not in usados:
                    complemento += " " + texto_tecnica_eja(tecnica, perfil)
                    usados.add(tecnica)
                    break
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"foco no conteudo", "conceituacao", "desenvolvimento", "leitura e construcao do conteudo", "leitura"}:
            if perfil == "ingles":
                complemento = (
                    " Explorar vocabulario e estruturas em ingles com exemplos funcionais do cotidiano, "
                    "pronuncia orientada e apoio visual, respeitando diferentes ritmos de leitura e fala da EJA."
                )
            else:
                complemento = (
                    " Explicar o conceito com linguagem acessivel e adulta, de forma pausada e dialogada, "
                    "relacionando o conteudo a situacoes praticas do cotidiano, saude, trabalho, tecnologia ou comunidade."
                )
            if tem_video:
                complemento += " Exibir o video indicado no material e orientar o registro das principais informacoes observadas."
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"pause e responda", "na pratica", "atividade", "atividade principal"}:
            complemento = (
                " Realizar perguntas rapidas para verificar a compreensao, promover correcao coletiva e retomar os pontos "
                "que apresentarem maior dificuldade."
            )
            for tecnica in tecnicas_pdf:
                if normalizar_texto(tecnica) in {"todo mundo escreve", "pause e responda", "write and share"} and tecnica not in usados:
                    complemento += " " + texto_tecnica_eja(tecnica, perfil)
                    usados.add(tecnica)
                    break
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"encerramento", "fechamento", "sistematizacao"}:
            if perfil == "ingles":
                complemento = (
                    " Encerrar retomando expressoes essenciais em ingles e relacionando o uso da lingua a situacoes reais "
                    "de comunicacao, trabalho, servicos, tecnologia ou convivio social."
                )
            else:
                complemento = (
                    f" Encerrar relacionando {tema} a aplicacoes praticas, tecnologias, saude, ambiente ou situacoes do cotidiano, "
                    "reforcando a relevancia do conteudo para a vida adulta e para a participacao social."
                )
            texto = _anexar_orientacao_unica(texto, complemento)

        novo["texto"] = texto
        adaptada.append(novo)

    if garantir_tecnicas_fn:
        adaptada = garantir_tecnicas_fn(adaptada, [tecnica for tecnica in tecnicas_pdf if tecnica not in usados])
        tecnicas_lemov = ["VIREM E CONVERSEM", "TODO MUNDO ESCREVE", "PAUSE E RESPONDA", "COM SUAS PALAVRAS", "DE OLHO NO MODELO", "HORA DA LEITURA", "UM PASSO DE CADA VEZ"]
        for item in adaptada:
            if isinstance(item, dict) and "texto" in item:
                texto_item = item["texto"]
                for tecnica in tecnicas_lemov:
                    texto_item = re.sub(re.escape(tecnica), tecnica, texto_item, flags=re.I)
                item["texto"] = texto_item
    return consolidar_blocos_eja(adaptada)
