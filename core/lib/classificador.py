"""
Classificador unificado de perfil disciplinar, tipo de aula e recursos.

Centraliza a logica que tambem aparece em lote.py para que os modulos de
metodologia, acompanhamento, acessibilidade e extracao usem a mesma base.
"""

from __future__ import annotations

import re
from core.normalizacao import normalizar as normalizar_texto


def normalizar_compacto(texto: str) -> str:
    """Normaliza removendo também espaços para tolerar nomes com caracteres quebrados."""
    return re.sub(r"[\W_]+", "", normalizar_texto(texto))


def contem_termos(base: str, termos: list[str] | tuple[str, ...]) -> bool:
    """Verifica se algum dos termos aparece na string base."""
    base_normalizada = normalizar_texto(base)
    return any(normalizar_texto(termo) in base_normalizada for termo in termos)


def contem_termo_exato(base: str, termos: list[str] | tuple[str, ...]) -> bool:
    """Verifica correspondencia por palavra ou expressao inteira."""
    base_normalizada = normalizar_texto(base)
    for termo in termos:
        termo_normalizado = normalizar_texto(termo)
        if not termo_normalizado:
            continue
        if re.search(rf"(?<!\w){re.escape(termo_normalizado)}(?!\w)", base_normalizada):
            return True
    return False


def _turma_indica_ensino_medio(turma: str) -> bool:
    base = normalizar_texto(turma)
    return bool(
        base
        and (
            "ensino medio" in base
            or re.search(r"(?<!\d)[123]\s*ano\b", base)
            or re.search(r"(?<!\d)[123]\s*serie\b", base)
        )
    )


def perfil_disciplina(disciplina: str, turma: str = "") -> str:
    """Retorna o perfil pedagogico da disciplina."""
    base = normalizar_texto(disciplina)
    compacto = normalizar_compacto(disciplina)
    turma_base = normalizar_texto(turma)

    if ("orient" in base and "estud" in base) or "orienestudos" in base:
        return "orientacao_estudos"
    if compacto.startswith("orient") and "estud" in compacto:
        return "orientacao_estudos"
    if contem_termo_exato(base, ["orientacao de estudos", "orientacao estudos", "orienestudos"]):
        return "orientacao_estudos"
    if ("leitura" in compacto and "reda" in compacto) or ("reda" in compacto and "leitura" in compacto):
        return "leitura_redacao"
    if contem_termo_exato(base, ["redacao e leitura", "leitura e redacao"]):
        return "leitura_redacao"
    if contem_termo_exato(base, ["lingua portuguesa", "portugues"]) or "portugues" in compacto:
        if contem_termo_exato(base, ["ensino medio", "medio", "1 ano", "2 ano", "3 ano", "em"]) or _turma_indica_ensino_medio(turma_base):
            return "lingua_portuguesa_em"
        return "lingua_portuguesa_ef"
    if (compacto.startswith("ci") and compacto.endswith("ncias")) or "ciencias" in compacto:
        return "ciencias_ef"
    if contem_termo_exato(base, ["ciencias"]):
        return "ciencias_ef"
    if contem_termo_exato(base, ["biologia"]):
        return "biologia"
    if contem_termo_exato(base, ["quimica"]):
        return "quimica"
    if contem_termo_exato(base, ["fisica"]):
        return "fisica"
    if compacto.startswith("hist") and compacto.endswith("ria"):
        return "historia"
    if contem_termo_exato(base, ["historia"]):
        return "historia"
    if contem_termo_exato(base, ["geografia"]):
        return "geografia"
    if "ingles" in base or "english" in base:
        return "ingles"
    if contem_termo_exato(base, ["arte"]):
        return "arte"
    if "projeto" in compacto and "vida" in compacto:
        return "projeto_de_vida"
    if contem_termo_exato(base, ["projeto de vida"]):
        return "projeto_de_vida"
    if compacto.startswith("educa") and "financeira" in compacto:
        return "educacao_financeira"
    if contem_termo_exato(base, ["educacao financeira"]):
        return "educacao_financeira"
    if compacto.startswith("matem") and compacto.endswith("tica"):
        return "matematica"
    if contem_termo_exato(base, ["matematica"]):
        return "matematica"
    if contem_termo_exato(base, ["tecnologia e inovacao", "tecnologia", "inovacao"]):
        return "tecnologia_inovacao"
    if contem_termo_exato(base, ["sociologia"]):
        return "sociologia"
    if compacto.startswith("lideran") or "oratoria" in compacto:
        return "lideranca_oratoria"
    if contem_termo_exato(base, ["lideranca e oratoria", "lideranca", "oratoria"]):
        return "lideranca_oratoria"
    return "geral"


# ── Palavras-chave e função de classificação para Projeto de Vida ──────────

