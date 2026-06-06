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


def _normalizar_termos_internos(texto: str) -> str:
    texto = str(texto or "")
    correcoes = {
        "evidências": "evidencias",
        "socialização": "socializacao",
    }
    for origem, destino in correcoes.items():
        texto = texto.replace(origem, destino)
        texto = texto.replace(origem.capitalize(), destino[:1].upper() + destino[1:])
    return texto


class ValidadorQualidade:
    """Remove etapas vazias e formata corretamente os blocos de texto."""

    def refinar(self, metodologia: list[dict]) -> list[dict]:
        validada = []
        for etapa in metodologia:
            if etapa.get("texto") and len(etapa["texto"].strip()) > 10:
                texto = naturalizar_texto_metodologico(corrigir_mojibake(etapa["texto"].strip()))
                texto = _normalizar_termos_internos(texto)
                if not texto.endswith('.'):
                    texto += '.'
                etapa["texto"] = texto
                validada.append(etapa)
        return validada


def _etapas_por_perfil(perfil: str, tipo: str) -> list[tuple[str, str]]:
    """Define as etapas metodológicas adequadas ao perfil e tipo de aula."""

    if perfil == "ingles":
        if tipo == "leitura_em":
            return [
                ("Para começar", "para_comecar_virem_e_conversem"),
                ("Vocabulário", "vocabulario_pre_leitura"),
                ("Hora da leitura", "leitura_texto_principal"),
                ("Foco no conteúdo", "foco_conteudo_estrategia"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "questoes_vestibular"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "gramatica":
            return [
                ("Relembre", "relembre_ou_para_comecar"),
                ("Na prática — Vocabulário", "listening_ou_vocabulario"),
                ("Foco no conteúdo", "foco_conteudo_gramatica"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática — Exercícios", "exercicios_estruturados"),
                ("Produção oral", "producao_oral_duplas"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "listening":
            return [
                ("Para começar", "para_comecar_virem_e_conversem"),
                ("Vocabulário", "vocabulario_pre_escuta"),
                ("Na prática", "listening_atividade"),
                ("Foco no conteúdo", "foco_conteudo"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "pratica_adicional"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "producao_oral":
            return [
                ("Relembre", "relembre"),
                ("Vocabulário", "vocabulario_expressoes"),
                ("De olho no modelo", "modelo_dialogo"),
                ("Na prática", "pratica_em_duplas"),
                ("Produção própria", "producao_propria"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "leitura_literaria":
            return [
                ("Para começar", "para_comecar_virem_e_conversem"),
                ("Foco no conteúdo", "foco_conteudo_estrategia_literaria"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "atividades_leitura"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "musica":
            return [
                ("Relembre", "relembre_ou_para_comecar"),
                ("Na prática", "listening_musica"),
                ("De olho no modelo", "analise_letra"),
                ("Foco no conteúdo", "foco_conteudo_gramatica"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "exercicios_pratica"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "revisao":
            return [
                ("Relembre", "relembre_sintese"),
                ("Na prática", "atividades_revisao_multiplas"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        # vocabulario e fallback geral
        return [
            ("Para começar", "para_comecar"),
            ("Vocabulário", "vocabulario"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Encerramento", "encerramento")
        ]

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

    if perfil == "ciencias_ef":
        if tipo == "revisao_retomada":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Exercicio resolvido", "modelo"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "producao_projeto":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Na pratica", "producao"),
                ("Compartilhamento", "compartilhamento"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "leitura_analise":
            return [
                ("Para comecar", "para_comecar"),
                ("Hora da leitura", "leitura"),
                ("Foco no conteudo", "foco"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "estudo_caso":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco"),
                ("Estudo de caso", "estudo_caso"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        return [
            ("Para comecar", "para_comecar"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "biologia":
        if tipo == "aula_desafio":
            return [
                ("Desafio da semana", "desafio"),
                ("Entendendo o problema", "entendendo_problema"),
                ("Solucao em acao", "solucao_acao"),
                ("Hora da verdade", "hora_verdade"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "aula_pratica":
            return [
                ("Relembre", "relembre"),
                ("Na pratica", "pratica"),
                ("Discussao dos resultados", "discussao_resultados"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "revisao_consolidacao":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "impacto_socioambiental":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        return [
            ("Para comecar", "para_comecar"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
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
    """Gerador especializado de frases para o perfil Projeto de Vida.

    Retorna dicionário de frases por chave de etapa (para integração no motor
    geral via _frases_por_contexto). Cobre 6 tipos de aula:
    'autoconhecimento', 'futureme', 'producao_coletiva',
    'convivencia', 'consciencia_social', 'encerramento'.
    """
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
            "ponto_de_partida": (
                f"Iniciar a aula retomando a proposta de {tema} e convidando os estudantes a refletirem sobre o "
                f"que esperam descobrir sobre si mesmos. Conectar a atividade ao projeto bimestral de autoconhecimento "
                f"profissional e abrir para breve troca em duplas: '{questao}'."
            ),
            "construindo_o_conceito": (
                f"Apresentar o conceito de {conceito_seguro} de forma dialogada, esclarecendo que os resultados da "
                f"plataforma são pontos de partida para reflexão — não rótulos definitivos. Reforçar que "
                f"personalidade e habilidades se desenvolvem ao longo da vida."
            ),
            "acesso_plataforma": (
                f"Orientar os estudantes a acessarem a plataforma FutureMe e seguirem o passo a passo para o "
                f"{act_name}, garantindo que todos consigam navegar com autonomia, apoiando individualmente quem "
                f"tiver dificuldade. Após a conclusão, pedir que leiam o relatório com atenção."
            ),
            "compartilhamento": (
                f"Organizar trios para a troca dos resultados: em quais partes do relatório você mais se reconheceu? "
                f"O que não fez sentido? Com base no seu perfil, que tipos de profissões parecem combinar mais com você? "
                f"Alguns trios compartilham com a turma."
            ),
            "encerramento": (
                f"Encerrar com síntese: o relatório é apenas um ponto de partida. O que você pretende investigar "
                f"mais sobre {tema}? Propor registro individual no caderno."
            ),
        }

    if tipo == "producao_coletiva":
        match_prod = re.search(r"(?:biomapa|campanha|mostra|painel|caixa dos vinculos|video|festival do minuto|hq)", texto_norm)
        prod_name = match_prod.group(0).title() if match_prod else "projeto do bimestre"
        return {
            "relembre": (
                f"Retomar o projeto bimestral e o que foi produzido nas aulas anteriores, conectando ao foco "
                f"da aula: {tema}. Verificar onde cada grupo parou e o que precisa avançar."
            ),
            "foco_no_tema": (
                f"Apresentar a proposta de {tema}, esclarecendo o produto esperado — {prod_name} —, os critérios "
                f"de qualidade e os próximos passos. Analisar coletivamente o modelo, identificando os elementos "
                f"que devem estar presentes na produção."
            ),
            "producao_em_grupos": (
                f"Organizar a turma em grupos, distribuir materiais e orientar a produção passo a passo, garantindo "
                f"que todos participem com funções definidas. Circular pela sala apoiando os grupos e incentivando "
                f"o uso dos recursos indicados."
            ),
            "apresentacao": (
                f"Promover o compartilhamento das produções com a turma, valorizando as escolhas de cada grupo. "
                f"Propor avaliação coletiva com base nos critérios combinados."
            ),
            "encerramento": (
                f"Encerrar com registro individual: o que você aprendeu ao produzir {tema} em grupo? Como esse "
                f"processo se conecta à sua trajetória e projeto de vida?"
            ),
        }

    if tipo == "convivencia":
        return {
            "relembre": (
                f"Retomar o Painel de Convivência ou produto anterior, revisitando os acordos coletivos e o que foi "
                f"discutido nas aulas anteriores sobre {tema}."
            ),
            "foco_no_tema": (
                f"Apresentar o dilema ou tema de reflexão coletiva sobre {conceito_seguro}, explicando como as "
                f"decisões de cada um afetam o grupo e ajudando a turma a relacionar sentir, pensar e agir de "
                f"forma respeitosa na convivência escolar."
            ),
            "circulo_ou_votacao": (
                f"Organizar a turma em círculo, definir os papéis (mediador, secretário, guardião do tempo) e conduzir "
                f"o debate sobre {tema} com rodadas de fala respeitosas, levantamento de soluções e avaliação de "
                f"consequências. Registrar a decisão coletiva no Painel de Convivência."
            ),
            "encerramento": (
                f"Encerrar com compromisso individual escrito: o que você pode fazer concretamente para contribuir "
                f"com {tema} no cotidiano da escola e da sua comunidade?"
            ),
        }


    if tipo == "consciencia_social":
        return {
            "para_comecar": (
                f"Iniciar com dinâmica corporal ou leitura de dados que evidenciem diferenças de condições de vida "
                f"relacionadas a {tema}. Conduzir sem julgamento individual, garantindo um ambiente de respeito e "
                f"acolhimento."
            ),
            "foco_no_tema": (
                f"Apresentar dados e reportagens sobre {tema} de forma dialogada, conectando as informações à "
                f"realidade dos estudantes. Convidar à análise crítica sobre privilégios, desvantagens e o papel "
                f"de cada um como agente de transformação."
            ),
            "pratica": (
                f"Propor atividade de análise: mapa do ambiente digital, leitura crítica de mídia, revisão de HQ "
                f"ou registro no livro sobre {tema}. Orientar os estudantes a identificar padrões, questionar "
                f"representações e propor perspectivas mais inclusivas."
            ),
            "encerramento": (
                f"Encerrar com reflexão individual: reconhecer {tema} muda o que você faz? O que você pode começar "
                f"a fazer de diferente a partir de hoje?"
            ),
        }

    if tipo == "encerramento":
        match_prod = re.search(r"(?:caixa dos vinculos|painel de convivencia|mostra|pacto final|video|biomapa)", texto_norm)
        prod_name = match_prod.group(0).title() if match_prod else "projeto do bimestre"
        return {
            "relembre": (
                f"Abrir simbolicamente o projeto bimestral — {prod_name} — revisitando o percurso completo. "
                f"Convidar os estudantes a lembrarem das aulas, das reflexões e das produções realizadas ao longo "
                f"do bimestre."
            ),
            "sintese_do_percurso": (
                f"Propor síntese coletiva: o que aprendemos sobre {tema} neste bimestre? Quais foram os momentos "
                f"mais marcantes? O que mudou na forma de pensar sobre o futuro?"
            ),
            "producao_final": (
                f"Orientar a produção final do projeto bimestral — vídeo, mostra, pacto, post-it com palavras-chave — "
                f"garantindo que cada estudante contribua com sua perspectiva pessoal."
            ),
            "encerramento": (
                f"Reservar tempo para a síntese individual escrita, com perguntas que conectem o aprendizado à vida "
                f"fora da escola: o que você leva deste bimestre? O que pretende fazer de diferente? Encerrar com "
                f"ritual coletivo — depositar palavras na caixa, assinar o painel ou compartilhar com a turma — "
                f"reforçando que esse gesto representa um pacto pessoal e coletivo com os aprendizados do bimestre."
            ),
        }

    # autoconhecimento / default
    if midia_nome:
        ponto_partida_str = (
            f"Iniciar a aula com a escuta/exibição da música ou vídeo '{midia_nome}', convidando os estudantes "
            f"a perceberem as emoções e ideias despertadas, sem exigir exposicao pessoal. Propor que conversem "
            f"em duplas sobre as questões: '{p1}' e '{p2}'."
        )
    else:
        ponto_partida_str = (
            f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. "
            f"Propor que os estudantes reflitam sobre a pergunta: '{questao.rstrip('?')}', "
            f"respeitando diferentes ritmos de participacao."
        )

    return {
        "ponto_de_partida": ponto_partida_str,
        "construindo_o_conceito": (
            f"Apresentar o conceito de {tema} de forma dialogada, convidando os estudantes a relacionarem as "
            f"ideias às suas próprias experiências, valores e percepções. Destacar os pontos centrais do tema "
            f"com perguntas que incentivem a participação."
        ),
        "colocando_em_pratica": (
            f"Orientar a elaboração individual de {atividade}, com instruções passo a passo. Garantir que a "
            f"socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas."
        ),
        "virem_e_conversem": (
            f"Organizar duplas para o compartilhamento das produções: cada estudante apresenta seu registro, "
            f"explica suas escolhas e ouve as percepções do colega sobre {tema}, praticando a escuta ativa."
        ),
        "encerramento": (
            f"Encerrar a aula com síntese pessoal escrita no caderno: o que você descobriu sobre {conceito_seguro}? "
            f"O que esse aprendizado muda na forma como você pensa sobre seu futuro?"
        ),
    }


def _metodologia_projeto_vida(
    texto_base: str,
    tema: str,
    tipo: str,
    conceito: str = "",
    atividade_extraida: str = "",
) -> list[dict]:
    """Adapter de Projeto de Vida em `list[dict]`, com fonte unica de conteudo."""

    tipo_normalizado = tipo or "autoconhecimento"
    frases = _metodologia_projeto_de_vida(
        texto_base=texto_base,
        tema=tema,
        tipo=tipo_normalizado,
        conceito=conceito,
        atividade_extraida=atividade_extraida,
    )
    if not frases:
        return []

    etapas = []
    for titulo, chave in _etapas_por_perfil("projeto_de_vida", tipo_normalizado):
        texto = frases.get(chave)
        if texto:
            etapas.append({"titulo": titulo, "texto": texto})
    return etapas


def _metodologia_ingles(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "") -> dict[str, str] | None:
    import re
    texto_norm = normalizar_texto(texto_base)

    # Extrair perguntas se houver
    perguntas = re.findall(r"([^?\n]{15,100}\?)", texto_base)
    pergunta_str = f" \"{perguntas[0].strip()}\"" if perguntas else ""

    atividade = atividade_extraida or "as atividades propostas"

    if tipo == "leitura_em":
        return {
            "para_comecar_virem_e_conversem": (
                f"Iniciar a aula com a técnica Virem e conversem, propondo perguntas sobre {tema} para ativar o conhecimento "
                f"prévio dos estudantes:{pergunta_str if pergunta_str else ' como o tema se relaciona com o cotidiano deles?'} "
                f"Socializar as respostas com a turma antes de avançar para o texto principal."
            ),
            "vocabulario_pre_leitura": (
                f"Apresentar o vocabulário temático da aula com apoio visual e prática de pronúncia (listen and repeat), "
                f"incentivando os estudantes a registrarem as novas palavras no caderno. Destacar palavras cognatas e falsos amigos."
            ),
            "leitura_texto_principal": (
                f"Conduzir a leitura orientada do texto da aula sobre {tema}, explorando cognatas, palavras-chave e estratégias "
                f"de inferência pelo contexto. Atividade central: {atividade}."
            ),
            "foco_conteudo_estrategia": (
                f"Apresentar e praticar as estratégias de leitura para o tipo de texto da aula: identificação de cognatas, "
                f"busca por palavras-chave, inferência pelo contexto e análise das imagens para consolidar a compreensão."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de verificação da aprendizagem com a questão de múltipla escolha do material, "
                f"solicitando que os estudantes respondam individualmente e justifiquem sua escolha antes da correção coletiva."
            ),
            "questoes_vestibular": (
                f"Propor a resolução de questão de vestibular (ENEM/SARESP/UNESP) presente no material sobre {tema}, "
                f"orientando os estudantes a aplicar as estratégias de leitura estudadas (eliminação de alternativas e busca de evidências)."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar a aula com a técnica Com suas palavras, solicitando que os estudantes respondam em inglês "
                f"às perguntas de síntese do material. Registrar os pontos que precisarão ser retomados."
            )
        }

    if tipo == "gramatica":
        conteudo_gramatica = conceito or tema
        return {
            "relembre_ou_para_comecar": (
                f"Retomar com a turma os principais conceitos ou vocabulário trabalhados na aula anterior relacionados a {tema}, "
                f"com exemplos e síntese visual no quadro."
            ),
            "listening_ou_vocabulario": (
                f"Conduzir a escuta do áudio de introdução ou apresentar o vocabulário inicial de {tema}, "
                f"praticando a pronúncia das palavras novas com a técnica listen and repeat."
            ),
            "foco_conteudo_gramatica": (
                f"Retomar os exemplos do texto/áudio e identificar com a turma a estrutura gramatical de {conteudo_gramatica}. "
                f"Apresentar a regra de forma clara e contextualizada, com exemplos retirados do material."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de verificação com a questão do material, solicitando que os estudantes decidam "
                f"e justifiquem a resposta antes da correção coletiva."
            ),
            "exercicios_estruturados": (
                f"Conduzir as atividades de fixação (fill in the blanks, matching ou reorganização de frases) no caderno, "
                f"orientando o uso do material de apoio. Atividade: {atividade}."
            ),
            "producao_oral_duplas": (
                f"Organizar os estudantes em duplas para a prática oral utilizando o modelo de diálogo e o banco de palavras "
                f"do material (técnica In pairs), estimulando a troca de papéis."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar a aula com a técnica Com suas palavras, solicitando que os estudantes produzam uma frase curta "
                f"em inglês usando a estrutura gramatical trabalhada ({conteudo_gramatica})."
            )
        }

    if tipo == "listening":
        return {
            "para_comecar_virem_e_conversem": (
                f"Iniciar com a técnica Virem e conversem para que os estudantes compartilhem o que já sabem sobre o tema {tema}, "
                f"levantando hipóteses a partir de imagens."
            ),
            "vocabulario_pre_escuta": (
                f"Apresentar as palavras-chave do áudio de {tema} com foco na pronúncia e no significado, preparando a turma "
                f"para a escuta atenta."
            ),
            "listening_atividade": (
                f"Conduzir a escuta atenta do áudio (técnica Listen to the audio), orientando os estudantes a identificar informações "
                f"específicas da atividade: {atividade}. Garantir script para estudantes surdos."
            ),
            "foco_conteudo": (
                f"Explicar as estruturas gramaticais e expressões centrais identificadas na conversa gravada, conectando ao uso prático."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de checagem de compreensão com questão rápida do material antes de avançar para as demais atividades."
            ),
            "pratica_adicional": (
                f"Propor atividade prática baseada no áudio (exercício de true/false ou preenchimento de tabela), em duplas ou individualmente."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar solicitando que os estudantes citem pelo menos duas informações-chave ouvidas no áudio, utilizando o inglês "
                f"para sintetizar."
            )
        }

    if tipo == "producao_oral":
        return {
            "relembre": (
                f"Relembrar expressões e vocabulário úteis para situações cotidianas semelhantes a {tema}, "
                f"praticando brevemente a pronúncia com a classe."
            ),
            "vocabulario_expressoes": (
                f"Apresentar as expressões idiomáticas ou alterações de conversação do material úteis para a interação oral sobre {tema}."
            ),
            "modelo_dialogo": (
                f"Apresentar o modelo de diálogo do material e conduzir a leitura em voz alta com toda a classe (listen and repeat) "
                f"para fixar entonação e pronúncia."
            ),
            "pratica_em_duplas": (
                f"Organizar a prática oral do diálogo em duplas (In pairs), orientando que troquem de papéis e variem as informações "
                f"do diálogo conforme as opções do material."
            ),
            "producao_propria": (
                f"Propor que as duplas criem e encenem sua própria versão do diálogo ou realizem a produção oral solicitada: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Pedir que algumas duplas voluntárias encenem o diálogo para a classe. Valorizar a comunicação e o esforço de fala em inglês."
            )
        }

    if tipo == "leitura_literaria":
        return {
            "para_comecar_virem_e_conversem": (
                f"Iniciar a aula ativando o conhecimento dos alunos sobre o autor ou gênero literário do trecho a ser lido em {tema}, "
                f"propondo hipóteses com base em ilustrações ou títulos."
            ),
            "foco_conteudo_estrategia_literaria": (
                f"Apresentar estratégias de leitura literária: identificação de personagens, cenários, adjetivos de descrição "
                f"física ou psicológica, e análise do tom positivo ou negativo do autor."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de verificação sobre o fragmento literário lido, pedindo que os estudantes justifiquem "
                f"a resposta correta."
            ),
            "atividades_leitura": (
                f"Orientar a análise detalhada do trecho literário proposto, localizando adjetivos e descrições cruciais. "
                f"Atividade principal: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar pedindo que os estudantes resumam o conflito do personagem ou a ideia principal do trecho literário "
                f"com suas palavras em inglês."
            )
        }

    if tipo == "musica":
        return {
            "relembre_ou_para_comecar": (
                f"Iniciar a aula conectando com o artista ou tema da canção de hoje relacionada a {tema}, "
                f"despertando o interesse e a familiaridade dos estudantes com a música."
            ),
            "listening_musica": (
                f"Conduzir a escuta de um fragmento ou da música completa (usando lyric video no YouTube), incentivando "
                f"a turma a acompanhar a letra e cantar junto."
            ),
            "analise_letra": (
                f"Conduzir a leitura e análise de trechos da letra da música, identificando o tema central e os novos "
                f"vocabulários no contexto lírico."
            ),
            "foco_conteudo_gramatica": (
                f"Destacar a estrutura gramatical de {conceito or tema} presente nos versos da canção, analisando a regra a partir do uso real."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa formativa para discutir o significado de versos específicos da música ou sobre a estrutura gramatical estudada."
            ),
            "exercicios_pratica": (
                f"Propor exercícios práticos como matching de versos, completar lacunas da letra da música (fill in the blanks) "
                f"ou ordenação de estrofes. Atividade: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar pedindo aos alunos para expressarem sua opinião sobre a música usando uma frase simples em inglês "
                f"(ex: 'I like this song because...')."
            )
        }

    if tipo == "revisao":
        return {
            "relembre_sintese": (
                f"Iniciar a aula revisando os principais pontos lexicais e gramaticais trabalhados nas últimas aulas relacionados a {tema}, "
                f"usando esquemas resumidos no quadro."
            ),
            "atividades_revisao_multiplas": (
                f"Conduzir a resolução das atividades de revisão e consolidação do bloco (exercícios práticos e simulados). Atividade: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Pedir que os estudantes citem pelo menos 3 coisas (regras, palavras ou frases) que aprenderam a fazer em inglês neste bloco."
            )
        }

    # Fallback / Vocabulário
    return {
        "para_comecar": (
            f"Iniciar a aula ativando os conhecimentos prévios sobre o vocabulário de {tema}. Propor discussão rápida em duplas."
        ),
        "vocabulario": (
            f"Apresentar o vocabulário de {tema} com apoio de imagens e prática de pronúncia usando a técnica listen and repeat."
        ),
        "foco": (
            f"Formalizar o vocabulário e as expressões do material no quadro, explicando classe gramatical e usos."
        ),
        "pause": (
            f"Realizar uma pausa para checagem rápida de vocabulário com perguntas direcionadas aos estudantes."
        ),
        "pratica": (
            f"Conduzir a atividade prática com o banco de palavras e exercícios do material. Atividade: {atividade}."
        ),
        "encerramento": (
            f"Encerrar pedindo aos estudantes que usem 3 palavras novas da aula de hoje em inglês em frases curtas no caderno."
        )
    }



def _metodologia_ciencias(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "") -> dict[str, str] | None:
    """Gerador especializado de frases para Ciencias EF."""
    base = normalizar_texto(" ".join([tema, texto_base, atividade_extraida]))
    conceito_seguro = conceito if normalizar_texto(conceito) not in {"ciencias", "ciencia", "geral"} else tema
    atividade = atividade_extraida or "as atividades propostas no material"

    contexto = "uma situacao concreta do cotidiano, imagem, noticia ou dado apresentado no material"
    if any(k in base for k in ["inpe", "ibge", "detran", "fapesp", "jornal da usp", "g1", "cnn", "onu", "anvisa", "fiocruz"]):
        contexto = "o dado ou a fonte real apresentada no material"
    elif any(k in base for k in ["sao paulo", "cantareira", "aricanduva", "praca da se", "goiania", "brasil"]):
        contexto = "o exemplo local ou brasileiro apresentado no material"

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
            f"Iniciar a aula com {contexto} sobre {tema}, propondo que os estudantes discutam em duplas o que ja sabem e quais hipoteses conseguem levantar."
        ),
        "foco": (
            f"Apresentar o conceito de {conceito_seguro}, partindo dos exemplos do material e construindo progressivamente a definicao cientifica com esquemas, imagens ou comparacoes."
        ),
        "pause": (
            "Propor questao objetiva, verdadeiro/falso ou pergunta curta para verificar a compreensao do conceito antes da atividade pratica, com correcao dialogada."
        ),
        "pratica": (
            f"Orientar atividade escrita de aplicacao, garantindo que todos registrem respostas e justificativas com base no conceito estudado. Atividade central: {atividade}."
        ),
        "encerramento": (
            f"Encerrar com Com suas palavras, solicitando que os estudantes sintetizem o que aprenderam sobre {tema} e retomem as hipoteses iniciais."
        ),
    }


def _metodologia_biologia(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "", habilidade: str = "") -> dict[str, str] | None:
    """Gerador especializado de frases para Biologia."""
    base = normalizar_texto(" ".join([tema, texto_base, atividade_extraida, habilidade]))
    conceito_seguro = conceito if normalizar_texto(conceito) not in {"biologia", "geral", ""} else tema
    atividade = atividade_extraida or "as atividades propostas no material"

    contexto = "uma imagem, noticia, dado ou situacao concreta apresentada no material"
    if any(k in base for k in ["reportagem", "noticia", "amazonia", "inpe", "ods", "matriz energetica", "saude publica", "desmatamento"]):
        contexto = "um dado real, noticia ou problema socioambiental apresentado no material"
    elif any(k in base for k in ["grafico", "infografico", "esquema", "de olho no modelo"]):
        contexto = "o modelo visual cientifico apresentado no material"

    if tipo == "aula_desafio":
        return {
            "desafio": (
                f"Apresentar o caso real relacionado a {tema}, destacando os dados mais impactantes e convidando a turma a levantar hipoteses iniciais sem corrigi-las neste momento."
            ),
            "entendendo_problema": (
                f"Conduzir a analise das evidencias em etapas, revelando gradualmente as informacoes do caso e explicando {conceito_seguro} com apoio do raciocinio cientifico, sempre um passo de cada vez."
            ),
            "solucao_acao": (
                f"Organizar duplas ou grupos para elaborar hipoteses, comparar explicacoes e propor respostas fundamentadas para o caso, usando como base {atividade}."
            ),
            "hora_verdade": (
                "Retomar as hipoteses construidas pelos grupos, apresentar as respostas esperadas e discutir por que algumas explicacoes se aproximam mais das evidencias do que outras."
            ),
            "encerramento": (
                f"Encerrar com Com suas palavras, pedindo que os estudantes expliquem o que o caso ajudou a compreender sobre {tema} e quais medidas ou conclusoes cientificas podem ser defendidas."
            ),
        }

    if tipo == "aula_pratica":
        return {
            "relembre": (
                f"Retomar com a turma os conceitos necessarios para observar o fenomeno relacionado a {tema}, recuperando equacoes, etapas ou ideias-chave antes da pratica."
            ),
            "pratica": (
                f"Apresentar os materiais e orientar a montagem da atividade experimental em etapas curtas, pedindo que os estudantes observem, registrem e relacionem o que ocorre com {conceito_seguro}. Atividade central: {atividade}."
            ),
            "discussao_resultados": (
                "Conduzir a discussao dos resultados com Todo mundo escreve, comparando observacoes, confirmando ou revendo hipoteses e explicitando as evidencias mais importantes."
            ),
            "encerramento": (
                f"Finalizar solicitando que os estudantes expliquem, com suas palavras, o que foi observado e como a pratica ajudou a compreender {tema}."
            ),
        }

    if tipo == "revisao_consolidacao":
        return {
            "relembre": (
                f"Retomar termos e conceitos ja estudados sobre {tema}, pedindo que a turma explique com suas palavras o que lembra antes da correcao formal."
            ),
            "foco": (
                f"Conduzir a revisao por meio de quiz, comparacoes e retomada dos conceitos centrais de {conceito_seguro}, esclarecendo diferencas, relacoes e exemplos."
            ),
            "pratica": (
                f"Orientar leitura, classificacao ou resolucao das questoes de consolidacao, solicitando que os estudantes voltem ao material para localizar evidencias e justificar respostas. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar com perguntas comparativas e Com suas palavras, consolidando o que foi retomado sobre {tema} e identificando duvidas que ainda precisam de reforco."
            ),
        }

    if tipo == "impacto_socioambiental":
        return {
            "para_comecar": (
                f"Iniciar a aula apresentando {contexto} sobre {tema}, propondo uma pergunta disparadora que ajude a turma a relacionar fenomenos biologicos, sociedade e ambiente."
            ),
            "foco": (
                f"Explicar {conceito_seguro} de forma progressiva, relacionando o conteudo a impactos ambientais, saude publica, sustentabilidade ou responsabilidade coletiva, sempre um passo de cada vez."
            ),
            "de_olho_modelo": (
                "Apresentar o grafico, infografico, mapa ou esquema do material e orientar a leitura, pedindo que os estudantes identifiquem dados-chave, comparacoes e implicacoes do modelo visual."
            ),
            "pratica": (
                f"Propor atividade de analise de caso, texto ou dados, solicitando registro individual com base em evidencias e conexoes entre ciencia, ambiente e vida cotidiana. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar retomando a conexao entre {tema} e suas implicacoes sociais, ambientais ou de saude, com perguntas de sintese em Com suas palavras."
            ),
        }

    return {
        "para_comecar": (
            f"Iniciar a aula com {contexto} relacionado a {tema}, convidando os estudantes a levantar hipoteses e ativar conhecimentos previos antes da definicao formal."
        ),
        "foco": (
            f"Explicar {conceito_seguro} em etapas sequenciais, destacando processo, relacoes de causa e consequencia e exemplos biologicos que ajudem a turma a compreender o conteudo um passo de cada vez."
        ),
        "pause": (
            "Propor um Pause e responda antes da atividade pratica, com tempo breve para resposta individual e correcao dialogada baseada nas evidencias e no conceito central."
        ),
        "pratica": (
            f"Orientar a aplicacao do conceito em leitura, classificacao, interpretacao de modelo ou atividade investigativa, pedindo registro individual e justificativa cientifica. Atividade central: {atividade}."
        ),
        "encerramento": (
            f"Finalizar com Com suas palavras, pedindo que os estudantes sintetizem o que aprenderam sobre {tema} e como esse conhecimento se conecta a situacoes reais."
        ),
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
    if perfil == "ingles":
        _frases_ingles = _metodologia_ingles(texto_base, tema, tipo, conceito, atividade_extraida)
        if _frases_ingles is not None:
            base.update(_frases_ingles)
            return base

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
        frases_orientacao = montar_frases_orientacao_estudos(tema, texto_base)
        base.update(frases_orientacao)
        if not frases_orientacao.get("_e_especifico", False):
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

    elif perfil == "ciencias_ef":
            _frases_ciencias = _metodologia_ciencias(texto_base, tema, tipo, conceito, atividade_extraida)
            if _frases_ciencias is not None:
                base.update(_frases_ciencias)
                return base

    elif perfil == "biologia":
            _frases_biologia = _metodologia_biologia(texto_base, tema, tipo, conceito, atividade_extraida, habilidade)
            if _frases_biologia is not None:
                base.update(_frases_biologia)
                return base

    elif perfil in {"quimica", "fisica"}:
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
