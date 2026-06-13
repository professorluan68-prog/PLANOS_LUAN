"""
Gerador de estratÃ©gias de acessibilidade por tipo de recurso.

Em vez de gerar frases genÃ©ricas por disciplina, analisa o tipo de
atividade/recurso presente no conteÃºdo e seleciona estratÃ©gias
especÃ­ficas de um catÃ¡logo organizado.
"""

import re
from core.lib.classificador import normalizar_texto, contem_termos, detectar_recursos
from core.lib.progressao import _indice_hash
from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural
from core.lib.acessibilidade_perfis import (
    gerar_acessibilidade_especifica_por_aula,
    gerar_acessibilidade_por_perfil,
)


# â”€â”€ CatÃ¡logo de estratÃ©gias por tipo de recurso/atividade â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CATALOGO_ESTRATEGIAS = {
    "leitura_texto": [
        "Realizar leitura mediada com pausas para explicar vocabulÃ¡rio e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Permitir leitura em dupla ou com apoio de colega-tutor.",
        "Destacar palavras-chave da aula no quadro antes da leitura.",
        "Oferecer perguntas-guia escritas para orientar a leitura.",
    ],
    "analise_imagem": [
        "Descrever oralmente os elementos visuais da imagem ou slide.",
        "Ampliar imagens no quadro ou projetor, apontando detalhes importantes.",
        "Oferecer roteiro de observaÃ§Ã£o da imagem com perguntas simples.",
        "Permitir registro por desenho, esquema ou anotaÃ§Ã£o oral.",
    ],
    "analise_grafico": [
        "Ler coletivamente os eixos, legendas e tÃ­tulos do grÃ¡fico ou tabela.",
        "Disponibilizar versÃ£o simplificada ou ampliada dos dados.",
        "Organizar as informaÃ§Ãµes em lista ou tÃ³picos no quadro.",
        "Oferecer questÃµes de leitura guiada para interpretar os dados.",
    ],
    "calculo_resolucao": [
        "Disponibilizar resoluÃ§Ã£o comentada e exemplos de referÃªncia.",
        "Organizar a atividade em etapas curtas com retomadas coletivas.",
        "Oferecer mediaÃ§Ã£o individual e aceitar diferentes formas de registro.",
        "Disponibilizar material de apoio (tabuada, fÃ³rmulas, calculadora).",
        "Apresentar exemplos resolvidos como referÃªncia antes da atividade.",
    ],
    "producao_textual": [
        "Disponibilizar banco de palavras e modelos de inÃ­cio de frases.",
        "Permitir produÃ§Ã£o oral com escrita assistida ou registro em tÃ³picos.",
        "Oferecer checklist simples de revisÃ£o com critÃ©rios claros.",
        "Organizar a escrita em etapas (rascunho, revisÃ£o, versÃ£o final).",
    ],
    "experimentacao": [
        "Garantir acessibilidade fÃ­sica dos materiais para todos.",
        "Descrever etapas do experimento em cartÃµes visuais passo a passo.",
        "Oferecer registro por desenho, tÃ³picos ou explicaÃ§Ã£o oral.",
        "Organizar grupos cooperativos com funÃ§Ãµes simples e definidas.",
    ],
    "debate_oral": [
        "Oferecer perguntas orientadoras escritas antes da fala.",
        "Permitir respostas escritas ou sinalizaÃ§Ã£o para quem tem dificuldade de fala.",
        "Organizar turnos de fala com tempo e mediaÃ§Ã£o do professor.",
        "Disponibilizar tempo para rascunho de ideias antes da socializaÃ§Ã£o.",
    ],
    "escuta_audio": [
        "Disponibilizar transcriÃ§Ã£o ou resumo curto do Ã¡udio ou vÃ­deo.",
        "Permitir repetiÃ§Ã£o do Ã¡udio e pausas para anotaÃ§Ãµes.",
        "Oferecer perguntas orientadoras simples antes de ouvir.",
        "Organizar discussÃ£o em duplas apÃ³s a escuta.",
    ],
}

