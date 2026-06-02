"""
Gerador de estratégias de acessibilidade por tipo de recurso.

Em vez de gerar frases genéricas por disciplina, analisa o tipo de
atividade/recurso presente no conteúdo e seleciona estratégias
específicas de um catálogo organizado.
"""

import re
from core.lib.classificador import normalizar_texto, contem_termos, detectar_recursos
from core.lib.progressao import _indice_hash
from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural


# ── Catálogo de estratégias por tipo de recurso/atividade ──────────────────

CATALOGO_ESTRATEGIAS = {
    "leitura_texto": [
        "Realizar leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar a organização das respostas.",
        "Permitir leitura em dupla com estudante-tutor para apoiar ritmos diferentes de compreensão.",
        "Destacar palavras-chave e trechos centrais no quadro ou projetor antes da leitura individual.",
        "Oferecer perguntas orientadoras por escrito para guiar a leitura e a localização de informações.",
    ],
    "analise_imagem": [
        "Descrever oralmente os elementos da imagem, destacando informações centrais para estudantes com dificuldade de leitura visual.",
        "Ampliar imagens no quadro ou projetor, apontando elementos que devem ser observados.",
        "Oferecer roteiro escrito de observação da imagem com perguntas orientadoras.",
        "Permitir registro por desenho, esquema ou anotação oral das observações.",
    ],
    "analise_grafico": [
        "Ler coletivamente os eixos, legendas e títulos do gráfico ou tabela antes da análise individual.",
        "Disponibilizar versão simplificada ou ampliada dos dados para apoiar a leitura.",
        "Organizar as informações em lista ou tópicos no quadro para facilitar a comparação.",
        "Oferecer questões de leitura guiada para orientar a interpretação dos dados.",
    ],
    "calculo_resolucao": [
        "Disponibilizar resolução comentada e exemplos graduados para favorecer a compreensão dos procedimentos.",
        "Organizar a atividade em etapas curtas com retomadas coletivas e comparação de estratégias.",
        "Oferecer mediação individual durante os registros, permitindo diferentes formas de resolução e conferência.",
        "Disponibilizar material de apoio (tabuada, fórmulas, calculadora) conforme a necessidade.",
        "Apresentar exemplos resolvidos como referência antes da resolução autônoma.",
    ],
    "producao_textual": [
        "Disponibilizar banco de palavras, expressões e modelos de início de parágrafo para apoiar a escrita.",
        "Permitir produção oral com transcrição assistida ou registro por tópicos.",
        "Oferecer checklist de revisão com critérios visuais claros e linguagem acessível.",
        "Organizar a produção em etapas (planejamento, rascunho, revisão) com mediação em cada fase.",
    ],
    "experimentacao": [
        "Garantir acessibilidade física dos materiais e instrumentos para todos os estudantes.",
        "Descrever etapas do experimento em cartões visuais sequenciais com imagens de apoio.",
        "Oferecer registro por desenho, esquema ou explicação oral para estudantes com dificuldade de escrita.",
        "Organizar grupos cooperativos com funções definidas para favorecer a participação de todos.",
    ],
    "debate_oral": [
        "Oferecer perguntas orientadoras por escrito antes da participação oral.",
        "Permitir participação por registro escrito ou sinalização para quem tem dificuldade de fala.",
        "Organizar turnos de fala com mediação para garantir escuta e respeito a todos os participantes.",
        "Disponibilizar tempo para preparação individual antes de socializar posições.",
    ],
    "escuta_audio": [
        "Disponibilizar transcrição ou resumo escrito do conteúdo de áudio ou vídeo.",
        "Permitir repetição do áudio e pausas para anotação e verificação da compreensão.",
        "Oferecer perguntas orientadoras antes da escuta para direcionar a atenção.",
        "Organizar discussão em duplas após a escuta para trocar percepções e complementar informações.",
    ],
}

# ── Estratégias genéricas por perfil (fallback) ────────────────────────────

