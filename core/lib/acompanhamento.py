"""
Compositor de acompanhamento da aprendizagem por camadas.

Gera textos de acompanhamento contextualizados por:
1. Perfil disciplinar
2. Tipo de aula
3. Etapas da metodologia
4. Habilidade BNCC (quando disponível)
5. Variação sequencial (posição da aula na sequência)
"""

import re
from core.lib.classificador import normalizar_texto, contem_termos
from core.lib.progressao import verbo_observacao, verbo_verificacao, verbo_acompanhamento, conector_progressao
from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural


# ── Frases-base por perfil disciplinar e tipo de aula ──────────────────────

_ACOMPANHAMENTO_POR_PERFIL_TIPO = {
    "matematica": {
        "verificacao": [
            "☑ Observar se os estudantes demonstram autonomia na resolução das atividades, aplicando corretamente os conceitos trabalhados no bloco.",
            "☑ Verificar se a turma consegue justificar as estratégias escolhidas e interpretar os resultados obtidos.",
            "☑ Acompanhar se os estudantes identificam e corrigem erros no próprio raciocínio durante a atividade.",
        ],
        "khan": [
            "☑ Observar se os estudantes demonstram autonomia na resolução das atividades, aplicando corretamente os conceitos trabalhados no bloco.",
            "☑ Verificar se a turma consegue justificar as estratégias escolhidas e interpretar os resultados obtidos.",
            "☑ Acompanhar se os estudantes identificam e corrigem erros no próprio raciocínio durante a atividade.",
        ],
        "modelagem": [
            "☑ Verificar se os estudantes identificam corretamente os dados necessários e compreendem o que está sendo pedido em cada situação.",
            "☑ Acompanhar se a turma reconhece a relação entre o resultado obtido e o contexto da situação estudada, evitando respostas apenas numéricas.",
            "☑ Conferir se os registros finais articulam cálculo, interpretação e conclusão, demonstrando compreensão do conceito trabalhado.",
        ],
        "grafico": [
            "☑ Verificar se os estudantes interpretam corretamente os dados, eixos, valores e informações apresentadas em gráficos ou tabelas do material.",
            "☑ Acompanhar se a turma utiliza os dados do material para sustentar respostas, evitando conclusões sem evidências.",
            "☑ Observar se conseguem relacionar a representação gráfica ao contexto real da situação estudada.",
        ],
        "resolucao_problemas": [
            "☑ Verificar se os estudantes aplicam as etapas do método de resolução: compreender, planejar, executar e verificar.",
            "☑ Acompanhar se a turma justifica a estratégia escolhida e verifica se o resultado faz sentido no contexto do problema.",
            "☑ Observar se os estudantes conseguem resolver problemas variados, transferindo o raciocínio para situações novas.",
        ],
        "_default": [
            "☑ Verificar se os estudantes identificam corretamente os dados necessários e compreendem o que está sendo pedido em cada situação.",
            "☑ Acompanhar se a turma reconhece a relação entre o resultado obtido e o contexto da situação estudada, evitando respostas apenas numéricas.",
            "☑ Conferir se os registros finais articulam cálculo, interpretação e conclusão, demonstrando compreensão do conceito trabalhado.",
        ],
    },
    "lingua_portuguesa_ef": {
        "producao": [
            "{v_obs} como os estudantes planejam, revisam e ajustam a produção textual, considerando gênero, finalidade comunicativa e organização das ideias.",
            "{v_ver} se os estudantes incorporam as orientações discutidas na aula para qualificar clareza, coerência e adequação linguística.",
            "{v_acomp} os registros produzidos, considerando avanços entre rascunho, revisão e versão final, bem como a autonomia no uso dos critérios trabalhados.",
        ],
        "argumentacao": [
            "{v_obs} a participação dos estudantes nas discussões, considerando a escuta, a formulação de posicionamentos e o uso de argumentos consistentes.",
            "{v_ver} se os estudantes identificam tese, argumentos e recursos persuasivos nos textos e interações analisados.",
            "{v_acomp} se os registros e respostas evidenciam clareza de posicionamento, justificativa e respeito às diferentes perspectivas.",
        ],
        "_default": [
            "{v_obs} se os estudantes compreendem as ideias centrais de {tema} e reconhecem os elementos textuais ou linguísticos em foco.",
            "{v_ver} a participação nas leituras, análises, discussões e registros, considerando interpretação, argumentação e ampliação de repertório.",
            "{v_acomp} se os estudantes aplicam as estratégias de leitura, análise da linguagem ou produção de sentidos com autonomia crescente.",
        ],
    },
    "lingua_portuguesa_em": {
        "_default": [
            "{v_obs} se os estudantes compreendem as ideias centrais de {tema} e reconhecem os elementos textuais ou linguísticos em foco.",
            "{v_ver} a participação nas leituras, análises, discussões e registros, considerando interpretação, argumentação e ampliação de repertório.",
            "{v_acomp} se os estudantes aplicam as estratégias de leitura, análise da linguagem ou produção de sentidos com autonomia crescente.",
        ],
    },
    "leitura_redacao": {
        "_default": [
            "{v_obs} se os estudantes compreendem as ideias centrais de {tema} e reconhecem os elementos textuais ou linguísticos em foco.",
            "{v_ver} a participação nas leituras, análises, discussões e registros, considerando interpretação, argumentação e ampliação de repertório.",
            "{v_acomp} se os estudantes aplicam as estratégias de leitura, análise da linguagem ou produção de sentidos com autonomia crescente.",
        ],
    },
    "orientacao_estudos": {
        "_default": [
            "{v_obs} se os estudantes utilizam as estratégias de organização, leitura, retomada e planejamento propostas durante a aula.",
            "{v_ver} se os estudantes conseguem identificar dificuldades, selecionar procedimentos de estudo e explicar como podem aplicá-los em outras situações.",
            "{v_acomp} os registros produzidos, considerando autonomia, constância e capacidade de monitorar o próprio processo de aprendizagem.",
        ],
    },
    "ciencias_ef": {
        "_default": [
            "{v_obs} se os estudantes relacionam {tema} aos conceitos científicos trabalhados e utilizam evidências para sustentar suas respostas.",
            "{v_ver} a participação nas investigações, discussões, registros e socializações, considerando clareza de hipóteses e explicações.",
            "{v_acomp} se os estudantes interpretam fenômenos, dados, experimentos ou representações com base nos conceitos desenvolvidos na aula.",
        ],
    },
    "biologia": {
        "_default": [
            "{v_obs} se os estudantes relacionam fenômenos biológicos e ambientais, utilizando conceitos científicos para explicar causas, efeitos e interdependências.",
            "{v_ver} se os estudantes interpretam dados, imagens, esquemas ou situações-problema com base nas evidências discutidas na aula.",
            "{v_acomp} se os registros mostram uso progressivo do vocabulário científico e capacidade de justificar posições e soluções.",
        ],
    },
    "quimica": {
        "_default": [
            "{v_obs} se os estudantes identificam evidências, transformações e relações entre substâncias, materiais ou processos químicos em estudo.",
            "{v_ver} se os estudantes organizam informações, analisam representações e explicam resultados utilizando conceitos e linguagem adequados.",
            "{v_acomp} se os estudantes conseguem aplicar os conhecimentos trabalhados para interpretar fenômenos, comparar situações e justificar conclusões.",
        ],
    },
    "fisica": {
        "_default": [
            "{v_obs} se os estudantes identificam grandezas, variáveis e relações físicas envolvidas nas situações analisadas na aula.",
            "{v_ver} se os estudantes interpretam esquemas, gráficos, experimentos ou problemas, articulando conceitos e evidências.",
            "{v_acomp} se os estudantes explicam procedimentos, analisam resultados e utilizam os conceitos físicos para justificar suas respostas.",
        ],
    },
    "historia": {
        "_default": [
            "{v_obs} se os estudantes identificam sujeitos, contextos, permanências, mudanças e relações temporais nas fontes e situações estudadas.",
            "{v_ver} se os estudantes utilizam evidências históricas para interpretar acontecimentos, comparar perspectivas e sustentar explicações.",
            "{v_acomp} os registros e respostas, considerando vocabulário histórico, organização das ideias e progressiva autonomia de análise.",
        ],
    },
    "geografia": {
        "_default": [
            "{v_obs} se os estudantes interpretam paisagens, mapas, gráficos, tabelas e outras linguagens geográficas com atenção aos conceitos em foco.",
            "{v_ver} se os estudantes relacionam território, sociedade, natureza e escalas de análise nas situações discutidas ao longo da aula.",
            "{v_acomp} os registros produzidos, considerando clareza na leitura de dados, argumentação e aplicação dos conceitos trabalhados.",
        ],
    },
    "ingles": {
        "_default": [
            "{v_obs} se os estudantes compreendem vocabulário, estruturas e comandos em língua inglesa nas atividades propostas.",
            "{v_ver} se os estudantes participam das práticas de leitura, escuta, oralidade e escrita com apoio progressivamente mais autônomo.",
            "{v_acomp} se os registros e interações evidenciam uso contextualizado da língua, ampliação de repertório e compreensão do tema estudado.",
        ],
    },
    "arte": {
        "_default": [
            "{v_obs} se os estudantes participam das práticas de apreciação, experimentação, criação e análise propostas durante a aula.",
            "{v_ver} se os estudantes reconhecem elementos, linguagens, procedimentos e intencionalidades presentes nas produções artísticas estudadas.",
            "{v_acomp} se os registros e produções revelam ampliação de repertório, argumentação sensível e uso de referências discutidas coletivamente.",
        ],
    },
    "projeto_de_vida": {
        "autoconhecimento": [
            "{v_obs} se o estudante identifica pelo menos três possibilidades de futuro conectadas aos seus interesses e valores, com justificativa para cada escolha.",
            "{v_ver} se o estudante reconhece fatores externos (contexto social, oportunidades, imprevistos) que influenciam suas escolhas, sem se limitar à vontade individual.",
            "{v_acomp} a qualidade da troca em duplas, avaliando se o estudante escuta ativamente o colega e oferece sugestões pertinentes ao projeto de vida do outro.",
        ],
        "futureme": [
            "{v_obs} se o estudante completa o questionário da plataforma com autenticidade, respondendo com base em suas preferências reais, sem buscar ‘a resposta certa’.",
            "{v_ver} se o estudante interpreta o relatório de forma crítica, identificando o que faz sentido e o que não se alinha à sua experiência, sem aceitar passivamente o resultado.",
            "{v_acomp} a troca em duplas/trios, avaliando se o estudante conecta os resultados da plataforma a situações concretas do cotidiano escolar e pessoal.",
        ],
        "producao_coletiva": [
            "{v_obs} se o grupo elabora um produto concreto (biomapa, campanha, vídeo) com elementos claros: objetivo, mensagem, público-alvo e estratégia de ação.",
            "{v_ver} se todos os integrantes do grupo participam ativamente da produção, com funções definidas e contribuições visíveis.",
            "{v_acomp} a apresentação do produto, avaliando se o grupo consegue explicar as escolhas feitas e conectá-las ao tema do bimestre.",
        ],
        "convivencia": [
            "{v_obs} se o estudante participa do Círculo de Convivência com escuta ativa, respeitando os acordos de fala e sem interromper os colegas.",
            "{v_ver} se o estudante contribui com pelo menos uma proposta de solução para o dilema discutido, justificando com base nos efeitos para o grupo.",
            "{v_acomp} o registro individual do compromisso, avaliando se o estudante identifica uma ação concreta que pode realizar para colocar a decisão coletiva em prática.",
        ],
        "consciencia_social": [
            "{v_obs} se o estudante reconhece a diferença entre privilégios e desvantagens como condições estruturais, e não apenas como resultado do esforço individual.",
            "{v_ver} se o estudante identifica, no ambiente digital e na mídia, padrões de representação que privilegiam certos perfis e invisibilizam outros.",
            "{v_acomp} o registro individual, avaliando se o estudante indica mudanças concretas em sua forma de agir ao reconhecer desigualdades.",
        ],
        "encerramento": [
            "{v_obs} se o estudante identifica pelo menos uma descoberta significativa sobre si mesmo ao longo do bimestre, conectando-a a situações concretas vividas nas aulas.",
            "{v_ver} se o estudante consegue nomear uma mudança no modo de agir, sentir ou ver o mundo a partir dos aprendizados do bimestre.",
            "{v_acomp} a participação no ritual simbólico de encerramento, avaliando se o estudante escolhe palavras/compromissos que refletem os temas trabalhados.",
        ],
        "_default": [
            "{v_obs} a participação dos estudantes nas reflexões e interações propostas, considerando escuta, respeito, cooperação e elaboração de ideias.",
            "{v_ver} se os estudantes relacionam o tema da aula a escolhas, atitudes, estratégias de convivência e planejamento pessoal ou coletivo.",
            "{v_acomp} os registros produzidos, valorizando argumentação, consciência crítica e apropriação dos conceitos sem exigir exposição excessiva.",
        ],
    },
    "lideranca_oratoria": {
        "_default": [
            "{v_obs} a participação dos estudantes nas reflexões e interações propostas, considerando escuta, respeito, cooperação e elaboração de ideias.",
            "{v_ver} se os estudantes relacionam o tema da aula a escolhas, atitudes, estratégias de convivência e planejamento pessoal ou coletivo.",
            "{v_acomp} os registros produzidos, valorizando argumentação, consciência crítica e apropriação dos conceitos sem exigir exposição excessiva.",
        ],
    },
    "educacao_financeira": {
        "orcamento_planejamento": [
            "{v_obs} se os estudantes identificam receitas, despesas, prioridades e metas em situações de organização financeira.",
            "{v_ver} se os estudantes elaboram ou analisam o orçamento simulado com critérios claros, relacionando escolhas, limites e saldo.",
            "{v_acomp} se os registros mostram compreensão progressiva sobre planejamento, controle de gastos e tomada de decisão responsável.",
        ],
        "consumo_consciente": [
            "{v_obs} se os estudantes diferenciam necessidade, desejo, prioridade e custo-benefício nas situações de consumo analisadas.",
            "{v_ver} se os estudantes justificam escolhas de consumo com base em dados, consequências e critérios construídos na aula.",
            "{v_acomp} se os registros evidenciam postura crítica sem julgamento moralista sobre hábitos pessoais ou familiares.",
        ],
        "investimento_poupanca": [
            "{v_obs} se os estudantes compreendem a função da poupança, da reserva de emergência e do planejamento de metas.",
            "{v_ver} se os estudantes interpretam valores, rendimentos, prazos ou cenários de acumulação, justificando decisões com coerência.",
            "{v_acomp} se os registros relacionam constância, objetivo financeiro, imprevistos e uso responsável dos recursos.",
        ],
        "credito_endividamento": [
            "{v_obs} se os estudantes reconhecem juros, parcelas, custo total e riscos envolvidos no uso de crédito.",
            "{v_ver} se os estudantes comparam alternativas de pagamento e justificam quando o crédito pode ser vantajoso ou arriscado.",
            "{v_acomp} se os cálculos e registros mostram compreensão sobre endividamento, planejamento e uso responsável do crédito.",
        ],
        "empreendedorismo": [
            "{v_obs} se os estudantes identificam custos, preço, público, recursos necessários e viabilidade em propostas empreendedoras simples.",
            "{v_ver} se os estudantes justificam decisões do projeto com base em planejamento, responsabilidade e análise do contexto.",
            "{v_acomp} se os registros mostram articulação entre ideia, necessidade, produto ou serviço e organização financeira.",
        ],
        "analise_percentuais_noticias": [
            "{v_obs} se os estudantes identificam percentuais, valores de referencia e comparacoes presentes nas noticias analisadas.",
            "{v_ver} se os estudantes interpretam tabelas, graficos ou manchetes numericas sem se limitar a localizar dados soltos.",
            "{v_acomp} se os registros mostram relacao entre o calculo realizado e o sentido da informacao apresentada na noticia.",
        ],
        "governo_economia": [
            "{v_obs} se os estudantes reconhecem situacoes em que a acao do governo interfere em precos, servicos ou circulacao de recursos.",
            "{v_ver} se os estudantes relacionam exemplos discutidos em aula a ideias de arrecadacao, regulacao e impacto coletivo.",
            "{v_acomp} se os registros mostram compreensao progressiva sobre a relacao entre economia, direitos e organizacao da vida social.",
        ],
        "impacto_decisoes_economicas": [
            "{v_obs} se os estudantes analisam como escolhas economicas afetam consumo, prioridades e planejamento do cotidiano.",
            "{v_ver} se os estudantes comparam alternativas e justificam decisões com base em consequencias e criterios objetivos.",
            "{v_acomp} se os registros mostram relacao entre recursos disponiveis, metas e impactos das escolhas feitas.",
        ],
        "cidadania_financeira": [
            "{v_obs} se os estudantes reconhecem direitos, responsabilidades e formas de proteção em situações de consumo.",
            "{v_ver} se os estudantes analisam comprovantes, garantias, segurança e critérios de escolha em serviços ou compras.",
            "{v_acomp} se as respostas indicam autonomia para tomar decisões financeiras mais seguras e conscientes.",
        ],
        "instituicoes_financeiras": [
            "{v_obs} se os estudantes reconhecem a função das instituições financeiras na guarda, movimentação e proteção do dinheiro.",
            "{v_ver} se os estudantes comparam serviços financeiros, identificando possibilidades, cuidados e critérios de segurança.",
            "{v_acomp} se os registros relacionam instituição financeira, organização dos recursos e escolhas responsáveis.",
        ],
        "_default": [
            "{v_obs} se os estudantes analisam situações de consumo, orçamento, planejamento e tomada de decisão com base em critérios claros.",
            "{v_ver} se os estudantes interpretam cálculos, dados e cenários financeiros, justificando escolhas e prioridades com coerência.",
            "{v_acomp} se os registros mostram compreensão progressiva das relações entre objetivos, recursos, limites e consequências das decisões.",
        ],
    },
    "tecnologia_inovacao": {
        "dispositivos_entrada_saida": [
            "{v_ver} se os estudantes diferenciam dispositivos de entrada e de saida, classificando corretamente os equipamentos apresentados.",
            "{v_obs} se conseguem justificar a funcao de teclado, mouse, camera, microfone, monitor, impressora, projetor e caixa de som nas atividades propostas.",
            "{v_acomp} os registros produzidos em esquemas, colunas, listas ou respostas orais, considerando clareza e compreensao do funcionamento dos dispositivos.",
        ],
        "programacao_inicial": [
            "{v_ver} se os estudantes reconhecem as principais teclas e comandos utilizados na atividade digital proposta.",
            "{v_obs} se seguem a sequencia de blocos, eventos ou instrucoes com autonomia progressiva durante a construcao da atividade.",
            "{v_acomp} se os registros e producoes evidenciam compreensao sobre teclado, bandeira verde, bloco diga e organizacao dos comandos no ambiente de programacao.",
        ],
        "cultura_digital": [
            "{v_ver} se os estudantes identificam comportamentos respeitosos e inadequados nas interacoes digitais analisadas.",
            "{v_obs} a participacao nas discussoes sobre respeito, etica, emocoes e convivencia online, considerando a capacidade de justificar as respostas.",
            "{v_acomp} se os registros e propostas de regras demonstram compreensao sobre responsabilidade digital, empatia e cuidado nas interacoes virtuais.",
        ],
        "comunicacao_digital": [
            "{v_ver} se os estudantes reconhecem perguntas confusas, incompletas ou pouco objetivas em mensagens e foruns.",
            "{v_obs} se reescrevem mensagens com clareza, respeito e informacoes suficientes para solicitar ajuda ou explicar um problema.",
            "{v_acomp} os registros produzidos, considerando organizacao das ideias, objetividade e uso adequado das estrategias de comunicacao trabalhadas na aula.",
        ],
        "consumo_tecnologia": [
            "{v_ver} se os estudantes compreendem o conceito de obsolescencia programada e relacionam o tema ao descarte e ao consumo de tecnologia.",
            "{v_obs} se conectam consumo excessivo, lixo eletronico e impactos ambientais nas discussoes e atividades realizadas.",
            "{v_acomp} as propostas de campanha, listas ou orientacoes produzidas pela turma, considerando viabilidade, consciencia ambiental e clareza das ideias.",
        ],
        "_default": [
            "{v_obs} se os estudantes compreendem os conceitos centrais relacionados a {tema} e participam das atividades de análise, discussão e registro.",
            "{v_ver} se articulam o tema estudado a situações do cotidiano, usos da tecnologia e formas de resolver problemas ou se comunicar melhor.",
            "{v_acomp} os registros produzidos, considerando clareza de ideias, autonomia crescente e aplicação prática do conhecimento trabalhado.",
        ],
    },
    "sociologia": {
        "_default": [
            "{v_obs} se os estudantes compreendem os conceitos centrais relacionados a {tema} e participam das atividades de análise, discussão e registro.",
            "{v_ver} se os estudantes articulam o tema estudado a situações do cotidiano, contextos sociais ou usos práticos do conhecimento.",
            "{v_acomp} os registros produzidos, considerando clareza de ideias, argumentação e autonomia crescente nas respostas.",
        ],
    },
}

