"""Regras especÃ­ficas de acessibilidade por disciplina e por aula."""

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


def _tem_marcador_visao(base: str) -> bool:
    return bool(
        re.search(
            r"\b(?:olho|retina|cornea|pupila|cristalino|sistema visual|formacao da imagem|caminho da luz|visao)\b",
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
            "Ampliar o esquema anatÃ´mico e nomear oralmente cada estrutura antes da atividade individual.",
            "Disponibilizar banco de palavras com os nomes das estruturas para apoiar a legenda.",
            "Permitir apoio em dupla para leitura guiada e conferÃªncia das identificaÃ§Ãµes.",
        ]
    if "texto sintese" in base or "texto-sintese" in base or "sintese individual" in base:
        return [
            "Oferecer roteiro com perguntas-chave para organizar a escrita do texto-sÃ­ntese.",
            "Destacar palavras-chave no quadro e permitir produÃ§Ã£o inicial em tÃ³picos antes do texto final.",
            "Realizar mediaÃ§Ã£o individual para revisÃ£o de clareza, sequÃªncia de ideias e vocabulÃ¡rio cientÃ­fico.",
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
            "Preencher uma linha da tabela como exemplo antes do trabalho autÃ´nomo.",
            "Organizar pares produtivos para apoiar leitura dos comandos e preenchimento dos campos.",
            "Permitir consulta constante ao material digital e ao quadro durante a atividade.",
        ]
    return []


def _acessibilidade_lingua_portuguesa(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["trilha", "alice no pais das maravilhas", "pequeno principe", "peter pan", "leitura compartilhada", "predicao guiada"]):
        return [
            "Realizar leitura mediada com pausas para explicaÃ§Ã£o de palavras e acontecimentos importantes da narrativa.",
            "Permitir respostas orais, desenhos, tÃ³picos ou pequenos registros escritos como forma de participaÃ§Ã£o.",
            "Disponibilizar perguntas orientadoras para auxiliar na compreensÃ£o e organizaÃ§Ã£o das ideias.",
        ]

    if any(k in base for k in ["versao final", "redacao paulista", "revisao orientada", "revis", "reescrita", "rascunho", "producao textual", "producao de textos"]):
        return [
            "Disponibilizar checklist simplificado para orientar a revisÃ£o do texto.",
            "Permitir apoio individual durante a leitura, revisÃ£o e escrita da versÃ£o final.",
            "Oferecer modelos de organizaÃ§Ã£o textual e exemplos de conectivos para auxiliar a produÃ§Ã£o escrita.",
        ]

    if "verbo haver" in base or re.search(r"\bhaver\b", base):
        return [
            "Oferecer exemplos prÃ¡ticos antes das atividades autÃ´nomas.",
            "Disponibilizar esquemas simples com regras e exemplos do verbo haver.",
            "Permitir apoio em dupla durante leitura e resoluÃ§Ã£o das questÃµes.",
        ]

    if "tirinha" in base and any(k in base for k in ["humor", "critica", "conflito", "linguagem mista"]):
        return [
            "Disponibilizar perguntas orientadoras para auxiliar na interpretaÃ§Ã£o das tirinhas.",
            "Permitir respostas orais, desenhos ou registros em tÃ³picos curtos.",
            "Realizar leitura mediada das imagens e falas para apoiar a compreensÃ£o.",
        ]

    if any(k in base for k in ["figura de linguagem", "figuras de linguagem", "imperativo"]) and any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario"]):
        return [
            "Ampliar imagens e destacar visualmente informaÃ§Ãµes importantes dos anÃºncios.",
            "Permitir leitura em dupla ou apoio do professor durante as atividades.",
            "Disponibilizar exemplos resolvidos antes das propostas individuais.",
        ]

    if any(k in base for k in ["metafora", "metaforas"]) and any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario"]):
        return [
            "Disponibilizar palavras-chave e exemplos simples de metÃ¡foras.",
            "Permitir explicaÃ§Ãµes orais mediadas durante as atividades.",
            "Realizar leitura guiada dos anÃºncios, destacando elementos importantes.",
        ]

    if any(k in base for k in ["publicidade", "anuncio", "anuncios", "publicitario", "propaganda", "slogan"]):
        return [
            "Disponibilizar perguntas curtas e objetivas para orientar a anÃ¡lise dos anÃºncios.",
            "Permitir registros por tÃ³picos, desenhos ou respostas orais.",
            "Retomar coletivamente conceitos importantes antes das atividades.",
        ]

    if any(k in base for k in ["carta de reclamacao", "reclamar por escrito", "texto reivindicatorio", "reivindicatorios"]):
        return [
            "Realizar leitura mediada da carta de reclamaÃ§Ã£o, destacando finalidade, estrutura e argumentos.",
            "Disponibilizar roteiro com perguntas curtas para orientar a anÃ¡lise do texto.",
            "Permitir respostas orais, registros em tÃ³picos ou produÃ§Ã£o em dupla conforme a necessidade.",
        ]

    if any(k in base for k in ["conjuncao", "conjuncoes", "locucao conjuntiva", "locucoes conjuntivas"]):
        return [
            "Disponibilizar quadro com exemplos de conjunÃ§Ãµes e relaÃ§Ãµes de sentido.",
            "Oferecer exemplos comentados antes das atividades autÃ´nomas.",
            "Permitir apoio em dupla durante leitura, identificaÃ§Ã£o e resoluÃ§Ã£o das questÃµes.",
        ]

    if any(k in base for k in ["texto multissemiotico", "linguagem verbal", "linguagem nao verbal"]):
        return [
            "Realizar leitura guiada das imagens, falas e demais elementos visuais do texto.",
            "Disponibilizar perguntas orientadoras para apoiar a relaÃ§Ã£o entre linguagem verbal e nÃ£o verbal.",
            "Permitir registros por tÃ³picos, desenhos, setas ou respostas orais mediadas.",
        ]

    if any(k in base for k in ["leitura_literaria", "cronica", "conto", "poema", "poesia", "narrativa",
                               "eu lirico", "narrador", "enredo", "personagem", "fruicao", "literatura"]):
        return [
            "Realizar leitura mediada do texto literÃ¡rio com pausas para explicaÃ§Ã£o de palavras, expressÃµes e acontecimentos.",
            "Disponibilizar perguntas orientadoras que auxiliem na identificaÃ§Ã£o de personagens, conflito e tema.",
            "Permitir respostas orais, desenhos, mapas mentais ou registros em tÃ³picos como forma de participaÃ§Ã£o.",
        ]

    if any(k in base for k in ["gramatica_contextualizada", "modo subjuntivo", "modo indicativo",
                               "tempos verbais", "coesao", "coesivos", "pronomes", "regencia",
                               "modalizacao", "polissemia", "intertextualidade"]):
        return [
            "Disponibilizar esquemas visuais com exemplos da norma ou fenÃ´meno gramatical estudado.",
            "Oferecer trechos comentados antes das atividades autÃ´nomas para facilitar a identificaÃ§Ã£o do conteÃºdo.",
            "Permitir apoio em dupla ou resoluÃ§Ã£o parcial com mediaÃ§Ã£o do professor.",
        ]

    if any(k in base for k in ["leitura_jornalistica", "noticia", "editorial", "reportagem",
                               "manchete", "lide", "jornalismo", "midia", "imparcialidade"]):
        return [
            "Disponibilizar glossÃ¡rio com termos do universo jornalÃ­stico utilizados no texto.",
            "Realizar leitura mediada do texto com Ãªnfase em lide, manchete e intenÃ§Ã£o comunicativa.",
            "Permitir respostas em tÃ³picos curtos ou orais com apoio de perguntas orientadoras.",
        ]

    if any(k in base for k in ["producao_textual", "producao", "resenha", "carta do leitor",
                               "estrutura do genero", "publico-alvo", "suporte", "redija"]):
        return [
            "Disponibilizar modelo de planejamento textual com etapas simples e exemplos de estrutura.",
            "Oferecer lista de verificaÃ§Ã£o para que os estudantes confiram adequaÃ§Ã£o ao gÃªnero antes da versÃ£o final.",
            "Permitir apoio individual na escrita e na revisÃ£o, incluindo ditado para o professor quando necessÃ¡rio.",
        ]

    if any(k in base for k in ["pesquisa", "scielo", "curadoria", "plagio", "fontes confiaveis",
                               "divulgacao cientifica", "direitos autorais", "google academico"]):
        return [
            "Disponibilizar lista de sites e fontes confiÃ¡veis previamente selecionadas pelo professor.",
            "Orientar a pesquisa com roteiro de etapas simples: busca, seleÃ§Ã£o, leitura e registro.",
            "Permitir que os estudantes trabalhem em dupla durante a navegaÃ§Ã£o e a sÃ­ntese das informaÃ§Ãµes.",
        ]

    return [
        "Disponibilizar perguntas orientadoras para apoiar a leitura, a interpretaÃ§Ã£o e a organizaÃ§Ã£o das respostas.",
        "Permitir registros por tÃ³picos, frases curtas, desenho, esquema ou resposta oral mediada.",
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
            "Organizar atividades paralelas no caderno para estudantes sem acesso ao dispositivo ou com dificuldade de navegaÃ§Ã£o no aplicativo.",
            "Oferecer orientaÃ§Ã£o individual sobre como interpretar os feedbacks do aplicativo e utilizÃ¡-los para corrigir estratÃ©gias.",
            "Disponibilizar resoluÃ§Ã£o comentada para os estudantes que precisarem de apoio adicional na atividade de revisÃ£o.",
        ]

    if any(k in base for k in ["verificacao", "revisao", "relembre", "retomar", "consolidar"]):
        return [
            "Apresentar um exemplo resolvido no quadro antes da atividade individual, destacando cada etapa do raciocÃ­nio.",
            "Disponibilizar uma sequÃªncia de apoio com dados, operaÃ§Ã£o esperada e espaÃ§o para conferÃªncia do resultado.",
            "Oferecer mediaÃ§Ã£o individual durante a retomada, permitindo registro por etapas e revisÃ£o das respostas antes da correÃ§Ã£o coletiva.",
        ]

    if any(k in base for k in ["grafico", "representacao grafica", "plano cartesiano", "eixo", "pares ordenados", "tabela"]):
        return [
            "Ler coletivamente os eixos, legendas e tÃ­tulos do grÃ¡fico ou tabela antes da anÃ¡lise individual.",
            "Disponibilizar versÃ£o simplificada ou ampliada dos dados para apoiar a leitura e interpretaÃ§Ã£o.",
            "Organizar questÃµes de leitura guiada para orientar os estudantes na interpretaÃ§Ã£o dos dados e na elaboraÃ§Ã£o das conclusÃµes.",
        ]

    if any(k in base for k in ["resolucao de problemas", "metodo de polya", "polya", "todo mundo escreve"]):
        return [
            "Apresentar resolucao comentada de um problema similar para servir como referÃªncia orientadora antes da atividade individual.",
            "Organizar a resoluÃ§Ã£o em etapas curtas e visuais: identificaÃ§Ã£o dos dados, escolha da estratÃ©gia, cÃ¡lculo e verificaÃ§Ã£o do resultado.",
            "Permitir o uso de calculadora, tabuada ou material manipulÃ¡vel para estudantes com dificuldade de cÃ¡lculo, focando na compreensÃ£o do mÃ©todo.",
        ]

    if any(k in base for k in ["geogebra", "calculadora cientifica", "geometria dinamica", "acesse o site"]):
        return [
            "Demonstrar cada etapa do uso da ferramenta no projetor antes da exploraÃ§Ã£o individual ou em dupla.",
            "Organizar roteiro com instruÃ§Ãµes visuais passo a passo para apoiar estudantes com dificuldade de navegaÃ§Ã£o na ferramenta.",
            "Permitir que estudantes com dificuldade de acesso ao equipamento participem em dupla ou utilizem recursos impressos equivalentes.",
        ]

    return [
        "Disponibilizar resoluÃ§Ã£o comentada e exemplos graduados para favorecer a compreensÃ£o dos procedimentos e das relaÃ§Ãµes matemÃ¡ticas envolvidas.",
        "Organizar a atividade em etapas curtas com retomadas coletivas, comparando estratÃ©gias e destacando dados, operaÃ§Ãµes e representaÃ§Ãµes essenciais.",
        "Oferecer mediaÃ§Ã£o individual durante os registros e cÃ¡lculos, permitindo diferentes formas de resoluÃ§Ã£o, conferÃªncia e explicaÃ§Ã£o das respostas.",
    ]


def _acessibilidade_ciencias(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))
    tipo = detectar_tipo_aula(desenvolvimento, tema, "Ciencias")

    if tipo == "analise_dados":
        return [
            "â˜‘ Ler coletivamente titulo, fonte, legenda, unidades e valores do grafico, tabela, mapa ou infografico antes da analise individual.",
            "â˜‘ Disponibilizar perguntas orientadoras para ajudar a turma a comparar dados, identificar tendencias e relacionar informacoes ao fenomeno estudado.",
            "â˜‘ Permitir registro em topicos, tabela simples, setas ou resposta oral mediada antes da conclusao discursiva completa.",
        ]

    if tipo == "modelagem_cientifica" and _tema_astronomia(base):
        grupo_astronomia = _grupo_modelagem_astronomia(base)
        if grupo_astronomia == "movimentos_terra":
            return [
                "â˜‘ Disponibilizar esquema visual com eixo terrestre, orbita, hemisferios e sentido dos movimentos para apoiar a leitura e a montagem do modelo.",
                "â˜‘ Organizar a atividade em etapas curtas, marcando no modelo o eixo, a direcao da rotacao e a incidencia de luz antes da socializacao.",
                "â˜‘ Permitir registro por desenho identificado, setas, frases curtas ou explicacao oral mediada ao comparar dia e noite, translacao ou estacoes do ano.",
            ]
        if grupo_astronomia == "sistema_sol_terra_lua":
            return [
                "â˜‘ Disponibilizar esquema visual com Sol, Terra, Lua, iluminacao, sombra e posicoes relativas para apoiar a leitura e a montagem do modelo.",
                "â˜‘ Organizar a atividade em etapas curtas, com demonstracao inicial da fonte de luz, dos alinhamentos e da sequencia de fases ou eclipses.",
                "â˜‘ Permitir registro por desenho identificado, legenda, setas ou explicacao oral mediada ao justificar como o modelo representa fases, movimentos ou eclipses.",
            ]
        return [
            "â˜‘ Disponibilizar esquema visual com Sol, Terra, Lua, eixo, orbita ou fases identificados para apoiar a leitura e a montagem do modelo.",
            "â˜‘ Organizar a atividade em etapas curtas, com demonstracao inicial e marcacao das posicoes e movimentos antes da socializacao.",
            "â˜‘ Permitir registro por desenho identificado, legenda, setas ou explicacao oral mediada ao justificar como o modelo representa o fenomeno estudado.",
        ]
    if tipo == "modelagem_cientifica":
        return [
            "â˜‘ Disponibilizar esquema visual com nomes das partes e funcao de cada componente para apoiar a construcao ou leitura do modelo.",
            "â˜‘ Organizar a atividade em etapas curtas, com demonstracao inicial e modelo parcialmente preenchido para consulta durante a montagem.",
            "â˜‘ Permitir registro por desenho identificado, legenda, topicos ou explicacao oral mediada ao apresentar o modelo construido.",
        ]

    if tipo == "situacao_problema":
        return [
            "â˜‘ Dividir o cenario em perguntas menores para identificar problema, causas, impactos, agentes envolvidos e possiveis solucoes.",
            "â˜‘ Disponibilizar quadro comparativo ou roteiro com criterios de analise para orientar a elaboracao das propostas em grupo.",
            "â˜‘ Permitir respostas em topicos, esquema de causa e consequencia, plano simples de acao ou explicacao oral mediada antes do registro final.",
        ]

    if tipo == "pratica_experimental":
        return [
            "â˜‘ Apresentar materiais, etapas e cuidados da pratica em sequencia visual curta, com retomada oral antes do inicio da atividade.",
            "â˜‘ Organizar grupos cooperativos com funcoes definidas para garantir participacao de todos durante observacao, registro e comparacao dos resultados.",
            "â˜‘ Permitir registro por desenho, tabela simples, palavras-chave ou explicacao oral mediada durante a observacao do fenomeno.",
        ]

    if tipo == "investigativa":
        return [
            "â˜‘ Disponibilizar quadro com pergunta inicial, hipoteses e evidencias para apoiar a organizacao do raciocinio cientifico.",
            "â˜‘ Utilizar perguntas orientadoras e retomadas passo a passo para ajudar a turma a observar, registrar e comparar pistas relevantes.",
            "â˜‘ Permitir respostas em frases curtas, topicos, setas ou explicacao oral mediada antes da sintese final escrita.",
        ]

    if tipo == "impacto_socioambiental":
        return [
            "â˜‘ Ler coletivamente dados, noticias, mapas ou infograficos, destacando palavras-chave, fonte e relacoes de causa e consequencia.",
            "â˜‘ Disponibilizar perguntas orientadoras e quadro de impactos, agentes e medidas para apoiar a analise do problema socioambiental.",
            "â˜‘ Permitir registro em topicos, tabela simples, setas ou resposta oral mediada ao justificar propostas de acao e responsabilidade coletiva.",
        ]

    if tipo == "producao_projeto" or any(k in base for k in ["seminario", "cartilha", "campanha", "apresentacao", "produto final"]):
        return [
            "â˜‘ Disponibilizar roteiro simples com criterios da producao: conceito cientifico, exemplo, explicacao e organizacao visual.",
            "â˜‘ Permitir que a apresentacao seja feita com apoio de topicos, cartaz, leitura parcial ou fala compartilhada entre integrantes.",
            "â˜‘ Oferecer tempo para revisao orientada antes da socializacao, retomando vocabulario cientifico essencial.",
        ]

    if tipo == "estudo_caso" or any(k in base for k in ["estudo_caso", "estudo de caso", "caso"]):
        return [
            "â˜‘ Dividir o estudo de caso em perguntas menores: identificar o problema, localizar evidencias, explicar causas e registrar conclusao.",
            "â˜‘ Disponibilizar esquema de causa e consequencia para apoiar a organizacao do raciocinio cientifico.",
            "â˜‘ Permitir respostas em topicos, setas, desenho explicativo ou explicacao oral antes do registro final.",
        ]

    if tipo == "leitura_analise" or any(k in base for k in ["noticia", "reportagem", "inpe", "ibge", "fonte", "hora da leitura"]):
        return [
            "â˜‘ Realizar leitura mediada do texto ou dado, destacando fonte, tema, informacoes centrais e vocabulario cientifico.",
            "â˜‘ Disponibilizar perguntas orientadoras para localizar evidencias e relacionar o texto aos conceitos da aula.",
            "â˜‘ Permitir registro em frases curtas ou topicos antes da resposta discursiva completa.",
        ]

    if tipo == "revisao_retomada" or any(k in base for k in ["relembre", "exercicio resolvido", "retomar"]):
        return [
            f"â˜‘ Retomar coletivamente um esquema, imagem ou registro anterior sobre {tema} antes da atividade individual.",
            "â˜‘ Disponibilizar quadro de palavras-chave e relacoes centrais do fenomeno para consulta durante a retomada.",
            "â˜‘ Organizar pares de apoio para comparar respostas, revisar justificativas e retificar duvidas antes da correcao coletiva.",
        ]
    return [
        "â˜‘ Utilizar imagens, esquemas, tabelas e exemplos do cotidiano para tornar o conceito cientifico mais concreto.",
        "â˜‘ Organizar o registro em etapas curtas: hipotese inicial, conceito estudado, evidencia observada e sintese final.",
        "â˜‘ Permitir diferentes formas de resposta, como topicos, desenho, setas, frases curtas ou explicacao oral mediada.",
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
            f"â˜‘ Utilizar imagens, esquemas, tabelas e exemplos do material para tornar mais concreto o estudo de {tema}.",
            f"â˜‘ Organizar o registro em etapas curtas ligadas a {tema}, com palavras-chave, evidencias observadas e sintese final para apoiar a compreensao.",
            "â˜‘ Permitir diferentes formas de resposta, como topicos, desenho, setas, frases curtas ou explicacao oral mediada, antes do registro final completo.",
        ]
    return itens


