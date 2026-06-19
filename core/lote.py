import os
import re
import hashlib
import logging
from pathlib import Path

from core.avaliacao import gerar_acessibilidade_dinamica, gerar_acompanhamento_dinamico
from core.metodologia_texto import ajustar_verbos_para_infinitivo
from core.projeto_vida_escopo import buscar_item_projeto_vida, montar_aprendizagem_projeto_vida
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
    _tipo_conteudo_cdp,
    _tema_cdp_seguro,
    limpar_tema_cdp_contextual,
    _limpar_texto_cdp_contextual,
    _conceito_cdp_contextual,
)
from divisor_metodologia import processar_pdf_e_dividir_metodologia

# Compatibilidade para testes e legado
_eh_cdp_contextual_disciplina = eh_cdp_contextual_disciplina
_disciplina_base_cdp_contextual = disciplina_base_cdp_contextual
_limpar_tema_cdp_contextual = limpar_tema_cdp_contextual
_formatar_material_cdp_contextual = formatar_material_cdp_contextual
_metodologia_cdp_contextual = metodologia_cdp_contextual
_acompanhamento_cdp_contextual = acompanhamento_cdp_contextual
_acessibilidade_cdp_contextual = acessibilidade_cdp_contextual
_normalizar = normalizar_texto_lote
_perfil_disciplina = perfil_disciplina
logger = logging.getLogger(__name__)

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


def _detectar_tecnicas_matematica(texto: str, tema: str) -> set[str]:
    base = normalizar_texto_lote(f"{tema} {texto}")
    tecnicas = set()
    mapa = {
        "virem_conversem": ["virem e conversem"],
        "todo_mundo_escreve": ["todo mundo escreve"],
        "com_suas_palavras": ["com suas palavras"],
        "hora_leitura": ["hora da leitura"],
        "de_olho_modelo": ["de olho no modelo"],
        "relembre": ["relembre"],
        "geogebra": ["geogebra"],
        "calculadora": ["calculadora"],
        "arvore_possibilidades": ["arvore de possibilidades", "árvore de possibilidades"],
        "mapa_mental": ["mapa mental"],
        "resolucao_etapas": ["compreender", "planejar", "executar", "verificar"],
    }
    for tecnica, termos in mapa.items():
        if _contem(base, termos):
            tecnicas.add(tecnica)
    return tecnicas


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


def _linhas_secao_matematica(texto: str, marcador: str) -> list[str]:
    marcadores = {
        "para comecar",
        "relembre",
        "exploracao",
        "foco no conteudo",
        "formalizacao",
        "pause e responda",
        "na pratica",
        "encerramento",
    }
    linhas = _limpar_linhas(texto)
    alvo = normalizar_texto_lote(marcador)
    inicio = None

    for indice, linha in enumerate(linhas):
        if normalizar_texto_lote(linha) == alvo:
            inicio = indice + 1
            break

    if inicio is None:
        return []

    ignorar = {
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "pause e responda",
        "veja no livro!",
        "resolucao",
        "fica a dica",
        "conversando sobre o tema",
        "planejando fica mais facil",
    }

    coletadas = []
    for linha in linhas[inicio:]:
        normalizada = normalizar_texto_lote(linha)
        if normalizada in marcadores:
            break
        if normalizada in ignorar:
            continue
        if re.fullmatch(r"\d+\s*minutos?", normalizada):
            continue
        if "freepik" in normalizada or "pixabay" in normalizada or "disponivel em:" in normalizada:
            continue
        coletadas.append(linha)
    return coletadas


def _tem_secao_matematica(texto: str, marcador: str) -> bool:
    alvo = normalizar_texto_lote(marcador)
    return any(normalizar_texto_lote(linha) == alvo for linha in _limpar_linhas(texto))


def _primeira_secao_matematica(texto: str) -> str:
    secoes = ["relembre", "para comecar", "exploracao", "foco no conteudo", "na pratica", "encerramento"]
    melhor_indice = None
    melhor_secao = ""
    for indice, linha in enumerate(_limpar_linhas(texto)):
        normalizada = normalizar_texto_lote(linha)
        if normalizada in secoes and (melhor_indice is None or indice < melhor_indice):
            melhor_indice = indice
            melhor_secao = normalizada
    return melhor_secao


def _contar_atividades_matematica(texto: str) -> int:
    return len(set(re.findall(r"atividade\s*(\d+)", normalizar_texto_lote(texto), flags=re.I)))


def _detectar_formato_aula_matematica(texto: str, tema: str) -> str:
    base = normalizar_texto_lote(f"{tema} {texto}")
    primeira_secao = _primeira_secao_matematica(texto)
    tem_pause = _tem_secao_matematica(texto, "pause e responda")
    tem_foco = _tem_secao_matematica(texto, "foco no conteudo")
    total_atividades = _contar_atividades_matematica(texto)

    if "aula de verificacao" in base or re.search(r"\bverificacao\b", normalizar_texto_lote(tema)):
        return "verificacao"
    if primeira_secao == "relembre" and not tem_foco:
        return "verificacao"
    if primeira_secao == "na pratica" and total_atividades >= 2 and not tem_foco and not tem_pause:
        return "pratica_intensiva"
    if _contem(base, ["modelagem", "polya", "hora da leitura", "de olho no modelo", "um passo de cada vez"]):
        return "modelagem"
    if _contem(normalizar_texto_lote(tema), ["retomando"]) or _contem(base, ["retomar os conceitos", "retomar os conceitos de"]):
        return "retomada"
    return "conceito_novo"