# ── Conectores com etapas da metodologia ───────────────────────────────────

_CONECTORES_ETAPAS = {
    "para comecar": "nas trocas iniciais e no levantamento de conhecimentos prévios",
    "relembre": "na retomada dos conceitos trabalhados anteriormente",
    "foco no conteudo": "durante a explicação e a análise do conteúdo central",
    "na pratica": "na resolução das atividades propostas e nos registros individuais",
    "pause e responda": "durante a verificação e a correção dialogada",
    "encerramento": "na síntese final e nos registros de fechamento",
    "leitura e construcao do conteudo": "durante a leitura guiada e a construção coletiva do conteúdo",
    "contextualizacao": "durante a contextualização e a mobilização de repertórios",
    "leitura analitica": "na análise dos textos, imagens e recursos apresentados",
    "sistematizacao": "na sistematização dos conceitos e registros construídos",
}

_PRIORIDADE_ETAPA = [
    "na pratica",
    "atividade",
    "producao textual",
    "calculos financeiros",
    "analise de caso",
    "foco no conteudo",
    "leitura analitica",
    "encerramento",
    "para comecar",
]


def _etapa_principal(etapas: list[str] | None) -> str:
    etapas_norm = [normalizar_texto(etapa) for etapa in list(etapas or []) if str(etapa or "").strip()]
    for prioridade in _PRIORIDADE_ETAPA:
        if prioridade in etapas_norm:
            return prioridade
    return etapas_norm[0] if etapas_norm else ""


