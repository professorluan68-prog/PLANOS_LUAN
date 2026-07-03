import os
import re
import hashlib
import logging
from pathlib import Path

from core.ae_priorizado import carregar_base_habilidades_planilha
from core.avaliacao import gerar_acessibilidade_dinamica, gerar_acompanhamento_dinamico
from core.listas_pedagogicas import normalizar_lista_exatamente_tres
from core.metodologia_texto import ajustar_verbos_para_infinitivo
from core.projeto_vida_escopo import buscar_item_projeto_vida, montar_aprendizagem_projeto_vida
from core.referencias_cdp_contextual import referencia_cdp_contextual_por_pdf
from core.redacao_leitura_metodologia import gerar_metodologia_redacao_leitura
from core.orientacao_estudos_objetivos import (
    buscar_objetivos_orientacao_estudos,
    formatar_objetivos_orientacao_estudos,
)
from core.qualidade_metodologica import detectar_contexto_metodologico, naturalizar_metodologia_professor, revisar_metodologia
from core.lib.gerador_colunas_pedagogicas import montar_colunas_pedagogicas
from core.lib.classificador import normalizar_texto as normalizar_texto_lote, perfil_disciplina as perfil_disciplina, contem_termos as _contem, detectar_tipo_aula as _detectar_tipo_aula_classificador
from core.lib.extrator_pdf import extrair_texto_pdf as _extrair_texto_pdf, limpar_linhas as _limpar_linhas
from core.lib.extrator_pptx import (
    eh_cenario_piloto_pptx,
    encontrar_pptx_correspondente,
    extrair_estrutura_pptx,
    estrutura_pptx_para_dados_aula,
)
from core.lib.extrator_titulo import (
    _extrair_titulo_multilinha,
    _juntar_partes_titulo,
    _limpar_titulo_material,
    _linha_generica,
    _linha_periodo_ensino,
    _linha_rotulo_aula,
    _linhas_relevantes,
    _titulo_deve_juntar_continuacao,
    _titulo_em_linha_aula,
)
from core.eja.adaptador_eja import perfil_suporta_eja as _perfil_suporta_eja
from core.lib.modalidades import adaptar_metodologia_eja as _adaptar_metodologia_eja, garantir_tecnicas_lemov_na_metodologia as _garantir_tecnicas_lemov_na_metodologia
from core.orientacao_estudos_metodologia import extrair_etapas_orientacao_estudos as _extrair_etapas_orientacao_estudos
from core.cdp.gerador_cdp import (
    acessibilidade_cdp_contextual,
    acompanhamento_cdp_contextual,
    disciplina_base_cdp_contextual,
    eh_cdp_contextual_disciplina,
    formatar_material_cdp_contextual,
    metodologia_cdp_contextual,
    tipo_conteudo_cdp,
    tema_cdp_seguro,
    limpar_tema_cdp_contextual,
    limpar_texto_cdp_contextual,
    conceito_cdp_contextual,
)
from core.divisor_metodologia import processar_pdf_e_dividir_metodologia
from core.contexto_aula_pdf import DependenciasContextoAulaPDF, preparar_contexto_aula_pdf
from core.executor_plano import finalizar_plano_aula, processar_lote_pdfs
from core.reuso_cache_plano import tentar_reutilizar_cache_plano
from core.resultados_aula import (
    DependenciasResultadosAula,
    montar_resultado_aula_ia as _montar_resultado_aula_ia_core,
    montar_resultado_aula_local as _montar_resultado_aula_local_core,
)
from core.seletor_referencias import (
    assinatura_docx_referencia as _assinatura_docx_referencia,
    deve_aplicar_referencia_docx_no_resultado_ia as _deve_aplicar_referencia_docx_no_resultado_ia,
    habilidade_referencia_docx as _habilidade_referencia_docx,
    itens_referencia_docx as _itens_referencia_docx,
    localizar_docx_referencia_por_perfil as _localizar_docx_referencia_por_perfil,
    material_aula_com_titulo as _material_aula_com_titulo,
    origem_metodologia_por_referencia as _origem_metodologia_por_referencia,
    perfil_docx_somente_colunas_pedagogicas as _perfil_docx_somente_colunas_pedagogicas,
    perfil_prioriza_docx_sobre_cache_json as _perfil_prioriza_docx_sobre_cache_json,
    referencia_docx_por_perfil as _referencia_docx_por_perfil,
    referencia_docx_sobrescreve_metadados as _referencia_docx_sobrescreve_metadados,
    sobrescrever_listas_pedagogicas_com_referencia as _sobrescrever_listas_pedagogicas_com_referencia,
)

# Compatibilidade para testes e legado
_eh_cdp_contextual_disciplina = eh_cdp_contextual_disciplina
_disciplina_base_cdp_contextual = disciplina_base_cdp_contextual
_limpar_tema_cdp_contextual = limpar_tema_cdp_contextual
_formatar_material_cdp_contextual = formatar_material_cdp_contextual
_metodologia_cdp_contextual = metodologia_cdp_contextual
_acompanhamento_cdp_contextual = acompanhamento_cdp_contextual
_acessibilidade_cdp_contextual = acessibilidade_cdp_contextual
_tipo_conteudo_cdp = tipo_conteudo_cdp
_tema_cdp_seguro = tema_cdp_seguro
_limpar_texto_cdp_contextual = limpar_texto_cdp_contextual
_conceito_cdp_contextual = conceito_cdp_contextual
_normalizar = normalizar_texto_lote
_perfil_disciplina = perfil_disciplina
logger = logging.getLogger(__name__)

def _titulo_escopo_projeto_vida_confiavel(titulo: str) -> bool:
    titulo = re.sub(r"\s+", " ", str(titulo or "")).strip()
    if not titulo or len(titulo) > 140:
        return False

    base = _normalizar(titulo)
    marcadores_texto_bimestre = (
        "este bimestre",
        "se organiza em torno",
        "roadmap",
        "entregas",
        "produto",
        "ao longo das aulas",
        "competencias socioemocionais",
    )
    return not any(marcador in base for marcador in marcadores_texto_bimestre)


def _localizar_planilha_habilidade_local(caminho_pdf: str) -> Path | None:
    caminho = Path(str(caminho_pdf or "").strip())
    pasta = caminho.parent if caminho.parent.exists() else None
    if not pasta:
        return None

    padroes = ["planilha.xlsx", "GUIA*.xlsx", "*GUIA*.xlsx", "*.xlsx"]
    vistos: set[Path] = set()
    for padrao in padroes:
        for candidato in pasta.glob(padrao):
            try:
                resolvido = candidato.resolve()
            except OSError:
                continue
            if candidato.name.startswith("~$") or resolvido in vistos:
                continue
            vistos.add(resolvido)
            return candidato
    return None


def _habilidade_planilha_local(caminho_pdf: str, numero_aula: str) -> str:
    planilha = _localizar_planilha_habilidade_local(caminho_pdf)
    if not planilha:
        return ""

    match = re.search(r"\d{1,3}", str(numero_aula or ""))
    if not match:
        return ""
    numero = int(match.group(0))

    try:
        itens = carregar_base_habilidades_planilha(str(planilha)).get("mapa_por_aula", [])
    except Exception:
        return ""

    for item in itens:
        if int(item.get("aula_numero") or 0) != numero:
            continue
        return re.sub(r"\s+", " ", str(item.get("habilidade_textos") or "")).strip()
    return ""


def _resolver_habilidade_portugues(habilidade_pdf: str, caminho_pdf: str, numero_aula: str) -> str:
    habilidade_pdf = re.sub(r"\s+", " ", str(habilidade_pdf or "")).strip()
    if not _texto_habilidade_invalido_ou_truncado(habilidade_pdf):
        return habilidade_pdf

    habilidade_planilha = _habilidade_planilha_local(caminho_pdf, numero_aula)
    if habilidade_planilha and not _texto_habilidade_invalido_ou_truncado(habilidade_planilha):
        return habilidade_planilha

    return habilidade_pdf


def _disciplina_base_cdp_por_cadastro(disciplina: str) -> str:
    base = normalizar_texto_lote(disciplina)
    if "cdp" not in base:
        return ""
    opcoes = [
        ("Língua Portuguesa", ["lingua portuguesa", "portugues"]),
        ("Matemática", ["matematica"]),
        ("Ciências", ["ciencias"]),
        ("História", ["historia"]),
        ("Geografia", ["geografia"]),
        ("Arte", ["arte"]),
        ("Biologia", ["biologia"]),
        ("Física", ["fisica"]),
        ("Química", ["quimica"]),
        ("Língua Inglesa", ["lingua inglesa", "ingles"]),
        ("Sociologia", ["sociologia"]),
        ("Liderança e Oratória", ["lideranca e oratoria", "lideranca", "oratoria"]),
    ]
    for nome, termos in opcoes:
        if any(termo in base for termo in termos):
            return nome
    return ""

_ORIENTACAO_ESTUDOS_TITULOS = {
    ("missao", 1): "Jogos com palavras e imagens",
    ("missao", 2): "Para chorar de rir",
    ("missao", 3): "Da charge à notícia",
    ("missao", 4): "Que tirada!",
    ("missao", 5): "Vamos a fundo nos assuntos",
    ("missao", 6): "Uma palavra puxa a outra",
    ("missao", 7): "A trama do texto",
    ("missao", 8): "Por dentro dos verbetes",
    ("missao", 9): "Narrativas breves",
    ("missao", 10): "A voz da poesia",
    ("missao", 11): "Um mergulho no cordel",
    ("missao", 12): "Poema para mim e para você",
    ("missao", 13): "Lendas e narrativa",
    ("missao", 14): "Qual é a moral da história",
    ("missao", 15): "O texto no teatro",
    ("missao", 16): "Opinião versus fato",
    ("trilha", 1): "Crônicas e conectivos",
    ("trilha", 2): "Romances e conectivos",
    ("trilha", 3): "Crônicas, tirinhas e conectivos",
    ("trilha", 4): "Histórias em quadrinhos e humor",
    ("trilha", 5): "Contos e finalidade do texto",
    ("trilha", 6): "Causos e variação linguística",
    ("trilha", 7): "Projetos culturais e coesão textual",
    ("trilha", 8): "Cartas de leitor e argumento",
    ("trilha", 9): "Elementos da notícia",
    ("trilha", 10): "Notícias e opinião",
    ("trilha", 11): "Notícias, charges e crítica",
    ("trilha", 12): "Carta aberta e argumentação",
    ("trilha", 13): "Muito mais informações",
    ("trilha", 14): "Reportagens e informação",
    ("trilha", 15): "Campanhas comunitárias e informação",
    ("trilha", 16): "Textos de divulgação científica",
    ("jornada", 1): "Nas entrelinhas da notícia",
    ("jornada", 2): "Repercussão das notícias nos quadrinhos",
    ("jornada", 3): "Contando o dia a dia",
    ("jornada", 4): "Diferentes formas de dizer a mesma coisa",
    ("jornada", 5): "Linguagem poética, versos e rimas",
    ("jornada", 6): "Lendas e mitos: rever com olhos novos",
    ("jornada", 7): "Entre manifestos e outras reivindicações",
    ("jornada", 8): "Das resenhas às videorresenhas",
    ("jornada", 9): "Informação visual",
    ("jornada", 10): "Informações em infográficos, gráficos, tabelas e esquemas",
    ("jornada", 11): "Linguagem poética: poema, slam e canção",
    ("jornada", 12): "Palavras, ilustrações e paratextos",
    ("jornada", 13): "Recursos midiáticos",
    ("jornada", 14): "A língua (a) viva: variedades linguísticas",
    ("jornada", 15): "Gêneros científicos e refutação de teses",
    ("jornada", 16): "Anúncios para você",
}


def _familia_numero_orientacao_estudos(caminho_pdf: str) -> tuple[str, int]:
    base_arquivo = normalizar_texto_lote(Path(caminho_pdf).stem)
    for familia in ("missao", "trilha", "jornada"):
        match = re.search(rf"{familia}[_\s-]*(\d{{1,2}})", base_arquivo)
        if match:
            return familia, int(match.group(1))
    return "", 0


def _titulo_catalogado_orientacao_estudos(caminho_pdf: str, texto: str = "") -> str:
    familia, numero = _familia_numero_orientacao_estudos(caminho_pdf)
    if familia and numero:
        titulo = _ORIENTACAO_ESTUDOS_TITULOS.get((familia, numero))
        if titulo:
            return f"{familia.upper()} {numero} - {titulo}"

    base_texto = normalizar_texto_lote(texto)
    for (familia_catalogo, numero_catalogo), titulo_catalogado in _ORIENTACAO_ESTUDOS_TITULOS.items():
        if normalizar_texto_lote(titulo_catalogado) in base_texto:
            return f"{familia_catalogo.upper()} {numero_catalogo} - {titulo_catalogado}"
    return ""


def _titulo_ja_rotulado_orientacao_estudos(titulo: str) -> bool:
    return bool(re.match(r"^(missao|trilha|jornada)\s+\d+\s+-\s+", normalizar_texto_lote(titulo)))


def _detectar_tecnicas_lemov(texto: str, tema: str = "") -> list[str]:
    base = normalizar_texto_lote(f"{tema} {texto}")
    mapa = [
        ("VIREM E CONVERSEM", ["virem e conversem"]),
        ("TODO MUNDO ESCREVE", ["todo mundo escreve"]),
        ("COM SUAS PALAVRAS", ["com suas palavras"]),
        ("HORA DA LEITURA", ["hora da leitura"]),
        ("DE OLHO NO MODELO", ["de olho no modelo"]),
        ("PAUSE E RESPONDA", ["pause e responda"]),
        ("UM PASSO DE CADA VEZ", ["um passo de cada vez"]),
    ]
    tecnicas = []
    for nome, termos in mapa:
        if any(termo in base for termo in termos):
            tecnicas.append(nome)
    return tecnicas


def _detectar_tipo_aula(texto: str, tema: str, disciplina: str = "", turma: str = "") -> str:
    return _detectar_tipo_aula_classificador(texto, tema, disciplina, turma=turma)


def _metodologia_fixa_pdf_especial(texto: str, disciplina: str, tema: str) -> list[dict] | None:
    perfil = perfil_disciplina(disciplina)
    base = normalizar_texto_lote(f"{disciplina} {tema} {texto}")

    if perfil == "matematica" and _contem(base, ["aula khan", "pratica na khan", "atividade khan"]) and _contem(
        base,
        ["revisao", "conceito de funcao", "relacoes proporcionais", "grandezas diretamente proporcionais"],
    ):
        return [
            {
                "titulo": "Para comecar",
                "texto": (
                    "Retomar com a turma os conceitos principais da aula, relacionando o conteudo a situacoes "
                    "do cotidiano e levantando conhecimentos previos dos alunos sobre funcao, proporcionalidade "
                    "e relacoes entre grandezas."
                ),
            },
            {
                "titulo": "Foco no conteudo",
                "texto": (
                    "Revisar os conceitos trabalhados em sala por meio de exemplos no quadro, leitura de graficos, "
                    "analise de tabelas e pequenas situacoes-problema, destacando como uma grandeza pode depender "
                    "da outra e como essa relacao pode ser representada matematicamente."
                ),
            },
            {
                "titulo": "Pratica e consolidacao",
                "texto": (
                    "Orientar os alunos na resolucao de atividades no caderno e, em seguida, encaminha-los para "
                    "a pratica no aplicativo, reforcando que o objetivo e revisar, testar hipoteses, aprender com "
                    "os erros e repetir a atividade sempre que necessario ate dominar a habilidade."
                ),
            },
            {
                "titulo": "Fechamento",
                "texto": (
                    "Retomar coletivamente as principais duvidas percebidas durante a atividade, socializar "
                    "estrategias de resolucao e registrar os pontos que precisarao ser reforcados nas proximas "
                    "aulas, utilizando o desempenho dos alunos no aplicativo como apoio para o acompanhamento "
                    "da aprendizagem."
                ),
            },
        ]

    return None