# Tipo 1 — Autoconhecimento e Reflexão Pessoal
_PV_AUTOCONHECIMENTO = [
    "autoconhecimento", "identidade", "valores", "interesses", "habilidades",
    "sonhos", "metas", "futuro profissional", "projeto de vida", "escolha profissional",
    "perfil profissional", "mapa de opcoes", "trajetoria", "planejamento",
    "quem sou eu", "quem quero ser", "meu futuro", "caminhos profissionais",
    "ensino superior", "curso tecnico", "empreendedorismo", "carreira",
    # termos adicionais da análise metodológica completa
    "quem sou eu", "o que valorizo", "meus interesses", "minhas habilidades",
    "caminhos profissionais", "planejando meu futuro", "planejando meu projeto",
]

# Tipo 2 — Plataforma Digital FutureMe
_PV_FUTUREME = [
    "futureme", "plataforma", "questionario de perfil profissional",
    "questionario de personalidade", "mapa de oportunidades", "podio dos cursos",
    "podio das profissoes", "guia das profissoes", "relatorio de perfil",
    "autoconhecimento profissional", "jornada do futuro", "sp.futureme.tech",
    # termos adicionais da análise metodológica completa
    "questionario de perfil", "passo a frente", "ssp109", "ppf109",
]

# Tipo 3 — Produção Coletiva e Projeto
_PV_PRODUCAO_COLETIVA = [
    "biomapa", "campanha", "bora cuidar", "cartaz", "panfleto", "faixa",
    "planejamento da campanha", "mensagens-chave", "divulgacao", "mobilizacao",
    "video de 1 minuto", "festival do minuto", "minuto escola", "hq",
    "historia em quadrinhos", "mostra", "produto final", "projeto bimestral",
    "caixa dos vinculos", "painel de convivencia",
    # termos adicionais da análise metodológica completa
    "producao coletiva", "em grupos", "grupos de", "antes que vire print",
    "grupos de seis", "grupos de quatro", "grupos de cinco",
]

# Tipo 4 — Convivência e Tomada de Decisão
_PV_CONVIVENCIA = [
    "circulo de convivencia", "tomada de decisao", "dilema", "votacao",
    "mediador", "secretario", "guardiao do tempo", "acordos de fala",
    "escuta ativa", "comunicacao nao violenta", "cnv", "gremio estudantil",
    "gestao democratica", "conselho escolar", "protagonismo juvenil",
    "convivencia", "conflito", "bullying", "painel de convivencia",
    # termos adicionais da análise metodológica completa
    "conselho de classe participativo", "apm", "decidir juntos", "decisao coletiva",
]

# Tipo 5 — Consciência Social e Engajamento
_PV_CONSCIENCIA_SOCIAL = [
    "privilegios", "desvantagens", "desigualdade", "vulnerabilidade",
    "desigualdade digital", "acesso a internet", "representatividade",
    "estereotipos", "inteligencia artificial", "vies", "engajamento",
    "consciencia social", "caminhada do privilegio", "ambiente digital",
    "inclusao", "exclusao", "diversidade",
    # termos adicionais da análise metodológica completa
    "passo a frente", "quem e mais vulneravel", "perfis subrepresentados",
    "leitura critica de midia", "vieses da ia", "vieses artificiais",
]

# Tipo 6 — Encerramento e Síntese
_PV_ENCERRAMENTO = [
    "pacto final", "sintese", "encerramento", "celebracao", "jornada",
    "o que aprendemos", "refletindo sobre a jornada", "caixa dos vinculos",
    "palavras que marcaram", "compromisso", "vinculos respeitosos",
    "mostra", "apresentacao final", "post-it", "mapa mental coletivo",
    # termos adicionais da análise metodológica completa
    "encerramento de bimestre", "sintese do bimestre", "pacto",
    "abrir a caixa", "reler o painel", "revisitar o mapa",
]


def _tipo_aula_projeto_de_vida(titulo: str, texto: str) -> str:
    """
    Classifica o tipo de aula de Projeto de Vida com base no título e texto.

    Retorna: 'futureme', 'encerramento', 'consciencia_social', 'convivencia',
             'producao_coletiva' ou 'autoconhecimento'.

    Prioridades (do mais específico ao mais genérico):
        1. futureme       — referência explícita à plataforma FutureMe
        2. encerramento   — síntese, pacto final, encerramento de bimestre
        3. consciencia_social — privilégios, desigualdades, vulnerabilidade
        4. convivencia    — círculo de convivência, dilema, votação coletiva
        5. producao_coletiva — biomapa, campanha, HQ, produto coletivo em grupos
        6. autoconhecimento — padrão para reflexão individual
    """
    titulo_norm = normalizar_texto(titulo)
    texto_norm = normalizar_texto(texto)
    base_norm = f"{titulo_norm} {texto_norm}"

    # 1. Plataforma Digital FutureMe (prioridade máxima)
    if contem_termos(base_norm, _PV_FUTUREME):
        return "futureme"

    # 2. Encerramento e Síntese
    if contem_termos(base_norm, _PV_ENCERRAMENTO):
        return "encerramento"

    # 3. Consciência Social e Engajamento
    if contem_termos(base_norm, _PV_CONSCIENCIA_SOCIAL):
        return "consciencia_social"

    # 4. Convivência e Tomada de Decisão
    if contem_termos(base_norm, _PV_CONVIVENCIA):
        return "convivencia"

    # 5. Produção Coletiva e Projeto
    if contem_termos(base_norm, _PV_PRODUCAO_COLETIVA):
        return "producao_coletiva"

    # Padrão: autoconhecimento e reflexão pessoal
    return "autoconhecimento"


