"""
Validador pedagogico expandido para planos de aula.

Valida tema, metodologia, acompanhamento, acessibilidade e aprendizagem.
"""

import re
from collections import Counter

from core.educacao_financeira_validacao import validar_requisitos_educacao_financeira
from core.listas_pedagogicas import (
    itens_lista_pedagogica,
    problemas_lista_exatamente_tres,
)
from core.qualidade_metodologica import normalizar_texto, tem_mojibake


_ROTULOS_ETAPAS = (
    "para comecar",
    "disparo inicial",
    "contextualizacao",
    "leitura ou exploracao inicial",
    "leitura compartilhada ou individual",
    "leitura e construcao do conteudo",
    "predicao guiada",
    "analise guiada",
    "foco no conteudo",
    "sistematizacao",
    "producao textual",
    "revisao e fechamento",
    "revisao orientada",
    "escrita da versao final",
    "submissao e socializacao",
    "encerramento",
)


def _normalizar_rotulo(texto: str) -> str:
    texto = (texto or "").strip().lower()
    return re.sub(r"[^a-z\s]", "", texto).strip()


def _contar_etapas_metodologia(metodologia) -> int:
    etapas = set()
    for item in metodologia or []:
        if isinstance(item, dict):
            titulo = _normalizar_rotulo(item.get("titulo", ""))
            texto = str(item.get("texto", "") or "")
        else:
            titulo = ""
            texto = str(item or "")

        if titulo:
            etapas.add(titulo)

        texto_norm = _normalizar_rotulo(texto)
        for rotulo in _ROTULOS_ETAPAS:
            if re.search(rf"\b{re.escape(rotulo)}\b", texto_norm):
                etapas.add(rotulo)

    return len(etapas)


def validar_aulas_geradas(
    aulas,
    permitir_temas_repetidos: bool = False,
    permitir_metodologia_simples: bool = False,
) -> list[str]:
    """Valida a qualidade pedagogica das aulas geradas."""
    problemas = []
    if not aulas:
        return ["Nenhuma aula foi gerada."]

    temas_vistos = set()
    for idx, aula in enumerate(aulas, start=1):
        tema = str(aula.get("tema", "")).strip()
        if not tema:
            problemas.append(f"Aula {idx}: tema nao identificado.")
        if not permitir_temas_repetidos and tema and tema in temas_vistos:
            problemas.append(
                f"Aula {idx}: tema '{tema}' repetido de aula anterior. "
                "Considere diferenciar com subtema ou continuidade."
            )
        temas_vistos.add(tema)

        metodologia = aula.get("metodologia") or []
        if not metodologia:
            problemas.append(f"Aula {idx}: metodologia vazia.")
        else:
            primeiro = metodologia[0]
            texto_primeiro = primeiro.get("texto", "") if isinstance(primeiro, dict) else str(primeiro)
            if len(texto_primeiro.strip()) < 40:
                problemas.append(f"Aula {idx}: desenvolvimento muito curto.")

            etapas_identificadas = _contar_etapas_metodologia(metodologia)
            if not permitir_metodologia_simples and etapas_identificadas < 3 and len(metodologia) < 3:
                problemas.append(
                    f"Aula {idx}: metodologia com poucas etapas ({etapas_identificadas}). "
                    "Um plano completo deve ter pelo menos 3 etapas."
                )

        aprendizagem = str(aula.get("aprendizagem", "")).strip()
        if not aprendizagem:
            problemas.append(f"Aula {idx}: campo de aprendizagem vazio.")
        elif len(aprendizagem) < 20:
            problemas.append(f"Aula {idx}: aprendizagem muito curta ({len(aprendizagem)} chars).")

        acompanhamento = aula.get("acompanhamento") or []
        if not acompanhamento:
            problemas.append(f"Aula {idx}: acompanhamento da aprendizagem vazio.")
        else:
            itens_validos = itens_lista_pedagogica(acompanhamento)
            problemas.extend(
                problemas_lista_exatamente_tres(
                    "acompanhamento da aprendizagem",
                    itens_validos,
                    prefixo=f"Aula {idx}: ",
                )
            )

        acessibilidade = aula.get("acessibilidade") or []
        if not acessibilidade:
            problemas.append(f"Aula {idx}: acessibilidade vazia.")
        else:
            itens_validos = itens_lista_pedagogica(acessibilidade)
            problemas.extend(
                problemas_lista_exatamente_tres(
                    "acessibilidade",
                    itens_validos,
                    prefixo=f"Aula {idx}: ",
                )
            )

        for problema in validar_requisitos_educacao_financeira(aula):
            problemas.append(f"Aula {idx}: {problema}")

    return problemas