_FALLBACK_POR_PERFIL = {
    "matematica": [
        "Disponibilizar resolução comentada e exemplos graduados para favorecer a compreensão dos procedimentos e das relações matemáticas envolvidas.",
        "Organizar a atividade em etapas curtas com retomadas coletivas, comparando estratégias e destacando dados, operações e representações essenciais.",
        "Oferecer mediação individual durante os registros e cálculos, permitindo diferentes formas de resolução, conferência e explicação das respostas.",
    ],
    "lingua_portuguesa_ef": [
        "Oferecer leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema, banco de ideias ou critérios de análise e produção para apoiar a organização das respostas e textos.",
        "Realizar mediações individuais, retomadas coletivas e flexibilização do registro conforme as necessidades observadas na turma.",
    ],
    "lingua_portuguesa_em": [
        "Oferecer leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema, banco de ideias ou critérios de análise e produção para apoiar a organização das respostas e textos.",
        "Realizar mediações individuais, retomadas coletivas e flexibilização do registro conforme as necessidades observadas na turma.",
    ],
    "leitura_redacao": [
        "Oferecer leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema, banco de ideias ou critérios de análise e produção para apoiar a organização das respostas e textos.",
        "Realizar mediações individuais, retomadas coletivas e flexibilização do registro conforme as necessidades observadas na turma.",
    ],
    "orientacao_estudos": [
        "Modelar estratégias de estudo com exemplos concretos, registros guiados e demonstração de como organizar tempo, materiais e etapas da tarefa.",
        "Retomar os procedimentos com linguagem clara, perguntas orientadoras e apoio visual para favorecer a compreensão do que fazer em cada momento.",
        "Oferecer acompanhamento individualizado e diferentes formas de registro para apoiar estudantes com dificuldades de organização e monitoramento da aprendizagem.",
    ],
    "ciencias_ef": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "biologia": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "quimica": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "fisica": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "historia": [
        "Utilizar fontes, imagens, mapas, linhas do tempo e esquemas para apoiar a compreensão dos processos históricos e do vocabulário específico.",
        "Retomar relações de tempo, causa, consequência, permanência e mudança com registros guiados e sínteses no quadro.",
        "Oferecer mediação individual e diferentes formas de resposta, como tópicos, setas, frases curtas, explicação oral ou apoio coletivo na leitura das fontes.",
    ],
    "geografia": [
        "Utilizar mapas, imagens, gráficos, tabelas e exemplos próximos da realidade dos estudantes para favorecer a leitura das diferentes linguagens geográficas.",
        "Organizar registros guiados com palavras-chave, legendas, comparações e relações entre sociedade, natureza e território.",
        "Oferecer mediação individual e retomadas coletivas durante a interpretação das informações e a elaboração das respostas.",
    ],
    "ingles": [
        "Apresentar vocabulário com apoio visual, modelos de frases, leitura guiada e repetições curtas para favorecer a compreensão e a participação.",
        "Organizar as atividades em etapas pequenas, com exemplos de resposta, banco de palavras e checagens frequentes de entendimento.",
        "Permitir respostas por associação, seleção, fala curta, escrita orientada ou produção em dupla, conforme a necessidade dos estudantes.",
    ],
    "arte": [
        "Utilizar imagens, sons, vídeos curtos, demonstrações e exemplos culturais variados para ampliar o acesso aos repertórios mobilizados na aula.",
        "Organizar registros guiados com palavras-chave, comparações e sínteses coletivas para apoiar a leitura e a apreciação das produções artísticas.",
        "Permitir diferentes formas de participação e expressão, como fala, escrita, desenho, criação em dupla ou registro individual orientado.",
    ],
    "projeto_de_vida": [
        "Promover ambiente acolhedor, com combinados de escuta e respeito, para que os estudantes participem sem exposição excessiva de vivências pessoais.",
        "Utilizar perguntas orientadoras, exemplos concretos e registros visuais para apoiar a reflexão e a elaboração das respostas.",
        "Permitir diferentes formas de participação, como fala, escrita, desenho, registro individual ou produção em dupla, respeitando ritmos e necessidades.",
    ],
    "lideranca_oratoria": [
        "Promover ambiente acolhedor, com combinados de escuta e respeito, para que os estudantes participem sem exposição excessiva de vivências pessoais.",
        "Utilizar perguntas orientadoras, exemplos concretos e registros visuais para apoiar a reflexão e a elaboração das respostas.",
        "Permitir diferentes formas de participação, como fala, escrita, desenho, registro individual ou produção em dupla, respeitando ritmos e necessidades.",
    ],
    "educacao_financeira": [
        "Utilizar situações concretas do cotidiano, como compras, orçamento, metas e escolhas de consumo, para favorecer a compreensão do tema.",
        "Organizar cálculos, dados e informações em tabelas, listas, esquemas ou passo a passo no quadro para apoiar leitura e tomada de decisão.",
        "Oferecer mediação individual e correção dialogada, retomando vocabulário financeiro, critérios de escolha e estratégias de resolução conforme as dificuldades observadas.",
    ],
    "tecnologia_inovacao": [
        "Apresentar exemplos concretos do cotidiano tecnologico da turma, como teclado, mouse, monitor, celular, mensagens, foruns e equipamentos da escola, para facilitar a compreensao do conteudo.",
        "Demonstrar cada etapa no quadro ou no projetor antes da execucao individual, com retomada oral dos comandos, blocos, regras ou classificacoes necessarios a atividade.",
        "Permitir registros por palavras-chave, colunas, topicos, desenhos, esquemas, frases curtas, producao em dupla ou resposta oral mediada, conforme a necessidade dos estudantes.",
    ],
    "sociologia": [
        "Apresentar o conteúdo com exemplos concretos, linguagem clara e apoio visual para favorecer a compreensão dos conceitos e problemas discutidos.",
        "Organizar registros guiados, perguntas orientadoras e sínteses parciais para apoiar a participação e a construção das respostas.",
        "Oferecer acompanhamento individual, retomadas coletivas e flexibilização das formas de registro conforme as necessidades da turma.",
    ],
}