# Alias para compatibilidade com nomes alternativos usados em outros módulos
_tipo_aula_projeto_vida = _tipo_aula_projeto_de_vida


# ── Palavras-chave e função de classificação para Língua Inglesa ──────────

_INGLES_MUSICA = ["song", "lyrics", "listen to the song", "sing along", "youtube", "music video"]
_INGLES_LEITURA_LITERARIA = ["literary", "novel", "character", "setting", "description", "golding", "montgomery", "lewis", "stoker", "rowling", "dahl"]
_INGLES_REVISAO = ["review", "revisao", "relembre", "retomar", "let's review", "remember", "last class", "aula anterior"]
_INGLES_LEITURA_EM = ["vestibular", "enem", "unesp", "unicamp", "saresp", "comic strip", "tirinha", "reading strategies", "multiple choice", "keywords", "cognates", "cognatas"]
_INGLES_LISTENING = ["listen to the audio", "listen to the conversation", "luvvoice", "fish audio", "script para o estudante surdo", "script", "surdo"]
_INGLES_PRODUCAO_ORAL = ["in pairs", "em duplas", "talk to your classmate", "speak in english", "tongue twister", "dialogue", "conversation", "dialogo"]
_INGLES_GRAMATICA = ["grammar", "gramatica", "simple past", "will", "going to", "conditional", "if clause", "irregular verbs", "regular verbs", "present simple", "like to", "to be"]
_INGLES_VOCABULARIO = ["learn these words", "practice pronunciation", "listen and repeat", "word bank", "banco de palavras", "glossario"]


def _tipo_aula_ingles(titulo: str, texto: str) -> str:
    """
    Classifica o tipo de aula de Língua Inglesa com base no título e texto.

    Retorna: 'musica', 'leitura_literaria', 'revisao', 'leitura_em', 'listening',
             'producao_oral', 'gramatica', 'vocabulario' ou 'leitura_em'.

    Prioridades (do mais específico ao mais genérico):
        1. musica             — referência a song, lyrics, etc.
        2. leitura_literaria  — termos literários ou autores específicos.
        3. revisao            — revisão, relembre, review, etc.
        4. leitura_em         — vestibular, enem, tirinhas, etc.
        5. listening          — áudio, listen to the audio, etc.
        6. producao_oral      — em duplas, in pairs, etc.
        7. gramatica          — grammar, simple past, conditional, etc.
        8. vocabulario        — learn these words, listen and repeat, etc.
        9. leitura_em         — padrão de fallback.
    """
    titulo_norm = normalizar_texto(titulo)
    texto_norm = normalizar_texto(texto)
    base_norm = f"{titulo_norm} {texto_norm}"

    if contem_termos(base_norm, _INGLES_MUSICA):
        return "musica"
    if contem_termos(base_norm, _INGLES_LEITURA_LITERARIA):
        return "leitura_literaria"
    if contem_termos(titulo_norm, _INGLES_REVISAO) or base_norm.count("relembre") >= 2:
        return "revisao"
    if contem_termos(base_norm, _INGLES_LEITURA_EM):
        return "leitura_em"
    if contem_termos(base_norm, _INGLES_LISTENING):
        return "listening"
    if contem_termos(base_norm, _INGLES_PRODUCAO_ORAL):
        return "producao_oral"
    if contem_termos(base_norm, _INGLES_GRAMATICA):
        return "gramatica"
    if contem_termos(base_norm, _INGLES_VOCABULARIO):
        return "vocabulario"
    return "leitura_em"


# ── Palavras-chave e função de classificação para Língua Portuguesa ────────

_LP_LEITURA_LITERARIA = [
    "cronica", "conto", "poema", "poesia", "narrativa", "leitura literaria",
    "genero literario", "eu lirico", "narrador", "enredo", "personagem",
    "metafora", "figuras de linguagem", "fruicao", "apreciacao",
    "machado de assis", "clarice lispector", "rubem braga", "carlos drummond",
    "marina colasanti", "conto indigena", "literatura",
]

_LP_GRAMATICA_CONTEXTUALIZADA = [
    "modo subjuntivo", "modo indicativo", "tempos verbais", "preterito",
    "futuro", "gerundio", "coesao", "elementos coesivos", "conjuncoes",
    "pronomes", "regencia verbal", "regencia nominal", "oracoes subordinadas",
    "adverbiais", "adjetivas", "modalizacao", "polissemia", "intertextualidade",
    "conectores", "anafora", "catafora",
]

_LP_LEITURA_JORNALISTICA = [
    "noticia", "editorial", "artigo de opiniao", "carta do leitor",
    "reportagem", "manchete", "lide", "tema central", "subtemas",
    "fato", "opiniao", "parcialidade", "imparcialidade", "veiculo",
    "jornalismo", "midia", "fonte", "intencionalidade",
    "resenha critica",
]

_LP_PRODUCAO_TEXTUAL = [
    "produza", "escreva uma carta", "redija", "elabore",
    "carta do leitor", "resenha", "artigo", "producao",
    "estrutura do genero", "publico-alvo", "suporte", "circulacao",
]

