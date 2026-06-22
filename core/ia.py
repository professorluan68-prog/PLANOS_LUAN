import json
import os
import re
from typing import Any

from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from config import IA_TIMEOUT_SEGUNDOS, MODELO_GEMINI_PADRAO
from core.lib.classificador import normalizar_texto, perfil_disciplina
from core.prompts_por_disciplina import get_orientacao_disciplina, get_system_prompt
from core.qualidade_metodologica import (
    detectar_contexto_metodologico,
    detectar_nivel_ensino,
    extrair_conceito_central,
    naturalizar_metodologia_professor,
    regras_consolidadas_para_prompt,
    revisar_metodologia,
    titulo_esta_truncado,
)
from core.referencias_metodologia import carregar_referencia_metodologica


class EtapaMetodologia(BaseModel):
    titulo: str = Field(description="Titulo da etapa, como Relembre, Foco no conteudo, Na pratica ou Encerramento.")
    texto: str = Field(description="Texto descritivo com a acao do professor e os recursos utilizados.")


class PlanoAulaIA(BaseModel):
    tema: str = Field(description="Conceito central da aula, sem rotulos administrativos como AULA 1 ou bimestre.")
    aprendizagem: str = Field(description="Aprendizagem essencial e/ou codigo da BNCC encontrado no slide.")
    metodologia: list[EtapaMetodologia] = Field(description="Etapas de desenvolvimento da aula.")


_FRASES_PROIBIDAS = (
    "Relacionar a explicação aos registros anteriores para que a turma perceba continuidade, aprofundamento e novos desafios.",
    "O docente apresenta",
    "Conduzir uma discussão final onde",
    "Ressalte a importância",
    "Foco no conteúdo",
)

_CORRECOES_PONTUAIS = {
    "proxima": "próxima",
    "sequencia": "sequência",
    "conducao": "condução",
    "visiveis": "visíveis",
    "mantem": "mantém",
    "avancos": "avanços",
}

_FINS_INCOMPLETOS_APRENDIZAGEM_IA = {
    "a", "as", "o", "os", "um", "uma", "de", "da", "das", "do", "dos",
    "em", "e", "com", "para", "por", "que",
}


def _aprendizagem_padrao_projeto_vida(tema: str) -> str:
    foco = extrair_conceito_central(tema) or "o tema da aula"
    if re.sub(r"\s+", " ", foco.lower()).strip() == "o tema da aula":
        foco = re.sub(r"\s+", " ", str(tema or "")).strip(" .:-") or "o ambiente digital"
    base = re.sub(r"\s+", " ", foco.lower()).strip()
    if any(termo in base for termo in ["post", "postar", "public", "print", "rede", "digital", "internet", "online"]):
        return (
            f"Refletir sobre {foco}, analisando escolhas, exposicao, respeito, responsabilidade e "
            "consequencias das acoes no ambiente digital."
        )
    return (
        f"Refletir sobre {foco}, relacionando o tema a escolhas, atitudes, convivencia respeitosa, "
        "autoconhecimento e tomada de decisao responsavel."
    )


def _extrair_codigo_bncc(texto: str) -> str:
    match = re.search(r"\(([A-Za-z]{2}\d+[A-Za-z0-9]*)\)", str(texto or ""))
    return f"({match.group(1).upper()})" if match else ""


def _aplicar_codigo_bncc(codigo: str, texto: str) -> str:
    texto_limpo = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto_limpo:
        return ""
    if codigo:
        return f"Habilidade: {codigo} {texto_limpo}"
    return texto_limpo