_ACESSIBILIDADE_FINANCEIRA_POR_TIPO = {
    "orcamento_planejamento": [
        "Organizar receitas, despesas, metas e saldo em tabela simples ou esquema no quadro, com exemplos graduados antes da atividade individual.",
        "Oferecer roteiro com etapas do planejamento financeiro: identificar recursos, listar gastos, definir prioridades e revisar escolhas.",
        "Apoiar individualmente estudantes com dificuldade em leitura de dados, cálculos ou organização das respostas.",
    ],
    "consumo_consciente": [
        "Apresentar critérios visuais para comparar alternativas de consumo, como necessidade, desejo, preço, durabilidade e consequência da escolha.",
        "Utilizar exemplos neutros e cotidianos, evitando exposição ou julgamento dos hábitos financeiros pessoais e familiares.",
        "Permitir registros por tópicos, esquemas ou explicação oral para apoiar a justificativa das decisões.",
    ],
    "investimento_poupanca": [
        "Representar metas, prazos e valores acumulados em quadro, tabela ou linha do tempo para facilitar a compreensão.",
        "Retomar o vocabulário financeiro essencial, como poupança, reserva, rendimento, meta e imprevisto, antes dos cálculos.",
        "Oferecer exemplos passo a passo e mediação individual durante a interpretação dos cenários.",
    ],
    "credito_endividamento": [
        "Disponibilizar resolução comentada para comparação entre valor à vista, parcelas, juros e custo total.",
        "Destacar no quadro os dados do problema e as perguntas que orientam a decisão responsável sobre crédito.",
        "Permitir calculadora, tabelas de apoio ou registro por etapas para estudantes com dificuldade nos cálculos.",
    ],
    "empreendedorismo": [
        "Organizar o projeto em etapas curtas: ideia, público, recursos, custos, preço, viabilidade e revisão.",
        "Utilizar quadro ou ficha de planejamento para apoiar a organização das decisões do grupo.",
        "Permitir diferentes formas de participação, como fala, desenho, tópicos, cálculo com apoio ou registro em dupla.",
    ],
    "analise_percentuais_noticias": [
        "Organizar no quadro os dados principais da noticia, destacando valor de referencia, percentual e comparacao antes dos calculos.",
        "Retomar passo a passo a leitura de tabelas, graficos e manchetes numericas, com exemplos simples antes da atividade individual.",
        "Permitir registro por etapas, uso de esquemas e apoio individual na interpretacao dos percentuais e de seu significado.",
    ],
    "governo_economia": [
        "Apresentar exemplos concretos de impostos, servicos publicos e regulacao com linguagem acessivel e apoio visual no quadro.",
        "Registrar palavras-chave e relacoes principais em esquema simples para apoiar a compreensao do papel do governo na economia.",
        "Realizar leitura mediada dos enunciados e permitir respostas por topicos curtos ou fala orientada quando necessario.",
    ],
    "impacto_decisoes_economicas": [
        "Organizar as situacoes em etapas curtas, destacando recursos disponiveis, alternativas e possiveis consequencias de cada escolha.",
        "Utilizar exemplos proximos do cotidiano e comparacoes simples para apoiar a analise das decisoes economicas.",
        "Oferecer apoio individual e flexibilizacao do registro para estudantes com dificuldade na interpretacao dos cenarios apresentados.",
    ],
    "cidadania_financeira": [
        "Utilizar exemplos de comprovantes, garantias, direitos e cuidados de segurança com linguagem acessível.",
        "Registrar no quadro palavras-chave e procedimentos de proteção para orientar a análise das situações.",
        "Realizar leitura mediada dos enunciados e apoiar estudantes com dificuldade na interpretação dos direitos e responsabilidades.",
    ],
    "instituicoes_financeiras": [
        "Explicar funções de instituições financeiras com exemplos concretos e vocabulário acessível, como banco, conta, cartão e segurança.",
        "Organizar comparações em lista ou quadro para diferenciar formas de guardar, movimentar e proteger o dinheiro.",
        "Oferecer apoio individual durante a leitura e a organização das respostas sobre serviços financeiros.",
    ],
}