_LP_PESQUISA = [
    "scielo", "curadoria", "artigo cientifico", "plagio",
    "base de dados", "google academico", "fontes confiaveis",
    "divulgacao cientifica", "direitos autorais",
]


def _tipo_aula_lingua_portuguesa(titulo: str, texto: str) -> str:
    """
    Classifica o tipo de aula de Língua Portuguesa com base no título e texto.

    Retorna:
        'leitura_literaria', 'gramatica_contextualizada',
        'leitura_jornalistica', 'producao_textual' ou 'pesquisa'.

    Regra especial: se o título contém 'Parte 2', 'Parte 3' ou 'Parte 4'
    e o conteúdo traz termos de gramática contextualizada, retorna
    'gramatica_contextualizada'.
    """
    titulo_norm = normalizar_texto(titulo)
    texto_norm = normalizar_texto(texto)

    # Regra especial: aula de continuidade com foco gramatical
    if any(p in titulo_norm for p in ["parte 2", "parte 3", "parte 4"]):
        if contem_termos(texto_norm, _LP_GRAMATICA_CONTEXTUALIZADA):
            return "gramatica_contextualizada"

    # Pesquisa acadêmica
    if contem_termos(texto_norm, _LP_PESQUISA):
        return "pesquisa"

    # Produção textual
    if contem_termos(texto_norm, _LP_PRODUCAO_TEXTUAL):
        return "producao_textual"

    # Leitura jornalística
    if contem_termos(texto_norm, _LP_LEITURA_JORNALISTICA):
        if contem_termos(texto_norm, ["fato", "opiniao", "parcialidade", "veiculo", "intencionalidade", "manchete"]):
            return "leitura_jornalistica"

    # Gramática contextualizada
    if contem_termos(texto_norm, _LP_GRAMATICA_CONTEXTUALIZADA):
        return "gramatica_contextualizada"

    # Leitura literária (padrão para LP)
    return "leitura_literaria"


def _tipo_aula_lingua_portuguesa_em(titulo: str, texto: str) -> str:
    """Classifica o tipo de aula de Língua Portuguesa Ensino Médio com base no título e texto."""
    titulo_norm = normalizar_texto(titulo)
    texto_norm = normalizar_texto(texto)

    # 1. Aula de prática oral (debate, seminário)
    if any(k in titulo_norm for k in ["debate", "seminario", "apresentacao oral", "oralidade"]):
        return "pratica_oral"

    # 2. Aula de produção textual
    if any(k in titulo_norm for k in ["producao", "parte final", "escrita", "redigir", "elaborar"]):
        return "producao_textual"

    # 3. Aula de literatura
    if any(k in titulo_norm for k in [
        "trovadorismo", "modernismo", "romantismo", "realismo", "geracao",
        "guimaraes rosa", "clarice", "machado", "drummond", "literatura",
        "estetica", "vanguardas", "romance", "conto", "poema", "poesia"
    ]):
        return "literatura"

    # 4. Aula de gênero textual
    if any(k in titulo_norm for k in [
        "diario", "manifesto", "playlist", "cronica", "noticia",
        "reportagem", "resenha", "fanzine", "podcast", "genero"
    ]):
        return "genero_textual"

    # 5. Aula de gramática integrada (quando gramática é o foco principal)
    if any(k in titulo_norm for k in [
        "flexao", "regencia", "concordancia", "ortografia", "oracoes",
        "sintaxe", "semantica"
    ]):
        return "gramatica_integrada"

    # Verificação no texto_norm para fallbacks
    if any(k in texto_norm for k in ["debate", "seminario", "apresentacao oral"]):
        return "pratica_oral"
    if any(k in texto_norm for k in ["producao textual", "produzir texto", "escrever", "redigir"]):
        return "producao_textual"
    if any(k in texto_norm for k in ["trovadorismo", "modernismo", "romantismo", "realismo", "literatura"]):
        return "literatura"
    if any(k in texto_norm for k in ["diario", "manifesto", "playlist", "cronica", "genero textual"]):
        return "genero_textual"
    if any(k in texto_norm for k in ["flexao verbal", "regencia", "concordancia", "oracoes subordinadas"]):
        return "gramatica_integrada"

    # Default
    return "genero_textual"


_CIENCIAS_PRODUCAO_PROJETO = [
    "producao", "projeto", "seminario", "apresentacao", "cartilha",
    "campanha", "folder", "modelo", "de olho no modelo", "produto final",
]

_CIENCIAS_REVISAO = [
    "relembre", "retomar", "revisao", "anteriormente", "aulas anteriores",
    "exercicio resolvido", "no 1 bimestre estudamos", "consolidar",
]

_CIENCIAS_ESTUDO_CASO = [
    "estudo de caso", "situacao-problema", "situacao problema", "caso",
    "cenario", "analise o caso", "explique as consequencias", "fadiga",
    "radiacao", "atleta", "mitocondria", "cesio-137", "dna",
]