class CompositorAcompanhamento:
    """Motor de composição de acompanhamento por camadas."""

    def compor(
        self,
        perfil: str,
        tipo: str,
        tema: str,
        habilidade: str = "",
        etapas_metodologia: list[str] | None = None,
        indice_aula: int = 0,
        disciplina: str = "",
        aprendizagem: str = "",
        desenvolvimento: str = "",
    ) -> list[str]:
        """
        Compõe 3 itens de acompanhamento da aprendizagem, customizados por camadas.

        Args:
            perfil: perfil disciplinar (ex: 'matematica', 'lingua_portuguesa_ef')
            tipo: tipo de aula (ex: 'leitura', 'producao', 'resolucao_problemas')
            tema: tema da aula
            habilidade: habilidade BNCC extraída, se disponível
            etapas_metodologia: lista de títulos de etapas na metodologia
            indice_aula: posição da aula na sequência (0-based)
            disciplina: nome da disciplina (fallback)
            aprendizagem: texto de aprendizagem
            desenvolvimento: texto de desenvolvimento/metodologia
        """
        # Camada 1: Selecionar base pelo perfil + tipo
        perfis_lp = {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}
        perfil_lookup = perfil
        if perfil in perfis_lp and perfil not in _ACOMPANHAMENTO_POR_PERFIL_TIPO:
            perfil_lookup = "lingua_portuguesa_ef"

        grupo = _ACOMPANHAMENTO_POR_PERFIL_TIPO.get(perfil_lookup, {})
        templates = grupo.get(tipo, grupo.get("_default", []))
        if not templates:
            templates = [
                "{v_obs} se os estudantes compreendem os conceitos centrais relacionados a {tema} {conector}.",
                "{v_ver} a participação, os registros produzidos e a forma como os estudantes justificam suas respostas ao longo da aula.",
                "{v_acomp} se os estudantes conseguem aplicar os conhecimentos trabalhados com autonomia progressiva nas atividades orientadas.",
            ]

        # Camada 2: Resolver verbos com variação por posição
        v_obs = verbo_observacao(indice_aula, tema)
        v_ver = verbo_verificacao(indice_aula, tema)
        v_acomp = verbo_acompanhamento(indice_aula, tema)
        conector = conector_progressao(indice_aula)

        itens = []
        for template in templates:
            texto = template.format(
                v_obs=v_obs,
                v_ver=v_ver,
                v_acomp=v_acomp,
                tema=tema,
                conector=conector,
            )
            itens.append(texto)

        # Camada 3: Enriquecer com referência à etapa da metodologia
        if etapas_metodologia:
            etapa_principal = _etapa_principal(etapas_metodologia)
            conector_etapa = _CONECTORES_ETAPAS.get(etapa_principal, "")
            if conector_etapa and len(itens) >= 2:
                # Enriquece o segundo item com referência à etapa
                item_enriquecido = itens[1]
                if not any(c in item_enriquecido.lower() for c in ["nas trocas", "na retomada", "durante a"]):
                    item_enriquecido = item_enriquecido.rstrip(".")
                    item_enriquecido += f", especialmente {conector_etapa}."
                    itens[1] = item_enriquecido

        # Camada 4: Incorporar referência à habilidade BNCC
        if habilidade and len(habilidade) > 10:
            codigo_match = re.search(r'((?:EM|EF)\d{2}[A-Z]{2}\d{2}[A-Z]?)', habilidade, re.I)
            if codigo_match:
                codigo = codigo_match.group(1).upper()
                if len(itens) >= 1:
                    itens[0] = itens[0].rstrip(".")
                    itens[0] += f", em articulação com a habilidade ({codigo})."

        return itens