def _acessibilidade_biologia(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    tipo = detectar_tipo_aula(desenvolvimento, tema, "Biologia")

    if tipo == "etico_biotecnologico":
        return [
            "â˜‘ Disponibilizar glossÃ¡rio simplificado com termos cientÃ­ficos de bioÃ©tica (autonomia, consentimento, dignidade) e vocabulÃ¡rio tÃ©cnico para apoiar a leitura do estudo de caso.",
            "â˜‘ Oferecer um esquema visual ou fluxograma resumindo a histÃ³ria de Henrietta Lacks ou o dilema Ã©tico em foco, facilitando a identificaÃ§Ã£o das pistas.",
            "â˜‘ Permitir formas flexÃ­veis de resposta no Na prÃ¡tica (registro em tÃ³picos, desenhos, setas ou explicaÃ§Ã£o oral mediada pelo professor).",
        ]

    if tipo == "molecular_genetico":
        return [
            "â˜‘ Disponibilizar glossÃ¡rio visual (diagramas com legenda do DNA/RNA/genes) e tabela de equivalÃªncia de bases nitrogenadas como consulta durante a aula.",
            "â˜‘ Fornecer gabaritos tÃ¡teis, modelos fÃ­sicos ou templates estruturados (quadro de Punnett ou heredograma em branco com linhas guias) para o preenchimento passo a passo.",
            "â˜‘ Permitir registro alternativo para a resoluÃ§Ã£o dos cruzamentos (tÃ³picos descritivos, setas indicativas ou explicaÃ§Ã£o verbal gravada ou mediada).",
        ]

    if tipo == "debate_critico":
        return [
            "â˜‘ Disponibilizar glossÃ¡rio simplificado desmistificando os conceitos de variabilidade e ancestralidade, auxiliando na compreensÃ£o de textos e notÃ­cias.",
            "â˜‘ Oferecer um roteiro de perguntas orientadoras para direcionar o debate coletivo e a anÃ¡lise das evidÃªncias cientÃ­ficas que contrapÃµem o racismo cientÃ­fico.",
            "â˜‘ Permitir a elaboraÃ§Ã£o do plano de aÃ§Ã£o em formato de lista, tÃ³picos estruturados, desenho de painel ou gravaÃ§Ã£o de Ã¡udio do posicionamento do grupo.",
        ]

    if tipo == "aplicacao_biotecnologica":
        return [
            "â˜‘ Disponibilizar glossÃ¡rio de processos biotecnolÃ³gicos (vacinas, soros, clonagem) e infogrÃ¡ficos das etapas de produÃ§Ã£o industrial para apoiar a leitura.",
            "â˜‘ Fornecer roteiro passo a passo com lacunas e banco de palavras-chave como apoio para preenchimento do estudo de caso clÃ­nico ou do processo biolÃ³gico.",
            "â˜‘ Permitir respostas simplificadas ou indicaÃ§Ã£o visual de termos-chave para fixaÃ§Ã£o do funcionamento das biotecnologias antes da socializaÃ§Ã£o.",
        ]

    if tipo == "revisao_aprofundamento":
        return [
            "â˜‘ Disponibilizar tabelas comparativas e imagens de sÃ­ntese das aulas anteriores para consulta imediata durante as atividades de aprofundamento.",
            "â˜‘ Dividir a resoluÃ§Ã£o de problemas complexos de vestibulares em etapas menores e sequenciais, orientando o raciocÃ­nio clÃ­nico com perguntas guias.",
            "â˜‘ Permitir a realizaÃ§Ã£o dos exercÃ­cios em duplas de cooperaÃ§Ã£o mÃºtua com registro em tÃ³picos ou explicaÃ§Ã£o falada.",
        ]

    if tipo == "aula_desafio":
        return [
            "â˜‘ Dividir o estudo de caso em perguntas menores: identificar o problema, localizar evidÃªncias, formular hipÃ³teses e registrar a conclusÃ£o em etapas.",
            "â˜‘ Disponibilizar esquema visual com dados do caso, pistas principais e espaÃ§o para comparar hipÃ³teses antes da Hora da verdade.",
            "â˜‘ Permitir respostas em tÃ³picos, setas, desenho explicativo ou fala mediada antes do registro final escrito.",
        ]

    if tipo == "aula_pratica":
        return [
            "â˜‘ Apresentar materiais, procedimentos e objetivos da prÃ¡tica em sequÃªncia visual curta, com retomada oral antes do inÃ­cio da atividade.",
            "â˜‘ Permitir registro por desenho, esquema, tabela simples ou explicaÃ§Ã£o oral para estudantes com dificuldade de escrita durante a observaÃ§Ã£o.",
            "â˜‘ Organizar grupos cooperativos com funÃ§Ãµes definidas para garantir participaÃ§Ã£o de todos na prÃ¡tica e na discussÃ£o dos resultados.",
        ]

    if tipo == "revisao_consolidacao":
        return [
            "â˜‘ Disponibilizar glossÃ¡rio, quadro de palavras-chave ou comparaÃ§Ã£o entre conceitos para apoiar a revisÃ£o antes das respostas individuais.",
            "â˜‘ Conduzir o quiz ou a retomada com leitura mediada das questÃµes, dando tempo de resposta e retomando os termos centrais no quadro.",
            "â˜‘ Permitir respostas em frases curtas, tÃ³picos ou explicaÃ§Ã£o oral mediada antes da versÃ£o discursiva completa.",
        ]

    if tipo == "impacto_socioambiental":
        return [
            "â˜‘ Ler coletivamente os dados, mapas, grÃ¡ficos ou notÃ­cias antes da anÃ¡lise individual, destacando fonte, tÃ­tulo, legenda e palavras-chave.",
            "â˜‘ Organizar perguntas orientadoras para ajudar a turma a relacionar o fenÃ´meno biolÃ³gico a impactos ambientais ou de saÃºde.",
            "â˜‘ Permitir registro por tÃ³picos, setas, tabela simples ou fala mediada.",
        ]

    return [
        "â˜‘ Utilizar imagens, esquemas, modelos visuais e exemplos do cotidiano para tornar o conceito biolÃ³gico mais concreto.",
        "â˜‘ Organizar a atividade em etapas curtas, com apoio no quadro para destacar processo, evidÃªncias e sÃ­ntese.",
        "â˜‘ Permitir diferentes formas de resposta, como tÃ³picos, desenho, setas ou explicaÃ§Ã£o oral.",
    ]


def _acessibilidade_ingles(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    tipo = detectar_tipo_aula(desenvolvimento, tema, "LÃ­ngua Inglesa")
    conteudo = tema

    if tipo in ["leitura_em", "leitura_literaria"]:
        return [
            "â˜‘ Disponibilizar o texto com glossÃ¡rio bilÃ­ngue (inglÃªs-portuguÃªs) das palavras mais difÃ­ceis, apoiando estudantes com menor repertÃ³rio lexical.",
            "â˜‘ Oferecer perguntas orientadoras em portuguÃªs para ajudar na localizaÃ§Ã£o das informaÃ§Ãµes no texto, reduzindo a sobrecarga cognitiva.",
            "â˜‘ Permitir que estudantes com dificuldade de leitura respondam oralmente em portuguÃªs, com transcriÃ§Ã£o assistida pelo professor.",
        ]
    if tipo in ["gramatica", "musica"]:
        return [
            f"â˜‘ Disponibilizar tabela de referÃªncia com a estrutura gramatical de {conteudo} e exemplos em inglÃªs e portuguÃªs para consulta durante as atividades.",
            "â˜‘ Oferecer banco de palavras e modelos de frases como apoio para estudantes com dificuldade de produÃ§Ã£o escrita em inglÃªs.",
            "â˜‘ Permitir que estudantes com dificuldade de escrita respondam oralmente ou por meio de esquemas visuais antes do registro escrito.",
        ]
    if tipo == "listening":
        return [
            "â˜‘ Disponibilizar o script do Ã¡udio para estudantes surdos ou com dificuldade de compreensÃ£o auditiva, garantindo acesso ao conteÃºdo.",
            "â˜‘ Oferecer o vocabulÃ¡rio temÃ¡tico com traduÃ§Ã£o e imagens antes da escuta, reduzindo a dificuldade de compreensÃ£o.",
            "â˜‘ Permitir que estudantes com dificuldade auditiva realizem a atividade com base no script, participando das mesmas tarefas de compreensÃ£o.",
        ]
    if tipo == "producao_oral":
        return [
            "â˜‘ Oferecer modelo de diÃ¡logo e banco de palavras/expressÃµes em inglÃªs para apoiar estudantes com menor proficiÃªncia oral.",
            "â˜‘ Permitir que estudantes com dificuldade de fala participem da atividade por escrito, produzindo o diÃ¡logo no caderno antes de apresentar.",
            "â˜‘ Organizar duplas heterogÃªneas, pareando estudantes com diferentes nÃ­veis de proficiÃªncia para apoio mÃºtuo durante a prÃ¡tica oral.",
        ]
    return [
        "â˜‘ Oferecer apoio visual com palavras-chave, imagens e exemplos em inglÃªs e portuguÃªs para facilitar a compreensÃ£o do conteÃºdo.",
        "â˜‘ Permitir diferentes formas de registro (oral, escrito, esquema visual) para estudantes com dificuldades especÃ­ficas de aprendizagem.",
        "â˜‘ Disponibilizar o vocabulÃ¡rio temÃ¡tico com traduÃ§Ã£o e pronÃºncia para consulta durante as atividades, reduzindo a barreira lexical.",
    ]


def _acessibilidade_lingua_portuguesa_em(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    return [
        "â˜‘ Disponibilizar o texto Ã¢ncora com fonte ampliada e espaÃ§amento maior para estudantes com dificuldade visual ou dislexia.",
        "â˜‘ Permitir que estudantes com dificuldade de escrita respondam oralmente ou em dupla com apoio de colega.",
        "â˜‘ Oferecer roteiro estruturado com perguntas-guia para estudantes com dificuldade de organizaÃ§Ã£o do pensamento ou produÃ§Ã£o textual.",
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