def validar_aula_final(aula: dict) -> list[str]:
    """Faz uma checagem semântica detalhada e pedagógica antes do preenchimento do DOCX."""
    avisos = []

    disciplina = normalizar_texto(aula.get("disciplina", ""))
    tema = normalizar_texto(aula.get("tema", ""))
    aprendizagem = normalizar_texto(aula.get("aprendizagem", ""))

    if len(tema) < 8 or tema in {"estudar matematica", "aula de ciencias", "tema da aula"}:
        avisos.append("Tema muito genérico ou vazio.")

    metodologia = aula.get("metodologia", [])
    if len(metodologia) < 3 and _contar_etapas_metodologia(metodologia) < 3:
        avisos.append(
            f"Metodologia com poucas etapas ({len(metodologia)}). "
            "O plano deve apresentar ao menos 3 momentos pedagógicos."
        )

    conteudo_ref = tema + " " + aprendizagem
    conteudo_palavras = {
        palavra
        for palavra in conteudo_ref.split()
        if len(palavra) > 3 and palavra not in {
            "para", "como", "com", "uma", "mais", "sobre", "aula", "conteudo", "tema",
            "estudantes", "alunos", "professor", "ciencias", "matematica", "portugues",
            "atividade", "recurso",
        }
    }

    verbos_professor = {
        "professor", "docente", "mediador", "apresent", "condu", "propor", "propo",
        "solicit", "orient", "explic", "retom", "exib", "pergunt", "question",
        "mostr", "lider", "medi", "inici", "peca", "peça", "organiz", "aplic",
        "utiliz", "registr", "acompanh", "disponibiliz", "promov", "contextualiz",
    }
    termos_estudantes = {
        "aluno", "estudante", "turma", "dupla", "grupo", "eles", "compartilh", "escrev",
        "respond", "resolv", "realiz", "discut", "particip", "leem", "leiam", "leitura",
        "observ", "compar", "identifi", "analis", "produz", "organiz", "registr", "socializ",
        "expliqu", "elabor", "relacion",
    }
    termos_interacao_registro = {
        "caderno", "registro", "respost", "escrev", "dupla", "grupo", "roda", "discussao",
        "debate", "socializ", "cadernos", "anot", "compartilh", "pergunta", "question",
        "hipotese", "leitura guiada", "leitura orientada", "pausa", "oral", "topicos",
    }

    etapas_textos = []
    for item in metodologia:
        if not isinstance(item, dict):
            continue
        titulo = item.get("titulo", "")
        texto = item.get("texto", "")
        titulo_norm = normalizar_texto(titulo).lower()
        texto_norm = normalizar_texto(texto).lower()
        etapas_textos.append(texto)

        if not any(termo in texto_norm for termo in verbos_professor):
            avisos.append(f"Etapa '{titulo}': não descreve claramente a ação do professor.")
        if not any(termo in texto_norm for termo in termos_estudantes):
            avisos.append(f"Etapa '{titulo}': não descreve claramente a ação dos alunos.")
        etapa_foco_conteudo = "foco" in titulo_norm and "conteudo" in titulo_norm
        if (
            not etapa_foco_conteudo
            and not any(termo in texto_norm for termo in termos_interacao_registro)
        ):
            avisos.append(f"Etapa '{titulo}': não prevê momentos de interação ou de registro (ex: caderno, duplas).")
        if conteudo_palavras and not any(termo in texto_norm for termo in conteudo_palavras):
            avisos.append(f"Etapa '{titulo}': não menciona termos específicos do conteúdo da aula.")

    if len(etapas_textos) >= 2:
        palavras_totais = []
        for etapa in etapas_textos:
            palavras_totais.extend([palavra for palavra in normalizar_texto(etapa).split() if len(palavra) > 3])
        if palavras_totais:
            counts = Counter(palavras_totais)
            repetidas = sum(contagem for contagem in counts.values() if contagem > 2)
            if len(palavras_totais) > 20 and (repetidas / len(palavras_totais)) > 0.4:
                avisos.append("Metodologia com alto índice de repetição de termos.")

    # Validador Semântico de Coerência de Recursos (Item 4)
    texto_metodologia_completa = " ".join(etapas_textos)
    texto_metodologia_norm = normalizar_texto(texto_metodologia_completa)
    texto_fonte_norm = normalizar_texto(aula.get("texto_fonte") or "")
    recursos_norm = [normalizar_texto(str(r)) for r in (aula.get("recursos_detectados") or [])]

    # Coerência de Vídeo
    termos_video_metodologia = ["video", "assista", "assistir", "audiovisual", "filme", "documentario", "youtube"]
    propoe_video = any(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_metodologia_norm) for t in termos_video_metodologia)
    if propoe_video:
        termos_video_fonte = ["video", "youtube", "link", "links", "assista", "assistir", "filme", "documentario", "qrcode", "qr code", "http"]
        tem_video_fonte = any(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_fonte_norm) for t in termos_video_fonte) or any("video" in r or "link" in r or "youtube" in r or "http" in r for r in recursos_norm)
        if not tem_video_fonte:
            avisos.append("Metodologia propõe o uso de vídeo, mas nenhum vídeo foi detectado no material de origem.")

    # Coerência de Gráfico/Tabela
    termos_grafico_metodologia = ["grafico", "tabela", "infografico", "tabelas", "graficos"]
    propoe_grafico = any(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_metodologia_norm) for t in termos_grafico_metodologia)
    if propoe_grafico:
        termos_grafico_fonte = ["grafico", "tabela", "infografico", "porcentagem", "dados", "%", "figura", "imagem", "tabelas", "graficos", "eixo", "coluna", "linha"]
        tem_grafico_fonte = any(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_fonte_norm) for t in termos_grafico_fonte) or any("grafico" in r or "tabela" in r or "infografico" in r or "dado" in r or "%" in r for r in recursos_norm)
        if not tem_grafico_fonte:
            avisos.append("Metodologia propõe análise de gráfico/tabela sem correspondência no material de origem.")

    # Coerência de Experimento
    termos_experimento_metodologia = ["experimento", "aula pratica", "laboratorio", "pratica experimental", "experiencia", "procedimento pratico"]
    propoe_experimento = any(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_metodologia_norm) for t in termos_experimento_metodologia)
    if propoe_experimento:
        termos_experimento_fonte = ["experimento", "pratica", "laboratorio", "materiais", "procedimento", "passo a passo", "mistura", "experiencia", "observar", "reacao", "hipotese", "cientifico"]
        tem_experimento_fonte = any(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto_fonte_norm) for t in termos_experimento_fonte) or any("experimento" in r or "pratica" in r or "laboratorio" in r or "mistura" in r or "materiais" in r for r in recursos_norm)
        if not tem_experimento_fonte:
            avisos.append("Metodologia menciona realização de experimento sem correspondência ou procedimento prático no material de origem.")

    acessibilidade = aula.get("acessibilidade") or []
    acompanhamento = aula.get("acompanhamento") or []
    avisos.extend(
        problemas_lista_exatamente_tres(
            "Acompanhamento da aprendizagem",
            itens_lista_pedagogica(acompanhamento),
        )
    )
    avisos.extend(
        problemas_lista_exatamente_tres(
            "Acessibilidade",
            itens_lista_pedagogica(acessibilidade),
        )
    )
    texto_acessibilidade = " ".join(str(item) for item in acessibilidade).lower()
    placeholders_acess = {
        "estrategia generica", "apoio generico", "leitura simples", "informacao do material",
    }
    if any(placeholder in texto_acessibilidade for placeholder in placeholders_acess):
        avisos.append("Acessibilidade contém orientações ou placeholders genéricos.")
    if conteudo_palavras and not any(termo in texto_acessibilidade for termo in conteudo_palavras):
        avisos.append("Acessibilidade genérica sem ligação específica ao conteúdo ou tema da aula.")

    for problema in validar_requisitos_educacao_financeira(aula):
        avisos.append(problema)

    texto_total = " ".join([
        tema,
        aprendizagem,
        " ".join(etapas_textos),
        " ".join(acessibilidade),
        " ".join(str(item) for item in aula.get("acompanhamento", [])),
    ])
    texto_norm = normalizar_texto(texto_total)

    if tem_mojibake(texto_total):
        avisos.append("Texto com possível problema de codificação.")
    if "relacionado a relacionado" in texto_total.lower():
        avisos.append("Possível frase artificial ou repetida.")

    if disciplina and "matematica" in disciplina and any(
        termo in texto_norm for termo in ["texto literario", "personagens", "enredo", "cronica"]
    ):
        avisos.append("Possível contaminação: metodologia de leitura literária em Matemática.")
    if disciplina and "geografia" in disciplina and any(
        termo in texto_norm for termo in ["equacao", "incognita", "resolver x", "sistema de equacoes"]
    ):
        avisos.append("Possível contaminação: linguagem algébrica em Geografia.")
    if disciplina and "historia" in disciplina and any(
        termo in texto_norm for termo in ["calculo", "equacao", "porcentagem", "resolver operacoes"]
    ):
        avisos.append("Possível contaminação: cálculo matemático em História.")
    if "producao textual" in tema and not any(
        termo in texto_norm for termo in ["rascunho", "revis", "reescrita", "planejamento"]
    ):
        avisos.append("Produção textual sem etapa clara de planejamento ou revisão.")

    return avisos