def _resumo_contexto_matematica(texto: str, tema: str) -> str:
    base = normalizar_texto_lote(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "a situação de Marta, que quer comprar um celular de R$ 3.800,00 e precisa planejar quanto economizar por mês"
    if "carro eletrico" in base and "carro hibrido" in base:
        return "a comparação entre os custos de um carro elétrico e de um carro híbrido, considerando gasto por quilômetro e manutenção anual"
    if "josue" in base and "salada de frutas" in base:
        return "as situações-problema sobre compra de frutas, lucro de vendedores, tempos de viagem e descontos progressivos"
    if "internet discada" in base and "banda larga" in base:
        return "a comparação entre internet discada e banda larga para analisar tempo de download e razão entre grandezas"
    if "construcao civil" in base and "agua" in base and "concreto" in base:
        return "o consumo de água na construção civil para relacionar volume de concreto e quantidade de água utilizada"

    linhas = _linhas_secao_matematica(texto, "para comecar") or _linhas_secao_matematica(texto, "na pratica")
    if linhas:
        linhas_contexto = []
        for linha in linhas:
            if _linha_com_marcador_metodologico(linha):
                continue
            linha_limpa = _limpar_linha_metodologica(linha)
            if _linha_instrucao_matematica(linha_limpa):
                continue
            linhas_contexto.append(linha_limpa)
            if len(linhas_contexto) >= 3:
                break
        resumo = re.sub(r"\s+", " ", " ".join(linhas_contexto)).strip()
        if resumo:
            return resumo[:220].rstrip(" .")
    return tema


def _resumo_pratica_matematica(texto: str, tema: str) -> str:
    base = normalizar_texto_lote(f"{tema} {texto}")
    if "josue" in base and "bia" in base and "bruna" in base:
        return "situações sobre compra de frutas, lucro de vendedores online, tempos de viagem e descontos progressivos"
    if "idade de ana" in base or "triplo da minha idade" in base:
        return "situações sobre idade, distribuição de estudantes e equações do 1º grau"
    if "carro eletrico" in base and "concessionaria" in base:
        return "atividades progressivas de modelagem algébrica em contextos de veículos, produção e investimento"
    if "internet discada" in base and "banda larga" in base:
        return "situações de comparação entre velocidades, tamanhos de arquivo e relações entre grandezas"
    if "construcao civil" in base and "agua" in base:
        return "situações de leitura de tabelas, construção de pares ordenados e representação gráfica entre grandezas"

    if _contar_atividades_matematica(texto) >= 2:
        return "atividades progressivas de resolução, registro e verificação das respostas"
    return f"problemas e registros relacionados a {tema}"


def _pergunta_pause_matematica(texto: str) -> str:
    linhas = _linhas_secao_matematica(texto, "pause e responda")
    if not linhas:
        return ""
    bloco = re.sub(r"\s+", " ", " ".join(linhas)).strip()
    if "idade de ana" in normalizar_texto_lote(bloco):
        return "O triplo da idade de Ana, aumentado em 6 anos, totaliza 108 anos. Solicitar que os estudantes escrevam a equacao que modela essa situacao."
    citacao = re.search(r"falou:\s*[\"“]?([^\"”]{25,220})", bloco, flags=re.I)
    if citacao:
        return citacao.group(1).strip(" .")
    if ":" in bloco:
        apos_dois_pontos = bloco.split(":", 1)[1].strip(" \"")
        if len(apos_dois_pontos) >= 25:
            return apos_dois_pontos[:220].rstrip(" .")
    for trecho in re.findall(r"[^?]{25,220}\?", bloco):
        trecho_limpo = trecho.strip(" \"")
        if len(trecho_limpo) >= 30:
            return trecho_limpo
    return bloco[:220].rstrip(" .")


def _fechamento_reflexivo_matematica(texto: str, tema: str, formato: str) -> str:
    base = normalizar_texto_lote(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "retomar o significado de incógnita, solução e verificação, conectando a resposta final à meta financeira de Marta"
    if "carro eletrico" in base and "carro hibrido" in base:
        return "sistematizar as quatro etapas de Polya e discutir quando uma equação do 1º grau é um bom modelo matemático para a situação"
    if "josue" in base and "bruna" in base:
        return "destacar que o valor da incógnita nem sempre é a resposta final e reforçar a importância de verificar cada solução no contexto"
    if "internet discada" in base and "banda larga" in base:
        return "retomar como razão entre grandezas de espécies diferentes ajuda a interpretar tempo, velocidade e unidades de medida"
    if "construcao civil" in base and "agua" in base:
        return "sintetizar como a relação entre grandezas pode ser representada por tabela e gráfico, conectando a leitura matemática ao contexto ambiental"
    if formato == "pratica_intensiva":
        return "retomar os caminhos de resolução usados pela turma e reforçar a importância de verificar se o resultado encontrado faz sentido no problema"
    return f"sistematizar as estratégias construídas pela turma para compreender e resolver situações relacionadas a {tema}"


def _aprendizagem_matematica(tema: str, tipo: str, texto: str) -> str:
    base = normalizar_texto_lote(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "Retomar e aplicar equações do 1º grau para modelar situações do cotidiano, identificar a incógnita, resolver por operações inversas e verificar a solução encontrada."
    if tipo == "modelagem":
        return "Modelar situações-problema utilizando equações do 1º grau, aplicando estratégias de resolução, interpretação do enunciado e verificação do resultado no contexto."
    if tipo == "funcoes":
        return "Identificar relações de dependência entre grandezas e representá-las por tabelas, expressões e gráficos, interpretando o comportamento da função no contexto analisado."
    if tipo == "grandezas_medidas":
        return "Compreender e comparar relações entre grandezas de espécies diferentes, analisando razões, unidades e proporcionalidade em situações-problema."
    if tipo == "estatistica_probabilidade":
        return "Ler, organizar e interpretar dados, tabelas e gráficos para justificar conclusões e resolver situações que envolvam análise de informações."
    if tipo == "algebra":
        return "Resolver e interpretar situações-problema por meio de equações do 1º grau, identificando incógnitas, organizando procedimentos e verificando a coerência das soluções."
    return f"Compreender e aplicar conceitos relacionados a {tema}."


def _detectar_tipo_aula(texto: str, tema: str, disciplina: str = "", turma: str = "") -> str:
    return _detectar_tipo_aula_classificador(texto, tema, disciplina, turma=turma)

    base = normalizar_texto_lote(f"{disciplina} {tema} {texto}")
    perfil = perfil_disciplina(disciplina, turma=turma)
    tema_base = normalizar_texto_lote(tema)

    if perfil == "educacao_financeira":
        _EF_AULA_PRATICA = [
            "pesquisa de precos", "elaborar uma tabela", "simular gastos",
            "dividir os alunos em trios", "trabalhar de forma individual",
            "material impresso como guia", "sentar em circulo para compartilhar",
            "pesquisa de preços", "elaborar uma planilha", "simular despesas",
            "planejamento pratico", "planejamento prático",
        ]
        if _contem(base, _EF_AULA_PRATICA):
            return "aula_pratica_continuidade"

        mapa_tema = [
            ("instituicoes_financeiras", ["onde guardamos o dinheiro", "guardar dinheiro", "onde guardar o dinheiro", "guardamos o dinheiro"]),
            ("investimento_poupanca", ["por que poupamos", "porque poupamos", "reserva de emergencia", "poupamos"]),
            ("orcamento_planejamento", ["objetivos em familia ou em grupo", "objetivos em familia", "objetivos em grupo", "planejamento financeiro"]),
            ("analise_percentuais_noticias", ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias"]),
            ("governo_economia", ["papel do governo na economia", "governo na economia"]),
            ("impacto_decisoes_economicas", ["impacto das decisoes economicas", "decisoes economicas em nossas vidas"]),
        ]
        for tipo, termos in mapa_tema:
            if _contem(tema_base, termos):
                return tipo
        if _contem(tema_base, ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]):
            return "credito_endividamento"
        if _contem(tema_base, ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]):
            return "empreendedorismo"
        if _contem(tema_base, ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]):
            return "cidadania_financeira"
        if _contem(tema_base, ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]):
            return "instituicoes_financeiras"
        if _contem(tema_base, ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]):
            return "investimento_poupanca"
        if _contem(tema_base, ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]):
            return "orcamento_planejamento"
        if _contem(tema_base, ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias", "manchetes", "noticias", "percentual", "porcentagem"]):
            return "analise_percentuais_noticias"
        if _contem(tema_base, ["papel do governo na economia", "governo na economia", "estado na economia", "politicas publicas", "impostos", "arrecadacao"]):
            return "governo_economia"
        if _contem(tema_base, ["impacto das decisoes economicas", "decisoes economicas em nossas vidas", "impacto das escolhas economicas", "escolhas economicas"]):
            return "impacto_decisoes_economicas"
        if _contem(tema_base, ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]):
            return "consumo_consciente"
        if _contem(base, ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]):
            return "credito_endividamento"
        if _contem(base, ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]):
            return "empreendedorismo"
        if _contem(base, ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]):
            return "cidadania_financeira"
        if _contem(base, ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]):
            return "instituicoes_financeiras"
        if _contem(base, ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]):
            return "investimento_poupanca"
        if _contem(base, ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]):
            return "orcamento_planejamento"
        if _contem(base, ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]):
            return "consumo_consciente"
        return "decisao_financeira"

    if perfil == "matematica":
        if _contem(base, ["aula khan", "pratica na khan", "atividade khan"]) and _contem(
            base,
            ["revisao", "conceito de funcao", "relacoes proporcionais", "grandezas diretamente proporcionais"],
        ):
            return "revisao_khan_funcao"
        if _contem(
            base,
            [
                "modelagem",
                "modelar situacoes",
                "modelar situacoes-problema",
                "metodo de polya",
                "polya",
                "representar matematicamente",
                "sentenca matematica",
            ],
        ):
            return "modelagem"
        if _contem(tema_base, ["grandeza", "razao", "proporcao"]):
            return "grandezas_medidas"
        if _contem(base, ["equac", "equa", "variavel", "incognita", "express", "polinom", "sistema", "inequac", "logarit", "1 grau", "2 grau", "modulo"]):
            return "algebra"
        if _contem(base, ["func", "f(x)", "lei de formacao", "dominio", "imagem", "grafico de funcao", "taxa de variacao"]):
            return "funcoes"
        if _contem(base, ["combinat", "permut", "arranjo", "fatorial", "contagem", "ordem importa", "anagrama", "comissao", "placa", "senha"]):
            return "combinatoria"
        if _contem(base, ["grandeza", "razao", "proporcao", "velocidade media", "mbps", "kbps"]):
            return "grandezas_medidas"
        if _contem(base, ["estatist", "probab", "media", "mediana", "moda", "amostra", "espaco amostral", "evento", "frequencia", "censo", "pesquisa"]):
            return "estatistica_probabilidade"
        if _contem(base, ["geometr", "area", "perimetro", "volume", "angulo", "triangulo", "figura", "solido", "pitagoras", "malha", "trigonom"]):
            return "geometria"
        if _contem(base, ["numero", "fracao", "decimal", "porcentagem", "potencia", "raiz", "divisibilidade", "operacao", "mmc", "mdc", "primo"]):
            return "numeros_operacoes"
        return "resolucao_problemas"

    if _contem(base, ["producao textual", "produzir", "rascunho", "revisao", "reescrita", "redacao", "planejamento do texto"]):
        return "producao"
    if _contem(base, ["debate", "argumento", "opiniao", "tese", "ponto de vista", "carta de leitor"]):
        return "argumentacao"
    if _contem(base, ["fonte historica", "documento historico", "linha do tempo", "periodo historico", "cronologia"]):
        return "fonte_historica"
    if _contem(base, ["mapa", "paisagem", "territorio", "regiao", "grafico", "escala", "cartografia"]):
        return "analise_geografica"
    if _contem(base, ["experimento", "investigacao", "hipotese", "modelo", "observacao", "processo natural"]):
        return "investigacao"
    if _contem(base, ["calculo", "problema", "porcentagem", "juros", "orcamento", "tabela", "grafico"]):
        return "resolucao_problemas"
    if _contem(base, ["vocabulary", "listen", "repeat", "speaking", "reading", "writing", "dialogue"]):
        return "lingua_estrangeira"
    if _contem(base, ["apreciacao", "criacao", "experimentacao", "musica", "imagem", "obra", "performance"]):
        return "arte_pratica"
    if _contem(base, ["autoconhecimento", "convivencia", "projeto de vida", "escolha", "respeito", "planejamento pessoal"]):
        return "reflexiva"
    if _contem(
        base,
        [
            "leitura",
            "leia",
            "texto",
            "interpreta",
            "genero textual",
            "conto",
            "cronica",
            "anuncio",
            "publicidade",
            "publicitario",
            "slogan",
            "observe",
        ],
    ):
        return "leitura"
    return "geral"


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


def _linha_instrucao_matematica(linha: str) -> bool:
    normalizada = normalizar_texto_lote(linha)
    inicios_instrucao = (
        "resolva",
        "calcule",
        "determine",
        "registre",
        "complete",
        "observe",
        "assinale",
        "responda",
        "explique",
        "justifique",
        "copie",
        "escreva",
        "analise",
    )
    return normalizada.startswith(inicios_instrucao)


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


def _tecnica_por_perfil(perfil: str) -> dict[str, str]:
    tecnicas = {
        "lingua_portuguesa_ef": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lingua_portuguesa_em": {
            "discussao": "DEBATE ORIENTADO",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "leitura_redacao": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "orientacao_estudos": {
            "discussao": "discussao em duplas sobre estrategias de estudo",
            "registro": "registro de estrategia no caderno",
            "sintese": "autoavaliacao breve",
        },
        "ciencias_ef": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "biologia": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "quimica": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM PROCEDIMENTOS E RESULTADOS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "fisica": {
            "discussao": "OBSERVEM E LEVANTEM HIPOTESES",
            "registro": "REGISTREM MEDIDAS E RELACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "historia": {
            "discussao": "ANALISEM AS FONTES",
            "registro": "REGISTREM A CRONOLOGIA",
            "sintese": "COM SUAS PALAVRAS",
        },
        "geografia": {
            "discussao": "OBSERVEM O MAPA/IMAGEM",
            "registro": "REGISTREM AS RELACOES ESPACIAIS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "ingles": {
            "discussao": "LISTEN AND REPEAT",
            "registro": "WRITE AND SHARE",
            "sintese": "SAY IT IN ENGLISH",
        },
        "arte": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "REGISTRO NO DIARIO DE BORDO",
            "sintese": "APRECIACAO COMPARTILHADA",
        },
        "projeto_de_vida": {
            "discussao": "roda de conversa acolhedora",
            "registro": "registro pessoal sem exposicao obrigatoria",
            "sintese": "compromisso para a semana",
        },
        "educacao_financeira": {
            "discussao": "analise orientada de caso",
            "registro": "registro de calculos, criterios e decisoes",
            "sintese": "planejamento de aplicacao",
        },
        "matematica": {
            "discussao": "uma conversa em duplas",
            "registro": "um registro individual no caderno",
            "sintese": "síntese com as próprias palavras",
        },
        "tecnologia_inovacao": {
            "discussao": "PENSEM EM SOLUCOES",
            "registro": "REGISTREM O PROTOTIPO OU ALGORITMO",
            "sintese": "APRESENTEM A SOLUCAO",
        },
        "sociologia": {
            "discussao": "DEBATAM O FENOMENO SOCIAL",
            "registro": "REGISTREM ARGUMENTOS E EVIDENCIAS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lideranca_oratoria": {
            "discussao": "PRATIQUEM EM DUPLAS OU GRUPOS",
            "registro": "REGISTREM FEEDBACKS E AVANCOS",
            "sintese": "AUTOAVALIACAO BREVE",
        },
        "ciencias": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lingua_portuguesa": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "redacao": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "orientacao": {
            "discussao": "discussao em duplas sobre estrategias de estudo",
            "registro": "registro de estrategia no caderno",
            "sintese": "autoavaliacao breve",
        },
        "projeto_vida": {
            "discussao": "roda de conversa acolhedora",
            "registro": "registro pessoal sem exposicao obrigatoria",
            "sintese": "compromisso para a semana",
        },
    }
    return tecnicas.get(perfil, tecnicas["lingua_portuguesa_ef"])


