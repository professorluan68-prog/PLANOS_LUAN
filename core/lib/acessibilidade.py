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
from core.lib.acessibilidade_perfis import (
    gerar_acessibilidade_especifica_por_aula,
    gerar_acessibilidade_por_perfil,
)


# ── Catálogo de estratégias por tipo de recurso/atividade ──────────────────

CATALOGO_ESTRATEGIAS = {
    "leitura_texto": [
        "Realizar leitura mediada com pausas para explicar vocabulário e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Permitir leitura em dupla ou com apoio de colega-tutor.",
        "Destacar palavras-chave da aula no quadro antes da leitura.",
        "Oferecer perguntas-guia escritas para orientar a leitura.",
    ],
    "analise_imagem": [
        "Descrever oralmente os elementos visuais da imagem ou slide.",
        "Ampliar imagens no quadro ou projetor, apontando detalhes importantes.",
        "Oferecer roteiro de observação da imagem com perguntas simples.",
        "Permitir registro por desenho, esquema ou anotação oral.",
    ],
    "analise_grafico": [
        "Ler coletivamente os eixos, legendas e títulos do gráfico ou tabela.",
        "Disponibilizar versão simplificada ou ampliada dos dados.",
        "Organizar as informações em lista ou tópicos no quadro.",
        "Oferecer questões de leitura guiada para interpretar os dados.",
    ],
    "calculo_resolucao": [
        "Disponibilizar resolução comentada e exemplos de referência.",
        "Organizar a atividade em etapas curtas com retomadas coletivas.",
        "Oferecer mediação individual e aceitar diferentes formas de registro.",
        "Disponibilizar material de apoio (tabuada, fórmulas, calculadora).",
        "Apresentar exemplos resolvidos como referência antes da atividade.",
    ],
    "producao_textual": [
        "Disponibilizar banco de palavras e modelos de início de frases.",
        "Permitir produção oral com escrita assistida ou registro em tópicos.",
        "Oferecer checklist simples de revisão com critérios claros.",
        "Organizar a escrita em etapas (rascunho, revisão, versão final).",
    ],
    "experimentacao": [
        "Garantir acessibilidade física dos materiais para todos.",
        "Descrever etapas do experimento em cartões visuais passo a passo.",
        "Oferecer registro por desenho, tópicos ou explicação oral.",
        "Organizar grupos cooperativos com funções simples e definidas.",
    ],
    "debate_oral": [
        "Oferecer perguntas orientadoras escritas antes da fala.",
        "Permitir respostas escritas ou sinalização para quem tem dificuldade de fala.",
        "Organizar turnos de fala com tempo e mediação do professor.",
        "Disponibilizar tempo para rascunho de ideias antes da socialização.",
    ],
    "escuta_audio": [
        "Disponibilizar transcrição ou resumo curto do áudio ou vídeo.",
        "Permitir repetição do áudio e pausas para anotações.",
        "Oferecer perguntas orientadoras simples antes de ouvir.",
        "Organizar discussão em duplas após a escuta.",
    ],
}

# ── Estratégias genéricas por perfil (fallback) ────────────────────────────