_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO = {
    "autoconhecimento": [
        "Promover ambiente acolhedor, com combinados de escuta e respeito, para que os estudantes participem sem exposição excessiva de vivências pessoais.",
        "Oferecer modelo estruturado do mapa com campos pré-definidos para alunos que precisam de mais apoio para organizar as ideias visualmente.",
        "Garantir que a atividade de compartilhamento em duplas seja feita com colega escolhido pelo próprio aluno, respeitando vínculos de confiança.",
    ],
    "futureme": [
        "Providenciar dispositivo individual para alunos sem acesso a celular, garantindo que todos possam usar a plataforma sem depender de compartilhamento.",
        "Permitir que alunos que não se sintam confortáveis em cadastrar informações pessoais preencham apenas os campos obrigatórios.",
        "Oferecer versão impressa do questionário para alunos com dificuldade de navegação digital, garantindo a mesma experiência de reflexão.",
    ],
    "producao_coletiva": [
        "Garantir que alunos com dificuldade motora ou de escrita assumam funções de coordenação, fala ou organização no grupo, sem ficarem excluídos da produção.",
        "Oferecer modelo simplificado do produto (biomapa, campanha) para grupos com dificuldade de organização, com campos pré-definidos para preenchimento.",
        "Permitir que grupos sem acesso a celular realizem a apresentação ao vivo ou leiam o roteiro em voz alta, garantindo a mesma qualidade de participação.",
    ],
    "convivencia": [
        "Garantir que alunos mais tímidos ou com dificuldade de expressão oral possam contribuir por escrito, entregando sua proposta ao secretário do círculo.",
        "Oferecer roteiro de perguntas-guia para alunos que precisam de mais estrutura para participar do debate, sem expô-los desnecessariamente.",
        "Permitir que alunos que não se sintam confortáveis com o dilema escolhido pela turma registrem sua perspectiva individualmente no caderno.",
    ],
    "consciencia_social": [
        "Conduzir a dinâmica da Caminhada do Privilégio sem obrigar nenhum aluno a participar — oferecer a opção de observar e registrar as percepções por escrito.",
        "Garantir que a discussão sobre desigualdades não exponha situações pessoais de vulnerabilidade — manter o foco em grupos sociais, não em indivíduos.",
        "Oferecer roteiro de análise com perguntas-guia para alunos que precisam de mais estrutura para identificar padrões de representação no ambiente digital.",
    ],
    "encerramento": [
        "Permitir que alunos que não se sintam confortáveis com o ritual simbólico coletivo registrem suas palavras/compromissos individualmente no caderno.",
        "Oferecer perguntas-guia simplificadas para alunos com dificuldade de síntese, ajudando-os a identificar pelo menos uma descoberta e uma mudança de atitude.",
        "Garantir que alunos sem acesso a celular participem da produção final (vídeo) por meio de apresentação ao vivo ou leitura do roteiro, com o mesmo valor.",
    ],
}


