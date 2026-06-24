from core.lib.classificador import normalizar_texto


# Repertórios controlados de variação pedagógica
REPERTORIO_RETOMADA = {
    "LEITURA INVESTIGATIVA": "recuperar a pergunta ou problema central da aula anterior para orientar nossa analise de hoje",
    "COMPARAÇÃO E DIÁLOGO": "reler a sintese anterior e revisar palavras-chave coletivamente para situar a turma",
    "ANÁLISE MODELADA": "comparar duas respostas ou registros anteriores dos estudantes para tirar duvidas e mapear progressos",
    "ESCRITA E AUTORIA": "retomar brevemente um trecho estudado ou reconstruir uma ideia em esquema no quadro"
}

REPERTORIO_LEITURA = {
    "LEITURA INVESTIGATIVA": "leitura silenciosa com marcacao individual de termos-chave e evidencias textuais",
    "COMPARAÇÃO E DIÁLOGO": "leitura comparativa e atenta entre dois trechos, imagens ou elementos linguisticos do material",
    "ANÁLISE MODELADA": "leitura em partes com pausas para perguntas de compreensao orientadas pelo professor",
    "ESCRITA E AUTORIA": "leitura expressiva e compartilhada do texto de referencia, observando as escolhas do autor"
}

REPERTORIO_REGISTRO = {
    "LEITURA INVESTIGATIVA": "registro de anotacao de evidencias e elaboracao de resposta fundamentada no caderno",
    "COMPARAÇÃO E DIÁLOGO": "construcao de um quadro comparativo ou esquema destacando semelhancas e diferencas encontradas",
    "ANÁLISE MODELADA": "sintese em duas frases ou resumo estruturado das ideias principais do texto",
    "ESCRITA E AUTORIA": "elaboracao de um pequeno comentario interpretativo ou planejamento do rascunho de escrita"
}

REPERTORIO_ENCERRAMENTO = {
    "LEITURA INVESTIGATIVA": "anotacao de uma evidencia textual conclusiva no caderno",
    "COMPARAÇÃO E DIÁLOGO": "revisao colaborativa em dupla e explicacao do aprendizado com as proprias palavras",
    "ANÁLISE MODELADA": "registro de uma pergunta de continuidade para orientar o proximo estudo",
    "ESCRITA E AUTORIA": "preenchimento de um bilhete de saida com resposta sintetica a questao central da aula"
}

