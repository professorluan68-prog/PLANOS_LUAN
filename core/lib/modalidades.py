from core.eja.adaptador_eja import adaptar_metodologia_eja
from core.lib.classificador import normalizar_texto


def _acrescimo_generico_para_tecnica(tecnica: str, titulo: str) -> str:
    tecnica_norm = normalizar_texto(tecnica).upper()
    titulo_norm = normalizar_texto(titulo)

    if tecnica_norm == "VIREM E CONVERSEM":
        return " Promover uma troca breve de ideias em duplas, com foco nas hipoteses e nas primeiras percepcoes sobre o tema."
    if tecnica_norm == "TODO MUNDO ESCREVE":
        return " Solicitar registro individual no caderno para organizar hipoteses, conceitos centrais ou respostas iniciais."
    if tecnica_norm == "COM SUAS PALAVRAS":
        return " Pedir que os estudantes expliquem, oralmente ou por escrito, o que compreenderam com suas proprias palavras."
    if tecnica_norm == "DE OLHO NO MODELO":
        return " Apresentar um exemplo comentado como referencia antes da atividade principal."
    if tecnica_norm == "HORA DA LEITURA":
        return " Conduzir leitura orientada do material, com pausas para destacar informacoes importantes."
    if tecnica_norm == "UM PASSO DE CADA VEZ":
        return " Organizar a explicacao em etapas curtas, verificando a compreensao ao longo do percurso."
    if tecnica_norm == "PAUSE E RESPONDA":
        return " Realizar uma pausa de checagem para verificar a compreensao e retomar respostas da turma antes de avancar."

    if titulo_norm in {"encerramento", "segundo momento"}:
        return " Retomar os principais pontos da aula com uma breve verificacao de compreensao antes do fechamento."
    return " Integrar esse procedimento ao desenvolvimento da aula com exemplos, registros e intervencoes do professor."