class GeradorAcessibilidade:
    """Gera estratégias de acessibilidade contextualizadas por tipo de recurso."""

    def gerar(
        self,
        perfil: str,
        tipo: str,
        tema: str,
        recursos_detectados: list[str] | None = None,
        indice_aula: int = 0,
        aprendizagem: str = "",
        desenvolvimento: str = "",
        disciplina: str = "",
    ) -> list[str]:
        """
        Gera 3 itens de acessibilidade contextualizados.

        Se recursos_detectados estiver disponível, seleciona estratégias
        específicas do catálogo. Caso contrário, usa fallback por perfil.
        """
        # Só tenta detectar pelo texto gerado quando nenhum recurso veio do PDF.
        if recursos_detectados is None and desenvolvimento:
            recursos_detectados = detectar_recursos(desenvolvimento, tema)

        if perfil == "educacao_financeira" and tipo in _ACESSIBILIDADE_FINANCEIRA_POR_TIPO:
            return list(_ACESSIBILIDADE_FINANCEIRA_POR_TIPO[tipo])

        if perfil == "projeto_de_vida" and tipo in _ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO:
            return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO[tipo])

        if perfil in {"projeto_de_vida", "lideranca_oratoria"}:
            fallback = _FALLBACK_POR_PERFIL.get(perfil, [])
            if fallback:
                return list(fallback)

        # Estratégia: selecionar dos catálogos por recurso
        if recursos_detectados:
            itens = self._selecionar_por_recursos(recursos_detectados, indice_aula, tema)
            if len(itens) >= 3:
                return itens[:3]

        # Fallback: usar catálogo por perfil
        fallback = _FALLBACK_POR_PERFIL.get(perfil, [])
        if fallback:
            return list(fallback)

        # Fallback final genérico
        base_texto = normalizar_texto(f"{tema} {aprendizagem} {desenvolvimento}")
        if contem_termos(base_texto, ["imagem", "grafico", "mapa", "tabela", "esquema", "anuncio"]):
            primeiro = "Utilizar recursos visuais, exemplos concretos e mediação oral para favorecer a compreensão do conteúdo e das atividades propostas."
        else:
            primeiro = "Apresentar o conteúdo com linguagem clara, exemplos comentados e retomadas frequentes dos pontos essenciais."

        if contem_termos(base_texto, ["leitura", "texto", "fonte", "noticia", "conto", "documento"]):
            segundo = "Realizar leitura guiada com pausas para explicar vocabulário, informações centrais e comandos necessários à participação na aula."
        else:
            segundo = "Explicar as atividades passo a passo, com apoio visual e perguntas orientadoras para apoiar diferentes ritmos de aprendizagem."

        return [
            primeiro,
            segundo,
            "Oferecer mediação individual, tempo ampliado quando necessário e diferentes formas de registro para apoiar a participação de todos os estudantes.",
        ]

    def _selecionar_por_recursos(
        self, recursos: list[str], indice_aula: int, tema: str
    ) -> list[str]:
        """Seleciona estratégias do catálogo baseado nos recursos detectados."""
        itens_selecionados = []
        recursos_usados = set()

        for recurso in recursos:
            if recurso in recursos_usados:
                continue
            estrategias = CATALOGO_ESTRATEGIAS.get(recurso, [])
            if not estrategias:
                continue

            # Seleciona uma estratégia com variação pelo índice da aula
            idx = _indice_hash([recurso, tema, str(indice_aula)], len(estrategias))
            itens_selecionados.append(estrategias[idx])
            recursos_usados.add(recurso)

            if len(itens_selecionados) >= 3:
                break

        # Se não completou 3, adiciona estratégia genérica de mediação
        while len(itens_selecionados) < 3:
            genericas = [
                "Oferecer mediação individual durante as atividades, adequando explicações, tempo e forma de resposta conforme as necessidades da turma.",
                "Utilizar apoio visual, retomadas coletivas e registros orientados para favorecer a compreensão dos conceitos trabalhados.",
                "Organizar intervenções com exemplos comentados e acompanhamento próximo para apoiar estudantes com dificuldades de leitura, interpretação ou organização das tarefas.",
            ]
            idx_gen = len(itens_selecionados) % len(genericas)
            itens_selecionados.append(genericas[idx_gen])

        return itens_selecionados


# ── Instância global e função de conveniência ──────────────────────────────

_gerador = GeradorAcessibilidade()


def _tem_marcador_visao(base: str) -> bool:
    return bool(
        re.search(
            r"\b(?:olho|retina|cornea|pupila|cristalino|sistema visual|formacao da imagem|caminho da luz|visao)\b",
            base,
            flags=re.I,
        )
    )


def _acessibilidade_especifica_por_aula(
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    recursos_detectados: list[str] | None = None,
) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))
    recursos = {normalizar_texto(item) for item in (recursos_detectados or [])}
    if _tem_marcador_visao(base):
        return [
            "Ampliar o esquema anatômico e nomear oralmente cada estrutura antes da atividade individual.",
            "Disponibilizar banco de palavras com os nomes das estruturas para apoiar a legenda.",
            "Permitir apoio em dupla para leitura guiada e conferência das identificações.",
        ]
    if "texto sintese" in base or "texto-sintese" in base or "sintese individual" in base:
        return [
            "Oferecer roteiro com perguntas-chave para organizar a escrita do texto-síntese.",
            "Destacar palavras-chave no quadro e permitir produção inicial em tópicos antes do texto final.",
            "Realizar mediação individual para revisão de clareza, sequência de ideias e vocabulário científico.",
        ]
    if "tabela" in base and not recursos:
        return [
            "Preencher uma linha da tabela como exemplo antes do trabalho autônomo.",
            "Organizar pares produtivos para apoiar leitura dos comandos e preenchimento dos campos.",
            "Permitir consulta constante ao material digital e ao quadro durante a atividade.",
        ]
    return []