def _frases_por_contexto(perfil: str, tipo: str, tema: str, conceito: str, turma: str, texto_base: str = "") -> dict[str, str]:
    tecnicas = _tecnica_por_perfil(perfil)
    tecnicas_pdf = _detectar_tecnicas_matematica(texto=texto_base, tema=tema) if perfil == "matematica" else set()

    base = {
        "para_comecar": (
            f"Retomar conhecimentos previos da turma sobre {tema}. Propor {tecnicas['discussao']} "
            "para levantar hipoteses, exemplos e duvidas iniciais."
        ),
        "leitura": (
            "Realizar leitura guiada dos textos, imagens, comandos e/ou exemplos do material, fazendo pausas "
            "para destacar informacoes relevantes. Organizar no quadro as ideias principais e as palavras-chave "
            "que orientam a atividade."
        ),
        "contextualizacao": (
            f"Contextualizar {tema} a partir de situacoes do cotidiano, repertorios culturais ou exemplos do "
            "material, ajudando a turma a compreender por que esse conteudo e relevante e como ele circula "
            "socialmente."
        ),
        "leitura_analitica": (
            "Conduzir leitura analitica do texto, imagem, dado ou situacao apresentada, destacando escolhas de "
            "linguagem, organizacao das ideias, pistas visuais e informacoes que sustentam a compreensao."
        ),
        "exploracao": (
            "Estimular os estudantes a levantar estrategias, testar caminhos e comparar representacoes antes da "
            "sistematizacao, valorizando diferentes formas de pensar e justificar o raciocinio."
        ),
        "foco": (
            f"Analisar {conceito}, relacionando o conteudo ao objetivo da aula. Explicar os pontos centrais de "
            "forma dialogada e verificar se a turma compreende as relacoes entre conceito, exemplo e atividade."
        ),
        "formalizacao": (
            "Sistematizar no quadro os conceitos, propriedades, procedimentos e registros essenciais da aula, "
            "nomeando cada etapa da resolucao e retomando criterios para validar as respostas."
        ),
        "pratica": (
            f"Orientar a resolucao das atividades propostas, usando {tecnicas['registro']} para garantir registro "
            "individual. Circular pela sala, mediar duvidas e solicitar justificativas para as respostas."
        ),
        "pause": (
            "Socializar algumas respostas e realizar correcao dialogada, retomando trechos do material, registros "
            "dos estudantes e duvidas comuns antes de avancar."
        ),
        "encerramento": (
            f"Finalizar com {tecnicas['sintese']}, retomando os aprendizados sobre {tema} e registrando uma sintese "
            "curta no quadro ou no caderno."
        ),
    }

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        if tipo == "producao":
            base["leitura"] = (
                "Apresentar a proposta de producao e realizar leitura guiada dos comandos, destacando finalidade, "
                "interlocutor, genero textual e criterios de qualidade. Organizar no quadro um roteiro de planejamento."
            )
            base["foco"] = (
                f"Analisar as caracteristicas do genero relacionado a {tema}, observando estrutura, linguagem, "
                "organizacao das ideias e marcas que orientam a escrita."
            )
            base["pratica"] = (
                "Orientar o planejamento, a escrita do rascunho e a revisao. Solicitar que os estudantes confiram "
                "se o texto atende a finalidade, ao publico e aos criterios combinados."
            )
        elif tipo == "argumentacao":
            base["foco"] = (
                f"Analisar tese, opiniao, argumentos e estrategias persuasivas presentes em {conceito}. Destacar "
                "como escolhas de linguagem e exemplos ajudam a sustentar o ponto de vista."
            )
        else:
            base["foco"] = (
                f"Analisar {conceito}, destacando genero, finalidade, publico-alvo, recursos de linguagem e pistas "
                "textuais ou visuais que ajudam na compreensao."
            )

    elif perfil == "orientacao_estudos" or perfil == "orientacao":
        base["foco"] = (
            f"Trabalhar {conceito} como oportunidade para ensinar uma estrategia de estudo: localizar informacoes, "
            "interpretar comandos, justificar respostas e revisar registros."
        )
        base["pratica"] = (
            "Orientar a resolucao das atividades explicitando o passo a passo de estudo: ler o comando, marcar "
            "palavras-chave, buscar evidencias, responder e revisar a resposta."
        )
        base["encerramento"] = (
            f"Finalizar com autoavaliacao breve sobre qual estrategia ajudou mais a compreender {tema} e como ela "
            "pode ser usada em outras disciplinas."
        )

    elif perfil in {"ciencias_ef", "ciencias", "biologia", "quimica", "fisica"}:
        base["para_comecar"] = (
            f"Contextualizar {tema} com uma situacao-problema, imagem, dado ou exemplo do cotidiano. Propor "
            f"{tecnicas['discussao']} para que os estudantes antecipem explicacoes e levantem evidencias."
        )
        base["foco"] = (
            f"Explicar {conceito} de forma progressiva, relacionando fenomeno, causa, consequencia e exemplos. "
            "Usar esquemas no quadro para diferenciar observacao, hipotese e conceito cientifico."
        )
        base["pratica"] = (
            f"Orientar leitura de texto, imagem, modelo ou atividade investigativa, solicitando {tecnicas['registro']}. "
            "Retomar as evidencias usadas pelos estudantes para justificar as respostas."
        )

    elif perfil == "historia":
        base["foco"] = (
            f"Apresentar o contexto historico de {conceito}, situando sujeitos, tempo, espaco e conflitos envolvidos. "
            "Relacionar as ideias iniciais da turma com os conceitos historicos em estudo."
        )
        base["pratica"] = (
            "Orientar a analise de fontes, imagens, mapas, linhas do tempo ou textos do material. Solicitar registro "
            "das evidencias encontradas e mediacao para diferenciar fato, interpretacao e contexto."
        )

    elif perfil == "geografia":
        base["foco"] = (
            f"Analisar {conceito} considerando paisagem, territorio, escala, localizacao e relacoes entre sociedade "
            "e natureza. Usar mapa, imagem, tabela ou grafico como apoio para a explicacao."
        )
        base["pratica"] = (
            "Orientar leitura de mapas, imagens, graficos ou situacoes-problema, solicitando que os estudantes "
            "identifiquem elementos espaciais e expliquem relacoes de causa e consequencia."
        )

    elif perfil == "ingles":
        base["para_comecar"] = (
            f"Retomar vocabulario conhecido relacionado a {tema} com repeticao oral breve e exemplos no quadro. "
            "Estimular que os estudantes tentem pronunciar e reconhecer palavras antes da sistematizacao."
        )
        base["leitura"] = (
            "Apresentar o texto, dialogo, imagem ou situacao comunicativa, alternando leitura em voz alta, escuta "
            "e repeticao. Destacar vocabulario-chave e estruturas em ingles com apoio em exemplos."
        )
        base["foco"] = (
            f"Explorar o uso comunicativo de {conceito}, mostrando quando e como empregar as expressoes estudadas. "
            "Registrar no quadro exemplos curtos em ingles e seus sentidos em contexto."
        )
        base["pratica"] = (
            "Organizar pratica oral e escrita em pares, com repeticao, preenchimento, pequenas respostas ou dialogos. "
            "Acompanhar pronuncia, compreensao e uso funcional das expressoes."
        )

    elif perfil == "arte":
        base["foco"] = (
            f"Apresentar referencias artisticas relacionadas a {conceito}, orientando apreciacao de elementos visuais, "
            "sonoros, corporais ou culturais. Valorizar percepcoes diferentes sem reduzir a aula a explicacao teorica."
        )
        base["pratica"] = (
            "Propor experimentacao, criacao ou apreciacao orientada, com registro no diario de bordo. Acompanhar "
            "processos criativos, escolhas dos estudantes e socializacao das producoes ou percepcoes."
        )

    elif perfil == "projeto_de_vida" or perfil == "projeto_vida":
        conceito_seguro = tema if _conceito_generico_ou_quebrado_projeto_vida(conceito) else conceito
        base["para_comecar"] = (
            f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. Propor "
            "troca em duplas ou roda de conversa breve, respeitando diferentes ritmos de participacao."
        )
        base["foco"] = (
            f"Construir a reflexao sobre {conceito_seguro} por meio de exemplos escolares e cotidianos, ajudando a turma a "
            "relacionar sentir, pensar e agir de forma respeitosa."
        )
        base["pratica"] = (
            "Orientar atividade reflexiva com registro individual, escolha pessoal ou planejamento simples. Garantir "
            "que a socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas."
        )
        base["encerramento"] = (
            f"Encerrar com um compromisso simples ou observacao para a semana, relacionado a {tema}, reforcando "
            "autonomia, respeito e cuidado nas relacoes."
        )

    elif perfil == "educacao_financeira":
        conceito_seguro = tema if normalizar_texto_lote(conceito) in {"educacao financeira", "financeira"} else conceito

        situacoes = {
            "orcamento_planejamento": "uma situacao de organizacao de renda, gastos e prioridades para cumprir uma meta simples",
            "consumo_consciente": "um dilema de consumo em que a turma precise comparar necessidade, desejo, preco, durabilidade e impacto da escolha",
            "investimento_poupanca": "uma situacao de poupanca ou reserva de emergencia em que pequenos valores acumulados ajudam a lidar com imprevistos",
            "credito_endividamento": "uma compra parcelada ou oferta de credito em que seja necessario comparar valor a vista, juros, parcelas e custo total",
            "empreendedorismo": "um pequeno projeto de venda, servico ou solucao para a comunidade escolar, analisando custos, preco e viabilidade",
            "analise_percentuais_noticias": "uma noticia, manchete ou grafico em que a turma precise interpretar percentuais e relacionar os dados a uma situacao real",
            "governo_economia": "uma situacao cotidiana sobre como a acao do governo influencia precos, servicos, impostos e a vida economica da populacao",
            "impacto_decisoes_economicas": "uma situacao do cotidiano em que escolhas economicas afetam consumo, planejamento, prioridades e bem-estar",
            "cidadania_financeira": "uma situacao de consumo que envolva direitos, responsabilidades, comprovantes, garantia ou uso seguro de servicos financeiros",
            "instituicoes_financeiras": "uma situacao cotidiana sobre onde guardar, movimentar e proteger o dinheiro com seguranca",
        }
        situacao = situacoes.get(tipo, f"uma situacao financeira real relacionada a {tema}")

        base["para_comecar"] = (
            f"Apresentar {situacao}, sem exigir relatos pessoais nem julgamentos sobre habitos financeiros familiares. "
            "Convidar os estudantes a levantar hipoteses sobre escolhas, riscos, prioridades e consequencias antes da sistematizacao."
        )
        base["analise_caso"] = (
            f"Conduzir a analise do caso ligado a {tema}, identificando dados importantes, alternativas possiveis, "
            "criterios de decisao e consequencias de curto e longo prazo. Registrar no quadro as perguntas que ajudam a decidir com responsabilidade."
        )
        base["foco"] = (
            f"Desenvolver {conceito_seguro} de forma contextualizada, relacionando o conceito a situacoes reais de consumo, "
            "planejamento, poupanca, credito ou organizacao de recursos. Explicar o vocabulario financeiro necessario e construir criterios claros para a tomada de decisao."
        )
        base["pause"] = (
            "Promover uma pausa para que a turma compare alternativas, justifique escolhas e avalie impactos financeiros, "
            "retomando dados do material e duvidas comuns antes de seguir para a aplicacao."
        )
        base["calculos"] = (
            "Orientar calculos financeiros de forma guiada, destacando dados, operacoes, porcentagens, juros, parcelas, saldo ou custo total conforme o material. "
            "Relacionar cada resultado numerico a uma decisao possivel, evitando que a atividade fique apenas mecanica."
        )
        base["planejamento"] = (
            "Orientar a elaboracao ou analise de um planejamento financeiro simulado, organizando receita, despesas, prioridades, metas e saldo. "
            "Acompanhar os registros para que os estudantes expliquem os criterios usados nas escolhas."
        )
        base["simulacao"] = (
            "Organizar uma simulacao financeira ou analise de alternativas, aplicando os criterios construidos na aula para escolher, comparar, planejar ou revisar uma decisao. "
            "Solicitar registro de calculos, justificativas e possiveis consequencias."
        )
        base["projeto"] = (
            "Orientar a organizacao de um projeto empreendedor simples, levantando recursos necessarios, custos, preco, publico, viabilidade e cuidados eticos. "
            "Solicitar que os estudantes justifiquem as decisoes tomadas no planejamento."
        )
        base["pratica"] = (
            "Orientar a resolucao das atividades do material com registro individual ou em dupla, acompanhando leitura de dados, comparacao de alternativas e justificativa das decisoes. "
            "Retomar vocabulario financeiro e criterios de escolha sempre que surgirem duvidas."
        )

        if tipo == "orcamento_planejamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} como estrategia de organizacao financeira, relacionando receitas, despesas, gastos, prioridades e metas. "
                "Construir com a turma criterios para controlar recursos e ajustar escolhas conforme limites e objetivos."
            )
            base["pratica"] = base["planejamento"]
        elif tipo == "consumo_consciente":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} a partir de criterios de consumo consciente, diferenciando necessidade, desejo, prioridade, custo-beneficio e impacto da escolha. "
                "Evitar tom moralista e conduzir a analise com base em argumentos, dados e consequencias."
            )
        elif tipo == "investimento_poupanca":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando poupanca, reserva, rendimento, constancia e planejamento de metas. "
                "Mostrar como a organizacao dos recursos ajuda a lidar com imprevistos e objetivos de curto ou longo prazo."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "credito_endividamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} com foco no uso responsavel do credito, analisando juros, parcelas, custo total, riscos de endividamento e criterios para decidir. "
                "Comparar alternativas sem estimular consumo, priorizando avaliacao critica e planejamento."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "empreendedorismo":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} articulando oportunidade, necessidade, produto ou servico, custos, preco, lucro e viabilidade. "
                "Relacionar a proposta a planejamento, responsabilidade e analise do contexto."
            )
            base["pratica"] = base["projeto"]
        elif tipo == "analise_percentuais_noticias":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} por meio da leitura de noticias, manchetes, tabelas e graficos, ajudando a turma a interpretar percentuais, "
                "comparar dados e perceber como os numeros influenciam a compreensao dos fatos."
            )
            base["calculos"] = (
                "Orientar calculos de porcentagem e comparacao de variacoes com apoio do quadro, destacando o significado de cada dado antes do procedimento numerico. "
                "Retomar passo a passo como localizar o valor de referencia, calcular percentuais e interpretar o resultado no contexto da noticia analisada."
            )
            base["pratica"] = (
                "Propor leitura guiada de noticias ou situacoes semelhantes, seguida de registros no caderno com interpretacao dos percentuais, comparacao de informacoes "
                "e justificativa sobre o que os dados revelam."
            )
        elif tipo == "governo_economia":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando arrecadacao, servicos publicos, regulacao e impactos economicos no cotidiano. "
                "Conduzir a turma a perceber como decisoes do governo interferem em precos, circulacao de dinheiro e acesso a direitos."
            )
            base["pratica"] = (
                "Orientar a analise de exemplos concretos, comparando situacoes em que a acao do governo influencia consumo, trabalho, precos ou servicos. "
                "Solicitar registros curtos com explicacao das relacoes observadas."
            )
        elif tipo == "impacto_decisoes_economicas":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} por meio de escolhas economicas do cotidiano, relacionando recursos disponiveis, prioridades, consumo e consequencias de curto e longo prazo. "
                "Estimular a turma a comparar alternativas com base em criterios claros e realistas."
            )
            base["pratica"] = (
                "Propor situacoes-problema simples para que os estudantes comparem escolhas, antecipem impactos e justifiquem decisoes com base nos dados apresentados. "
                "Retomar o vocabulario financeiro necessario sempre que surgirem duvidas."
            )
        elif tipo == "cidadania_financeira":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando direitos do consumidor, responsabilidades, seguranca, comprovantes, garantias e autonomia nas decisoes financeiras. "
                "Orientar a turma a identificar formas de protecao e uso consciente de servicos financeiros."
            )
        elif tipo == "instituicoes_financeiras":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} explicando a funcao das instituicoes financeiras na guarda, movimentacao, controle e protecao do dinheiro. "
                "Comparar exemplos como banco, conta digital, poupanca e outros servicos, destacando seguranca e planejamento."
            )

        base["encerramento"] = (
            f"Sintetizar os aprendizados financeiros relacionados a {tema}, retomando criterios de decisao, organizacao e responsabilidade. "
            "Propor um fechamento com planejamento de aplicacao no cotidiano, sem solicitar exposicao de informacoes financeiras pessoais."
        )

    elif perfil == "matematica":
        formato = _detectar_formato_aula_matematica(texto_base, tema)
        contexto = _resumo_contexto_matematica(texto_base, tema)
        pratica = _resumo_pratica_matematica(texto_base, tema)
        pergunta_pause = _pergunta_pause_matematica(texto_base)
        tecnica_inicio = "uma conversa em duplas" if "virem_conversem" in tecnicas_pdf else "uma discussão coletiva inicial"
        tecnica_registro = "um registro individual no caderno" if "todo_mundo_escreve" in tecnicas_pdf else tecnicas["registro"]

        if formato == "verificacao":
            base["para_comecar"] = (
                f"Retomar com a turma os procedimentos essenciais relacionados a {tema}, recuperando "
                "criterios de resolucao, organizacao dos registros e verificacao das respostas antes das atividades."
            )
        elif formato == "pratica_intensiva":
            base["para_comecar"] = (
                "Retomar brevemente as estrategias discutidas na aula anterior e combinar com a turma como registrar "
                "equacao, resolucao e verificacao em cada situacao proposta."
            )
        else:
            base["para_comecar"] = (
                f"Apresentar {contexto} e propor {tecnica_inicio} para que os estudantes mobilizem conhecimentos "
                "previos, levantem hipoteses e identifiquem o que precisa ser descoberto na situacao."
            )

        if tipo == "algebra":
            base["foco"] = (
                f"Conduzir a construcao de {conceito}, identificando a incognita, organizando os dados do problema e "
                "mostrando como as propriedades da igualdade ajudam a transformar e validar cada passo da resolucao."
            )
        elif tipo == "funcoes":
            base["foco"] = (
                f"Conduzir a leitura de {conceito} articulando tabela, pares ordenados, representacao grafica e "
                "interpretacao da dependencia entre as grandezas envolvidas no contexto estudado."
            )
        elif tipo == "grandezas_medidas":
            base["foco"] = (
                f"Desenvolver {conceito} relacionando unidades, razoes e comparacoes entre grandezas, destacando como "
                "as variacoes do contexto ajudam a construir significado para os calculos."
            )
        elif tipo == "estatistica_probabilidade":
            base["foco"] = (
                f"Desenvolver {conceito} por meio da leitura de dados, tabelas e graficos, orientando a turma a "
                "organizar informacoes, justificar conclusoes e conferir a coerencia das interpretacoes."
            )
        elif tipo == "combinatoria":
            base["foco"] = (
                f"Desenvolver {conceito} discutindo criterios de contagem, verificando se a ordem importa e escolhendo "
                "a estrategia mais adequada antes de iniciar os calculos."
            )
        elif tipo == "modelagem":
            base["foco"] = (
                f"Conduzir a modelagem da situacao apresentada em {tema}, traduzindo os dados para linguagem "
                "matematica, construindo a equacao e interpretando a solucao no contexto original."
            )
        else:
            base["foco"] = (
                f"Explorar {conceito} com exemplos guiados, destacando dados, relacoes, procedimentos e criterios para "
                "verificar se o resultado encontrado faz sentido na situacao estudada."
            )

        if "hora_leitura" in tecnicas_pdf:
            base["foco"] = (
                base["foco"]
                + " Integrar leitura orientada para explicitar como interpretar o enunciado, selecionar informações "
                "relevantes e planejar o caminho de resolução."
            )
        if "um_passo" in tecnicas_pdf or "um passo de cada vez" in normalizar_texto_lote(texto_base):
            base["foco"] = (
                base["foco"]
                + " Construir a estratégia de forma gradual, nomeando cada etapa do procedimento."
            )
        if "de_olho_modelo" in tecnicas_pdf:
            base["foco"] = (
                base["foco"]
                + " Apoiar a explicação com um exemplo resolvido, comentando por que a solução encontrada é válida."
            )

        base["formalizacao"] = ""
        if pergunta_pause:
            base["pause"] = (
                f"Propor a questao do material: {pergunta_pause} Socializar as respostas e realizar correcao "
                "dialogada, retomando as justificativas matematicas construidas pela turma."
            )
        else:
            base["pause"] = (
                "Socializar algumas estrategias, comparar caminhos de resolucao e retomar com a turma os criterios "
                "usados para validar cada resposta."
            )

        if formato == "verificacao":
            base["pratica"] = (
                f"Organizar {tecnica_registro} com atividades de retomada e verificacao, solicitando resolucao "
                "completa, comparacao de estrategias e conferência cuidadosa da coerencia dos resultados."
            )
        elif formato == "pratica_intensiva":
            base["pratica"] = (
                f"Organizar {tecnica_registro} com {pratica}, solicitando que cada estudante registre equacao, "
                "resolucao, justificativa e verificacao da resposta em todas as atividades propostas."
            )
        else:
            base["pratica"] = (
                f"Orientar {tecnica_registro} com {pratica}, acompanhando a interpretacao dos enunciados, a "
                "organizacao dos calculos e a validacao das solucoes construidas pela turma."
            )

        fechamento = _fechamento_reflexivo_matematica(texto_base, tema, formato)
        base["encerramento"] = (
            f"Encerrar com {tecnicas['sintese']}, para {fechamento} e registrar uma sintese coletiva do que "
            "foi aprendido na aula."
        )

    elif perfil == "tecnologia_inovacao":
        base["para_comecar"] = (
            f"Apresentar um problema real relacionado a {tema}, incentivando observacao do contexto e levantamento "
            "de necessidades antes da construcao de solucoes."
        )
        base["pratica"] = (
            "Orientar criacao, programacao, prototipagem ou teste de solucao, acompanhando escolhas tecnicas, "
            "iteracoes e registros do processo."
        )

    elif perfil == "sociologia":
        base["para_comecar"] = (
            f"Apresentar um fenomeno social ligado a {tema} por meio de situacao, imagem, dado ou relato, "
            "provocando estranhamento e questionamentos iniciais."
        )
        base["foco"] = (
            f"Analisar {conceito} sociologicamente, articulando teoria, conceitos e exemplos da realidade social "
            "para superar leituras baseadas apenas no senso comum."
        )

    elif perfil == "lideranca_oratoria":
        base["para_comecar"] = (
            f"Realizar aquecimento vocal, corporal ou mental relacionado a {tema}, criando um ambiente acolhedor "
            "para a pratica de comunicacao e reduzindo a ansiedade de exposicao."
        )
        base["foco"] = (
            f"Apresentar tecnicas e conceitos ligados a {conceito}, demonstrando aplicacoes em fala publica, "
            "argumentacao, escuta ativa ou lideranca colaborativa."
        )
        base["pause"] = (
            "Promover pratica oral breve com feedback positivo sobre avancos observados antes de sugerir ajustes, "
            "fortalecendo confianca e progressao da turma."
        )
        base["pratica"] = (
            "Orientar exercicios, miniapresentacoes, debates ou dinamicas de lideranca de forma progressiva, "
            "sem expor estudantes abruptamente e valorizando preparo, escuta e cooperacao."
        )
        base["encerramento"] = (
            "Encerrar com autoavaliacao breve sobre comunicacao, postura e participacao, registrando um proximo "
            "passo de desenvolvimento para a turma."
        )

    return base