def _metodologia_por_blocos_estruturados(blocos: dict[str, str] | None) -> list[dict]:
    if not isinstance(blocos, dict):
        return []

    ordem = [
        ("Para comecar", "Para comecar"),
        ("Foco no conteudo", "Foco no conteudo"),
        ("Na pratica", "Na pratica"),
        ("Encerramento", "Encerramento"),
    ]
    metodologia = []
    for chave, titulo in ordem:
        texto = str(blocos.get(chave) or "").strip()
        if texto:
            metodologia.append({"titulo": titulo, "texto": texto})
    return metodologia


def _conceito_principal(linhas: list[str], tema: str) -> str:
    marcadores_ignorar = {
        "para comecar",
        "contextualizacao",
        "leitura analitica",
        "leitura e construcao do conteudo",
        "exploracao",
        "foco no conteudo",
        "formalizacao",
        "pause e responda",
        "na pratica",
        "revisao e reescrita",
        "relembre",
        "encerramento",
        "sistematizacao",
        "todo mundo escreve",
        "virem e conversem",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "listen and repeat",
        "write and share",
        "say it in english",
    }
    candidatos = []
    for linha in linhas[:12]:
        normalizada = normalizar_texto_lote(linha)
        if normalizada in marcadores_ignorar:
            continue
        if _linha_com_marcador_metodologico(linha):
            continue
        linha_limpa = _limpar_linha_metodologica(linha)
        if not linha_limpa:
            continue
        if _linha_instrucao_matematica(linha_limpa):
            continue
        if 8 <= len(linha_limpa) <= 120:
            candidatos.append(linha_limpa)
    return candidatos[0] if candidatos else tema


def _linha_com_marcador_metodologico(linha: str) -> bool:
    normalizada = normalizar_texto_lote(linha)
    marcadores = [
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "pause e responda",
        "para comecar",
        "foco no conteudo",
        "na pratica",
        "encerramento",
    ]
    quantidade = sum(1 for marcador in marcadores if marcador in normalizada)
    if quantidade >= 2:
        return True
    return any(normalizada.startswith(marcador) for marcador in marcadores)


def _limpar_linha_metodologica(linha: str) -> str:
    limpa = re.sub(r"\s+", " ", str(linha or "")).strip(" -:;•\t")
    padroes = [
        r"\bVIREM\s+E\s+CONVERSEM\b",
        r"\bTODO\s+MUNDO\s+ESCREVE\b",
        r"\bCOM\s+SUAS\s+PALAVRAS\b",
        r"\bHORA\s+DA\s+LEITURA\b",
        r"\bDE\s+OLHO\s+NO\s+MODELO\b",
        r"\bUM\s+PASSO\s+DE\s+CADA\s+VEZ\b",
    ]
    for padrao in padroes:
        limpa = re.sub(padrao, "", limpa, flags=re.I)
    limpa = re.sub(r"\s+", " ", limpa).strip(" -:;•\t")
    return limpa


from core.lib.matematica_lote import _linha_instrucao_matematica


def _perguntas_orientadoras(tipo: str, tema: str, conceito: str) -> str:
    perguntas = {
        "algebra": [
            "Quais grandezas estao envolvidas na situacao?",
            "Como representar matematicamente essa relacao?",
            "O resultado encontrado faz sentido no contexto?",
        ],
        "funcoes": [
            "Que relacao de dependencia existe entre as grandezas?",
            "Como a tabela e o grafico representam essa variacao?",
            "O comportamento e crescente ou decrescente? Por quê?",
        ],
        "geometria": [
            "Que propriedades da figura ajudam na resolucao?",
            "Que medidas precisam ser observadas ou calculadas?",
            "Como justificar o procedimento utilizado?",
        ],
        "grandezas_medidas": [
            "Quais sao as grandezas envolvidas e suas unidades?",
            "A relacao e direta ou inversamente proporcional?",
            "Como interpretar o valor obtido no contexto?",
        ],
        "estatistica_probabilidade": [
            "Que dados ou eventos precisam ser analisados?",
            "Como organizar essas informacoes para interpretar melhor?",
            "O resultado pode ser expresso em fracao, decimal e porcentagem?",
        ],
        "combinatoria": [
            "A ordem dos elementos importa nesta situacao?",
            "Como listar ou contar os casos possiveis de modo organizado?",
            "O total encontrado faz sentido no contexto?",
        ],
        "modelagem": [
            "Que grandezas e relacoes aparecem na situacao?",
            "Como traduzir o problema para linguagem matematica?",
            "Como interpretar a resposta no contexto original?",
        ],
        "verificacao": [
            "Que conceito ou procedimento precisa ser retomado?",
            "Qual estrategia e mais adequada para resolver cada item?",
            "Como verificar se a resposta final esta coerente?",
        ],
        "leitura": [
            f"O que o titulo {tema} antecipa sobre o texto?",
            "Quais informacoes ajudam a compreender a finalidade do material?",
            "Que pistas do texto ou da imagem justificam as respostas?",
        ],
        "argumentacao": [
            "Qual opiniao ou ponto de vista aparece no material?",
            "Que argumentos sustentam essa ideia?",
            "Que recursos tornam a mensagem mais convincente?",
        ],
        "producao": [
            "Para quem o texto sera escrito?",
            "Qual finalidade deve orientar a producao?",
            "Que criterios precisam ser observados na revisao?",
        ],
        "investigacao": [
            "Que fenomeno ou problema esta sendo investigado?",
            "Quais evidencias aparecem no material?",
            "Como podemos explicar o processo com nossas palavras?",
        ],
        "fonte_historica": [
            "Quem produziu essa fonte e em que contexto?",
            "Que informacoes ela revela sobre o periodo estudado?",
            "Que relacao podemos fazer com o presente?",
        ],
        "analise_geografica": [
            "Que elementos da paisagem, mapa ou grafico precisam ser observados?",
            "Que relacoes existem entre espaco, sociedade e natureza?",
            "Que exemplos do cotidiano ajudam a entender o tema?",
        ],
        "resolucao_problemas": [
            "Quais dados o problema apresenta?",
            "Que estrategia de resolucao pode ser usada?",
            "Como verificar se o resultado faz sentido?",
        ],
        "lingua_estrangeira": [
            "Quais palavras ou expressoes ja conhecemos?",
            "Em que situacao real podemos usar esse vocabulario?",
            "Como pronunciar e empregar as estruturas trabalhadas?",
        ],
        "arte_pratica": [
            "Que sensacoes, ideias ou referencias a obra/material provoca?",
            "Que elementos visuais, sonoros ou corporais podemos perceber?",
            "Como transformar essa observacao em criacao ou registro?",
        ],
        "reflexiva": [
            "Como esse tema aparece na vida escolar ou pessoal?",
            "Que escolhas ou atitudes podem ser observadas nessa situacao?",
            "Que compromisso simples pode ser assumido a partir da aula?",
        ],
    }
    escolhidas = perguntas.get(tipo) or [
        f"O que ja sabemos sobre {tema}?",
        f"Quais ideias principais aparecem em {conceito}?",
        "Como registrar e aplicar o que foi discutido?",
    ]
    return "Perguntas orientadoras: " + " ".join(f"- {p}" for p in escolhidas)





def _eh_producao_final_redacao(texto_base: str, tema: str = "") -> bool:
    # Check top lines of the text_base for reading indicators
    linhas_topo = _limpar_linhas(texto_base)[:6]
    texto_topo = normalizar_texto_lote(" ".join(linhas_topo))
    texto_topo_limpo = re.sub(r"[^\w\s]", " ", texto_topo)
    texto_topo_limpo = re.sub(r"\s+", " ", texto_topo_limpo).strip()
    if "pratica de linguagem leitura" in texto_topo_limpo or "praticas de leitura" in texto_topo_limpo or "praticas de linguagem leitura" in texto_topo_limpo:
        if "producao de textos" not in texto_topo_limpo and "pratica de linguagem producao" not in texto_topo_limpo:
            return False

    base = normalizar_texto_lote(f"{tema} {texto_base}")
    if "pratica de linguagem" in base and "leitura" in base and not any(
        termo in base
        for termo in [
            "producao de textos",
            "versao final",
            "revisao orientada",
            "redacao paulista",
            "submissao",
            "reescrita",
            "rascunho",
        ]
    ):
        return False
    return any(
        termo in base
        for termo in [
            "producao de textos",
            "versao final",
            "revisao orientada",
            "redacao paulista",
            "submissao",
            "reescrita",
            "rascunho",
        ]
    )



def _extrair_tema_redacao_leitura(texto: str) -> str | None:
    linhas = _limpar_linhas(texto)
    if not linhas:
        return None
        
    texto_topo = " ".join(linhas[:20])
    
    # 1. Trilha with quotes
    match_trilha = re.search(r'(Trilha\s+[“"\'\u201c][^”"\'\u201d]+[”"\'\u201d])', texto_topo, flags=re.I)
    if match_trilha:
        return match_trilha.group(1).strip()
        
    # 2. Elaboração do Projeto/Rascunho/Texto
    match_elab = re.search(r'(Elaboração\s+(?:do|de|)\s*(?:Projeto\s+de\s+Texto\s+\d+|rascunho|texto\s+\d+))', texto_topo, flags=re.I)
    if match_elab:
        return match_elab.group(1).strip()
        
    # 3. Versão final do Texto / Rascunho
    match_versao = re.search(r'(Versão\s+final\s+do\s+Texto\s+\d+|Versão\s+final\s+do\s+rascunho)', texto_topo, flags=re.I)
    if match_versao:
        return match_versao.group(1).strip()

    # 4. Devolutiva do Texto
    match_devolutiva = re.search(r'(Devolutiva\s+do\s+Texto\s+\d+)', texto_topo, flags=re.I)
    if match_devolutiva:
        return match_devolutiva.group(1).strip()
        
    # Fallback to line-by-line matches if not found in joined format
    for linha in linhas[:20]:
        match = re.search(r'(Trilha\s+[“"[][^”"\]]+[”"\]])', linha, flags=re.I)
        if match:
            return match.group(1).strip()
        
        match_v = re.search(r'(Versão\s+final\s+do\s+Texto\s+\d+)', linha, flags=re.I)
        if match_v:
            return match_v.group(1).strip()

        match_d = re.search(r'(Devolutiva\s+do\s+Texto\s+\d+)', linha, flags=re.I)
        if match_d:
            return match_d.group(1).strip()

    # Generic Trilha/Versão final/Devolutiva matches
    for linha in linhas[:20]:
        linha_lower = linha.lower()
        if "trilha" in linha_lower:
            match = re.search(r'(Trilha\s+.+)', linha, flags=re.I)
            if match:
                t = match.group(1).split('|')[0].strip()
                t = re.sub(r'^(Trilha\s+[^-\n]+).*$', r'\1', t).strip()
                return t
        if "versao final" in normalizar_texto_lote(linha):
            match = re.search(r'(Versão\s+final\s+.+)', linha, flags=re.I)
            if match:
                return match.group(1).split('|')[0].strip()
        if "devolutiva" in normalizar_texto_lote(linha):
            match = re.search(r'(Devolutiva\s+.+)', linha, flags=re.I)
            if match:
                return match.group(1).split('|')[0].strip()
                
    return None


def _metodologia_leitura_redacao_modelo(texto_base: str, tema: str, turma: str = "") -> list[dict]:
    return gerar_metodologia_redacao_leitura(texto_base, tema, turma=turma)