def _acessibilidade_lingua_portuguesa(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["trilha", "alice no pais das maravilhas", "pequeno principe", "peter pan", "leitura compartilhada", "predicao guiada"]):
        return [
            "Realizar leitura mediada com pausas para explicação de palavras e acontecimentos importantes da narrativa.",
            "Permitir respostas orais, desenhos, tópicos ou pequenos registros escritos como forma de participação.",
            "Disponibilizar perguntas orientadoras para auxiliar na compreensão e organização das ideias.",
        ]

    if any(k in base for k in ["versao final", "redacao paulista", "revisao orientada", "revis", "reescrita", "rascunho", "producao textual", "producao de textos"]):
        return [
            "Disponibilizar checklist simplificado para orientar a revisão do texto.",
            "Permitir apoio individual durante a leitura, revisão e escrita da versão final.",
            "Oferecer modelos de organização textual e exemplos de conectivos para auxiliar a produção escrita.",
        ]

    if "verbo haver" in base or re.search(r"\bhaver\b", base):
        return [
            "Oferecer exemplos práticos antes das atividades autônomas.",
            "Disponibilizar esquemas simples com regras e exemplos do verbo haver.",
            "Permitir apoio em dupla durante leitura e resolução das questões.",
        ]

    if "tirinha" in base and any(k in base for k in ["humor", "critica", "conflito", "linguagem mista"]):
        return [
            "Disponibilizar perguntas orientadoras para auxiliar na interpretação das tirinhas.",
            "Permitir respostas orais, desenhos ou registros em tópicos curtos.",
            "Realizar leitura mediada das imagens e falas para apoiar a compreensão.",
        ]

    if any(k in base for k in ["figura de linguagem", "figuras de linguagem", "imperativo"]) and any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario"]):
        return [
            "Ampliar imagens e destacar visualmente informações importantes dos anúncios.",
            "Permitir leitura em dupla ou apoio do professor durante as atividades.",
            "Disponibilizar exemplos resolvidos antes das propostas individuais.",
        ]

    if any(k in base for k in ["metafora", "metaforas"]) and any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario"]):
        return [
            "Disponibilizar palavras-chave e exemplos simples de metáforas.",
            "Permitir explicações orais mediadas durante as atividades.",
            "Realizar leitura guiada dos anúncios, destacando elementos importantes.",
        ]

    if any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario", "propaganda", "slogan"]):
        return [
            "Disponibilizar perguntas curtas e objetivas para orientar a análise dos anúncios.",
            "Permitir registros por tópicos, desenhos ou respostas orais.",
            "Retomar coletivamente conceitos importantes antes das atividades.",
        ]

    if any(k in base for k in ["carta de reclamacao", "reclamar por escrito", "texto reivindicatorio", "reivindicatorios"]):
        return [
            "Realizar leitura mediada da carta de reclamação, destacando finalidade, estrutura e argumentos.",
            "Disponibilizar roteiro com perguntas curtas para orientar a análise do texto.",
            "Permitir respostas orais, registros em tópicos ou produção em dupla conforme a necessidade.",
        ]

    if any(k in base for k in ["conjuncao", "conjuncoes", "locucao conjuntiva", "locucoes conjuntivas"]):
        return [
            "Disponibilizar quadro com exemplos de conjunções e relações de sentido.",
            "Oferecer exemplos comentados antes das atividades autônomas.",
            "Permitir apoio em dupla durante leitura, identificação e resolução das questões.",
        ]

    if any(k in base for k in ["texto multissemiotico", "linguagem verbal", "linguagem nao verbal"]):
        return [
            "Realizar leitura guiada das imagens, falas e demais elementos visuais do texto.",
            "Disponibilizar perguntas orientadoras para apoiar a relação entre linguagem verbal e não verbal.",
            "Permitir registros por tópicos, desenhos, setas ou respostas orais mediadas.",
        ]


    # Novos tipos de aula LP — derivados da classificacao especializada
    if any(k in base for k in ["leitura_literaria", "cronica", "conto", "poema", "poesia", "narrativa",
                                "eu lirico", "narrador", "enredo", "personagem", "fruicao", "literatura"]):
        return [
            "Realizar leitura mediada do texto literário com pausas para explicação de palavras, expressões e acontecimentos.",
            "Disponibilizar perguntas orientadoras que auxiliem na identificação de personagens, conflito e tema.",
            "Permitir respostas orais, desenhos, mapas mentais ou registros em tópicos como forma de participação.",
        ]

    if any(k in base for k in ["gramatica_contextualizada", "modo subjuntivo", "modo indicativo",
                                "tempos verbais", "coesao", "coesivos", "pronomes", "regencia",
                                "modalizacao", "polissemia", "intertextualidade"]):
        return [
            "Disponibilizar esquemas visuais com exemplos da norma ou fenômeno gramatical estudado.",
            "Oferecer trechos comentados antes das atividades autônomas para facilitar a identificação do conteúdo.",
            "Permitir apoio em dupla ou resolução parcial com mediação do professor.",
        ]

    if any(k in base for k in ["leitura_jornalistica", "noticia", "editorial", "reportagem",
                                "manchete", "lide", "jornalismo", "midia", "imparcialidade"]):
        return [
            "Disponibilizar glossário com termos do universo jornalístico utilizados no texto.",
            "Realizar leitura mediada do texto com ênfase em lide, manchete e intenção comunicativa.",
            "Permitir respostas em tópicos curtos ou orais com apoio de perguntas orientadoras.",
        ]

    if any(k in base for k in ["producao_textual", "producao", "resenha", "carta do leitor",
                                "estrutura do genero", "publico-alvo", "suporte", "redija"]):
        return [
            "Disponibilizar modelo de planejamento textual com etapas simples e exemplos de estrutura.",
            "Oferecer lista de verificação para que os estudantes confiram adequação ao gênero antes da versão final.",
            "Permitir apoio individual na escrita e na revisão, incluindo ditado para o professor quando necessário.",
        ]

    if any(k in base for k in ["pesquisa", "scielo", "curadoria", "plagio", "fontes confiaveis",
                                "divulgacao cientifica", "direitos autorais", "google academico"]):
        return [
            "Disponibilizar lista de sites e fontes confiáveis previamente selecionadas pelo professor.",
            "Orientar a pesquisa com roteiro de etapas simples: busca, seleção, leitura e registro.",
            "Permitir que os estudantes trabalhem em dupla durante a navegação e a síntese das informações.",
        ]

    return [
        "Disponibilizar perguntas orientadoras para apoiar a leitura, a interpretação e a organização das respostas.",
        "Permitir registros por tópicos, frases curtas, desenho, esquema ou resposta oral mediada.",
        "Realizar retomadas coletivas dos comandos e dos conceitos importantes antes das atividades.",
    ]



