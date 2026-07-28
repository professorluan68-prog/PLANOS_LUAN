from core.lib.classificador import normalizar_texto, contem_termos
import re
from core.qualidade_metodologica import corrigir_mojibake, extrair_conceito_central, limitar_texto_natural


def _tecnica_em_aspas(tecnica: str) -> str:
    return f'“{str(tecnica or "").strip().upper()}”'


def _listar_topicos_curta(topicos: list[str]) -> str:
    itens = [str(item or "").strip() for item in topicos if str(item or "").strip()]
    if not itens:
        return ""
    if len(itens) == 1:
        return itens[0]
    if len(itens) == 2:
        return f"{itens[0]} e {itens[1]}"
    return f"{', '.join(itens[:-1])} e {itens[-1]}"


def _topico_foco_ciencias_valido(texto: str) -> str:
    candidato = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip(" .;:-"))
    base = normalizar_texto(candidato)
    if not candidato or len(candidato) < 4 or len(candidato) > 90:
        return ""
    if any(
        marcador in base
        for marcador in [
            "produzido pela",
            "disponivel em",
            "ensino fundamental",
            "anos finais",
            "aula ",
            "bimestre",
            "minutos",
            "para comecar",
            "foco no conteudo",
            "pause e responda",
            "na pratica",
            "encerramento",
            "referencias",
        ]
    ):
        return ""
    if re.match(r"^\d+\s*o?\s*pilar da teoria celular\b", base):
        return ""
    if re.search(r"https?://|\d+\s*minutos?", candidato, flags=re.I):
        return ""
    return candidato


def _topicos_complementares_foco_ciencias(texto_base: str, tema: str, conceito: str) -> list[str]:
    linhas = [linha.strip() for linha in corrigir_mojibake(str(texto_base or "")).splitlines() if linha.strip()]
    topicos: list[str] = []
    vistos: set[str] = set()
    conceito_norm = normalizar_texto(" ".join([tema, conceito]))

    def adicionar(candidato: str) -> None:
        topico = _topico_foco_ciencias_valido(candidato)
        if not topico:
            return
        topico_norm = normalizar_texto(topico)
        if topico_norm and (topico_norm in conceito_norm or conceito_norm in topico_norm):
            return
        for existente in list(topicos):
            existente_norm = normalizar_texto(existente)
            if topico_norm == existente_norm:
                return
            if topico_norm in existente_norm:
                return
            if existente_norm in topico_norm:
                topicos.remove(existente)
                vistos.discard(existente_norm)
        vistos.add(topico_norm)
        topicos.append(topico)

    for indice, linha in enumerate(linhas):
        linha_norm = normalizar_texto(linha)
        if linha_norm == "foco no conteudo":
            for proxima in linhas[indice + 1: indice + 4]:
                if normalizar_texto(proxima) != "foco no conteudo":
                    adicionar(proxima)
                    break
        if "seres unicelulares e pluricelulares" in linha_norm:
            adicionar("seres unicelulares e pluricelulares")
        elif "seres unicelulares e" in linha_norm and indice + 1 < len(linhas):
            proxima_norm = normalizar_texto(linhas[indice + 1])
            if "pluricelulares" in proxima_norm:
                adicionar("seres unicelulares e pluricelulares")
        elif "seres unicelulares" in linha_norm:
            adicionar("seres unicelulares")

    return topicos[:3]


def _atividade_ciencias_segura(atividade_extraida: str, tema: str) -> str:
    tema_base = _tema_base_ciencias(tema)
    fallback = f'atividades propostas no material, articuladas ao tema "{tema_base}"'
    atividade_limpa = corrigir_mojibake(str(atividade_extraida or "")).strip()
    atividade_limpa = re.sub(r"^\d+\s*minutos?\s*", "", atividade_limpa, flags=re.I)
    atividade_limpa = re.sub(
        r"^(?:atividade\s*\d+|correcao|hora da leitura|na pratica|situacao-problema)\s*[:\-]?\s*",
        "",
        atividade_limpa,
        flags=re.I,
    )
    atividade_limpa = re.sub(
        r"\b(?:responda a questao a seguir|responda a pergunta a seguir)\b[:\-]?\s*",
        "",
        atividade_limpa,
        flags=re.I,
    )
    atividade_limpa = re.sub(r"\s{2,}", " ", atividade_limpa).strip(" .:-")
    if _texto_extraido_ruidoso_ciencias(atividade_limpa):
        return fallback
    return limitar_texto_natural(atividade_limpa, limite=150).strip(" .:-")



