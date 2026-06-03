from core.eja.adaptador_eja import adaptar_metodologia_eja
from core.lib.classificador import normalizar_texto

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

    faltantes = [tecnica for tecnica in tecnicas_pdf if not any(normalizar_texto(tecnica) in texto for texto in textos_norm)]
    if not faltantes:
        return metodologia

    for indice, item in enumerate(metodologia):
        if not isinstance(item, dict):
            metodologia_ajustada.append(item)
            continue

        novo_item = dict(item)
        titulo = normalizar_texto(novo_item.get("titulo", ""))
        texto = str(novo_item.get("texto", "")).strip()

        if faltantes and titulo in {"para comecar", "primeiro momento", "abertura", "relembre"}:
            tecnica = faltantes.pop(0)
            if tecnica == "VIREM E CONVERSEM":
                acrescimo = " Aplicar a tecnica VIREM E CONVERSEM para que os estudantes compartilhem percepcoes, levantem hipoteses e retomem conhecimentos previos."
            elif tecnica == "TODO MUNDO ESCREVE":
                acrescimo = " Utilizar a tecnica TODO MUNDO ESCREVE para garantir o registro individual de hipoteses, ideias centrais ou respostas iniciais."
            elif tecnica == "HORA DA LEITURA":
                acrescimo = " Utilizar a tecnica HORA DA LEITURA para conduzir a leitura orientada do material, com pausas para destacar informacoes importantes."
            elif tecnica == "DE OLHO NO MODELO":
                acrescimo = " Aplicar a tecnica DE OLHO NO MODELO, apresentando um exemplo comentado antes da atividade individual."
            elif tecnica == "PAUSE E RESPONDA":
                acrescimo = " Realizar o momento PAUSE E RESPONDA para checar a compreensao, retomar respostas da turma e esclarecer duvidas antes de avancar."
            elif tecnica == "UM PASSO DE CADA VEZ":
                acrescimo = " Utilizar a tecnica UM PASSO DE CADA VEZ para organizar a explicacao em etapas curtas antes de avancar."
            elif tecnica == "COM SUAS PALAVRAS":
                acrescimo = " Aplicar a tecnica COM SUAS PALAVRAS para que os estudantes expliquem oralmente ou por escrito o que compreenderam."
            else:
                acrescimo = f" Incorporar a tecnica {tecnica} ao desenvolvimento da aula, articulando-a aos exemplos, registros e intervencoes do professor."
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
                if tecnica == "TODO MUNDO ESCREVE":
                    acrescimo = " Utilizar a tecnica TODO MUNDO ESCREVE para que cada estudante organize por escrito a resolucao ou as ideias centrais da aula."
                elif tecnica == "COM SUAS PALAVRAS":
                    acrescimo = " Aplicar a tecnica COM SUAS PALAVRAS para que os estudantes retomem os pontos principais trabalhados."
                elif tecnica == "PAUSE E RESPONDA":
                    acrescimo = " Realizar o momento PAUSE E RESPONDA para conferir a compreensao da turma antes de avancar."
                else:
                    acrescimo = f" Incorporar a tecnica {tecnica} ao desenvolvimento da aula, articulando-a aos exemplos, registros e intervencoes do professor."
                if normalizar_texto(acrescimo) not in normalizar_texto(texto):
                    item["texto"] = f"{texto}{acrescimo}".strip()
                if not faltantes:
                    break

    return metodologia_ajustada