def _metodologia_lingua_portuguesa(
    texto_base: str,
    tema: str,
    tipo: str,
    perfil_metodologico: str = None,
    tipo_aula: str = "simples"
) -> dict[str, str] | None:
    """Gerador especializado de frases para o perfil Lingua Portuguesa com variacao controlada."""
    # Obter perfil de variacao pedagogica
    if not perfil_metodologico:
        perfil_metodologico = "LEITURA INVESTIGATIVA"

    retomada = REPERTORIO_RETOMADA.get(perfil_metodologico, REPERTORIO_RETOMADA["LEITURA INVESTIGATIVA"])
    leitura = REPERTORIO_LEITURA.get(perfil_metodologico, REPERTORIO_LEITURA["LEITURA INVESTIGATIVA"])
    registro = REPERTORIO_REGISTRO.get(perfil_metodologico, REPERTORIO_REGISTRO["LEITURA INVESTIGATIVA"])
    encerramento = REPERTORIO_ENCERRAMENTO.get(perfil_metodologico, REPERTORIO_ENCERRAMENTO["LEITURA INVESTIGATIVA"])

    # Se for aula dupla, retornamos a estrutura de 6 etapas
    if tipo_aula == "dupla":
        if tipo == "autoavaliacao":
            return {
                "para_comecar": f"Retomar o percurso de estudo de {tema} e {retomada} para ativar os conhecimentos.",
                "hora_leitura": f"Conduzir {leitura} dos criterios de autoavaliacao estabelecidos no material.",
                "foco": f"Apresentar a definicao e o proposito de cada criterio de avaliacao sobre {tema}.",
                "pratica": f"Orientar o preenchimento da autoavaliacao ou rubrica de forma individual com {registro}.",
                "socializacao": "Promover devolutiva e socializacao breve das percepcoes da turma, trocando estrategias de estudo.",
                "encerramento": f"Encerrar sistematizando metas coletivas e realizando {encerramento}."
            }
        if tipo == "literatura":
            return {
                "para_comecar": f"Apresentar imagens, contexto historico ou perguntas sobre {tema} e {retomada} para aquecimento.",
                "hora_leitura": f"Conduzir {leitura} de trechos literarios selecionados para analise critica.",
                "foco": f"Apresentar a estetica, autores e marcas literarias de {tema} integradas ao contexto social.",
                "pratica": f"Orientar exercicio aplicado de analise de recursos expressivos com {registro}.",
                "socializacao": "Promover socializacao em duplas comparando percepcoes e efeitos de sentido identificados.",
                "encerramento": f"Finalizar consolidando a sintese dos aprendizados esteticos com {encerramento}."
            }
        if tipo == "genero_textual":
            return {
                "para_comecar": f"Iniciar conectando o genero de {tema} ao cotidiano e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de um texto modelo do genero para identificar sua estrutura.",
                "foco": f"Apresentar a definicao, marcas linguisticas, publico-alvo e circulacao social do genero de {tema}.",
                "pratica": f"Propor exercicios praticos de interpretacao e analise linguistica com {registro}.",
                "socializacao": "Organizar socializacao das respostas em pequenos grupos para discussao das marcas do genero.",
                "encerramento": f"Finalizar sistematizando a funcao social do genero com {encerramento}."
            }
        if tipo == "producao_textual":
            return {
                "para_comecar": f"Apresentar a proposta de escrita sobre {tema} e realizar {retomada} dos objetivos.",
                "hora_leitura": f"Conduzir {leitura} das referencias de escrita e instrucoes de producao.",
                "foco": f"Apresentar os criterios de qualidade e roteiro de planejamento estrutural do texto de {tema}.",
                "pratica": f"Orientar as etapas de planejamento e escrita do rascunho autoral com {registro}.",
                "socializacao": "Organizar revisao colaborativa entre pares para troca de sugestoes de aprimoramento.",
                "encerramento": f"Finalizar estimulando a reflexao sobre o processo de reescrita e aplicar {encerramento}."
            }
        if tipo == "pratica_oral":
            return {
                "para_comecar": f"Retomar a finalidade da pratica oral de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de roteiros, exemplos de apresentacao ou guias de escuta ativa.",
                "foco": f"Sistematizar os recursos de linguagem oral de {tema}, como entonacao, postura e clareza.",
                "pratica": f"Orientar a preparacao e o ensaio ou apresentacao dos estudantes com {registro}.",
                "socializacao": "Promover apresentacao e socializacao das producoes orais com devolutiva respeitosa da turma.",
                "encerramento": f"Encerrar avaliando como a oralidade colaborou para expressar o tema e aplicar {encerramento}."
            }
        if tipo == "gramatica_integrada":
            return {
                "para_comecar": f"Apresentar pergunta motivadora ou trecho curto sobre o fenomeno de {tema} e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} do texto-base localizando o fenomeno gramatical em foco.",
                "foco": f"Sistematizar o conteudo gramatical de {tema} conectando a regra aos efeitos de sentido.",
                "pratica": f"Propor exercicios aplicados de identificacao e escrita com {registro}.",
                "socializacao": "Realizar correcao dialogada e compartilhamento de duvidas comuns sobre {tema}.",
                "encerramento": f"Finalizar sintetizando a importancia da convencao estudada e realizar {encerramento}."
            }
        if tipo == "leitura_multimodal":
            return {
                "para_comecar": f"Iniciar analisando cartaz, imagem ou infografico sobre {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} do texto multimodal articulando os diferentes modos de linguagem.",
                "foco": f"Sistematizar como recursos verbais e visuais constroem sentido no material sobre {tema}.",
                "pratica": f"Propor atividade aplicada de analise de elementos visuais com {registro}.",
                "socializacao": "Promover correcao dialogada comparando as diferentes leituras e hipoteses da turma.",
                "encerramento": f"Finalizar destacando a leitura critica do texto multimodal e aplicar {encerramento}."
            }
        if tipo == "resumo_retextualizacao":
            return {
                "para_comecar": f"Apresentar esquema, cartaz ou infografico de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} do texto-base destacando topicos, palavras-chave e dados centrais.",
                "foco": f"Explicar como transformar informacoes do material em texto coerente e autoral sobre {tema}.",
                "pratica": f"Orientar a producao de resumo ou retextualizacao no caderno com {registro}.",
                "socializacao": "Organizar leitura cruzada entre duplas para verificacao de coesao e fidelidade ao original.",
                "encerramento": f"Finalizar consolidando os criterios de resumo e realizar {encerramento}."
            }
        if tipo == "variacao_linguistica":
            return {
                "para_comecar": f"Iniciar apresentando situacao real de uso da lingua sobre {tema} e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} destacando exemplos de variacao regional, social ou historica.",
                "foco": f"Sistematizar o conceito de variacao linguistica em {tema} contra o preconceito linguistico.",
                "pratica": f"Propor atividade de classificacao, analise e {registro} no caderno.",
                "socializacao": "Promover discussao dialogada sobre a adequacao da fala aos diferentes contextos de uso.",
                "encerramento": f"Finalizar reforcando que adequacao e diferente de erro e realizar {encerramento}."
            }
        if tipo == "argumentacao_debate":
            return {
                "para_comecar": f"Apresentar tema polemico sobre {tema} e realizar {retomada} para aquecimento.",
                "hora_leitura": f"Conduzir {leitura} de artigo de opiniao ou editorial localizando a tese e argumentos.",
                "foco": "Explicar a estrutura da argumentacao (tese, argumentos, contra-argumentos e evidencias).",
                "pratica": f"Orientar a definicao e o registro de posicionamentos fundamentados com {registro}.",
                "socializacao": "Organizar debate regrado ou roda de conversa para socializacao dos argumentos da turma.",
                "encerramento": f"Finalizar sintetizando a importancia de argumentar com respeito e aplicar {encerramento}."
            }
        if tipo == "texto_digital_blog":
            return {
                "para_comecar": f"Retomar a leitura anterior e os registros sobre {tema} fazendo {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de post de blog ou postagem analisando o tom do texto e o leitor.",
                "foco": f"Sistematizar a organizacao e a linguagem do texto digital sobre {tema}.",
                "pratica": f"Orientar a escrita de um comentario ou resposta argumentativa com {registro}.",
                "socializacao": "Promover compartilhamento dos comentarios e devolutiva coletiva sobre clareza e respeito.",
                "encerramento": f"Finalizar discutindo a leitura critica no meio digital e aplicar {encerramento}."
            }
        if tipo == "analise_linguistica_ortografia":
            return {
                "para_comecar": f"Retomar exemplos linguisticos do texto estudado em {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} focalizando palavras ou marcas especificas a serem analisadas.",
                "foco": f"Sistematizar a regra ortografica ou recurso linguistico em {tema} e seu efeito de sentido.",
                "pratica": f"Orientar atividade aplicada de analise de palavras e revisao escrita com {registro}.",
                "socializacao": "Realizar correcao comentada no quadro tirando duvidas recorrentes.",
                "encerramento": f"Finalizar sintetizando como o estudo da escrita amplia a expressividade com {encerramento}."
            }
        # Fallback de dupla
        return {
            "para_comecar": f"Iniciar a aula conectando {tema} aos conhecimentos previos e realizar {retomada}.",
            "hora_leitura": f"Conduzir {leitura} de trechos selecionados do material de {tema}.",
            "foco": f"Sistematizar os principais conceitos de {tema} com base em exemplos contextualizados.",
            "pratica": f"Orientar a resolucao das questoes propostas com {registro} no caderno.",
            "socializacao": "Promover correcao dialogada e partilha de duvidas.",
            "encerramento": f"Finalizar sintetizando as aprendizagens centrais e aplicar {encerramento}."
        }
    else:
        # AULA SIMPLES (Garante as chaves específicas que o motor de etapas necessita)
        if tipo == "autoavaliacao":
            return {
                "para_comecar": f"Retomar com a turma o percurso de {tema} e {retomada}.",
                "foco": f"Apresentar os criterios de autoavaliacao estabelecidos para {tema}.",
                "pratica": f"Orientar a autoavaliacao de forma individual com {registro}.",
                "socializacao": "Promover partilha das impressoes e autoavaliacoes em duplas.",
                "encerramento": f"Finalizar discutindo as metas individuais de avanco e aplicar {encerramento}."
            }
        if tipo == "literatura":
            return {
                "para_comecar": f"Apresentar imagens ou contexto do autor de {tema} e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} dos trechos literarios ou fragmentos selecionados.",
                "foco": f"Explorar a estetica, marcas literarias e construcao de sentidos em {tema}.",
                "pratica": f"Orientar exercicio de analise critica do texto com {registro}.",
                "encerramento": f"Finalizar com reflexao sobre o tema estetico e aplicar {encerramento}."
            }
        if tipo == "genero_textual":
            return {
                "para_comecar": f"Iniciar conectando o genero de {tema} ao cotidiano e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de um texto modelo representativo do genero.",
                "foco": f"Apresentar definicao, suporte, publico-alvo e marcas do genero de {tema}.",
                "pratica": f"Propor exercicios praticos de interpretacao do genero com {registro}.",
                "encerramento": f"Finalizar sintetizando a funcao social do genero e aplicar {encerramento}."
            }
        if tipo == "producao_textual":
            return {
                "para_comecar": f"Apresentar a proposta de escrita sobre {tema} e {retomada} dos objetivos.",
                "foco": f"Apresentar os criterios de qualidade e roteiro de planejamento para {tema}.",
                "pratica": f"Conduzir {leitura} e orientar planejamento e rascunho com {registro}.",
                "encerramento": f"Finalizar refletindo sobre a escrita e revisao, aplicando {encerramento}."
            }
        if tipo == "pratica_oral":
            return {
                "relembre": f"Retomar a finalidade da atividade oral sobre {tema} e {retomada}.",
                "foco": f"Sistematizar resources da linguagem oral de {tema}, como entonacao e clareza.",
                "planejamento_oral": f"Orientar a organizacao do roteiro ou dos topicos de fala sobre {tema}.",
                "pratica": f"Conduzir a preparacao e a apresentacao oral com base em {leitura} e {registro}.",
                "socializacao": "Promover devolutiva coletiva valorizando clareza e respeito.",
                "encerramento": f"Finalizar sintetizando as percepcoes orais coletivas e aplicando {encerramento}."
            }
        if tipo == "gramatica_integrada":
            return {
                "para_comecar": f"Apresentar pergunta motivadora ou trecho curto sobre {tema} e realizar {retomada}.",
                "foco": f"Sistematizar o conteudo gramatical de {tema} relacionando a regra ao texto.",
                "pratica": f"Conduzir {leitura} e propor exercicios praticos com {registro}.",
                "encerramento": f"Finalizar consolidando o uso correto da convencao estudada com {encerramento}."
            }
        if tipo == "leitura_multimodal":
            return {
                "para_comecar": f"Iniciar analisando imagem, cartaz ou infografico sobre {tema} e realizar {retomada}.",
                "foco": f"Sistematizar como recursos verbais e visuais constroem sentido em {tema}.",
                "pratica": f"Conduzir {leitura} orientada do texto multimodal seguida de {registro}.",
                "socializacao": "Promover compartilhamento de leituras e visões sobre o texto multimodal.",
                "encerramento": f"Finalizar destacando a leitura critica do texto e aplicar {encerramento}."
            }
        if tipo == "resumo_retextualizacao":
            return {
                "para_comecar": f"Apresentar esquema, cartaz ou infografico de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} guiada e orientar a producao do resumo com {registro}.",
                "foco": f"Explicar a transformacao de dados do material em texto coerente sobre {tema}.",
                "de_olho_modelo": f"Apresentar exemplo estruturado de resumo para orientar a producao.",
                "todo_mundo_escreve": f"Solicitar escrita de topicos-chave para estruturacao do texto.",
                "pratica": f"Propor exercicios praticos de sintese baseados em {leitura}.",
                "revisao_colega": f"Promover a troca de resumos para revisao gramatical e textual simples.",
                "encerramento": f"Finalizar consolidando os criterios de resumo e realizar {encerramento}."
            }
        if tipo == "variacao_linguistica":
            return {
                "para_comecar": f"Iniciar apresentando situacao real de uso da lingua de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} destacando exemplos de variacao regional, social ou historica.",
                "foco": f"Sistematizar conceito de variacao em {tema} contra preconceitos.",
                "pause": f"Realizar pausa formativa para classificar casos de adequacao contextual.",
                "pratica": f"Propor atividade de classificacao, analise e {registro} no caderno.",
                "encerramento": f"Finalizar reforcando a adequacao ao contexto e aplicar {encerramento}."
            }
        if tipo == "argumentacao_debate":
            return {
                "para_comecar": f"Apresentar tema polemico sobre {tema} e realizar {retomada}.",
                "foco": f"Explicar a estrutura da argumentacao (tese, argumentos e evidencias) em {tema}.",
                "pause": f"Realizar checagem objetiva dos tipos de argumentos identificados.",
                "hora_leitura": f"Conduzir {leitura} do texto argumentativo ou de opiniao estudado.",
                "planejamento_debate": f"Organizar roteiro simples de argumentos e contra-argumentos.",
                "pratica": f"Orientar o registro de posicionamento com {registro} e discussao.",
                "encerramento": f"Finalizar incentivando a argumentacao respeitosa e aplicar {encerramento}."
            }
        if tipo == "texto_digital_blog":
            return {
                "para_comecar": f"Retomar a leitura anterior e os registros sobre {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de post de blog analisando a linguagem e interlocutores.",
                "foco": f"Sistematizar a organizacao e linguagem do texto digital de {tema}.",
                "todo_mundo_escreve": f"Orientar elaboracao de comentario curto ou resposta argumentativa.",
                "pratica": f"Orientar escrita do comentario final no caderno com {registro}.",
                "encerramento": f"Finalizar com discussao critica sobre leitura digital e aplicar {encerramento}."
            }
        if tipo == "analise_linguistica_ortografia":
            return {
                "para_comecar": f"Retomar marcas ou palavras do texto estudado em {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} focada nas palavras a serem analisadas.",
                "foco": f"Sistematizar recurso linguistico ou ortografico de {tema} e seus efeitos.",
                "pratica": f"Conduzir {leitura} e propor exercicio de analise ortografica com {registro}.",
                "socializacao": f"Realizar correcao dialogada comparando registros no quadro.",
                "encerramento": f"Finalizar sintetizando o estudo contextualizado com {encerramento}."
            }

        # Fallbacks antigos para compatibilidade
        if tipo == "gramatica_contextualizada":
            return {
                "relembre": f"Retomar conhecimentos sobre o fenomeno gramatical e realizar {retomada}.",
                "foco": f"Explicar a norma-padrao ou variacao linguistica em {tema} conectando regra e sentido.",
                "pause": f"Realizar pausas para analise de trechos especificos do material.",
                "pratica": f"Orientar aplicacao dos conceitos com {registro} no caderno.",
                "encerramento": f"Sintetizar regra ou norma estudada em {tema} e aplicar {encerramento}."
            }
        if tipo == "leitura_jornalistica":
            return {
                "para_comecar": f"Mobilizar conhecimentos sobre {tema} a partir de manchetes e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de texto jornalistico identificando lide e dados.",
                "pratica": f"Propor questoes de compreensao e analise com {registro}.",
                "foco": f"Explorar papel do jornalismo e construcao de sentidos em {tema}.",
                "encerramento": f"Sintetizar as percepcoes sobre leitura e aplicar {encerramento}."
            }

        return None
    return None