# ── Instância global para uso direto ────────────────────────────────────────

_compositor = CompositorAcompanhamento()


def _tem_marcador_visao(base: str) -> bool:
    return bool(
        re.search(
            r"\b(?:olho|retina|cornea|pupila|cristalino|sistema visual|formacao da imagem|caminho da luz|visao)\b",
            base,
            flags=re.I,
        )
    )


def _tem_marcador_audicao(base: str) -> bool:
    return bool(
        re.search(
            r"\b(?:audicao|ouvido|decibel|decibeis|poluicao sonora|caminho do som|sistema auditivo)\b",
            base,
            flags=re.I,
        )
    )


def _acompanhamento_especifico_por_aula(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))
    if _tem_marcador_visao(base):
        return [
            "Verificar se os estudantes identificam corretamente as estruturas do olho no esquema proposto.",
            "Observar se explicam, com linguagem científica, o caminho da luz até a formação da imagem.",
            "Conferir se os registros (legenda ou síntese) mantêm correspondência entre estrutura e função.",
        ]
    if _tem_marcador_audicao(base):
        return [
            "Verificar se os estudantes descrevem o caminho do som e relacionam partes do sistema auditivo às funções.",
            "Observar se conectam nível de decibéis, riscos à audição e impactos da poluição sonora.",
            "Conferir se o resumo final apresenta medidas coerentes de prevenção e proteção auditiva.",
        ]
    if any(k in base for k in ["sistema respiratorio", "hematose", "ventilacao pulmonar", "pulmao"]):
        return [
            "Verificar se os estudantes classificam os órgãos do sistema respiratório por localização e função.",
            "Observar se explicam ventilação pulmonar e hematose com sequência lógica.",
            "Conferir se os registros em tabela ou síntese usam os conceitos centrais da aula.",
        ]
    if "tabela" in base:
        return [
            "Verificar se os estudantes preenchem a tabela com informações corretas e completas.",
            "Observar se relacionam os dados da tabela aos conceitos discutidos na aula.",
            "Conferir se justificam oralmente ou por escrito as escolhas registradas na atividade.",
        ]
    return []