def _obra_literaria_redacao(tema: str, texto_base: str = "") -> str:
    fonte = " ".join([str(tema or ""), str(texto_base or "")[:800]])
    match = re.search(r"[\"“”']([^\"“”']{3,80})[\"“”']", fonte)
    if match:
        return match.group(1).strip()
    texto = re.sub(r"^\s*aula\s*\d+\s*[-:–—]?\s*", "", str(tema or ""), flags=re.I).strip(" -:–—")
    texto = re.sub(r"^trilha\s*", "", texto, flags=re.I).strip(" -:–—")
    return texto or "a obra literaria em estudo"


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



def _genero_textual_redacao(texto_base: str, tema: str = "") -> str:
    base = normalizar_texto_lote(f"{tema} {texto_base}")
    if "resenha" in base:
        return "resenha"
    if "cronica" in base or "crônica" in base:
        return "cronica"
    if "sinopse" in base:
        return "sinopse"
    if _eh_producao_final_redacao(texto_base, tema):
        return "producao textual"
    return "narrativa"


def _objetivo_pedagogico_redacao(texto_base: str, tema: str, genero: str) -> str:
    base = normalizar_texto_lote(f"{tema} {texto_base}")
    habilidade = "interpretar, analisar e produzir textos"
    if genero == "producao textual" or "revis" in base:
        habilidade = "planejar, revisar, reescrever e aprimorar textos"
    elif genero == "resenha":
        habilidade = "analisar, argumentar e sustentar opinioes sobre uma obra"

    finalidade = "compartilhar leitura, impressoes e posicionamentos com clareza"
    if genero == "resenha":
        finalidade = "recomendar ou nao a obra a leitores da escola, justificando a opiniao"
    elif genero == "cronica":
        finalidade = "relatar uma situacao do cotidiano para provocar identificacao e reflexao"
    elif genero == "sinopse":
        finalidade = "apresentar a obra a leitores da escola de forma objetiva e convidativa"
    elif genero == "producao textual":
        finalidade = "produzir a versao final do texto para circulacao escolar ou envio na plataforma"

    return (
        f"Desenvolver a capacidade de {habilidade}, considerando o genero {genero}, "
        f"escrevendo para os colegas da turma com o objetivo de {finalidade}."
    )