def _aprendizagem_fallback_por_perfil(perfil: str, tema: str, codigo: str = "") -> str:
    foco = extrair_conceito_central(tema)
    foco_norm = normalizar_texto(foco).lower()
    is_comando = (
        any(foco_norm.startswith(v) for v in ["observe", "leia", "responda", "analise", "assista", "copie", "preencha", "complete"])
        or any(k in foco_norm for k in ["perguntas propostas", "propostas no material", "de olho no material", "no caderno"])
        or len(foco.split()) > 8
    )
    if is_comando or not foco:
        foco = "o tema da aula"
    else:
        foco = re.sub(r"\s+", " ", str(foco)).strip(" .:-")

    if perfil in {"projeto_de_vida", "lideranca_oratoria"}:
        return _aplicar_codigo_bncc(codigo, _aprendizagem_padrao_projeto_vida(foco))
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return _aplicar_codigo_bncc(
            codigo,
            f"Analisar textos e linguagens relacionados a {foco}, desenvolvendo leitura, interpretacao, analise da linguagem e producao de sentidos de acordo com as propostas da aula.",
        )
    if perfil == "historia":
        return _aplicar_codigo_bncc(
            codigo,
            f"Analisar sujeitos, contextos, permanencias e mudancas relacionados a {foco}, utilizando fontes, registros e argumentos historicos para sustentar as interpretacoes construidas na aula.",
        )
    if perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        return _aplicar_codigo_bncc(
            codigo,
            f"Compreender e explicar aspectos relacionados a {foco}, articulando observacao, conceitos cientificos, leitura de esquemas e registro das evidencias trabalhadas na aula.",
        )
    if perfil == "geografia":
        return _aplicar_codigo_bncc(
            codigo,
            f"Analisar aspectos relacionados a {foco}, relacionando territorio, sociedade, natureza e leitura de diferentes linguagens geograficas ao longo da aula.",
        )
    if perfil == "educacao_financeira":
        if any(k in foco_norm for k in ["credito", "endividamento", "divida", "dividas", "emprestimo", "financiamento", "juros", "parcel"]):
            return _aplicar_codigo_bncc(
                codigo,
                f"Analisar situacoes relacionadas a {foco}, comparando custos, prazos, riscos e impactos no orcamento antes de tomar decisoes financeiras mais conscientes.",
            )
        if any(k in foco_norm for k in ["poupanca", "reserva", "investimento", "rendimento", "imprevisto"]):
            return _aplicar_codigo_bncc(
                codigo,
                f"Compreender como poupanca, reserva e planejamento de longo prazo se relacionam a {foco}, analisando possibilidades de organizacao financeira e protecao diante de imprevistos.",
            )
        if any(k in foco_norm for k in ["consumo", "preco", "cesta basica", "simulador", "simuladores", "energia", "agua", "gas", "internet", "necessidade", "desejo"]):
            return _aplicar_codigo_bncc(
                codigo,
                f"Analisar escolhas de consumo relacionadas a {foco}, comparando precos, necessidades, gastos fixos e variaveis e seus efeitos no orcamento familiar.",
            )
        if any(k in foco_norm for k in ["orcamento", "planejamento", "receita", "despesa", "gasto", "saldo", "planner", "meta"]):
            return _aplicar_codigo_bncc(
                codigo,
                f"Compreender como receitas, despesas, prioridades e metas interferem em {foco}, analisando dados, comparando escolhas e registrando estrategias de planejamento financeiro.",
            )
        return _aplicar_codigo_bncc(
            codigo,
            f"Compreender conceitos de educacao financeira relacionados a {foco}, articulando organizacao do orcamento, analise de dados e tomada de decisao responsavel.",
        )

    return _aplicar_codigo_bncc(
        codigo,
        f"Compreender e analisar conceitos relacionados a {foco}, articulando leitura, discussao orientada e registro das ideias centrais trabalhadas na aula.",
    )


def _serializar_modelo(objeto: Any) -> dict:
    if hasattr(objeto, "model_dump"):
        return objeto.model_dump()
    if hasattr(objeto, "dict"):
        return objeto.dict()
    return dict(objeto)


def _limpar_json_markdown(texto: str) -> str:
    texto = str(texto or "").strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    return texto


def _serializar_rascunho_base(rascunho_base: dict | None) -> str:
    if not isinstance(rascunho_base, dict):
        return ""

    linhas = []
    tema = str(rascunho_base.get("tema") or "").strip()
    aprendizagem = str(rascunho_base.get("aprendizagem") or "").strip()
    metodologia = rascunho_base.get("metodologia") or []

    if tema:
        linhas.append(f"Tema base: {tema}")
    if aprendizagem:
        linhas.append(f"Aprendizagem base: {aprendizagem}")

    blocos_metodologia = []
    for item in metodologia:
        if not isinstance(item, dict):
            continue
        titulo = str(item.get("titulo") or "").strip() or "Etapa"
        texto = re.sub(r"\s+", " ", str(item.get("texto") or "")).strip()
        if texto:
            blocos_metodologia.append(f"- {titulo}: {texto}")

    if blocos_metodologia:
        linhas.append("Metodologia base:")
        linhas.extend(blocos_metodologia[:6])

    return "\n".join(linhas).strip()[:2500]