def _remover_abertura_generica(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    padroes = [
        r"^Retomar conhecimentos previos da turma sobre [^.]+\.?\s*",
        r"^Retomar conhecimentos pr[eé]vios da turma sobre [^.]+\.?\s*",
        r"^Promover discuss[aã]o inicial sobre [^.]+\.?\s*",
        r"^Apresentar [^.]+ e propor [^.]+ para que os estudantes mobilizem conhecimentos previos, levantem hipoteses e identifiquem o que precisa ser descoberto na situacao\.?\s*",
    ]
    for padrao in padroes:
        texto = re.sub(padrao, "", texto, count=1, flags=re.I).strip()
    return texto


def _anexar_orientacao_unica(texto: str, orientacao: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    orientacao = re.sub(r"\s+", " ", str(orientacao or "")).strip()
    if not orientacao:
        return texto
    if normalizar_texto_lote(orientacao[:80]) in normalizar_texto_lote(texto):
        return texto
    if texto and not texto.endswith((".", "!", "?")):
        texto += "."
    return f"{texto} {orientacao}".strip() if texto else orientacao


def _ajustar_texto_por_sequencia(
    texto: str,
    chave: str,
    indice_aula: int = 0,
    total_aulas: int = 1,
    tema: str = "",
) -> str:
    """Diferencia metodologia quando varios PDFs compoem uma sequencia."""
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if total_aulas <= 1 or not texto:
        return texto

    indice_aula = max(0, min(indice_aula, total_aulas - 1))
    ultima = indice_aula == total_aulas - 1
    primeira = indice_aula == 0

    if chave == "para_comecar" and not primeira:
        resto = _remover_abertura_generica(texto)
        if ultima:
            opcoes_abertura = [
                (
                    f"Retomar o percurso das aulas anteriores sobre {tema}, destacando os registros, "
                    "duvidas e estrategias ja construidos pela turma."
                ),
                (
                    f"Revisitar o percurso das aulas anteriores sobre {tema}, retomando os registros, "
                    "duvidas e estrategias construidos ate aqui."
                ),
                (
                    f"Dar continuidade ao estudo de {tema}, recuperando o percurso das aulas anteriores "
                    "e os registros produzidos pela turma."
                ),
            ]
        else:
            opcoes_abertura = [
                (
                    f"Retomar a aula anterior sobre {tema} e conectar os registros ja produzidos "
                    "ao novo foco do dia."
                ),
                (
                    f"Recuperar aprendizagens da aula anterior sobre {tema}, articulando os registros "
                    "ja produzidos ao novo foco do dia."
                ),
                (
                    f"Revisitar os registros da aula anterior sobre {tema} e relacionar essas anotacoes "
                    "ao encaminhamento do dia."
                ),
                (
                    f"Dar continuidade ao estudo de {tema}, retomando o que foi registrado anteriormente "
                    "e conectando ao foco da aula."
                ),
                (
                    f"Reativar os conhecimentos construidos na aula anterior sobre {tema}, conectando "
                    "os registros ja produzidos ao novo foco do dia."
                ),
            ]
        abertura = _escolher_variacao(opcoes_abertura, [tema, chave, str(indice_aula), str(total_aulas), resto[:120]])
        return f"{abertura} {resto}".strip()

    if chave in {"leitura", "contextualizacao", "leitura_analitica", "foco"} and not primeira:
        orientacao = (
            "Retomar registros anteriores quando necessário, ajudando a turma a perceber a continuidade do estudo."
        )
        return _anexar_orientacao_unica(texto, orientacao)

    if chave in {"pratica", "calculos", "planejamento", "projeto"} and not primeira:
        orientacao = (
            "Solicitar que os estudantes comparem as respostas de hoje com as estrategias usadas anteriormente, "
            "identificando avancos, ajustes e duvidas persistentes."
        )
        return _anexar_orientacao_unica(texto, orientacao)

    if chave == "pause" and not primeira:
        orientacao = (
            "Usar a pausa tambem para verificar quais aprendizagens da sequencia ja estao consolidadas "
            "e quais ainda precisam de retomada."
        )
        return _anexar_orientacao_unica(texto, orientacao)

    if chave == "encerramento":
        if ultima:
            orientacao = (
                "Fechar a sequencia com uma sintese final, retomando o percurso completo e registrando "
                "o que a turma consegue fazer com mais autonomia."
            )
        elif not primeira:
            orientacao = (
                "Registrar uma sintese parcial e uma pergunta para orientar a proxima aula da sequencia."
            )
        else:
            orientacao = (
                "Indicar que os registros desta aula serao retomados na continuidade da sequencia."
            )
        return _anexar_orientacao_unica(texto, orientacao)

    return texto


def _ajustar_metodologia_por_sequencia(
    metodologia,
    indice_aula: int = 0,
    total_aulas: int = 1,
    tema: str = "",
):
    if total_aulas <= 1:
        return metodologia

    mapa_titulos = {
        "para comecar": "para_comecar",
        "relembre": "para_comecar",
        "retomada conceitual": "para_comecar",
        "contextualizacao": "contextualizacao",
        "contextualizacao pratica": "foco",
        "leitura analitica": "leitura_analitica",
        "leitura e construcao do conteudo": "leitura",
        "foco no conteudo": "foco",
        "pause e responda": "pause",
        "na pratica": "pratica",
        "atividade central": "pratica",
        "calculos financeiros": "calculos",
        "planejamento orcamentario": "planejamento",
        "projeto empreendedor": "projeto",
        "encerramento": "encerramento",
        "encerramento reflexivo": "encerramento",
        "revisao e reescrita": "encerramento",
    }

    ajustada = []
    for item in metodologia or []:
        if not isinstance(item, dict):
            ajustada.append(item)
            continue
        novo_item = dict(item)
        titulo = normalizar_texto_lote(novo_item.get("titulo", ""))
        chave = mapa_titulos.get(titulo, "")
        if chave:
            novo_item["texto"] = _ajustar_texto_por_sequencia(
                novo_item.get("texto", ""),
                chave,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                tema=tema,
            )
        ajustada.append(novo_item)
    return _reduzir_frases_repetitivas_metodologia(
        ajustada,
        tema=tema,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
    )


def _montar_etapas_metodologia(
    texto: str,
    disciplina: str,
    turma: str,
    tema: str,
    indice_aula: int = 0,
    total_aulas: int = 1,
    contexto_geracao: dict | None = None,
) -> list[dict]:
    perfil = perfil_disciplina(disciplina)
    if perfil == "leitura_redacao":
        return _metodologia_leitura_redacao_modelo(texto, tema, turma=turma)

    metodologia = _motor_metodologico.gerar(
        texto_pdf=texto,
        disciplina=disciplina,
        turma=turma,
        tema=tema,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        contexto_geracao=contexto_geracao,
    )
    mapa_titulos = {
        "para comecar": "Para comecar",
        "relembre": "Relembre",
        "contextualizacao": "Contextualizacao",
        "leitura analitica": "Leitura analitica",
        "leitura e construcao do conteudo": "Leitura e construcao do conteudo",
        "foco no conteudo": "Foco no conteudo",
        "pause e responda": "Pause e responda",
        "na pratica": "Na pratica",
        "analise de caso": "Analise de caso",
        "calculos financeiros": "Calculos financeiros",
        "planejamento orcamentario": "Planejamento orcamentario",
        "projeto empreendedor": "Projeto empreendedor",
        "revisao e reescrita": "Revisao e reescrita",
        "encerramento": "Encerramento",
    }
    harmonizada = []
    for item in metodologia or []:
        if not isinstance(item, dict):
            harmonizada.append(item)
            continue
        novo_item = dict(item)
        titulo_norm = normalizar_texto_lote(novo_item.get("titulo", ""))
        if titulo_norm in mapa_titulos:
            novo_item["titulo"] = mapa_titulos[titulo_norm]
        harmonizada.append(novo_item)
    return harmonizada


def _tema_por_texto(texto: str, caminho_pdf: str, disciplina: str) -> str:
    if perfil_disciplina(disciplina) == "orientacao_estudos":
        titulo_catalogado = _titulo_catalogado_orientacao_estudos(caminho_pdf, texto)
        if titulo_catalogado:
            return titulo_catalogado

    def limpar_prefixo_disciplina(titulo: str) -> str:
        palavras_titulo = str(titulo or "").split()
        palavras_disciplina = str(disciplina or "").split()
        if not palavras_titulo or not palavras_disciplina:
            return str(titulo or "").strip()

        prefixo_titulo = [normalizar_texto_lote(p) for p in palavras_titulo[: len(palavras_disciplina)]]
        prefixo_disciplina = [normalizar_texto_lote(p) for p in palavras_disciplina]
        if prefixo_titulo == prefixo_disciplina:
            return " ".join(palavras_titulo[len(palavras_disciplina) :]).strip()

        primeiro_titulo = normalizar_texto_lote(palavras_titulo[0])
        primeiro_disciplina = normalizar_texto_lote(palavras_disciplina[0])
        if primeiro_titulo and primeiro_disciplina and primeiro_titulo[:5] == primeiro_disciplina[:5]:
            return " ".join(palavras_titulo[1:]).strip()

        return str(titulo or "").strip()

    linhas = _limpar_linhas(texto)
    for linha in linhas[:12]:
        titulo_aula = limpar_prefixo_disciplina(_limpar_titulo_material(_titulo_em_linha_aula(linha), disciplina))
        if len(titulo_aula) >= 6:
            titulo_aula_norm = normalizar_texto_lote(titulo_aula).replace(" ", "").replace("\ufffd", "")
            if not ("sugestoes" in titulo_aula_norm and "condu" in titulo_aula_norm):
                return titulo_aula[:120]

    if perfil_disciplina(disciplina) == "leitura_redacao":
        tema_leitura = _extrair_tema_redacao_leitura(texto)
        if tema_leitura:
            return tema_leitura

    candidatos = []
    disciplina_norm = normalizar_texto_lote(disciplina)
    disciplina_base = disciplina_norm.split()[0] if disciplina_norm else ""
    for linha in linhas[:8]:
        linha_norm = normalizar_texto_lote(linha)
        if linha_norm == disciplina_norm:
            continue
        if disciplina_base and len(linha.split()) <= max(2, len(str(disciplina or "").split())) and linha_norm.startswith(disciplina_base[:5]):
            continue
        titulo = _limpar_titulo_material(linha, disciplina)
        normalizada = normalizar_texto_lote(titulo)
        if len(titulo) < 4 or not titulo:
            continue
        if any(token in normalizada for token in ["bimestre", "ensino medio", "ensino fundamental"]):
            break
        if _linha_generica(titulo, disciplina):
            continue
        if _linha_rotulo_aula(normalizada) or normalizada.startswith(("slide ", "pagina ", "página ")):
            if candidatos:
                break
            continue
        candidatos.append(titulo)
        if len(candidatos) >= 4:
            break

    if candidatos:
        titulo = _juntar_partes_titulo(candidatos)
        titulo = limpar_prefixo_disciplina(titulo)
        if len(titulo) >= 6:
            return titulo[:120]

    titulo_multilinha = limpar_prefixo_disciplina(_extrair_titulo_multilinha(texto, disciplina))
    if len(titulo_multilinha) >= 6:
        return titulo_multilinha[:120]
    for linha in _limpar_linhas(texto):
        titulo = limpar_prefixo_disciplina(_limpar_titulo_material(linha, disciplina))
        titulo_norm = normalizar_texto_lote(titulo)
        if len(titulo) >= 6 and not _linha_generica(titulo, disciplina) and not (_linha_rotulo_aula(titulo_norm) or titulo_norm.startswith("slide ")):
            return titulo[:120]
    return Path(caminho_pdf).stem.replace("_", " ").replace("-", " ").title()


def _rotulo_aula_material(texto: str, caminho_pdf: str) -> str:
    # 1. Tentar ler do texto do PDF
    padrao_texto = re.compile(r"\baula\s*(?:n[.o]?\s*)?(\d{1,3})\b", flags=re.I)
    for linha in _limpar_linhas(texto)[:30]:
        match = padrao_texto.search(linha)
        if match:
            return f"AULA {match.group(1)}"

    # 2. Tentar padrão com separador e número no final do nome do arquivo, ex: Nome_01.pdf
    stem = Path(caminho_pdf).stem
    # Limpar sufixos de cópia comuns
    stem = re.sub(r"\s*\(\d+\)$", "", stem)
    stem = re.sub(r"(?i)\s*-\s*c[oó]pia$", "", stem)
    stem = re.sub(r"(?i)\s*-\s*copy$", "", stem)
    stem = stem.strip()

    match_end = re.search(r"[\s_.-]\s*(\d{1,4})$", stem)
    if match_end:
        return f"AULA {int(match_end.group(1))}"

    # 3. Padrão clássico "aula 12" no nome do arquivo
    match = re.search(r"\baula[_\s-]*(\d{1,3})\b", stem, flags=re.I)
    if match:
        return f"AULA {match.group(1)}"

    match_pdf = re.search(r"^pdf[_\s-]*(\d{1,3})(?:\D|$)", stem, flags=re.I)
    if match_pdf:
        return f"AULA {int(match_pdf.group(1))}"
    return ""


def _material_digital_por_texto(texto: str, caminho_pdf: str, disciplina: str, tema: str = "") -> str:
    rotulo = _rotulo_aula_material(texto, caminho_pdf)
    titulo = (tema or _tema_por_texto(texto, caminho_pdf, disciplina)).strip()
    if perfil_disciplina(disciplina) == "orientacao_estudos" and _titulo_ja_rotulado_orientacao_estudos(titulo):
        if rotulo:
            return f"{rotulo} - {titulo}"
        return titulo
    if rotulo and titulo:
        return f"{rotulo} - {titulo}"
    return rotulo or titulo


def _texto_metodologia(metodologia) -> str:
    blocos = []
    for item in metodologia or []:
        if isinstance(item, dict):
            titulo = str(item.get("titulo", "") or "").strip()
            texto = str(item.get("texto", "") or "").strip()
            blocos.append(f"{titulo}:\n{texto}".strip() if titulo else texto)
        else:
            blocos.append(str(item))
    return "\n\n".join(blocos)


def _metodologia_em_blocos_por_texto(texto: str) -> list[dict]:
    titulos_validos = {
        "para comecar",
        "disparo inicial / contextualizacao",
        "disparo inicial / contextualização",
        "leitura ou exploracao inicial",
        "leitura ou exploração inicial",
        "leitura compartilhada ou individual",
        "predicao guiada",
        "predição guiada",
        "analise guiada",
        "análise guiada",
        "sistematizacao",
        "sistematização",
        "foco no conteudo",
        "foco no conteúdo",
        "pause e responda",
        "na pratica",
        "na prática",
        "producao textual",
        "produção textual",
        "revisao orientada",
        "revisão orientada",
        "escrita da versao final",
        "escrita da versão final",
        "submissao e socializacao",
        "submissão e socialização",
        "revisao e fechamento",
        "revisão e fechamento",
        "encerramento",
    }
    linhas = [linha.rstrip() for linha in str(texto or "").splitlines()]
    blocos = []
    atual = None

    for linha in linhas:
        limpa = linha.strip()
        if not limpa:
            continue

        match = re.match(r"^([^:]{2,90}):\s*(.*)$", limpa)
        titulo_chave = normalizar_texto_lote(match.group(1)) if match else ""
        if match and titulo_chave in {normalizar_texto_lote(t) for t in titulos_validos}:
            titulo = match.group(1).strip()
            corpo = match.group(2).strip()
            if atual:
                atual["texto"] = " ".join(atual["texto"]).strip()
                blocos.append(atual)
            atual = {"titulo": titulo, "texto": [corpo] if corpo else []}
            continue

        if atual:
            atual["texto"].append(limpa)
        else:
            atual = {"titulo": "Desenvolvimento", "texto": [limpa]}

    if atual:
        atual["texto"] = " ".join(atual["texto"]).strip()
        blocos.append(atual)

    return [bloco for bloco in blocos if bloco.get("texto")]


_PADRAO_CODIGO_APRENDIZAGEM = re.compile(r"\(?((?:EM|EF)\d{2}[A-Z]{2,4}\d{0,3}[A-Z]?)\)?", flags=re.I)
_PADRAO_TURMA_METODOLOGIA = re.compile(
    r"\b(da turma|com a turma)\s+\d{1,2}\s*[º°oªa?]?\s*(?:ano|s[ée]rie|em|ef)?\s*[A-Z]?\b",
    flags=re.I,
)
_FINS_INCOMPLETOS_APRENDIZAGEM = {
    "a",
    "as",
    "o",
    "os",
    "um",
    "uma",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "em",
    "e",
    "com",
    "para",
    "por",
    "que",
}


_MARCADORES_INCOMPATIVEIS_TEMA = {
    "parasitoses": {
        "tema": [
            "esquistossomose",
            "platelminto",
            "platelmintos",
            "nematodeo",
            "nematodeos",
            "lombriga",
            "amarelao",
            "ascaris",
            "ancylostoma",
            "schistosoma",
            "parasita",
            "parasitos",
            "parasitologia",
        ],
        "bloqueados": [
            "audicao",
            "auditivo",
            "decibeis",
            "poluicao sonora",
            "som",
            "sistema visual",
            "visao",
            "olho humano",
            "retina",
        ],
    },
    "virologia": {
        "tema": ["virus", "viral", "virais", "virologia", "vacina", "vacinal"],
        "bloqueados": [
            "audicao",
            "auditivo",
            "decibeis",
            "poluicao sonora",
            "platelminto",
            "nematodeo",
            "lombriga",
            "esquistossomose",
        ],
    },
    "genetica_biotecnologia": {
        "tema": [
            "hereditariedade",
            "heredograma",
            "mendel",
            "dna",
            "gene",
            "genes",
            "genetica",
            "genetico",
            "biotecnologia",
            "clonagem",
            "bioetica",
            "biosseguranca",
        ],
        "bloqueados": [
            "audicao",
            "auditivo",
            "decibeis",
            "poluicao sonora",
            "caminho do som",
            "sistema digestorio",
            "digestao",
            "grupos alimentares",
            "cardapio",
        ],
    },
}


def _trecho_incompleto_aprendizagem(texto: str) -> bool:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return True
    normalizado = normalizar_texto_lote(texto)
    if any(marcador in texto for marcador in ["⬅", "←", "→"]):
        return True
    if "http" in normalizado or "disponivel em" in normalizado:
        return True
    if texto.endswith((",", ";", ":", "/", "-")):
        return True
    if texto.count("(") > texto.count(")") or texto.count("[") > texto.count("]"):
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    if palavras and normalizar_texto_lote(palavras[-1]) in _FINS_INCOMPLETOS_APRENDIZAGEM:
        return True
    if texto.count("?") >= 2 or re.match(r"^(?:o que|como|por que|qual)\b", normalizado):
        return True
    return len(texto) > 700


def _texto_incompativel_com_tema(texto: str, tema: str, conceito: str = "") -> bool:
    base_tema = normalizar_texto_lote(f"{tema} {conceito}")
    base_texto = normalizar_texto_lote(texto)
    if not base_texto or not base_tema:
        return False
    if _texto_tem_dominio_visao(base_texto) and not _tema_permite_dominio_visao(base_tema):
        return True
    if _texto_tem_dominio_audicao(base_texto) and not _tema_permite_dominio_audicao(base_tema):
        return True
    if _texto_tem_anatomia_especifica(base_texto) and not _tema_permite_anatomia_especifica(base_tema):
        return True
    if _tema_virus_celulas(base_tema) and _texto_tem_vacinacao(base_texto):
        return True
    for regra in _MARCADORES_INCOMPATIVEIS_TEMA.values():
        if any(marcador in base_tema for marcador in regra["tema"]):
            return any(marcador in base_texto for marcador in regra["bloqueados"])
    return False


def _texto_tem_dominio_visao(texto_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:olho|olhos|retina|cornea|pupila|cristalino|sistema visual|caminho da luz|formacao da imagem|estruturas do olho|visao)\b",
            texto_normalizado,
            flags=re.I,
        )
    )