def _perguntas_analise_redacao(genero: str, tema: str) -> list[str]:
    if genero == "resenha":
        return [
            "O que a obra apresentada mostra de mais importante ao leitor?",
            "Que opiniao sobre a obra aparece no texto e como ela foi justificada?",
            "Que elementos fazem esse texto convencer ou nao o leitor a buscar a obra?",
        ]
    if genero == "cronica":
        return [
            "Que situacao cotidiana aparece no texto e como ela se desenvolve?",
            "Como o narrador apresenta o conflito ou desafio vivido?",
            "Que reflexao sobre o cotidiano o texto provoca no leitor?",
        ]
    return [
        f"Quais acontecimentos, informacoes ou ideias centrais aparecem em {tema}?",
        "Como as escolhas de linguagem ajudam o leitor a compreender o texto e seus sentidos?",
        "Que reflexoes, opinioes ou relacoes com o cotidiano essa leitura desperta?",
    ]


def _sistematizacao_redacao(genero: str) -> str:
    if genero == "resenha":
        return (
            "Organizar coletivamente uma lista com os elementos essenciais da resenha: apresentacao da obra, tipo de historia, "
            "opiniao fundamentada, pontos positivos e/ou negativos e recomendacao final."
        )
    if genero == "cronica":
        return (
            "Registrar em esquema os elementos da cronica: narrador, situacao cotidiana, conflito ou desafio, desenvolvimento da narrativa e reflexao final."
        )
    if genero == "sinopse":
        return (
            "Retomar em passo a passo os elementos da sinopse: apresentacao da obra, personagens ou situacao central, tema principal e convite para a leitura."
        )
    return (
        "Organizar coletivamente um esquema com genero textual, finalidade, leitor previsto, estrutura basica e recursos de linguagem que poderao apoiar a escrita."
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


def _seccionar_texto_por_tema(texto: str, tema: str) -> str:
    linhas = texto.splitlines()
    tema_norm = normalizar_texto_lote(tema)
    tema_norm_limpo = re.sub(r'[“"”\'\[\]]', '', tema_norm).strip()
    
    idx_inicio = 0
    for i, linha in enumerate(linhas):
        linha_norm = normalizar_texto_lote(linha)
        linha_norm_limpo = re.sub(r'[“"”\'\[\]]', '', linha_norm).strip()
        if tema_norm_limpo in linha_norm_limpo or (len(tema_norm_limpo) > 5 and tema_norm_limpo[:15] in linha_norm_limpo):
            idx_inicio = i
            break
            
    idx_fim = len(linhas)
    for i in range(idx_inicio + 1, len(linhas)):
        linha_norm = normalizar_texto_lote(linhas[i])
        if "trilha " in linha_norm or "versao final " in linha_norm or "devolutiva " in linha_norm:
            linha_norm_limpo = re.sub(r'[“"”\'\[\]]', '', linha_norm).strip()
            if tema_norm_limpo not in linha_norm_limpo:
                idx_fim = i
                break
                
    return "\n".join(linhas[idx_inicio:idx_fim])


def _extrair_etapas_redacao_leitura(texto: str) -> list[dict]:
    linhas = texto.splitlines()
    etapas = []
    secao_atual = None
    linhas_secao = []
    
    for linha in linhas:
        linha_clean = linha.strip()
        match = re.match(r"^\s*(\d+)\.\s*(.+)$", linha_clean)
        if match:
            if secao_atual:
                etapas.append({
                    "numero": secao_atual["numero"],
                    "titulo": secao_atual["titulo"],
                    "texto": "\n".join(linhas_secao).strip()
                })
            secao_atual = {
                "numero": int(match.group(1)),
                "titulo": match.group(2).strip(),
            }
            linhas_secao = []
        else:
            if secao_atual is not None:
                if linha_clean.isdigit() and len(linha_clean) <= 2:
                    continue
                linhas_secao.append(linha_clean)
                
    if secao_atual:
        etapas.append({
            "numero": secao_atual["numero"],
            "titulo": secao_atual["titulo"],
            "texto": "\n".join(linhas_secao).strip()
        })
        
    return etapas


def _metodologia_leitura_redacao_modelo(texto_base: str, tema: str, turma: str = "") -> list[dict]:
    return gerar_metodologia_redacao_leitura(texto_base, tema, turma=turma)
    genero = _genero_textual_redacao(texto_base, tema)
    objetivo = _objetivo_pedagogico_redacao(texto_base, tema, genero)
    perguntas = _perguntas_analise_redacao(genero, tema)

    # 1. Tentar extrair as etapas do PDF
    etapas_pdf = []
    if texto_base:
        secao = _seccionar_texto_por_tema(texto_base, tema)
        etapas_pdf = _extrair_etapas_redacao_leitura(secao)

    # 2. Gerar a estrutura padrão
    if _eh_producao_final_redacao(texto_base, tema):
        metodologia = [
            {
                "titulo": "Disparo inicial / contextualizacao",
                "texto": (
                    f"Apresentar o tema da aula e explicar que o trabalho sera voltado a finalizacao da producao textual. "
                    f"Retomar o percurso ja vivido pela turma e explicitar o objetivo da aula: {objetivo}"
                ),
            },
            {
                "titulo": "Leitura ou exploracao inicial",
                "texto": (
                    "Orientar releitura guiada do proprio rascunho, com instrucoes claras para observar tema, organizacao das ideias, "
                    "clareza das informacoes, adequacao ao genero textual e dialogo com o leitor."
                ),
            },
            {
                "titulo": "Analise guiada",
                "texto": (
                    "Conduzir perguntas orientadoras para revisar o texto: 1) O texto comunica com clareza a ideia principal? "
                    "2) A organizacao das partes ajuda o leitor a acompanhar a escrita? 3) O que pode ser melhorado para tornar a producao mais completa e adequada ao genero?"
                ),
            },
            {
                "titulo": "Sistematizacao",
                "texto": (
                    "Organizar no quadro um checklist de revisao com criterios obrigatorios: atendimento ao tema, estrutura do genero, paragrafos organizados, pontuacao, conectivos, ortografia e efeito pretendido no leitor."
                ),
            },
            {
                "titulo": "Producao textual",
                "texto": (
                    "Solicitar a escrita da versao final do texto em contexto real de circulacao, como mural da escola, pasta da turma ou plataforma Redacao Paulista. "
                    "Explicar o que escrever, para quem escrever e com qual objetivo, orientando os estudantes a incorporar as melhorias feitas durante a revisao."
                ),
            },
            {
                "titulo": "Revisao e fechamento",
                "texto": (
                    "Finalizar com revisao final em dupla ou individual, retomando o checklist e incentivando adjustments antes da entrega. "
                    "Encerrar com reflexao sobre o que melhorou do rascunho para a versao final e por que revisar faz parte do processo de escrita."
                ),
            },
        ]
    else:
        obra = _obra_literaria_redacao(tema, texto_base)
        metodologia = [
            {
                "titulo": "Disparo inicial / contextualizacao",
                "texto": (
                    f"Apresentar a aula a partir da obra {obra}, conectando o tema ao cotidiano, as experiencias leitoras da turma e o repertorio dos estudantes. "
                    f"Explicar o proposito da atividade e explicitar o objetivo pedagogico: {objetivo}"
                ),
            },
            {
                "titulo": "Leitura ou exploracao inicial",
                "texto": (
                    f"Propor leitura guiada ou exploracao inicial de trechos de {obra}, com foco no genero {genero}, nas personagens, nos acontecimentos e na forma como o texto busca envolver o leitor."
                ),
            },
            {
                "titulo": "Analise guiada",
                "texto": (
                    f"Conduzir perguntas interpretativas e reflexivas: 1) {perguntas[0]} 2) {perguntas[1]} 3) {perguntas[2]}"
                ),
            },
            {
                "titulo": "Sistematizacao",
                "texto": _sistematizacao_redacao(genero),
            },
            {
                "titulo": "Producao textual",
                "texto": (
                    f"Propor uma atividade de escrita em contexto real, como recomendacao para colegas, texto para mural da escola, diario de leitura ou publicacao da turma. "
                    f"Explicar o que escrever, para quem escrever e com qual objetivo, garantindo integracao entre leitura e escrita, incentivando producoes textuais criativas e deixando claros os criterios obrigatorios do genero {genero}."
                ),
            },
            {
                "titulo": "Revisao e fechamento",
                "texto": (
                    "Orientar revisao com checklist de clareza, organizacao, adequacao ao genero, justificativa das opinioes e efeito no leitor. "
                    "Encerrar com socializacao breve e reflexao sobre como a leitura ajudou a produzir um texto mais consciente e melhor elaborado."
                ),
            },
        ]

    # 3. Enriquecimento via PDF desativado para Redação e Leitura.
    # Os PDFs desta disciplina contêm fragmentos de instruções pedagógicas internas
    # (ex: "l Que situações marcaram", "(cid:212) Nível 1 - Compreensão") que,
    # quando extraídos, tornam a metodologia confusa e incoerente.
    # O texto base gerado pelo modelo é completo e correto — não deve ser substituído.
    if False and etapas_pdf:
        mapa_etapas = {i: [] for i in range(6)}
        
        for idx_e, e in enumerate(etapas_pdf):
            t_norm = normalizar_texto_lote(e["titulo"])
            # Usa apenas o texto da etapa (sem o prefixo verboso) para manter
            # a metodologia no tamanho adequado ao modelo de plano.
            texto_completo = e["texto"].strip() if e["texto"].strip() else e["titulo"]
            
            mapped = False
            if any(k in t_norm for k in ["retomada", "prepara", "abertura", "context", "introducao", "disparo"]):
                mapa_etapas[0].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["leitura", "exploracao", "ler"]):
                mapa_etapas[1].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["analise", "pergunta", "discussao", "positivo", "revisao guiada"]):
                mapa_etapas[2].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["sistematizacao", "registro", "roteiro", "esquema", "oportunidade", "melhoria"]):
                mapa_etapas[3].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["producao", "escrita", "escrever", "submissao", "plataforma", "redacao"]):
                mapa_etapas[4].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["fechamento", "revisao", "conclusao", "socializacao", "encerramento"]):
                mapa_etapas[5].append(texto_completo)
                mapped = True
                
            if not mapped:
                total = len(etapas_pdf)
                if total <= 3:
                    seq_map = {0: [0], 1: [1], 2: [1], 3: [2], 4: [2], 5: [2]}
                elif total == 4:
                    seq_map = {0: [0], 1: [1], 2: [1], 3: [2], 4: [2], 5: [3]}
                else:
                    seq_map = {0: [0], 1: [1], 2: [2], 3: [3], 4: [3], 5: [4]}
                
                for b_idx, e_idxs in seq_map.items():
                    if idx_e in e_idxs:
                        mapa_etapas[b_idx].append(texto_completo)

        for i in range(6):
            if mapa_etapas[i]:
                # O conteúdo extraído do PDF substitui o texto base do bloco,
                # evitando acúmulo que tornava a metodologia excessivamente longa.
                metodologia[i]["texto"] = " ".join(mapa_etapas[i])

    return metodologia


