"""Regras específicas de acessibilidade por disciplina e por aula."""

import re
from typing import Callable

from core.lib.classificador import contem_termos, normalizar_texto


def _base_tem_termo(base: str, termo: str) -> bool:
    termo = re.escape(normalizar_texto(termo))
    termo = termo.replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<!\w){termo}(?!\w)", base, flags=re.I))


def _base_tem_algum(base: str, termos: list[str]) -> bool:
    return any(_base_tem_termo(base, termo) for termo in termos)


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


def _tem_marcador_visao(base: str) -> bool:
    base_clean = base.replace("de olho", "")
    return bool(
        re.search(
            r"\b(?:olho|retina|cornea|pupila|cristalino|sistema visual|formacao da imagem|caminho da luz|visao)\b",
            base_clean,
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


def gerar_acessibilidade_especifica_por_aula(
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
        vocab = "vocabulário científico" if any(k in base for k in ["ciencia", "biologia", "quimica", "fisica", "corpo", "celula", "anatomia"]) else "vocabulário adequado ao tema da aula"
        return [
            "Oferecer roteiro com perguntas-chave para organizar a escrita do texto-síntese.",
            "Destacar palavras-chave no quadro e permitir produção inicial em tópicos antes do texto final.",
            f"Realizar mediação individual para revisão de clareza, sequência de ideias e {vocab}.",
        ]
    if _grupo_modelagem_astronomia(base) == "observacao_ceu":
        return [
            "Ampliar a imagem do ceu, das estrelas ou dos astros citados na aula, destacando legendas e elementos essenciais antes da analise individual.",
            "Destacar no quadro palavras-chave como astros, calendario, orientacao e observacao para apoiar a leitura e a participacao da turma.",
            "Permitir registro em topicos, desenho identificado, setas ou explicacao oral mediada ao relacionar observacao do ceu e conhecimentos historicos.",
        ]
    if "tabela" in base and not recursos and _tema_astronomia(base):
        return [
            f"Preencher coletivamente uma linha da tabela com um exemplo ligado a {tema} antes do trabalho autonomo.",
            "Destacar no quadro os conceitos, movimentos ou caracteristicas que a turma precisara comparar na tabela.",
            "Permitir consulta ao material e ao quadro durante a atividade, com apoio em dupla para leitura dos comandos e conferencia dos registros.",
        ]
    if "tabela" in base and not recursos and (_base_indica_matematica(base) or _base_indica_historia(base)):
        return []
    if "tabela" in base and not recursos:
        return [
            "Preencher uma linha da tabela como exemplo antes do trabalho autônomo.",
            "Organizar pares produtivos para apoiar leitura dos comandos e preenchimento dos campos.",
            "Permitir consulta constante ao material digital e ao quadro durante a atividade.",
        ]
    return []


def _acessibilidade_lingua_portuguesa(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["autoavaliacao", "avaliando com consciencia", "concluindo a jornada", "portfolio", "rubrica", "percurso de aprendizagem"]):
        return [
            "Disponibilizar roteiro simples com critérios de autoavaliação e exemplos de evidências do percurso.",
            "Permitir registro em tópicos, frases curtas ou resposta oral mediada antes do preenchimento final.",
            "Retomar coletivamente palavras-chave como avanço, dificuldade, estratégia e próxima meta.",
        ]

    if any(k in base for k in ["apresentacao oral", "apresentacoes orais", "podcast", "vlog", "video", "audiovisual", "esquete"]):
        return [
            "Disponibilizar roteiro de fala ou gravação com começo, desenvolvimento, fechamento e tempo previsto.",
            "Oferecer lista curta de critérios sobre clareza, postura, escuta e relação com o conteúdo estudado.",
            "Permitir apresentação em dupla, apoio por tópicos ou ensaio mediado antes da socialização.",
        ]

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
    from core.lib.classificador import (
        _PV_CONSCIENCIA_SOCIAL,
        _PV_CONVIVENCIA,
        _PV_ENCERRAMENTO,
        _PV_FUTUREME,
        _PV_PRODUCAO_COLETIVA,
    )

    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if contem_termos(base, _PV_FUTUREME):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["futureme"])
    if contem_termos(base, _PV_ENCERRAMENTO):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["encerramento"])
    if contem_termos(base, _PV_CONSCIENCIA_SOCIAL):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["consciencia_social"])
    if contem_termos(base, _PV_CONVIVENCIA):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["convivencia"])
    if contem_termos(base, _PV_PRODUCAO_COLETIVA):
        return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["producao_coletiva"])
    return list(_ACESSIBILIDADE_PROJETO_VIDA_POR_TIPO["autoconhecimento"])