_CIENCIAS_LEITURA_ANALISE = [
    "hora da leitura", "texto", "noticia", "reportagem", "artigo",
    "dados do inpe", "dados do ibge", "agencia fapesp", "jornal da usp",
    "g1", "cnn brasil", "lei n", "anvisa", "fiocruz", "fonte",
]

_CIENCIAS_CONCEITO_NOVO = [
    "camadas da terra", "estrutura da terra", "foco no conteudo", "para comecar"
]

_BIOLOGIA_ETICO = [
    "bioetica", "etica", "hela", "consentimento", "patente",
    "clonagem", "terapia genica", "comite de etica",
    "pesquisa com seres humanos", "henrietta lacks", "dignidade", "sigilo",
    "beneficencia", "nao maleficencia", "justica", "cep", "conep"
]

_BIOLOGIA_DEBATE = [
    "darwinismo social", "eugenia", "racismo cientifico", "racismo estrutural",
    "discriminacao", "segregacao social", "segregacao racial", "pseudociencia", "determinismo biologico",
    "mengele", "nazismo", "branqueamento", "ancestralidade", "variabilidade genetica",
    "endogamia", "casamento consanguineo", "equidade", "diversidade"
]

_BIOLOGIA_MOLECULAR = [
    "dna", "rna", "nucleotideo", "base nitrogenada", "adenina", "timina",
    "citosina", "guanina", "uracila", "dupla helice", "replicacao",
    "transcricao", "traducao", "rna mensageiro", "mrna", "trna", "rrna",
    "rna polimerase", "helicase", "dna polimerase", "semiconservativo",
    "genoma", "gene", "genotipo", "fenotipo", "alelo", "homozigoto",
    "heterozigoto", "dominante", "recessivo", "mendel", "quadro de punnett",
    "heredograma", "cromossomo", "daltonismo", "hemofilia"
]

_BIOLOGIA_BIOTEC = [
    "biotecnologia", "engenharia genetica", "dna recombinante", "plasmideo",
    "clonagem reprodutiva", "clonagem terapeutica", "celulas-tronco",
    "terapia genica", "car-t", "insulina recombinante", "vacina", "soro",
    "anticorpo", "antigeno", "imunidade", "butantan", "fiocruz", "anvisa",
    "patente", "licenciamento compulsorio", "medicamento generico",
    "sistema imune", "imunidade inata", "imunidade adquirida", "linfocito",
    "macrofago", "neutrofilo", "leucocito", "soro antiofidico",
    "memoria imunologica", "imunizacao ativa", "imunizacao passiva",
    "variola", "ze gotinha"
]

_BIOLOGIA_REVISAO = [
    "relembre", "retomada", "revisao", "consolidacao", "consolidar", "retomar"
]

_BIOLOGIA_CONCEITO_NOVO = [
    "para comecar", "foco no conteudo", "um passo de cada vez",
    "pause e responda", "de olho no modelo", "fotossintese",
    "respiracao celular", "ecologia", "virus", "celula", "biomas",
    "metabolismo", "energia",
]


def _tipo_aula_ciencias(titulo: str, texto: str) -> str:
    """Classifica aulas de Ciencias EF conforme a analise metodologica."""
    titulo_norm = normalizar_texto(titulo)
    texto_norm = normalizar_texto(texto)
    base_norm = f"{titulo_norm} {texto_norm}"

    if contem_termos(base_norm, _CIENCIAS_PRODUCAO_PROJETO):
        return "producao_projeto"
    if contem_termos(base_norm, _CIENCIAS_REVISAO):
        return "revisao_retomada"
    if contem_termos(base_norm, _CIENCIAS_ESTUDO_CASO):
        return "estudo_caso"
    if contem_termos(base_norm, _CIENCIAS_LEITURA_ANALISE):
        return "leitura_analise"
    if contem_termos(base_norm, _CIENCIAS_CONCEITO_NOVO):
        return "conceito_novo"
    return "conceito_novo"


def _tipo_aula_biologia(titulo: str, texto: str) -> str:
    """Classifica aulas de Biologia conforme a análise metodológica."""
    titulo_norm = normalizar_texto(titulo)
    texto_norm = normalizar_texto(texto)
    base_norm = f"{titulo_norm} {texto_norm}"

    # Primeiro tenta pelo título para maior precisão usando termo exato
    if contem_termo_exato(titulo_norm, _BIOLOGIA_ETICO):
        return "etico_biotecnologico"
    if contem_termo_exato(titulo_norm, _BIOLOGIA_DEBATE):
        return "debate_critico"
    if contem_termo_exato(titulo_norm, _BIOLOGIA_MOLECULAR):
        return "molecular_genetico"
    if contem_termo_exato(titulo_norm, _BIOLOGIA_BIOTEC):
        return "aplicacao_biotecnologica"

    # Fallback para o texto completo usando termo exato
    if contem_termo_exato(base_norm, _BIOLOGIA_ETICO):
        return "etico_biotecnologico"
    if contem_termo_exato(base_norm, _BIOLOGIA_DEBATE):
        return "debate_critico"
    if contem_termo_exato(base_norm, _BIOLOGIA_MOLECULAR):
        return "molecular_genetico"
    if contem_termo_exato(base_norm, _BIOLOGIA_BIOTEC):
        return "aplicacao_biotecnologica"

    if contem_termo_exato(base_norm, _BIOLOGIA_REVISAO):
        return "revisao_aprofundamento"

    return "conceito_novo"


