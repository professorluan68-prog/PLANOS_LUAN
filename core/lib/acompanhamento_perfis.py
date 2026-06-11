"""Geradores específicos de acompanhamento por disciplina e por aula."""

import re
from typing import Callable

from core.lib.classificador import contem_termos, normalizar_texto


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
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["producao_projeto", "seminario", "cartilha", "campanha", "apresentacao", "produto final"]):
        return [
            "Verificar se o produto traz informações científicas corretas.",
            "Observar se usam vocabulário científico nas explicações.",
            "Acompanhar a clareza e colaboração dos grupos.",
        ]

    if any(k in base for k in ["estudo_caso", "estudo de caso", "situacao-problema", "situacao problema", "caso"]):
        return [
            "Verificar se identificam o problema do caso e reúnem evidências.",
            "Observar se relacionam causa, consequência e conceito científico.",
            "Acompanhar registros, avaliando coerência e conceitos científicos.",
        ]

    if any(k in base for k in ["leitura_analise", "noticia", "reportagem", "dados", "inpe", "ibge", "fonte", "hora da leitura"]):
        return [
            "Verificar se localizam informações centrais no texto ou fonte.",
            "Observar se relacionam leitura e conceitos a saúde e ambiente.",
            "Acompanhar respostas escritas e justificativas com evidências.",
        ]

    if any(k in base for k in ["revisao_retomada", "relembre", "exercicio resolvido", "retomar"]):
        return [
            "Verificar se recordam conceitos anteriores relacionados à aula.",
            "Observar se compreendem o exemplo e o aplicam em questões.",
            "Acompanhar os registros, identificando pontos para retomada.",
        ]

    return [
        "Verificar se os estudantes compreendem o conceito cientifico central e conseguem relaciona-lo a exemplos do cotidiano.",
        "Observar a participacao no Pause e responda, considerando justificativas e correcao dialogada.",
        "Acompanhar a atividade escrita, conferindo se as respostas usam evidencias, vocabulario cientifico e sintese propria.",
    ]


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


GeradorAcompanhamento = Callable[[str, str, str], list[str]]

GERADORES_ACOMPANHAMENTO_POR_PERFIL: dict[str, GeradorAcompanhamento] = {
    "ingles": _acompanhamento_ingles,
    "lingua_portuguesa_ef": _acompanhamento_lingua_portuguesa,
    "lingua_portuguesa_em": _acompanhamento_lingua_portuguesa,
    "leitura_redacao": _acompanhamento_lingua_portuguesa,
    "matematica": _acompanhamento_matematica,
    "ciencias_ef": _acompanhamento_ciencias,
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