_TERMOS_PEDAGOGICOS = {
    # Termos básicos e pedagógicos comuns
    "estudante", "estudantes", "aluno", "alunos", "professor", "docente", "aula", "texto",
    "atividade", "atividades", "exercicio", "exercicios", "pratica", "praticas", "teoria",
    "conteudo", "conteudos", "tema", "temas", "assunto", "assuntos", "conceito", "conceitos",
    "conhecimento", "conhecimentos", "habilidade", "habilidades", "competencia", "competencias",
    "objetivo", "objetivos", "meta", "metas", "proposito", "propositos", "finalidade",
    "estrategia", "estrategias", "metodologia", "metodologias", "metodo", "metodos",
    "tecnica", "tecnicas", "recurso", "recursos", "material", "materiais", "ferramenta",
    "lousa", "quadro", "apagador", "caneta", "caderno", "cadernos", "livro", "livros",
    "impresso", "digital", "internet", "computador", "celular", "projetor", "datashow",
    "video", "audio", "imagem", "imagens", "fotografia", "grafico", "graficos", "tabela",
    "desenvolvimento", "inicio", "fim", "minutos", "tempo", "momento", "etapa", "passo",
    "leitura", "escrita", "producao", "textual", "redacao", "resumo", "sintese", "esquema",
    "mapa", "mental", "conceitual", "organizador", "painel", "roda", "conversa", "debate",
    "discussao", "apresentacao", "seminario", "pesquisa", "entrevista", "relatorio",
    "experimento", "laboratorio", "observacao", "analise", "conclusao", "hipotese", "teste",
    "ensaio", "simulacao", "dupla", "duplas", "grupo", "grupos", "equipe", "equipes",
    "individual", "coletivo", "socializacao", "compartilhamento", "troca", "interacao",
    "colaboracao", "cooperacao", "registro", "registros", "anotacao", "anotacoes",
    "apontamento", "apontamentos", "pergunta", "perguntas", "resposta", "respostas",
    "questionamento", "questionamentos", "duvida", "duvidas", "esclarecimento",
    "esclarecimentos", "explicacao", "explicacoes", "correcao", "correcoes", "feedback",
    "retorno", "avaliacao", "avaliacoes", "prova", "exame", "trabalho", "projeto",
    "portifolio", "autoavaliacao", "orientacao", "orientacoes", "instrucao", "instrucoes",
    "comando", "comandos", "virem", "conversem", "todo", "mundo", "escreve", "olho",
    "modelo", "hora", "pause", "responda", "cada", "vez", "suas", "palavras", "lemov",
    "pedir", "solicitar", "orientar", "explicar", "mediar", "conduzir", "propor",
    "realizar", "fazer", "desenvolver", "aplicar", "utilizar", "usar", "empregar",
    "iniciar", "finalizar", "encerrar", "concluir", "retomar", "revisar", "relembrar",
    "contextualizar", "sistematizar", "consolidar", "fixar", "avaliar", "verificar",
    "acompanhar", "observar", "analisar", "interpretar", "compreender", "entender",
    "identificar", "reconhecer", "relacionar", "comparar", "diferenciar", "distinguir",
    "classificar", "categorizar", "organizar", "estruturar", "planejar", "projetar",
    "criar", "produzir", "elaborar", "construir", "desenhar", "pintar", "escrever",
    "ler", "falar", "ouvir", "escutar", "assistir", "ver", "perceber", "sobre", "como",
    "para", "qual", "quais", "quem", "onde", "quando", "porque", "pois", "durante",
    "apos", "antes", "depois", "logo", "entao", "assim", "portanto", "porem", "mas",
    "contudo", "todavia", "entretanto", "embora", "ainda", "sim", "talvez", "sempre",
    "nunca", "jamais", "muito", "pouco", "mais", "menos", "quase", "apenas", "somente",
    "tudo", "nada", "alguem", "ninguem", "qualquer", "algum", "nenhum", "outro", "mesmo",
    "proprio", "quanto", "tamanho", "pelo", "pela", "pelos", "pelas", "num", "numa",
    "nuns", "numas", "dum", "duma", "duns", "dumas", "nisso", "naquilo", "neste", "nesta",
    "nesse", "nessa", "naquele", "naquela", "deste", "desta", "desse", "dessa", "daquele",
    "daquela", "este", "esta", "esse", "essa", "aquele", "aquela", "isto", "isso", "aquilo",
    "meu", "minha", "teu", "tua", "seu", "sua", "nosso", "nossa", "vosso", "vossa",
    "pedindo", "apresentando", "solicitando", "conduzindo", "realizando", "organizando",
    "incorporando", "retomando", "verificando", "indicando", "revisando", "contexto",
    "foco", "slide", "slides", "atencao", "principal", "principais", "seguinte",
    "seguintes", "conforme", "segundo", "sugestao", "sugestoes", "exemplo", "exemplos",
    "caso", "casos", "situacao", "situacoes", "problema", "problemas", "solucao", "solucoes",
    "alternativa", "alternativas", "opcao", "apresentar", "garantir", "incentivar",
    "relacionarem", "cotidiano", "centrais", "meio", "ajudando", "termos", "importantes",
    "importancia", "criterios", "especificacoes", "clareza", "comentado", "orientador",
    "comparacao", "conceitual", "organizem", "diferencas", "expliquem", "maiores",
    "precisao", "favorecer", "organizacao", "pensamento", "descrição", "descricao",
    "pontos", "especialmente", "conseguiu", "indicar", "retomados", "continuidade",
    "sequencia", "parte", "partes", "fase", "fases", "passos", "dia", "dias", "semana",
    "semanas", "mes", "meses", "ano", "anos", "bimestre", "bimestres",

    # Conjugações e termos estruturais extras (evita falsos negativos na aderência)
    "inicie", "conduza", "questione", "solicite", "respondam", "socialize", "oriente",
    "acompanhe", "faca", "ajustar", "seguir", "partir", "retome", "feche", "encerre",
    "apresente", "discuta", "analise", "compare", "registre", "escreva", "leia", "pesquise",
    "pergunte", "indique", "verifique", "observe", "avalie", "sinalize", "destaque", "traga",
    "escrevendo", "lendo", "discutindo", "pausa", "duas", "tres", "breve", "iniciais", "finais",
    "demais", "orientadora", "conclusoes", "evidencias", "anotacoes", "registros",
    "participacao", "atencao", "caderno", "respostas", "duvidas", "conferencia", "observar",
    "participar", "verificar", "anotar", "escrever", "descrever", "explicar", "analisar",
    "avaliar", "sintetizar", "detalhar", "destacar", "comparar", "relacionar", "identificar",
    "caracterizar", "diferenciar", "concluir", "fechar", "resumir", "sintese", "esquema",
    "anotacao", "registro", "resumo", "evidencia", "conclusao", "pergunta", "resposta",
    "duvida", "discussao", "debate", "painel", "roda", "conversa", "apresentacao",
    "seminario", "pesquisa", "relatorio", "trabalho", "projeto", "avaliacao", "correcao",
    "feedback", "retorno", "instrucao", "comando", "virem", "conversem", "escreve", "olho",
    "modelo", "hora", "pause", "responda", "cada", "vez", "suas", "palavras", "lemov",
    "pedir", "mediar", "propor", "usar", "utilizar", "gerar", "gerado", "geracao", "feito",
    "forma", "formas", "diferentes", "comuns", "especificas", "especifica", "especifico",
    "foco", "modo", "modos", "tipo", "tipos", "aulas", "materiais", "digitais", "digital",
    "estudos", "orientacoes", "orientador", "estudarem", "estudar", "aprender", "aprendizagem",
    "ensino", "fundamental", "medio", "ciclo", "anos", "series", "serie", "turmas", "turma"
}