_TIPOS_MATEMATICA = [
    ("modelagem", ["modelagem", "modelar situacoes", "metodo de polya", "polya", "representar matematicamente", "sentenca matematica", "modelo matematico", "lei de formacao", "representacao algebrica", "equacionamento", "funcao como modelo"]),
    ("grandezas_medidas", ["grandeza", "razao", "proporcao", "velocidade media", "mbps", "kbps"]),
    ("algebra", ["equac", "equa", "variavel", "incognita", "express", "polinom", "sistema", "inequac", "logarit", "1 grau", "2 grau", "modulo"]),
    ("funcoes", ["func", "f(x)", "lei de formacao", "dominio", "imagem", "grafico de funcao", "taxa de variacao"]),
    ("combinatoria", ["combinat", "permut", "arranjo", "fatorial", "contagem", "ordem importa", "anagrama", "comissao", "placa", "senha", "principio aditivo", "principio multiplicativo", "principios de contagem", "diagrama de arvore", "arvore de possibilidades"]),
    ("estatistica_probabilidade", ["estatist", "probab", "media", "mediana", "moda", "amostra", "espaco amostral", "evento", "evento favoravel", "frequencia", "censo", "pesquisa"]),
    ("geometria", ["geometr", "area", "perimetro", "volume", "angulo", "triangulo", "figura", "solido", "pitagoras", "malha", "trigonom"]),
    ("numeros_operacoes", ["numero", "fracao", "decimal", "porcentagem", "potencia", "raiz", "divisibilidade", "operacao", "mmc", "mdc", "primo"]),
]


# ── Palavras-chave para classificação de tipo de aula de Matemática ─────────

_MAT_KHAN = ["khan", "bit.ly", "khanmigo", "khan academy", "proficiencia", "login"]
_MAT_VERIFICACAO = ["verificacao", "revisao", "relembre", "retomar", "consolidar", "sanar duvidas"]
_MAT_TECNOLOGIA = ["geogebra", "calculadora cientifica", "acesse o site", "geometria dinamica", "aplicativo"]
_MAT_MODELAGEM = ["modelagem", "modelo matematico", "lei de formacao", "representacao algebrica", "modelar"]
_MAT_GRAFICO = ["grafico", "representacao grafica", "plano cartesiano", "pares ordenados", "construindo graficos"]
_MAT_RESOLUCAO = ["resolucao de problemas", "metodo de polya"]


def _tipo_aula_matematica(titulo: str, texto: str) -> str:
    """
    Classifica o tipo de aula de Matemática com base no título e texto do PDF.

    Retorna: 'khan', 'verificacao', 'tecnologia', 'modelagem', 'grafico',
             'resolucao_problemas' ou 'conceito_novo'.

    Prioridades:
        1. khan  — estrutura completamente diferente, identificado por link/nome
        2. verificacao  — sem conceito novo, começa pela retomada
        3. tecnologia  — uso de GeoGebra, calculadora científica ou site
        4. modelagem  — tradução de situação real para linguagem algébrica
        5. grafico  — construção e leitura de representação gráfica
        6. resolucao_problemas  — método de Polya ou múltiplas atividades TME
        7. conceito_novo  — padrão quando nenhuma regra anterior se aplica
    """
    t = normalizar_texto(titulo)
    tx = normalizar_texto(texto)

    # 1. Aula Khan (prioridade máxima — estrutura completamente diferente)
    if contem_termos(t, _MAT_KHAN) or contem_termos(tx, ["bit.ly", "khanmigo"]):
        return "khan"

    # 2. Aula de verificação/revisão
    if contem_termos(t, _MAT_VERIFICACAO):
        return "verificacao"

    # 3. Aula com tecnologia
    if contem_termos(tx, _MAT_TECNOLOGIA):
        return "tecnologia"

    # 4. Aula de modelagem algébrica
    if contem_termos(t, _MAT_MODELAGEM):
        return "modelagem"

    # 5. Aula de representação gráfica
    if contem_termos(t, _MAT_GRAFICO):
        return "grafico"

    # 6. Aula de resolução de problemas
    if contem_termos(t, _MAT_RESOLUCAO) or tx.count("todo mundo escreve") >= 4:
        return "resolucao_problemas"

    # Padrão: aula de conceito novo
    return "conceito_novo"

_TIPOS_EDUCACAO_FINANCEIRA = [
    ("credito_endividamento", ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]),
    ("empreendedorismo", ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]),
    ("analise_percentuais_noticias", ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias", "manchetes", "noticias", "percentual", "porcentagem"]),
    ("governo_economia", ["papel do governo na economia", "governo na economia", "estado na economia", "politicas publicas", "impostos", "arrecadacao"]),
    ("impacto_decisoes_economicas", ["impacto das decisoes economicas", "decisoes economicas em nossas vidas", "impacto das escolhas economicas", "escolhas economicas"]),
    ("cidadania_financeira", ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]),
    ("instituicoes_financeiras", ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]),
    ("investimento_poupanca", ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]),
    ("orcamento_planejamento", ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]),
    ("consumo_consciente", ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]),
]

