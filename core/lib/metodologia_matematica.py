from core.lib.classificador import normalizar_texto

def _metodologia_matematica(texto_base: str, tema: str, tipo: str, turma: str = "", tecnicas: dict = None) -> list[dict]:
    """Gerador especializado de etapas para o perfil Matemática.

    Retorna lista de dicts {titulo, text} diferenciada por tipo de aula:
    'conceito_novo', 'verificacao', 'khan', 'modelagem', 'grafico',
    'resolucao_problemas', 'tecnologia'.

    Chame este gerador a partir de _frases_por_contexto quando perfil=='matematica'.
    A lista retornada sobrepõe o dicionário base de frases usado pelo motor geral.
    """
    # 0. Normalização e Detecção dos perfis matemáticos (regras 1 a 12)
    tema_lower = (tema or "").lower()
    texto_lower = (texto_base or "").lower()
    combinado = tema_lower + " " + texto_lower

    # Regra 01: Estatística ou Porcentagem
    is_stat = any(p in combinado for p in ["estatistica", "porcentagem", "porcent", "media", "ponderada", "amplitude", "variancia", "desvio"])
    # Regra 02: Álgebra ou Equações
    is_algebra = any(p in combinado for p in ["algebra", "equacao", "equacoes", "sistema", "incognita", "variavel", "adicao", "substituicao"])
    # Regra 03: Geometria ou Medidas
    is_geometry = any(p in combinado for p in ["geometria", "medida", "volume", "prisma", "cilindro", "triangulo", "pitagoras", "retangulo", "aresta", "face", "raio", "circulo", "area", "figuras planas"])
    # Regra 04: Funções e Gráficos
    is_functions = any(p in combinado for p in ["funcao", "funcoes", "grafico", "parabola", "concavidade", "vertice", "raizes", "exponencial", "logarit"])
    # Regra 05: Probabilidade ou Análise Combinatória
    is_prob = any(
        p in combinado
        for p in [
            "probabilidade", "combinatoria", "arranjo", "combinacao", "permutacao",
            "fatorial", "contagem", "multiplicativo", "possibilidades",
            "arvore de possibilidades", "principio aditivo", "principio multiplicativo",
            "espaco amostral", "evento favoravel", "diagrama de arvore",
            "principios de contagem",
        ]
    )
    # Regra 06: Khan Academy
    is_khan = tipo == "khan" or "khan" in combinado
    # Regra 07: Novo / Regra 08: Revisão
    is_new_topic = tipo == "conceito_novo" or any(p in combinado for p in ["introducao", "conceito de", "definicao", "propriedade", "parte 1"])
    is_revision = tipo in {"revisao", "verificacao"} or any(
        p in combinado for p in ["revisao", "retomada", "consolidar", "trilha", "parte 2", "parte 3", "parte 4"]
    )

    # Regra 11: Ensino Fundamental / Regra 12: Ensino Médio
    turma_lower = (turma or "").lower()
    is_ef = any(f"{i}" in turma_lower for i in [6, 7, 8, 9]) or "fundamental" in turma_lower
    is_em = any(f"{i}" in turma_lower for i in [1, 2, 3]) or "medio" in turma_lower or "médio" in turma_lower or "em" in turma_lower
    if not is_ef and not is_em:
        is_em = True # default to EM

    # Recupera técnicas lemov ou usa fallback
    tecnicas = tecnicas or {}
    t_disc = tecnicas.get("abertura", "Virem e conversem")
    t_reg = tecnicas.get("registro", "Todo mundo escreve")
    t_sint = tecnicas.get("sintese", "Com suas palavras")
    t_verif = tecnicas.get("verificacao", "Pause e responda")

    # Constantes das etapas
    # Para começar
    if is_stat:
        para_comecar_txt = f"Iniciar a aula com a leitura estruturada de um gráfico ou tabela real sobre {tema}, orientando os estudantes a identificarem de forma clara e explícita o título, os eixos, a fonte dos dados e o período de coleta antes de realizar qualquer cálculo."
    elif is_algebra:
        para_comecar_txt = f"Iniciar a aula apresentando uma situação-problema sobre {tema} narrada inteiramente em linguagem cotidiana e sem a utilização de símbolos matemáticos, estimulando a intuição inicial dos estudantes."
    else:
        para_comecar_txt = f"Iniciar a aula apresentando uma situação contextualizada ou pergunta disparadora sobre {tema} para aproximar o conceito da realidade da turma."

    if is_new_topic:
        para_comecar_txt += " Propor uma pergunta de sondagem de conhecimentos prévios para levantar as hipóteses iniciais dos estudantes."
    elif is_revision:
        # Aula de continuidade: substituir o texto base por retomada direta com "aula anterior" e "conversa em duplas"
        para_comecar_txt = (
            f"Retomar brevemente o conteúdo da aula anterior sobre {tema}, "
            "propondo conversa em duplas para que os estudantes compartilhem o que lembram."
        )

    if is_algebra:
        para_comecar_txt += f" Solicitar um registro inicial individual por meio da técnica {t_reg}, para que cada estudante anote a hipótese de resolução antes da socialização."

    para_comecar_txt += f" Utilizar a técnica {t_disc} para socializar as ideias iniciais antes da formalização."

    if is_ef:
        para_comecar_txt += " Adote uma linguagem simples e situações familiares do universo juvenil."
    elif is_em:
        para_comecar_txt += " Conectar brevemente o tema a conceitos do Ensino Fundamental que servem de base para a aula."

    # Foco no conteúdo
    if is_khan:
        foco_txt = f"Contextualizar brevemente o conteúdo de {tema} na lousa por 5 a 7 minutos com um exemplo rápido, apresentando a trilha da aula. Em seguida, orientar os estudantes sobre o login e a navegação na plataforma Khan Academy."
    elif is_algebra:
        foco_txt = f"Desenvolver o conceito de {tema} no quadro de forma progressiva e dialogada, modelando explicitamente o processo de tradução da linguagem natural para a linguagem algébrica, convertendo cada sentença do problema em expressões matemáticas equivalentes."
    else:
        foco_txt = f"Sistematizar o conceito de {tema} de forma progressiva, conectando a explicação e propriedades aos exemplos práticos."

    if is_functions:
        foco_txt += " Conduzir de forma organizada a construção de uma tabela de valores numéricos na lousa antes de traçar o esboço do gráfico correspondente no plano cartesiano."

    # Regra 09: Múltiplas representações
    if is_functions or is_stat or any(p in combinado for p in ["representacao", "representacoes", "tabela", "grafico"]):
        foco_txt += " Demonstrar de forma explícita a transição entre múltiplas representações (tabular, algébrica e gráfica), verbalizando o que muda e o que permanece igual em cada caso."

    if is_em:
        foco_txt += f" Apresentar a formalização matemática precisa de {tema}, contendo sua definição correta, notações formais e propriedades fundamentais."

    foco_txt += f" Conduzir a explanação utilizando a técnica Um passo de cada vez para estruturar o raciocínio em etapas claras."

    # De olho no modelo
    if is_geometry:
        modelo_txt = f"Apresentar um problema-modelo sobre {tema} resolvido de forma detalhada na lousa. Desenhar de forma cuidadosa e organizada a figura geométrica correspondente antes de iniciar qualquer cálculo, identificando e nomeando elementos como base, altura, raio, arestas ou ângulos retos."
    elif is_prob:
        modelo_txt = f"Apresentar um exemplo-modelo comentado na lousa sobre {tema}, construindo de forma visual um diagrama de árvore ou uma tabela de possibilidades para tornar o processo de contagem e a organização do espaço amostral visualmente explícitos antes de aplicar qualquer fórmula."
    else:
        modelo_txt = f"Apresentar um problema-modelo sobre {tema} resolvido de forma detalhada na lousa como referência orientadora."

    if is_new_topic:
        modelo_txt += " Apresentar o exemplo mais simples possível do tópico, sem variações complexas ou casos especiais, para fixar as bases conceituais."
    
    if is_ef:
        modelo_txt += " Demonstrar as operações e os cálculos passo a passo de forma exclusivamente manual, reforçando a importância de não usar a calculadora nesta etapa."

    modelo_txt += " Utilizar a técnica De olho no modelo para explicitar o raciocínio clínico completo (leitura, dados, estratégia, execução e verificação)."

    # Pause e responda
    pause_txt = f"Realizar uma parada estratégica curta propondo uma pergunta objetiva de checagem formativa sobre {tema} para verificar a compreensão em tempo real."
    # Regra 10: Retomada se > 40% de insegurança
    pause_txt += " Caso mais de 40% da turma demonstre insegurança ou dúvidas, pausar o avanço e propor a retomada imediata com um segundo exemplo focado no ponto de maior dificuldade."

    # Na prática
    if is_khan:
        pratica_txt = f"Orientar os estudantes a realizarem as atividades de {tema} na plataforma Khan Academy. O professor deve realizar circulação ativa de forma sistemática pela sala, observando as telas, mapeando erros comuns e apoiando prioritariamente os estudantes que estão travados."
    else:
        pratica_txt = f"Propor que os estudantes resolvam os exercícios de {tema} no caderno, aplicando o procedimento estudado."

    if is_functions:
        pratica_txt += " Garantir que a atividade prática inclua pelo menos uma questão de interpretação crítica de gráfico além dos cálculos numéricos."

    if is_revision:
        pratica_txt += " Organizar a prática de forma progressiva, partindo dos exercícios mais simples de fixação até desafios de maior complexidade."

    if is_ef:
        pratica_txt += " Orientar a resolução manual e minuciosa dos cálculos passo a passo, evitando o uso de calculadora."

    pratica_txt += f" Utilizar a técnica {t_reg} para que os estudantes registrem individualmente o raciocínio antes de qualquer comparação."

    # Encerramento
    if is_khan:
        encerramento_txt = f"Finalizar a aula projetando os relatórios de progresso da plataforma Khan Academy, destacando os pontos de avanço da turma e identificando as principais dificuldades para orientar os próximos planejamentos."
    else:
        encerramento_txt = f"Conduzir a síntese coletiva dos aprendizados sobre {tema}, organizando o resumo das ideias no quadro."

    encerramento_txt += f" Aplicar a técnica {t_sint}, solicitando que os estudantes expliquem com suas palavras o conceito ou procedimento estudado na aula antes do fechamento final."

    # 1. Ajustes por tipos de aula
    if tipo == "khan":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "verificacao":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "modelagem":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "grafico":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "resolucao_problemas":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Pause e responda", "texto": pause_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "tecnologia" or tipo == "tecnologia_matematica":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    # default: conceito_novo / matematica_padrao
    return [
        {"titulo": "Para começar", "texto": para_comecar_txt},
        {"titulo": "Foco no conteúdo", "texto": foco_txt},
        {"titulo": "De olho no modelo", "texto": modelo_txt},
        {"titulo": "Pause e responda", "texto": pause_txt},
        {"titulo": "Na prática", "texto": pratica_txt},
        {"titulo": "Encerramento", "texto": encerramento_txt},
    ]