# â”€â”€ EstratÃ©gias genÃ©ricas por perfil (fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_FALLBACK_POR_PERFIL = {
    "matematica": [
        "Disponibilizar resoluÃ§Ã£o comentada e exemplos para favorecer a compreensÃ£o.",
        "Organizar a atividade em etapas curtas com retomadas coletivas.",
        "Oferecer mediaÃ§Ã£o individual e aceitar diferentes formas de cÃ¡lculo.",
    ],
    "lingua_portuguesa_ef": [
        "Oferecer leitura mediada com pausas para explicar vocabulÃ¡rio e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Realizar mediaÃ§Ãµes individuais e flexibilizar as formas de registro.",
    ],
    "lingua_portuguesa_em": [
        "Oferecer leitura mediada com pausas para explicar vocabulÃ¡rio e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Realizar mediaÃ§Ãµes individuais e flexibilizar as formas de registro.",
    ],
    "leitura_redacao": [
        "Oferecer leitura mediada com pausas para explicar vocabulÃ¡rio e comandos.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar as respostas.",
        "Realizar mediaÃ§Ãµes individuais e flexibilizar as formas de registro.",
    ],
    "orientacao_estudos": [
        "Modelar estratÃ©gias de estudo com exemplos concretos e registros guiados.",
        "Retomar procedimentos com linguagem simples e apoio visual.",
        "Oferecer acompanhamento individualizado e flexibilidade no registro.",
    ],
    "ciencias_ef": [
        "Utilizar imagens, esquemas, tabelas e exemplos concretos.",
        "Organizar registros guiados com palavras-chave e relaÃ§Ãµes de causa e consequÃªncia.",
        "Oferecer mediaÃ§Ã£o individual, permitindo respostas em tÃ³picos ou desenhos.",
    ],
    "biologia": [
        "Utilizar imagens, esquemas, tabelas e exemplos do cotidiano.",
        "Organizar registros guiados com palavras-chave e relaÃ§Ãµes de causa e consequÃªncia.",
        "Oferecer mediaÃ§Ã£o individual, permitindo respostas em tÃ³picos ou desenhos.",
    ],
    "quimica": [
        "Utilizar imagens, esquemas, tabelas e exemplos prÃ¡ticos.",
        "Organizar registros guiados com palavras-chave e relaÃ§Ãµes de causa e consequÃªncia.",
        "Oferecer mediaÃ§Ã£o individual, permitindo respostas em tÃ³picos ou desenhos.",
    ],
    "fisica": [
        "Utilizar imagens, esquemas, tabelas e demonstraÃ§Ãµes prÃ¡ticas.",
        "Organizar registros guiados com palavras-chave and relaÃ§Ãµes de causa e consequÃªncia.",
        "Oferecer mediaÃ§Ã£o individual, permitindo respostas em tÃ³picos ou desenhos.",
    ],
    "historia": [
        "Utilizar fontes, imagens, mapas, linhas do tempo e esquemas simples.",
        "Retomar relaÃ§Ãµes de tempo, causa e consequÃªncia com registros guiados.",
        "Oferecer mediaÃ§Ã£o individual e aceitar respostas por tÃ³picos ou frases curtas.",
    ],
    "geografia": [
        "Utilizar mapas, imagens e exemplos do cotidiano para leitura territorial.",
        "Organizar registros guiados com legendas, palavras-chave e comparaÃ§Ãµes simples.",
        "Oferecer mediaÃ§Ã£o individual e retomadas coletivas nas interpretaÃ§Ãµes.",
    ],
    "ingles": [
        "Apresentar vocabulÃ¡rio com apoio visual, modelos de frases e repetiÃ§Ãµes curtas.",
        "Organizar atividades em etapas pequenas, com banco de palavras.",
        "Permitir respostas por associaÃ§Ã£o, fala curta ou escrita guiada.",
    ],
    "arte": [
        "Utilizar imagens, sons e demonstraÃ§Ãµes prÃ¡ticas para ampliar o acesso.",
        "Organizar registros guiados com palavras-chave e sÃ­nteses coletivas.",
        "Permitir diferentes formas de participaÃ§Ã£o (fala, escrita, desenho ou dupla).",
    ],
    "projeto_de_vida": [
        "Promover ambiente acolhedor, sem exposiÃ§Ã£o de vivÃªncias pessoais.",
        "Utilizar perguntas diretas, exemplos concretos e registros visuais.",
        "Permitir participaÃ§Ã£o livre por fala, escrita ou desenho, respeitando ritmos.",
    ],
    "lideranca_oratoria": [
        "Promover ambiente acolhedor, sem exposiÃ§Ã£o de vivÃªncias pessoais.",
        "Utilizar perguntas diretas, exemplos concretos e registros visuais.",
        "Permitir participaÃ§Ã£o livre por fala, escrita ou desenho, respeitando ritmos.",
    ],
    "educacao_financeira": [
        "Utilizar situaÃ§Ãµes do cotidiano como compras e planejamento.",
        "Organizar tabelas, dados e passos no quadro para tomada de decisÃ£o.",
        "Oferecer mediaÃ§Ã£o individual e correÃ§Ã£o dialogada nas dificuldades.",
    ],
    "tecnologia_inovacao": [
        "Apresentar exemplos concretos do cotidiano tecnolÃ³gico da turma.",
        "Demonstrar cada etapa no quadro ou projetor antes da prÃ¡tica.",
        "Permitir registros por palavras-chave, tÃ³picos, desenhos ou duplas.",
    ],
    "sociologia": [
        "Apresentar conceitos com exemplos prÃ¡ticos e linguagem acessÃ­vel.",
        "Organizar registros guiados, perguntas orientadoras e sÃ­nteses curtas.",
        "Oferecer acompanhamento individual e flexibilizar as formas de registro.",
    ],
}