def _extrair_json_openai(response) -> dict:
    mensagem = response.choices[0].message
    parsed = getattr(mensagem, "parsed", None)
    if parsed is not None:
        return _serializar_modelo(parsed)
    texto = _limpar_json_markdown(mensagem.content)
    return json.loads(texto or "{}")


def _montar_prompt(
    texto_pdf: str,
    disciplina: str,
    turma: str,
    modalidade_eja: bool = False,
    permitir_tecnicas_explicitamente: bool = True,
    rascunho_base: dict | None = None,
    contexto_geracao: dict | None = None,
) -> str:
    perfil = perfil_disciplina(f"{disciplina} {turma}")
    contexto = "eja_regular" if modalidade_eja else detectar_contexto_metodologico(texto_pdf, disciplina=disciplina, turma=turma)
    nivel = detectar_nivel_ensino(turma=turma, disciplina=disciplina, texto_pdf=texto_pdf)
    orientacao = get_orientacao_disciplina(disciplina, turma=turma)
    referencia = carregar_referencia_metodologica(disciplina, turma)
    bloco_referencia = f"\n\nREFERENCIA METODOLOGICA DA DISCIPLINA:\n{referencia[:4200]}" if referencia else ""
    bloco_rascunho = ""
    rascunho_serializado = _serializar_rascunho_base(rascunho_base)
    if rascunho_serializado:
        bloco_rascunho = f"""

RASCUNHO LOCAL DO SISTEMA:
{rascunho_serializado}

USE O RASCUNHO LOCAL COMO BASE DE REFINAMENTO:
- Preserve o foco conceitual e a sequencia pedagogica do rascunho quando estiverem coerentes com o PDF.
- Melhore a especificidade, a naturalidade e a clareza do texto, sem inventar conteudos fora do material.
- Corrija trechos genericos do rascunho apenas quando o PDF trouxer pistas concretas para isso.
- Se o rascunho ja estiver adequado, faca apenas um ajuste fino de linguagem.
"""
    bloco_eja = ""
    if modalidade_eja:
        bloco_eja = """

MODALIDADE EJA:
- Escreva para Educacao de Jovens e Adultos, com linguagem acessivel, adulta, objetiva e respeitosa.
- Contextualize os conceitos em situacoes de vida, trabalho, saude, tecnologia, comunidade e cotidiano.
- Explique de forma pausada e dialogada, retomando vocabulario essencial sem infantilizar os estudantes.
- Em Biologia e Ingles, mantenha os blocos "Para comecar", "Foco no conteudo", "Pause e responda" e "Encerramento" sempre que o material permitir.
- Preserve tecnicas explicitas do PDF quando isso fizer parte do modelo da disciplina.
"""

    bloco_leitura_redacao = ""

    if perfil == "leitura_redacao":
        bloco_leitura_redacao = """

MODELO ESPECIFICO DE REDACAO E LEITURA:
- Priorize genero textual, objetivo pedagogico e funcao social da escrita.
- Use sempre 6 etapas fixas, nesta ordem: "Disparo inicial / contextualizacao", "Leitura ou exploracao inicial", "Analise guiada", "Sistematizacao", "Producao textual" e "Revisao e fechamento".
- Para trilha literaria/leitura de obra, articule leitura literaria, impressoes dos estudantes, personagens, acontecimentos, hipotese/predicao e conexao com producao textual.
- Para aula de producao textual/finalizacao, mantenha a mesma estrutura de 6 etapas, mas direcione a exploracao inicial para releitura do rascunho, a sistematizacao para checklist de revisao e a producao textual para versao final/submissao.
- Na analise guiada, inclua ao menos tres perguntas orientadoras: compreensao, interpretacao e reflexao.
- Na producao textual, explicite sempre o que escrever, para quem escrever e com qual objetivo.
- Para resenha, incluir apresentacao da obra, tipo de historia, opiniao, pontos positivos/negativos e recomendacao final.
- Para cronica, incluir narrador em primeira pessoa, situacao cotidiana, conflito/desafio e reflexao final.
- Nunca entregar apenas resumo; integrar leitura e escrita com linguagem clara, didatica e aplicavel em sala.
"""

    regra_tecnicas = ""
    if perfil in {"projeto_de_vida", "lideranca_oratoria"}:
        regra_tecnicas = "5. Nao cite tecnicas LEMOV nem nomes como VIREM E CONVERSEM, TODO MUNDO ESCREVE, COM SUAS PALAVRAS, HORA DA LEITURA, DE OLHO NO MODELO, PAUSE E RESPONDA ou UM PASSO DE CADA VEZ. Substitua por descricoes pedagogicas naturais, acolhedoras e coerentes com Projeto de Vida."
    elif permitir_tecnicas_explicitamente:
        regra_tecnicas = '5. Se o slide trouxer tecnicas pedagogicas explicitas, especialmente tecnicas LEMOV como "VIREM E CONVERSEM", "TODO MUNDO ESCREVE", "COM SUAS PALAVRAS", "HORA DA LEITURA", "DE OLHO NO MODELO", "PAUSE E RESPONDA" ou "UM PASSO DE CADA VEZ", cite o nome da tecnica em maiusculas dentro da acao docente de forma direta e natural, SEM usar a palavra "tecnica" ou "a tecnica" para nao soar repetitivo. Ex.: "Aplicar o VIREM E CONVERSEM para que os estudantes levantem hipoteses iniciais" e "Utilizar o TODO MUNDO ESCREVE para garantir o registro individual".'
    else:
        regra_tecnicas = "5. Nao cite tecnicas LEMOV nem nomes como VIREM E CONVERSEM, TODO MUNDO ESCREVE, COM SUAS PALAVRAS, HORA DA LEITURA, DE OLHO NO MODELO, PAUSE E RESPONDA ou UM PASSO DE CADA VEZ. Substitua por descricoes pedagogicas genericas e naturais."

    bloco_variacao = ""
    if contexto_geracao and (contexto_geracao.get("perfil_metodologico") or contexto_geracao.get("tipo_aula")):
        perfil_sel = contexto_geracao.get("perfil_metodologico", "LEITURA INVESTIGATIVA")
        tipo_aula = contexto_geracao.get("tipo_aula", "simples")
        bloco_variacao = f"""
CONTEXTO DE VARIAÇÃO METODOLÓGICA:
- Perfil selecionado: {perfil_sel}
- Organização da aula: {tipo_aula}
- Esta metodologia deve manter o conteúdo do PDF, mas apresentar percurso pedagógico próprio.
- Não copie literalmente o rascunho.
- Não altere apenas verbos ou sinônimos.
- Varie ações concretas, agrupamento, forma de leitura, registro, socialização e encerramento.
- Não invente recursos ausentes do material.
- Preserve textos, fragmentos, imagens, vídeos e atividades realmente identificados.
- Não mencione o nome do professor na metodologia.
"""

    return f"""Voce e um especialista em planejamento pedagogico. Extraia as informacoes do slide abaixo.
DISCIPLINA: {disciplina}
TURMA: {turma}
PERFIL METODOLOGICO: {perfil}
CONTEXTO: {contexto}
NIVEL: {nivel}
{bloco_eja}
{bloco_leitura_redacao}

{orientacao}

{regras_consolidadas_para_prompt(perfil, contexto, nivel)}
{bloco_rascunho}

REGRAS:
1. Extraia o conceito central da aula. Nao devolva rotulos como "AULA 1", "2o bimestre", "Ensino Fundamental" ou "Parte 1" como tema principal.
2. Identifique o codigo da BNCC e a descricao da aprendizagem essencial se houver.
3. Elabore a metodologia em 4 a 6 etapas curtas e objetivas. Para Biologia e Ciencias, prefira os blocos "Para comecar", "Foco no conteudo", "Pause e responda" e "Encerramento" quando forem coerentes com o material.
3.1. Nao narre a aula inteira e nao repita os slides; escreva como plano de aula sintetico.
3.2. Limite o desenvolvimento total a cerca de 900 caracteres.
3.3. Preserve o produto real da atividade do material (ex.: texto-sintese, tabela, legenda de figura, resumo, respostas no livro). Nao troque o produto por outro formato.
4. Varie os inicios das frases entre as etapas e entre aulas diferentes, mantendo linguagem natural, objetiva e pedagogica.
{regra_tecnicas}
6. Devolva APENAS JSON valido seguindo a estrutura solicitada.
7. Evite frases genericas/repetitivas e trechos incompletos.
{bloco_referencia}
{bloco_variacao}

CONTEUDO DO SLIDE:
{texto_pdf[:6000]}
"""


