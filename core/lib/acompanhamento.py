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
from core.lib.classificador import normalizar_texto
from core.lib.progressao import verbo_observacao, verbo_verificacao, verbo_acompanhamento, conector_progressao
from core.listas_pedagogicas import normalizar_lista_exatamente_tres
from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural
from core.lib.acompanhamento_perfis import (
    gerar_acompanhamento_especifico_por_aula,
    gerar_acompanhamento_por_perfil,
)


# â”€â”€ Frases-base por perfil disciplinar e tipo de aula â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_ACOMPANHAMENTO_POR_PERFIL_TIPO = {
    "matematica": {
        "verificacao": [
            "Observar a autonomia dos estudantes na resolução das atividades.",
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
            "{v_obs} se o estudante completa o questionário da plataforma com autenticidade, respondendo com base em suas preferências reais, sem buscar â€˜a resposta certaâ€™.",
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

# â”€â”€ Conectores com etapas da metodologia â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Instância global para uso direto â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_compositor = CompositorAcompanhamento()



def _limitar_itens(itens: list[str], minimo: int = 2, maximo: int = 3) -> list[str]:
    fallbacks = [
        "Verificar se os estudantes compreendem os conceitos centrais da aula por meio das respostas e registros.",
        "Observar a participação da turma nas discussões, atividades orientadas e momentos de socialização.",
        "Conferir se os registros finais retomam o conteúdo trabalhado com clareza e progressiva autonomia.",
    ]
    return normalizar_lista_exatamente_tres(itens, fallbacks)[:maximo]




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

    especifico = gerar_acompanhamento_especifico_por_aula(tema, aprendizagem, desenvolvimento)
    if especifico:
        return _limitar_itens(especifico, minimo=2, maximo=3)

    acompanhamento_por_perfil = gerar_acompanhamento_por_perfil(
        perfil,
        tema,
        aprendizagem,
        desenvolvimento,
    )
    if acompanhamento_por_perfil:
        return _limitar_itens(
            acompanhamento_por_perfil,
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