def _acessibilidade_projeto_vida(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    """Detecta o tipo de aula de Projeto de Vida pelo contexto e retorna estratégias específicas.

    Cobre 6 tipos (mesma prioridade de _tipo_aula_projeto_de_vida em classificador.py):
    futureme, encerramento, consciencia_social, convivencia, producao_coletiva, autoconhecimento.
    """
    from core.lib.classificador import (
        _PV_FUTUREME, _PV_ENCERRAMENTO, _PV_CONSCIENCIA_SOCIAL,
        _PV_CONVIVENCIA, _PV_PRODUCAO_COLETIVA,
    )
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    # 1. Plataforma FutureMe
    if contem_termos(base, _PV_FUTUREME):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["futureme"])

    # 2. Encerramento e Síntese
    if contem_termos(base, _PV_ENCERRAMENTO):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["encerramento"])

    # 3. Consciência Social
    if contem_termos(base, _PV_CONSCIENCIA_SOCIAL):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["consciencia_social"])

    # 4. Convivência e Tomada de Decisão
    if contem_termos(base, _PV_CONVIVENCIA):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["convivencia"])

    # 5. Produção Coletiva
    if contem_termos(base, _PV_PRODUCAO_COLETIVA):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["producao_coletiva"])

    # 6. Autoconhecimento (padrão)
    return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["autoconhecimento"])