def _detectar_produto_atividade(texto_pdf: str) -> str:
    base = re.sub(r"\s+", " ", str(texto_pdf or "")).lower()
    detectores_diretos = [
        (r"\blivro do estudante\b|\bresponda(?:m)? no livro\b|\bregistre(?:m)? (?:as )?respostas? no livro\b|\batividades? no livro\b", "respostas no livro"),
        (r"\bregistro(?:s)? escrito(?:s)?\b|\bregistre(?:m)? por escrito\b|\bresponda(?:m)? por escrito\b", "registro escrito"),
        (r"\bmodelo tridimensional\b|\bconstr(?:ua|uir|ucao|u[cç][aã]o) de um modelo\b|\bcaixa lunar\b|\bmaquete\b", "modelo explicativo"),
        (r"\bencenacao\b|\brepresentacao do sistema\b|\bcena original\b", "representacao do fenomeno"),
    ]
    for padrao, rotulo in detectores_diretos:
        if re.search(padrao, base, flags=re.I):
            return rotulo
    padroes = [
        (r"texto[-\s]?s[ií]ntese|s[ií]ntese individual", "texto-síntese"),
        (r"\btabela\b", "tabela"),
        (r"legenda\s+de\s+figura|legendar\s+(?:a\s+)?figura|legendar\s+(?:a\s+)?imagem|legende\s+(?:a\s+)?figura|legende\s+(?:a\s+)?imagem|\blegenda\s+da\s+figura\b|\blegenda\s+da\s+imagem\b", "legenda de figura"),
        (r"\bresumo\b", "resumo"),
        (r"todo mundo escreve|na pr[aá]tica|veja no livro|pause e responda|hora da leitura", "atividade do material"),
    ]
    for padrao, rotulo in padroes:
        if re.search(padrao, base, flags=re.I):
            return rotulo
    return ""


