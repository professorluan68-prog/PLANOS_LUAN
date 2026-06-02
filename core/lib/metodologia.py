"""
Motor unificado de geração de metodologia (sem IA).

Substitui a geração fraca do inteligencia_local.py (5 etapas fixas)
pelo motor sofisticado que já existia no lote.py (etapas variáveis por perfil),
integrando as novas bibliotecas de técnicas e progressão.
"""

from core.lib.classificador import perfil_disciplina, detectar_tipo_aula, normalizar_texto, contem_termos
from core.lib.tecnicas import SeletorTecnicas
from core.lib.progressao import ajustar_texto_por_posicao
from core.lib.extrator_pdf import ExtratorPDF
from core.orientacao_estudos_metodologia import montar_frases_orientacao_estudos
from core.qualidade_metodologica import (
    corrigir_mojibake,
    naturalizar_texto_metodologico,
)


_seletor_tecnicas = SeletorTecnicas()
_extrator = ExtratorPDF()


class ValidadorQualidade:
    """Remove etapas vazias e formata corretamente os blocos de texto."""

    def refinar(self, metodologia: list[dict]) -> list[dict]:
        validada = []
        for etapa in metodologia:
            if etapa.get("texto") and len(etapa["texto"].strip()) > 10:
                texto = naturalizar_texto_metodologico(corrigir_mojibake(etapa["texto"].strip()))
                if not texto.endswith('.'):
                    texto += '.'
                etapa["texto"] = texto
                validada.append(etapa)
        return validada


