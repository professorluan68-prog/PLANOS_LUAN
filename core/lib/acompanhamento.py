"""
Compositor de acompanhamento da aprendizagem por camadas.

Gera textos de acompanhamento contextualizados por:
1. Perfil disciplinar
2. Tipo de aula
3. Etapas da metodologia
4. Habilidade BNCC (quando disponÃ­vel)
5. VariaÃ§Ã£o sequencial (posiÃ§Ã£o da aula na sequÃªncia)
"""

import re
from core.lib.classificador import normalizar_texto
from core.lib.progressao import verbo_observacao, verbo_verificacao, verbo_acompanhamento, conector_progressao
from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural
from core.lib.acompanhamento_perfis import (
    gerar_acompanhamento_especifico_por_aula,
    gerar_acompanhamento_por_perfil,
)


# â”€â”€ Frases-base por perfil disciplinar e tipo de aula â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_ACOMPANHAMENTO_POR_PERFIL_TIPO = {
    "matematica": {
        "verificacao": [
            "Observar a autonomia dos estudantes na resoluÃ§Ã£o das atividades.",
            "â˜‘ Verificar se a turma consegue justificar as estratÃ©gias escolhidas e interpretar os resultados obtidos.",
            "â˜‘ Acompanhar se os estudantes identificam e corrigem erros no prÃ³prio raciocÃ­nio durante a atividade.",
        ],
        "khan": [
            "â˜‘ Observar se os estudantes demonstram autonomia na resoluÃ§Ã£o das atividades, aplicando corretamente os conceitos trabalhados no bloco.",
            "â˜‘ Verificar se a turma consegue justificar as estratÃ©gias escolhidas e interpretar os resultados obtidos.",
            "â˜‘ Acompanhar se os estudantes identificam e corrigem erros no prÃ³prio raciocÃ­nio durante a atividade.",
        ],
        "modelagem": [
            "â˜‘ Verificar se os estudantes identificam corretamente os dados necessÃ¡rios e compreendem o que estÃ¡ sendo pedido em cada situaÃ§Ã£o.",
            "â˜‘ Acompanhar se a turma reconhece a relaÃ§Ã£o entre o resultado obtido e o contexto da situaÃ§Ã£o estudada, evitando respostas apenas numÃ©ricas.",
            "â˜‘ Conferir se os registros finais articulam cÃ¡lculo, interpretaÃ§Ã£o e conclusÃ£o, demonstrando compreensÃ£o do conceito trabalhado.",
        ],
        "grafico": [
            "â˜‘ Verificar se os estudantes interpretam corretamente os dados, eixos, valores e informaÃ§Ãµes apresentadas em grÃ¡ficos ou tabelas do material.",
            "â˜‘ Acompanhar se a turma utiliza os dados do material para sustentar respostas, evitando conclusÃµes sem evidÃªncias.",
            "â˜‘ Observar se conseguem relacionar a representaÃ§Ã£o grÃ¡fica ao contexto real da situaÃ§Ã£o estudada.",
        ],
        "resolucao_problemas": [
            "â˜‘ Verificar se os estudantes aplicam as etapas do mÃ©todo de resoluÃ§Ã£o: compreender, planejar, executar e verificar.",
            "â˜‘ Acompanhar se a turma justifica a estratÃ©gia escolhida e verifica se o resultado faz sentido no contexto do problema.",
            "â˜‘ Observar se os estudantes conseguem resolver problemas variados, transferindo o raciocÃ­nio para situaÃ§Ãµes novas.",
        ],
        "_default": [
            "â˜‘ Verificar se os estudantes identificam corretamente os dados necessÃ¡rios e compreendem o que estÃ¡ sendo pedido em cada situaÃ§Ã£o.",
            "â˜‘ Acompanhar se a turma reconhece a relaÃ§Ã£o entre o resultado obtido e o contexto da situaÃ§Ã£o estudada, evitando respostas apenas numÃ©ricas.",
            "â˜‘ Conferir se os registros finais articulam cÃ¡lculo, interpretaÃ§Ã£o e conclusÃ£o, demonstrando compreensÃ£o do conceito trabalhado.",
        ],
    },
    "lingua_portuguesa_ef": {
        "producao": [
            "{v_obs} como os estudantes planejam, revisam e ajustam a produÃ§Ã£o textual, considerando gÃªnero, finalidade comunicativa e organizaÃ§Ã£o das ideias.",
            "{v_ver} se os estudantes incorporam as orientaÃ§Ãµes discutidas na aula para qualificar clareza, coerÃªncia e adequaÃ§Ã£o linguÃ­stica.",
            "{v_acomp} os registros produzidos, considerando avanÃ§os entre rascunho, revisÃ£o e versÃ£o final, bem como a autonomia no uso dos critÃ©rios trabalhados.",
        ],
        "argumentacao": [
            "{v_obs} a participaÃ§Ã£o dos estudantes nas discussÃµes, considerando a escuta, a formulaÃ§Ã£o de posicionamentos e o uso de argumentos consistentes.",
            "{v_ver} se os estudantes identificam tese, argumentos e recursos persuasivos nos textos e interaÃ§Ãµes analisados.",
            "{v_acomp} se os registros e respostas evidenciam clareza de posicionamento, justificativa e respeito Ã s diferentes perspectivas.",
        ],
        "_default": [
            "{v_obs} se os estudantes compreendem as ideias centrais de {tema} e reconhecem os elementos textuais ou linguÃ­sticos em foco.",
            "{v_ver} a participaÃ§Ã£o nas leituras, anÃ¡lises, discussÃµes e registros, considerando interpretaÃ§Ã£o, argumentaÃ§Ã£o e ampliaÃ§Ã£o de repertÃ³rio.",
            "{v_acomp} se os estudantes aplicam as estratÃ©gias de leitura, anÃ¡lise da linguagem ou produÃ§Ã£o de sentidos com autonomia crescente.",
        ],
    },
    "lingua_portuguesa_em": {
        "_default": [
            "{v_obs} se os estudantes compreendem as ideias centrais de {tema} e reconhecem os elementos textuais ou linguÃ­sticos em foco.",
            "{v_ver} a participaÃ§Ã£o nas leituras, anÃ¡lises, discussÃµes e registros, considerando interpretaÃ§Ã£o, argumentaÃ§Ã£o e ampliaÃ§Ã£o de repertÃ³rio.",
            "{v_acomp} se os estudantes aplicam as estratÃ©gias de leitura, anÃ¡lise da linguagem ou produÃ§Ã£o de sentidos com autonomia crescente.",
        ],
    },
    "leitura_redacao": {
        "_default": [
            "{v_obs} se os estudantes compreendem as ideias centrais de {tema} e reconhecem os elementos textuais ou linguÃ­sticos em foco.",
            "{v_ver} a participaÃ§Ã£o nas leituras, anÃ¡lises, discussÃµes e registros, considerando interpretaÃ§Ã£o, argumentaÃ§Ã£o e ampliaÃ§Ã£o de repertÃ³rio.",
            "{v_acomp} se os estudantes aplicam as estratÃ©gias de leitura, anÃ¡lise da linguagem ou produÃ§Ã£o de sentidos com autonomia crescente.",
        ],
    },
    "orientacao_estudos": {
        "_default": [
            "{v_obs} se os estudantes utilizam as estratÃ©gias de organizaÃ§Ã£o, leitura, retomada e planejamento propostas durante a aula.",
            "{v_ver} se os estudantes conseguem identificar dificuldades, selecionar procedimentos de estudo e explicar como podem aplicÃ¡-los em outras situaÃ§Ãµes.",
            "{v_acomp} os registros produzidos, considerando autonomia, constÃ¢ncia e capacidade de monitorar o prÃ³prio processo de aprendizagem.",
        ],
    },
    "ciencias_ef": {
        "_default": [
            "{v_obs} se os estudantes relacionam {tema} aos conceitos cientÃ­ficos trabalhados e utilizam evidÃªncias para sustentar suas respostas.",
            "{v_ver} a participaÃ§Ã£o nas investigaÃ§Ãµes, discussÃµes, registros e socializaÃ§Ãµes, considerando clareza de hipÃ³teses e explicaÃ§Ãµes.",
            "{v_acomp} se os estudantes interpretam fenÃ´menos, dados, experimentos ou representaÃ§Ãµes com base nos conceitos desenvolvidos na aula.",
        ],
    },
    "biologia": {
        "_default": [
            "{v_obs} se os estudantes relacionam fenÃ´menos biolÃ³gicos e ambientais, utilizando conceitos cientÃ­ficos para explicar causas, efeitos e interdependÃªncias.",
            "{v_ver} se os estudantes interpretam dados, imagens, esquemas ou situaÃ§Ãµes-problema com base nas evidÃªncias discutidas na aula.",
            "{v_acomp} se os registros mostram uso progressivo do vocabulÃ¡rio cientÃ­fico e capacidade de justificar posiÃ§Ãµes e soluÃ§Ãµes.",
        ],
    },
    "quimica": {
        "_default": [
            "{v_obs} se os estudantes identificam evidÃªncias, transformaÃ§Ãµes e relaÃ§Ãµes entre substÃ¢ncias, materiais ou processos quÃ­micos em estudo.",
            "{v_ver} se os estudantes organizam informaÃ§Ãµes, analisam representaÃ§Ãµes e explicam resultados utilizando conceitos e linguagem adequados.",
            "{v_acomp} se os estudantes conseguem aplicar os conhecimentos trabalhados para interpretar fenÃ´menos, comparar situaÃ§Ãµes e justificar conclusÃµes.",
        ],
    },
    "fisica": {
        "_default": [
            "{v_obs} se os estudantes identificam grandezas, variÃ¡veis e relaÃ§Ãµes fÃ­sicas envolvidas nas situaÃ§Ãµes analisadas na aula.",
            "{v_ver} se os estudantes interpretam esquemas, grÃ¡ficos, experimentos ou problemas, articulando conceitos e evidÃªncias.",
            "{v_acomp} se os estudantes explicam procedimentos, analisam resultados e utilizam os conceitos fÃ­sicos para justificar suas respostas.",
        ],
    },
    "historia": {
        "_default": [
            "{v_obs} se os estudantes identificam sujeitos, contextos, permanÃªncias, mudanÃ§as e relaÃ§Ãµes temporais nas fontes e situaÃ§Ãµes estudadas.",
            "{v_ver} se os estudantes utilizam evidÃªncias histÃ³ricas para interpretar acontecimentos, comparar perspectivas e sustentar explicaÃ§Ãµes.",
            "{v_acomp} os registros e respostas, considerando vocabulÃ¡rio histÃ³rico, organizaÃ§Ã£o das ideias e progressiva autonomia de anÃ¡lise.",
        ],
    },
    "geografia": {
        "_default": [
            "{v_obs} se os estudantes interpretam paisagens, mapas, grÃ¡ficos, tabelas e outras linguagens geogrÃ¡ficas com atenÃ§Ã£o aos conceitos em foco.",
            "{v_ver} se os estudantes relacionam territÃ³rio, sociedade, natureza e escalas de anÃ¡lise nas situaÃ§Ãµes discutidas ao longo da aula.",
            "{v_acomp} os registros produzidos, considerando clareza na leitura de dados, argumentaÃ§Ã£o e aplicaÃ§Ã£o dos conceitos trabalhados.",
        ],
    },
    "ingles": {
        "_default": [
            "{v_obs} se os estudantes compreendem vocabulÃ¡rio, estruturas e comandos em lÃ­ngua inglesa nas atividades propostas.",
            "{v_ver} se os estudantes participam das prÃ¡ticas de leitura, escuta, oralidade e escrita com apoio progressivamente mais autÃ´nomo.",
            "{v_acomp} se os registros e interaÃ§Ãµes evidenciam uso contextualizado da lÃ­ngua, ampliaÃ§Ã£o de repertÃ³rio e compreensÃ£o do tema estudado.",
        ],
    },
    "arte": {
        "_default": [
            "{v_obs} se os estudantes participam das prÃ¡ticas de apreciaÃ§Ã£o, experimentaÃ§Ã£o, criaÃ§Ã£o e anÃ¡lise propostas durante a aula.",
            "{v_ver} se os estudantes reconhecem elementos, linguagens, procedimentos e intencionalidades presentes nas produÃ§Ãµes artÃ­sticas estudadas.",
            "{v_acomp} se os registros e produÃ§Ãµes revelam ampliaÃ§Ã£o de repertÃ³rio, argumentaÃ§Ã£o sensÃ­vel e uso de referÃªncias discutidas coletivamente.",
        ],
    },
    "projeto_de_vida": {
        "autoconhecimento": [
            "{v_obs} se o estudante identifica pelo menos trÃªs possibilidades de futuro conectadas aos seus interesses e valores, com justificativa para cada escolha.",
            "{v_ver} se o estudante reconhece fatores externos (contexto social, oportunidades, imprevistos) que influenciam suas escolhas, sem se limitar Ã  vontade individual.",
            "{v_acomp} a qualidade da troca em duplas, avaliando se o estudante escuta ativamente o colega e oferece sugestÃµes pertinentes ao projeto de vida do outro.",
        ],
        "futureme": [
            "{v_obs} se o estudante completa o questionÃ¡rio da plataforma com autenticidade, respondendo com base em suas preferÃªncias reais, sem buscar â€˜a resposta certaâ€™.",
            "{v_ver} se o estudante interpreta o relatÃ³rio de forma crÃ­tica, identificando o que faz sentido e o que nÃ£o se alinha Ã  sua experiÃªncia, sem aceitar passivamente o resultado.",
            "{v_acomp} a troca em duplas/trios, avaliando se o estudante conecta os resultados da plataforma a situaÃ§Ãµes concretas do cotidiano escolar e pessoal.",
        ],
        "producao_coletiva": [
            "{v_obs} se o grupo elabora um produto concreto (biomapa, campanha, vÃ­deo) com elementos claros: objetivo, mensagem, pÃºblico-alvo e estratÃ©gia de aÃ§Ã£o.",
            "{v_ver} se todos os integrantes do grupo participam ativamente da produÃ§Ã£o, com funÃ§Ãµes definidas e contribuiÃ§Ãµes visÃ­veis.",
            "{v_acomp} a apresentaÃ§Ã£o do produto, avaliando se o grupo consegue explicar as escolhas feitas e conectÃ¡-las ao tema do bimestre.",
        ],
        "convivencia": [
            "{v_obs} se o estudante participa do CÃ­rculo de ConvivÃªncia com escuta ativa, respeitando os acordos de fala e sem interromper os colegas.",
            "{v_ver} se o estudante contribui com pelo menos uma proposta de soluÃ§Ã£o para o dilema discutido, justificando com base nos efeitos para o grupo.",
            "{v_acomp} o registro individual do compromisso, avaliando se o estudante identifica uma aÃ§Ã£o concreta que pode realizar para colocar a decisÃ£o coletiva em prÃ¡tica.",
        ],
        "consciencia_social": [
            "{v_obs} se o estudante reconhece a diferenÃ§a entre privilÃ©gios e desvantagens como condiÃ§Ãµes estruturais, e nÃ£o apenas como resultado do esforÃ§o individual.",
            "{v_ver} se o estudante identifica, no ambiente digital e na mÃ­dia, padrÃµes de representaÃ§Ã£o que privilegiam certos perfis e invisibilizam outros.",
            "{v_acomp} o registro individual, avaliando se o estudante indica mudanÃ§as concretas em sua forma de agir ao reconhecer desigualdades.",
        ],
        "encerramento": [
            "{v_obs} se o estudante identifica pelo menos uma descoberta significativa sobre si mesmo ao longo do bimestre, conectando-a a situaÃ§Ãµes concretas vividas nas aulas.",
            "{v_ver} se o estudante consegue nomear uma mudanÃ§a no modo de agir, sentir ou ver o mundo a partir dos aprendizados do bimestre.",
            "{v_acomp} a participaÃ§Ã£o no ritual simbÃ³lico de encerramento, avaliando se o estudante escolhe palavras/compromissos que refletem os temas trabalhados.",
        ],
        "_default": [
            "{v_obs} a participaÃ§Ã£o dos estudantes nas reflexÃµes e interaÃ§Ãµes propostas, considerando escuta, respeito, cooperaÃ§Ã£o e elaboraÃ§Ã£o de ideias.",
            "{v_ver} se os estudantes relacionam o tema da aula a escolhas, atitudes, estratÃ©gias de convivÃªncia e planejamento pessoal ou coletivo.",
            "{v_acomp} os registros produzidos, valorizando argumentaÃ§Ã£o, consciÃªncia crÃ­tica e apropriaÃ§Ã£o dos conceitos sem exigir exposiÃ§Ã£o excessiva.",
        ],
    },
    "lideranca_oratoria": {
        "_default": [
            "{v_obs} a participaÃ§Ã£o dos estudantes nas reflexÃµes e interaÃ§Ãµes propostas, considerando escuta, respeito, cooperaÃ§Ã£o e elaboraÃ§Ã£o de ideias.",
            "{v_ver} se os estudantes relacionam o tema da aula a escolhas, atitudes, estratÃ©gias de convivÃªncia e planejamento pessoal ou coletivo.",
            "{v_acomp} os registros produzidos, valorizando argumentaÃ§Ã£o, consciÃªncia crÃ­tica e apropriaÃ§Ã£o dos conceitos sem exigir exposiÃ§Ã£o excessiva.",
        ],
    },
    "educacao_financeira": {
        "orcamento_planejamento": [
            "{v_obs} se os estudantes identificam receitas, despesas, prioridades e metas em situaÃ§Ãµes de organizaÃ§Ã£o financeira.",
            "{v_ver} se os estudantes elaboram ou analisam o orÃ§amento simulado com critÃ©rios claros, relacionando escolhas, limites e saldo.",
            "{v_acomp} se os registros mostram compreensÃ£o progressiva sobre planejamento, controle de gastos e tomada de decisÃ£o responsÃ¡vel.",
        ],
        "consumo_consciente": [
            "{v_obs} se os estudantes diferenciam necessidade, desejo, prioridade e custo-benefÃ­cio nas situaÃ§Ãµes de consumo analisadas.",
            "{v_ver} se os estudantes justificam escolhas de consumo com base em dados, consequÃªncias e critÃ©rios construÃ­dos na aula.",
            "{v_acomp} se os registros evidenciam postura crÃ­tica sem julgamento moralista sobre hÃ¡bitos pessoais ou familiares.",
        ],
        "investimento_poupanca": [
            "{v_obs} se os estudantes compreendem a funÃ§Ã£o da poupanÃ§a, da reserva de emergÃªncia e do planejamento de metas.",
            "{v_ver} se os estudantes interpretam valores, rendimentos, prazos ou cenÃ¡rios de acumulaÃ§Ã£o, justificando decisÃµes com coerÃªncia.",
            "{v_acomp} se os registros relacionam constÃ¢ncia, objetivo financeiro, imprevistos e uso responsÃ¡vel dos recursos.",
        ],
        "credito_endividamento": [
            "{v_obs} se os estudantes reconhecem juros, parcelas, custo total e riscos envolvidos no uso de crÃ©dito.",
            "{v_ver} se os estudantes comparam alternativas de pagamento e justificam quando o crÃ©dito pode ser vantajoso ou arriscado.",
            "{v_acomp} se os cÃ¡lculos e registros mostram compreensÃ£o sobre endividamento, planejamento e uso responsÃ¡vel do crÃ©dito.",
        ],
        "empreendedorismo": [
            "{v_obs} se os estudantes identificam custos, preÃ§o, pÃºblico, recursos necessÃ¡rios e viabilidade em propostas empreendedoras simples.",
            "{v_ver} se os estudantes justificam decisÃµes do projeto com base em planejamento, responsabilidade e anÃ¡lise do contexto.",
            "{v_acomp} se os registros mostram articulaÃ§Ã£o entre ideia, necessidade, produto ou serviÃ§o e organizaÃ§Ã£o financeira.",
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
            "{v_ver} se os estudantes comparam alternativas e justificam decisÃµes com base em consequencias e criterios objetivos.",
            "{v_acomp} se os registros mostram relacao entre recursos disponiveis, metas e impactos das escolhas feitas.",
        ],
        "cidadania_financeira": [
            "{v_obs} se os estudantes reconhecem direitos, responsabilidades e formas de proteÃ§Ã£o em situaÃ§Ãµes de consumo.",
            "{v_ver} se os estudantes analisam comprovantes, garantias, seguranÃ§a e critÃ©rios de escolha em serviÃ§os ou compras.",
            "{v_acomp} se as respostas indicam autonomia para tomar decisÃµes financeiras mais seguras e conscientes.",
        ],
        "instituicoes_financeiras": [
            "{v_obs} se os estudantes reconhecem a funÃ§Ã£o das instituiÃ§Ãµes financeiras na guarda, movimentaÃ§Ã£o e proteÃ§Ã£o do dinheiro.",
            "{v_ver} se os estudantes comparam serviÃ§os financeiros, identificando possibilidades, cuidados e critÃ©rios de seguranÃ§a.",
            "{v_acomp} se os registros relacionam instituiÃ§Ã£o financeira, organizaÃ§Ã£o dos recursos e escolhas responsÃ¡veis.",
        ],
        "_default": [
            "{v_obs} se os estudantes analisam situaÃ§Ãµes de consumo, orÃ§amento, planejamento e tomada de decisÃ£o com base em critÃ©rios claros.",
            "{v_ver} se os estudantes interpretam cÃ¡lculos, dados e cenÃ¡rios financeiros, justificando escolhas e prioridades com coerÃªncia.",
            "{v_acomp} se os registros mostram compreensÃ£o progressiva das relaÃ§Ãµes entre objetivos, recursos, limites e consequÃªncias das decisÃµes.",
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
            "{v_obs} se os estudantes compreendem os conceitos centrais relacionados a {tema} e participam das atividades de anÃ¡lise, discussÃ£o e registro.",
            "{v_ver} se articulam o tema estudado a situaÃ§Ãµes do cotidiano, usos da tecnologia e formas de resolver problemas ou se comunicar melhor.",
            "{v_acomp} os registros produzidos, considerando clareza de ideias, autonomia crescente e aplicaÃ§Ã£o prÃ¡tica do conhecimento trabalhado.",
        ],
    },
    "sociologia": {
        "_default": [
            "{v_obs} se os estudantes compreendem os conceitos centrais relacionados a {tema} e participam das atividades de anÃ¡lise, discussÃ£o e registro.",
            "{v_ver} se os estudantes articulam o tema estudado a situaÃ§Ãµes do cotidiano, contextos sociais ou usos prÃ¡ticos do conhecimento.",
            "{v_acomp} os registros produzidos, considerando clareza de ideias, argumentaÃ§Ã£o e autonomia crescente nas respostas.",
        ],
    },
}