def _frase_produto_atividade(produto: str) -> str:
    produto_limpo = str(produto or "").strip()
    if not produto_limpo:
        return "realizem a atividade principal"

    frases = {
        "respostas no livro": "registrem respostas no livro",
        "registro escrito": "organizem um registro escrito",
        "modelo explicativo": "construam um modelo explicativo",
        "representacao do fenomeno": "elaborem uma representacao do fenomeno",
    }
    return frases.get(produto_limpo, f"produzam {produto_limpo}")


def _limpar_texto_curto(texto: str) -> str:
    saida = re.sub(r"\s+", " ", str(texto or "")).strip()
    saida = re.sub(r"\b(?:por|de|com|para)\s*\.$", ".", saida, flags=re.I)
    saida = re.sub(r"esta atividade deve durar cerca de\.?", "", saida, flags=re.I).strip(" .")
    for errado, certo in _CORRECOES_PONTUAIS.items():
        saida = re.sub(rf"\b{errado}\b", certo, saida, flags=re.I)
    saida = re.sub(r"\bIniciar com uma pausa de para que\b", "Iniciar com uma pausa breve para que", saida, flags=re.I)
    saida = re.sub(
        r"\bAssistir a um material impresso, quadro e registro no caderno sobre\b",
        "Analisar com a turma um esquema e os registros no caderno sobre",
        saida,
        flags=re.I,
    )
    saida = re.sub(
        r"\bAssistir a um material impresso, quadro e registro no caderno\b",
        "Analisar com a turma um esquema e os registros no caderno",
        saida,
        flags=re.I,
    )
    padroes_bloqueio = [
        r"relacionar a explica.*?continuidade,\s*aprofundamento e novos desafios\.?",
        r"o docente apresenta",
        r"conduzir uma discuss.*?final onde",
        r"ressalte a import[aâ]ncia",
        r"foco no conte[uú]do",
    ]
    for padrao in padroes_bloqueio:
        saida = re.sub(padrao, "", saida, flags=re.I)
    return re.sub(r"\s+", " ", saida).strip(" .")