_ACESSIBILIDADE_FINANCEIRA_POR_TIPO = {
    "orcamento_planejamento": [
        "Organizar receitas, despesas, metas e saldo em tabela simples ou esquema no quadro, com exemplos graduados antes da atividade individual.",
        "Oferecer roteiro com etapas do planejamento financeiro: identificar recursos, listar gastos, definir prioridades e revisar escolhas.",
        "Apoiar individualmente estudantes com dificuldade em leitura de dados, cÃ¡lculos ou organizaÃ§Ã£o das respostas.",
    ],
    "consumo_consciente": [
        "Apresentar critÃ©rios visuais para comparar alternativas de consumo, como necessidade, desejo, preÃ§o, durabilidade e consequÃªncia da escolha.",
        "Utilizar exemplos neutros e cotidianos, evitando exposiÃ§Ã£o ou julgamento dos hÃ¡bitos financeiros pessoais e familiares.",
        "Permitir registros por tÃ³picos, esquemas ou explicaÃ§Ã£o oral para apoiar a justificativa das decisÃµes.",
    ],
    "investimento_poupanca": [
        "Representar metas, prazos e valores acumulados em quadro, tabela ou linha do tempo para facilitar a compreensÃ£o.",
        "Retomar o vocabulÃ¡rio financeiro essencial, como poupanÃ§a, reserva, rendimento, meta e imprevisto, antes dos cÃ¡lculos.",
        "Oferecer exemplos passo a passo e mediaÃ§Ã£o individual durante a interpretaÃ§Ã£o dos cenÃ¡rios.",
    ],
    "credito_endividamento": [
        "Disponibilizar resoluÃ§Ã£o comentada para comparaÃ§Ã£o entre valor Ã  vista, parcelas, juros e custo total.",
        "Destacar no quadro os dados do problema e as perguntas que orientam a decisÃ£o responsÃ¡vel sobre crÃ©dito.",
        "Permitir calculadora, tabelas de apoio ou registro por etapas para estudantes com dificuldade nos cÃ¡lculos.",
    ],
    "empreendedorismo": [
        "Organizar o projeto em etapas curtas: ideia, pÃºblico, recursos, custos, preÃ§o, viabilidade e revisÃ£o.",
        "Utilizar quadro ou ficha de planejamento para apoiar a organizaÃ§Ã£o das decisÃµes do grupo.",
        "Permitir diferentes formas de participaÃ§Ã£o, como fala, desenho, tÃ³picos, cÃ¡lculo com apoio ou registro em dupla.",
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
        "Utilizar exemplos de comprovantes, garantias, direitos e cuidados de seguranÃ§a com linguagem acessÃ­vel.",
        "Registrar no quadro palavras-chave e procedimentos de proteÃ§Ã£o para orientar a anÃ¡lise das situaÃ§Ãµes.",
        "Realizar leitura mediada dos enunciados e apoiar estudantes com dificuldade na interpretaÃ§Ã£o dos direitos e responsabilidades.",
    ],
    "instituicoes_financeiras": [
        "Explicar funÃ§Ãµes de instituiÃ§Ãµes financeiras com exemplos concretos e vocabulÃ¡rio acessÃ­vel, como banco, conta, cartÃ£o e seguranÃ§a.",
        "Organizar comparaÃ§Ãµes em lista ou quadro para diferenciar formas de guardar, movimentar e proteger o dinheiro.",
        "Oferecer apoio individual durante a leitura e a organizaÃ§Ã£o das respostas sobre serviÃ§os financeiros.",
    ],
}


