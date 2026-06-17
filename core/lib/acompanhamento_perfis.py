"""Geradores específicos de acompanhamento por disciplina e por aula."""

import re
from typing import Callable

from core.lib.classificador import contem_termos, normalizar_texto


def _base_tem_termo(base: str, termo: str) -> bool:
    termo = re.escape(normalizar_texto(termo))
    termo = termo.replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<!\w){termo}(?!\w)", base, flags=re.I))


def _base_tem_algum(base: str, termos: list[str]) -> bool:
    return any(_base_tem_termo(base, termo) for termo in termos)


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


def _tema_astronomia(base: str) -> bool:
    return _base_tem_algum(
        base,
        [
            "astronomia",
            "observacao do ceu",
            "observacao da lua",
            "sol",
            "terra",
            "lua",
            "eclipse",
            "eclipses",
            "fases da lua",
            "rotacao",
            "translacao",
            "precessao",
            "orbita",
            "estacoes do ano",
            "estacao do ano",
            "caixa lunar",
        ],
    )


def _grupo_modelagem_astronomia(base: str) -> str:
    if _base_tem_algum(
        base,
        [
            "rotacao",
            "translacao",
            "precessao",
            "orbita",
            "eixo",
            "inclinacao",
            "estacoes do ano",
            "estacao do ano",
        ],
    ):
        return "movimentos_terra"
    if _base_tem_algum(
        base,
        [
            "fases da lua",
            "movimentos da lua",
            "observacao da lua",
            "sistema sol",
            "sol terra lua",
            "eclipse",
            "eclipses",
            "caixa lunar",
            "lua",
        ],
    ):
        return "sistema_sol_terra_lua"
    if _base_tem_algum(base, ["astronomia", "observacao do ceu"]):
        return "observacao_ceu"
    return "geral"


def _base_indica_matematica(base: str) -> bool:
    return any(
        termo in base
        for termo in [
            "matematica",
            "porcent",
            "media aritmetica",
            "volume",
            "area",
            "esfera",
            "equacao",
            "funcao",
            "juros",
            "gols",
            "notas",
            "resolucao de problemas",
        ]
    )


def _base_indica_historia(base: str) -> bool:
    return any(
        termo in base
        for termo in [
            "historia",
            "reinado",
            "regencial",
            "revolta",
            "revoltas",
            "imperio",
            "imperial",
            "cabanagem",
            "sabinada",
            "farrapos",
            "balaiada",
            "males",
        ]
    )