def _aprendizagem_ia_invalida(texto: str, tema: str) -> bool:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return True
    normalizado = re.sub(r"\s+", " ", texto.lower()).strip()
    if texto.endswith((",", ";", ":", "/", "-")):
        return True
    if texto.count("?") >= 2 or re.match(r"^(?:o que|como|por que|qual)\b", normalizado):
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    if palavras and palavras[-1].lower() in _FINS_INCOMPLETOS_APRENDIZAGEM_IA:
        return True
    tema_norm = extrair_conceito_central(tema).lower()
    marcadores_genericos = (
        "desenvolver habilidades relacionadas ao tema",
        "compreender o tema da aula",
        "conteudo da aula",
    )
    return len(texto) > 700 or (len(texto) < 28 and not tema_norm) or any(m in normalizado for m in marcadores_genericos)


_FINS_INCOMPLETOS_METODOLOGIA_IA = {
    "a",
    "as",
    "o",
    "os",
    "um",
    "uma",
    "uns",
    "umas",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "e",
    "em",
    "para",
    "por",
    "com",
    "sem",
    "sobre",
    "entre",
    "como",
    "que",
    "onde",
    "quando",
    "qual",
    "quais",
    "ao",
    "aos",
    "no",
    "na",
    "nos",
    "nas",
    "pelo",
    "pela",
    "pelos",
    "pelas",
    "seu",
    "sua",
    "seus",
    "suas",
}


def _termina_com_trecho_incompleto(texto: str) -> bool:
    texto_limpo = re.sub(r"\s+", " ", str(texto or "")).strip(" .,:;!?-")
    if not texto_limpo:
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto_limpo)
    if not palavras:
        return True
    ultimas = [p.lower() for p in palavras[-4:]]
    if ultimas[-1] in _FINS_INCOMPLETOS_METODOLOGIA_IA:
        return True
    final = " ".join(ultimas)
    if re.search(
        r"\b(?:onde|quando|que|para|com|sobre)\s+(?:(?:o|a|os|as|um|uma)\s+)?(?:alunos|estudantes)?$",
        final,
    ):
        return True
    if len(ultimas) >= 2 and re.search(r"(?:ando|endo|indo)$", ultimas[-2]):
        return True
    return False