_TIPOS_TECNOLOGIA_INOVACAO = [
    ("programacao_inicial", ["startlab", "bloco diga", "bandeira verde", "blocos de eventos", "aparencia", "algoritmo", "programacao", "mensagens interativas", "criando com teclado"]),
    ("cultura_digital", ["cultura digital", "interacoes digitais", "forum", "emocoes", "etica", "respeito", "comportamentos respeitosos", "convivencia online"]),
    ("comunicacao_digital", ["perguntas claras", "duvidas corretamente", "fazer perguntas", "mensagem", "forum", "pedido de ajuda", "comunicacao clara", "perguntas inadequadas"]),
    ("consumo_tecnologia", ["obsolescencia", "lixo eletronico", "consumo excessivo", "consumo consciente", "descarte", "sustentabilidade", "impactos ambientais"]),
    ("dispositivos_entrada_saida", ["entrada e saida", "dispositivo de entrada", "dispositivo de saida", "teclado", "mouse", "monitor", "impressora", "microfone", "camera", "projetor", "caixa de som"]),
]

_TIPOS_GERAIS = [
    ("producao", ["producao textual", "produzir", "rascunho", "revisao", "reescrita", "redacao", "planejamento do texto"]),
    ("argumentacao", ["debate", "argumento", "opiniao", "tese", "ponto de vista", "carta de leitor"]),
    ("fonte_historica", ["fonte historica", "documento historico", "linha do tempo", "periodo historico", "cronologia"]),
    ("analise_geografica", ["mapa", "paisagem", "territorio", "regiao", "grafico", "escala", "cartografia"]),
    ("investigacao", ["experimento", "investigacao", "hipotese", "modelo", "observacao", "processo natural"]),
    ("resolucao_problemas", ["calculo", "problema", "porcentagem", "juros", "orcamento", "tabela", "grafico"]),
    ("lingua_estrangeira", ["vocabulary", "listen", "repeat", "speaking", "reading", "writing", "dialogue", "vocabulario", "escutar", "repetir", "falar", "ler", "escrever", "dialogo"]),
    ("arte_pratica", ["apreciacao", "criacao", "experimentacao", "musica", "imagem", "obra", "performance"]),
    ("reflexiva", ["autoconhecimento", "convivencia", "projeto de vida", "escolha", "respeito", "planejamento pessoal"]),
    ("leitura", ["leitura", "leia", "texto", "interpreta", "genero textual", "conto", "cronica", "anuncio", "publicidade", "publicitario", "slogan", "observe"]),
]

_MARCADORES_RECURSOS_PRIORITARIOS = {
    "analise_grafico": [
        "analise o grafico",
        "observe o grafico",
        "leia o grafico",
        "com base no grafico",
        "analise a tabela",
        "observe a tabela",
        "preencha a tabela",
        "complete a tabela",
        "com base na tabela",
    ],
    "analise_geografica": [
        "observe o mapa",
        "analise o mapa",
        "com base no mapa",
        "leia o mapa",
        "localize no mapa",
    ],
    "analise_imagem": [
        "observe a imagem",
        "analise a imagem",
        "leitura da imagem",
        "observe a charge",
        "analise a charge",
    ],
    "producao_textual": [
        "produza um texto",
        "escreva um texto",
        "produza uma resenha",
        "produza uma cronica",
        "produza uma carta",
        "rascunho",
        "revisao",
        "reescrita",
    ],
    "calculo_resolucao": [
        "resolva os calculos",
        "resolva as questoes",
        "calcule",
        "efetue",
        "determine o valor",
    ],
    "experimentacao": [
        "realize o experimento",
        "observe o experimento",
        "hipotese",
        "procedimento",
        "conclusao do experimento",
    ],
}