def _tema_permite_dominio_visao(tema_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:olho|olhos|retina|cornea|pupila|cristalino|sistema visual|caminho da luz|formacao da imagem|visao)\b",
            tema_normalizado,
            flags=re.I,
        )
    )


def _texto_tem_dominio_audicao(texto_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:audicao|ouvido|ouvidos|decibel|decibeis|poluicao sonora|caminho do som|sistema auditivo|protecao auditiva)\b",
            texto_normalizado,
            flags=re.I,
        )
    )


def _tema_permite_dominio_audicao(tema_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:audicao|ouvido|ouvidos|decibel|decibeis|poluicao sonora|som|sistema auditivo|auditiva)\b",
            tema_normalizado,
            flags=re.I,
        )
    )


def _texto_tem_anatomia_especifica(texto_normalizado: str) -> bool:
    return any(
        marcador in texto_normalizado
        for marcador in [
            "esquema anatomico",
            "nomear oralmente cada estrutura",
            "nomes das estruturas",
        ]
    )


def _tema_permite_anatomia_especifica(tema_normalizado: str) -> bool:
    return bool(
        _tema_permite_dominio_visao(tema_normalizado)
        or _tema_permite_dominio_audicao(tema_normalizado)
        or re.search(
            r"\b(?:sistema respiratorio|pulmao|pulmoes|hematose|ventilacao pulmonar|sistema digestorio|corpo humano|anatomia|fisiologico|fisiologicos)\b",
            tema_normalizado,
            flags=re.I,
        )
    )


def _tema_virus_celulas(tema_normalizado: str) -> bool:
    return "virus" in tema_normalizado and any(
        termo in tema_normalizado
        for termo in ["celula", "celulas", "capsideo", "metabolismo", "intracelular", "bacteriofago"]
    )


def _tema_astronomia_terra_lua(tema_normalizado: str) -> bool:
    return any(
        termo in tema_normalizado
        for termo in [
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
        ]
    )


def _texto_tem_vacinacao(texto_normalizado: str) -> bool:
    return any(termo in texto_normalizado for termo in ["vacinacao", "vacina", "vacinal", "cobertura vacinal", "mutacao"])


def _foco_limpo_aprendizagem(tema: str, conceito: str = "") -> str:
    for candidato in [tema, conceito, "o tema da aula"]:
        texto = re.sub(r"\s+", " ", str(candidato or "")).strip(" .:-")
        if texto and not _trecho_incompleto_aprendizagem(texto):
            return texto[:140]
    return "o tema da aula"


def _conceito_generico_ou_quebrado_projeto_vida(conceito: str) -> bool:
    base = normalizar_texto_lote(conceito)
    if not base:
        return True
    if any(
        marcador in base
        for marcador in [
            "questao essencial",
            "habilidade",
            "competencia",
            "competencias",
            "tema da aula",
            "conteudo da aula",
        ]
    ):
        return True
    ultimo = base.split()[-1]
    return ultimo in {"a", "as", "o", "os", "de", "da", "do", "e", "em", "com", "para", "por"}


def _aprendizagem_padrao_projeto_vida(tema: str) -> str:
    foco = _foco_limpo_aprendizagem(tema, tema)
    if normalizar_texto_lote(foco) == "o tema da aula":
        foco = re.sub(r"\s+", " ", str(tema or "")).strip(" .:-") or "o ambiente digital"
    base = normalizar_texto_lote(foco)
    if any(termo in base for termo in ["post", "postar", "public", "print", "rede", "digital", "internet", "online"]):
        return (
            f"Refletir sobre {foco}, analisando escolhas, exposicao, respeito, responsabilidade e "
            "consequencias das acoes no ambiente digital."
        )
    return (
        f"Refletir sobre {foco}, relacionando o tema a escolhas, atitudes, convivencia respeitosa, "
        "autoconhecimento e tomada de decisao responsavel."
    )


def _aprendizagem_padrao_por_perfil(tema: str, perfil: str, conceito: str = "") -> str:
    foco = _foco_limpo_aprendizagem(tema, conceito)

    if perfil in {"projeto_de_vida", "lideranca_oratoria"}:
        return _aprendizagem_padrao_projeto_vida(foco)
    if perfil == "matematica":
        return (
            f"Resolver e analisar situacoes-problema relacionadas a {foco}, mobilizando procedimentos de calculo, "
            "interpretacao e justificativa das estrategias utilizadas."
        )
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        base_lp = normalizar_texto_lote(" ".join([foco, conceito]))
        if any(k in base_lp for k in ["literatura medieval", "trovadorismo", "cantiga"]):
            return (
                f"Analisar textos da tradição medieval portuguesa em {foco}, relacionando contexto histórico, "
                "vozes literárias, recursos expressivos e efeitos de sentido construídos na leitura."
            )
        if any(k in base_lp for k in ["gil vicente", "auto da barca"]):
            return (
                f"Interpretar trechos dramáticos relacionados a {foco}, observando personagens, crítica social, "
                "contexto histórico e recursos de linguagem presentes na obra."
            )
        if any(k in base_lp for k in ["classicismo", "camoes", "lusiadas"]):
            return (
                f"Analisar textos e referências do Classicismo em {foco}, relacionando forma poética, contexto "
                "renascentista, intertextualidades e construção de sentidos."
            )
        if any(k in base_lp for k in ["anuncio", "publicitario", "publicidade", "midias digitais"]):
            return (
                f"Analisar anúncios e campanhas relacionados a {foco}, reconhecendo público-alvo, suporte, "
                "recursos verbais e visuais, estratégias persuasivas e efeitos de sentido."
            )
        return (
            f"Analisar textos e linguagens relacionados a {foco}, desenvolvendo leitura, interpretacao, "
            "analise da linguagem e producao de sentidos de acordo com as propostas da aula."
        )
    if perfil == "historia":
        return (
            f"Analisar sujeitos, contextos, permanencias e mudancas relacionados a {foco}, utilizando fontes, "
            "registros e argumentos historicos para sustentar as interpretacoes construidas na aula."
        )
    if perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        return (
            f"Compreender e explicar aspectos relacionados a {foco}, articulando observacao, conceitos cientificos, "
            "leitura de esquemas e registro das evidencias trabalhadas na aula."
        )
    if perfil == "geografia":
        return (
            f"Analisar criticamente aspectos relacionados a {foco}, relacionando territorio, sociedade, natureza "
            "e leitura de diferentes linguagens geograficas ao longo da aula."
        )
    if perfil == "educacao_financeira":
        base_ef = normalizar_texto_lote(" ".join([foco, conceito]))
        if any(k in base_ef for k in ["credito", "endividamento", "divida", "dividas", "emprestimo", "financiamento", "juros", "parcel"]):
            return (
                f"Analisar situacoes relacionadas a {foco}, comparando custos, prazos, riscos e impactos no orcamento "
                "antes de tomar decisoes financeiras mais conscientes."
            )
        if any(k in base_ef for k in ["poupanca", "reserva", "investimento", "rendimento", "imprevisto"]):
            return (
                f"Compreender como poupanca, reserva e planejamento de longo prazo se relacionam a {foco}, "
                "analisando possibilidades de organizacao financeira e protecao diante de imprevistos."
            )
        if any(k in base_ef for k in ["consumo", "preco", "cesta basica", "simulador", "simuladores", "energia", "agua", "gas", "internet", "necessidade", "desejo"]):
            return (
                f"Analisar escolhas de consumo relacionadas a {foco}, comparando precos, necessidades, gastos fixos "
                "e variaveis e seus efeitos no orcamento familiar."
            )
        if any(k in base_ef for k in ["orcamento", "planejamento", "receita", "despesa", "gasto", "saldo", "planner", "meta"]):
            return (
                f"Compreender como receitas, despesas, prioridades e metas interferem em {foco}, analisando dados, "
                "comparando escolhas e registrando estrategias de planejamento financeiro."
            )
        return (
            f"Compreender conceitos de educacao financeira relacionados a {foco}, articulando organizacao do orcamento, "
            "analise de dados e tomada de decisao responsavel."
        )

    return f"Compreender e analisar conceitos relacionados a {foco}, articulando leitura, discussao orientada e registro das ideias centrais trabalhadas na aula."