def _acompanhamento_lingua_portuguesa(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["trilha", "alice no pais das maravilhas", "pequeno principe", "peter pan", "leitura compartilhada", "predicao guiada"]):
        return [
            "Observar se os estudantes participam das discussões e compartilham impressões sobre a narrativa lida.",
            "Verificar a compreensão dos acontecimentos, personagens e conflitos presentes no trecho trabalhado.",
            "Acompanhar os registros orais e escritos produzidos durante as atividades de leitura e interpretação.",
        ]

    if any(k in base for k in ["versao final", "redacao paulista", "revisao orientada", "reescrita", "rascunho"]):
        return [
            "Verificar se os estudantes revisam e reorganizam o texto considerando clareza, sequência das ideias e adequação ao gênero trabalhado.",
            "Observar a participação durante os momentos de revisão, correção e reescrita da produção textual.",
            "Acompanhar se os estudantes conseguem identificar ajustes necessários antes da versão final e do envio da atividade.",
        ]

    if "verbo haver" in base or re.search(r"\bhaver\b", base):
        return [
            "Verificar se os estudantes identificam o uso do verbo haver nas situações propostas.",
            "Observar a aplicação correta das regras discutidas durante as atividades.",
            "Acompanhar a participação nas correções coletivas e nas atividades em dupla.",
        ]

    if "tirinha" in base and any(k in base for k in ["humor", "critica", "conflito", "linguagem mista"]):
        return [
            "Observar se os estudantes identificam elementos de humor, crítica e conflito nas tirinhas trabalhadas.",
            "Verificar a participação nas discussões e a capacidade de explicar sentidos da linguagem verbal e não verbal.",
            "Acompanhar os registros produzidos durante as atividades e retomadas coletivas.",
        ]

    if any(k in base for k in ["figura de linguagem", "figuras de linguagem", "imperativo"]) and any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario"]):
        return [
            "Observar se os estudantes reconhecem figuras de linguagem e estratégias persuasivas nos anúncios.",
            "Verificar a compreensão sobre o uso do imperativo na publicidade.",
            "Acompanhar os registros individuais produzidos durante as análises.",
        ]

    if any(k in base for k in ["metafora", "metaforas"]) and any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario"]):
        return [
            "Verificar se os estudantes identificam metáforas visuais e verbais nos anúncios.",
            "Observar como relacionam imagens, palavras e sentidos produzidos na publicidade.",
            "Acompanhar a participação nas atividades em grupo e socialização das respostas.",
        ]

    if any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario", "propaganda", "slogan"]):
        return [
            "Observar se os estudantes reconhecem elementos verbais e visuais dos anúncios.",
            "Verificar a participação nas análises e discussões sobre estratégias publicitárias.",
            "Acompanhar os registros produzidos nas atividades de interpretação.",
        ]

    if any(k in base for k in ["carta de reclamacao", "reclamar por escrito", "texto reivindicatorio", "reivindicatorios"]):
        return [
            "Observar se os estudantes reconhecem a finalidade, a estrutura e os argumentos da carta de reclamação.",
            "Verificar a participação na leitura, na análise dos trechos e nas discussões sobre reivindicação.",
            "Acompanhar os registros produzidos nas atividades de interpretação e organização das ideias.",
        ]

    if any(k in base for k in ["conjuncao", "conjuncoes", "locucao conjuntiva", "locucoes conjuntivas"]):
        return [
            "Verificar se os estudantes identificam conjunções e relações de sentido entre as orações.",
            "Observar a aplicação dos conceitos nas atividades de leitura e análise dos textos.",
            "Acompanhar a participação nas correções coletivas e os registros produzidos no caderno.",
        ]

    if any(k in base for k in ["texto multissemiótico", "texto multissemiótico", "multissemiotico", "linguagem verbal", "linguagem nao verbal"]):
        return [
        "Observar se os estudantes relacionam linguagem verbal e não verbal na construção dos sentidos do texto.",
        "Verificar a participação nas leituras, análises e discussões sobre os recursos utilizados.",
        "Acompanhar os registros produzidos durante as atividades e retomadas coletivas.",
    ]

    # Novos tipos de aula LP — derivados da classificacao especializada
    if any(k in base for k in ["leitura_literaria", "cronica", "conto", "poema", "poesia", "narrativa",
                                "eu lirico", "narrador", "enredo", "personagem", "fruicao", "literatura"]):
        return [
            "Observar se os estudantes identificam elementos do texto literário como narrador, personagens e conflito.",
            "Verificar a participação nas discussões sobre o texto e a capacidade de compartilhar leituras e impressões.",
            "Acompanhar os registros produzidos durante as atividades de leitura e interpretação literária.",
        ]

    if any(k in base for k in ["gramatica_contextualizada", "modo subjuntivo", "modo indicativo",
                                "tempos verbais", "coesao", "coesivos", "pronomes", "regencia",
                                "modalizacao", "polissemia", "intertextualidade"]):
        return [
            "Verificar se os estudantes identificam e aplicam a norma ou fenômeno gramatical estudado em situações reais de uso.",
            "Observar a participação nas análises de trechos e a correção coletiva das atividades.",
            "Acompanhar os registros que demonstram compreensão sobre o efeito de sentido produzido pelo recurso gramatical.",
        ]

    if any(k in base for k in ["leitura_jornalistica", "noticia", "editorial", "reportagem",
                                "manchete", "lide", "jornalismo", "midia", "imparcialidade"]):
        return [
            "Observar se os estudantes distinguem fato e opinião nos textos jornalísticos analisados.",
            "Verificar a participação nas discussões sobre o papel da mídia e a intencionalidade dos textos.",
            "Acompanhar os registros produzidos durante as atividades de leitura e análise crítica.",
        ]

    if any(k in base for k in ["producao_textual", "producao", "resenha", "carta do leitor",
                                "estrutura do genero", "publico-alvo", "suporte", "redija"]):
        return [
            "Verificar se os estudantes planejam, escrevem e revisam o texto considerando o gênero e a situação comunicativa.",
            "Observar a participação no planejamento e nas etapas de produção, com atenção à clareza e coerência.",
            "Acompanhar os registros produzidos, avaliando se atendem à finalidade, ao público e às convenções do gênero.",
        ]

    if any(k in base for k in ["pesquisa", "scielo", "curadoria", "plagio", "fontes confiaveis",
                                "divulgacao cientifica", "direitos autorais", "google academico"]):
        return [
            "Observar se os estudantes identificam critérios de confiabilidade em fontes de pesquisa.",
            "Verificar a compreensão sobre autoria, plágio e uso responsável das informações coletadas.",
            "Acompanhar os registros produzidos durante as atividades de curadoria e seleção de fontes.",
        ]

    return [
        "Observar se os estudantes compreendem o gênero, o tema e os recursos linguísticos trabalhados na aula.",
        "Verificar a participação nas leituras, análises, discussões e correções coletivas.",
        "Acompanhar os registros produzidos durante as atividades, considerando clareza e relação com o conteúdo estudado.",
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



def _acompanhamento_projeto_vida(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    """Detecta o tipo de aula de Projeto de Vida pelo contexto e retorna 3 itens específicos com ☑.

    Cobre 6 tipos:
    - futureme (plataforma FutureMe)
    - encerramento (síntese, pacto, ritual de fechamento)
    - consciencia_social (privilégios, desigualdade digital)
    - convivencia (círculo, dilema, tomada de decisão)
    - producao_coletiva (biomapa, campanha, HQ)
    - autoconhecimento (padrão)
    """
    from core.lib.classificador import (
        _PV_FUTUREME, _PV_ENCERRAMENTO, _PV_CONSCIENCIA_SOCIAL,
        _PV_CONVIVENCIA, _PV_PRODUCAO_COLETIVA,
    )
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    # 1. Plataforma FutureMe
    if contem_termos(base, _PV_FUTUREME):
        return [
            "☑ Observar se o estudante acessa e completa o questionário da plataforma com autenticidade, respondendo com base em suas preferências reais.",
            "☑ Verificar se o estudante interpreta o relatório de forma crítica, identificando o que faz sentido e o que não se alinha à sua experiência.",
            "☑ Acompanhar a troca em trios, avaliando se o estudante conecta os resultados da plataforma a situações concretas do cotidiano e a possibilidades de futuro.",
        ]

    # 2. Encerramento e Síntese
    if contem_termos(base, _PV_ENCERRAMENTO):
        return [
            "☑ Observar se o estudante identifica pelo menos uma descoberta significativa sobre si mesmo ao longo do bimestre, conectando-a a situações concretas vividas nas aulas.",
            "☑ Verificar se o estudante consegue nomear uma mudança no modo de agir, sentir ou ver o mundo a partir dos aprendizados do bimestre.",
            "☑ Acompanhar a participação no ritual simbólico de encerramento, avaliando se o estudante escolhe palavras e compromissos que refletem os temas trabalhados.",
        ]

    # 3. Consciência Social
    if contem_termos(base, _PV_CONSCIENCIA_SOCIAL):
        return [
            "☑ Observar se o estudante reconhece a diferença entre privilégios e desvantagens como condições estruturais, e não apenas como resultado do esforço individual.",
            "☑ Verificar se o estudante identifica, no ambiente digital e na mídia, padrões de representação que privilegiam certos perfis e invisibilizam outros.",
            "☑ Acompanhar o registro individual, avaliando se o estudante indica mudanças concretas em sua forma de agir ao reconhecer as desigualdades.",
        ]

    # 4. Convivência e Tomada de Decisão
    if contem_termos(base, _PV_CONVIVENCIA):
        return [
            "☑ Observar se o estudante participa do Círculo de Convivência com escuta ativa, respeitando os acordos de fala e sem interromper os colegas.",
            "☑ Verificar se o estudante contribui com pelo menos uma proposta de solução para o dilema discutido, justificando com base nos efeitos para o grupo.",
            "☑ Acompanhar o registro individual do compromisso, avaliando se o estudante identifica uma ação concreta que pode realizar para colocar a decisão coletiva em prática.",
        ]

    # 5. Produção Coletiva
    if contem_termos(base, _PV_PRODUCAO_COLETIVA):
        return [
            "☑ Observar se o grupo elabora um produto concreto (biomapa, campanha, vídeo) com elementos claros: objetivo, mensagem, público-alvo e estratégia de ação.",
            "☑ Verificar se todos os integrantes do grupo participam ativamente da produção, com funções definidas e contribuições visíveis no produto final.",
            "☑ Acompanhar a apresentação, avaliando se o grupo consegue explicar as escolhas feitas e conectá-las ao tema do bimestre.",
        ]

    # 6. Autoconhecimento (padrão)
    return [
        "☑ Observar se o estudante identifica pelo menos três possibilidades de futuro conectadas aos seus interesses e valores, com justificativa para cada escolha.",
        "☑ Verificar se o estudante reconhece fatores externos (contexto social, oportunidades, imprevistos) que influenciam suas escolhas, sem se limitar à vontade individual.",
        "☑ Acompanhar a qualidade da troca em duplas, avaliando se o estudante escuta ativamente o colega e oferece sugestões pertinentes ao projeto de vida do outro.",
    ]




def _acompanhamento_matematica(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    """Detecta o tipo de aula de Matemática pelo contexto e retorna 3 itens específicos com ☑."""
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    # Aula Khan ou Verificação
    if any(k in base for k in ["verificacao", "revisao", "khan", "relembre", "bit.ly", "khanmigo"]):
        return [
            "☑ Observar se os estudantes demonstram autonomia na resolução das atividades, aplicando corretamente os conceitos trabalhados no bloco.",
            "☑ Verificar se a turma consegue justificar as estratégias escolhidas e interpretar os resultados obtidos.",
            "☑ Acompanhar se os estudantes identificam e corrigem erros no próprio raciocínio durante a atividade.",
        ]

    # Aula de gráfico ou representação
    if any(k in base for k in ["grafico", "representacao grafica", "plano cartesiano", "eixo", "tabela", "pares ordenados"]):
        return [
            "☑ Verificar se os estudantes interpretam corretamente os dados, eixos, valores e informações apresentadas em gráficos ou tabelas do material.",
            "☑ Acompanhar se a turma utiliza os dados do material para sustentar respostas, evitando conclusões sem evidências.",
            "☑ Observar se conseguem relacionar a representação gráfica ao contexto real da situação estudada.",
        ]

    # Aula de resolução de problemas
    if any(k in base for k in ["resolucao de problemas", "metodo de polya", "polya"]):
        return [
            "☑ Verificar se os estudantes aplicam as etapas do método de resolução: compreender, planejar, executar e verificar.",
            "☑ Acompanhar se a turma justifica a estratégia escolhida e verifica se o resultado faz sentido no contexto do problema.",
            "☑ Observar se os estudantes conseguem resolver problemas variados, transferindo o raciocínio para situações novas.",
        ]

    # Padrão: conceito_novo / modelagem
    return [
        "☑ Verificar se os estudantes identificam corretamente os dados necessários e compreendem o que está sendo pedido em cada situação.",
        "☑ Acompanhar se a turma reconhece a relação entre o resultado obtido e o contexto da situação estudada, evitando respostas apenas numéricas.",
        "☑ Conferir se os registros finais articulam cálculo, interpretação e conclusão, demonstrando compreensão do conceito trabalhado.",
    ]


def _acompanhamento_ingles(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    """Detecta o tipo de aula de Língua Inglesa pelo contexto e retorna 3 itens específicos com ☑.

    Cobre as 8 tipologias:
    - leitura_em
    - gramatica
    - listening
    - vocabulario
    - producao_oral
    - leitura_literaria
    - musica
    - revisao
    """
    from core.lib.classificador import detectar_tipo_aula
    tipo = detectar_tipo_aula(desenvolvimento, tema, "Língua Inglesa")
    conteudo = tema

    if tipo == "leitura_em":
        return [
            f"☑ Verificar se os estudantes identificam corretamente as informações gerais e específicas do texto sobre {conteudo}, localizando evidências no texto para justificar as respostas.",
            "☑ Acompanhar se a turma aplica as estratégias de leitura apresentadas (palavras-chave, cognatas, inferência pelo contexto) para resolver as questões de múltipla escolha.",
            "☑ Observar se os estudantes conseguem eliminar as alternativas incorretas com base em trechos do texto, explicando o raciocínio utilizado."
        ]
    elif tipo == "gramatica":
        return [
            f"☑ Verificar se os estudantes identificam e utilizam corretamente a estrutura gramatical de {conteudo} nos exercícios propostos.",
            f"☑ Acompanhar se a turma consegue produzir frases em inglês usando {conteudo} de forma comunicativa, não apenas mecânica.",
            "☑ Observar se os estudantes reconhecem os exemplos da estrutura gramatical em textos e áudios autênticos, conectando a regra ao uso real."
        ]
    elif tipo == "listening":
        return [
            f"☑ Verificar se os estudantes identificam as informações gerais e específicas solicitadas durante a escuta do áudio sobre {conteudo}.",
            "☑ Acompanhar se a turma utiliza o vocabulário apresentado antes da escuta para compreender o áudio, sem depender de tradução.",
            "☑ Observar se os estudantes conseguem completar as atividades de compreensão oral com base no que ouviram, justificando as respostas."
        ]
    elif tipo == "producao_oral":
        return [
            f"☑ Verificar se os estudantes produzem frases e diálogos em inglês sobre {conteudo} de forma comunicativa, utilizando o vocabulário e as estruturas trabalhadas.",
            "☑ Acompanhar se a turma pratica a pronúncia correta das palavras e expressões novas durante as atividades orais.",
            "☑ Observar se os estudantes interagem em inglês com os colegas durante as atividades em duplas, demonstrando iniciativa comunicativa."
        ]
    elif tipo == "leitura_literaria":
        return [
            f"☑ Verificar se os estudantes identificam elementos do texto literário sobre {conteudo}, analisando a caracterização de personagens e cenários.",
            "☑ Acompanhar se a turma utiliza as estratégias de leitura literária apresentadas para analisar o tom das descrições.",
            "☑ Observar se os estudantes conseguem explicar o conflito do trecho literário com suas palavras em inglês."
        ]
    elif tipo == "musica":
        return [
            f"☑ Verificar se os estudantes identificam a estrutura gramatical ou o vocabulário trabalhado na letra da música sobre {conteudo}.",
            "☑ Acompanhar se os estudantes compreendem o tema central da canção através da leitura e audição da letra.",
            "☑ Observar se a turma participa ativamente da escuta e da prática musical, realizando os exercícios de fixação propostos."
        ]
    elif tipo == "revisao":
        return [
            f"☑ Verificar se os estudantes revisam e consolidam os principais pontos lexicais e gramaticais sobre {conteudo} trabalhados no bloco.",
            "☑ Acompanhar se os estudantes demonstram autonomia na resolução das atividades variadas de prática e revisão.",
            "☑ Observar se a turma consegue apontar em inglês o que aprendeu a fazer ao longo deste bloco de aulas."
        ]
    # vocabulario e fallback geral
    return [
        f"☑ Verificar se os estudantes compreendem e utilizam o vocabulário ou conteúdo de {conteudo} nas atividades propostas.",
        "☑ Acompanhar se a turma produz em inglês (oral ou escrito) usando os recursos linguísticos trabalhados na aula.",
        f"☑ Observar se os estudantes conseguem explicar com suas palavras o que aprenderam sobre {conteudo}, em inglês."
    ]


def gerar_acompanhamento_aprimorado(
    tema: str,
    aprendizagem: str = "",
    desenvolvimento: str = "",
    disciplina: str = "",
    perfil: str = "",
    tipo: str = "",
    habilidade: str = "",
    etapas_metodologia: list[str] | None = None,
    indice_aula: int = 0,
) -> list[str]:
    """
    Gera acompanhamento da aprendizagem aprimorado.
    Compatível com a assinatura de gerar_acompanhamento_dinamico() do avaliacao.py,
    mas com camadas adicionais de personalização.
    """
    from core.lib.classificador import perfil_disciplina, detectar_tipo_aula

    if not perfil:
        perfil = perfil_disciplina(disciplina)
    if not tipo:
        tipo = detectar_tipo_aula(desenvolvimento, tema, disciplina)

    especifico = _acompanhamento_especifico_por_aula(tema, aprendizagem, desenvolvimento)
    if especifico:
        return _limitar_itens(especifico, minimo=2, maximo=3)

    if perfil == "ingles":
        return _limitar_itens(
            _acompanhamento_ingles(tema, aprendizagem, desenvolvimento),
            minimo=2,
            maximo=3,
        )

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return _limitar_itens(
            _acompanhamento_lingua_portuguesa(tema, aprendizagem, desenvolvimento),
            minimo=2,
            maximo=3,
        )

    if perfil == "matematica":
        return _limitar_itens(
            _acompanhamento_matematica(tema, aprendizagem, desenvolvimento),
            minimo=2,
            maximo=3,
        )

    if perfil == "projeto_de_vida":
        return _limitar_itens(
            _acompanhamento_projeto_vida(tema, aprendizagem, desenvolvimento),
            minimo=2,
            maximo=3,
        )

    return _limitar_itens(_compositor.compor(
        perfil=perfil,
        tipo=tipo,
        tema=tema,
        habilidade=habilidade,
        etapas_metodologia=etapas_metodologia,
        indice_aula=indice_aula,
        disciplina=disciplina,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
    ), minimo=2, maximo=3)