# â”€â”€ Conectores com etapas da metodologia â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_CONECTORES_ETAPAS = {
    "para comecar": "nas trocas iniciais e no levantamento de conhecimentos prÃ©vios",
    "relembre": "na retomada dos conceitos trabalhados anteriormente",
    "foco no conteudo": "durante a explicaÃ§Ã£o e a anÃ¡lise do conteÃºdo central",
    "na pratica": "na resoluÃ§Ã£o das atividades propostas e nos registros individuais",
    "pause e responda": "durante a verificaÃ§Ã£o e a correÃ§Ã£o dialogada",
    "encerramento": "na sÃ­ntese final e nos registros de fechamento",
    "leitura e construcao do conteudo": "durante a leitura guiada e a construÃ§Ã£o coletiva do conteÃºdo",
    "contextualizacao": "durante a contextualizaÃ§Ã£o e a mobilizaÃ§Ã£o de repertÃ³rios",
    "leitura analitica": "na anÃ¡lise dos textos, imagens e recursos apresentados",
    "sistematizacao": "na sistematizaÃ§Ã£o dos conceitos e registros construÃ­dos",
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
    """Motor de composiÃ§Ã£o de acompanhamento por camadas."""

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
        CompÃµe 3 itens de acompanhamento da aprendizagem, customizados por camadas.

        Args:
            perfil: perfil disciplinar (ex: 'matematica', 'lingua_portuguesa_ef')
            tipo: tipo de aula (ex: 'leitura', 'producao', 'resolucao_problemas')
            tema: tema da aula
            habilidade: habilidade BNCC extraÃ­da, se disponÃ­vel
            etapas_metodologia: lista de tÃ­tulos de etapas na metodologia
            indice_aula: posiÃ§Ã£o da aula na sequÃªncia (0-based)
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
                "{v_ver} a participaÃ§Ã£o, os registros produzidos e a forma como os estudantes justificam suas respostas ao longo da aula.",
                "{v_acomp} se os estudantes conseguem aplicar os conhecimentos trabalhados com autonomia progressiva nas atividades orientadas.",
            ]

        # Camada 2: Resolver verbos com variaÃ§Ã£o por posiÃ§Ã£o
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

        # Camada 3: Enriquecer com referÃªncia Ã  etapa da metodologia
        if etapas_metodologia:
            etapa_principal = _etapa_principal(etapas_metodologia)
            conector_etapa = _CONECTORES_ETAPAS.get(etapa_principal, "")
            if conector_etapa and len(itens) >= 2:
                # Enriquece o segundo item com referÃªncia Ã  etapa
                item_enriquecido = itens[1]
                if not any(c in item_enriquecido.lower() for c in ["nas trocas", "na retomada", "durante a"]):
                    item_enriquecido = item_enriquecido.rstrip(".")
                    item_enriquecido += f", especialmente {conector_etapa}."
                    itens[1] = item_enriquecido

        # Camada 4: Incorporar referÃªncia Ã  habilidade BNCC
        if habilidade and len(habilidade) > 10:
            codigo_match = re.search(r'((?:EM|EF)\d{2}[A-Z]{2}\d{2}[A-Z]?)', habilidade, re.I)
            if codigo_match:
                codigo = codigo_match.group(1).upper()
                if len(itens) >= 1:
                    itens[0] = itens[0].rstrip(".")
                    itens[0] += f", em articulaÃ§Ã£o com a habilidade ({codigo})."

        return itens


# â”€â”€ InstÃ¢ncia global para uso direto â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_compositor = CompositorAcompanhamento()



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
    CompatÃ­vel com a assinatura de gerar_acompanhamento_dinamico() do avaliacao.py,
    mas com camadas adicionais de personalizaÃ§Ã£o.
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