def _remover_residuos_aprendizagem(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    padroes_corte = [
        r"\bTrilha\b",
        r"\bPr[aá]tica de linguagem\b",
        r"\bSUGEST[OÕ]ES PARA CONDU[ÇC][AÃ]O\b",
        r"\bAULA\s+\d+\b",
        r"\b\d+\.\s+(?:Disparo inicial|Leitura|Formula[çc][aã]o|An[aá]lise|Sistematiza[çc][aã]o|Produ[çc][aã]o|Revis[aã]o)\b",
        r"\s[●•]\s",
    ]
    for padrao in padroes_corte:
        match = re.search(padrao, texto, flags=re.I)
        if match and match.start() > 20:
            return texto[:match.start()].strip(" .;:-")
    return texto


def _sanitizar_aprendizagem(aprendizagem: str, tema: str, conceito: str = "", perfil: str = "") -> str:
    texto = _remover_residuos_aprendizagem(aprendizagem)
    texto = re.sub(
        r"^(?:C\d+\s*:\s*)?(?:Habilidades?\s+BNCC\s+e\s+Curr[ií]culo\s+Paulista|Habilidades?|Aprendizagem essencial|Compet[eê]ncia)\s*:\s*",
        "",
        texto,
        flags=re.I,
    ).strip()
    texto = re.sub(
        r"^(?:Habilidades?\s+BNCC\s+e\s+Curr[ií]culo\s+Paulista)\s*",
        "",
        texto,
        flags=re.I,
    ).strip()
    texto = re.sub(r"^(?:Habilidades?)\s*:\s*", "", texto, flags=re.I).strip()
    texto = re.sub(r"^(?:Habilidade\s+)+", "", texto, flags=re.I).strip()
    texto = re.sub(r"\s*\((?:S[ÃA]O\s+PAULO|BRASIL),\s*\d{4}\)\s*\.?", "", texto, flags=re.I).strip()
    match = _PADRAO_CODIGO_APRENDIZAGEM.search(texto)
    codigo = f"({match.group(1).upper()})" if match else ""

    if (
        perfil in {"projeto_de_vida", "lideranca_oratoria"}
        and (
            _trecho_incompleto_aprendizagem(texto)
            or _texto_incompativel_com_tema(texto, tema, conceito)
            or "desenvolver habilidades relacionadas ao tema da aula" in normalizar_texto_lote(texto)
        )
    ):
        if codigo:
            return f"Habilidade: {codigo} {_aprendizagem_padrao_projeto_vida(tema)}"
        return _aprendizagem_padrao_projeto_vida(tema)

    if _trecho_incompleto_aprendizagem(texto) or _texto_incompativel_com_tema(texto, tema, conceito):
        base_especifica = _aprendizagem_padrao_por_perfil(tema, perfil, conceito)
        if codigo:
            return f"Habilidade: {codigo} {base_especifica}"
        return base_especifica

    if codigo and not texto.lower().startswith("habilidade:"):
        texto = f"Habilidade: {texto}"
    return texto


def _texto_habilidade_invalido_ou_truncado(texto: str) -> bool:
    base = normalizar_texto_lote(texto)
    if not base:
        return True

    texto_limpo = re.sub(r"^habilidade:\s*", "", texto.strip(), flags=re.I)
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto_limpo)
    if not palavras:
        return True

    ultimo = normalizar_texto_lote(palavras[-1])
    if ultimo in {"a", "as", "o", "os", "de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "que"}:
        return True

    if len(texto_limpo) < 30:
        return True

    if texto_limpo[:1].islower():
        return True

    if _trecho_incompleto_aprendizagem(texto_limpo):
        return True

    return False


def _sintetizar_objetivos_e_conteudos_para_aprendizagem(
    tema: str,
    conceito: str = "",
    objetivos: list[str] | None = None,
    conteudos: list[str] | None = None,
    perfil: str = "",
) -> str:
    objetivos = [re.sub(r"\s+", " ", str(x or "")).strip(" .;:-") for x in (objetivos or []) if str(x or "").strip()]
    conteudos = [re.sub(r"\s+", " ", str(x or "")).strip(" .;:-") for x in (conteudos or []) if str(x or "").strip()]

    base_conceitual = conceito or " ".join(conteudos[:2])
    foco_tema = _foco_limpo_aprendizagem(tema, base_conceitual)

    if perfil == "geografia":
        if objetivos:
            verbo_base = objetivos[0]
            verbo_base = re.sub(r"^(identificar|analisar|reconhecer|interpretar|comparar|avaliar|explicar)\s+", lambda m: m.group(1).capitalize() + " ", verbo_base, flags=re.I)
            complemento = ""
            if len(objetivos) > 1:
                complemento = objetivos[1]
                complemento = re.sub(r"^(identificar|analisar|reconhecer|interpretar|comparar|avaliar|explicar)\s+", "", complemento, flags=re.I)
                complemento = complemento[:180].rstrip(" .;:-")
                if complemento:
                    return f"{verbo_base.rstrip(' .;:-')}, {complemento}."
            return verbo_base.rstrip(" .;:-") + "."

        if conteudos:
            return f"Analisar criticamente aspectos relacionados a {foco_tema}, com base nos conteúdos e discussões propostos no material."

        return f"Analisar criticamente aspectos relacionados a {foco_tema}, relacionando o tema aos conceitos centrais da aula."

    if objetivos:
        base = objetivos[0].rstrip(" .;:-")
        if len(objetivos) > 1:
            segundo = re.sub(r"^(identificar|analisar|reconhecer|interpretar|comparar|avaliar|explicar|aplicar|justificar)\s+", "", objetivos[1], flags=re.I).rstrip(" .;:-")
            if segundo:
                return f"{base}, {segundo}."
        return base + "."

    if conteudos:
        return f"Compreender e analisar conceitos relacionados a {foco_tema}, articulando os conteúdos trabalhados no material."

    return _aprendizagem_padrao_por_perfil(tema, perfil, base_conceitual)


def _montar_aprendizagem_inteligente(
    habilidade_pdf: str,
    tema: str,
    conceito: str,
    perfil: str,
    objetivos_secao: list[str] | None = None,
    conteudos_secao: list[str] | None = None,
) -> str:
    habilidade_pdf = re.sub(r"\s+", " ", str(habilidade_pdf or "")).strip()

    if habilidade_pdf and not _texto_habilidade_invalido_ou_truncado(habilidade_pdf):
        return _sanitizar_aprendizagem(habilidade_pdf, tema, conceito, perfil=perfil)

    fallback = _sintetizar_objetivos_e_conteudos_para_aprendizagem(
        tema=tema,
        conceito=conceito,
        objetivos=objetivos_secao,
        conteudos=conteudos_secao,
        perfil=perfil,
    )
    return _sanitizar_aprendizagem(fallback, tema, conceito, perfil=perfil)


def _termos_relevantes_tema(tema: str) -> list[str]:
    stopwords = {
        "aula", "tema", "para", "como", "com", "uma", "mais", "sobre", "conteudo",
        "estudantes", "alunos", "professor", "historia", "habilidade", "identificar",
        "explicar", "caracterizar", "analisar", "processo", "formacao",
    }
    termos = []
    for palavra in normalizar_texto_lote(tema).split():
        if len(palavra) > 3 and palavra not in stopwords and palavra not in termos:
            termos.append(palavra)
    return termos


def _contextualizar_item_historia(item: str, tema: str, tipo: str) -> str:
    texto = re.sub(r'^(?:[☑☒☐]|☑|[\u2611\u2612\u2610]|\s|[-*+•]|\[[ xX]\])+\s*', '', str(item or "").strip())
    if not texto:
        return ""
    texto_norm = normalizar_texto_lote(texto)
    tema_limpo = str(tema or "o tema histórico").strip()
    termos_tema = _termos_relevantes_tema(tema_limpo)
    if termos_tema and any(termo in texto_norm for termo in termos_tema):
        return texto

    if tipo == "acessibilidade":
        if any(t in texto_norm for t in ["material", "impresso", "leitura"]):
            return f"{texto.rstrip('.')} sobre {tema_limpo}, com palavras-chave históricas em destaque."
        if any(t in texto_norm for t in ["visual", "imagem", "mapa"]):
            return f"Utilizar imagem, mapa, linha do tempo ou quadro comparativo sobre {tema_limpo} para apoiar a compreensão."
        if any(t in texto_norm for t in ["tempo", "apoio", "individual"]):
            return f"{texto.rstrip('.')} durante o registro em tópicos sobre {tema_limpo}."
        return f"{texto.rstrip('.')} com retomada de conceitos históricos ligados a {tema_limpo}."

    if any(t in texto_norm for t in ["particip", "engaj"]):
        return f"{texto.rstrip('.')} nas discussões sobre {tema_limpo}."
    if any(t in texto_norm for t in ["anot", "caderno", "registro", "escrev"]):
        return f"{texto.rstrip('.')} sobre {tema_limpo}."
    if any(t in texto_norm for t in ["respost", "avali", "confer"]):
        return f"{texto.rstrip('.')} relacionando {tema_limpo} aos conceitos históricos trabalhados."
    return f"{texto.rstrip('.')} sobre {tema_limpo}."


def _contextualizar_itens_historia(itens: list[str], tema: str, tipo: str) -> list[str]:
    contextualizados = [_contextualizar_item_historia(item, tema, tipo) for item in itens or []]
    return [item for item in contextualizados if item]


def _fallback_acompanhamento_tema(tema: str, perfil: str) -> list[str]:
    base = normalizar_texto_lote(tema)
    if perfil == "historia":
        return [
            f"☑ Verificar se os estudantes relacionam {tema} aos sujeitos, conflitos, instituições ou transformações históricas discutidas na aula.",
            "☑ Observar se utilizam evidências do material, como imagem, mapa, trecho ou registro, para justificar respostas históricas.",
            "☑ Conferir se o registro no caderno apresenta síntese com vocabulário histórico e relação entre causa, consequência ou permanência.",
        ]
    if any(termo in base for termo in ["esquistossomose", "platelminto", "nematodeo", "lombriga", "amarelao", "parasita"]):
        return [
            "☑ Verificar se os estudantes identificam agente causador, ciclo de vida, formas de transmissão e principais sintomas da parasitose estudada.",
            "☑ Observar se relacionam saneamento básico, prevenção e promoção da saúde às medidas de controle da doença.",
            "☑ Conferir se os registros utilizam vocabulário científico adequado e organizam relações entre hospedeiro, ambiente e profilaxia.",
        ]
    if _tema_virus_celulas(base):
        return [
            "☑ Verificar se os estudantes comparam vírus e células, identificando capsídeo, material genético, organelas e metabolismo.",
            "☑ Observar se interpretam imagens, esquemas ou tabelas para diferenciar seres vivos, células e vírus.",
            "☑ Conferir se os registros justificam por que os vírus dependem de células para se multiplicar.",
        ]
    if any(termo in base for termo in ["virus", "viral", "virais", "virologia", "vacina", "vacinal"]):
        return [
            "☑ Verificar se os estudantes relacionam vírus, mutações, vacinação e prevenção com base nos exemplos discutidos.",
            "☑ Observar se interpretam imagens, dados ou situações-problema para explicar a importância da cobertura vacinal.",
            "☑ Conferir se os registros usam vocabulário científico adequado e justificam relações entre saúde individual e coletiva.",
        ]
    if any(termo in base for termo in ["hereditariedade", "heredograma", "mendel", "dna", "gene", "genes", "genetica", "biotecnologia", "clonagem", "bioetica", "biosseguranca"]):
        return [
            f"☑ Verificar se os estudantes relacionam {tema} aos conceitos de hereditariedade, variabilidade genética ou biotecnologia trabalhados na aula.",
            "☑ Observar se utilizam evidências, esquemas, cruzamentos ou dados do material para justificar as respostas.",
            "☑ Conferir se os registros apresentam vocabulário científico adequado e conexões coerentes entre conceito, exemplo e conclusão.",
        ]
    if _tema_astronomia_terra_lua(base):
        return [
            f"☑ Verificar se os estudantes relacionam {tema} à observação do céu, aos movimentos dos astros ou às posições relativas discutidas na aula.",
            "☑ Observar se utilizam imagens, modelos, registros ou esquemas para explicar o fenômeno estudado com vocabulário científico adequado.",
            "☑ Conferir se as respostas apresentam relações coerentes entre observação, explicação científica e o foco conceitual trabalhado.",
        ]
    if perfil in {"biologia", "ciencias_ef"}:
        return [
            f"☑ Verificar se os estudantes compreendem os conceitos científicos relacionados a {tema}.",
            "☑ Observar participação, registros, interpretação de imagens ou esquemas e uso de evidências durante a aula.",
            "☑ Conferir se as respostas apresentam vocabulário científico e relações coerentes entre conceito, observação e análise.",
        ]
    return [
        f"☑ Verificar se os estudantes compreendem os conceitos centrais relacionados a {tema}.",
        "☑ Observar a participação, os registros e a forma como justificam respostas durante as atividades propostas.",
        "☑ Conferir se as produções finais retomam o tema da aula com clareza, coerência e autonomia progressiva.",
    ]


def _fallback_acessibilidade_tema(tema: str, perfil: str) -> list[str]:
    base = normalizar_texto_lote(tema)
    if perfil == "historia":
        return [
            f"☑ Realizar leitura guiada do material sobre {tema}, destacando palavras-chave no quadro antes do registro.",
            "☑ Disponibilizar quadro comparativo, linha do tempo ou mapa de relações para apoiar a compreensão do processo histórico.",
            "☑ Permitir resposta oral mediada ou registro em tópicos e frases curtas, retomando conceitos históricos essenciais da aula.",
        ]
    if any(termo in base for termo in ["esquistossomose", "platelminto", "nematodeo", "lombriga", "amarelao", "parasita"]):
        return [
            "☑ Utilizar esquema ampliado do ciclo de vida do parasita, destacando agente causador, hospedeiro, transmissão e prevenção.",
            "☑ Disponibilizar banco de palavras com termos como saneamento, profilaxia, hospedeiro, contaminação e tratamento.",
            "☑ Conduzir leitura guiada das imagens e comandos, permitindo registro por tópicos, setas ou desenho esquemático.",
        ]
    if _tema_virus_celulas(base):
        return [
            "☑ Ampliar esquemas comparativos entre vírus e células, destacando capsídeo, material genético, organelas e metabolismo.",
            "☑ Disponibilizar banco de palavras com termos como vírus, célula, capsídeo, material genético, organela e metabolismo.",
            "☑ Organizar a comparação em tabela ou tópicos, com leitura mediada dos comandos e retomada coletiva das diferenças.",
        ]
    if any(termo in base for termo in ["virus", "viral", "virais", "virologia", "vacina", "vacinal"]):
        return [
            "☑ Apresentar imagens e esquemas simples sobre vírus, mutações e vacinação antes da atividade individual.",
            "☑ Disponibilizar banco de palavras com termos como vírus, vacina, mutação, imunização e cobertura vacinal.",
            "☑ Organizar as respostas em etapas curtas, com leitura mediada dos comandos e síntese coletiva no quadro.",
        ]
    if any(termo in base for termo in ["hereditariedade", "heredograma", "mendel", "dna", "gene", "genes", "genetica", "biotecnologia", "clonagem", "bioetica", "biosseguranca"]):
        return [
            "☑ Disponibilizar esquemas ampliados, quadros de cruzamento ou roteiros visuais para apoiar a leitura dos conceitos genéticos.",
            "☑ Oferecer banco de palavras com termos como DNA, gene, alelo, heredograma, hereditariedade, biotecnologia e evidência.",
            "☑ Permitir registro por desenho, tabela, setas ou frases curtas, com mediação na interpretação dos comandos.",
        ]
    if _tema_astronomia_terra_lua(base):
        return [
            "☑ Utilizar esquema visual com Sol, Terra, Lua, eixo, órbita, fases ou astros observados, conforme o foco da aula, para apoiar a compreensão do fenômeno.",
            "☑ Destacar no quadro palavras-chave e relações espaciais importantes, com retomada oral antes do registro individual.",
            "☑ Permitir registro por desenho identificado, setas, frases curtas ou explicação oral mediada durante a análise do modelo, imagem ou situação observada.",
        ]
    if perfil in {"biologia", "ciencias_ef"}:
        return [
            "☑ Utilizar imagens, esquemas e exemplos do cotidiano para apoiar a compreensão dos conceitos científicos.",
            "☑ Destacar palavras-chave no quadro e orientar registros por tópicos, setas ou frases curtas.",
            "☑ Oferecer mediação individual e retomada coletiva dos comandos antes da atividade principal.",
        ]
    return [
        "☑ Disponibilizar roteiro, palavras-chave ou perguntas orientadoras para apoiar a compreensão da atividade.",
        "☑ Permitir diferentes formas de registro, como tópicos, frases curtas, esquema, desenho ou resposta oral mediada.",
        "☑ Realizar retomadas coletivas dos comandos e oferecer mediação individual conforme as necessidades observadas.",
    ]


def _normalizar_itens_contextuais(
    acompanhamento: list[str],
    acessibilidade: list[str],
    tema: str,
    perfil: str,
) -> tuple[list[str], list[str]]:
    acomp = list(acompanhamento or [])
    acess = list(acessibilidade or [])
    base_tema = normalizar_texto_lote(tema)
    tema_parasitologia = any(
        termo in base_tema
        for termo in ["esquistossomose", "platelminto", "nematodeo", "lombriga", "amarelao", "parasita"]
    )
    termos_parasitologia = ["parasita", "parasit", "saneamento", "profilax", "hospedeiro", "transmissao", "doenca"]
    
    if not acomp or any(_texto_incompativel_com_tema(item, tema) for item in acomp):
        fallback = _fallback_acompanhamento_tema(tema, perfil)
        if fallback:
            acomp = fallback
    if not acess or any(_texto_incompativel_com_tema(item, tema) for item in acess):
        fallback = _fallback_acessibilidade_tema(tema, perfil)
        if fallback:
            acess = fallback

    if perfil == "historia":
        termos_tema = _termos_relevantes_tema(tema)
        texto_acomp_hist = normalizar_texto_lote(" ".join(acomp))
        texto_acess_hist = normalizar_texto_lote(" ".join(acess))
        if termos_tema and not any(termo in texto_acomp_hist for termo in termos_tema):
            acomp = _contextualizar_itens_historia(acomp, tema, "acompanhamento") or _fallback_acompanhamento_tema(tema, perfil)
        if termos_tema and not any(termo in texto_acess_hist for termo in termos_tema):
            acess = _contextualizar_itens_historia(acess, tema, "acessibilidade") or _fallback_acessibilidade_tema(tema, perfil)
            
    if tema_parasitologia:
        texto_acomp = normalizar_texto_lote(" ".join(acomp))
        texto_acess = normalizar_texto_lote(" ".join(acess))
        if texto_acomp and not any(termo in texto_acomp for termo in termos_parasitologia):
            fallback = _fallback_acompanhamento_tema(tema, perfil)
            if fallback:
                acomp = fallback
        if texto_acess and not any(termo in texto_acess for termo in termos_parasitologia):
            fallback = _fallback_acessibilidade_tema(tema, perfil)
            if fallback:
                acess = fallback

    acomp = normalizar_lista_exatamente_tres(acomp, _fallback_acompanhamento_tema(tema, perfil))
    acess = normalizar_lista_exatamente_tres(acess, _fallback_acessibilidade_tema(tema, perfil))

    return acomp, acess


def _foco_historia_para_metodologia(tema: str, texto: str = "") -> dict[str, str]:
    base = normalizar_texto_lote(f"{tema} {texto}")
    if any(t in base for t in ["guerras medicas", "guerra medica", "persas", "persa", "hoplita", "hoplitas"]):
        return {
            "foco": "Guerras Médicas entre persas e gregos",
            "detalhe_1": "as causas do conflito",
            "detalhe_2": "a atuação dos hoplitas e das pólis gregas",
            "pergunta": "por que o conflito entre persas e gregos marcou a organização das pólis",
        }
    if any(t in base for t in ["alexandr", "helenic", "helenica", "macedonia", "macedonia"]):
        return {
            "foco": "Império Alexandrino e difusão da cultura helênica",
            "detalhe_1": "a expansão macedônica",
            "detalhe_2": "a circulação de elementos culturais helênicos",
            "pergunta": "como a expansão de Alexandre favoreceu trocas culturais",
        }
    if any(t in base for t in ["monarquia romana", "patric", "plebe", "reis", "instituic", "roma antiga"]):
        return {
            "foco": "monarquia romana",
            "detalhe_1": "a atuação de patrícios, reis e demais grupos sociais",
            "detalhe_2": "as instituições políticas iniciais de Roma",
            "pergunta": "como a monarquia organizava poder e sociedade em Roma",
        }
    if any(t in base for t in ["polis", "polís", "atenas", "esparta", "cidade estado", "cidades estado"]):
        return {
            "foco": "pólis gregas e cidades-estado",
            "detalhe_1": "as características de Atenas e Esparta",
            "detalhe_2": "as formas de participação política e organização social",
            "pergunta": "como as pólis gregas organizavam a vida política e social",
        }
    foco = str(tema or "o tema histórico da aula").strip()
    return {
        "foco": foco,
        "detalhe_1": "os sujeitos históricos envolvidos",
        "detalhe_2": "as mudanças, permanências e relações de poder",
        "pergunta": f"como {foco} se relaciona ao contexto histórico estudado",
    }


def _etapa_historia_canonica(titulo: str) -> str:
    base = normalizar_texto_lote(titulo)
    if any(t in base for t in ["para comecar", "relembre", "abertura", "inicio"]):
        return "Para começar"
    if any(t in base for t in ["foco", "conteudo", "contextualizacao", "explicacao"]):
        return "Foco no conteúdo"
    if any(t in base for t in ["pause", "responda", "checagem"]):
        return "Pause e responda"
    if any(t in base for t in ["pratica", "atividade", "de olho no modelo", "modelo", "analise"]):
        return "Na prática"
    if any(t in base for t in ["encerramento", "fechamento", "sintese", "conclusao"]):
        return "Encerramento"
    return ""


def _etapas_historia_fallback(tema: str, texto: str, indice_aula: int, total_aulas: int) -> dict[str, str]:
    foco = _foco_historia_para_metodologia(tema, texto)
    return {
        "Para começar": (
            f"Inicie a aula retomando {foco['foco']} com uma pergunta disparadora sobre {foco['pergunta']}. "
            "Peça que os estudantes conversem em duplas e registrem no caderno uma hipótese inicial."
        ),
        "Foco no conteúdo": (
            f"Conduza a explicação sobre {foco['foco']}, relacionando {foco['detalhe_1']} e {foco['detalhe_2']}. "
            "Questione a turma durante a leitura de imagens, mapas ou trechos do material para que anotem conceitos-chave."
        ),
        "Pause e responda": (
            f"Faça uma pausa de checagem e solicite que as duplas respondam no caderno uma pergunta orientadora sobre {foco['detalhe_1']}. "
            "Socialize duas ou três respostas para ajustar dúvidas antes de seguir."
        ),
        "Na prática": (
            f"Oriente os estudantes a analisar a fonte, imagem, mapa ou atividade do material, comparando {foco['detalhe_1']} e {foco['detalhe_2']}. "
            "Acompanhe os grupos na seleção de evidências históricas e no registro das conclusões."
        ),
        "Encerramento": (
            f"Conduza a síntese final com a turma, retomando {foco['foco']} e pedindo que os estudantes escrevam uma conclusão curta. "
            "Finalize destacando uma relação de causa, consequência ou permanência observada na aula."
        ),
    }


def _completar_metodologia_historia(
    metodologia,
    texto: str,
    tema: str,
    indice_aula: int = 0,
    total_aulas: int = 1,
):
    etapas = []
    presentes = set()
    for item in metodologia or []:
        if not isinstance(item, dict):
            continue
        texto_item = re.sub(r"\s+", " ", str(item.get("texto") or "")).strip()
        if not texto_item:
            continue
        etapa = dict(item)
        canonica = _etapa_historia_canonica(etapa.get("titulo", ""))
        if canonica:
            presentes.add(canonica)
        etapas.append(etapa)

    if not etapas:
        presentes = set()

    fallbacks = _etapas_historia_fallback(tema, texto, indice_aula, total_aulas)
    ordem = ["Para começar", "Foco no conteúdo", "Pause e responda", "Na prática", "Encerramento"]
    alvo_minimo = 4 if tema else 3
    for titulo in ordem:
        if len(etapas) >= alvo_minimo and len(presentes) >= alvo_minimo:
            break
        if titulo in presentes:
            continue
        etapas.append({"titulo": titulo, "texto": fallbacks[titulo]})
        presentes.add(titulo)

    return _reduzir_frases_repetitivas_metodologia(
        etapas,
        tema=tema,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
    )


def _aprimorar_historia_pos_processamento(
    metodologia,
    acompanhamento,
    acessibilidade,
    texto: str,
    tema: str,
    indice_aula: int = 0,
    total_aulas: int = 1,
):
    metodologia = _completar_metodologia_historia(
        metodologia,
        texto=texto,
        tema=tema,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
    )
    acompanhamento, acessibilidade = _normalizar_itens_contextuais(
        acompanhamento,
        acessibilidade,
        tema,
        "historia",
    )
    return metodologia, acompanhamento, acessibilidade


def _remover_turma_metodologia(texto: str) -> str:
    return _PADRAO_TURMA_METODOLOGIA.sub(lambda m: m.group(1), str(texto or ""))


def _indice_variacao(partes: list[str], total: int) -> int:
    if total <= 1:
        return 0
    chave = "|".join(str(parte or "") for parte in partes)
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    return int(digest, 16) % total


def _escolher_variacao(opcoes: list[str], partes: list[str]) -> str:
    return opcoes[_indice_variacao(partes, len(opcoes))]


_FRASES_REPETITIVAS_METODOLOGIA = [
    (
        r"Retomar registros anteriores quando necess[aá]rio, ajudando a turma a perceber a continuidade do estudo\.?",
        [
            "Revisitar anotações já produzidas e relacioná-las ao foco do dia, ajudando a turma a perceber a continuidade do estudo.",
            "Comparar os registros da aula anterior com o novo conteúdo, destacando avanços e dúvidas que ainda precisam de retomada.",
            "Usar as anotações anteriores como ponto de partida para que a turma acompanhe a continuidade da sequência.",
            "Retomar evidências registradas anteriormente e conectá-las às novas questões propostas na aula.",
        ],
    ),
    (
        r"Conduzir leitura orientada do material, com pausas para destacar informa[cç][oõ]es importantes\.?",
        [
            "Realizar leitura guiada do material, pausando para localizar conceitos, evidências e dúvidas da turma.",
            "Mediar a leitura do trecho selecionado, destacando palavras-chave e relações históricas importantes.",
            "Orientar a leitura com pausas breves para que os estudantes anotem informações centrais no caderno.",
            "Organizar leitura comentada do material, alternando explicação, perguntas e registros rápidos.",
        ],
    ),
    (
        r"Solicitar que os estudantes comparem as respostas de hoje com as estrategias usadas anteriormente, identificando avancos, ajustes e duvidas persistentes\.?",
        [
            "Pedir que os estudantes confrontem as respostas atuais com registros anteriores, identificando avanços, ajustes e dúvidas persistentes.",
            "Orientar a turma a comparar as respostas do dia com estratégias já usadas, registrando o que mudou na compreensão.",
            "Propor que as duplas revisem respostas anteriores e indiquem no caderno avanços, correções e pontos que ainda exigem retomada.",
            "Acompanhar a comparação entre registros da sequência, ajudando os estudantes a reconhecer progressos e dúvidas.",
        ],
    ),
    (
        r"Registrar uma sintese parcial e uma pergunta para orientar a proxima aula da sequencia\.?",
        [
            "Organizar uma síntese breve e uma pergunta orientadora para abrir a próxima aula da sequência.",
            "Fechar com registro curto das ideias centrais e uma questão que ajude a continuidade do estudo.",
            "Sistematizar uma ideia-chave no caderno e deixar uma pergunta para retomada no próximo encontro.",
            "Concluir com síntese parcial, destacando uma dúvida ou relação histórica para a próxima aula.",
        ],
    ),
]


def _reduzir_frases_repetitivas_metodologia(
    metodologia,
    tema: str,
    indice_aula: int = 0,
    total_aulas: int = 1,
):
    ajustada = []
    for idx, item in enumerate(metodologia or []):
        if not isinstance(item, dict):
            ajustada.append(item)
            continue
        texto = str(item.get("texto", "") or "")
        titulo = str(item.get("titulo", "") or "")
        for padrao, opcoes in _FRASES_REPETITIVAS_METODOLOGIA:
            if re.search(padrao, texto, flags=re.I):
                escolha = _escolher_variacao(
                    opcoes,
                    [tema, titulo, str(indice_aula), str(total_aulas), str(idx), padrao],
                )
                texto = re.sub(padrao, escolha, texto, count=1, flags=re.I)
        novo_item = dict(item)
        novo_item["texto"] = texto
        ajustada.append(novo_item)
    return ajustada


_VARIACOES_INICIO_METODOLOGIA = [
    (
        r"^Retomar conhecimentos previos",
        [
            "Retomar conhecimentos previos",
            "Mobilizar conhecimentos previos",
            "Ativar conhecimentos previos",
            "Iniciar pela retomada dos conhecimentos previos",
        ],
    ),
    (
        r"^Retomar conhecimentos prévios",
        [
            "Retomar conhecimentos prévios",
            "Mobilizar conhecimentos prévios",
            "Ativar conhecimentos prévios",
            "Iniciar pela retomada dos conhecimentos prévios",
        ],
    ),
    (
        r"^Promover discussao",
        [
            "Promover discussao",
            "Abrir dialogo",
            "Conduzir conversa",
            "Organizar troca de ideias",
        ],
    ),
    (
        r"^Promover discussão",
        [
            "Promover discussão",
            "Abrir diálogo",
            "Conduzir conversa",
            "Organizar troca de ideias",
        ],
    ),
    (
        r"^Apresentar",
        [
            "Apresentar",
            "Introduzir",
            "Explorar",
            "Contextualizar",
        ],
    ),
    (
        r"^Realizar leitura guiada",
        [
            "Realizar leitura guiada",
            "Conduzir leitura guiada",
            "Mediar a leitura guiada",
            "Organizar leitura orientada",
        ],
    ),
    (
        r"^Conduzir leitura",
        [
            "Conduzir leitura",
            "Mediar leitura",
            "Organizar leitura",
            "Orientar leitura",
        ],
    ),
    (
        r"^Analisar",
        [
            "Analisar",
            "Explorar",
            "Examinar",
            "Investigar com a turma",
        ],
    ),
    (
        r"^Explicar",
        [
            "Explicar",
            "Desenvolver a explicacao sobre",
            "Construir a explicacao de",
            "Apresentar de forma progressiva",
        ],
    ),
    (
        r"^Orientar",
        [
            "Orientar",
            "Acompanhar",
            "Conduzir",
            "Mediar",
        ],
    ),
    (
        r"^Socializar",
        [
            "Socializar",
            "Compartilhar coletivamente",
            "Promover a socializacao de",
            "Retomar com a turma",
        ],
    ),
    (
        r"^Sistematizar",
        [
            "Sistematizar",
            "Organizar",
            "Registrar de forma coletiva",
            "Consolidar",
        ],
    ),
    (
        r"^Finalizar com",
        [
            "Finalizar com",
            "Concluir com",
            "Encaminhar o fechamento com",
            "Organizar uma sintese final com",
        ],
    ),
    (
        r"^Encerrar com",
        [
            "Encerrar com",
            "Fechar a aula com",
            "Concluir com",
            "Promover o encerramento com",
        ],
    ),
    (
        r"^Retomar a importancia",
        [
            "Retomar a importancia",
            "Destacar, no fechamento, a importancia",
            "Conduzir uma sintese sobre a importancia",
            "Fechar a aula reforcando a importancia",
        ],
    ),
    (
        r"^Retomar a importância",
        [
            "Retomar a importância",
            "Destacar, no fechamento, a importância",
            "Conduzir uma síntese sobre a importância",
            "Fechar a aula reforçando a importância",
        ],
    ),
]


def _variar_inicio_etapa(texto: str, partes_seed: list[str]) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return ""

    for padrao, opcoes in _VARIACOES_INICIO_METODOLOGIA:
        if re.search(padrao, texto, flags=re.IGNORECASE):
            escolha = _escolher_variacao(opcoes, partes_seed + [padrao, texto[:160]])
            return re.sub(padrao, escolha, texto, count=1, flags=re.IGNORECASE)
    return texto


def _colocar_aspas_no_titulo(texto: str, titulo: str) -> str:
    texto_final = str(texto or "")
    titulo = str(titulo or "").strip()
    if len(titulo) < 4:
        return texto_final

    padrao = re.compile(rf'(?<!["“]){re.escape(titulo)}(?!["”])', flags=re.I)
    return padrao.sub(lambda match: f'"{match.group(0)}"', texto_final)


def _variar_linguagem_metodologia(metodologia, disciplina: str, turma: str, tema: str):
    """Aplica variacao linguistica controlada sem alterar a estrutura pedagogica."""
    variadas = []
    for idx, item in enumerate(metodologia or []):
        if not isinstance(item, dict):
            variadas.append(item)
            continue

        titulo = str(item.get("titulo", "")).strip()
        texto = str(item.get("texto", "")).strip()
        texto_variado = _variar_inicio_etapa(
            texto,
            [disciplina, turma, tema, titulo, str(idx)],
        )
        texto_variado = _remover_turma_metodologia(texto_variado)
        texto_variado = _colocar_aspas_no_titulo(texto_variado, tema)
        texto_variado = ajustar_verbos_para_infinitivo(texto_variado)
        novo_item = dict(item)
        novo_item["texto"] = texto_variado
        variadas.append(novo_item)
    return variadas


def _acompanhamento_por_contexto(perfil: str, tipo: str, tema: str) -> list[str]:
    base = [
        f"Verificar se os estudantes compreendem os conceitos centrais relacionados a {tema} durante as discussões e atividades propostas.",
        "Observar a participação, os registros produzidos e a forma como os estudantes justificam suas respostas ao longo da aula.",
        "Acompanhar se os estudantes conseguem aplicar os conhecimentos trabalhados com autonomia progressiva nas atividades orientadas.",
    ]

    if perfil == "matematica":
        return [
            f"Verificar se os estudantes identificam corretamente os elementos matemáticos envolvidos em {tema} e organizam estratégias coerentes de resolução.",
            "Observar se os estudantes utilizam adequadamente procedimentos, propriedades e registros matemáticos durante as resoluções.",
            "Acompanhar se os estudantes interpretam os resultados encontrados e conseguem justificar os caminhos escolhidos ao longo das atividades.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return [
            f"Verificar se os estudantes compreendem as ideias centrais de {tema} e identificam os elementos textuais trabalhados na aula.",
            "Observar a participação nas leituras, discussões e registros, considerando a capacidade de argumentar, interpretar e revisar as respostas.",
            "Acompanhar se os estudantes aplicam as estratégias de leitura, análise ou produção textual com progressiva autonomia.",
        ]

    if perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        return [
            f"Verificar se os estudantes relacionam {tema} aos conceitos científicos trabalhados e utilizam evidências para sustentar suas respostas.",
            "Observar a participação nas investigações, registros e socializações, considerando a clareza das hipóteses e explicações apresentadas.",
            "Acompanhar se os estudantes conseguem interpretar fenômenos, dados ou experimentos com base nos conceitos desenvolvidos na aula.",
        ]

    return base


def _acessibilidade_por_contexto(perfil: str, tipo: str, tema: str) -> list[str]:
    base = [
        "Disponibilizar mediação individualizada durante as atividades, adequando explicações, tempo e forma de resposta conforme as necessidades da turma.",
        "Utilizar apoio visual, retomadas coletivas e registros orientados para favorecer a compreensão dos conceitos trabalhados.",
        "Organizar intervenções com exemplos comentados e acompanhamento próximo para apoiar estudantes com dificuldades de leitura, interpretação ou organização das tarefas.",
    ]

    if perfil == "matematica":
        return [
            "Disponibilizar resolução comentada e exemplos passo a passo para favorecer a compreensão dos procedimentos matemáticos.",
            "Utilizar apoio visual e retomadas coletivas para auxiliar estudantes com dificuldades na interpretação dos problemas.",
            "Realizar acompanhamento individualizado durante as atividades, auxiliando na organização dos cálculos e identificação das operações necessárias.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return [
            "Oferecer apoio à leitura com destaque para palavras-chave, trechos importantes e orientações passo a passo para a realização das atividades.",
            "Utilizar mediação oral, retomadas coletivas e exemplos comentados para favorecer a compreensão dos textos e comandos.",
            "Adaptar tempo, forma de registro e acompanhamento das produções conforme as necessidades observadas na turma.",
        ]

    return base


def _acompanhamento_dinamico_contexto(
    perfil: str,
    tipo: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str,
) -> list[str]:
    return gerar_acompanhamento_dinamico(
        tema=tema,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
        perfil=perfil,
        tipo=tipo,
    )


def _acessibilidade_dinamica_contexto(
    perfil: str,
    tipo: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str,
) -> list[str]:
    return gerar_acessibilidade_dinamica(
        tema=tema,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
        perfil=perfil,
        tipo=tipo,
    )


from core.inteligencia_local import SistemaGeracaoMetodologica
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.extrator_pdf import ExtratorPDF
from core.lib.metodologia import MotorMetodologico
from core.validador_plano import validar_aula_final

gerador_inteligente = SistemaGeracaoMetodologica()
_extrator_lib = ExtratorPDF()
_motor_metodologico = MotorMetodologico()


def _perfil_gerador_colunas_habilitado(perfil: str) -> bool:
    return perfil not in {
        "projeto_de_vida",
        "lideranca_oratoria",
        "leitura_redacao",
        "orientacao_estudos",
        "ciencias_ef",
    }


def _tentar_gerador_colunas_pedagogicas(
    texto: str,
    titulo_aula: str,
    disciplina: str,
    turma: str,
    tema: str,
    perfil: str,
    contexto_metodologico: str,
    indice_aula: int,
    total_aulas: int,
    modalidade_eja_ativa: bool,
) -> dict | None:
    if not _perfil_gerador_colunas_habilitado(perfil):
        return None

    try:
        colunas = montar_colunas_pedagogicas(texto_pdf=texto, titulo_aula=titulo_aula, perfil=perfil)
        metodologia = list(colunas.get("metodologia_blocos") or [])
        acompanhamento = list(colunas.get("acompanhamento_aprendizagem") or [])
        acessibilidade = list(colunas.get("acessibilidade") or [])
        if not metodologia or len(acompanhamento) < 2 or len(acessibilidade) < 2:
            return None

        metodologia = _ajustar_metodologia_por_sequencia(
            metodologia,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            tema=tema,
        )
        metodologia, _ = revisar_metodologia(
            metodologia,
            perfil=perfil,
            tema=tema,
            contexto=contexto_metodologico,
        )
        metodologia = naturalizar_metodologia_professor(metodologia, perfil=perfil)
        if modalidade_eja_ativa:
            tecnicas_pdf = _detectar_tecnicas_lemov(texto, tema)
            metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_pdf, _garantir_tecnicas_lemov_na_metodologia)

        return {
            "metodologia": metodologia,
            "acompanhamento": acompanhamento,
            "acessibilidade": acessibilidade,
            "pistas_pdf": colunas.get("pistas"),
        }
    except Exception:
        return None