def _acessibilidade_matematica(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["khan", "khanmigo", "bit.ly", "aplicativo", "plataforma", "site", "link", "login", "senha"]):
        return [
            "☑ Organizar atividades paralelas no caderno para estudantes sem acesso ao dispositivo ou com dificuldade de navegação no aplicativo.",
            "☑ Oferecer orientação individual sobre como interpretar os feedbacks do aplicativo e utilizá-los para corrigir estratégias.",
            "☑ Disponibilizar resolução comentada para os estudantes que precisarem de apoio adicional na atividade de revisão.",
        ]

    if any(k in base for k in ["verificacao", "revisao", "relembre", "retomar", "consolidar"]):
        return [
            "☑ Apresentar um exemplo resolvido no quadro antes da atividade individual, destacando cada etapa do raciocínio.",
            "☑ Disponibilizar uma sequência de apoio com dados, operação esperada e espaço para referência/conferência do resultado.",
            "☑ Oferecer mediação individual durante a retomada, permitindo registro por etapas e revisão das respostas antes da correção coletiva.",
        ]

    if any(k in base for k in ["fracao", "fracoes", "decimal", "decimais", "adicao", "adicoes", "subtracao", "subtracoes", "multiplicacao", "multiplicacoes", "divisao", "divisoes", "racionais", "dizima", "dizimas", "operacao", "operacoes", "potencia", "potencias", "raiz", "raizes", "numero", "numeros"]):
        return [
            "☑ Disponibilizar materiais manipuláveis ou representações visuais (como frações circulares, reta numérica ou grades decimais) para apoiar a visualização.",
            "☑ Oferecer resoluções passo a passo com esquemas de cores que diferenciem numeradores de denominadores ou partes inteiras de decimais.",
            "☑ Permitir a conferência intermediária dos cálculos usando tabuada de apoio ou roteiro de procedimentos para reduzir a sobrecarga cognitiva."
        ]

    if any(k in base for k in ["proporcao", "proporcoes", "proporcional", "proporcionais", "razao", "razoes", "regra de tres", "partes desiguais", "partes proporcionais", "grandeza", "grandezas", "inversamente", "diretamente", "escala", "escalas"]):
        return [
            "☑ Fornecer tabelas de proporcionalidade pré-estruturadas onde os estudantes possam organizar as grandezas antes de efetuar os cálculos.",
            "☑ Apresentar setas indicativas coloridas para destacar se a relação entre as grandezas é direta ou inversamente proporcional.",
            "☑ Disponibilizar exemplos resolvidos do uso da regra de três simples, explicitando o passo do produto cruzado e isolamento da incógnita."
        ]

    if any((_base_tem_termo(base, k) if k in {"pa", "pg"} else k in base) for k in ["sequencia", "sequencias", "progressao", "progressoes", "pa", "pg", "regularidade", "regularidades", "generalizacao", "generalizacoes", "padrao numerico"]):
        return [
            "☑ Organizar quadros visuais onde os primeiros termos da sequência estejam em destaque, acompanhados de setas que mostram a regra de acréscimo/multiplicação.",
            "☑ Fornecer tabelas de correspondência (posição do termo versus valor) para facilitar a visualização da regularidade.",
            "☑ Permitir que os estudantes expliquem a regularidade oralmente ou desenhem o próximo termo antes de formalizar a expressão algébrica geral."
        ]

    if any(k in base for k in ["algoritmo", "algoritmos", "fluxograma", "fluxogramas"]):
        return [
            "☑ Disponibilizar fluxogramas coloridos com símbolos de tamanho ampliado e descrições curtas em cada caixa de processo ou decisão.",
            "☑ Oferecer um checklist estruturado contendo a sequência de passos lógicos para resolver o problema de forma linear.",
            "☑ Permitir que estudantes com dificuldade de organização espacial expliquem os passos lógicos oralmente ou por meio de tópicos escritos."
        ]

    if any(k in base for k in ["grafico", "representacao grafica", "plano cartesiano", "eixo", "pares ordenados", "tabela"]):
        return [
            "☑ Ler coletivamente os eixos, legendas e títulos do gráfico ou tabela antes da análise individual.",
            "☑ Disponibilizar versão simplificada ou ampliada dos dados para apoiar a leitura e interpretação.",
            "☑ Organizar questões de leitura guiada para orientar os estudantes na interpretação dos dados e na elaboração das conclusões.",
        ]

    if any(k in base for k in ["resolucao de problemas", "metodo de polya", "polya", "todo mundo escreve"]):
        return [
            "☑ Apresentar resolução comentada de um problema similar para servir como referência orientadora antes da atividade individual.",
            "☑ Organizar a resolução em etapas curtas e visuais: identificação dos dados, escolha da estratégia, cálculo e verificação do resultado.",
            "☑ Permitir o uso de calculadora, tabuada ou material manipulável para estudantes com dificuldade de cálculo, focando na compreensão do método.",
        ]

    if any(k in base for k in ["geogebra", "calculadora cientifica", "geometria dinamica", "acesse o site", "simetria", "rotacao", "translacao", "transformacao", "paralela", "transversal", "congruencia", "quadrilatero", "losango", "trapezio", "paralelogramo"]):
        return [
            "☑ Demonstrar cada etapa do uso da ferramenta ou construção geométrica no projetor antes da exploração individual ou em dupla.",
            "☑ Organizar roteiro com instruções visuais passo a passo para apoiar estudantes com dificuldade de navegação ou visualização das transformações no plano.",
            "☑ Permitir que estudantes com dificuldade participem em dupla ou utilizem modelos geométricos manipuláveis e malhas quadriculadas impressas.",
        ]

    return [
        "☑ Disponibilizar resolução comentada e exemplos graduados para favorecer a compreensão dos procedimentos e das relações matemáticas envolvidas.",
        "☑ Organizar a atividade em etapas curtas com retomadas coletivas, comparando estratégias e destacando dados, operações e representações essenciais.",
        "☑ Oferecer mediação individual durante os registros e cálculos, permitindo diferentes formas de resolução, conferência e explicação das respostas.",
    ]


