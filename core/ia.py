import json
import logging
import os
import re
import time
from typing import Any

try:
    from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
except ImportError:
    OpenAI = None
    APIConnectionError = None
    APITimeoutError = None
    RateLimitError = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from config import IA_TIMEOUT_SEGUNDOS, MODELO_GEMINI_PADRAO
from core.lib.classificador import normalizar_texto, perfil_disciplina
from core.models import EtapaMetodologia, PlanoAulaIA
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
from core.referencias_metodologia import carregar_referencia_metodologica, get_regras_estruturais_historia

logger = logging.getLogger(__name__)

_ERROS_OPENAI_RETRIAVEIS = tuple(
    erro
    for erro in (RateLimitError, APIConnectionError, APITimeoutError)
    if erro is not None
)

_TERMOS_RETRY_GENERICO = (
    "rate limit",
    "rate_limit",
    "timeout",
    "timed out",
    "deadline",
    "connection reset",
    "temporarily unavailable",
    "service unavailable",
    "overloaded",
    "429",
    "503",
)


def _erro_parece_temporario(erro: Exception) -> bool:
    texto = f"{type(erro).__name__}: {erro}".lower()
    return any(termo in texto for termo in _TERMOS_RETRY_GENERICO)


_FRASES_PROIBIDAS = (
    "Relacionar a explicação aos registros anteriores para que a turma perceba continuidade, aprofundamento e novos desafios.",
    "O docente apresenta",
    "Conduzir uma discussão final onde",
    "Ressalte a importância",
    "Foco no conteúdo",
    "PAUSE E RESPONDA",
    "Pause e responda",
    "pause e responda",
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
    acompanhamento = rascunho_base.get("acompanhamento") or []
    acessibilidade = rascunho_base.get("acessibilidade") or []

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

    if acompanhamento:
        linhas.append("Acompanhamento da aprendizagem base:")
        for item in acompanhamento:
            linhas.append(f"- {item}")

    if acessibilidade:
        linhas.append("Acessibilidade base:")
        for item in acessibilidade:
            linhas.append(f"- {item}")

    return "\n".join(linhas).strip()[:3500]


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
    palavras_chave_esperadas: list[str] | None = None,
    esboco_pdf: list[str] | None = None,
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

RASCUNHO LOCAL DO SISTEMA (CONTEUDO JA EXISTENTE NO DOCX OU HEURISTICAS):
{rascunho_serializado}

USE O RASCUNHO LOCAL COMO BASE DE REFINAMENTO:
- O rascunho local traz a metodologia, o acompanhamento da aprendizagem e a acessibilidade ja cadastrados ou sugeridos.
- Refine e integre esses 3 componentes com base no conteudo do PDF para garantir que sejam 100% coerentes com o material digital.
- Melhore a especificidade, a naturalidade e a clareza de todos os textos, sem inventar conteudos fora do material.
- Se o acompanhamento ou acessibilidade do rascunho forem genericos, mude-os para citar elementos e termos especificos do conteudo da aula.
- VARIABILIDADE LEXICAL: Voce DEVE evitar repeticoes de palavras e expressoes ao longo das etapas, especialmente em inicios de frases (ex: nao repita "Retomar brevemente..."). Se o rascunho base possuir frases repetitivas, REESCREVA-AS completamente usando sinonimos e estruturas variadas.
- Cada aula deve parecer unica. Varie amplamente os verbos nas etapas "Para comecar" e "Encerramento".
- CRITICO: Mantenha a concisao e o tamanho do texto original. Voce tem total liberdade para reescrever e diversificar as frases para evitar repeticao, desde que mantenha a objetividade e a estrutura curtas. NAO aumente o tamanho do texto inutilmente.
"""
    bloco_eja = ""
    if modalidade_eja:
        bloco_eja = """

MODALIDADE EJA:
- Escreva para Educacao de Jovens e Adultos, com linguagem acessivel, adulta, simples, objetiva e respeitosa.
- Priorize a relacao do conteudo com o mundo do trabalho, sem deixar de considerar vida cotidiana, saude, tecnologia e comunidade.
- Explique de forma pausada e dialogada, retomando vocabulario essencial sem infantilizar os estudantes.
- Refine a metodologia, o acompanhamento da aprendizagem e a acessibilidade do DOCX com base no PDF, preservando o sentido e a ordem das atividades.
- Em Biologia e Ingles, mantenha os blocos "Para comecar", "Foco no conteudo", "Pause e responda" e "Encerramento" quando o material trouxer essa organizacao.
- Em Lideranca e Oratoria, preserve as etapas do DOCX/PDF, inclusive mais de um bloco "Na pratica" quando houver.
- Nao cite Lemov nem nomes de tecnicas como VIREM E CONVERSEM, TODO MUNDO ESCREVE, COM SUAS PALAVRAS, HORA DA LEITURA, DE OLHO NO MODELO ou UM PASSO DE CADA VEZ. Descreva apenas a acao pedagogica de forma natural.
- No acompanhamento, observe a compreensao, a participacao e a aplicacao do conteudo em situacoes reais.
- Na acessibilidade, valorize experiencias de vida e profissionais, registros simplificados, apoio visual e diferentes ritmos de aprendizagem.
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

    bloco_historia = ""
    if perfil == "historia":
        regras_historia = get_regras_estruturais_historia()
        bloco_historia = f"""
================================================================================
DISCIPLINA: HISTÓRIA — INSTRUÇÕES OBRIGATÓRIAS E INEGOCIÁVEIS
================================================================================
{regras_historia}

================================================================================
SCHEMA JSON OBRIGATÓRIO PARA HISTÓRIA
================================================================================
O campo "metodologia" deve ser uma lista de objetos com esta estrutura exata:

  {{
    "titulo": <string — APENAS um dos valores permitidos abaixo>,
    "texto":  <string — MÁXIMO 300 CARACTERES. Conte antes de escrever.>
  }}

VALORES PERMITIDOS para o campo "titulo" (enum estrito):
  - "Para começar"
  - "Foco no conteúdo"
  - "Na prática"
  - "Encerramento"
  - "Relembre"  (somente se NÃO houver "Para começar" na mesma aula)

VALORES PROIBIDOS para o campo "titulo" (nunca use):
  ❌ "Pause e responda"   É PROIBIDO ABSOLUTO EM HISTÓRIA
  ❌ "Pausa e responda"
  ❌ "Pause"
  ❌ Qualquer variação de "Pause e responda"

LIMITE DE CARACTERES — REGRA CRÍTICA:
  - Cada "texto" de etapa: MÁXIMO 300 CARACTERES
  - Antes de finalizar cada etapa, conte: len(texto) <= 300
  - Se ultrapassar: corte na última frase completa antes do limite
  - Uma etapa com mais de 300 chars será TRUNCADA pelo sistema

================================================================================
EXEMPLO NEGATIVO — O QUE NÃO FAZER (saída REJEITADA):
================================================================================
❌ ERRADO:
{{
  "metodologia": [
    {{"titulo": "Para começar", "texto": "..."}},
    {{"titulo": "Foco no conteúdo", "texto": "..."}},
    {{"titulo": "Pause e responda", "texto": "Responda: O que é uma polis?"}},
    {{"titulo": "Encerramento", "texto": "..."}}
  ]
}}
⛔ REJEITADO porque contém "Pause e responda" (proibido em História)
⛔ REJEITADO se qualquer "texto" tiver mais de 300 caracteres

================================================================================
EXEMPLO POSITIVO — O QUE FAZER (saída ACEITA):
================================================================================
✅ CORRETO:
{{
  "metodologia": [
    {{"titulo": "Para começar",    "texto": "Iniciar com VIREM E CONVERSEM: o que os alunos sabem sobre cidades-estado gregas? Registrar hipóteses no quadro. (máx 300 chars ✅)"}},
    {{"titulo": "Foco no conteúdo","texto": "Conduzir leitura do mapa das polis gregas, destacando Atenas e Esparta. Solicitar registro no caderno dos conceitos: polis, cidadão, ágora. (máx 300 chars ✅)"}},
    {{"titulo": "Na prática",      "texto": "Atividade 1: Responder no caderno as questões do material sobre diferenças entre Atenas e Esparta. Atividade 2: Completar o quadro comparativo. (máx 300 chars ✅)"}},
    {{"titulo": "Encerramento",    "texto": "Aplicar COM SUAS PALAVRAS: cada aluno escreve uma frase respondendo às perguntas finais do PDF sobre permanências e mudanças das polis na atualidade. (máx 300 chars ✅)"}}
  ]
}}
================================================================================
"""

    regra_tecnicas = ""
    if modalidade_eja:
        regra_tecnicas = "5. No EJA, nao cite tecnicas LEMOV nem seus nomes. Converta qualquer marcador do PDF em uma descricao pedagogica natural, simples e direta."
    elif perfil in {"projeto_de_vida", "lideranca_oratoria"}:
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

    bloco_palavras_chave = ""
    if palavras_chave_esperadas:
        palavras_txt = "; ".join(palavras_chave_esperadas)
        bloco_palavras_chave = f"""
PALAVRAS-CHAVE OBRIGATÓRIAS (CURADORIA DO PROFESSOR):
{palavras_txt}

INSTRUÇÃO CRÍTICA DE ADERÊNCIA:
- Você DEVE incluir todas (ou no mínimo 85% delas) as palavras-chave listadas acima no texto final do seu plano de aula (distribuídas na Metodologia, Acompanhamento ou Acessibilidade).
- Mantenha essas palavras-chave na exata ordem sequencial/cronológica em que foram listadas, garantindo um sentido pedagógico correto.
- Não altere o radical ou a grafia destas palavras para evitar falhas no validador automático.
- Use essas palavras-chave como guia principal para detalhar e reescrever a metodologia da aula.
"""

    bloco_esboco = ""
    if esboco_pdf:
        linhas_esboco = "\n".join(f"  {linha}" for linha in esboco_pdf)
        bloco_esboco = f"""
ESTRUTURA SEQUENCIAL DO PDF (ESBOÇO PÁGINA-A-PÁGINA):
{linhas_esboco}

INSTRUÇÃO CRÍTICA DE FIDELIDADE AO PDF:
- A metodologia DEVE seguir EXATAMENTE a sequencia de secoes e elementos listados no esboco acima.
- Se o esboco mostra "PARA COMECAR: IMAGEM / urna eletronica", a etapa "Para comecar" DEVE mencionar a urna eletronica.
- Se o esboco lista dois blocos "FOCO NO CONTEUDO" separados por "NA PRATICA", gere dois blocos distintos na metodologia, cada um com seu titulo "Foco no conteudo".
- Se o esboco lista "NA PRATICA: ATIVIDADE 1" e "NA PRATICA: ATIVIDADE 2", gere DUAS etapas "Na pratica" distintas.
- Cada pagina descrita no esboco de "FOCO NO CONTEUDO" (IMAGEM, MAPA, TEXTO, MAPA MENTAL, VIDEO, QUADRO) deve ser refletida na metodologia em ordem.
- NAO reorganize, NAO funda, NAO omita secoes que o esboco distingue.
- Use as TECNICAS PEDAGOGICAS exatamente como listadas no esboco (entre aspas).
- Os titulos das etapas devem corresponder as secoes do esboco: "Para comecar", "Foco no conteudo", "Na pratica", "Encerramento".
- Ignore secoes "PAUSE E RESPONDA" do esboco; nao gere etapa com esse titulo.
"""

    tamanho_etapa_regras = "3.2. PADRONIZAÇÃO DE TAMANHO (MUITO IMPORTANTE): CADA ETAPA deve ser EXTREMAMENTE CURTA, direta e em formato de tópicos ou frases curtas. NÃO AUMENTE O TEXTO INUTILMENTE. NO MÁXIMO 2 a 3 linhas por etapa (entre 15 e 40 palavras). NÃO explique de forma detalhada ou teórica como a aula será feita. NÃO justifique suas escolhas. Vá direto ao ponto, citando a ação (ex: 'Leitura do texto X e registro de impressões', 'Resolução das questões 1 a 3 no caderno'). Seja 100% focado na execução objetiva."
    if perfil == "historia":
        tamanho_etapa_regras = "3.2. PADRONIZAÇÃO DE TAMANHO (HISTÓRIA): CADA ETAPA deve ser extremamente curta (NO MÁXIMO 400 caracteres no total). Apenas refine o texto base com as palavras-chave do PDF. NÃO AUMENTE O TEXTO INUTILMENTE. Seja cirúrgico, mantendo a metodologia curta e direta sem dar explicações extras."

    return f"""Voce e um especialista em planejamento pedagogico. Extraia as informacoes do slide abaixo.
DISCIPLINA: {disciplina}
TURMA: {turma}
PERFIL METODOLOGICO: {perfil}
CONTEXTO: {contexto}
NIVEL: {nivel}
{bloco_esboco}
{bloco_palavras_chave}
{bloco_eja}
{bloco_leitura_redacao}
{bloco_historia}

{orientacao}

{regras_consolidadas_para_prompt(perfil, contexto, nivel)}
{bloco_rascunho}

REGRAS:
1. Extraia o conceito central da aula. Nao devolva rotulos como "AULA 1", "2o bimestre", "Ensino Fundamental" ou "Parte 1" como tema principal.
2. Identifique o codigo da BNCC e a descricao da aprendizagem essencial se houver.
3. Elabore a metodologia seguindo as etapas identificadas no esboco do PDF. O numero de etapas deve corresponder a estrutura real do material. Quando nao houver esboco, use 4 a 6 etapas. Para Biologia e Ciencias, prefira os blocos "Para comecar", "Foco no conteudo", "Pause e responda" e "Encerramento" quando forem coerentes com o material.
3.1. Nao narre a aula inteira e nao repita os slides; escreva como plano de aula sintetico mas fiel a sequencia do PDF.
{tamanho_etapa_regras}
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


# Limite de caracteres padronizado por perfil (máximo 300 caracteres por etapa)
_LIMITE_CHARS_POR_ETAPA = {
    "historia": 300,
    "geografia": 300,
    "lingua_portuguesa": 300,
    "lingua_portuguesa_ef": 300,
    "lingua_portuguesa_em": 300,
    "leitura_redacao": 300,
    "redacao": 300,
}
_LIMITE_CHARS_DEFAULT = 300


def _normalizar_titulo_etapa(titulo: str) -> str:
    """Normaliza título de etapa para comparação (ex: 'Foco no conteúdo' -> 'foco no conteudo')."""
    return normalizar_texto(titulo).lower().strip()


def _segmentar_por_posicao(metodologia: list[dict]) -> list[list[dict]]:
    """
    CORREÇÃO FALHA #1 — Agrupa etapas consecutivas de mesmo tipo em segmentos.
    Quebra o segmento quando o tipo de etapa muda.
    Ex: [FC, FC, FC, NP, FC, FC, FC, NP2, ENC]
    → [[FC,FC,FC], [NP], [FC,FC,FC], [NP2], [ENC]]
    """
    segmentos: list[list[dict]] = []
    segmento_atual: list[dict] = []
    titulo_atual: str | None = None
    for item in metodologia:
        titulo = _normalizar_titulo_etapa(item.get("titulo", ""))
        if titulo != titulo_atual and segmento_atual:
            segmentos.append(segmento_atual)
            segmento_atual = []
        titulo_atual = titulo
        segmento_atual.append(item)
    if segmento_atual:
        segmentos.append(segmento_atual)
    return segmentos


def _compactar_segmento(segmento: list[dict], limite_chars: int) -> list[dict[str, str]]:
    """
    CORREÇÃO FALHA #1 — Compacta DENTRO de um segmento (deduplicação + limpeza).
    Etapas consecutivas de mesmo tipo são reunidas em um único bloco.
    """
    if not segmento:
        return []
    titulo_base = str(segmento[0].get("titulo", "")).strip() or "Etapa"
    textos_unicos: list[str] = []
    vistos: set[str] = set()
    for item in segmento:
        texto = _limpar_texto_curto(item.get("texto", ""))
        if not texto:
            continue
        norm = re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()
        if norm in vistos:
            continue
        vistos.add(norm)
        textos_unicos.append(texto)
    if not textos_unicos:
        return []
    # Reunir textos do segmento em um único bloco
    texto_reunido = " ".join(textos_unicos)
    texto_cortado = _cortar_sem_quebrar_frase(texto_reunido, limite_chars)
    if not texto_cortado:
        # Tentar cada texto individual
        for txt in textos_unicos:
            resultado = _cortar_sem_quebrar_frase(txt, limite_chars)
            if resultado:
                return [{"titulo": titulo_base, "texto": resultado}]
        return []
    return [{"titulo": titulo_base, "texto": texto_cortado}]


def _compactar_metodologia(metodologia: list[dict], texto_pdf: str, perfil: str = "") -> list[dict[str, str]]:
    produto = _detectar_produto_atividade(texto_pdf)
    limite_etapa = _LIMITE_CHARS_POR_ETAPA.get(perfil, _LIMITE_CHARS_DEFAULT)
    if perfil == "historia":
        limite_etapa = min(limite_etapa, 420)
    itens: list[dict[str, str]] = []

    # CORREÇÃO FALHA #1 — Para perfil historia, usar segmentação posicional
    if perfil == "historia":
        # Primeiro, limpar textos vazios
        itens_limpos = []
        for item in metodologia or []:
            titulo = str(item.get("titulo", "")).strip() or "Etapa"
            texto = _limpar_texto_curto(item.get("texto", ""))
            if not texto:
                continue
            # CORREÇÃO FALHA #5/REGRA 1 — Remover etapas "Pause e responda"
            titulo_norm = _normalizar_titulo_etapa(titulo)
            if "pause" in titulo_norm and "responda" in titulo_norm:
                continue
            # CORREÇÃO FALHA #5/REGRA 2 — Converter "Relembre" em "Para começar"
            if "relembre" in titulo_norm:
                titulo = "Para começar"
            itens_limpos.append({"titulo": titulo, "texto": texto})

        if not itens_limpos:
            itens_limpos = [{"titulo": "Desenvolvimento", "texto": "Iniciar com pergunta disparadora e retomar os conceitos centrais com apoio do material digital."}]

        # Segmentar por posição e compactar dentro de cada segmento
        segmentos = _segmentar_por_posicao(itens_limpos)
        for segmento in segmentos:
            itens.extend(_compactar_segmento(segmento, limite_etapa))
    else:
        # Fluxo para outros perfis — aplicar limite
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
            texto = _cortar_sem_quebrar_frase(texto, limite_etapa)
            if texto:
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

    # Permitir até 10 etapas para seguir a estrutura real do PDF
    itens = itens[:10]
    # Não forçar mínimo de 4 etapas — manter apenas as etapas que o PDF realmente tem
    if not itens:
        itens = [
            {
                "titulo": "Desenvolvimento",
                "texto": "Realizar socialização breve das respostas e finalizar com síntese dos conceitos principais.",
            }
        ]

    # CORREÇÃO FALHA #4 — Reservar orçamento mínimo para encerramento
    orcamento_encerramento = 300 if perfil == "historia" else 0
    orcamento_total = 1650 if perfil == "historia" else 9600

    total = 0
    saida: list[dict[str, str]] = []
    for idx, item in enumerate(itens):
        # Reservar espaço para encerramento se não é a última etapa
        is_ultima = idx == len(itens) - 1
        reserva = orcamento_encerramento if (not is_ultima and orcamento_encerramento > 0) else 0
        restante = orcamento_total - total - reserva
        if restante <= 40:
            break
        lim = min(limite_etapa, restante)
        texto = _cortar_sem_quebrar_frase(item["texto"], lim)
        if not texto:
            continue
        saida.append({"titulo": item["titulo"], "texto": texto})
        total += len(texto)
        if idx >= 9:
            break
    return saida[:10]


def _validar_schema_resposta(data: dict) -> None:
    """Valida se a resposta da IA tem a estrutura esperada."""
    if not isinstance(data, dict):
        raise ValueError(
            f"Resposta da IA invalida: esperado dict, recebido {type(data).__name__}"
        )
    if not isinstance(data.get("metodologia"), list):
        # Tenta converter string para lista se possível
        met = data.get("metodologia")
        if isinstance(met, str) and met.strip():
            data["metodologia"] = [{"titulo": "Desenvolvimento", "texto": met}]
        else:
            raise ValueError(
                f"Schema invalido: 'metodologia' deve ser lista, "
                f"recebido: {type(met).__name__}"
            )
    if not data.get("tema"):
        raise ValueError("Schema invalido: campo 'tema' ausente ou vazio.")


def _normalizar_saida_ia(data: dict, texto_pdf: str, disciplina: str, turma: str) -> dict:
    _validar_schema_resposta(data)
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
        consolidar=False,
    )
    metodologia = _compactar_metodologia(metodologia, texto_pdf, perfil)
    metodologia = naturalizar_metodologia_professor(metodologia, perfil=perfil)
    if not metodologia:
        raise ValueError("A IA nao devolveu metodologia utilizavel.")
    if not relatorio.get("aceita") and relatorio.get("score", 0) < 40:
        raise ValueError("A metodologia da IA nao passou nos criterios minimos de qualidade.")

    aprendizagem = str(data.get("aprendizagem", "") or "").strip()
    if _aprendizagem_ia_invalida(aprendizagem, tema):
        codigo = _extrair_codigo_bncc(aprendizagem)
        aprendizagem = _aprendizagem_fallback_por_perfil(perfil, tema, codigo)

    acompanhamento = data.get("acompanhamento") or []
    acessibilidade = data.get("acessibilidade") or []

    if isinstance(acompanhamento, list):
        acompanhamento = [str(item).strip() for item in acompanhamento if str(item).strip()]
    else:
        acompanhamento = []

    if isinstance(acessibilidade, list):
        acessibilidade = [str(item).strip() for item in acessibilidade if str(item).strip()]
    else:
        acessibilidade = []

    return {
        "tema": tema,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
        "acompanhamento": acompanhamento,
        "acessibilidade": acessibilidade,
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


def _chamar_openai_com_retry(client, modelo, messages, response_format, max_tentativas=3):
    """Chama a API da OpenAI com retry e backoff exponencial."""
    for tentativa in range(max_tentativas):
        try:
            return client.chat.completions.parse(
                model=modelo,
                messages=messages,
                response_format=response_format,
                timeout=IA_TIMEOUT_SEGUNDOS,
            )
        except Exception as e:
            nome_erro = type(e).__name__
            erro_retriavel = isinstance(e, _ERROS_OPENAI_RETRIAVEIS) if _ERROS_OPENAI_RETRIAVEIS else False
            if erro_retriavel or _erro_parece_temporario(e):
                if tentativa == max_tentativas - 1:
                    raise
                espera = (2 ** tentativa) + 1
                logger.warning("OpenAI %s — tentativa %d/%d, aguardando %ds...", nome_erro, tentativa + 1, max_tentativas, espera)
                time.sleep(espera)
            else:
                raise
    raise RuntimeError("Falha apos todas as tentativas de chamada OpenAI.")


def _chamar_gemini_com_retry(client, modelo, prompt, config, max_tentativas=3):
    """Chama a API do Gemini com retry e backoff exponencial."""
    for tentativa in range(max_tentativas):
        try:
            return client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=config,
            )
        except Exception as e:
            nome_erro = type(e).__name__
            if _erro_parece_temporario(e):
                if tentativa == max_tentativas - 1:
                    raise
                espera = (2 ** tentativa) + 1
                logger.warning("Gemini %s — tentativa %d/%d, aguardando %ds...", nome_erro, tentativa + 1, max_tentativas, espera)
                time.sleep(espera)
            else:
                raise
    raise RuntimeError("Falha apos todas as tentativas de chamada Gemini.")


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
    palavras_chave_esperadas: list[str] | None = None,
    esboco_pdf: list[str] | None = None,
) -> dict:
    prompt = _montar_prompt(
        texto_pdf,
        disciplina,
        turma,
        modalidade_eja=modalidade_eja,
        permitir_tecnicas_explicitamente=permitir_tecnicas_explicitamente,
        rascunho_base=rascunho_base,
        contexto_geracao=contexto_geracao,
        palavras_chave_esperadas=palavras_chave_esperadas,
        esboco_pdf=esboco_pdf,
    )
    system_prompt = get_system_prompt(disciplina, turma)

    if provedor.lower() == "openai":
        if not OpenAI or not os.getenv("OPENAI_API_KEY"):
            raise Exception("Chave OPENAI_API_KEY nao configurada ou biblioteca ausente.")
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=IA_TIMEOUT_SEGUNDOS,
        )
        response = _chamar_openai_com_retry(
            client,
            modelo or "gpt-4o-mini",
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            PlanoAulaIA,
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

        response = _chamar_gemini_com_retry(
            client,
            modelo or MODELO_GEMINI_PADRAO,
            prompt_json,
            types.GenerateContentConfig(
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