def _resolver_contexto_orientacao_estudos(
    caminho_pdf: str,
    texto: str,
    tema: str,
    material_digital: str,
    indice_aula: int,
) -> tuple[str, str, str]:
    etapas_orientacao = _extrair_etapas_orientacao_estudos(texto)
    if not etapas_orientacao:
        return texto, tema, material_digital

    idx_etapa = None
    base_nome = Path(caminho_pdf).name.lower()
    match_etapa = re.search(r"etapa[_\s-]*(final|\d+)", base_nome)
    if match_etapa:
        rotulo_arq = match_etapa.group(1)
        if rotulo_arq == "final":
            for indice, etapa in enumerate(etapas_orientacao):
                if "final" in etapa["titulo"].lower():
                    idx_etapa = indice
                    break
        else:
            try:
                num_etapa = int(rotulo_arq)
                for indice, etapa in enumerate(etapas_orientacao):
                    if str(num_etapa) in etapa["titulo"].lower():
                        idx_etapa = indice
                        break
            except ValueError:
                pass

    if idx_etapa is None:
        idx_etapa = min(max(indice_aula, 0), len(etapas_orientacao) - 1)

    etapa_atual = etapas_orientacao[idx_etapa]
    titulo_base = material_digital or tema or _titulo_catalogado_orientacao_estudos(caminho_pdf, texto)
    texto_etapa = etapa_atual["texto"]
    rotulo_etapa = etapa_atual["titulo"].upper()
    tema_etapa = f"{titulo_base} - {rotulo_etapa}" if titulo_base else rotulo_etapa
    material_etapa = rotulo_etapa.title()
    return texto_etapa, tema_etapa, material_etapa