def _acessibilidade_ciencias(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))
    tipo = detectar_tipo_aula(desenvolvimento, tema, "Ciencias")

    if tipo == "analise_dados":
        return [
            "☑ Ler coletivamente titulo, fonte, legenda, unidades e valores do grafico, tabela, mapa ou infografico antes da analise individual.",
            "☑ Disponibilizar perguntas orientadoras para ajudar a turma a comparar dados, identificar tendencias e relacionar informacoes ao fenomeno estudado.",
            "☑ Permitir registro em topicos, tabela simples, setas ou resposta oral mediada antes da conclusao discursiva completa.",
        ]

    if tipo == "modelagem_cientifica" and _tema_astronomia(base):
        grupo_astronomia = _grupo_modelagem_astronomia(base)
        if grupo_astronomia == "movimentos_terra":
            return [
                "☑ Disponibilizar esquema visual com eixo terrestre, orbita, hemisferios e sentido dos movimentos para apoiar a leitura e a montagem do modelo.",
                "☑ Organizar a atividade em etapas curtas, marcando no modelo o eixo, a direcao da rotacao e a incidencia de luz antes da socializacao.",
                "☑ Permitir registro por desenho identificado, setas, frases curtas ou explicacao oral mediada ao comparar dia e noite, translacao ou estacoes do ano.",
            ]
        if grupo_astronomia == "sistema_sol_terra_lua":
            return [
                "☑ Disponibilizar esquema visual com Sol, Terra, Lua, iluminacao, sombra e posicoes relativas para apoiar a leitura e a montagem do modelo.",
                "☑ Organizar a atividade em etapas curtas, com demonstracao inicial da fonte de luz, dos alinhamentos e da sequencia de fases ou eclipses.",
                "☑ Permitir registro por desenho identificado, legenda, setas ou explicacao oral mediada ao justificar como o modelo representa fases, movimentos ou eclipses.",
            ]
        return [
            "☑ Disponibilizar esquema visual com Sol, Terra, Lua, eixo, orbita ou fases identificados para apoiar a leitura e a montagem do modelo.",
            "☑ Organizar a atividade em etapas curtas, com demonstracao inicial e marcacao das posicoes e movimentos antes da socializacao.",
            "☑ Permitir registro por desenho identificado, legenda, setas ou explicacao oral mediada ao justificar como o modelo representa o fenomeno estudado.",
        ]
    if tipo == "modelagem_cientifica":
        return [
            "☑ Disponibilizar esquema visual com nomes das partes e funcao de cada componente para apoiar a construcao ou leitura do modelo.",
            "☑ Organizar a atividade em etapas curtas, com demonstracao inicial e modelo parcialmente preenchido para consulta durante a montagem.",
            "☑ Permitir registro por desenho identificado, legenda, topicos ou explicacao oral mediada ao apresentar o modelo construido.",
        ]

    if tipo == "situacao_problema":
        return [
            "☑ Dividir o cenario em perguntas menores para identificar problema, causas, impactos, agentes envolvidos e possiveis solucoes.",
            "☑ Disponibilizar quadro comparativo ou roteiro com criterios de analise para orientar a elaboracao das propostas em grupo.",
            "☑ Permitir respostas em topicos, esquema de causa e consequencia, plano simples de acao ou explicacao oral mediada antes do registro final.",
        ]

    if tipo == "pratica_experimental":
        return [
            "☑ Apresentar materiais, etapas e cuidados da pratica em sequencia visual curta, com retomada oral antes do inicio da atividade.",
            "☑ Organizar grupos cooperativos com funcoes definidas para garantir participacao de todos durante observacao, registro e comparacao dos resultados.",
            "☑ Permitir registro por desenho, tabela simples, palavras-chave ou explicacao oral mediada durante a observacao do fenomeno.",
        ]

    if tipo == "investigativa":
        return [
            "☑ Disponibilizar quadro com pergunta inicial, hipoteses e evidencias para apoiar a organizacao do raciocinio cientifico.",
            "☑ Utilizar perguntas orientadoras e retomadas passo a passo para ajudar a turma a observar, registrar e comparar pistas relevantes.",
            "☑ Permitir respostas em frases curtas, topicos, setas ou explicacao oral mediada antes da sintese final escrita.",
        ]

    if tipo == "impacto_socioambiental":
        return [
            "☑ Ler coletivamente dados, noticias, mapas ou infograficos, destacando palavras-chave, fonte e relacoes de causa e consequencia.",
            "☑ Disponibilizar perguntas orientadoras e quadro de impactos, agentes e medidas para apoiar a analise do problema socioambiental.",
            "☑ Permitir registro em topicos, tabela simples, setas ou resposta oral mediada ao justificar propostas de acao e responsabilidade coletiva.",
        ]

    if tipo == "producao_projeto" or any(k in base for k in ["seminario", "cartilha", "campanha", "apresentacao", "produto final"]):
        return [
            "☑ Disponibilizar roteiro simples com criterios da producao: conceito cientifico, exemplo, explicacao e organizacao visual.",
            "☑ Permitir que a apresentacao seja feita com apoio de topicos, cartaz, leitura parcial ou fala compartilhada entre integrantes.",
            "☑ Oferecer tempo para revisao orientada antes da socializacao, retomando vocabulario cientifico essencial.",
        ]

    if tipo == "estudo_caso" or any(k in base for k in ["estudo_caso", "estudo de caso", "caso"]):
        return [
            "☑ Dividir o estudo de caso em perguntas menores: identificar o problema, localizar evidencias, explicar causas e registrar conclusao.",
            "☑ Disponibilizar esquema de causa e consequencia para apoiar a organizacao do raciocinio cientifico.",
            "☑ Permitir respostas em topicos, setas, desenho explicativo ou explicacao oral antes do registro final.",
        ]

    if tipo == "leitura_analise" or any(k in base for k in ["noticia", "reportagem", "inpe", "ibge", "fonte", "hora da leitura"]):
        return [
            "☑ Realizar leitura mediada do texto ou dado, destacando fonte, tema, informacoes centrais e vocabulario cientifico.",
            "☑ Disponibilizar perguntas orientadoras para localizar evidencias e relacionar o texto aos conceitos da aula.",
            "☑ Permitir registro em frases curtas ou topicos antes da resposta discursiva completa.",
        ]

    if tipo == "revisao_retomada" or any(k in base for k in ["relembre", "exercicio resolvido", "retomar"]):
        return [
            f"☑ Retomar coletivamente um esquema, imagem ou registro anterior sobre {tema} antes da atividade individual.",
            "☑ Disponibilizar quadro de palavras-chave e relacoes centrais do fenomeno para consulta durante a retomada.",
            "☑ Organizar pares de apoio para comparar respostas, revisar justificativas e retificar duvidas antes da correcao coletiva.",
        ]
    return [
        "☑ Utilizar imagens, esquemas, tabelas e exemplos do cotidiano para tornar o conceito cientifico mais concreto.",
        "☑ Organizar o registro em etapas curtas: hipotese inicial, conceito estudado, evidencia observada e sintese final.",
        "☑ Permitir diferentes formas de resposta, como topicos, desenho, setas, frases curtas ou explicacao oral mediada.",
    ]


