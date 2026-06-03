"""Regras específicas de acessibilidade por disciplina e por aula."""

import re
from typing import Callable

from core.lib.classificador import contem_termos, normalizar_texto


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
    return bool(
        re.search(
            r"\b(?:olho|retina|cornea|pupila|cristalino|sistema visual|formacao da imagem|caminho da luz|visao)\b",
            base,
            flags=re.I,
        )
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
            "Organizar atividades paralelas no caderno para estudantes sem acesso ao dispositivo ou com dificuldade de navegação no aplicativo.",
            "Oferecer orientação individual sobre como interpretar os feedbacks do aplicativo e utilizá-los para corrigir estratégias.",
            "Disponibilizar resolução comentada para os estudantes que precisarem de apoio adicional na atividade de revisão.",
        ]

    if any(k in base for k in ["verificacao", "revisao", "relembre", "retomar", "consolidar"]):
        return [
            "Apresentar um exemplo resolvido no quadro antes da atividade individual, destacando cada etapa do raciocínio.",
            "Disponibilizar uma sequência de apoio com dados, operação esperada e espaço para conferência do resultado.",
            "Oferecer mediação individual durante a retomada, permitindo registro por etapas e revisão das respostas antes da correção coletiva.",
        ]

    if any(k in base for k in ["grafico", "representacao grafica", "plano cartesiano", "eixo", "pares ordenados", "tabela"]):
        return [
            "Ler coletivamente os eixos, legendas e títulos do gráfico ou tabela antes da análise individual.",
            "Disponibilizar versão simplificada ou ampliada dos dados para apoiar a leitura e interpretação.",
            "Organizar questões de leitura guiada para orientar os estudantes na interpretação dos dados e na elaboração das conclusões.",
        ]

    if any(k in base for k in ["resolucao de problemas", "metodo de polya", "polya", "todo mundo escreve"]):
        return [
            "Apresentar resolucao comentada de um problema similar para servir como referência orientadora antes da atividade individual.",
            "Organizar a resolução em etapas curtas e visuais: identificação dos dados, escolha da estratégia, cálculo e verificação do resultado.",
            "Permitir o uso de calculadora, tabuada ou material manipulável para estudantes com dificuldade de cálculo, focando na compreensão do método.",
        ]

    if any(k in base for k in ["geogebra", "calculadora cientifica", "geometria dinamica", "acesse o site"]):
        return [
            "Demonstrar cada etapa do uso da ferramenta no projetor antes da exploração individual ou em dupla.",
            "Organizar roteiro com instruções visuais passo a passo para apoiar estudantes com dificuldade de navegação na ferramenta.",
            "Permitir que estudantes com dificuldade de acesso ao equipamento participem em dupla ou utilizem recursos impressos equivalentes.",
        ]

    return [
        "Disponibilizar resolução comentada e exemplos graduados para favorecer a compreensão dos procedimentos e das relações matemáticas envolvidas.",
        "Organizar a atividade em etapas curtas com retomadas coletivas, comparando estratégias e destacando dados, operações e representações essenciais.",
        "Oferecer mediação individual durante os registros e cálculos, permitindo diferentes formas de resolução, conferência e explicação das respostas.",
    ]