_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO = {
    "autoconhecimento": [
        "Promover ambiente acolhedor, com combinados de escuta e respeito, para que os estudantes participem sem exposiÃ§Ã£o excessiva de vivÃªncias pessoais.",
        "Oferecer modelo estruturado do mapa com campos prÃ©-definidos para alunos que precisam de mais apoio para organizar as ideias visualmente.",
        "Garantir que a atividade de compartilhamento em duplas seja feita com colega escolhido pelo prÃ³prio aluno, respeitando vÃ­nculos de confianÃ§a.",
    ],
    "futureme": [
        "Providenciar dispositivo individual para alunos sem acesso a celular, garantindo que todos possam usar a plataforma sem depender de compartilhamento.",
        "Permitir que alunos que nÃ£o se sintam confortÃ¡veis em cadastrar informaÃ§Ãµes pessoais preencham apenas os campos obrigatÃ³rios.",
        "Oferecer versÃ£o impressa do questionÃ¡rio para alunos com dificuldade de navegaÃ§Ã£o digital, garantindo a mesma experiÃªncia de reflexÃ£o.",
    ],
    "producao_coletiva": [
        "Garantir que alunos com dificuldade motora ou de escrita assumam funÃ§Ãµes de coordenaÃ§Ã£o, fala ou organizaÃ§Ã£o no grupo, sem ficarem excluÃ­dos da produÃ§Ã£o.",
        "Oferecer modelo simplificado do produto (biomapa, campanha) para grupos com dificuldade de organizaÃ§Ã£o, com campos prÃ©-definidos para preenchimento.",
        "Permitir que grupos sem acesso a celular realizem a apresentaÃ§Ã£o ao vivo ou leiam o roteiro em voz alta, garantindo a mesma qualidade de participaÃ§Ã£o.",
    ],
    "convivencia": [
        "Garantir que alunos mais tÃ­midos ou com dificuldade de expressÃ£o oral possam contribuir por escrito, entregando sua proposta ao secretÃ¡rio do cÃ­rculo.",
        "Oferecer roteiro de perguntas-guia para alunos que precisam de mais estrutura para participar do debate, sem expÃ´-los desnecessariamente.",
        "Permitir que alunos que nÃ£o se sintam confortÃ¡veis com o dilema escolhido pela turma registrem sua perspectiva individualmente no caderno.",
    ],
    "consciencia_social": [
        "Conduzir a dinÃ¢mica da Caminhada do PrivilÃ©gio sem obrigar nenhum aluno a participar â€” oferecer a opÃ§Ã£o de observar e registrar as percepÃ§Ãµes por escrito.",
        "Garantir que a discussÃ£o sobre desigualdades nÃ£o exponha situaÃ§Ãµes pessoais de vulnerabilidade â€” manter o foco em grupos sociais, nÃ£o em indivÃ­duos.",
        "Oferecer roteiro de anÃ¡lise com perguntas-guia para alunos que precisam de mais estrutura para identificar padrÃµes de representaÃ§Ã£o no ambiente digital.",
    ],
    "encerramento": [
        "Permitir que alunos que nÃ£o se sintam confortÃ¡veis com o ritual simbÃ³lico coletivo registrem suas palavras/compromissos individualmente no caderno.",
        "Oferecer perguntas-guia simplificadas para alunos com dificuldade de sÃ­ntese, ajudando-os a identificar pelo menos uma descoberta e uma mudanÃ§a de atitude.",
        "Garantir que alunos sem acesso a celular participem da produÃ§Ã£o final (vÃ­deo) por meio de apresentaÃ§Ã£o ao vivo ou leitura do roteiro, com o mesmo valor.",
    ],
}