def _detectar_tipo_educacao_financeira_por_tema(tema_base: str) -> str | None:
    """Prioriza o titulo/tema para evitar contaminacao por texto auxiliar."""
    mapa_prioritario = [
        ("instituicoes_financeiras", ["onde guardamos o dinheiro", "guardar dinheiro", "onde guardar o dinheiro", "guardamos o dinheiro"]),
        ("investimento_poupanca", ["por que poupamos", "porque poupamos", "reserva de emergencia", "poupamos"]),
        ("orcamento_planejamento", ["objetivos em familia ou em grupo", "objetivos em familia", "objetivos em grupo", "planejamento financeiro"]),
        ("analise_percentuais_noticias", ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias"]),
        ("governo_economia", ["papel do governo na economia", "governo na economia"]),
        ("impacto_decisoes_economicas", ["impacto das decisoes economicas", "decisoes economicas em nossas vidas"]),
    ]
    for tipo, termos in mapa_prioritario:
        if contem_termos(tema_base, termos):
            return tipo
    return None


def _detectar_tipo_por_catalogo(
    tema_base: str,
    texto_base: str,
    catalogo: list[tuple[str, list[str]]],
    default: str,
) -> str:
    for tipo, termos in catalogo:
        if contem_termo_exato(tema_base, termos) or contem_termos(tema_base, termos):
            return tipo
    for tipo, termos in catalogo:
        if contem_termo_exato(texto_base, termos) or contem_termos(texto_base, termos):
            return tipo
    return default


def detectar_tipo_aula(texto: str, tema: str, disciplina: str = "", turma: str = "") -> str:
    """Classifica o tipo de aula a partir do conteudo."""
    base = normalizar_texto(f"{disciplina} {tema} {texto}")
    tema_base = normalizar_texto(tema)
    perfil = perfil_disciplina(disciplina, turma=turma)

    if perfil == "educacao_financeira":
        _EF_AULA_PRATICA = [
            "pesquisa de precos", "elaborar uma tabela", "simular gastos",
            "dividir os alunos em trios", "trabalhar de forma individual",
            "material impresso como guia", "sentar em circulo para compartilhar",
            "pesquisa de preços", "elaborar uma planilha", "simular despesas",
            "planejamento pratico", "planejamento prático",
        ]
        if contem_termos(base, _EF_AULA_PRATICA):
            return "aula_pratica_continuidade"

        tipo_por_tema = _detectar_tipo_educacao_financeira_por_tema(tema_base)
        if tipo_por_tema:
            return tipo_por_tema
        return _detectar_tipo_por_catalogo(tema_base, base, _TIPOS_EDUCACAO_FINANCEIRA, "decisao_financeira")

    if perfil == "matematica":
        # Classificador especializado por tipo de aula (khan, verificacao, tecnologia,
        # modelagem, grafico, resolucao_problemas, conceito_novo)
        tipo_mat = _tipo_aula_matematica(tema, texto)
        # Se o classificador especializado retornou um tipo metodológico, usa-o.
        # Para conteúdo matemático (algebra, funcoes etc.) complementa com catálogo.
        if tipo_mat != "conceito_novo":
            return tipo_mat
        # Para conceito_novo, tenta refinar o sub-tipo de conteúdo via catálogo.
        tipo_conteudo = _detectar_tipo_por_catalogo(tema_base, base, _TIPOS_MATEMATICA, "")
        return tipo_conteudo if tipo_conteudo else tipo_mat

    if perfil == "tecnologia_inovacao":
        return _detectar_tipo_por_catalogo(tema_base, base, _TIPOS_TECNOLOGIA_INOVACAO, "tecnologia_geral")

    # Língua Inglesa — classificador especializado
    if perfil == "ciencias_ef":
        return _tipo_aula_ciencias(tema, texto)

    if perfil == "biologia":
        return _tipo_aula_biologia(tema, texto)

    if perfil == "ingles":
        return _tipo_aula_ingles(tema, texto)

    # Língua Portuguesa — classificador especializado
    if perfil == "lingua_portuguesa_em":
        return _tipo_aula_lingua_portuguesa_em(tema, texto)
    if perfil in {"lingua_portuguesa_ef", "leitura_redacao"}:
        return _tipo_aula_lingua_portuguesa(tema, texto)

    # Projeto de Vida — classificador especializado
    if perfil == "projeto_de_vida":
        return _tipo_aula_projeto_de_vida(tema, texto)

    for tipo, termos in _TIPOS_GERAIS:
        if contem_termo_exato(tema_base, termos) or contem_termos(tema_base, termos):
            return tipo
    for tipo, termos in _TIPOS_GERAIS:
        if contem_termo_exato(base, termos) or contem_termos(base, termos):
            return tipo

    return "geral"


_RECURSOS_DETECTAVEIS = {
    "leitura_texto": ["leitura", "leia", "texto", "trecho", "conto", "cronica", "poema", "artigo", "noticia"],
    "analise_imagem": ["imagem", "ilustracao", "foto", "fotografia", "pintura", "obra", "charge"],
    "analise_grafico": ["grafico", "tabela", "dados", "infografico", "mapa"],
    "calculo_resolucao": ["calcule", "resolva", "operacao", "equacao", "formula", "expressao"],
    "producao_textual": ["producao", "escreva", "redija", "rascunho", "reescrita", "revisao"],
    "experimentacao": ["experimento", "observacao", "laboratorio", "material", "procedimento"],
    "debate_oral": ["debate", "discussao", "opiniao", "argumento", "apresentacao", "oralidade"],
    "escuta_audio": ["audio", "musica", "som", "podcast", "video", "assista"],
}


def detectar_recursos(texto: str, tema: str = "") -> list[str]:
    """Detecta tipos de recursos/atividades presentes no conteudo."""
    base = normalizar_texto(f"{tema} {texto}")
    recursos = [
        recurso
        for recurso, marcadores in _MARCADORES_RECURSOS_PRIORITARIOS.items()
        if any(marcador in base for marcador in marcadores)
    ]
    if recursos:
        return recursos
    recursos = [
        recurso
        for recurso, termos in _RECURSOS_DETECTAVEIS.items()
        if contem_termo_exato(base, termos) or contem_termos(base, termos)
    ]
    return recursos or ["leitura_texto"]