def _acessibilidade_ciencias(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    base = normalizar_texto(" ".join([tema, aprendizagem, desenvolvimento]))

    if any(k in base for k in ["producao_projeto", "seminario", "cartilha", "campanha", "apresentacao", "produto final"]):
        return [
            "Disponibilizar roteiro simples com criterios da producao: conceito cientifico, exemplo, explicacao e organizacao visual.",
            "Permitir que a apresentacao seja feita com apoio de topicos, cartaz, leitura parcial ou fala compartilhada entre integrantes.",
            "Oferecer tempo para revisao orientada antes da socializacao, retomando vocabulario cientifico essencial.",
        ]

    if any(k in base for k in ["estudo_caso", "estudo de caso", "situacao-problema", "situacao problema", "caso"]):
        return [
            "Dividir o estudo de caso em perguntas menores: identificar o problema, localizar evidencias, explicar causas e registrar conclusao.",
            "Disponibilizar esquema de causa e consequencia para apoiar a organizacao do raciocinio cientifico.",
            "Permitir respostas em topicos, setas, desenho explicativo ou explicacao oral antes do registro final.",
        ]

    if any(k in base for k in ["leitura_analise", "noticia", "reportagem", "dados", "inpe", "ibge", "fonte", "hora da leitura"]):
        return [
            "Realizar leitura mediada do texto ou dado, destacando fonte, tema, informacoes centrais e vocabulario cientifico.",
            "Disponibilizar perguntas orientadoras para localizar evidencias e relacionar o texto aos conceitos da aula.",
            "Permitir registro em frases curtas ou topicos antes da resposta discursiva completa.",
        ]

    if any(k in base for k in ["revisao_retomada", "relembre", "exercicio resolvido", "retomar"]):
        return [
            "Apresentar um exemplo resolvido no quadro antes da atividade individual, explicitando cada etapa do raciocinio.",
            "Disponibilizar quadro de palavras-chave e conceitos ja estudados para consulta durante a retomada.",
            "Organizar pares de apoio para comparar respostas e revisar justificativas antes da correcao coletiva.",
        ]

    return [
        "Utilizar imagens, esquemas, tabelas e exemplos do cotidiano para tornar o conceito cientifico mais concreto.",
        "Organizar o registro em etapas curtas: hipotese inicial, conceito estudado, evidencia observada e sintese final.",
        "Permitir diferentes formas de resposta, como topicos, desenho, setas, frases curtas ou explicacao oral mediada.",
    ]


def _acessibilidade_biologia(tema: str, aprendizagem: str, desenvolvimento: str) -> list[str]:
    from core.lib.classificador import detectar_tipo_aula

    tipo = detectar_tipo_aula(desenvolvimento, tema, "Biologia")

    if tipo == "aula_desafio":
        return [
            "Dividir o estudo de caso em perguntas menores: identificar o problema, localizar evidências, formular hipóteses e registrar a conclusão em etapas.",
            "Disponibilizar esquema visual com dados do caso, pistas principais e espaço para comparar hipóteses antes da Hora da verdade.",
            "Permitir respostas em tópicos, setas, desenho explicativo ou fala mediada antes do registro final escrito.",
        ]

    if tipo == "aula_pratica":
        return [
            "Apresentar materiais, procedimentos e objetivos da prática em sequência visual curta, com retomada oral antes do início da atividade.",
            "Permitir registro por desenho, esquema, tabela simples ou explicação oral para estudantes com dificuldade de escrita durante a observação.",
            "Organizar grupos cooperativos com funções definidas para garantir participação de todos na prática e na discussão dos resultados.",
        ]

    if tipo == "revisao_consolidacao":
        return [
            "Disponibilizar glossário, quadro de palavras-chave ou comparação entre conceitos para apoiar a revisão antes das respostas individuais.",
            "Conduzir o quiz ou a retomada com leitura mediada das questões, dando tempo de resposta e retomando os termos centrais no quadro.",
            "Permitir respostas em frases curtas, tópicos ou explicação oral mediada antes da versão discursiva completa.",
        ]

    if tipo == "impacto_socioambiental":
        return [
            "Ler coletivamente os dados, mapas, gráficos ou notícias antes da análise individual, destacando fonte, título, legenda e palavras-chave.",
            "Organizar perguntas orientadoras para ajudar a turma a relacionar o fenômeno biológico a impactos ambientais, sociais ou de saúde pública.",
            "Permitir registro por tópicos, setas, tabela simples ou fala mediada para apoiar a interpretação crítica das evidências.",
        ]

    return [
        "Utilizar imagens, esquemas, modelos visuais e exemplos do cotidiano para tornar o conceito biológico mais concreto.",
        "Organizar a atividade em etapas curtas, com apoio no quadro para destacar processo, evidências, palavras-chave e síntese final.",
        "Permitir diferentes formas de resposta, como tópicos, desenho, setas, frases curtas ou explicação oral mediada conforme a necessidade.",
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


GeradorAcessibilidade = Callable[[str, str, str], list[str]]

GERADORES_ACESSIBILIDADE_POR_PERFIL: dict[str, GeradorAcessibilidade] = {
    "ingles": _acessibilidade_ingles,
    "lingua_portuguesa_ef": _acessibilidade_lingua_portuguesa,
    "lingua_portuguesa_em": _acessibilidade_lingua_portuguesa,
    "leitura_redacao": _acessibilidade_lingua_portuguesa,
    "matematica": _acessibilidade_matematica,
    "ciencias_ef": _acessibilidade_ciencias,
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