def extrair_palavras_chaves(texto: str) -> set:
    """Extrai palavras-chave ignorando termos pedagógicos e estruturais."""
    palavras = re.findall(r'\b[a-z]{4,}\b', normalizar_texto(texto).lower())
    return {p for p in palavras if p not in _TERMOS_PEDAGOGICOS}

def calcular_aderencia_pdf(aula: dict) -> tuple[float, list[str]]:
    """
    Calcula a porcentagem de sobreposição de vocabulário significativo entre a 
    metodologia gerada e o texto original do PDF, garantindo que o modelo
    não alucinou conceitos externos.
    """
    texto_fonte = aula.get("texto_fonte") or ""
    metodologia = aula.get("metodologia", [])
    
    if not texto_fonte or not metodologia:
        return 100.0, []
        
    # Heurística: Se o texto extraído do PDF for extremamente curto (menos de 300 caracteres),
    # assumimos que é uma execução de teste ou material sem texto viável,
    # pulando a checagem lexical para evitar falsos alertas pedagógicos.
    if len(texto_fonte.strip()) < 300:
        return 100.0, []
        
    texto_metodologia = " ".join(item.get("texto", "") if isinstance(item, dict) else str(item) for item in metodologia)
    
    chaves_fonte = extrair_palavras_chaves(texto_fonte)
    chaves_met = extrair_palavras_chaves(texto_metodologia)
    
    if not chaves_met:
        return 100.0, []
        
    # Fuzzy matching baseado em correspondência parcial de radicais (4 primeiras letras)
    # ou contenção de strings para contornar conjugações e variações gramaticais.
    termos_estranhos = set()
    for pm in chaves_met:
        matched = False
        if pm in chaves_fonte:
            matched = True
        else:
            # Checa radical comum
            for cf in chaves_fonte:
                if pm[:4] == cf[:4]:
                    matched = True
                    break
                if len(pm) >= 4 and len(cf) >= 4:
                    if pm in cf or cf in pm:
                        matched = True
                        break
        if not matched:
            termos_estranhos.add(pm)

    aderencia = ((len(chaves_met) - len(termos_estranhos)) / len(chaves_met)) * 100

    alertas = []
    if aderencia < 80.0:
        termos_formatados = ", ".join(list(termos_estranhos)[:5]) # Mostra até 5 termos
        alertas.append(f"Aderência ao PDF baixa ({aderencia:.0f}%). A metodologia inseriu conceitos não encontrados no material original (ex: '{termos_formatados}'). Sugestão: Remova conteúdos externos e foque apenas no que está no PDF.")
        
    return aderencia, alertas