def _texto_extraido_ruidoso_ciencias(texto: str) -> bool:
    texto_limpo = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip())
    base = normalizar_texto(texto_limpo)
    if not texto_limpo:
        return True
    if len(texto_limpo) > 180:
        return True
    if texto_limpo.count("?") >= 2:
        return True
    if any(
        marcador in base
        for marcador in [
            "referencias",
            "tempo",
            "expectativas de resposta",
            "dinamica de conducao",
            "correcao",
            "responda a questao",
            "responda a pergunta",
            "atividade 2",
            "atividade 3",
            "link para video",
            "aplicativo",
            "simulador",
            "desenho explicacao",
        ]
    ):
        return True
    if re.search(r"(?:^|[\s(])[123]\)", texto_limpo):
        return True
    if any(simbolo in texto_limpo for simbolo in ["●", "•"]):
        return True
    return False



def _conceito_ciencias_seguro(conceito: str, tema: str) -> str:
    tema_base = _tema_base_ciencias(tema)
    conceito_limpo = corrigir_mojibake(str(conceito or "")).strip(" .:-\"")
    conceito_norm = normalizar_texto(conceito_limpo)
    if conceito_norm in {"", "ciencias", "ciencia", "geral"}:
        return tema_base
    if conceito_norm == normalizar_texto(tema_base):
        return tema_base
    if _texto_extraido_ruidoso_ciencias(conceito_limpo):
        return tema_base
    return limitar_texto_natural(conceito_limpo, limite=110).strip(" .:-\"")




def _tema_base_ciencias(tema: str) -> str:
    tema_limpo = corrigir_mojibake(str(tema or "")).strip(" .:-\"")
    return extrair_conceito_central(tema_limpo) or tema_limpo or "o tema da aula"