def _montar_resultado_cdp_contextual(
    texto: str,
    tema: str,
    disciplina_base: str,
    numero_aula: str,
    indice_aula: int,
    perfil: str,
    tipo: str,
    extracao_pdf: dict,
    caminho_pdf: str = "",
) -> dict:
    referencia_docx = referencia_cdp_contextual_por_pdf(caminho_pdf, numero_aula, tema=tema)
    if referencia_docx:
        titulo_referencia = str(referencia_docx.get("titulo") or "").strip()
        numero_referencia = str(referencia_docx.get("numero") or "").strip()
        if titulo_referencia:
            tema = titulo_referencia
        if numero_referencia:
            numero_aula = numero_referencia

    conceito_cdp = extracao_pdf.get("conceito_extraido", tema)
    habilidade_cdp = extracao_pdf.get("habilidade", "")
    if habilidade_cdp and len(habilidade_cdp) > 15:
        aprendizagem_cdp = habilidade_cdp
    else:
        foco_cdp = _foco_limpo_aprendizagem(
            limpar_tema_cdp_contextual(tema, disciplina_base),
            limpar_tema_cdp_contextual(conceito_cdp, disciplina_base),
        )
        aprendizagem_cdp = f"Compreender e aplicar conceitos relacionados a {foco_cdp}, realizando registros e resolu??es com apoio do professor."

    metodologia_cdp = metodologia_cdp_contextual(
        perfil,
        tipo,
        tema,
        conceito_cdp,
        indice_aula,
        texto_pdf=texto,
        extracao_pdf=extracao_pdf,
        disciplina_base=disciplina_base,
    )
    acompanhamento_cdp = acompanhamento_cdp_contextual(perfil, tema, conceito_cdp, indice_aula)
    acessibilidade_cdp = acessibilidade_cdp_contextual(perfil, tema, conceito_cdp, indice_aula)

    if referencia_docx:
        metodologia_cdp = naturalizar_metodologia_professor(referencia_docx.get("metodologia") or [], perfil=perfil)
        acompanhamento_cdp = list(referencia_docx.get("acompanhamento") or [])[:3]
        acessibilidade_cdp = list(referencia_docx.get("acessibilidade") or [])[:3]

    from core.lib.higienizador_pedagogico import higienizar_plano, detectar_recursos_reais

    recursos_reais = detectar_recursos_reais(texto)
    metodologia_cdp, acompanhamento_cdp, acessibilidade_cdp = higienizar_plano(
        metodologia_cdp,
        acompanhamento_cdp,
        acessibilidade_cdp,
        perfil,
        disciplina_base,
        tema,
        recursos_reais,
    )
    if referencia_docx:
        acompanhamento_cdp, acessibilidade_cdp = (
            _sobrescrever_listas_pedagogicas_com_referencia(
                referencia_docx,
                acompanhamento_cdp,
                acessibilidade_cdp,
            )
        )

    from core.qualidade_metodologica import sanitizar_texto_cdp_estrito
    return {
        "disciplina": disciplina_base,
        "tema": tema,
        "material": formatar_material_cdp_contextual(tema, disciplina_base),
        "numero_aula": numero_aula,
        "aprendizagem": sanitizar_texto_cdp_estrito(_sanitizar_aprendizagem(aprendizagem_cdp, tema, conceito_cdp, perfil=perfil)),
        "metodologia": metodologia_cdp,
        "acompanhamento": acompanhamento_cdp,
        "acessibilidade": acessibilidade_cdp,
        "origem_metodologia": "docx_referencia_cdp_contextual" if referencia_docx else "motor_local_cdp_contextual",
        "fonte_referencia_metodologia": (referencia_docx or {}).get("fonte", ""),
        "ia_usada": False,
        "ia_provedor": "",
        "ia_erro": "",
    }


def _limpar_repeticao_tecnicas_lemov_ia(metodologia: list[dict]) -> list[dict]:
    import re
    if not metodologia:
        return metodologia

    artigos = {
        "virem e conversem": "o",
        "todo mundo escreve": "o",
        "com suas palavras": "o",
        "hora da leitura": "a",
        "de olho no modelo": "o",
        "pause e responda": "o",
        "um passo de cada vez": "o",
        "pausa produtiva": "a"
    }

    novas_etapas = []
    for item in metodologia:
        if not isinstance(item, dict) or "texto" not in item:
            novas_etapas.append(item)
            continue

        texto = item["texto"]
        for nome_base, artigo in artigos.items():
            pattern = re.compile(
                r"\b(a|da|pela)?\s*t[eé]cnica\s+(?:de\s+)?(?:[\"“'”])?(" + re.escape(nome_base) + r")\b(?:[\"“'”])?",
                re.IGNORECASE
            )
            def replace_func(match):
                art_ant = match.group(1)
                nome_match = match.group(2)
                if art_ant:
                    art_ant_lower = art_ant.lower()
                    if art_ant_lower == "a":
                        art_novo = artigo
                    elif art_ant_lower == "da":
                        art_novo = "do" if artigo == "o" else "da"
                    elif art_ant_lower == "pela":
                        art_novo = "pelo" if artigo == "o" else "pela"
                    else:
                        art_novo = art_ant
                    if art_ant[0].isupper():
                        art_novo = art_novo.capitalize()
                    return f"{art_novo} {nome_match}"
                else:
                    return nome_match
            texto = pattern.sub(replace_func, texto)

        texto = re.sub(r"\s+", " ", texto).strip()
        novo_item = dict(item)
        novo_item["texto"] = texto
        novas_etapas.append(novo_item)

    return novas_etapas


def _dependencias_resultados_aula() -> DependenciasResultadosAula:
    from core.lib.higienizador_pedagogico import detectar_recursos_reais, higienizar_plano

    return DependenciasResultadosAula(
        referencia_docx_por_perfil_fn=_referencia_docx_por_perfil,
        habilidade_referencia_docx_fn=_habilidade_referencia_docx,
        origem_metodologia_por_referencia_fn=_origem_metodologia_por_referencia,
        deve_aplicar_referencia_docx_no_resultado_ia_fn=_deve_aplicar_referencia_docx_no_resultado_ia,
        sobrescrever_listas_pedagogicas_com_referencia_fn=_sobrescrever_listas_pedagogicas_com_referencia,
        extracao_pdf_fn=_extrator_lib.extrair,
        detectar_tipo_aula_fn=_detectar_tipo_aula,
        resolver_habilidade_portugues_fn=_resolver_habilidade_portugues,
        montar_aprendizagem_inteligente_fn=_montar_aprendizagem_inteligente,
        tentar_gerador_colunas_pedagogicas_fn=_tentar_gerador_colunas_pedagogicas,
        metodologia_leitura_redacao_modelo_fn=_metodologia_leitura_redacao_modelo,
        detectar_tecnicas_lemov_fn=_detectar_tecnicas_lemov,
        garantir_tecnicas_lemov_na_metodologia_fn=_garantir_tecnicas_lemov_na_metodologia,
        variar_linguagem_metodologia_fn=_variar_linguagem_metodologia,
        ajustar_metodologia_por_sequencia_fn=_ajustar_metodologia_por_sequencia,
        revisar_metodologia_fn=revisar_metodologia,
        naturalizar_metodologia_professor_fn=naturalizar_metodologia_professor,
        adaptar_metodologia_eja_fn=_adaptar_metodologia_eja,
        texto_metodologia_fn=_texto_metodologia,
        gerar_acompanhamento_aprimorado_fn=gerar_acompanhamento_aprimorado,
        gerar_acessibilidade_aprimorada_fn=gerar_acessibilidade_aprimorada,
        normalizar_itens_contextuais_fn=_normalizar_itens_contextuais,
        montar_etapas_metodologia_fn=_montar_etapas_metodologia,
        aprimorar_historia_pos_processamento_fn=_aprimorar_historia_pos_processamento,
        detectar_recursos_reais_fn=detectar_recursos_reais,
        higienizar_plano_fn=higienizar_plano,
        validar_aula_final_fn=validar_aula_final,
    )


def _montar_resultado_aula_ia(
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    turma: str,
    provedor_ia: str,
    perfil: str,
    contexto_metodologico: str,
    indice_aula: int,
    total_aulas: int,
    modalidade_eja_ativa: bool,
    plano_ia: dict,
    metodologia_fixa_pdf: list[dict],
    aprendizagem_pv: str,
    objetivos_orientacao: list[str],
    aprendizagem_orientacao: str,
    caminho_pdf: str = "",
    bimestre: str = "",
    rascunho_base: dict | None = None,
) -> dict:
    return _montar_resultado_aula_ia_core(
        texto=texto,
        tema=tema,
        material_digital=material_digital,
        numero_aula=numero_aula,
        disciplina_base=disciplina_base,
        turma=turma,
        provedor_ia=provedor_ia,
        perfil=perfil,
        contexto_metodologico=contexto_metodologico,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        modalidade_eja_ativa=modalidade_eja_ativa,
        plano_ia=plano_ia,
        metodologia_fixa_pdf=metodologia_fixa_pdf,
        aprendizagem_pv=aprendizagem_pv,
        objetivos_orientacao=objetivos_orientacao,
        aprendizagem_orientacao=aprendizagem_orientacao,
        dependencias=_dependencias_resultados_aula(),
        caminho_pdf=caminho_pdf,
        bimestre=bimestre,
        rascunho_base=rascunho_base,
    )


def _montar_resultado_aula_local(
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    turma: str,
    provedor_ia: str,
    perfil: str,
    contexto_metodologico: str,
    indice_aula: int,
    total_aulas: int,
    modalidade_eja_ativa: bool,
    metodologia_fixa_pdf: list[dict],
    aprendizagem_pv: str,
    objetivos_orientacao: list[str],
    aprendizagem_orientacao: str,
    usar_ia: bool,
    ia_erro: str,
    contexto_geracao: dict | None = None,
    caminho_pdf: str = "",
    bimestre: str = "",
) -> dict:
    return _montar_resultado_aula_local_core(
        texto=texto,
        tema=tema,
        material_digital=material_digital,
        numero_aula=numero_aula,
        disciplina_base=disciplina_base,
        turma=turma,
        provedor_ia=provedor_ia,
        perfil=perfil,
        contexto_metodologico=contexto_metodologico,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        modalidade_eja_ativa=modalidade_eja_ativa,
        metodologia_fixa_pdf=metodologia_fixa_pdf,
        aprendizagem_pv=aprendizagem_pv,
        objetivos_orientacao=objetivos_orientacao,
        aprendizagem_orientacao=aprendizagem_orientacao,
        usar_ia=usar_ia,
        ia_erro=ia_erro,
        dependencias=_dependencias_resultados_aula(),
        contexto_geracao=contexto_geracao,
        caminho_pdf=caminho_pdf,
        bimestre=bimestre,
    )


def _preparar_contexto_aula_pdf(
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    bimestre: str,
    indice_aula: int,
    modalidade_eja: bool,
    caminho_pptx_correspondente: str | None = None,
) -> dict:
    from core.disciplinas import eh_cdp
    from core.lib.aprofundamento import obter_dados_aprofundamento

    dependencias = DependenciasContextoAulaPDF(
        logger=logger,
        extrair_texto_pdf_fn=_extrair_texto_pdf,
        tema_por_texto_fn=_tema_por_texto,
        material_digital_por_texto_fn=_material_digital_por_texto,
        rotulo_aula_material_fn=_rotulo_aula_material,
        eh_cenario_piloto_pptx_fn=eh_cenario_piloto_pptx,
        encontrar_pptx_correspondente_fn=encontrar_pptx_correspondente,
        extrair_estrutura_pptx_fn=extrair_estrutura_pptx,
        estrutura_pptx_para_dados_aula_fn=estrutura_pptx_para_dados_aula,
        eh_cdp_contextual_disciplina_fn=eh_cdp_contextual_disciplina,
        disciplina_base_cdp_por_cadastro_fn=_disciplina_base_cdp_por_cadastro,
        disciplina_base_cdp_contextual_fn=disciplina_base_cdp_contextual,
        perfil_disciplina_fn=perfil_disciplina,
        obter_dados_aprofundamento_fn=obter_dados_aprofundamento,
        resolver_contexto_orientacao_estudos_fn=_resolver_contexto_orientacao_estudos,
        buscar_objetivos_orientacao_estudos_fn=buscar_objetivos_orientacao_estudos,
        formatar_objetivos_orientacao_estudos_fn=formatar_objetivos_orientacao_estudos,
        extracao_pdf_fn=_extrator_lib.extrair,
        detectar_tipo_aula_fn=_detectar_tipo_aula,
        metodologia_fixa_pdf_especial_fn=_metodologia_fixa_pdf_especial,
        metodologia_por_blocos_estruturados_fn=_metodologia_por_blocos_estruturados,
        perfil_suporta_eja_fn=_perfil_suporta_eja,
        eh_cdp_fn=eh_cdp,
        detectar_contexto_metodologico_fn=detectar_contexto_metodologico,
        buscar_item_projeto_vida_fn=buscar_item_projeto_vida,
        montar_aprendizagem_projeto_vida_fn=montar_aprendizagem_projeto_vida,
        referencia_docx_por_perfil_fn=_referencia_docx_por_perfil,
        habilidade_referencia_docx_fn=_habilidade_referencia_docx,
        material_aula_com_titulo_fn=_material_aula_com_titulo,
        titulo_escopo_projeto_vida_confiavel_fn=_titulo_escopo_projeto_vida_confiavel,
    )
    return preparar_contexto_aula_pdf(
        caminho_pdf=caminho_pdf,
        disciplina=disciplina,
        turma=turma,
        bimestre=bimestre,
        indice_aula=indice_aula,
        modalidade_eja=modalidade_eja,
        dependencias=dependencias,
        caminho_pptx_correspondente=caminho_pptx_correspondente,
    )