_FALLBACK_POR_PERFIL = {
    "matematica": [
        "Disponibilizar resolução comentada e exemplos para favorecer a compreensão.",
        "Organizar a atividade em etapas curtas com retomadas coletivas.",
        "Oferecer mediação individual e aceitar diferentes formas de cálculo.",
    ],
    "lingua_portuguesa_ef": [
        "Oferecer leitura mediada com pausas para explicar vocabulário e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Realizar mediações individuais e flexibilizar as formas de registro.",
    ],
    "lingua_portuguesa_em": [
        "Oferecer leitura mediada com pausas para explicar vocabulário e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Realizar mediações individuais e flexibilizar as formas de registro.",
    ],
    "leitura_redacao": [
        "Oferecer leitura mediada com pausas para explicar vocabulário e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Realizar mediações individuais e flexibilizar as formas de registro.",
    ],
    "orientacao_estudos": [
        "Modelar estratégias de estudo com exemplos concretos e registros guiados.",
        "Retomar procedimentos com linguagem simples e apoio visual.",
        "Oferecer acompanhamento individualizado e flexibilidade no registro.",
    ],
    "ciencias_ef": [
        "Utilizar imagens, esquemas, tabelas e exemplos concretos.",
        "Organizar registros guiados com palavras-chave e relações de causa e consequência.",
        "Oferecer mediação individual, permitindo respostas em tópicos ou desenhos.",
    ],
    "biologia": [
        "Utilizar imagens, esquemas, tabelas e exemplos do cotidiano.",
        "Organizar registros guiados com palavras-chave e relações de causa e consequência.",
        "Oferecer mediação individual, permitindo respostas em tópicos ou desenhos.",
    ],
    "quimica": [
        "Utilizar imagens, esquemas, tabelas e exemplos práticos.",
        "Organizar registros guiados com palavras-chave e relações de causa e consequência.",
        "Oferecer mediação individual, permitindo respostas em tópicos ou desenhos.",
    ],
    "fisica": [
        "Utilizar imagens, esquemas, tabelas e demonstrações práticas.",
        "Organizar registros guiados com palavras-chave and relações de causa e consequência.",
        "Oferecer mediação individual, permitindo respostas em tópicos ou desenhos.",
    ],
    "historia": [
        "Utilizar fontes, imagens, mapas, linhas do tempo e esquemas simples.",
        "Retomar relações de tempo, causa e consequência com registros guiados.",
        "Oferecer mediação individual e aceitar respostas por tópicos ou frases curtas.",
    ],
    "geografia": [
        "Utilizar mapas, imagens e exemplos do cotidiano para leitura territorial.",
        "Organizar registros guiados com legendas, palavras-chave e comparações simples.",
        "Oferecer mediação individual e retomadas coletivas nas interpretações.",
    ],
    "ingles": [
        "Apresentar vocabulário com apoio visual, modelos de frases e repetições curtas.",
        "Organizar atividades em etapas pequenas, com banco de palavras.",
        "Permitir respostas por associação, fala curta ou escrita guiada.",
    ],
    "arte": [
        "Utilizar imagens, sons e demonstrações práticas para ampliar o acesso.",
        "Organizar registros guiados com palavras-chave e sínteses coletivas.",
        "Permitir diferentes formas de participação (fala, escrita, desenho ou dupla).",
    ],
    "projeto_de_vida": [
        "Promover ambiente acolhedor, sem exposição de vivências pessoais.",
        "Utilizar perguntas diretas, exemplos concretos e registros visuais.",
        "Permitir participação livre por fala, escrita ou desenho, respeitando ritmos.",
    ],
    "lideranca_oratoria": [
        "Promover ambiente acolhedor, sem exposição de vivências pessoais.",
        "Utilizar perguntas diretas, exemplos concretos e registros visuais.",
        "Permitir participação livre por fala, escrita ou desenho, respeitando ritmos.",
    ],
    "educacao_financeira": [
        "Utilizar situações do cotidiano como compras e planejamento.",
        "Organizar tabelas, dados e passos no quadro para tomada de decisão.",
        "Oferecer mediação individual e correção dialogada nas dificuldades.",
    ],
    "tecnologia_inovacao": [
        "Apresentar exemplos concretos do cotidiano tecnológico da turma.",
        "Demonstrar cada etapa no quadro ou projetor antes da prática.",
        "Permitir registros por palavras-chave, tópicos, desenhos ou duplas.",
    ],
    "sociologia": [
        "Apresentar conceitos com exemplos práticos e linguagem acessível.",
        "Organizar registros guiados, perguntas orientadoras e sínteses curtas.",
        "Oferecer acompanhamento individual e flexibilizar as formas de registro.",
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

    especifico = gerar_acessibilidade_especifica_por_aula(
        tema,
        aprendizagem,
        desenvolvimento,
        recursos_detectados=recursos_detectados,
    )
    if especifico:
        return _limitar_itens(especifico, minimo=2, maximo=3)

    acessibilidade_por_perfil = gerar_acessibilidade_por_perfil(
        perfil,
        tema,
        aprendizagem,
        desenvolvimento,
    )
    if acessibilidade_por_perfil:
        return _limitar_itens(
            acessibilidade_por_perfil,
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