def _finalizar_trecho_metodologia(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip(" ,;:-")
    if not texto or _termina_com_trecho_incompleto(texto):
        return ""
    if texto.endswith((".", "!", "?")):
        return texto
    return texto + "."


_INICIOS_FRAGMENTADOS = (
    "que os", "que as", "que cada", "que todos", "que o", "que a",
    "para que", "fazendo com que", "garantindo que", "de forma que",
    "solicitando que", "pedindo que", "orientando que",
    "garantir o", "garantir a", "garantir os", "garantir as",
    "garantir que", "promover a", "promover o", "oferecer a", "oferecer o"
)


def _inicio_fragmentado(texto: str) -> bool:
    """Verifica se o texto começa com uma oração subordinada sem verbo principal."""
    texto_lower = texto.strip().lower()
    return any(texto_lower.startswith(inicio) for inicio in _INICIOS_FRAGMENTADOS)


def _cortar_sem_quebrar_frase(texto: str, limite: int) -> str:
    texto = _limpar_texto_curto(texto)
    if not texto or limite <= 0:
        return ""
    if len(texto) <= limite:
        resultado = _finalizar_trecho_metodologia(texto)
        return "" if _inicio_fragmentado(resultado) else resultado

    recorte = texto[:limite].rstrip()
    fim_frase = max(recorte.rfind("."), recorte.rfind("!"), recorte.rfind("?"))
    if fim_frase >= max(45, int(limite * 0.45)):
        resultado = _finalizar_trecho_metodologia(recorte[: fim_frase + 1])
        return "" if _inicio_fragmentado(resultado) else resultado

    fim_oracao = max(recorte.rfind(";"), recorte.rfind(":"))
    if fim_oracao >= max(45, int(limite * 0.55)):
        resultado = _finalizar_trecho_metodologia(recorte[:fim_oracao])
        return "" if _inicio_fragmentado(resultado) else resultado

    fim_virgula = recorte.rfind(",")
    if fim_virgula >= max(60, int(limite * 0.65)):
        resultado = _finalizar_trecho_metodologia(recorte[:fim_virgula])
        return "" if _inicio_fragmentado(resultado) else resultado
    return ""


def _posicao_atividade(itens: list, perfil: str) -> int:
    """Retorna a posição correta para inserção da etapa Atividade."""
    titulos = [normalizar_texto(i.get("titulo", "")) for i in itens]
    # Para Matemática: inserir após "De olho no modelo"
    if perfil == "matematica":
        for idx, titulo in enumerate(titulos):
            if "de olho no modelo" in titulo or "modelo" in titulo:
                return idx + 1
    # Para outros perfis: inserir após "Foco no conteúdo"
    for idx, titulo in enumerate(titulos):
        if "foco" in titulo or "conteudo" in titulo:
            return idx + 1
    return min(2, len(itens))


def _compactar_metodologia(metodologia: list[dict], texto_pdf: str, perfil: str = "") -> list[dict[str, str]]:
    produto = _detectar_produto_atividade(texto_pdf)
    itens: list[dict[str, str]] = []
    vistos: set[str] = set()

    for item in metodologia or []:
        titulo = str(item.get("titulo", "")).strip() or "Etapa"
        texto = _limpar_texto_curto(item.get("texto", ""))
        if not texto:
            continue
        norm = re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()
        if norm in vistos:
            continue
        vistos.add(norm)
        itens.append({"titulo": titulo, "texto": texto})

    if not itens:
        itens = [{"titulo": "Desenvolvimento", "texto": "Iniciar com pergunta disparadora e retomar os conceitos centrais com apoio do material digital."}]

    if produto == "atividade do material":
        produto = ""

    if produto:
        corpo = " ".join(i["texto"].lower() for i in itens)
        if produto not in corpo:
            pos = _posicao_atividade(itens, perfil)
            itens.insert(
                pos,
                {
                    "titulo": "Atividade",
                    "texto": f"Orientar a atividade principal do material para que os estudantes {_frase_produto_atividade(produto)}, acompanhando registros, duvidas e socializacao das respostas.",
                },
            )

    itens = itens[:6]
    while len(itens) < 4:
        itens.append(
            {
                "titulo": f"Etapa {len(itens)+1}",
                "texto": "Realizar socialização breve das respostas e finalizar com síntese dos conceitos principais.",
            }
        )

    total = 0
    saida: list[dict[str, str]] = []
    for idx, item in enumerate(itens):
        restante = 1200 - total
        if restante <= 40:
            break
        limite_item = min(320, restante)
        texto = _cortar_sem_quebrar_frase(item["texto"], limite_item)
        if not texto:
            continue
        saida.append({"titulo": item["titulo"], "texto": texto})
        total += len(texto)
        if idx >= 5:
            break
    return saida[:6]


def _normalizar_saida_ia(data: dict, texto_pdf: str, disciplina: str, turma: str) -> dict:
    perfil = perfil_disciplina(f"{disciplina} {turma}")
    contexto = detectar_contexto_metodologico(texto_pdf, disciplina=disciplina, turma=turma)
    tema = extrair_conceito_central(data.get("tema", ""))
    if not tema or titulo_esta_truncado(tema):
        tema = extrair_conceito_central(data.get("tema", "")) or "Tema da aula"

    metodologia, relatorio = revisar_metodologia(
        data.get("metodologia", []),
        perfil=perfil,
        tema=tema,
        contexto=contexto,
    )
    metodologia = _compactar_metodologia(metodologia, texto_pdf, perfil)
    metodologia = naturalizar_metodologia_professor(metodologia)
    if not metodologia:
        raise ValueError("A IA nao devolveu metodologia utilizavel.")
    if not relatorio.get("aceita") and relatorio.get("score", 0) < 40:
        raise ValueError("A metodologia da IA nao passou nos criterios minimos de qualidade.")

    aprendizagem = str(data.get("aprendizagem", "") or "").strip()
    if _aprendizagem_ia_invalida(aprendizagem, tema):
        codigo = _extrair_codigo_bncc(aprendizagem)
        aprendizagem = _aprendizagem_fallback_por_perfil(perfil, tema, codigo)

    return {
        "tema": tema,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
    }


def processar_item_cdp_ia(item: dict, disciplina: str, turma: str, provedor: str, modelo: str) -> dict:
    from core.cdp import habilidade_item_cdp, objeto_item_cdp, titulo_item_cdp

    titulo = titulo_item_cdp(item) or objeto_item_cdp(item) or "Conteudo proposto"
    habilidade = habilidade_item_cdp(item)
    objeto = objeto_item_cdp(item)
    texto_base = (
        f"DISCIPLINA: {disciplina}\n"
        f"TURMA: {turma}\n"
        f"TEMA: {titulo}\n"
        f"OBJETO/CONTEUDO: {objeto}\n"
        f"HABILIDADE: {habilidade}\n\n"
        "Elabore um plano para CDP/EJA com linguagem clara, adulta, contextualizada e sem citar tecnologias digitais. "
        "Amplie um pouco a metodologia, mantendo quatro blocos: Abertura, Desenvolvimento, Atividade e Fechamento. "
        "Use exemplos cotidianos, mediação do professor, registro no caderno e socialização final quando fizer sentido."
    )
    saida = processar_plano_ia(
        texto_base,
        disciplina,
        turma,
        provedor,
        modelo,
        modalidade_eja=True,
        permitir_tecnicas_explicitamente=False,
    )
    saida["tema"] = titulo
    if habilidade:
        saida["aprendizagem"] = habilidade
    termos_bloqueados = [
        "VIREM E CONVERSEM",
        "TODO MUNDO ESCREVE",
        "COM SUAS PALAVRAS",
        "HORA DA LEITURA",
        "DE OLHO NO MODELO",
        "PAUSE E RESPONDA",
        "UM PASSO DE CADA VEZ",
    ]
    for etapa in saida.get("metodologia", []) or []:
        texto = str(etapa.get("texto", ""))
        for termo in termos_bloqueados:
            texto = texto.replace(termo, "")
        etapa["texto"] = re.sub(r"\s{2,}", " ", texto).strip(" ,;:-")
    return saida


def processar_plano_ia(
    texto_pdf: str,
    disciplina: str,
    turma: str,
    provedor: str,
    modelo: str,
    modalidade_eja: bool = False,
    permitir_tecnicas_explicitamente: bool = True,
    rascunho_base: dict | None = None,
    contexto_geracao: dict | None = None,
) -> dict:
    prompt = _montar_prompt(
        texto_pdf,
        disciplina,
        turma,
        modalidade_eja=modalidade_eja,
        permitir_tecnicas_explicitamente=permitir_tecnicas_explicitamente,
        rascunho_base=rascunho_base,
        contexto_geracao=contexto_geracao,
    )
    system_prompt = get_system_prompt(disciplina, turma)

    if provedor.lower() == "openai":
        if not OpenAI or not os.getenv("OPENAI_API_KEY"):
            raise Exception("Chave OPENAI_API_KEY nao configurada ou biblioteca ausente.")
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=IA_TIMEOUT_SEGUNDOS,
        )
        response = client.chat.completions.parse(
            model=modelo or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format=PlanoAulaIA,
            timeout=IA_TIMEOUT_SEGUNDOS,
        )
        data = _extrair_json_openai(response)
        return _normalizar_saida_ia(data, texto_pdf, disciplina, turma)

    if provedor.lower() == "gemini":
        if not genai or not os.getenv("GEMINI_API_KEY"):
            raise Exception("Chave GEMINI_API_KEY nao configurada ou biblioteca ausente.")

        timeout_milisegundos = int(IA_TIMEOUT_SEGUNDOS) * 1000
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=timeout_milisegundos),
        )
        prompt_json = system_prompt + "\n\n" + prompt

        response = client.models.generate_content(
            model=modelo or MODELO_GEMINI_PADRAO,
            contents=prompt_json,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PlanoAulaIA,
                http_options=types.HttpOptions(timeout=timeout_milisegundos),
            ),
        )

        text = response.text.strip()
        text = _limpar_json_markdown(text)
        data = json.loads(text or "{}")
        return _normalizar_saida_ia(data, texto_pdf, disciplina, turma)

    raise Exception(f"Provedor {provedor} desconhecido.")