def _acessibilidade_ciencias_reforcada(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    itens = _acessibilidade_ciencias(tema, aprendizagem, desenvolvimento)
    texto = normalizar_texto(" ".join(itens))
    gatilhos_genericos = [
        "tornar o conceito cientifico mais concreto",
        "registro em etapas curtas",
        "diferentes formas de resposta",
    ]
    if all(gatilho in texto for gatilho in gatilhos_genericos):
        return [
            f"☑ Utilizar imagens, esquemas, tabelas e exemplos do material para tornar mais concreto o estudo de {tema}.",
            f"☑ Organizar o registro em etapas curtas ligadas a {tema}, com palavras-chave, evidencias observadas e sintese final para apoiar a compreensao.",
            "☑ Permitir diferentes formas de resposta, como topicos, desenho, setas, frases curtas ou explicacao oral mediada, antes do registro final completo.",
        ]
    return itens


def _acessibilidade_biologia(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    tipo = detectar_tipo_aula(desenvolvimento, tema, "Biologia")

    if tipo == "etico_biotecnologico":
        return [
            "☑ Disponibilizar glossário simplificado com termos científicos de bioética (autonomia, consentimento, dignidade) e vocabulário técnico para apoiar a leitura do estudo de caso.",
            "☑ Oferecer um esquema visual ou fluxograma resumindo a história de Henrietta Lacks ou o dilema ético em foco, facilitando a identificação das pistas.",
            "☑ Permitir formas flexíveis de resposta no Na prática (registro em tópicos, desenhos, setas ou explicação oral mediada pelo professor).",
        ]

    if tipo == "molecular_genetico":
        return [
            "☑ Disponibilizar glossário visual (diagramas com legenda do DNA/RNA/genes) e tabela de equivalência de bases nitrogenadas como consulta durante a aula.",
            "☑ Fornecer gabaritos táteis, modelos físicos ou templates estruturados (quadro de Punnett ou heredograma em branco com linhas guias) para o preenchimento passo a passo.",
            "☑ Permitir registro alternativo para a resolução dos cruzamentos (tópicos descritivos, setas indicativas ou explicação verbal gravada ou mediada).",
        ]

    if tipo == "debate_critico":
        return [
            "☑ Disponibilizar glossário simplificado desmistificando os conceitos de variabilidade e ancestralidade, auxiliando na compreensão de textos e notícias.",
            "☑ Oferecer um roteiro de perguntas orientadoras para direcionar o debate coletivo e a análise das evidências científicas que contrapõem o racismo científico.",
            "☑ Permitir a elaboração do plano de ação em formato de lista, tópicos estruturados, desenho de painel ou gravação de áudio do posicionamento do grupo.",
        ]

    if tipo == "aplicacao_biotecnologica":
        return [
            "☑ Disponibilizar glossário de processos biotecnológicos (vacinas, soros, clonagem) e infográficos das etapas de produção industrial para apoiar a leitura.",
            "☑ Fornecer roteiro passo a passo com lacunas e banco de palavras-chave como apoio para preenchimento do estudo de caso clínico ou do processo biológico.",
            "☑ Permitir respostas simplificadas ou indicação visual de termos-chave para fixação do funcionamento das biotecnologias antes da socialização.",
        ]

    if tipo == "revisao_aprofundamento":
        return [
            "☑ Disponibilizar tabelas comparativas e imagens de síntese das aulas anteriores para consulta imediata durante as atividades de aprofundamento.",
            "☑ Dividir a resolução de problemas complexos de vestibulares em etapas menores e sequenciais, orientando o raciocínio clínico com perguntas guias.",
            "☑ Permitir a realização dos exercícios em duplas de cooperação mútua com registro em tópicos ou explicação falada.",
        ]

    if tipo == "aula_desafio":
        return [
            "☑ Dividir o estudo de caso em perguntas menores: identificar o problema, localizar evidências, formular hipóteses e registrar a conclusão em etapas.",
            "☑ Disponibilizar esquema visual com dados do caso, pistas principais e espaço para comparar hipóteses antes da Hora da verdade.",
            "☑ Permitir respostas em tópicos, setas, desenho explicativo ou fala mediada antes do registro final escrito.",
        ]

    if tipo == "aula_pratica":
        return [
            "☑ Apresentar materiais, procedimentos e objetivos da prática em sequência visual curta, com retomada oral antes do início da atividade.",
            "☑ Permitir registro por desenho, esquema, tabela simples ou explicação oral para estudantes com dificuldade de escrita durante a observação.",
            "☑ Organizar grupos cooperativos com funções definidas para garantir participação de todos na prática e na discussão dos resultados.",
        ]

    if tipo == "revisao_consolidacao":
        return [
            "☑ Disponibilizar glossário, quadro de palavras-chave ou comparação entre conceitos para apoiar a revisão antes das respostas individuais.",
            "☑ Conduzir o quiz ou a retomada com leitura mediada das questões, dando tempo de resposta e retomando os termos centrais no quadro.",
            "☑ Permitir respostas em frases curtas, tópicos ou explicação oral mediada antes da versão discursiva completa.",
        ]

    if tipo == "impacto_socioambiental":
        return [
            "☑ Ler coletivamente os dados, mapas, gráficos ou notícias antes da análise individual, destacando fonte, título, legenda e palavras-chave.",
            "☑ Organizar perguntas orientadoras para ajudar a turma a relacionar o fenômeno biológico a impactos ambientais ou de saúde.",
            "☑ Permitir registro por tópicos, setas, tabela simples ou fala mediada.",
        ]

    return [
        "☑ Utilizar imagens, esquemas, modelos visuais e exemplos do cotidiano para tornar o conceito biológico mais concreto.",
        "☑ Organizar a atividade em etapas curtas, com apoio no quadro para destacar processo, evidências e síntese.",
        "☑ Permitir diferentes formas de resposta, como tópicos, desenho, setas ou explicação oral.",
    ]


def _acessibilidade_ingles(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    tipo = detectar_tipo_aula(desenvolvimento, tema, "Língua Inglesa")
    conteudo = tema

    if tipo in ["leitura_em", "leitura_literaria"]:
        return [
            "☑ Disponibilizar o texto com glossário bilíngue (inglês-português) das palavras mais difíceis, apoiando estudantes com menor repertório lexical.",
            "☑ Oferecer perguntas orientadoras em português para ajudar na localização das informações no texto, reduzindo a sobrecarga cognitiva.",
            "☑ Permitir que estudantes com dificuldade de leitura respondam oralmente em português, com transcrição assistida pelo professor.",
        ]
    if tipo in ["gramatica", "musica"]:
        return [
            f"☑ Disponibilizar tabela de referência com a estrutura gramatical de {conteudo} e exemplos em inglês e português para consulta durante as atividades.",
            "☑ Oferecer banco de palavras e modelos de frases como apoio para estudantes com dificuldade de produção escrita em inglês.",
            "☑ Permitir que estudantes com dificuldade de escrita respondam oralmente ou por meio de esquemas visuais antes do registro escrito.",
        ]
    if tipo == "listening":
        return [
            "☑ Disponibilizar o script do áudio para estudantes surdos ou com dificuldade de compreensão auditiva, garantindo acesso ao conteúdo.",
            "☑ Oferecer o vocabulário temático com tradução e imagens antes da escuta, reduzindo a dificuldade de compreensão.",
            "☑ Permitir que estudantes com dificuldade auditiva realizem a atividade com base no script, participando das mesmas tarefas de compreensão.",
        ]
    if tipo == "producao_oral":
        return [
            "☑ Oferecer modelo de diálogo e banco de palavras/expressões em inglês para apoiar estudantes com menor proficiência oral.",
            "☑ Permitir que estudantes com dificuldade de fala participem da atividade por escrito, produzindo o diálogo no caderno antes de apresentar.",
            "☑ Organizar duplas heterogêneas, pareando estudantes com diferentes níveis de proficiência para apoio mútuo durante a prática oral.",
        ]
    return [
        "☑ Oferecer apoio visual com palavras-chave, imagens e exemplos em inglês e português para facilitar a compreensão do conteúdo.",
        "☑ Permitir diferentes formas de registro (oral, escrito, esquema visual) para estudantes com dificuldades específicas de aprendizagem.",
        "☑ Disponibilizar o vocabulário temático com tradução e pronúncia para consulta durante as atividades, reduzindo a barreira lexical.",
    ]


def _acessibilidade_lingua_portuguesa_em(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    return [
        "☑ Disponibilizar o texto âncora com fonte ampliada e espaçamento maior para estudantes com dificuldade visual ou dislexia.",
        "☑ Permitir que estudantes com dificuldade de escrita respondam oralmente ou em dupla com apoio de colega.",
        "☑ Oferecer roteiro estruturado com perguntas-guia para estudantes com dificuldade de organização do pensamento ou produção textual.",
    ]

def _acessibilidade_historia(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if "tabela" in base or "quadro" in base:
        return [
            "Preencher coletivamente uma linha do quadro ou da tabela antes da atividade autonoma, destacando o que deve ser observado em cada coluna.",
            "Oferecer perguntas-guia para relacionar sujeitos, contexto, causas e consequencias historicas ao organizar os registros.",
            "Permitir consulta ao material, ao quadro e a exemplos comentados durante a producao das respostas.",
        ]

    if any(k in base for k in ["fonte", "documento", "carta", "imagem", "pintura", "charge", "memorial", "monumento"]):
        return [
            "Oferecer roteiro de observacao da fonte historica com perguntas simples sobre autoria, contexto e elementos principais.",
            "Destacar no quadro palavras-chave e relacoes temporais para apoiar a leitura e a interpretacao do material.",
            "Permitir respostas por topicos, frases curtas ou explicacao oral mediada antes do registro final.",
        ]

    return [
        "Utilizar fontes, imagens, mapas ou linhas do tempo com retomadas coletivas para favorecer a compreensao do contexto historico.",
        "Oferecer perguntas orientadoras e palavras-chave para apoiar a leitura, a interpretacao e a organizacao das ideias.",
        "Permitir registros por topicos, esquemas ou frases curtas, com mediacao individual quando necessario.",
    ]


GeradorAcessibilidade = Callable[[str, str, str], list[str]]

GERADORES_ACESSIBILIDADE_POR_PERFIL: dict[str, GeradorAcessibilidade] = {
    "ingles": _acessibilidade_ingles,
    "lingua_portuguesa_ef": _acessibilidade_lingua_portuguesa,
    "lingua_portuguesa_em": _acessibilidade_lingua_portuguesa_em,
    "leitura_redacao": _acessibilidade_lingua_portuguesa,
    "historia": _acessibilidade_historia,
    "matematica": _acessibilidade_matematica,
    "ciencias_ef": _acessibilidade_ciencias_reforcada,
    "biologia": _acessibilidade_biologia,
    "projeto_de_vida": _acessibilidade_projeto_vida,
}


def gerar_acessibilidade_por_perfil(
    perfil: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
) -> list[str]:
    gerador = GERADORES_ACESSIBILIDADE_POR_PERFIL.get(perfil)
    if not gerador:
        return []
    return gerador(tema, aprendizagem, desenvolvimento)