def _acessibilidade_matematica(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    """Gera acessibilidade específica para Matemática, diferenciada por tipo de aula."""
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    # Aula Khan ou Verificação
    if any(k in base for k in ["khan", "khanmigo", "bit.ly", "verificacao", "revisao", "relembre", "retomar", "consolidar"]):
        return [
            "Organizar atividades paralelas no caderno para estudantes sem acesso ao dispositivo ou com dificuldade de navegação no aplicativo.",
            "Oferecer orientação individual sobre como interpretar os feedbacks do aplicativo e utilizá-los para corrigir estratégias.",
            "Disponibilizar resolução comentada para os estudantes que precisarem de apoio adicional na atividade de revisão.",
        ]

    # Aula de Gráfico
    if any(k in base for k in ["grafico", "representacao grafica", "plano cartesiano", "eixo", "pares ordenados", "tabela"]):
        return [
            "Ler coletivamente os eixos, legendas e títulos do gráfico ou tabela antes da análise individual.",
            "Disponibilizar versão simplificada ou ampliada dos dados para apoiar a leitura e interpretação.",
            "Organizar questões de leitura guiada para orientar os estudantes na interpretação dos dados e na elaboração das conclusões.",
        ]

    # Aula de Resolução de Problemas
    if any(k in base for k in ["resolucao de problemas", "metodo de polya", "polya", "todo mundo escreve"]):
        return [
            "Apresentar resolucao comentada de um problema similar para servir como referência orientadora antes da atividade individual.",
            "Organizar a resolução em etapas curtas e visuais: identificação dos dados, escolha da estratégia, cálculo e verificação do resultado.",
            "Permitir o uso de calculadora, tabuada ou material manipulável para estudantes com dificuldade de cálculo, focando na compreensão do método.",
        ]

    # Aula de Tecnologia (GeoGebra, calculadora científica)
    if any(k in base for k in ["geogebra", "calculadora cientifica", "geometria dinamica", "acesse o site"]):
        return [
            "Demonstrar cada etapa do uso da ferramenta no projetor antes da exploração individual ou em dupla.",
            "Organizar roteiro com instruções visuais passo a passo para apoiar estudantes com dificuldade de navegação na ferramenta.",
            "Permitir que estudantes com dificuldade de acesso ao equipamento participem em dupla ou utilizem recursos impressos equivalentes.",
        ]

    # Padrão: conceito_novo e modelagem
    return [
        "Disponibilizar resolução comentada e exemplos graduados para favorecer a compreensão dos procedimentos e das relações matemáticas envolvidas.",
        "Organizar a atividade em etapas curtas com retomadas coletivas, comparando estratégias e destacando dados, operações e representações essenciais.",
        "Oferecer mediação individual durante os registros e cálculos, permitindo diferentes formas de resolução, conferência e explicação das respostas.",
    ]


def _limitar_itens(itens: list[str], minimo: int = 2, maximo: int = 3) -> list[str]:
    saida = []
    for texto in itens or []:
        txt = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip())
        if not txt:
            continue
        if len(txt) > 220:
            txt = limitar_texto_natural(txt, 220)
        saida.append(txt)
        if len(saida) >= maximo:
            break
    return saida[:maximo] if len(saida) >= minimo else saida


def gerar_acessibilidade_aprimorada(
    tema: str,
    aprendizagem: str = "",
    desenvolvimento: str = "",
    disciplina: str = "",
    perfil: str = "",
    tipo: str = "",
    recursos_detectados: list[str] | None = None,
    indice_aula: int = 0,
) -> list[str]:
    """
    Gera acessibilidade aprimorada.
    Compatível com a assinatura de gerar_acessibilidade_dinamica() do avaliacao.py,
    mas com seleção por tipo de recurso e variação sequencial.
    """
    from core.lib.classificador import perfil_disciplina, detectar_tipo_aula

    if not perfil:
        perfil = perfil_disciplina(disciplina)
    if not tipo:
        tipo = detectar_tipo_aula(desenvolvimento, tema, disciplina)

    especifico = _acessibilidade_especifica_por_aula(
        tema,
        aprendizagem,
        desenvolvimento,
        recursos_detectados=recursos_detectados,
    )
    if especifico:
        return _limitar_itens(especifico, minimo=2, maximo=3)

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return _limitar_itens(
            _acessibilidade_lingua_portuguesa(tema, aprendizagem, desenvolvimento),
            minimo=2,
            maximo=3,
        )

    if perfil == "matematica":
        return _limitar_itens(
            _acessibilidade_matematica(tema, aprendizagem, desenvolvimento),
            minimo=2,
            maximo=3,
        )

    if perfil == "projeto_de_vida":
        return _limitar_itens(
            _acessibilidade_projeto_vida(tema, aprendizagem, desenvolvimento),
            minimo=2,
            maximo=3,
        )

    return _limitar_itens(_gerador.gerar(
        perfil=perfil,
        tipo=tipo,
        tema=tema,
        recursos_detectados=recursos_detectados,
        indice_aula=indice_aula,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
    ), minimo=2, maximo=3)