def garantir_tecnicas_lemov_na_metodologia(metodologia, tecnicas_pdf: list[str]):
    if not metodologia or not tecnicas_pdf:
        return metodologia

    metodologia_ajustada = []
    textos_norm = []
    for item in metodologia:
        if isinstance(item, dict):
            textos_norm.append(normalizar_texto(item.get("texto", "")))
        else:
            textos_norm.append(normalizar_texto(str(item)))

    mapa_procura = {
        "VIREM E CONVERSEM": [
            "virem e conversem",
            "conversa inicial em duplas",
            "conversa em duplas",
            "conversar em duplas",
            "discussao em duplas",
            "troca em duplas",
            "discussao rapida em duplas",
            "conversar com o colega",
        ],
        "TODO MUNDO ESCREVE": [
            "todo mundo escreve",
            "registro individual no caderno",
            "registro individual",
            "registre individualmente",
            "escrevam no caderno",
            "escreva no caderno",
            "registro no caderno",
            "registrem no caderno",
        ],
        "COM SUAS PALAVRAS": [
            "com suas palavras",
            "sintese oral ou escrita",
            "sintese oral",
            "sintese escrita",
            "com suas proprias palavras",
            "linguagem propria",
            "reelaborarem",
            "expliquem oralmente ou por escrito",
        ],
        "DE OLHO NO MODELO": [
            "de olho no modelo",
            "exemplo comentado",
            "exemplo resolvido",
            "problema-modelo",
            "problema modelo",
            "modelo resolvido",
            "modelo de resolucao",
        ],
        "HORA DA LEITURA": [
            "hora da leitura",
            "leitura orientada",
            "leitura guiada",
            "leitura analitica",
        ],
        "UM PASSO DE CADA VEZ": [
            "um passo de cada vez",
            "explicacao em etapas",
            "etapas curtas",
            "etapas claras",
            "etapa por etapa",
            "passo a passo",
            "passo 1",
            "etapas do metodo",
        ],
        "PAUSE E RESPONDA": [
            "pause e responda",
            "pausa de checagem",
            "pausas de checagem",
            "checagem formativa",
            "pausa de verificacao",
            "verificacao da aprendizagem",
        ],
    }

    faltantes = []
    for tecnica in tecnicas_pdf:
        tecnica_norm = normalizar_texto(tecnica).upper()
        busca_termos = mapa_procura.get(tecnica_norm, [normalizar_texto(tecnica)])

        ja_presente = False
        for texto in textos_norm:
            if any(termo in texto for termo in busca_termos):
                ja_presente = True
                break
        if not ja_presente:
            faltantes.append(tecnica)

    if not faltantes:
        return metodologia

    for item in metodologia:
        if not isinstance(item, dict):
            metodologia_ajustada.append(item)
            continue

        novo_item = dict(item)
        titulo = normalizar_texto(novo_item.get("titulo", ""))
        texto = str(novo_item.get("texto", "")).strip()

        if faltantes and titulo in {"para comecar", "primeiro momento", "abertura", "relembre"}:
            tecnica = faltantes.pop(0)
            h = sum(ord(c) for c in (texto or ""))
            if tecnica == "VIREM E CONVERSEM":
                acrescimo = [
                    " Propor uma conversa rapida em duplas (VIREM E CONVERSEM) para que os estudantes compartilhem percepcoes, levantem hipoteses e retomem conhecimentos previos.",
                    " Conduzir uma breve troca de ideias em duplas (VIREM E CONVERSEM) para que os estudantes compartilhem suas hipoteses iniciais sobre o tema.",
                    " Orientar uma conversa rapida em duplas (VIREM E CONVERSEM) para discutir as primeiras impressoes e conectar com o conteudo da aula.",
                ][h % 3]
            elif tecnica == "TODO MUNDO ESCREVE":
                acrescimo = [
                    " Solicitar que todos os estudantes registrem individualmente no caderno (TODO MUNDO ESCREVE) para garantir o registro de hipoteses, ideias centrais ou respostas iniciais.",
                    " Orientar que todos os estudantes anotem suas impressoes e ideias iniciais no caderno (TODO MUNDO ESCREVE) de forma individual.",
                    " Propor que os estudantes facam um registro escrito individual no caderno (TODO MUNDO ESCREVE) antes de compartilhar as respostas.",
                ][h % 3]
            elif tecnica == "HORA DA LEITURA":
                acrescimo = [
                    " Conduzir uma leitura orientada do material (HORA DA LEITURA), realizando pausas para destacar informacoes importantes.",
                    " Mediar a leitura orientada do material (HORA DA LEITURA), pausando para destacar os conceitos e termos fundamentais.",
                    " Propor uma leitura compartilhada do material (HORA DA LEITURA), chamando atencao para os dados e informacoes principais.",
                ][h % 3]
            elif tecnica == "DE OLHO NO MODELO":
                acrescimo = [
                    " Apresentar um exemplo comentado na lousa (DE OLHO NO MODELO) para oferecer uma referencia clara de resolucao antes da pratica individual.",
                    " Demonstrar um problema-modelo resolvido no quadro (DE OLHO NO MODELO), servindo de guia antes que realizem as atividades.",
                    " Explicar um caso resolvido como referencia (DE OLHO NO MODELO) para direcionar as etapas do trabalho individual.",
                ][h % 3]
            elif tecnica == "PAUSE E RESPONDA":
                acrescimo = [
                    " Realizar uma parada estrategica para verificacao (PAUSE E RESPONDA) para checar a compreensao, retomar respostas da turma e esclarecer duvidas antes de avancar.",
                    " Propor uma pausa estrategica de verificacao (PAUSE E RESPONDA), fazendo uma pergunta rapida de checagem antes de prosseguir.",
                    " Conduzir uma pausa rapida para verificacao (PAUSE E RESPONDA) da compreensao, revisando as respostas iniciais antes de avancar.",
                ][h % 3]
            elif tecnica == "UM PASSO DE CADA VEZ":
                acrescimo = [
                    " Organizar a explicacao em etapas curtas e sequenciais (UM PASSO DE CADA VEZ) para orientar a compreensao de cada etapa antes de avancar.",
                    " Desenvolver a explicacao passo a passo em etapas curtas (UM PASSO DE CADA VEZ), verificando a compreensao de cada parte.",
                    " Conduzir a explanacao em etapas curtas e progressivas (UM PASSO DE CADA VEZ) para assegurar o entendimento de cada etapa.",
                ][h % 3]
            elif tecnica == "COM SUAS PALAVRAS":
                acrescimo = [
                    " Pedir que os estudantes expliquem com suas proprias palavras (COM SUAS PALAVRAS) para demonstrar o que compreenderam oralmente ou por escrito.",
                    " Solicitar que os estudantes expliquem com suas proprias palavras (COM SUAS PALAVRAS) a sintese do conceito apresentado.",
                    " Orientar os estudantes a explicarem o conceito com suas proprias palavras (COM SUAS PALAVRAS) para externar o entendimento.",
                ][h % 3]
            else:
                acrescimo = _acrescimo_generico_para_tecnica(tecnica, titulo)
            if normalizar_texto(acrescimo) not in normalizar_texto(texto):
                novo_item["texto"] = f"{texto}{acrescimo}".strip()

        metodologia_ajustada.append(novo_item)

    if faltantes:
        for item in metodologia_ajustada:
            if not isinstance(item, dict):
                continue
            titulo = normalizar_texto(item.get("titulo", ""))
            texto = str(item.get("texto", "")).strip()
            if titulo in {"na pratica", "foco no conteudo", "desenvolvimento", "encerramento", "segundo momento"}:
                tecnica = faltantes.pop(0)
                h = sum(ord(c) for c in (texto or ""))
                if tecnica == "TODO MUNDO ESCREVE":
                    acrescimo = [
                        " Solicitar que todos os estudantes registrem individualmente no caderno (TODO MUNDO ESCREVE) para que cada estudante organize por escrito a resolucao ou as ideias centrais da aula.",
                        " Orientar os estudantes a registrarem as resolucoes e conceitos fundamentais individualmente no caderno (TODO MUNDO ESCREVE).",
                        " Propor que cada estudante elabore seu registro escrito individual no caderno (TODO MUNDO ESCREVE) para fixacao dos aprendizados da aula.",
                    ][h % 3]
                elif tecnica == "COM SUAS PALAVRAS":
                    acrescimo = [
                        " Pedir que os estudantes expliquem com suas proprias palavras (COM SUAS PALAVRAS) para retomar os pontos principais trabalhados.",
                        " Solicitar que os estudantes expliquem o assunto com suas proprias palavras (COM SUAS PALAVRAS) no encerramento da aula.",
                        " Orientar a turma a sintetizar com suas proprias palavras (COM SUAS PALAVRAS) o que compreenderam dos pontos principais.",
                    ][h % 3]
                elif tecnica == "PAUSE E RESPONDA":
                    acrescimo = [
                        " Realizar uma parada estrategica para verificacao (PAUSE E RESPONDA) para conferir a compreensao da turma antes de avancar.",
                        " Propor uma pausa de checagem formativa (PAUSE E RESPONDA) para verificar a compreensao e sanar duvidas antes de avancar.",
                        " Realizar uma parada estrategica de verificacao (PAUSE E RESPONDA), assegurando que todos compreenderam a atividade antes de avancar.",
                    ][h % 3]
                else:
                    acrescimo = _acrescimo_generico_para_tecnica(tecnica, titulo)
                if normalizar_texto(acrescimo) not in normalizar_texto(texto):
                    item["texto"] = f"{texto}{acrescimo}".strip()
                if not faltantes:
                    break

    return metodologia_ajustada