class GeradorAcessibilidade:
    """Gera estratÃ©gias de acessibilidade contextualizadas por tipo de recurso."""

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

        Se recursos_detectados estiver disponÃ­vel, seleciona estratÃ©gias
        especÃ­ficas do catÃ¡logo. Caso contrÃ¡rio, usa fallback por perfil.
        """
        # SÃ³ tenta detectar pelo texto gerado quando nenhum recurso veio do PDF.
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

        # EstratÃ©gia: selecionar dos catÃ¡logos por recurso
        if recursos_detectados:
            itens = self._selecionar_por_recursos(recursos_detectados, indice_aula, tema)
            if len(itens) >= 3:
                return itens[:3]

        # Fallback: usar catÃ¡logo por perfil
        fallback = _FALLBACK_POR_PERFIL.get(perfil, [])
        if fallback:
            return list(fallback)

        # Fallback final genÃ©rico
        base_texto = normalizar_texto(f"{tema} {aprendizagem} {desenvolvimento}")
        if contem_termos(base_texto, ["imagem", "grafico", "mapa", "tabela", "esquema", "anuncio"]):
            primeiro = "Utilizar recursos visuais, exemplos concretos e mediaÃ§Ã£o oral para favorecer a compreensÃ£o do conteÃºdo e das atividades propostas."
        else:
            primeiro = "Apresentar o conteÃºdo com linguagem clara, exemplos comentados e retomadas frequentes dos pontos essenciais."

        if contem_termos(base_texto, ["leitura", "texto", "fonte", "noticia", "conto", "documento"]):
            segundo = "Realizar leitura guiada com pausas para explicar vocabulÃ¡rio, informaÃ§Ãµes centrais e comandos necessÃ¡rios Ã  participaÃ§Ã£o na aula."
        else:
            segundo = "Explicar as atividades passo a passo, com apoio visual e perguntas orientadoras para apoiar diferentes ritmos de aprendizagem."

        return [
            primeiro,
            segundo,
            "Oferecer mediaÃ§Ã£o individual, tempo ampliado quando necessÃ¡rio e diferentes formas de registro para apoiar a participaÃ§Ã£o de todos os estudantes.",
        ]

    def _selecionar_por_recursos(
        self, recursos: list[str], indice_aula: int, tema: str
    ) -> list[str]:
        """Seleciona estratÃ©gias do catÃ¡logo baseado nos recursos detectados."""
        itens_selecionados = []
        recursos_usados = set()

        for recurso in recursos:
            if recurso in recursos_usados:
                continue
            estrategias = CATALOGO_ESTRATEGIAS.get(recurso, [])
            if not estrategias:
                continue

            # Seleciona uma estratÃ©gia com variaÃ§Ã£o pelo Ã­ndice da aula
            idx = _indice_hash([recurso, tema, str(indice_aula)], len(estrategias))
            itens_selecionados.append(estrategias[idx])
            recursos_usados.add(recurso)

            if len(itens_selecionados) >= 3:
                break

        # Se nÃ£o completou 3, adiciona estratÃ©gia genÃ©rica de mediaÃ§Ã£o
        while len(itens_selecionados) < 3:
            genericas = [
                "Oferecer mediaÃ§Ã£o individual durante as atividades, adequando explicaÃ§Ãµes, tempo e forma de resposta conforme as necessidades da turma.",
                "Utilizar apoio visual, retomadas coletivas e registros orientados para favorecer a compreensÃ£o dos conceitos trabalhados.",
                "Organizar intervenÃ§Ãµes com exemplos comentados e acompanhamento prÃ³ximo para apoiar estudantes com dificuldades de leitura, interpretaÃ§Ã£o ou organizaÃ§Ã£o das tarefas.",
            ]
            idx_gen = len(itens_selecionados) % len(genericas)
            itens_selecionados.append(genericas[idx_gen])

        return itens_selecionados


# â”€â”€ InstÃ¢ncia global e funÃ§Ã£o de conveniÃªncia â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_gerador = GeradorAcessibilidade()



def _limitar_itens(itens: list[str], minimo: int = 2, maximo: int = 3) -> list[str]:
    saida = []
    for texto in itens or []:
        txt = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip())
        if not txt:
            continue
        if len(txt) > 220:
            txt = limitar_texto_natural(txt, 220)
        txt = re.sub(r"^[^\w(]+", "", txt)
        txt = f"\u2611 {txt}"
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
    CompatÃ­vel com a assinatura de gerar_acessibilidade_dinamica() do avaliacao.py,
    mas com seleÃ§Ã£o por tipo de recurso e variaÃ§Ã£o sequencial.
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