def _aula_por_pdf(
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    bimestre: str,
    usar_ia: bool,
    provedor_ia: str,
    modelo_ia: str = "",
    indice_aula: int = 0,
    total_aulas: int = 1,
    modalidade_eja: bool = False,
    professor: str = "",
    dividir_aula_atual: bool = False,
) -> dict:
    from core.variacao_metodologica import (
        obter_professor_id_por_nome,
        selecionar_perfil_metodologico,
        selecionar_proximo_perfil,
        montar_fingerprint_contexto,
        detectar_similaridade_excessiva,
    )

    hash_atual = ""
    hash_fonte_extracao_esperada = ""
    caminho_fonte_extracao_esperada = caminho_pdf
    caminho_pptx_correspondente = None
    if caminho_pdf:
        try:
            from core.revisao_final import calcular_sha256
            hash_atual = calcular_sha256(caminho_pdf)
            caminho_pptx_correspondente = encontrar_pptx_correspondente(caminho_pdf, disciplina, turma)
            if caminho_pptx_correspondente:
                caminho_fonte_extracao_esperada = caminho_pptx_correspondente
                hash_fonte_extracao_esperada = calcular_sha256(caminho_pptx_correspondente)
        except Exception:
            pass

    prof_id = obter_professor_id_por_nome(professor)
    perfil_metodologico = selecionar_perfil_metodologico(professor, turma, disciplina, bimestre)
    tipo_duracao = "dupla" if dividir_aula_atual else "simples"

    from core.revisao_final import VERSAO_GERADOR_ATUAL

    assinatura_referencia_docx = _assinatura_docx_referencia(caminho_pdf, disciplina, turma)
    perfil_disciplina_cache = perfil_disciplina(disciplina, turma=turma)
    priorizar_docx_sobre_cache_json = bool(
        assinatura_referencia_docx
        and _perfil_prioriza_docx_sobre_cache_json(perfil_disciplina_cache)
    )
    hash_contexto_fingerprint = f"{hash_atual}|ref:{assinatura_referencia_docx}" if assinatura_referencia_docx else hash_atual

    fingerprint_atual = montar_fingerprint_contexto(
        hash_pdf=hash_contexto_fingerprint,
        versao_gerador=VERSAO_GERADOR_ATUAL,
        professor_nome=professor,
        turma=turma,
        disciplina=disciplina,
        bimestre=bimestre,
        tipo_aula=tipo_duracao,
        perfil_metodologico=perfil_metodologico,
    )

    dados_json_antigos = None

    # Verificar cache JSON pré-gerado
    if caminho_pdf and not priorizar_docx_sobre_cache_json:
        resultado_cache = tentar_reutilizar_cache_plano(
            caminho_pdf=caminho_pdf,
            disciplina=disciplina,
            turma=turma,
            usar_ia=usar_ia,
            caminho_pptx_correspondente=str(caminho_pptx_correspondente) if caminho_pptx_correspondente else None,
            hash_atual=hash_atual,
            hash_fonte_extracao_esperada=hash_fonte_extracao_esperada,
            fingerprint_atual=fingerprint_atual,
            versao_gerador_atual=VERSAO_GERADOR_ATUAL,
            perfil_metodologico=perfil_metodologico,
            referencia_docx_por_perfil_fn=_referencia_docx_por_perfil,
            referencia_docx_sobrescreve_metadados_fn=_referencia_docx_sobrescreve_metadados,
            habilidade_referencia_docx_fn=_habilidade_referencia_docx,
            material_aula_com_titulo_fn=_material_aula_com_titulo,
            sobrescrever_listas_pedagogicas_com_referencia_fn=_sobrescrever_listas_pedagogicas_com_referencia,
            origem_metodologia_por_referencia_fn=_origem_metodologia_por_referencia,
            perfil_docx_somente_colunas_pedagogicas_fn=_perfil_docx_somente_colunas_pedagogicas,
        )
        dados_json_antigos = resultado_cache.dados_json_antigos
        if resultado_cache.aula_reutilizada is not None:
            return resultado_cache.aula_reutilizada

    contexto = _preparar_contexto_aula_pdf(
        caminho_pdf=caminho_pdf,
        disciplina=disciplina,
        turma=turma,
        bimestre=bimestre,
        indice_aula=indice_aula,
        modalidade_eja=modalidade_eja,
        caminho_pptx_correspondente=caminho_pptx_correspondente,
    )
    texto = contexto["texto"]
    tema = contexto["tema"]
    material_digital = contexto["material_digital"]
    numero_aula = contexto["numero_aula"]
    cdp_contextual = contexto["cdp_contextual"]
    disciplina_base = contexto["disciplina_base"]
    perfil = contexto["perfil"]
    objetivos_orientacao = contexto["objetivos_orientacao"]
    aprendizagem_orientacao = contexto["aprendizagem_orientacao"]
    extracao_pdf = contexto["extracao_pdf"]
    tipo = contexto["tipo"]
    metodologia_fixa_pdf = contexto["metodologia_fixa_pdf"]
    modalidade_eja_ativa = contexto["modalidade_eja_ativa"]
    contexto_metodologico = contexto["contexto_metodologico"]
    escopo_pv = contexto["escopo_pv"]
    aprendizagem_pv = contexto["aprendizagem_pv"]
    fonte_extracao = contexto.get("fonte_extracao", "pdf")
    arquivo_fonte_extracao = contexto.get("arquivo_fonte_extracao", caminho_fonte_extracao_esperada)

    contexto_geracao = {
        "professor": professor,
        "professor_id": prof_id,
        "disciplina": disciplina,
        "turma": turma,
        "bimestre": bimestre,
        "numero_aula": indice_aula + 1,
        "titulo": tema,
        "aulas_consecutivas": 2 if dividir_aula_atual else 1,
        "duracao_minutos": 90 if dividir_aula_atual else 45,
        "perfil_metodologico": perfil_metodologico,
        "tipo_aula": tipo_duracao,
    }

    resultado_final = None

    if cdp_contextual:
        resultado_final = _montar_resultado_cdp_contextual(
            texto=texto,
            tema=tema,
            disciplina_base=disciplina_base,
            numero_aula=numero_aula,
            indice_aula=indice_aula,
            perfil=perfil,
            tipo=tipo,
            extracao_pdf=extracao_pdf,
            caminho_pdf=caminho_pdf,
        )
    else:
        metodologia_anterior = dados_json_antigos.get("metodologia") if dados_json_antigos else None
        perfil_disciplina_atual = perfil_disciplina(disciplina)

        tentativas = 0
        max_tentativas = 3
        perfil_atual = perfil_metodologico
        resultado_candidato = None

        while tentativas < max_tentativas:
            contexto_geracao["perfil_metodologico"] = perfil_atual
            rascunho_local = _montar_resultado_aula_local(
                texto=texto,
                tema=tema,
                material_digital=material_digital,
                numero_aula=numero_aula,
                disciplina_base=disciplina_base,
                turma=turma,
                provedor_ia=provedor_ia,
                perfil=perfil,
                contexto_metodologico=contexto_metodologico,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                modalidade_eja_ativa=modalidade_eja_ativa,
                metodologia_fixa_pdf=metodologia_fixa_pdf,
                aprendizagem_pv=aprendizagem_pv,
                objetivos_orientacao=objetivos_orientacao,
                aprendizagem_orientacao=aprendizagem_orientacao,
                usar_ia=usar_ia,
                ia_erro="",
                contexto_geracao=contexto_geracao,
                caminho_pdf=caminho_pdf,
                bimestre=bimestre,
            )

            ia_erro = ""
            resultado_candidato = None

            if usar_ia:
                try:
                    from core.ia import processar_plano_ia

                    plano_ia = processar_plano_ia(
                        texto,
                        disciplina,
                        turma,
                        provedor_ia,
                        modelo_ia,
                        modalidade_eja=modalidade_eja_ativa,
                        rascunho_base=rascunho_local,
                        contexto_geracao=contexto_geracao,
                    )
                    tema_ia = tema if escopo_pv.get("titulo") else plano_ia.get("tema") or tema
                    resultado_candidato = _montar_resultado_aula_ia(
                        texto=texto,
                        tema=tema_ia,
                        material_digital=material_digital,
                        numero_aula=numero_aula,
                        disciplina_base=disciplina_base,
                        turma=turma,
                        provedor_ia=provedor_ia,
                        perfil=perfil,
                        contexto_metodologico=contexto_metodologico,
                        indice_aula=indice_aula,
                        total_aulas=total_aulas,
                        modalidade_eja_ativa=modalidade_eja_ativa,
                        plano_ia=plano_ia,
                        metodologia_fixa_pdf=metodologia_fixa_pdf,
                        aprendizagem_pv=aprendizagem_pv,
                        objetivos_orientacao=objetivos_orientacao,
                        aprendizagem_orientacao=aprendizagem_orientacao,
                        caminho_pdf=caminho_pdf,
                        bimestre=bimestre,
                    )
                except Exception as e:
                    ia_erro = f"Falha na IA ({provedor_ia}): {str(e)[:150]}. Usando motor heurístico local."

            if resultado_candidato is None:
                resultado_candidato = dict(rascunho_local)
                resultado_candidato["ia_erro"] = ia_erro
                if usar_ia:
                    resultado_candidato["ia_provedor"] = provedor_ia

            if (metodologia_anterior and
                perfil_disciplina_atual in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"} and
                detectar_similaridade_excessiva(resultado_candidato.get("metodologia"), metodologia_anterior)):

                perfil_atual = selecionar_proximo_perfil(perfil_atual)
                tentativas += 1
            else:
                resultado_final = resultado_candidato
                break

        if resultado_final is None:
            resultado_final = resultado_candidato

    return finalizar_plano_aula(
        resultado_final,
        caminho_pdf=caminho_pdf,
        perfil=perfil,
        fonte_extracao=fonte_extracao,
        arquivo_fonte_extracao=arquivo_fonte_extracao,
        hash_fonte_extracao=hash_fonte_extracao_esperada or hash_atual,
        fingerprint_contexto=fingerprint_atual,
        perfil_metodologico=perfil_metodologico,
        versao_gerador=VERSAO_GERADOR_ATUAL,
        hash_pdf=hash_atual,
        enriquecer_callback=_enriquecer_com_planilha,
    )


def _enriquecer_com_planilha(resultado: dict, caminho_pdf: str):
    import os
    import pandas as pd
    import re
    from pathlib import Path
    try:
        if not caminho_pdf: return
        pasta = Path(caminho_pdf).parent
        candidatos_planilha = [
            pasta / "GUIA.xlsx",
            pasta / "planilha.xlsx",
        ]
        candidatos_planilha.extend(sorted(pasta.glob("GUIA*.xlsx")))
        candidatos_planilha.extend(sorted(pasta.glob("*.xlsx")))
        if pasta.parent.exists():
            candidatos_planilha.append(pasta.parent / "planilha.xlsx")
            candidatos_planilha.extend(sorted(pasta.parent.glob("GUIA*.xlsx")))
            candidatos_planilha.extend(sorted(pasta.parent.glob("*.xlsx")))

        caminho_planilha = None
        for candidato in candidatos_planilha:
            if not candidato.exists():
                continue
            if candidato.name.startswith("~$"):
                continue
            caminho_planilha = candidato
            break
        if not caminho_planilha:
            return
            
        df = pd.read_excel(caminho_planilha)
        nome_arquivo = Path(caminho_pdf).name.upper()
        match_aula = re.search(r'AULA[_\s]*(\d+)', nome_arquivo)
        if not match_aula:
            return
            
        numero_aula = int(match_aula.group(1))
        
        match_serie = re.search(r'(\d)_ANO', str(pasta.absolute()).upper())
        serie_num = match_serie.group(1) if match_serie else None
            
        for index, row in df.iterrows():
            aula_planilha = str(row.get('AULA', '')).strip()
            # Allow "Aula 1", "01", "1", "Aulas 1 e 2", etc.
            match_p = re.search(r'\b0?' + str(numero_aula) + r'\b', aula_planilha)
            if not match_p:
                continue
            
            # Checa serie
            col_serie = [c for c in df.columns if 'ANO' in str(c).upper() or 'RIE' in str(c).upper()]
            if serie_num and col_serie:
                val_serie = str(row[col_serie[0]])
                if serie_num not in val_serie:
                    continue
                    
            # Achou a linha!
            col_titulo = [c for c in df.columns if 'TULO' in str(c).upper() or ('AULA' in str(c).upper() and c != 'AULA')]
            col_conteudo = [c for c in df.columns if 'CONTE' in str(c).upper() or 'OBJETO' in str(c).upper()]
            col_hab = [c for c in df.columns if 'HABILIDADE' in str(c).upper()]
            col_obj = [c for c in df.columns if 'OBJETIVO' in str(c).upper()]
            
            tema_parts = []
            if col_titulo and pd.notna(row[col_titulo[0]]):
                tema_parts.append(str(row[col_titulo[0]]).strip())
            elif col_conteudo and pd.notna(row[col_conteudo[0]]):
                tema_parts.append(str(row[col_conteudo[0]]).strip())
                
            if tema_parts and not str(resultado.get("fonte_referencia_metodologia") or "").strip():
                resultado["tema"] = " - ".join(tema_parts)
                
            aprendizagem = ""
            if col_hab and pd.notna(row[col_hab[0]]):
                aprendizagem += str(row[col_hab[0]]).strip()
            if col_obj and pd.notna(row[col_obj[0]]):
                if aprendizagem: aprendizagem += "\n"
                aprendizagem += "Objetivos: " + str(row[col_obj[0]]).strip()
                
            aprendizagem_atual = str(resultado.get("aprendizagem") or "").strip()
            pode_atualizar_aprendizagem = (
                not aprendizagem_atual
                or _texto_habilidade_invalido_ou_truncado(aprendizagem_atual)
            )
            if (
                aprendizagem
                and not str(resultado.get("fonte_referencia_metodologia") or "").strip()
                and pode_atualizar_aprendizagem
            ):
                resultado["aprendizagem"] = aprendizagem
                
            break
    except Exception as e:
        import logging
        logging.getLogger("PLANOS_LUAN").warning(f"Erro ao enriquecer com planilha: {e}")

def processar_varios_pdfs(
    caminhos_pdf,
    disciplina: str,
    turma: str,
    bimestre: str = "",
    usar_ia: bool = False,
    provedor_ia: str = "",
    modelo_ia: str = "",
    dividir_metodologia: bool = False,
    dividir_por_pdf: list[bool] | None = None,
    modalidade_eja: bool = False,
    progress_callback=None,
    professor: str = "",
) -> list[dict]:
    def _gerar_aula(caminho: str, idx: int, total_aulas_atual: int, dividir_aula_atual: bool):
        import inspect

        sig = inspect.signature(_aula_por_pdf)
        kwargs = {}
        if "professor" in sig.parameters:
            kwargs["professor"] = professor
        if "dividir_aula_atual" in sig.parameters:
            kwargs["dividir_aula_atual"] = dividir_aula_atual
        return _aula_por_pdf(
            caminho,
            disciplina,
            turma,
            bimestre,
            usar_ia,
            provedor_ia,
            modelo_ia,
            indice_aula=idx,
            total_aulas=total_aulas_atual,
            modalidade_eja=modalidade_eja,
            **kwargs,
        )

    return processar_lote_pdfs(
        caminhos_pdf,
        gerar_aula_callback=_gerar_aula,
        dividir_metodologia=dividir_metodologia,
        dividir_por_pdf=dividir_por_pdf,
        progress_callback=progress_callback,
        texto_metodologia_fn=_texto_metodologia,
        dividir_texto_fn=processar_pdf_e_dividir_metodologia,
        metodologia_por_texto_fn=_metodologia_em_blocos_por_texto,
    )