def _metodologia_ciencias(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "") -> dict[str, str] | None:
    """Gerador especializado de frases para Ciencias EF."""
    base = normalizar_texto(" ".join([tema, texto_base, atividade_extraida]))
    tema_base = _tema_base_ciencias(tema)
    conceito_seguro = _conceito_ciencias_seguro(conceito, tema_base)
    atividade = _atividade_ciencias_segura(atividade_extraida, tema_base)
    eh_rpg_manejo = any(
        marcador in base
        for marcador in [
            "rpg",
            "plano de manejo",
            "papel do governo",
            "papel da comunidade",
            "papel dos pesquisadores",
            "unidade de conservacao",
            "grupos assumem",
        ]
    )

    contexto = "uma situacao concreta do cotidiano, imagem, noticia ou dado apresentado no material"
    recurso_visual = "a imagem, o esquema, o instrumento ou o modelo apresentado no material"
    fonte_dados = "graficos, tabelas, mapas, infograficos ou dados apresentados no material"
    if any(k in base for k in ["inpe", "ibge", "detran", "fapesp", "jornal da usp", "g1", "cnn", "onu", "anvisa", "fiocruz"]):
        contexto = "o dado ou a fonte real apresentada no material"
        fonte_dados = "a fonte real e os dados apresentados no material"
    elif (
        any(k in base for k in ["sao paulo", "cantareira", "aricanduva", "praca da se", "goiania", "brasil"])
        and any(k in base for k in ["municipio", "cidade", "estado", "bacia", "rio", "territorio", "clima", "tempo", "ambiente"])
    ):
        contexto = "o exemplo local ou brasileiro apresentado no material"
    if any(k in base for k in ["modelo tridimensional", "modelo celular", "maquete", "representacao tridimensional"]):
        recurso_visual = "o modelo cientifico ou a representacao construida no material"
    elif "mapa" in base:
        recurso_visual = "a imagem, o esquema, o mapa ou o modelo apresentado no material"
    if any(k in base for k in ["anemometro", "barometro", "pluviometro", "termometro", "umidade relativa", "estacao meteorologica"]):
        fonte_dados = "os instrumentos e as medidas apresentados no material"

    if tipo == "conceito_novo":
        disparador_inicial = "a pergunta inicial, a imagem ou o exemplo apresentado no material"
        tecnicas_abertura = []
        if "virem e conversem" in base:
            tecnicas_abertura.append(_tecnica_em_aspas("VIREM E CONVERSEM"))
        if any(k in base for k in ["analise a imagem", "observe a imagem", "imagem", "esquema", "microscopio"]):
            disparador_inicial = "a imagem inicial e os esquemas apresentados no material"
        prefixo_para_comecar = ""
        if tecnicas_abertura:
            prefixo_para_comecar = f"Aplicar o {tecnicas_abertura[0]}: "
        topicos_complementares = _topicos_complementares_foco_ciencias(texto_base, tema_base, conceito_seguro)
        if topicos_complementares:
            foco_campo = (
                f"Explicar {conceito_seguro}, com destaque para {_listar_topicos_curta(topicos_complementares).lower()}, "
                "destacando definicoes, principios basicos, vocabulario cientifico e exemplos observados no material."
            )
        else:
            foco_campo = (
                f"Explicar {conceito_seguro}, destacando definicoes, principios basicos, vocabulario cientifico e exemplos "
                "observados no material para que a turma compreenda como o conceito aparece nos seres vivos, estruturas ou processos estudados."
            )
        prefixo_pratica = "Atividade 1: "
        if "todo mundo escreve" in base:
            prefixo_pratica += f'Aplicando {_tecnica_em_aspas("TODO MUNDO ESCREVE")}, '
        return {
            "para_comecar": (
                f"{prefixo_para_comecar}apresentar {disparador_inicial} para mobilizar conhecimentos previos e levantar hipoteses sobre {tema}, "
                "sem antecipar a resposta antes da observacao e da conversa inicial da turma."
            ),
            "foco": foco_campo,
            "pause": (
                "Realizar uma pausa de verificacao com pergunta objetiva ou associacao entre conceito e exemplo, corrigindo "
                "coletivamente duvidas antes da atividade principal."
            ),
            "pratica": (
                f"{prefixo_pratica}orientar a comparacao, classificacao ou registro solicitado no material, pedindo que os estudantes utilizem "
                f"imagens, esquemas e evidencias observadas para explicar {tema} com clareza, a partir da proposta do material: {atividade}."
            ),
            "encerramento": (
                f"Encerrar retomando as ideias construidas ao longo da aula e solicitar uma sintese curta sobre o que permite "
                f"reconhecer, explicar ou diferenciar em {tema}."
            ),
        }

    if tipo == "analise_dados":
        return {
            "para_comecar": (
                f"Contextualizar {tema} com {contexto}, mobilizando conhecimentos previos e levantando hipoteses sobre o que os dados podem revelar."
            ),
            "analise_dados": (
                f"Orientar a leitura de {fonte_dados}, destacando titulo, fonte, legenda, unidades, comparacoes e tendencias antes da formulacao das conclusoes."
            ),
            "foco": (
                f"Sistematizar {conceito_seguro}, relacionando os dados observados a explicacoes cientificas, relacoes de causa e consequencia e vocabulario proprio da area."
            ),
            "pratica": (
                f"Organizar a analise em duplas ou grupos, solicitando que a turma utilize os dados do material para justificar respostas e explicar o fenomeno estudado. Atividade central: {atividade}."
            ),
            "correcao_dialogada": (
                "Comparar as interpretacoes produzidas pela turma, corrigindo leituras apressadas dos dados e reforcando como as evidencias sustentam as conclusoes."
            ),
            "encerramento": (
                f"Encerrar retomando o que os dados ajudaram a compreender sobre {tema}, com sintese curta em linguagem cientifica."
            ),
        }

    if tipo == "modelagem_cientifica":
        return {
            "relembre": (
                f"Retomar com a turma o que ja foi estudado sobre {tema}, destacando os componentes e as relacoes que precisarao aparecer na representacao."
            ),
            "observacao_inicial": (
                f"Orientar a observacao de {recurso_visual}, identificando partes, funcoes e limites da representacao antes da construcao ou comparacao do modelo."
            ),
            "mao_na_massa": (
                "Conduzir a construcao ou montagem do modelo passo a passo, utilizando apenas os materiais e orientacoes presentes no material e acompanhando o registro das escolhas do grupo."
            ),
            "socializacao": (
                "Promover a apresentacao dos modelos, comparando semelhancas, diferencas, componentes identificados e a forma como cada grupo representou o processo ou a estrutura estudada."
            ),
            "correcao_dialogada": (
                f"Retomar coletivamente os componentes de {conceito_seguro}, ajustando imprecisoes e reforcando que o modelo simplifica a realidade para favorecer a compreensao."
            ),
            "encerramento": (
                f"Encerrar pedindo que os estudantes expliquem o que o modelo ajudou a compreender sobre {tema} e quais limites essa representacao apresenta."
            ),
        }

    if tipo == "situacao_problema":
        situacao_problema_txt = (
            f"Apresentar o cenario do material e orientar os grupos a identificar problema central, causas, consequencias, agentes envolvidos e criterios para propor solucoes."
        )
        pratica_txt = (
            f"Organizar o trabalho em equipes para elaborar respostas, plano de acao ou proposta de intervencao, exigindo justificativas apoiadas em conceitos e evidencias do material. Atividade central: {atividade}."
        )
        socializacao_txt = (
            "Mediar a apresentacao das propostas, estimulando perguntas entre os grupos e comparacao entre solucoes, responsabilidades e impactos considerados."
        )
        correcao_txt = (
            "Integrar as contribuicoes da turma, corrigindo simplificacoes, reforcando a complexidade do problema e validando as propostas com base nos conceitos cientificos."
        )
        encerramento_txt = (
            f"Finalizar retomando por que a analise de {tema} exige acao coletiva, argumentacao baseada em evidencias e articulacao entre diferentes agentes."
        )

        if eh_rpg_manejo:
            situacao_problema_txt = (
                "Apresentar a situacao-problema do RPG e explicitar que os grupos assumirao papeis diferentes, como governo, comunidade local e pesquisadores, para analisar interesses, responsabilidades e limites de cada agente."
            )
            pratica_txt = (
                f"Organizar os grupos por papel e orientar a construcao coletiva do plano de manejo, solicitando que cada equipe analise impactos, prioridades, evidencias do material e medidas viaveis antes de negociar a proposta final. Atividade central: {atividade}."
            )
            socializacao_txt = (
                "Mediar a apresentacao e a negociacao entre os grupos, comparando argumentos, conflitos de interesse, medidas de protecao e responsabilidades assumidas por cada papel."
            )
            correcao_txt = (
                "Retomar com a turma quais propostas ficaram mais coerentes com as evidencias cientificas, com os impactos observados e com a necessidade de preservar a unidade de conservacao."
            )
            encerramento_txt = (
                "Encerrar sintetizando os pontos principais do RPG, retomando as propostas para o plano de manejo e verificando quais argumentos foram mais fundamentados em evidencias cientificas."
            )

        return {
            "relembre": (
                f"Retomar os conceitos necessarios para analisar {tema}, recuperando o que a turma ja sabe sobre causas, impactos e agentes envolvidos."
            ),
            "situacao_problema": situacao_problema_txt,
            "pratica": pratica_txt,
            "socializacao": socializacao_txt,
            "correcao_dialogada": correcao_txt,
            "encerramento": encerramento_txt,
        }

    if tipo == "pratica_experimental":
        return {
            "relembre": (
                f"Retomar o conceito central de {tema} e o que a turma precisa observar para compreender o fenomeno durante a pratica."
            ),
            "para_comecar": (
                "Apresentar a questao investigativa, os materiais e os cuidados necessarios, esclarecendo o procedimento antes do inicio da atividade."
            ),
            "mao_na_massa": (
                "Conduzir o procedimento passo a passo, utilizando apenas os materiais e etapas indicados no material e acompanhando o registro das observacoes feitas pelos estudantes."
            ),
            "pratica": (
                f"Orientar a comparacao dos resultados observados, solicitando que a turma relacione o que ocorreu ao conceito cientifico estudado. Atividade central: {atividade}."
            ),
            "correcao_dialogada": (
                "Retomar as observacoes registradas pela turma, corrigindo interpretacoes precipitadas e reforcando como as evidencias ajudam a explicar o fenomeno."
            ),
            "encerramento": (
                f"Encerrar com sintese breve sobre o que a pratica permitiu compreender a respeito de {tema}, sem antecipar resultados nao observados no material."
            ),
        }

    if tipo == "investigativa":
        return {
            "para_comecar": (
                f"Lancar a questao investigativa relacionada a {tema}, pedindo que os estudantes formulem hipoteses iniciais antes da explicacao formal."
            ),
            "observacao_inicial": (
                f"Orientar a observacao de {recurso_visual}, destacando o que precisa ser registrado como evidencia durante a investigacao."
            ),
            "pratica": (
                f"Conduzir o registro das evidencias e a comparacao entre hipoteses, incentivando a turma a justificar respostas com base no que observou. Atividade central: {atividade}."
            ),
            "foco": (
                f"Sistematizar {conceito_seguro} a partir das evidencias levantadas, articulando observacao, explicacao cientifica e vocabulario proprio da aula."
            ),
            "encerramento": (
                f"Retomar a pergunta inicial e solicitar que os estudantes expliquem como as evidencias analisadas ajudaram a compreender {tema}."
            ),
        }

    if tipo == "impacto_socioambiental":
        return {
            "para_comecar": (
                f"Apresentar {contexto} sobre {tema}, mobilizando conhecimentos previos e perguntas sobre impactos, responsabilidades e possiveis formas de enfrentamento."
            ),
            "foco": (
                f"Explicar {conceito_seguro}, relacionando a aula a causas e consequencias, uso de recursos, saude, ambiente e responsabilidade coletiva."
            ),
            "analise_dados": (
                f"Orientar a leitura de {fonte_dados}, relacionando os dados, as evidencias e os exemplos do material aos impactos discutidos."
            ),
            "pratica": (
                f"Organizar a turma para analisar medidas possiveis, responsabilidades dos agentes envolvidos e propostas de acao, exigindo justificativas baseadas nos conceitos estudados. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar com sintese sobre como {tema} envolve ciencia, ambiente, sociedade e tomada de decisao responsavel, retomando as perguntas iniciais da aula."
            ),
        }

    if tipo == "revisao_retomada":
        return {
            "relembre": (
                f"Retomar com a turma os conceitos ja estudados sobre {tema}, usando uma pergunta curta em duplas para identificar o que ficou consolidado e o que precisa ser aprofundado."
            ),
            "foco": (
                f"Reorganizar {conceito_seguro} de forma progressiva, estabelecendo conexoes entre os conteudos anteriores, exemplos do material e novas aplicacoes cientificas."
            ),
            "modelo": (
                "Apresentar o exercicio resolvido ou exemplo comentado passo a passo, destacando o raciocinio cientifico usado para interpretar dados, esquemas ou situacoes-problema."
            ),
            "pause": (
                "Propor uma verificacao formativa rapida, com questao objetiva, verdadeiro ou falso ou pergunta curta, e corrigir coletivamente antes de seguir para a atividade."
            ),
            "pratica": (
                f"Orientar a atividade de retomada com registro escrito, solicitando que os estudantes justifiquem as respostas com base nos conceitos revisados. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar com sintese em linguagem propria, pedindo que os estudantes expliquem a relacao entre {tema} e os conceitos retomados na aula."
            ),
        }

    if tipo == "leitura_analise":
        return {
            "para_comecar": (
                f"Apresentar {contexto} sobre {tema} e propor que os estudantes levantem hipoteses em duplas, relacionando o assunto ao cotidiano e a questoes de ciencia, sociedade, saude ou ambiente."
            ),
            "leitura": (
                f"Realizar leitura compartilhada do texto, noticia, dado ou fonte sobre {tema}, identificando informacoes centrais, vocabulario cientifico e evidencias usadas para sustentar as ideias."
            ),
            "foco": (
                f"Explicar {conceito_seguro} articulando o texto lido aos conceitos cientificos, destacando relacoes de causa, consequencia, comparacao e impacto social ou ambiental."
            ),
            "pause": (
                "Fazer uma pausa de verificacao com pergunta objetiva ou verdadeiro/falso, solicitando que os estudantes justifiquem a resposta antes da correcao coletiva."
            ),
            "pratica": (
                f"Propor atividade escrita de interpretacao e analise critica, orientando a retomada do texto para localizar evidencias e construir respostas fundamentadas. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Retomar as hipoteses iniciais e solicitar uma sintese curta sobre o que o texto ajudou a compreender a respeito de {tema}."
            ),
        }

    if tipo == "estudo_caso":
        return {
            "para_comecar": (
                f"Apresentar o caso ou situacao-problema relacionado a {tema}, pedindo que os estudantes identifiquem o problema central e levantem explicacoes iniciais."
            ),
            "foco": (
                f"Sistematizar os conceitos necessarios para analisar o caso, explicando {conceito_seguro} com apoio de esquemas, dados ou exemplos do material."
            ),
            "estudo_caso": (
                "Conduzir a analise do caso em etapas: identificar os elementos envolvidos, explicar as relacoes cientificas e discutir consequencias para a saude, o ambiente ou a sociedade."
            ),
            "pause": (
                "Realizar checagem formativa antes da resposta final, verificando se a turma compreendeu quais evidencias sustentam a explicacao do caso."
            ),
            "pratica": (
                f"Orientar o registro escrito da solucao ou explicacao do caso, solicitando justificativa cientifica e retomada dos conceitos estudados. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Fechar a aula socializando algumas respostas e destacando como o raciocinio cientifico ajudou a interpretar {tema}."
            ),
        }

    if tipo == "producao_projeto":
        return {
            "relembre": (
                f"Retomar com a turma o percurso ja realizado sobre {tema}, recuperando os conceitos e criterios que deverao aparecer na producao ou apresentacao."
            ),
            "foco": (
                f"Explicar os criterios de qualidade da producao cientifica, destacando clareza das informacoes, uso correto de {conceito_seguro}, organizacao visual e relacao com a vida cotidiana."
            ),
            "producao": (
                f"Organizar os estudantes em grupos ou individualmente para finalizar, revisar ou apresentar a producao proposta no material. Atividade central: {atividade}."
            ),
            "compartilhamento": (
                "Promover socializacao das producoes, garantindo escuta da turma, perguntas breves e retomada dos criterios combinados."
            ),
            "encerramento": (
                f"Conduzir reflexao final sobre o que foi aprendido durante a producao e como esse conhecimento se relaciona a ciencia, sociedade, saude ou ambiente."
            ),
        }

    return {
        "para_comecar": (
            f"Apresentar {contexto} relacionado a {tema}, mobilizando conhecimentos previos, perguntas iniciais e relacoes com situacoes observaveis no cotidiano."
        ),
        "foco": (
            f"Explicar {conceito_seguro}, retomando exemplos, imagens, esquemas ou comparacoes presentes no material para que a turma compreenda estrutura, processo ou funcionamento com vocabulario cientifico adequado."
        ),
        "pause": (
            "Realizar uma pausa de checagem com pergunta objetiva, associacao entre conceito e exemplo ou explicacao curta, corrigindo duvidas antes da atividade principal."
        ),
        "pratica": (
            f"Orientar as atividades do material, pedindo que os estudantes utilizem evidencias, esquemas, dados ou observacoes da aula para explicar {tema} com clareza. Atividade central: {atividade}."
        ),
        "encerramento": (
            f"Encerrar retomando o que foi compreendido sobre {tema}, solicitando uma sintese curta que relacione conceito, exemplo observado e aplicacao no cotidiano."
        ),
    }