def gerar_acompanhamento_especifico_por_aula(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
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
    if _grupo_modelagem_astronomia(base) == "observacao_ceu":
        return [
            "Verificar se os estudantes relacionam a observação do céu aos conhecimentos astronômicos e aos usos históricos ou culturais discutidos na aula.",
            "Observar se interpretam imagens, relatos ou registros do material para explicar como diferentes povos observaram os astros.",
            "Conferir se as respostas utilizam vocabulário científico coerente ao tratar de céu, estrelas, astros, calendários ou orientação.",
        ]
    if "tabela" in base and _tema_astronomia(base):
        return [
            f"Verificar se os estudantes preenchem a tabela de {tema} com informacoes corretas e comparaveis.",
            f"Observar se relacionam os dados da tabela aos conceitos, movimentos ou caracteristicas estudadas em {tema}.",
            "Conferir se justificam oralmente ou por escrito as conclusoes registradas a partir da leitura da tabela.",
        ]
    if "tabela" in base and (_base_indica_matematica(base) or _base_indica_historia(base)):
        return []
    if "tabela" in base:
        return [
            "Verificar se os estudantes preenchem a tabela com informações corretas e completas.",
            "Observar se relacionam os dados da tabela aos conceitos discutidos na aula.",
            "Conferir se justificam oralmente ou por escrito as escolhas registradas na atividade.",
        ]
    return []


def _acompanhamento_lingua_portuguesa(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["autoavaliacao", "avaliando com consciencia", "concluindo a jornada", "portfolio", "rubrica", "percurso de aprendizagem"]):
        return [
            "☑ Verificar se o estudante retoma evidências do próprio percurso para reconhecer avanços e dificuldades.",
            "☑ Observar se o estudante registra metas ou próximos passos coerentes com os critérios de autoavaliação.",
            "☑ Acompanhar a participação na socialização das percepções de aprendizagem de forma respeitosa.",
        ]

    if any(k in base for k in ["apresentacao oral", "apresentacoes orais", "podcast", "vlog", "video", "audiovisual", "esquete"]):
        return [
            "☑ Verificar se os estudantes organizam a fala ou o roteiro considerando público, finalidade e conteúdo estudado.",
            "☑ Observar clareza, postura, escuta e respeito aos turnos durante apresentações, gravações ou socializações.",
            "☑ Acompanhar os registros e ajustes realizados a partir dos critérios combinados com a turma.",
        ]

    if any(k in base for k in ["trilha", "alice no pais das maravilhas", "pequeno principe", "peter pan", "leitura compartilhada", "predicao guiada"]):
        return [
            "Observar a participação nas discussões sobre a narrativa lida.",
            "Verificar a compreensão dos fatos e personagens do trecho.",
            "Acompanhar os registros escritos nas atividades de interpretação.",
        ]

    if any(k in base for k in ["versao final", "redacao paulista", "revisao orientada", "reescrita", "rascunho"]):
        return [
            "Verificar se revisam o texto considerando coerência e gênero.",
            "Observar a participação na revisão e reescrita do texto.",
            "Acompanhar a realização de ajustes antes da versão final.",
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

    if any(k in base for k in ["texto multissemiotico", "linguagem verbal", "linguagem nao verbal"]):
        return [
            "Observar se os estudantes relacionam linguagem verbal e não verbal na construção dos sentidos do texto.",
            "Verificar a participação nas leituras, análises e discussões sobre os recursos utilizados.",
            "Acompanhar os registros produzidos durante as atividades e retomadas coletivas.",
        ]

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


def _acompanhamento_projeto_vida(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import (
        _PV_CONSCIENCIA_SOCIAL,
        _PV_CONVIVENCIA,
        _PV_ENCERRAMENTO,
        _PV_FUTUREME,
        _PV_PRODUCAO_COLETIVA,
    )

    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if contem_termos(base, _PV_FUTUREME):
        return [
            "☑ Observar se o estudante completa o questionário com autenticidade.",
            "☑ Verificar se o estudante analisa o relatório final de forma crítica.",
            "☑ Acompanhar a troca em trios sobre os resultados e o futuro.",
        ]

    if contem_termos(base, _PV_ENCERRAMENTO):
        return [
            "☑ Observar se identifica descobertas sobre si ao longo do bimestre.",
            "☑ Verificar se indica mudanças na forma de agir ou ver o mundo.",
            "☑ Acompanhar a escolha de compromissos no encerramento.",
        ]

    if contem_termos(base, _PV_CONSCIENCIA_SOCIAL):
        return [
            "☑ Observar se compreende a diferença entre privilégios e desvantagens.",
            "☑ Verificar se identifica padrões de representação no meio digital.",
            "☑ Acompanhar registros sobre mudanças frente a desigualdades.",
        ]

    if contem_termos(base, _PV_CONVIVENCIA):
        return [
            "☑ Observar se participa do círculo com escuta ativa e respeito.",
            "☑ Verificar se propõe soluções para o dilema discutido.",
            "☑ Acompanhar a escrita de ações concretas para o compromisso.",
        ]

    if contem_termos(base, _PV_PRODUCAO_COLETIVA):
        return [
            "☑ Observar se elaboram produto com objetivo e mensagem claros.",
            "☑ Verificar a participação ativa de todos os integrantes do grupo.",
            "☑ Acompanhar a apresentação e explicação das escolhas do grupo.",
        ]

    return [
        "☑ Observar se indica possibilidades de futuro ligadas a interesses.",
        "☑ Verificar se reconhece fatores externos que afetam escolhas.",
        "☑ Acompanhar as trocas e sugestões pertinentes em duplas.",
    ]


def _acompanhamento_matematica(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["verificacao", "revisao", "khan", "relembre", "bit.ly", "khanmigo"]):
        return [
            "☑ Observar a autonomia na resolução das atividades da aula.",
            "☑ Verificar se justificam as estratégias e interpretam resultados.",
            "☑ Acompanhar se identificam e corrigem erros no raciocínio.",
        ]

    if any(k in base for k in ["fracao", "fracoes", "decimal", "decimais", "adicao", "adicoes", "subtracao", "subtracoes", "multiplicacao", "multiplicacoes", "divisao", "divisoes", "racionais", "dizima", "dizimas", "operacao", "operacoes", "potencia", "potencias", "raiz", "raizes", "numero", "numeros"]):
        return [
            "☑ Avaliar se os estudantes conseguem transitar entre diferentes representações numéricas (como fração e decimal) na resolução de problemas.",
            "☑ Acompanhar se realizam os procedimentos de cálculo manual passo a passo de forma organizada e precisa.",
            "☑ Verificar se a turma valida os resultados obtidos por meio de estimativas ou operações inversas.",
        ]

    if any(k in base for k in ["proporcao", "proporcoes", "proporcional", "proporcionais", "razao", "razoes", "regra de tres", "partes desiguais", "partes proporcionais", "grandeza", "grandezas", "inversamente", "diretamente", "escala", "escalas"]):
        return [
            "☑ Acompanhar se os estudantes identificam corretamente a relação de dependência entre as grandezas (direta ou inversamente proporcional).",
            "☑ Verificar se utilizam a constante de proporcionalidade de maneira adequada na estruturação dos cálculos.",
            "☑ Observar se aplicam corretamente a regra de três simples ou composta e validam a coerência física/prática do resultado.",
        ]

    if any((_base_tem_termo(base, k) if k in {"pa", "pg"} else k in base) for k in ["sequencia", "sequencias", "progressao", "progressoes", "pa", "pg", "regularidade", "regularidades", "generalizacao", "generalizacoes", "padrao numerico"]):
        return [
            "☑ Verificar se os estudantes deduzem o padrão ou regularidade numérica de forma indutiva a partir dos termos iniciais.",
            "☑ Acompanhar se conseguem formular e aplicar a expressão geral ou termo geral da sequência de maneira lógica.",
            "☑ Observar se identificam a diferença essencial entre progressões aritméticas e geométricas.",
        ]

    if any(k in base for k in ["algoritmo", "algoritmos", "fluxograma", "fluxogramas"]):
        return [
            "☑ Observar se os estudantes interpretam corretamente as decisões e ramificações lógicas propostas no fluxograma.",
            "☑ Acompanhar se conseguem traduzir a sequência lógica do problem em passos estruturados e ordenados (algoritmos).",
            "☑ Verificar se realizam testes de mesa para validar a corretude do algoritmo em diferentes cenários.",
        ]

    if any(k in base for k in ["grafico", "representacao grafica", "plano cartesiano", "eixo", "tabela", "pares ordenados"]):
        return [
            "☑ Verificar a interpretação de tabelas e gráficos da aula.",
            "☑ Acompanhar se utilizam dados da aula para justificar respostas.",
            "☑ Observar se relacionam a representação gráfica à situação real.",
        ]

    if any(k in base for k in ["resolucao de problemas", "metodo de polya", "polya"]):
        return [
            "☑ Verificar se aplicam etapas do método de resolução de problemas.",
            "☑ Acompanhar se justificam a estratégia e validam a solução.",
            "☑ Observar se conseguem resolver problemas semelhantes de forma autônoma.",
        ]

    return [
        "☑ Verificar se os estudantes identificam corretamente os dados necessários e compreendem o que está sendo pedido em cada situação.",
        "☑ Acompanhar se a turma reconhece a relação entre o resultado obtido e o contexto da situação estudada, evitando respostas apenas numéricas.",
        "☑ Conferir se os registros finais articulam cálculo, interpretação e conclusão, demonstrando compreensão do conceito trabalhado.",
    ]


def _acompanhamento_ciencias(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))
    tipo = detectar_tipo_aula(desenvolvimento, tema, "Ciencias")

    if tipo == "analise_dados":
        return [
            "☑ Verificar se os estudantes localizam titulo, fonte, legenda, unidades e valores relevantes nos dados analisados.",
            "☑ Observar se a turma compara informacoes e utiliza evidencias do material para justificar as conclusoes.",
            "☑ Conferir se os registros relacionam os dados ao fenomeno estudado com vocabulario cientifico adequado.",
        ]

    if tipo == "modelagem_cientifica" and _tema_astronomia(base):
        grupo_astronomia = _grupo_modelagem_astronomia(base)
        if grupo_astronomia == "movimentos_terra":
            return [
                f"☑ Verificar se os estudantes representam corretamente em {tema} o eixo, a orbita e os movimentos da Terra discutidos na aula.",
                "☑ Observar se a turma utiliza o modelo para explicar relacoes entre rotacao, translacao, inclinacao do eixo, duracao do dia ou estacoes do ano.",
                "☑ Conferir se registros, falas, setas ou legendas mostram como o modelo ajuda a compreender posicoes, sentidos e efeitos desses movimentos.",
            ]
        if grupo_astronomia == "sistema_sol_terra_lua":
            return [
                f"☑ Verificar se os estudantes representam corretamente em {tema} as posicoes relativas entre Sol, Terra e Lua, bem como fases, movimentos ou eclipses.",
                "☑ Observar se a turma utiliza o modelo para explicar iluminacao, alinhamentos e mudancas aparentes sem confundir o fenomeno com a representacao.",
                "☑ Conferir se registros, falas, legendas ou apresentacoes mostram relacoes coerentes entre fonte de luz, sombra, movimento e observacao do ceu.",
            ]
        return [
            f"☑ Verificar se os estudantes representam corretamente em {tema} os movimentos, alinhamentos, fases ou posicoes relativas discutidos na aula.",
            "☑ Observar se a turma utiliza o modelo para explicar o fenomeno estudado, sem confundir a representacao com a realidade.",
            "☑ Conferir se registros, falas, legendas ou apresentacoes mostram como o modelo ajuda a compreender o conceito cientifico central.",
        ]
    if tipo == "modelagem_cientifica":
        return [
            f"☑ Verificar se os estudantes identificam os componentes principais de {tema} e os relacionam corretamente a suas funcoes.",
            "☑ Observar se a turma reconhece que o modelo representa e simplifica a realidade, sem confundir a representacao com o objeto real.",
            "☑ Conferir se os registros ou apresentacoes explicam como o modelo ajuda a compreender estrutura, processo ou funcionamento.",
        ]

    if tipo == "situacao_problema":
        return [
            "☑ Verificar se os estudantes identificam causas, impactos, agentes envolvidos e criterios de analise no cenario proposto.",
            "☑ Observar se a turma justifica as solucoes com base em conceitos cientificos, dados ou evidencias do material.",
            "☑ Conferir se os registros articulam problema, proposta de acao, responsabilidade coletiva e viabilidade das medidas.",
        ]

    if tipo == "pratica_experimental":
        return [
            "☑ Verificar se os estudantes acompanham o procedimento, observam o fenomeno e registram etapas sem perder os objetivos da pratica.",
            "☑ Observar se a turma compara resultados e explica as observacoes com base no conceito cientifico estudado.",
            "☑ Conferir se os registros apresentam evidencias, conclusoes coerentes e uso adequado do vocabulario da aula.",
        ]

    if tipo == "investigativa":
        return [
            "☑ Verificar se os estudantes formulam hipoteses iniciais e as revisam a partir das evidencias observadas.",
            "☑ Observar se a turma registra dados, pistas ou resultados relevantes durante a investigacao.",
            "☑ Conferir se as explicacoes finais articulam pergunta inicial, evidencias analisadas e conceito cientifico trabalhado.",
        ]

    if tipo == "impacto_socioambiental":
        return [
            f"☑ Verificar se os estudantes relacionam {tema} a impactos, causas e consequencias ambientais, sociais ou de saude.",
            "☑ Observar se a turma utiliza dados, noticias ou exemplos do material para sustentar analises e posicionamentos.",
            "☑ Conferir se os registros incluem responsabilidades dos agentes envolvidos e propostas de acao coerentes com os conceitos estudados.",
        ]

    if tipo == "producao_projeto" or any(k in base for k in ["seminario", "cartilha", "campanha", "apresentacao", "produto final"]):
        return [
            "☑ Verificar se o produto traz informacoes cientificas corretas e coerentes com o tema estudado.",
            "☑ Observar se os estudantes usam vocabulario cientifico nas explicacoes e apresentacoes.",
            "☑ Acompanhar a clareza da comunicacao e a colaboracao dos grupos durante a socializacao.",
        ]

    if tipo == "estudo_caso" or any(k in base for k in ["estudo_caso", "estudo de caso", "caso"]):
        return [
            "☑ Verificar se identificam o problema do caso e reunem evidencias relevantes para analisa-lo.",
            "☑ Observar se relacionam causa, consequencia e conceito cientifico nas explicacoes.",
            "☑ Acompanhar os registros, avaliando coerencia das conclusoes e uso de conceitos cientificos.",
        ]

    if tipo == "leitura_analise" or any(k in base for k in ["noticia", "reportagem", "inpe", "ibge", "fonte", "hora da leitura"]):
        return [
            "☑ Verificar se localizam informacoes centrais no texto, noticia ou fonte analisada.",
            "☑ Observar se relacionam a leitura aos conceitos cientificos e a questoes de saude, ambiente ou sociedade.",
            "☑ Acompanhar respostas escritas e justificativas com base em evidencias do material.",
        ]

    if tipo == "revisao_retomada" or any(k in base for k in ["relembre", "exercicio resolvido", "retomar"]):
        return [
            f"☑ Verificar se retomam os conceitos ja estudados sobre {tema} e os conectam ao novo foco da aula.",
            "☑ Observar se utilizam registros anteriores, esquemas ou respostas ja produzidas para revisar explicacoes e corrigir duvidas.",
            "☑ Acompanhar os registros, identificando quais relacoes cientificas ja foram consolidadas e quais ainda precisam de reforco conceitual.",
        ]
    return [
        "☑ Verificar se os estudantes compreendem o conceito cientifico central e conseguem relaciona-lo a exemplos do cotidiano.",
        "☑ Observar a participacao no Pause e responda, considerando justificativas e correcao dialogada.",
        "☑ Acompanhar a atividade escrita, conferindo se as respostas usam evidencias, vocabulario cientifico e sintese propria.",
    ]


def _acompanhamento_ciencias_reforcado(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    itens = _acompanhamento_ciencias(tema, aprendizagem, desenvolvimento)
    texto = normalizar_texto(" ".join(itens))
    gatilhos_genericos = [
        "conceito cientifico central",
        "participacao no pause e responda",
        "atividade escrita",
    ]
    if all(gatilho in texto for gatilho in gatilhos_genericos):
        return [
            f"☑ Verificar se os estudantes compreendem o conceito cientifico central de {tema} e conseguem relaciona-lo a exemplos, fenomenos ou situacoes discutidas na aula.",
            f"☑ Observar se utilizam vocabulario cientifico, justificativas e evidencias do material ao explicar o que aprenderam sobre {tema}.",
            f"☑ Acompanhar a atividade escrita, conferindo se os registros apresentam clareza, sintese propria e relacao consistente com o foco de estudo de {tema}.",
        ]
    return itens


def _acompanhamento_biologia(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    tipo = detectar_tipo_aula(desenvolvimento, tema, "Biologia")

    if tipo == "etico_biotecnologico":
        return [
            f"☑ Verificar se os estudantes identificam as implicações éticas, legais ou sociais de {tema} e explicam a importância do consentimento e da bioética.",
            "☑ Observar se a turma analisa a relação entre autonomia e dignidade humana a partir dos princípios da integridade científica.",
            "☑ Acompanhar se os registros individuais analisam o estudo de caso fundamentando-se nas evidências científicas discutidas na aula.",
        ]

    if tipo == "molecular_genetico":
        return [
            f"☑ Verificar se os estudantes compreendem a estrutura molecular ou o cruzamento genético envolvido em {tema}.",
            "☑ Observar se explicam de forma clara a relação de causa e consequência entre genótipo e fenótipo na escala molecular.",
            "☑ Acompanhar se a turma utiliza diagramas (como quadro de Punnett ou heredogramas) para resolver e justificar os problemas genéticos.",
        ]

    if tipo == "debate_critico":
        return [
            f"☑ Verificar se os estudantes utilizam argumentos científicos sólidos sobre {tema} para combater preconceitos históricos ou pseudociências.",
            "☑ Observar se a turma analisa a variabilidade genética humana defendendo a inexistência de raças biológicas sob a perspectiva da genética moderna.",
            "☑ Acompanhar se os grupos elaboram propostas ou planos de ação fundamentados no rigor factual e nos direitos humanos.",
        ]

    if tipo == "aplicacao_biotecnologica":
        return [
            f"☑ Verificar se os estudantes descrevem as etapas e o mecanismo biológico de produção da tecnologia sobre {tema}.",
            "☑ Observar se a turma reconhece o papel de instituições públicas de pesquisa (como Butantan e Fiocruz) na soberania e saúde coletiva.",
            "☑ Acompanhar se os registros em duplas articulam aspectos de propriedade intelectual (patentes) e equidade de acesso no SUS.",
        ]

    if tipo == "revisao_aprofundamento":
        return [
            f"☑ Verificar se os estudantes retomam e integram os conceitos biológicos e moleculares fundamentais de {tema}.",
            "☑ Observar se a turma resolve e justifica coletivamente questões complexas e problemas de vestibulares ou do material.",
            "☑ Acompanhar se as respostas escritas mostram consolidação dos conceitos principais e a identificação de lacunas a serem retomadas.",
        ]

    if tipo == "aula_desafio":
        return [
            f"☑ Verificar se identificam o problema do caso e formulam hipóteses.",
            "☑ Observar se selecionam evidências para justificar explicações.",
            "☑ Acompanhar se os registros trazem conclusões sobre o caso.",
        ]

    if tipo == "aula_pratica":
        return [
            f"☑ Verificar se relacionam a prática aos conceitos científicos.",
            "☑ Observar se registram observações e comparam resultados da prática.",
            "☑ Acompanhar se explicam como a prática ajuda a compreender o tema.",
        ]

    if tipo == "revisao_consolidacao":
        return [
            f"☑ Verificar se os estudantes retomam conceitos e termos ligados a {tema}, diferenciando ideias próximas sem depender apenas da memória literal do slide.",
            "☑ Observar se a turma participa do quiz ou da revisão usando justificativas, comparações e respostas em linguagem própria.",
            "☑ Acompanhar se os registros revelam consolidação conceitual e identificação das dúvidas que ainda precisam de retomada.",
        ]

    if tipo == "impacto_socioambiental":
        return [
            f"☑ Verificar se os estudantes relacionam {tema} a impactos ambientais, sociais ou de saúde pública, usando dados e exemplos do material.",
            "☑ Observar se a turma interpreta gráficos, notícias, esquemas ou imagens com base em evidências, e não apenas em opiniões soltas.",
            "☑ Acompanhar se os registros articulam ciência, responsabilidade coletiva e possíveis soluções ou medidas de enfrentamento.",
        ]

    return [
        f"☑ Verificar se os estudantes compreendem o conceito biológico central de {tema} e conseguem explicá-lo em etapas com linguagem científica adequada.",
        "☑ Observar a participação no Pause e responda, considerando se a turma justifica respostas antes de avançar para a atividade de aplicação.",
        "☑ Acompanhar se os registros usam evidências, exemplos e síntese própria para relacionar o conteúdo a situações reais.",
    ]


def _acompanhamento_ingles(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    tipo = detectar_tipo_aula(desenvolvimento, tema, "Língua Inglesa")
    conteudo = tema

    if tipo == "leitura_em":
        return [
            f"☑ Verificar se identificam informações centrais e específicas no texto.",
            "☑ Acompanhar se aplicam estratégias de leitura para resolver as questões.",
            "☑ Observar se eliminam alternativas incorretas com base no texto.",
        ]
    if tipo == "gramatica":
        return [
            f"☑ Verificar se os estudantes identificam e utilizam corretamente a estrutura gramatical de {conteudo} nos exercícios propostos.",
            f"☑ Acompanhar se a turma consegue produzir frases em inglês usando {conteudo} de forma comunicativa, não apenas mecânica.",
            "☑ Observar se os estudantes reconhecem os exemplos da estrutura gramatical em textos e áudios autênticos, conectando a regra ao uso real.",
        ]
    if tipo == "listening":
        return [
            f"☑ Verificar se os estudantes identificam as informações gerais e específicas solicitadas durante a escuta do áudio sobre {conteudo}.",
            "☑ Acompanhar se a turma utiliza o vocabulário apresentado antes da escuta para compreender o áudio, sem depender de tradução.",
            "☑ Observar se os estudantes conseguem completar as atividades de compreensão oral com base no que ouviram, justificando as respostas.",
        ]
    if tipo == "producao_oral":
        return [
            f"☑ Verificar se os estudantes produzem frases e diálogos em inglês sobre {conteudo} de forma comunicativa, utilizando o vocabulário e as estruturas trabalhadas.",
            "☑ Acompanhar se a turma pratica a pronúncia correta das palavras e expressões novas durante as atividades orais.",
            "☑ Observar se os estudantes interagem em inglês com os colegas durante as atividades em duplas, demonstrando iniciativa comunicativa.",
        ]
    if tipo == "leitura_literaria":
        return [
            f"☑ Verificar se os estudantes identificam elementos do texto literário sobre {conteudo}, analisando a caracterização de personagens e cenários.",
            "☑ Acompanhar se a turma utiliza as estratégias de leitura literária apresentadas para analisar o tom das descrições.",
            "☑ Observar se os estudantes conseguem explicar o conflito do trecho literário com suas palavras em inglês.",
        ]
    if tipo == "musica":
        return [
            f"☑ Verificar se os estudantes identificam a estrutura gramatical ou o vocabulário trabalhado na letra da música sobre {conteudo}.",
            "☑ Acompanhar se os estudantes compreendem o tema central da canção através da leitura e audição da letra.",
            "☑ Observar se a turma participa ativamente da escuta e da prática musical, realizando os exercícios de fixação propostos.",
        ]
    if tipo == "revisao":
        return [
            f"☑ Verificar se os estudantes revisam e consolidam os principais pontos lexicais e gramaticais sobre {conteudo} trabalhados no bloco.",
            "☑ Acompanhar se os estudantes demonstram autonomia na resolução das atividades variadas de prática e revisão.",
            "☑ Observar se a turma consegue apontar em inglês o que aprendeu a fazer ao longo deste bloco de aulas.",
        ]
    return [
        f"☑ Verificar se os estudantes compreendem e utilizam o vocabulário ou conteúdo de {conteudo} nas atividades propostas.",
        "☑ Acompanhar se a turma produz em inglês (oral ou escrito) usando os recursos linguísticos trabalhados na aula.",
        f"☑ Observar se os estudantes conseguem explicar com suas palavras o que aprenderam sobre {conteudo}, em inglês.",
    ]


def _acompanhamento_lingua_portuguesa_em(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula, normalizar_texto
    import re
    tipo_aula = detectar_tipo_aula(desenvolvimento, tema, "Língua Portuguesa", turma="EM")
    
    tema_norm = normalizar_texto(tema)
    aprend_norm = normalizar_texto(aprendizagem)
    
    # Identificar se há termos gramaticais específicos ou de movimentos literários no tema/aprendizagem
    movimento = ""
    movimentos_list = ["trovadorismo", "modernismo", "romantismo", "realismo", "parnasianismo", "simbolismo", "naturalismo", "classicismo"]
    for mov in movimentos_list:
        if re.search(r'\b' + mov + r'\b', tema_norm) or re.search(r'\b' + mov + r'\b', aprend_norm):
            movimento = mov.title()
            break
    if not movimento:
        movimento = tema
        
    gramatica = ""
    gramatica_mapping = [
        ("tempo verbal", r"\btempo(s)? verbal(is)?\b"),
        ("modo verbal", r"\bmodo(s)? verbal(is)?\b"),
        ("sintaxe", r"\bsintaxe\b"),
        ("ortografia", r"\bortografia\b"),
        ("oracao", r"\boraca(o|oes)\b"),
        ("regencia", r"\bregencia\b"),
        ("concordancia", r"\bconcordancia\b"),
        ("coesao", r"\bcoesao\b"),
        ("verbos", r"\bverbo(s)?\b"),
        ("adjetiva", r"\badjetiva(s)?\b"),
        ("coordenada", r"\bcoordenada(s)?\b"),
        ("subordinada", r"\bsubordinada(s)?\b"),
        ("polissemia", r"\bpolissemia\b"),
    ]
    for gram_key, pattern in gramatica_mapping:
        if re.search(pattern, tema_norm) or re.search(pattern, aprend_norm):
            gramatica = gram_key
            break
    if not gramatica:
        gramatica = "recursos gramaticais/linguísticos"
        
    genero = ""
    generos_mapping = [
        ("diario", r"\bdiario(s)?\b"),
        ("manifesto", r"\bmanifesto(s)?\b"),
        ("playlist", r"\bplaylist(s)?\b"),
        ("cronica", r"\bcronica(s)?\b"),
        ("noticia", r"\bnoticia(s)?\b"),
        ("reportagem", r"\breportagem(ns)?\b"),
        ("resenha", r"\bresenha(s)?\b"),
        ("debate", r"\bdebate(s)?\b"),
        ("podcast", r"\bpodcast(s)?\b"),
        ("editorial", r"\beditorial(is)?\b"),
        ("carta", r"\bcarta(s)?\b"),
        ("vlog", r"\bvlog(s)?\b"),
        ("meme", r"\bmeme(s)?\b"),
        ("infografico", r"\binfografico(s)?\b"),
        ("anuncio", r"\banuncio(s)?\b"),
        ("publicidade", r"\bpublicidade(s)?\b"),
        ("propaganda", r"\bpropaganda(s)?\b"),
    ]
    for gen_key, pattern in generos_mapping:
        if re.search(pattern, tema_norm) or re.search(pattern, aprend_norm):
            if gen_key in ["anuncio", "publicidade", "propaganda"]:
                genero = "Anúncio publicitário"
            else:
                genero = gen_key.title()
            break
    if not genero:
        genero = "gênero estudado"

    if tipo_aula == "literatura":
        return [
            f"☑ Observar se o estudante identifica as características de {movimento} no texto lido.",
            f"☑ Verificar se o estudante relaciona o contexto histórico com as marcas estéticas da obra/trecho de {tema} analisado.",
            "☑ Acompanhar se o estudante sustenta oralmente ou por escrito suas interpretações com elementos do texto.",
        ]
    elif tipo_aula == "genero_textual":
        return [
            f"☑ Observar se o estudante reconhece as características estruturais e linguísticas do gênero {genero}.",
            f"☑ Verificar se o estudante interpreta adequadamente o propósito comunicativo do texto lido.",
            f"☑ Avaliar se o estudante aplica os {gramatica} de forma contextualizada em suas respostas escritas.",
        ]
    elif tipo_aula == "producao_textual":
        return [
            f"☑ Observar se o estudante planeja a produção considerando tema, estrutura e público do gênero {genero}.",
            f"☑ Verificar se o estudante produz texto adequado às características do gênero, com coesão e coerência.",
            f"☑ Avaliar se o estudante revisa e aprimora sua produção a partir das devolutivas dos colegas.",
        ]
    elif tipo_aula == "pratica_oral":
        return [
            f"☑ Observar se o estudante argumenta de forma fundamentada, respeitando seu turno de fala.",
            f"☑ Verificar se o estudante escuta ativamente e responde aos argumentos dos colegas com contra-argumentos.",
            f"☑ Avaliar se o estudante respeita as regras do debate e mantém postura adequada ao gênero oral formal.",
        ]
    else:
        # Fallback padrão
        return [
            f"☑ Observar se o estudante reconhece as marcas textuais e características do tema {tema}.",
            "☑ Verificar se o estudante interpreta e compreende as ideias principais do texto âncora.",
            f"☑ Avaliar se o estudante aplica os recursos de linguagem e gramática estudados em {tema} de forma contextualizada.",
        ]


GeradorAcompanhamento = Callable[[str, str, str], list[str]]

GERADORES_ACOMPANHAMENTO_POR_PERFIL: dict[str, GeradorAcompanhamento] = {
    "ingles": _acompanhamento_ingles,
    "lingua_portuguesa_ef": _acompanhamento_lingua_portuguesa,
    "lingua_portuguesa_em": _acompanhamento_lingua_portuguesa_em,
    "leitura_redacao": _acompanhamento_lingua_portuguesa,
    "matematica": _acompanhamento_matematica,
    "ciencias_ef": _acompanhamento_ciencias_reforcado,
    "biologia": _acompanhamento_biologia,
    "projeto_de_vida": _acompanhamento_projeto_vida,
}


def gerar_acompanhamento_por_perfil(
    perfil: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
) -> list[str]:
    gerador = GERADORES_ACOMPANHAMENTO_POR_PERFIL.get(perfil)
    if not gerador:
        return []
    return gerador(tema, aprendizagem, desenvolvimento)
