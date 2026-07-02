import re

from core.eja.adaptador_eja import adaptar_metodologia_eja
from core.lib.classificador import normalizar_texto


_TECNICAS_PADRONIZADAS = [
    "VIREM E CONVERSEM",
    "TODO MUNDO ESCREVE",
    "COM SUAS PALAVRAS",
    "HORA DA LEITURA",
    "DE OLHO NO MODELO",
    "PAUSE E RESPONDA",
    "UM PASSO DE CADA VEZ",
    "LISTEN AND REPEAT",
    "WRITE AND SHARE",
    "SAY IT IN ENGLISH",
]


def _padronizar_citacoes_tecnicas(texto: str) -> str:
    texto_final = str(texto or "")
    for tecnica in _TECNICAS_PADRONIZADAS:
        texto_final = re.sub(
            rf"\(\s*{re.escape(tecnica)}\s*\)",
            f"“{tecnica}”",
            texto_final,
            flags=re.I,
        )
        texto_final = re.sub(
            rf"(?<![\"“])\b{re.escape(tecnica)}\b(?![\"”])",
            f"“{tecnica}”",
            texto_final,
            flags=re.I,
        )
    return texto_final


def _acrescimo_generico_para_tecnica(tecnica: str, titulo: str) -> str:
    tecnica_norm = normalizar_texto(tecnica).upper()
    titulo_norm = normalizar_texto(titulo)

    if tecnica_norm == "VIREM E CONVERSEM":
        return " Promover uma troca breve de ideias em duplas, com foco nas hipóteses e nas primeiras percepções sobre o tema."
    if tecnica_norm == "TODO MUNDO ESCREVE":
        return " Solicitar registro individual no caderno para organizar hipóteses, conceitos centrais ou respostas iniciais."
    if tecnica_norm == "COM SUAS PALAVRAS":
        return " Pedir que os estudantes expliquem, oralmente ou por escrito, o que compreenderam com suas próprias palavras."
    if tecnica_norm == "DE OLHO NO MODELO":
        return " Apresentar um exemplo comentado como referência antes da atividade principal."
    if tecnica_norm == "HORA DA LEITURA":
        return " Conduzir leitura orientada do material, com pausas para destacar informações importantes."
    if tecnica_norm == "UM PASSO DE CADA VEZ":
        return " Organizar a explicação em etapas curtas, verificando a compreensão ao longo do percurso."
    if tecnica_norm == "PAUSE E RESPONDA":
        return " Realizar uma pausa de checagem para verificar a compreensão e retomar respostas da turma antes de avançar."

    if titulo_norm in {"encerramento", "segundo momento"}:
        return " Retomar os principais pontos da aula com uma breve verificação de compreensão antes do fechamento."
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
        return [
            {**item, "texto": _padronizar_citacoes_tecnicas(str(item.get("texto", "")).strip())}
            if isinstance(item, dict)
            else _padronizar_citacoes_tecnicas(str(item))
            for item in metodologia
        ]

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
                    " Propor uma conversa rápida em duplas (VIREM E CONVERSEM) para que os estudantes compartilhem percepções, levantem hipóteses e retomem conhecimentos prévios.",
                    " Conduzir uma breve troca de ideias em duplas (VIREM E CONVERSEM) para que os estudantes compartilhem suas hipóteses iniciais sobre o tema.",
                    " Orientar uma conversa rápida em duplas (VIREM E CONVERSEM) para discutir as primeiras impressões e conectar com o conteúdo da aula.",
                ][h % 3]
            elif tecnica == "TODO MUNDO ESCREVE":
                acrescimo = [
                    " Solicitar que todos os estudantes registrem individualmente no caderno (TODO MUNDO ESCREVE) para garantir o registro de hipóteses, ideias centrais ou respostas iniciais.",
                    " Orientar que todos os estudantes anotem suas impressões e ideias iniciais no caderno (TODO MUNDO ESCREVE) de forma individual.",
                    " Propor que os estudantes façam um registro escrito individual no caderno (TODO MUNDO ESCREVE) antes de compartilhar as respostas.",
                ][h % 3]
            elif tecnica == "HORA DA LEITURA":
                acrescimo = [
                    " Conduzir uma leitura orientada do material (HORA DA LEITURA), realizando pausas para destacar informações importantes.",
                    " Mediar a leitura orientada do material (HORA DA LEITURA), pausando para destacar os conceitos e termos fundamentais.",
                    " Propor uma leitura compartilhada do material (HORA DA LEITURA), chamando atenção para os dados e informações principais.",
                ][h % 3]
            elif tecnica == "DE OLHO NO MODELO":
                acrescimo = [
                    " Apresentar um exemplo comentado na lousa (DE OLHO NO MODELO) para oferecer uma referencia clara de resolucao antes da pratica individual.",
                    " Demonstrar um problema-modelo resolvido no quadro (DE OLHO NO MODELO), servindo de guia antes que realizem as atividades.",
                    " Explicar um caso resolvido como referencia (DE OLHO NO MODELO) para direcionar as etapas do trabalho individual.",
                ][h % 3]
            elif tecnica == "PAUSE E RESPONDA":
                acrescimo = [
                    " Realizar uma parada estratégica para verificação (PAUSE E RESPONDA) para checar a compreensão, retomar respostas da turma e esclarecer dúvidas antes de avançar.",
                    " Propor uma pausa estratégica de verificação (PAUSE E RESPONDA), fazendo uma pergunta rápida de checagem antes de prosseguir.",
                    " Conduzir uma pausa rápida para verificação (PAUSE E RESPONDA) da compreensão, revisando as respostas iniciais antes de avançar.",
                ][h % 3]
            elif tecnica == "UM PASSO DE CADA VEZ":
                acrescimo = [
                    " Organizar a explicação em etapas curtas e sequenciais (UM PASSO DE CADA VEZ) para orientar a compreensão de cada etapa antes de avançar.",
                    " Desenvolver a explicação passo a passo em etapas curtas (UM PASSO DE CADA VEZ), verificando a compreensão de cada parte.",
                    " Conduzir a explicação em etapas curtas e progressivas (UM PASSO DE CADA VEZ) para assegurar o entendimento de cada etapa.",
                ][h % 3]
            elif tecnica == "COM SUAS PALAVRAS":
                acrescimo = [
                    " Pedir que os estudantes expliquem com suas próprias palavras (COM SUAS PALAVRAS) para demonstrar o que compreenderam oralmente ou por escrito.",
                    " Solicitar que os estudantes expliquem com suas próprias palavras (COM SUAS PALAVRAS) a síntese do conceito apresentado.",
                    " Orientar os estudantes a explicarem o conceito com suas próprias palavras (COM SUAS PALAVRAS) para externar o entendimento.",
                ][h % 3]
            else:
                acrescimo = _acrescimo_generico_para_tecnica(tecnica, titulo)
            if normalizar_texto(acrescimo) not in normalizar_texto(texto):
                novo_item["texto"] = f"{texto}{acrescimo}".strip()

        if isinstance(novo_item, dict):
            novo_item["texto"] = _padronizar_citacoes_tecnicas(str(novo_item.get("texto", "")).strip())
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
                        " Propor que cada estudante elabore seu registro escrito individual no caderno (TODO MUNDO ESCREVE) para fixação dos aprendizados da aula.",
                    ][h % 3]
                elif tecnica == "COM SUAS PALAVRAS":
                    acrescimo = [
                        " Pedir que os estudantes expliquem com suas próprias palavras (COM SUAS PALAVRAS) para retomar os pontos principais trabalhados.",
                        " Solicitar que os estudantes expliquem o assunto com suas próprias palavras (COM SUAS PALAVRAS) no encerramento da aula.",
                        " Orientar a turma a sintetizar com suas próprias palavras (COM SUAS PALAVRAS) o que compreenderam dos pontos principais.",
                    ][h % 3]
                elif tecnica == "PAUSE E RESPONDA":
                    acrescimo = [
                        " Realizar uma parada estratégica para verificação (PAUSE E RESPONDA) para conferir a compreensão da turma antes de avançar.",
                        " Propor uma pausa de checagem formativa (PAUSE E RESPONDA) para verificar a compreensão e sanar dúvidas antes de avançar.",
                        " Realizar uma parada estratégica de verificação (PAUSE E RESPONDA), assegurando que todos compreenderam a atividade antes de avançar.",
                    ][h % 3]
                else:
                    acrescimo = _acrescimo_generico_para_tecnica(tecnica, titulo)
                if normalizar_texto(acrescimo) not in normalizar_texto(texto):
                    item["texto"] = f"{texto}{acrescimo}".strip()
                item["texto"] = _padronizar_citacoes_tecnicas(str(item.get("texto", "")).strip())
                if not faltantes:
                    break

    resultado = []
    for item in metodologia_ajustada:
        if isinstance(item, dict):
            novo_item = dict(item)
            novo_item["texto"] = _padronizar_citacoes_tecnicas(str(novo_item.get("texto", "")).strip())
            resultado.append(novo_item)
        else:
            resultado.append(_padronizar_citacoes_tecnicas(str(item)))
    return resultado