def _etapas_por_perfil(perfil: str, tipo: str, texto_base: str = "", tema: str = "") -> list[tuple[str, str]]:
    if perfil == "matematica":
        formato = _detectar_formato_aula_matematica(texto_base, tema)
        if formato == "verificacao":
            return [
                ("Relembre", "para_comecar"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if formato == "pratica_intensiva":
            return [
                ("Para comecar", "para_comecar"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]

        etapas = [
            ("Para comecar", "para_comecar"),
            ("Foco no conteudo", "foco"),
        ]
        if _tem_secao_matematica(texto_base, "pause e responda"):
            etapas.append(("Pause e responda", "pause"))
        etapas.extend(
            [
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        )
        return etapas

    if perfil == "lingua_portuguesa_em":
        return [
            ("Para comecar", "para_comecar"),
            ("Contextualizacao", "contextualizacao"),
            ("Leitura analitica", "leitura_analitica"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "leitura_redacao" and tipo == "producao":
        return [
            ("Para comecar", "para_comecar"),
            ("Leitura e construcao do conteudo", "leitura"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Revisao e reescrita", "encerramento"),
        ]

    if perfil == "educacao_financeira":
        if tipo == "aula_pratica_continuidade":
            return [
                ("Para comecar", "retomada_conceitual"),
                ("Foco no conteudo", "contextualizacao_pratica"),
                ("Na pratica", "atividade_central"),
                ("Encerramento", "encerramento_reflexivo"),
            ]
        etapas = [
            ("Para comecar", "para_comecar"),
            ("Analise de caso", "analise_caso"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
        ]
        base = normalizar_texto_lote(f"{texto_base} {tema}")
        if tipo in {"credito_endividamento", "investimento_poupanca", "analise_percentuais_noticias"} or _contem(base, ["juros", "porcentagem", "parcela", "rendimento", "calculo"]):
            etapas.append(("Calculos financeiros", "calculos"))
        if tipo == "orcamento_planejamento":
            etapas.append(("Planejamento orcamentario", "planejamento"))
        elif tipo == "empreendedorismo":
            etapas.append(("Projeto empreendedor", "projeto"))
        else:
            etapas.append(("Na pratica", "pratica"))
        etapas.append(("Encerramento", "encerramento"))
        return etapas

    return [
        ("Para comecar", "para_comecar"),
        ("Leitura e construcao do conteudo", "leitura"),
        ("Foco no conteudo", "foco"),
        ("Pause e responda", "pause"),
        ("Na pratica", "pratica"),
        ("Encerramento", "encerramento"),
    ]


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
    return ajustada


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
    objetivos: list[str] | None = None,
    conteudos: list[str] | None = None,
    perfil: str = "",
) -> str:
    objetivos = [re.sub(r"\s+", " ", str(x or "")).strip(" .;:-") for x in (objetivos or []) if str(x or "").strip()]
    conteudos = [re.sub(r"\s+", " ", str(x or "")).strip(" .;:-") for x in (conteudos or []) if str(x or "").strip()]

    foco_tema = _foco_limpo_aprendizagem(tema, " ".join(conteudos[:2]))

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

    return _aprendizagem_padrao_por_perfil(tema, perfil, " ".join(conteudos[:2]))


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
        objetivos=objetivos_secao,
        conteudos=conteudos_secao,
        perfil=perfil,
    )
    return _sanitizar_aprendizagem(fallback, tema, conceito, perfil=perfil)


def _fallback_acompanhamento_tema(tema: str, perfil: str) -> list[str]:
    base = normalizar_texto_lote(tema)
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

    def _formatar_item(it: str) -> str:
        it = re.sub(r'^(?:[☑☒☐]|☑|[\u2611\u2612\u2610]|\s|[-*+•]|\[[ xX]\])+\s*', '', it.strip())
        return f"☑ {it}"

    acomp = [_formatar_item(x) for x in acomp if x.strip()]
    acess = [_formatar_item(x) for x in acess if x.strip()]

    fb_acomp = [_formatar_item(x) for x in _fallback_acompanhamento_tema(tema, perfil)]
    fb_acess = [_formatar_item(x) for x in _fallback_acessibilidade_tema(tema, perfil)]

    while len(acomp) < 3:
        idx = len(acomp)
        if idx < len(fb_acomp):
            acomp.append(fb_acomp[idx])
        else:
            acomp.append(fb_acomp[0])

    while len(acess) < 3:
        idx = len(acess)
        if idx < len(fb_acess):
            acess.append(fb_acess[idx])
        else:
            acess.append(fb_acess[0])

    acomp = acomp[:3]
    acess = acess[:3]

    return acomp, acess


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
        metodologia = naturalizar_metodologia_professor(metodologia)
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
) -> dict:
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
) -> dict:
    extracao = _extrator_lib.extrair(texto, tema, disciplina=disciplina_base, numero_aula=numero_aula, turma=turma)
    tipo = _detectar_tipo_aula(extracao.get("texto_prioritario") or texto, tema, disciplina_base, turma=turma)
    habilidade_pdf = extracao.get("habilidade", "")
    objetivos_secao = extracao.get("objetivos_secao") or []
    conteudos_secao = extracao.get("conteudos_secao") or []
    if objetivos_orientacao:
        objetivos_secao = list(objetivos_orientacao)

    if aprendizagem_pv:
        aprendizagem = aprendizagem_pv
    elif perfil == "orientacao_estudos" and aprendizagem_orientacao:
        aprendizagem = aprendizagem_orientacao
        habilidade_pdf = aprendizagem_orientacao
    else:
        aprendizagem = _montar_aprendizagem_inteligente(
            habilidade_pdf=habilidade_pdf or plano_ia.get("aprendizagem", ""),
            tema=tema,
            conceito=extracao.get("conceito_extraido", tema),
            perfil=perfil,
            objetivos_secao=objetivos_secao,
            conteudos_secao=conteudos_secao,
        )

    colunas_planejamento = _tentar_gerador_colunas_pedagogicas(
        texto=texto,
        titulo_aula=material_digital or tema,
        disciplina=disciplina_base,
        turma=turma,
        tema=tema,
        perfil=perfil,
        contexto_metodologico=contexto_metodologico,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        modalidade_eja_ativa=modalidade_eja_ativa,
    )

    metodologia_ia = plano_ia.get("metodologia", [])
    if perfil == "leitura_redacao":
        metodologia_ia = _metodologia_leitura_redacao_modelo(texto, tema, turma=turma)
    if metodologia_ia:
        tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
        if perfil not in {"projeto_de_vida", "lideranca_oratoria"}:
            metodologia_ia = _garantir_tecnicas_lemov_na_metodologia(metodologia_ia, tecnicas_lemov_pdf)
        metodologia_ia = _variar_linguagem_metodologia(metodologia_ia, disciplina_base, turma, tema)
        if perfil != "leitura_redacao":
            metodologia_ia = _ajustar_metodologia_por_sequencia(
                metodologia_ia,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                tema=tema,
            )
        metodologia_ia, _ = revisar_metodologia(
            metodologia_ia,
            perfil=perfil,
            tema=tema,
            contexto=contexto_metodologico,
        )
        metodologia_ia = naturalizar_metodologia_professor(metodologia_ia)
        if modalidade_eja_ativa:
            metodologia_ia = _adaptar_metodologia_eja(
                metodologia_ia,
                perfil,
                tema,
                texto,
                tecnicas_lemov_pdf,
                _garantir_tecnicas_lemov_na_metodologia,
            )

    if metodologia_fixa_pdf:
        metodologia = metodologia_fixa_pdf
        desenvolvimento = _texto_metodologia(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade_pdf, etapas_metodologia=etapas_titulos,
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=extracao.get("recursos_detectados"),
        )
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    elif metodologia_ia:
        metodologia = metodologia_ia
        desenvolvimento = _texto_metodologia(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade_pdf, etapas_metodologia=etapas_titulos,
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=extracao.get("recursos_detectados"),
        )
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    elif colunas_planejamento:
        metodologia = colunas_planejamento["metodologia"]
        if modalidade_eja_ativa:
            tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
            metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_lemov_pdf, _garantir_tecnicas_lemov_na_metodologia)
        acompanhamento = colunas_planejamento["acompanhamento"]
        acessibilidade = colunas_planejamento["acessibilidade"]
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    else:
        metodologia = metodologia_ia
        desenvolvimento = _texto_metodologia(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade_pdf,
            etapas_metodologia=etapas_titulos,
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=extracao.get("recursos_detectados"),
        )
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )

    from core.lib.higienizador_pedagogico import higienizar_plano, detectar_recursos_reais

    recursos_reais = detectar_recursos_reais(texto)
    metodologia, acompanhamento, acessibilidade = higienizar_plano(
        metodologia, acompanhamento, acessibilidade,
        perfil, disciplina_base, tema, recursos_reais
    )

    aula_gerada = {
        "disciplina": disciplina_base,
        "tema": tema,
        "material": material_digital,
        "numero_aula": numero_aula,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
        "acompanhamento": acompanhamento,
        "acessibilidade": acessibilidade,
        "ia_usada": True,
        "ia_provedor": provedor_ia,
        "ia_erro": "",
    }
    aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
    return aula_gerada


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
) -> dict:
    extracao = _extrator_lib.extrair(texto, tema, disciplina=disciplina_base, numero_aula=numero_aula, turma=turma)
    tipo = _detectar_tipo_aula(extracao.get("texto_prioritario") or texto, tema, disciplina_base, turma=turma)
    conceito = extracao.get("conceito_extraido", tema)
    habilidade = extracao.get("habilidade", "")
    recursos = extracao.get("recursos_detectados", [])
    objetivos_secao = extracao.get("objetivos_secao") or []
    conteudos_secao = extracao.get("conteudos_secao") or []
    if objetivos_orientacao:
        objetivos_secao = list(objetivos_orientacao)

    if aprendizagem_pv:
        aprendizagem = aprendizagem_pv
        habilidade = aprendizagem_pv
    elif perfil == "orientacao_estudos" and aprendizagem_orientacao:
        aprendizagem = aprendizagem_orientacao
        habilidade = aprendizagem_orientacao
    else:
        aprendizagem = _montar_aprendizagem_inteligente(
            habilidade_pdf=habilidade,
            tema=tema,
            conceito=conceito,
            perfil=perfil,
            objetivos_secao=objetivos_secao,
            conteudos_secao=conteudos_secao,
        )
    if (
        perfil == "orientacao_estudos"
        and not aprendizagem_orientacao
        and re.search(r"(?i)\betapa\s+(\d+|final)\b", str(tema or "").strip())
    ):
        aprendizagem = (
            f"Desenvolver estrat?gias de leitura, interpreta??o e registro em {tema}, "
            "com foco em autonomia de estudo e resolu??o orientada das atividades."
        )

    colunas_planejamento = _tentar_gerador_colunas_pedagogicas(
        texto=texto,
        titulo_aula=material_digital or tema,
        disciplina=disciplina_base,
        turma=turma,
        tema=tema,
        perfil=perfil,
        contexto_metodologico=contexto_metodologico,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        modalidade_eja_ativa=modalidade_eja_ativa,
    )

    if metodologia_fixa_pdf:
        metodologia = metodologia_fixa_pdf
        desenvolvimento = _texto_metodologia(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade, etapas_metodologia=etapas_titulos,
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=recursos,
        )
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    elif colunas_planejamento:
        metodologia = colunas_planejamento["metodologia"]
        if modalidade_eja_ativa:
            tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
            metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_lemov_pdf, _garantir_tecnicas_lemov_na_metodologia)
        acompanhamento = colunas_planejamento["acompanhamento"]
        acessibilidade = colunas_planejamento["acessibilidade"]
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    else:
        metodologia = _montar_etapas_metodologia(
            texto,
            disciplina_base,
            turma,
            tema,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            contexto_geracao=contexto_geracao,
        )
        tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
        if perfil not in {"projeto_de_vida", "lideranca_oratoria"}:
            metodologia = _garantir_tecnicas_lemov_na_metodologia(metodologia, tecnicas_lemov_pdf)
        metodologia = _variar_linguagem_metodologia(metodologia, disciplina_base, turma, tema)
        metodologia, _ = revisar_metodologia(
            metodologia,
            perfil=perfil,
            tema=tema,
            contexto=contexto_metodologico,
        )
        metodologia = naturalizar_metodologia_professor(metodologia)
        metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_lemov_pdf, _garantir_tecnicas_lemov_na_metodologia) if modalidade_eja_ativa else metodologia

        desenvolvimento = _texto_metodologia(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade, etapas_metodologia=etapas_titulos,
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=recursos,
        )
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )

    from core.lib.higienizador_pedagogico import higienizar_plano, detectar_recursos_reais

    recursos_reais = detectar_recursos_reais(texto)
    metodologia, acompanhamento, acessibilidade = higienizar_plano(
        metodologia, acompanhamento, acessibilidade,
        perfil, disciplina_base, tema, recursos_reais
    )

    aula_gerada = {
        "disciplina": disciplina_base,
        "tema": tema,
        "material": material_digital,
        "numero_aula": numero_aula,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
        "acompanhamento": acompanhamento,
        "acessibilidade": acessibilidade,
        "ia_usada": False,
        "ia_provedor": provedor_ia if usar_ia else "",
        "ia_erro": ia_erro,
    }
    aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
    return aula_gerada