def _etapas_por_perfil(perfil: str, tipo: str) -> list[tuple[str, str]]:
    """Define as etapas metodológicas adequadas ao perfil e tipo de aula."""

    if perfil == "matematica":
        if tipo == "khan":
            return [
                ("Abertura", "abertura"),
                ("Prática na Khan Academy", "pratica_khan"),
                ("Fechamento", "fechamento_khan"),
            ]
        if tipo == "verificacao":
            return [
                ("Relembre", "para_comecar"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "modelagem":
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "grafico":
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo in {"resolucao_problemas", "tecnologia"}:
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Pause e responda", "pause"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        # conceito_novo e demais tipos do catálogo de conteúdo
        return [
            ("Para começar", "para_comecar"),
            ("Foco no conteúdo", "foco"),
            ("De olho no modelo", "de_olho_modelo"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "lingua_portuguesa_em":
        # Etapas várias por tipo de aula LP
        if tipo == "gramatica_contextualizada":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco"),
                ("Pause e responda", "pause"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "producao_textual":
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco"),
                ("Na prática", "pratica"),
                ("Compartilhamento", "compartilhamento"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "leitura_jornalistica":
            return [
                ("Para começar", "para_comecar"),
                ("Hora da leitura", "hora_leitura"),
                ("Na prática", "pratica"),
                ("Foco no conteúdo", "foco"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "pesquisa":
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        # leitura_literaria (padrão LP EM)
        return [
            ("Para começar", "para_comecar"),
            ("Hora da leitura", "hora_leitura"),
            ("Na prática", "pratica"),
            ("Foco no conteúdo", "foco"),
            ("Encerramento", "encerramento"),
        ]


    if perfil in {"leitura_redacao"} and tipo == "producao":
        return [
            ("Para começar", "para_comecar"),
            ("Leitura e construção do conteúdo", "leitura"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Revisão e reescrita", "encerramento"),
        ]

    if perfil == "orientacao_estudos":
        return [
            ("Para comecar", "para_comecar"),
            ("Leitura e construcao do conteudo", "leitura"),
            ("Foco no conteudo", "foco"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "educacao_financeira":
        etapas = [
            ("Para começar", "para_comecar"),
            ("Análise de caso", "analise_caso"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
        ]
        if tipo in {"credito_endividamento", "investimento_poupanca", "analise_percentuais_noticias"}:
            etapas.append(("Cálculos financeiros", "calculos"))
            etapas.append(("Na prática", "pratica"))
        elif tipo == "orcamento_planejamento":
            etapas.append(("Planejamento orçamentário", "planejamento"))
        elif tipo == "empreendedorismo":
            etapas.append(("Projeto empreendedor", "projeto"))
        else:
            etapas.append(("Na prática", "pratica"))
        etapas.append(("Encerramento", "encerramento"))
        return etapas

    if perfil == "projeto_de_vida":
        if tipo == "futureme":
            return [
                ("Para começar", "ponto_de_partida"),
                ("Foco no conteúdo", "construindo_o_conceito"),
                ("Na prática", "acesso_plataforma"),
                ("Compartilhamento", "compartilhamento"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "producao_coletiva":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco_no_tema"),
                ("Na prática", "producao_em_grupos"),
                ("Compartilhamento", "apresentacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "convivencia":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco_no_tema"),
                ("Na prática", "circulo_ou_votacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "consciencia_social":
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco_no_tema"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "encerramento":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "sintese_do_percurso"),
                ("Na prática", "producao_final"),
                ("Encerramento", "encerramento"),
            ]
        # autoconhecimento / default
        return [
            ("Para começar", "ponto_de_partida"),
            ("Foco no conteúdo", "construindo_o_conceito"),
            ("Na prática", "colocando_em_pratica"),
            ("Compartilhamento", "virem_e_conversem"),
            ("Encerramento", "encerramento"),
        ]

    # Padrão geral
    return [
        ("Para começar", "para_comecar"),
        ("Leitura e construção do conteúdo", "leitura"),
        ("Foco no conteúdo", "foco"),
        ("Pause e responda", "pause"),
        ("Na prática", "pratica"),
        ("Encerramento", "encerramento"),
    ]


_PRIORIDADE_RECURSO = [
    "producao_textual",
    "calculo_resolucao",
    "analise_grafico",
    "analise_geografica",
    "analise_imagem",
    "experimentacao",
    "debate_oral",
    "leitura_texto",
]


def _recurso_principal(recursos_detectados: list[str] | None) -> str:
    recursos = [normalizar_texto(recurso) for recurso in list(recursos_detectados or [])]
    for prioridade in _PRIORIDADE_RECURSO:
        if prioridade in recursos:
            return prioridade
    return recursos[0] if recursos else ""


def _ajustar_por_recurso(base: dict[str, str], recurso_principal: str, tema: str, atividade_extraida: str) -> None:
    atividade = corrigir_mojibake(atividade_extraida or "")
    if recurso_principal == "analise_grafico":
        base["foco"] = (
            f"Conduzir a leitura de gráficos ou tabelas relacionados a {tema}, destacando título, legenda, eixos, categorias, variações e comparação de dados antes da interpretação."
        )
        base["pratica"] = (
            f"Orientar a análise dos dados em etapas, retomando o que a atividade pede e solicitando registros sobre padrões, comparações e conclusões. Atividade central do material: {atividade or 'interpretar informações numéricas e justificar respostas.'}"
        )
    elif recurso_principal == "analise_geografica":
        base["foco"] = (
            f"Explorar o mapa como linguagem principal da aula, destacando título, legenda, escala, localização e o fenômeno espacial relacionado a {tema}."
        )
        base["pratica"] = (
            f"Orientar leitura guiada do mapa e registro das observações no caderno, solicitando localização, comparação e explicação do fenômeno analisado. Atividade central do material: {atividade or 'interpretar informações do mapa com apoio do professor.'}"
        )
    elif recurso_principal == "analise_imagem":
        base["leitura"] = (
            "Explorar a imagem, charge, fotografia ou esquema do material com leitura mediada, destacando elementos visuais, pistas de sentido e relações com o tema da aula."
        )
        base["pratica"] = (
            f"Orientar a observação guiada da imagem e a construção de respostas com base em evidências visuais, articulando descrição, interpretação e justificativa. Atividade central do material: {atividade or 'analisar a imagem e registrar as conclusões mais importantes.'}"
        )
    elif recurso_principal == "producao_textual":
        base["foco"] = (
            f"Retomar as características do gênero ou proposta de escrita relacionada a {tema}, destacando finalidade, interlocutor, organização das ideias e critérios de qualidade."
        )
        base["pratica"] = (
            f"Organizar a atividade em planejamento, escrita, revisão e reescrita, com mediação do professor durante o processo. Atividade central do material: {atividade or 'produzir um texto coerente com o gênero e revisar a versão inicial.'}"
        )
    elif recurso_principal == "calculo_resolucao":
        base["foco"] = (
            f"Explicar o procedimento central de {tema} com exemplo resolvido passo a passo, destacando leitura dos dados, escolha da operação e conferência do resultado."
        )
        base["pratica"] = (
            f"Orientar a resolução das questões em etapas, solicitando registro do raciocínio e comparação de estratégias. Atividade central do material: {atividade or 'resolver os cálculos e justificar o procedimento utilizado.'}"
        )
    elif recurso_principal == "experimentacao":
        base["foco"] = (
            f"Apresentar o fenômeno relacionado a {tema} por meio de observação orientada, hipótese inicial e organização das etapas do experimento ou demonstração."
        )
        base["pratica"] = (
            f"Conduzir a atividade experimental com registro de observações, comparação de resultados e conclusão baseada em evidências. Atividade central do material: {atividade or 'observar, registrar e concluir a partir da prática proposta.'}"
        )


def _conceito_projeto_vida(conceito: str, tema: str, texto_base: str, atividade_extraida: str) -> str:
    conceito_limpo = corrigir_mojibake(str(conceito or "")).strip(" .:-")
    conceito_norm = normalizar_texto(conceito_limpo)
    tema_norm = normalizar_texto(tema)
    base_contexto = normalizar_texto(" ".join([atividade_extraida or "", texto_base or "", tema or ""]))

    generico = (
        not conceito_norm
        or conceito_norm == tema_norm
        or any(
            marcador in conceito_norm
            for marcador in [
                "questao essencial",
                "habilidade",
                "competencia",
                "competencias",
                "tema da aula",
                "conteudo da aula",
            ]
        )
        or (conceito_norm.split()[-1:] and conceito_norm.split()[-1] in {"a", "as", "o", "os", "de", "da", "do", "e", "em", "com", "para", "por"})
    )
    if not generico:
        return conceito_limpo

    if any(termo in base_contexto for termo in ["autoconhecimento", "quem sou", "identidade"]):
        return "autoconhecimento e cuidado consigo"
    if any(termo in base_contexto for termo in ["opiniao", "opinioes", "ponto de vista", "pontos de vista", "conviv", "respeito"]):
        return "pontos de vista, respeito e convivencia"
    if any(termo in base_contexto for termo in ["print", "post", "postar", "digital", "rede", "online", "internet"]):
        return "exposicao e responsabilidade no ambiente digital"
    return "escolhas, convivencia e responsabilidade"


def _metodologia_matematica(texto_base: str, tema: str, tipo: str) -> list[dict]:
    """Gerador especializado de etapas para o perfil Matemática.

    Retorna lista de dicts {titulo, texto} diferenciada por tipo de aula:
    'conceito_novo', 'verificacao', 'khan', 'modelagem', 'grafico',
    'resolucao_problemas', 'tecnologia'.

    Chame este gerador a partir de _frases_por_contexto quando perfil=='matematica'.
    A lista retornada sobrepõe o dicionário base de frases usado pelo motor geral.
    """
    if tipo == "khan":
        return [
            {
                "titulo": "Abertura",
                "texto": f"Retomar com a turma os conceitos principais relacionados a {tema}, levantando conhecimentos prévios e orientando o acesso à plataforma.",
            },
            {
                "titulo": "Prática na Khan Academy",
                "texto": f"Encaminhar os estudantes para a prática no aplicativo, reforçando que o objetivo é revisar, testar hipóteses, aprender com os erros e repetir a atividade sempre que necessário até dominar a habilidade. Orientar paralelamente os que precisarem de atividades no caderno.",
            },
            {
                "titulo": "Fechamento",
                "texto": f"Retomar coletivamente as principais dúvidas percebidas durante a prática, socializar estratégias de resolução e registrar os pontos que precisarão ser reforçados, utilizando o desempenho dos estudantes no aplicativo como apoio para o acompanhamento.",
            },
        ]

    if tipo == "verificacao":
        return [
            {
                "titulo": "Relembre",
                "texto": f"Retomar com a turma os conceitos principais trabalhados no bloco, relacionando {tema} a situações do cotidiano e levantando conhecimentos prévios dos estudantes antes das atividades.",
            },
            {
                "titulo": "Na prática",
                "texto": f"Orientar os estudantes na resolução das atividades no caderno, trabalhando detalhadamente as resoluções e propondo outras estratégias quando necessário. Circular pela sala para identificar dificuldades e oferecer mediação individualizada.",
            },
            {
                "titulo": "Encerramento",
                "texto": f"Retomar coletivamente as principais dúvidas percebidas durante a atividade, socializar estratégias de resolução e registrar os pontos que precisarão ser reforçados nas próximas aulas.",
            },
        ]

    if tipo == "modelagem":
        return [
            {
                "titulo": "Para começar",
                "texto": f"Iniciar a aula com a situação-problema do material sobre {tema}, incentivando a turma a levantar hipóteses e identificar quais grandezas estão envolvidas. Aplicar Virem e conversem para socializar ideias antes da construção do modelo.",
            },
            {
                "titulo": "Foco no conteúdo",
                "texto": f"Conduzir a construção do modelo matemático para {tema}, identificando as grandezas envolvidas, estabelecendo a relação entre elas e traduzindo para linguagem algébrica. Destacar que o modelo é uma representação da situação real e que o resultado deve ser interpretado no contexto do problema.",
            },
            {
                "titulo": "De olho no modelo",
                "texto": f"Apresentar um exemplo comentado mostrando as diferentes representações do conceito: tabular, algébrica e gráfica, mostrando como cada forma revela aspectos distintos da mesma relação matemática.",
            },
            {
                "titulo": "Na prática",
                "texto": f"Encaminhar atividade de modelagem com registro dos cálculos e justificativa. Reforçar que o resultado deve ser interpretado no contexto, verificando se faz sentido na situação real estudada.",
            },
            {
                "titulo": "Encerramento",
                "texto": f"Encerrar com síntese: como traduzir uma situação real em linguagem matemática? O que o modelo nos permite descobrir? Aplicar Com suas palavras, incentivando os estudantes a reelaborarem com autonomia.",
            },
        ]

    if tipo == "grafico":
        return [
            {
                "titulo": "Para começar",
                "texto": f"Iniciar a aula com dados ou situação que motiva a representação gráfica de {tema}. Propor discussão em duplas sobre como representar visualmente a relação entre as grandezas.",
            },
            {
                "titulo": "Foco no conteúdo",
                "texto": f"Conduzir a leitura orientada de gráficos, tabelas ou dados do material, ajudando a turma a interpretar informações, comparar valores e construir conclusões com base nas evidências. Disponibilizar leitura guiada de gráficos, destacando título, eixos, valores e comparação entre os dados.",
            },
            {
                "titulo": "De olho no modelo",
                "texto": f"Apresentar exemplo comentado explorando as diferentes representações: tabular, algébrica e gráfica de {tema}.",
            },
            {
                "titulo": "Na prática",
                "texto": f"Propor atividade de aplicação em que os estudantes interpretem dados, construam ou analisem gráficos e registrem conclusões explicando o que as informações revelam sobre {tema}.",
            },
            {
                "titulo": "Encerramento",
                "texto": f"Encerrar com síntese da leitura gráfica, aplicando Com suas palavras: o que o gráfico/tabela nos mostra sobre {tema}? Que decisões podemos tomar a partir dessas informações?",
            },
        ]

    # resolucao_problemas e tecnologia: template de conceito_novo com ajuste no Foco
    if tipo == "resolucao_problemas":
        foco_extra = f"Conduzir a resolução seguindo as etapas do método: compreender o problema, construir um plano de ação, executar e verificar a solução. Destacar que a resposta deve ser interpretada no contexto, não apenas numérica."
    elif tipo == "tecnologia":
        foco_extra = f"Propor atividade de exploração em que os estudantes utilizem a ferramenta tecnológica disponível para investigar propriedades de {tema}, registrando observações e construindo conclusões a partir dos dados obtidos."
    else:
        foco_extra = None

    # Template padrão: conceito_novo (e fallback para resolucao_problemas/tecnologia)
    etapas = [
        {
            "titulo": "Para começar",
            "texto": f"Iniciar a aula com a situação-problema apresentada no material sobre {tema}, incentivando a turma a levantar hipóteses e antecipar possíveis caminhos de análise. Aplicar a técnica Virem e conversem para que os estudantes discutam em duplas e socializem suas ideias antes da explicação formal.",
        },
        {
            "titulo": "Foco no conteúdo",
            "texto": foco_extra or f"Desenvolver {tema} de forma progressiva, conectando explicação, exemplo e atividade guiada com mediação passo a passo, destacando dados, operações e interpretação dos resultados. Conduzir a explicação com a técnica Um passo de cada vez, organizando o conteúdo em etapas claras e progressivas.",
        },
        {
            "titulo": "De olho no modelo",
            "texto": f"Apresentar um exemplo comentado como referência orientadora antes da atividade principal, destacando cada etapa do raciocínio: identificação dos dados, escolha da estratégia, execução e verificação do resultado.",
        },
        {
            "titulo": "Pause e responda",
            "texto": f"Realizar uma pausa de verificação da aprendizagem para que os estudantes comparem respostas, justifiquem ideias e revisem o raciocínio antes de avançar. Usar a pausa também para verificar quais aprendizagens já estão consolidadas e quais precisam de retomada.",
        },
        {
            "titulo": "Na prática",
            "texto": f"Encaminhar atividade com registro dos cálculos e breve justificativa, reforçando a relação entre procedimento, resultado e tomada de decisão. Solicitar que os estudantes incluam a interpretação do resultado no contexto da situação estudada.",
        },
        {
            "titulo": "Encerramento",
            "texto": f"Encerrar a aula com síntese dos pontos principais, retomando especialmente {tema}. Aplicar a técnica Com suas palavras, incentivando os estudantes a reelaborarem o conteúdo com autonomia.",
        },
    ]
    return etapas


def _metodologia_lingua_portuguesa(texto_base: str, tema: str, tipo: str) -> dict[str, str] | None:
    """Gerador especializado de frases para o perfil Lingua Portuguesa."""
    if tipo == "gramatica_contextualizada":
        return {
            "relembre": "Retomar conhecimentos anteriores sobre o fenômeno gramatical em foco, utilizando exemplos curtos ou situações de uso.",
            "foco": f"Explicar o funcionamento da norma-padrão ou variação linguística em {tema}, conectando a regra ao efeito de sentido gerado no texto.",
            "pause": "Realizar pausas para análise de trechos específicos, verificando se a turma identifica a aplicação do conteúdo gramatical estudado.",
            "pratica": "Orientar a aplicação dos conceitos em frases ou pequenos textos, focando na adequação do uso da língua à intenção comunicativa.",
            "encerramento": f"Sintetizar a regra ou norma estudada em {tema}, destacando como o domínio dessa convenção amplia as possibilidades de escrita e leitura."
        }
    if tipo == "producao_textual":
        return {
            "para_comecar": f"Apresentar a proposta de escrita sobre {tema}, discutindo a relevância do tema e a situação comunicativa (quem escreve, para quem, onde).",
            "foco": "Analisar as convenções do gênero textual, estrutura, registro e recursos linguísticos necessários para a produção.",
            "pratica": "Orientar a escrita e o planejamento do texto, garantindo que os estudantes apliquem as características do gênero e critérios de qualidade.",
            "compartilhamento": "Promover um momento de compartilhamento das produções ou etapas do planejamento para revisão entre pares ou socialização.",
            "encerramento": "Finalizar com a verificação de autoria e a importância do processo de reescrita para o aperfeiçoamento do texto."
        }
    if tipo == "leitura_jornalistica":
        return {
            "para_comecar": f"Mobilizar conhecimentos sobre o tema {tema} a partir de manchetes ou contextos atuais de circulação social.",
            "hora_leitura": "Conduzir a leitura analítica do texto jornalístico, identificando lide, fato, dados e recursos de linguagem presentes.",
            "pratica": "Propor questões de compreensão e análise crítica, incentivando a busca por evidências no texto.",
            "foco": "Explorar o papel do jornalismo e a construção de sentidos no texto, destacando a importância da veracidade e da clareza na informação.",
            "encerramento": "Sintetizar as percepções sobre o tema e a leitura, reforçando o valor da informação consciente."
        }
    return None


def _metodologia_projeto_de_vida(texto_base: str, tema: str, tipo: str, conceito: str, atividade_extraida: str) -> dict[str, str] | None:
    """Gerador especializado de frases para o perfil Projeto de Vida."""
    import re
    texto_norm = normalizar_texto(texto_base)

    # Questão essencial
    match_q = re.search(r"(?:questao essencial|pergunta disparadora)[:\s]*([^\n?]+\??)", texto_base, re.I)
    questao = match_q.group(1).strip() if match_q else f"como as escolhas de hoje influenciam o amanhã em relação a {tema}?"

    # Música ou Vídeo disparador
    match_mv = re.search(r"(?:musica|m%C3%BAsica|clipe|video|v%C3%ADdeo|cancao|can%C3%A7ao|can%C3%A7%C3%A3o)[:\s]*([^\n,.]+)", texto_base, re.I)
    midia_nome = match_mv.group(1).strip() if match_mv else ""

    # Extração de perguntas adicionais
    perguntas = re.findall(r"([^?\n]{15,100}\?)", texto_base)
    p1 = perguntas[0].strip() if len(perguntas) > 0 else f"O que você pensa sobre {tema}?"
    p2 = perguntas[1].strip() if len(perguntas) > 1 else "Como isso se aplica no seu dia a dia?"

    # Construção do conceito
    conceito_seguro = _conceito_projeto_vida(conceito, tema, texto_base, atividade_extraida)

    # Atividade prática
    atividade = atividade_extraida or f"mapeamento e reflexão sobre {tema}"

    if tipo == "futureme":
        match_act = re.search(r"(?:questionario de perfil|questionario de personalidade|mapa de oportunidades|podio dos cursos|podio das profissoes)", texto_norm)
        act_name = match_act.group(0).title() if match_act else "Questionário de Perfil Profissional"
        return {
            "ponto_de_partida": f"Iniciar a aula convidando os estudantes a pensarem sobre o papel da tecnologia no autoconhecimento profissional. Propor a pergunta: '{questao}' e abrir para uma breve discussão em duplas.",
            "construindo_o_conceito": f"Apresentar o conceito de {conceito_seguro} de forma dialogada, destacando a importância de usar ferramentas estruturadas para mapear afinidades e possibilidades de carreira.",
            "acesso_plataforma": f"Orientar os estudantes a acessarem a plataforma FutureMe e seguirem o passo a passo para o {act_name}, garantindo que todos consigam navegar de forma autônoma e segura.",
            "compartilhamento": "Após a conclusão, organizar a troca em duplas ou trios sobre os resultados do relatório: o que mais fez sentido e o que causou surpresa, exercitando a escuta ativa.",
            "encerramento": "Encerrar propondo que cada estudante registre no caderno uma síntese pessoal sobre como as descobertas da plataforma se conectam aos seus objetivos futuros."
        }

    if tipo == "producao_coletiva":
        match_prod = re.search(r"(?:biomapa|campanha|mostra|painel|caixa dos vinculos|video|festival do minuto|hq)", texto_norm)
        prod_name = match_prod.group(0).title() if match_prod else "projeto do bimestre"
        return {
            "relembre": f"Retomar brevemente as reflexões e produções das aulas anteriores, relembrando o objetivo do {prod_name} e como cada estudante contribuiu até aqui.",
            "foco_no_tema": f"Explicar as etapas e critérios necessários para a produção prática de hoje, destacando o papel da colaboração, da divisão de tarefas e do respeito mútuo.",
            "producao_em_grupos": f"Organizar a turma em grupos de 4 a 6 estudantes e orientar a elaboração passo a passo do {prod_name}. Circular pela sala apoiando o desenvolvimento e a mediação de conflitos.",
            "apresentacao": f"Promover a socialização das produções ou do andamento das propostas com a turma, permitindo que cada grupo compartilhe suas escolhas e aprendizados.",
            "encerramento": f"Finalizar solicitando que cada estudante registre individualmente uma reflexão sobre a importância do trabalho coletivo e o impacto do {prod_name} no ambiente escolar."
        }

    if tipo == "convivencia":
        return {
            "relembre": f"Retomar os acordos de convivência e a importância de construir um espaço seguro para o diálogo e a tomada de decisões coletivas a partir de {tema}.",
            "foco_no_tema": f"Apresentar o dilema ou tema de reflexão coletiva sobre {conceito_seguro}, explicando como as decisões de cada um afetam o grupo e ajudando a turma a relacionar sentir, pensar e agir de forma respeitosa na convivência escolar.",
            "circulo_ou_votacao": "Organizar a turma em círculo para a dinâmica do Círculo de Convivência, estabelecendo os papéis de mediador, secretário e guardião do tempo. Após o debate, conduzir o levantamento de soluções e registrar a decisão coletiva no Painel de Convivência.",
            "encerramento": "Encerrar a aula solicitando o registro individual no caderno do compromisso pessoal que cada aluno assume para contribuir com a decisão do grupo e a harmonia da convivência."
        }

    if tipo == "consciencia_social":
        return {
            "para_comecar": f"Iniciar a aula com uma pergunta provocadora ou dinâmica corporal que sensibilize os estudantes para o tema de privilégios e desigualdades associados a {tema}, sem expor experiências pessoais.",
            "foco_no_tema": f"Apresentar conceitos e dados relacionados a {conceito_seguro}, discutindo a diferença entre condições estruturais e esforço individual de forma dialógica.",
            "pratica": "Conduzir a leitura dialogada de reportagem, infográfico ou situação-problema do material. Em seguida, propor atividade prática de análise crítica (como o mapa do ambiente digital ou revisão da HQ) para registrar as conclusões do grupo.",
            "encerramento": "Finalizar com uma reflexão escrita individual sobre como o reconhecimento de privilégios e desvantagens pode transformar as atitudes e escolhas diárias."
        }

    if tipo == "encerramento":
        match_prod = re.search(r"(?:caixa dos vinculos|painel de convivencia|mostra|pacto final|video|biomapa)", texto_norm)
        prod_name = match_prod.group(0).title() if match_prod else "projeto do bimestre"
        return {
            "relembre": f"Abrir a aula retomando simbolicamente a jornada do bimestre e revisitando o {prod_name} para reconectar a turma com as vivências acumuladas.",
            "sintese_do_percurso": "Conduzir uma breve retrospectiva dialogada sobre os temas trabalhados, celebrando a evolução, os desafios superados e os aprendizados construídos.",
            "producao_final": f"Orientar a conclusão e apresentação do produto final (vídeo, mostra, pacto ou painel), garantindo a participação de todos os estudantes.",
            "encerramento": "Reservar tempo para a escrita de uma síntese pessoal no caderno/livro, focando em uma descoberta significativa. Encerrar a aula com um ritual simbólico de compromisso (como depositar palavras na caixa, assinar o painel ou compartilhar post-its)."
        }

    # autoconhecimento / default
    if midia_nome:
        ponto_partida_str = f"Iniciar a aula com a escuta/exibição da música ou vídeo '{midia_nome}', convidando os estudantes a perceberem as emoções e ideias despertadas, sem exigir exposicao pessoal. Propor que conversem em duplas sobre as questões: '{p1}' e '{p2}'."
    else:
        ponto_partida_str = f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. Propor que os estudantes compartilhem suas impressões sobre a pergunta existencial: '{questao}', respeitando diferentes ritmos de participacao."

    return {
        "ponto_de_partida": ponto_partida_str,
        "construindo_o_conceito": f"Conduzir uma exposição dialogada sobre {conceito_seguro}, utilizando exemplos cotidianos para ajudar a turma a relacionar sentir, pensar e agir de forma respeitosa.",
        "colocando_em_pratica": f"Orientar a elaboração individual de {atividade}, com instruções passo a passo. Garantir que a socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas.",
        "virem_e_conversem": f"Organizar o compartilhamento das produções em duplas, com base nas perguntas do material, exercitando a escuta ativa e o respeito mútuo.",
        "encerramento": "Finalizar propondo que cada estudante registre no caderno uma síntese pessoal das descobertas e sentimentos despertados ao longo da aula."
    }


def _frases_por_contexto(
    perfil: str, tipo: str, tema: str, conceito: str,
    turma: str, tecnicas: dict, texto_base: str = "",
    atividade_extraida: str = "",
    recursos_detectados: list[str] | None = None,
    etapas_detectadas: list[str] | None = None,
    habilidade: str = "",
) -> dict[str, str]:
    """Gera frases contextualizadas para cada etapa da metodologia."""

    t_disc = tecnicas.get("abertura", "Virem e conversem")
    t_reg = tecnicas.get("registro", "Todo mundo escreve")
    t_sint = tecnicas.get("sintese", "Com suas palavras")
    t_verif = tecnicas.get("verificacao", "Pause e responda")

    base = {
        "para_comecar": (
            f"Retomar conhecimentos prévios da turma sobre {tema}. Propor {t_disc} "
            "para levantar hipóteses, exemplos e dúvidas iniciais."
        ),
        "leitura": (
            "Realizar leitura guiada dos textos, imagens, comandos e/ou exemplos do material, fazendo pausas "
            "para destacar informações relevantes. Organizar no quadro as ideias principais e as palavras-chave "
            "que orientam a atividade."
        ),
        "contextualizacao": (
            f"Contextualizar {tema} a partir de situações do cotidiano, repertórios culturais ou exemplos do "
            "material, ajudando a turma a compreender por que esse conteúdo é relevante e como ele circula "
            "socialmente."
        ),
        "leitura_analitica": (
            "Conduzir leitura analítica do texto, imagem, dado ou situação apresentada, destacando escolhas de "
            "linguagem, organização das ideias, pistas visuais e informações que sustentam a compreensão."
        ),
        "foco": (
            f"Analisar {conceito}, relacionando o conteúdo ao objetivo da aula. Explicar os pontos centrais de "
            "forma dialogada e verificar se a turma compreende as relações entre conceito, exemplo e atividade."
        ),
        "pratica": (
            f"Orientar a resolução das atividades propostas, usando {t_reg} para garantir registro "
            "individual. Circular pela sala, mediar dúvidas e solicitar justificativas para as respostas."
        ),
        "pause": (
            f"Socializar algumas respostas e realizar correção dialogada com {t_verif}, retomando trechos do "
            "material, registros dos estudantes e dúvidas comuns antes de avançar."
        ),
        "encerramento": (
            f"Finalizar com {t_sint}, retomando os aprendizados sobre {tema} e registrando uma síntese "
            "curta no quadro ou no caderno."
        ),
    }

    recurso_principal = _recurso_principal(recursos_detectados)
    _ajustar_por_recurso(base, recurso_principal, tema, atividade_extraida)

    # Ajustes por perfil
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        # Delegar para o gerador especializado de LP se o tipo for reconhecido
        _frases_lp = _metodologia_lingua_portuguesa(texto_base, tema, tipo)
        if _frases_lp is not None:
            base.update(_frases_lp)
            return base

        # Fallback antigo para tipos não cobertos pelo gerador especializado
        if tipo == "producao":
            base["leitura"] = (
                "Apresentar a proposta de produção e realizar leitura guiada dos comandos, destacando finalidade, "
                "interlocutor, gênero textual e critérios de qualidade. Organizar no quadro um roteiro de planejamento."
            )
            base["foco"] = (
                f"Analisar as características do gênero relacionado a {tema}, observando estrutura, linguagem, "
                "organização das ideias e marcas que orientam a escrita."
            )
            base["pratica"] = (
                f"Orientar o planejamento, a escrita do rascunho e a revisão, solicitando {t_reg}. Solicitar que os estudantes confiram "
                "se o texto atende à finalidade, ao público e aos critérios combinados."
            )
        elif tipo == "argumentacao":
            base["foco"] = (
                f"Analisar tese, opinião, argumentos e estratégias persuasivas presentes em {conceito}. Destacar "
                "como escolhas de linguagem e exemplos ajudam a sustentar o ponto de vista."
            )
        else:
            base["foco"] = (
                f"Analisar {conceito}, destacando gênero, finalidade, público-alvo, recursos de linguagem e pistas "
                "textuais ou visuais que ajudam na compreensão."
            )

    elif perfil in {"orientacao_estudos"}:
        base.update(montar_frases_orientacao_estudos(tema, texto_base))
        if recurso_principal == "producao_textual":
            base["foco"] = (
                f"Retomar as caracteristicas da proposta relacionada a {tema}, mostrando como planejar a escrita, selecionar ideias "
                "centrais e revisar o texto com base em criterios simples e visiveis."
            )
            base["pratica"] = (
                "Organizar a atividade em planejamento, rascunho, revisao e versao final, com apoio do professor para transformar "
                "os comandos do material em passos concretos de estudo e producao."
            )
        elif recurso_principal == "analise_grafico":
            base["foco"] = (
                f"Explorar {conceito} ensinando a turma a ler titulo, legendas, linhas, colunas, valores e comparacoes antes de tirar conclusoes."
            )
            base["pratica"] = (
                "Orientar a leitura dos dados em etapas, pedindo que os estudantes registrem o que observaram, comparem informacoes "
                "e expliquem como chegaram as respostas."
            )
        elif recurso_principal == "analise_imagem":
            base["foco"] = (
                f"Explorar {conceito} a partir da leitura de imagens, tirinhas, charges ou esquemas, ajudando a turma a descrever, "
                "interpretar pistas visuais e relaciona-las ao texto verbal."
            )
        if "de olho no saeb" in normalizar_texto(texto_base):
            base["pratica"] += (
                " Quando o material trouxer DE OLHO NO SAEB, conduzir a resolucao de forma guiada, explicando como ler "
                "o enunciado, localizar pistas e revisar alternativas sem transformar a aula em treino mecanico."
            )

    elif perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        base["para_comecar"] = (
            f"Contextualizar {tema} com uma situação-problema, imagem, dado ou exemplo do cotidiano. Propor "
            f"{t_disc} para que os estudantes antecipem explicações e levantem evidências."
        )
        base["foco"] = (
            f"Explicar {conceito} de forma progressiva, relacionando fenômeno, causa, consequência e exemplos. "
            "Usar esquemas no quadro para diferenciar observação, hipótese e conceito científico."
        )
        base["pratica"] = (
            f"Orientar leitura de texto, imagem, modelo ou atividade investigativa, solicitando {t_reg}. "
            "Retomar as evidências usadas pelos estudantes para justificar as respostas."
        )

    elif perfil == "historia":
        base["foco"] = (
            f"Apresentar o contexto histórico de {conceito}, situando sujeitos, tempo, espaço e conflitos envolvidos. "
            "Relacionar as ideias iniciais da turma com os conceitos históricos em estudo."
        )
        base["pratica"] = (
            f"Orientar a análise de fontes, imagens, mapas, linhas do tempo ou textos do material, usando {t_reg}. Solicitar registro "
            "das evidências encontradas e mediação para diferenciar fato, interpretação e contexto."
        )

    elif perfil == "geografia":
        base["foco"] = (
            f"Analisar {conceito} considerando paisagem, território, escala, localização e relações entre sociedade "
            "e natureza. Usar mapa, imagem, tabela ou gráfico como apoio para a explicação."
        )
        base["pratica"] = (
            f"Orientar leitura de mapas, imagens, gráficos ou situações-problema, solicitando {t_reg} para que os estudantes "
            "identifiquem elementos espaciais e expliquem relações de causa e consequência."
        )

    elif perfil == "ingles":
        base["para_comecar"] = (
            f"Retomar vocabulário conhecido relacionado a {tema} com repetição oral breve e exemplos no quadro. "
            "Estimular que os estudantes tentem pronunciar e reconhecer palavras antes da sistematização."
        )
        base["leitura"] = (
            "Apresentar o texto, diálogo, imagem ou situação comunicativa, alternando leitura em voz alta, escuta "
            "e repetição. Destacar vocabulário-chave e estruturas em inglês com apoio em exemplos."
        )
        base["foco"] = (
            f"Explorar o uso comunicativo de {conceito}, mostrando quando e como empregar as expressões estudadas. "
            "Registrar no quadro exemplos curtos em inglês e seus sentidos em contexto."
        )
        base["pratica"] = (
            f"Organizar prática oral e escrita em pares, com {t_reg} (repetição, preenchimento, pequenas respostas ou diálogos). "
            "Acompanhar pronúncia, compreensão e uso funcional das expressões."
        )

    elif perfil == "arte":
        base["foco"] = (
            f"Apresentar referências artísticas relacionadas a {conceito}, orientando apreciação de elementos visuais, "
            "sonoros, corporais ou culturais. Valorizar percepções diferentes sem reduzir a aula a explicação teórica."
        )
        base["pratica"] = (
            f"Propor experimentação, criação ou apreciação orientada, com {t_reg} no diário de bordo. Acompanhar "
            "processos criativos, escolhas dos estudantes e socialização das produções ou percepções."
        )

    elif perfil == "projeto_de_vida":
        _frases_pv = _metodologia_projeto_de_vida(texto_base, tema, tipo, conceito, atividade_extraida)
        if _frases_pv is not None:
            base.update(_frases_pv)
            return base

    elif perfil == "lideranca_oratoria":
        conceito_seguro = _conceito_projeto_vida(conceito, tema, texto_base, atividade_extraida)
        base["para_comecar"] = (
            f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. Propor "
            "troca em duplas ou roda de conversa breve, respeitando diferentes ritmos de participacao."
        )
        base["foco"] = (
            f"Construir a reflexao sobre {conceito_seguro} por meio de exemplos escolares e cotidianos, ajudando a turma a "
            "relacionar sentir, pensar e agir de forma respeitosa."
        )
        base["pratica"] = (
            "Orientar atividade reflexiva com registro individual, escolha pessoal ou planejamento simples. Garantir "
            "que a socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas."
        )
        base["encerramento"] = (
            f"Encerrar com um compromisso simples ou observacao para a semana, relacionado a {tema}, reforcando "
            "autonomia, respeito e cuidado nas relacoes."
        )

    elif perfil == "educacao_financeira":
        conceito_seguro = tema if normalizar_texto(conceito) in {"educacao financeira", "financeira"} else conceito
        situacoes = {
            "orcamento_planejamento": "uma situação de organização de renda, gastos e prioridades para cumprir uma meta simples",
            "consumo_consciente": "um dilema de consumo em que a turma precise comparar necessidade, desejo, preço, durabilidade e impacto da escolha",
            "investimento_poupanca": "uma situação de poupança ou reserva de emergência em que pequenos valores acumulados ajudam a lidar com imprevistos",
            "credito_endividamento": "uma compra parcelada ou oferta de crédito em que seja necessário comparar valor à vista, juros, parcelas e custo total",
            "empreendedorismo": "um pequeno projeto de venda, serviço ou solução para a comunidade escolar, analisando custos, preço e viabilidade",
            "analise_percentuais_noticias": "uma noticia, manchete ou grafico em que a turma precise interpretar percentuais e relacionar os dados a uma situacao real",
            "governo_economia": "uma situacao cotidiana sobre como a acao do governo influencia precos, servicos, impostos e a vida economica da populacao",
            "impacto_decisoes_economicas": "uma situacao do cotidiano em que escolhas economicas afetam consumo, planejamento, prioridades e bem-estar",
            "cidadania_financeira": "uma situação de consumo que envolva direitos, responsabilidades, comprovantes, garantia ou uso seguro de serviços financeiros",
            "instituicoes_financeiras": "uma situação cotidiana sobre onde guardar, movimentar e proteger o dinheiro com segurança",
        }
        situacao = situacoes.get(tipo, f"uma situação financeira real relacionada a {tema}")
        base["para_comecar"] = (
            f"Apresentar {situacao}, sem exigir relatos pessoais nem julgamentos sobre hábitos financeiros familiares. "
            "Convidar os estudantes a levantar hipóteses sobre escolhas, riscos, prioridades e consequências antes da sistematização."
        )
        base["analise_caso"] = (
            f"Conduzir a análise do caso ligado a {tema}, identificando dados importantes, alternativas possíveis, "
            "critérios de decisão e consequências de curto e longo prazo. Registrar no quadro as perguntas que ajudam a decidir com responsabilidade."
        )
        base["foco"] = (
            f"Desenvolver {conceito_seguro} de forma contextualizada, relacionando o conceito a situações reais de consumo, "
            "planejamento, poupança, crédito ou organização de recursos. Explicar o vocabulário financeiro necessário e construir critérios claros para a tomada de decisão."
        )
        base["pause"] = (
            "Promover uma pausa para que a turma compare alternativas, justifique escolhas e avalie impactos financeiros, "
            "retomando dados do material e dúvidas comuns antes de seguir para a aplicação."
        )
        base["calculos"] = (
            "Orientar cálculos financeiros de forma guiada, destacando dados, operações, porcentagens, juros, parcelas, saldo ou custo total conforme o material. "
            "Relacionar cada resultado numérico a uma decisão possível, evitando que a atividade fique apenas mecânica."
        )
        base["planejamento"] = (
            "Orientar a elaboração ou análise de um planejamento financeiro simulado, organizando receita, despesas, prioridades, metas e saldo. "
            "Acompanhar os registros para que os estudantes expliquem os critérios usados nas escolhas."
        )
        base["simulacao"] = (
            "Organizar uma simulação financeira ou análise de alternativas, aplicando os critérios construídos na aula para escolher, comparar, planejar ou revisar uma decisão. "
            "Solicitar registro de cálculos, justificativas e possíveis consequências."
        )
        base["projeto"] = (
            "Orientar a organização de um projeto empreendedor simples, levantando recursos necessários, custos, preço, público, viabilidade e cuidados éticos. "
            "Solicitar que os estudantes justifiquem as decisões tomadas no planejamento."
        )
        base["pratica"] = (
            "Orientar a resolução das atividades do material com registro individual ou em dupla, acompanhando leitura de dados, comparação de alternativas e justificativa das decisões. "
            "Retomar vocabulário financeiro e critérios de escolha sempre que surgirem dúvidas."
        )

        if tipo == "orcamento_planejamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} como estratégia de organização financeira, relacionando receitas, despesas, gastos, prioridades e metas. "
                "Construir com a turma critérios para controlar recursos e ajustar escolhas conforme limites e objetivos."
            )
            base["pratica"] = base["planejamento"]
        elif tipo == "consumo_consciente":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} a partir de critérios de consumo consciente, diferenciando necessidade, desejo, prioridade, custo-benefício e impacto da escolha. "
                "Evitar tom moralista e conduzir a análise com base em argumentos, dados e consequências."
            )
        elif tipo == "investimento_poupanca":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando poupança, reserva, rendimento, constância e planejamento de metas. "
                "Mostrar como a organização dos recursos ajuda a lidar com imprevistos e objetivos de curto ou longo prazo."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "credito_endividamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} com foco no uso responsável do crédito, analisando juros, parcelas, custo total, riscos de endividamento e critérios para decidir. "
                "Comparar alternativas sem estimular consumo, priorizando avaliação crítica e planejamento."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "empreendedorismo":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} articulando oportunidade, necessidade, produto ou serviço, custos, preço, lucro e viabilidade. "
                "Relacionar a proposta a planejamento, responsabilidade e análise do contexto."
            )
            base["pratica"] = base["projeto"]
        elif tipo == "analise_percentuais_noticias":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} por meio da leitura de noticias, manchetes, tabelas e graficos, ajudando a turma a interpretar percentuais, "
                "comparar dados e perceber como os numeros influenciam a compreensao dos fatos."
            )
            base["calculos"] = (
                "Orientar calculos de porcentagem e comparacao de variacoes com apoio do quadro, destacando o significado de cada dado antes do procedimento numerico. "
                "Retomar passo a passo como localizar o valor de referencia, calcular percentuais e interpretar o resultado no contexto da noticia analisada."
            )
            base["pratica"] = (
                "Propor leitura guiada de noticias ou situacoes semelhantes, seguida de registros no caderno com interpretacao dos percentuais, comparacao de informacoes "
                "e justificativa sobre o que os dados revelam."
            )
        elif tipo == "governo_economia":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando arrecadacao, servicos publicos, regulacao e impactos economicos no cotidiano. "
                "Conduzir a turma a perceber como decisoes do governo interferem em precos, circulacao de dinheiro e acesso a direitos."
            )
            base["pratica"] = (
                "Orientar a analise de exemplos concretos, comparando situacoes em que a acao do governo influencia consumo, trabalho, precos ou servicos. "
                "Solicitar registros curtos com explicacao das relacoes observadas."
            )
        elif tipo == "impacto_decisoes_economicas":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} por meio de escolhas economicas do cotidiano, relacionando recursos disponiveis, prioridades, consumo e consequencias de curto e longo prazo. "
                "Estimular a turma a comparar alternativas com base em criterios claros e realistas."
            )
            base["pratica"] = (
                "Propor situacoes-problema simples para que os estudantes comparem escolhas, antecipem impactos e justifiquem decisoes com base nos dados apresentados. "
                "Retomar o vocabulario financeiro necessario sempre que surgirem duvidas."
            )
        elif tipo == "cidadania_financeira":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando direitos do consumidor, responsabilidades, segurança, comprovantes, garantias e autonomia nas decisões financeiras. "
                "Orientar a turma a identificar formas de proteção e uso consciente de serviços financeiros."
            )
        elif tipo == "instituicoes_financeiras":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} explicando a função das instituições financeiras na guarda, movimentação, controle e proteção do dinheiro. "
                "Comparar exemplos como banco, conta digital, poupança e outros serviços, destacando segurança e planejamento."
            )

        base["encerramento"] = (
            f"Sintetizar os aprendizados financeiros relacionados a {tema}, retomando critérios de decisão, organização e responsabilidade. "
            "Propor um fechamento com planejamento de aplicação no cotidiano, sem solicitar exposição de informações financeiras pessoais."
        )

    elif perfil == "matematica":
        # Gerador especializado de Matemática — retorna lista de etapas completas
        etapas_mat = _metodologia_matematica(texto_base, tema, tipo)
        # Converte lista de dicts em dicionário de frases para o motor geral
        for etapa in etapas_mat:
            chave = normalizar_texto(etapa["titulo"]).replace(" ", "_")
            base[chave] = etapa["texto"]
        # Alimenta as chaves canônicas usadas pelos templates de etapas
        for etapa in etapas_mat:
            titulo_norm = normalizar_texto(etapa["titulo"])
            mapa_chaves = {
                "para comecar": "para_comecar",
                "relembre": "para_comecar",
                "abertura": "abertura",
                "pratica na khan academy": "pratica_khan",
                "fechamento": "fechamento_khan",
                "foco no conteudo": "foco",
                "de olho no modelo": "de_olho_modelo",
                "pause e responda": "pause",
                "na pratica": "pratica",
                "encerramento": "encerramento",
            }
            for titulo_key, chave_canon in mapa_chaves.items():
                if titulo_key in titulo_norm:
                    base[chave_canon] = etapa["texto"]
                    break

    elif perfil == "tecnologia_inovacao":
        base["para_comecar"] = (
            f"Ativar os conhecimentos previos da turma sobre {tema}, retomando exemplos do cotidiano escolar e digital que ajudem a dar sentido ao conteudo."
        )
        base["leitura"] = (
            "Realizar leitura guiada dos slides, explicando vocabulario, comandos, funcoes e exemplos de forma pausada, com registro no quadro das ideias principais."
        )
        base["foco"] = (
            f"Explorar {conceito} de forma concreta, relacionando o funcionamento da tecnologia, os usos no cotidiano e as escolhas dos estudantes durante a aula."
        )
        base["pause"] = (
            "Promover perguntas rapidas para verificar a compreensao, retomar respostas da turma e corrigir coletivamente possiveis duvidas antes da atividade principal."
        )
        base["pratica"] = (
            f"Orientar a atividade pratica com {t_reg}, acompanhando leitura dos comandos, organizacao dos registros e execucao passo a passo."
        )
        base["encerramento"] = (
            f"Retomar os aprendizados sobre {tema}, socializar algumas respostas ou producoes da turma e finalizar com uma sintese simples sobre o que foi descoberto na aula."
        )

        if tipo == "dispositivos_entrada_saida":
            base["para_comecar"] = (
                f"Ativar os conhecimentos previos da turma sobre {tema}, convidando os estudantes a observar os equipamentos tecnologicos presentes na escola e a dizer para que servem."
            )
            base["foco"] = (
                "Explorar a diferenca entre dispositivos de entrada e de saida, classificando coletivamente exemplos como teclado, mouse, microfone, camera, monitor, impressora, projetor e caixa de som."
            )
            base["pratica"] = (
                f"Orientar a classificacao dos dispositivos em colunas ou esquemas com {t_reg}, acompanhando as justificativas dos estudantes sobre a funcao de cada equipamento."
            )
        elif tipo == "programacao_inicial":
            base["para_comecar"] = (
                f"Retomar situacoes em que o teclado, o mouse ou botoes de inicio sao usados para dar comandos, conectando o tema {tema} a experiencias proximas da turma."
            )
            base["foco"] = (
                "Explicar o uso do teclado e dos comandos iniciais de programacao no StartLab, destacando teclas importantes, a bandeira verde, blocos de eventos e o bloco diga como formas de criar mensagens interativas."
            )
            base["pratica"] = (
                f"Orientar a montagem de comandos simples no ambiente de programacao com {t_reg}, demonstrando uma etapa no quadro ou projetor e acompanhando a execucao individual ou em dupla."
            )
        elif tipo == "cultura_digital":
            base["para_comecar"] = (
                f"Ativar os conhecimentos previos sobre {tema}, comparando formas antigas e atuais de comunicacao e incentivando a turma a pensar sobre convivencia nos ambientes digitais."
            )
            base["foco"] = (
                "Explorar atitudes respeitosas e inadequadas na internet, relacionando emocoes, convivencia online, responsabilidade e cuidado nas interacoes digitais."
            )
            base["pratica"] = (
                f"Orientar a analise de situacoes do cotidiano digital com {t_reg}, acompanhando a construcao de regras, exemplos e propostas de convivencia respeitosa."
            )
        elif tipo == "comunicacao_digital":
            base["para_comecar"] = (
                f"Apresentar uma situacao de duvida ou mensagem pouco clara relacionada a {tema}, convidando a turma a identificar por que a comunicacao nao funcionou."
            )
            base["foco"] = (
                "Explorar como fazer perguntas claras, objetivas, respeitosas e completas em ambientes digitais, mostrando quais informacoes ajudam a receber respostas mais precisas."
            )
            base["pratica"] = (
                f"Orientar a reescrita de perguntas e mensagens com {t_reg}, usando modelos simples no quadro e acompanhando a organizacao das informacoes pelos estudantes."
            )
        elif tipo == "consumo_tecnologia":
            base["para_comecar"] = (
                f"Apresentar um exemplo do cotidiano relacionado a {tema}, como celular, fone, carregador ou televisao, para provocar a reflexao sobre durabilidade, descarte e consumo."
            )
            base["foco"] = (
                "Explicar o conceito de obsolescencia programada e relaciona-lo ao lixo eletronico, ao consumo excessivo e a necessidade de escolhas mais conscientes no uso da tecnologia."
            )
            base["pratica"] = (
                f"Orientar a producao de listas, cartazes, campanhas ou propostas de solucao com {t_reg}, acompanhando a formulacao de dicas viaveis de consumo consciente e descarte correto."
            )

    elif perfil == "sociologia":
        base["para_comecar"] = (
            f"Apresentar um fenômeno social ligado a {tema} por meio de situação, imagem, dado ou relato, "
            "provocando estranhamento e questionamentos iniciais."
        )
        base["foco"] = (
            f"Analisar {conceito} sociologicamente, articulando teoria, conceitos e exemplos da realidade social "
            "para superar leituras baseadas apenas no senso comum."
        )

    return base


class MotorMetodologico:
    """Motor unificado de geração de metodologia sem IA."""

    def __init__(self):
        self.extrator = _extrator
        self.validador = ValidadorQualidade()
        self.seletor = _seletor_tecnicas

    def gerar(
        self,
        texto_pdf: str,
        disciplina: str,
        turma: str,
        tema: str,
        indice_aula: int = 0,
        total_aulas: int = 1,
    ) -> list[dict]:
        """
        Gera metodologia completa com etapas variáveis por perfil.

        Usa o motor sofisticado (equivalente ao _montar_etapas_metodologia
        do lote.py) em vez do motor fraco do inteligencia_local.py.
        """
        # 1. Classificar
        perfil = perfil_disciplina(disciplina)
        tipo = detectar_tipo_aula(texto_pdf, tema, disciplina)

        # 2. Extrair conceito
        extracao = self.extrator.extrair(texto_pdf, tema)
        conceito = extracao["conceito_extraido"]
        atividade = extracao.get("atividade_extraida", "")
        recursos = extracao.get("recursos_detectados", [])
        etapas_pdf = extracao.get("etapas_detectadas", [])
        habilidade = extracao.get("habilidade", "")

        # 3. Selecionar técnicas com variação
        tecnicas = self.seletor.selecionar_para_aula(perfil, tipo, tema, indice_aula)

        # 4. Gerar frases contextualizadas
        frases = _frases_por_contexto(
            perfil,
            tipo,
            tema,
            conceito,
            turma,
            tecnicas,
            texto_pdf,
            atividade_extraida=atividade,
            recursos_detectados=recursos,
            etapas_detectadas=etapas_pdf,
            habilidade=habilidade,
        )

        # 5. Montar etapas
        etapas_config = _etapas_por_perfil(perfil, tipo)
        metodologia = []
        for titulo, chave in etapas_config:
            texto_etapa = frases.get(chave, "").strip()
            if texto_etapa:
                # Aplicar progressão entre aulas
                texto_etapa = ajustar_texto_por_posicao(
                    texto_etapa, indice_aula, total_aulas, tema
                )
                metodologia.append({"titulo": titulo, "texto": texto_etapa})

        # 6. Validar
        return self.validador.refinar(metodologia)

    def extrair_dados(self, texto_pdf: str, tema: str) -> dict:
        """Expõe a extração de dados para uso por outros módulos."""
        return self.extrator.extrair(texto_pdf, tema)