def _preparar_contexto_aula_pdf(
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    bimestre: str,
    indice_aula: int,
    modalidade_eja: bool,
    caminho_pptx_correspondente: str | None = None,
) -> dict:
    texto_pdf = _extrair_texto_pdf(caminho_pdf)
    texto = texto_pdf
    fonte_extracao = "pdf"
    arquivo_fonte_extracao = caminho_pdf
    blocos_pptx = {}

    tema = _tema_por_texto(texto_pdf, caminho_pdf, disciplina)
    material_digital = _material_digital_por_texto(texto_pdf, caminho_pdf, disciplina, tema)
    numero_aula = _rotulo_aula_material(texto_pdf, caminho_pdf).replace("AULA", "", 1).strip()

    usar_pptx = eh_cenario_piloto_pptx(disciplina, turma)
    caminho_pptx = caminho_pptx_correspondente if usar_pptx else None
    if usar_pptx and not caminho_pptx:
        caminho_pptx = encontrar_pptx_correspondente(caminho_pdf, disciplina, turma)

    if usar_pptx and caminho_pptx:
        try:
            estrutura_pptx = extrair_estrutura_pptx(caminho_pptx)
            dados_pptx = estrutura_pptx_para_dados_aula(estrutura_pptx)
            texto = dados_pptx.get("texto_base") or texto_pdf
            tema = dados_pptx.get("tema") or tema
            material_digital = dados_pptx.get("material") or material_digital
            blocos_pptx = dados_pptx.get("blocos_pedagogicos") or {}
            numero_pptx = _rotulo_aula_material(texto, caminho_pdf).replace("AULA", "", 1).strip()
            numero_aula = numero_pptx or numero_aula
            fonte_extracao = "pptx"
            arquivo_fonte_extracao = caminho_pptx
            logger.info("[EXTRACAO] Fonte usada: PPTX")
            logger.info("[EXTRACAO] PPTX correspondente encontrado: %s", caminho_pptx)
        except Exception as exc:
            logger.warning("[EXTRACAO] Falha ao ler PPTX %s: %s", caminho_pptx, exc)
            texto = texto_pdf
            tema = _tema_por_texto(texto_pdf, caminho_pdf, disciplina)
            material_digital = _material_digital_por_texto(texto_pdf, caminho_pdf, disciplina, tema)
            numero_aula = _rotulo_aula_material(texto_pdf, caminho_pdf).replace("AULA", "", 1).strip()
            fonte_extracao = "pdf"
            arquivo_fonte_extracao = caminho_pdf
    else:
        logger.info("[EXTRACAO] Fonte usada: PDF")

    cdp_contextual = eh_cdp_contextual_disciplina(disciplina)
    disciplina_base = disciplina_base_cdp_contextual(texto, tema, caminho_pdf) if cdp_contextual else disciplina
    perfil = perfil_disciplina(disciplina_base, turma=turma)

    from core.lib.aprofundamento import obter_dados_aprofundamento
    dados_plan = obter_dados_aprofundamento(disciplina_base, numero_aula, turma=turma)
    if dados_plan and dados_plan.get("titulo"):
        tema = dados_plan["titulo"]
        material_digital = f"AULA {numero_aula} - {tema}"

    if perfil == "orientacao_estudos":
        texto, tema, material_digital = _resolver_contexto_orientacao_estudos(
            caminho_pdf=caminho_pdf,
            texto=texto,
            tema=tema,
            material_digital=material_digital,
            indice_aula=indice_aula,
        )

    objetivos_orientacao = (
        buscar_objetivos_orientacao_estudos(caminho_pdf=caminho_pdf, tema=tema)
        if perfil == "orientacao_estudos"
        else []
    )
    aprendizagem_orientacao = formatar_objetivos_orientacao_estudos(objetivos_orientacao)
    extracao_pdf = _extrator_lib.extrair(texto, tema, disciplina=disciplina_base, numero_aula=numero_aula, turma=turma)
    texto_prioritario_pdf = extracao_pdf.get("texto_prioritario") or texto
    tipo = _detectar_tipo_aula(texto_prioritario_pdf, tema, disciplina_base, turma=turma)
    metodologia_fixa_pdf = _metodologia_fixa_pdf_especial(texto, disciplina_base, tema)
    if not metodologia_fixa_pdf and fonte_extracao == "pptx":
        metodologia_fixa_pdf = _metodologia_por_blocos_estruturados(blocos_pptx)
    modalidade_eja_ativa = bool(modalidade_eja and _perfil_suporta_eja(perfil))
    from core.disciplinas import eh_cdp
    eh_cdp_real = (
        eh_cdp_contextual_disciplina(disciplina)
        or eh_cdp(disciplina)
        or detectar_contexto_metodologico(texto, caminho_pdf, disciplina_base, turma) == "cdp_eja"
    )
    if eh_cdp_real:
        contexto_metodologico = "cdp_eja"
    elif modalidade_eja_ativa:
        contexto_metodologico = "eja_regular"
    else:
        contexto_metodologico = "regular"
    escopo_pv = buscar_item_projeto_vida(turma, bimestre, numero_aula) if perfil == "projeto_de_vida" else {}
    aprendizagem_pv = montar_aprendizagem_projeto_vida(escopo_pv) if escopo_pv else ""
    if escopo_pv.get("titulo"):
        tema = escopo_pv["titulo"]
        material_digital = f"AULA {int(numero_aula)} - {tema}" if numero_aula.isdigit() else tema

    return {
        "texto": texto,
        "tema": tema,
        "material_digital": material_digital,
        "numero_aula": numero_aula,
        "cdp_contextual": cdp_contextual,
        "disciplina_base": disciplina_base,
        "perfil": perfil,
        "objetivos_orientacao": objetivos_orientacao,
        "aprendizagem_orientacao": aprendizagem_orientacao,
        "extracao_pdf": extracao_pdf,
        "tipo": tipo,
        "metodologia_fixa_pdf": metodologia_fixa_pdf,
        "modalidade_eja_ativa": modalidade_eja_ativa,
        "contexto_metodologico": contexto_metodologico,
        "escopo_pv": escopo_pv,
        "aprendizagem_pv": aprendizagem_pv,
        "fonte_extracao": fonte_extracao,
        "arquivo_fonte_extracao": arquivo_fonte_extracao,
    }
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

    fingerprint_atual = montar_fingerprint_contexto(
        hash_pdf=hash_atual,
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
    if caminho_pdf:
        try:
            import json
            from pathlib import Path
            caminho_json = Path(caminho_pdf).with_suffix(".json")
            if caminho_json.exists():
                with open(caminho_json, "r", encoding="utf-8") as f:
                    dados_json = json.load(f)
                if isinstance(dados_json, dict) and "metodologia" in dados_json:
                    dados_json_antigos = dados_json
                    hash_salvo = dados_json.get("hash_pdf")
                    hash_fonte_salva = dados_json.get("hash_fonte_extracao") or ""
                    versao_cache = str(dados_json.get("versao_gerador") or "")
                    fonte_cache = str(dados_json.get("fonte_extracao") or "pdf").lower()
                    arquivo_cache = str(dados_json.get("arquivo_fonte_extracao") or caminho_pdf)
                    fingerprint_salvo = dados_json.get("fingerprint_contexto")

                    if hash_salvo and hash_atual and hash_salvo != hash_atual:
                        pass
                    elif caminho_pptx_correspondente and fonte_cache != "pptx":
                        pass
                    elif caminho_pptx_correspondente and Path(arquivo_cache) != Path(caminho_pptx_correspondente):
                        pass
                    elif caminho_pptx_correspondente and hash_fonte_extracao_esperada and hash_fonte_salva != hash_fonte_extracao_esperada:
                        pass
                    elif not caminho_pptx_correspondente and fonte_cache == "pptx":
                        pass
                    elif versao_cache != VERSAO_GERADOR_ATUAL:
                        pass
                    elif fingerprint_salvo != fingerprint_atual:
                        perfil_disc = perfil_disciplina(disciplina, turma=turma)
                        if perfil_disc in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
                            pass
                        else:
                            # Para outras disciplinas, não invalidamos o cache apenas pelo fingerprint
                            aula_gerada = {
                                "disciplina": dados_json.get("disciplina") or disciplina,
                                "tema": dados_json.get("tema") or "",
                                "material": dados_json.get("material") or Path(caminho_pdf).name,
                                "numero_aula": dados_json.get("numero_aula") or "",
                                "aprendizagem": dados_json.get("aprendizagem") or "",
                                "metodologia": dados_json["metodologia"],
                                "acompanhamento": dados_json.get("acompanhamento") or [],
                                "acessibilidade": dados_json.get("acessibilidade") or [],
                                "ia_usada": dados_json.get("ia_usada", False),
                                "ia_provedor": dados_json.get("ia_provedor", ""),
                                "ia_erro": dados_json.get("ia_erro", ""),
                                "hash_pdf": hash_salvo or hash_atual,
                                "fonte_extracao": fonte_cache,
                                "arquivo_fonte_extracao": arquivo_cache,
                                "hash_fonte_extracao": hash_fonte_salva,
                                "confidence_score": dados_json.get("confidence_score", 100),
                                "avisos_validacao": dados_json.get("avisos_validacao") or [],
                                "fingerprint_contexto": fingerprint_salvo,
                                "versao_gerador": versao_cache,
                            }
                            if "avisos_validacao" not in dados_json:
                                aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
                            return aula_gerada
                    else:
                        aula_gerada = {
                            "disciplina": dados_json.get("disciplina") or disciplina,
                            "tema": dados_json.get("tema") or "",
                            "material": dados_json.get("material") or Path(caminho_pdf).name,
                            "numero_aula": dados_json.get("numero_aula") or "",
                            "aprendizagem": dados_json.get("aprendizagem") or "",
                            "metodologia": dados_json["metodologia"],
                            "acompanhamento": dados_json.get("acompanhamento") or [],
                            "acessibilidade": dados_json.get("acessibilidade") or [],
                            "ia_usada": dados_json.get("ia_usada", False),
                            "ia_provedor": dados_json.get("ia_provedor", ""),
                            "ia_erro": dados_json.get("ia_erro", ""),
                            "hash_pdf": hash_salvo or hash_atual,
                            "fonte_extracao": fonte_cache,
                            "arquivo_fonte_extracao": arquivo_cache,
                            "hash_fonte_extracao": hash_fonte_salva,
                            "confidence_score": dados_json.get("confidence_score", 100),
                            "avisos_validacao": dados_json.get("avisos_validacao") or [],
                            "fingerprint_contexto": fingerprint_salvo,
                            "versao_gerador": versao_cache,
                        }
                        if "avisos_validacao" not in dados_json:
                            aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
                        return aula_gerada
        except Exception:
            pass

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

    resultado_final["fonte_extracao"] = fonte_extracao
    resultado_final["arquivo_fonte_extracao"] = arquivo_fonte_extracao
    resultado_final["hash_fonte_extracao"] = hash_fonte_extracao_esperada or hash_atual
    resultado_final["fingerprint_contexto"] = fingerprint_atual
    resultado_final["versao_gerador"] = VERSAO_GERADOR_ATUAL

    try:
        from core.revisao_final import revisar_aula_gerada, gravar_sidecar_json
        resultado_final = revisar_aula_gerada(resultado_final, perfil)
        if caminho_pdf and hash_atual:
            gravar_sidecar_json(caminho_pdf, resultado_final, hash_atual)
    except Exception:
        pass

    return resultado_final


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
    aulas = []
    total_aulas = len(caminhos_pdf or [])
    for idx, caminho in enumerate(caminhos_pdf or []):
        if progress_callback:
            try:
                progress_callback(idx, total_aulas, caminho)
            except Exception:
                pass
        dividir_aula_atual = bool(dividir_por_pdf[idx]) if dividir_por_pdf and idx < len(dividir_por_pdf) else dividir_metodologia
        import inspect
        sig = inspect.signature(_aula_por_pdf)
        kwargs = {}
        if "professor" in sig.parameters:
            kwargs["professor"] = professor
        if "dividir_aula_atual" in sig.parameters:
            kwargs["dividir_aula_atual"] = dividir_aula_atual
        aula = _aula_por_pdf(
            caminho,
            disciplina,
            turma,
            bimestre,
            usar_ia,
            provedor_ia,
            modelo_ia,
            indice_aula=idx,
            total_aulas=total_aulas,
            modalidade_eja=modalidade_eja,
            **kwargs
        )
        if dividir_aula_atual:
            texto = _texto_metodologia(aula["metodologia"])
            parte1, parte2 = processar_pdf_e_dividir_metodologia(texto)
            aula_primeiro = dict(aula)
            aula_primeiro["metodologia"] = _metodologia_em_blocos_por_texto(parte1)

            aula_segundo = dict(aula)
            aula_segundo["tema"] = f"{aula['tema']} - continuidade"
            aula_segundo["metodologia"] = _metodologia_em_blocos_por_texto(parte2)

            aulas.extend([aula_primeiro, aula_segundo])
        else:
            aulas.append(aula)
    return aulas
