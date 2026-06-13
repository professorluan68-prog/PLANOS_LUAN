from __future__ import annotations

import random
import re
import unicodedata

from dataclasses import dataclass, field
from typing import Dict, List

from core.lib.extrator_blocos_pedagogicos import extrair_blocos_pedagogicos
from core.normalizacao import normalizar as norm


def clean(txt: str) -> str:
    return re.sub(r"\s+", " ", (txt or "")).strip()


def sentenca(txt: str) -> str:
    txt = clean(txt)
    if not txt:
        return ""
    if txt[-1] not in ".!?":
        txt += "."
    return txt[0].upper() + txt[1:]


def dedup(seq: List[str]) -> List[str]:
    out = []
    seen = set()
    for item in seq:
        key = norm(item)
        if key and key not in seen:
            seen.add(key)
            out.append(clean(item))
    return out


def deterministic_choice(options: List[str], seed_key: str) -> str:
    if not options:
        return ""
    rng = random.Random(seed_key)
    return rng.choice(options)


@dataclass
class PistasPedagogicas:
    titulo: str = ""
    conteudos: List[str] = field(default_factory=list)
    objetivos: List[str] = field(default_factory=list)
    vocabulario_chave: List[str] = field(default_factory=list)

    tem_para_comecar: bool = False
    tem_relembre: bool = False
    tem_foco_conteudo: bool = False
    tem_pause_responda: bool = False
    tem_atividade_final: bool = False
    tem_video: bool = False

    tem_grafico: bool = False
    tem_tabela: bool = False
    tem_calculo: bool = False
    tem_comparacao: bool = False
    tem_estudo_caso: bool = False
    tem_situacao_problema: bool = False
    tem_noticia: bool = False
    tem_imagem_inicial: bool = False
    tem_mapa: bool = False
    tem_leitura_guiada: bool = False
    tem_construcao_conceito: bool = False
    tem_analise_linguistica: bool = False

    tecnicas_lemov: List[str] = field(default_factory=list)

    perfil: str = "geral"
    verbo_objetivo: str = "compreender"


TECNICAS_LEMOV = {
    "virem e conversem": "Virem e conversem",
    "todo mundo escreve": "Todo mundo escreve",
    "com suas palavras": "Com suas palavras",
    "um passo de cada vez": "Um passo de cada vez",
    "de olho no modelo": "De olho no modelo",
    "hora da leitura": "Hora da leitura",
    "pausa produtiva": "Pausa produtiva",
}

VERBOS_OBJETIVO = [
    "analisar", "comparar", "interpretar", "reconhecer", "explicar",
    "avaliar", "identificar", "planejar", "aplicar", "justificar",
]

PALAVRAS_GRAFICO = ["grafico", "gráfico", "grafico de", "gráfico de", "eixo", "eixos", "fluxo de refugiados"]
PALAVRAS_TABELA = ["tabela", "tabelas", "quadro comparativo", "quadro-sintese", "quadro síntese"]
PALAVRAS_CALCULO = ["juros", "porcentagem", "percentual", "cálculo", "calculo", "rendimento"]
PALAVRAS_COMPARACAO = ["comparar", "comparação", "comparacao", "diferença", "diferenca", "sinônimos", "sinonimos"]
PALAVRAS_ESTUDO_CASO = ["situação", "situacao", "caso", "estudante de 25 anos", "um rapaz se mudou"]
PALAVRAS_NOTICIA = ["leia a notícia", "leia a noticia", "notícia", "noticia", "manchete", "reportagem"]
PALAVRAS_IMAGEM = ["observe as imagens", "observe a imagem", "imagem de satélite", "imagem de satelite"]
PALAVRAS_MAPA = ["mapa interativo", "fluxo de migração", "fluxo de migracao", "legenda", "países ou regiões", "paises ou regioes"]
PALAVRAS_LEITURA = ["leia", "leitura", "hora da leitura"]
PALAVRAS_CONSTRUCAO_CONCEITO = ["construindo o conceito"]
PALAVRAS_DEBATE = ["virem e conversem", "com suas palavras", "para refletir"]
PALAVRAS_ANALISE_LINGUISTICA = [
    "ordem direta", "ordem inversa", "hiperbato", "hipérbato", "conjuncoes", "conjunções",
    "regencia verbal", "regência verbal", "regencia nominal", "regência nominal",
    "oracoes subordinadas", "orações subordinadas", "modalizacao", "modalização",
    "analise sintatica", "análise sintática",
]


def extrair_bullets_secao(texto: str, marcador_secao: str) -> List[str]:
    linhas = [l.strip() for l in texto.replace("●", "\n● ").splitlines() if l.strip()]
    secao = False
    itens = []

    for linha in linhas:
        n = norm(linha)
        if marcador_secao in n:
            secao = True
            continue

        if secao and any(rot in n for rot in ["objetivos", "conteudos", "conteúdos", "habilidades", "recursos didaticos", "duração da aula", "duracao da aula"]) and marcador_secao not in n:
            break

        if secao and linha.startswith("●"):
            itens.append(linha.lstrip("●").strip(" ;:."))

    return dedup(itens)


def extrair_conteudos_objetivos(texto: str) -> Dict[str, List[str]]:
    return {
        "conteudos": extrair_bullets_secao(texto, "conteudos"),
        "objetivos": extrair_bullets_secao(texto, "objetivos"),
    }


def detectar_tecnicas(texto: str) -> List[str]:
    t = norm(texto)
    achadas = []
    for chave, nome in TECNICAS_LEMOV.items():
        if chave in t:
            achadas.append(nome)
    return dedup(achadas)


def detectar_verbo_objetivo(objetivos: List[str]) -> str:
    n = norm(" ".join(objetivos))
    for verbo in VERBOS_OBJETIVO:
        if verbo in n:
            return verbo
    return "compreender"


def extrair_vocabulario_chave(conteudos: List[str], objetivos: List[str], titulo: str) -> List[str]:
    candidatos = []
    if titulo:
        titulo_limpo = re.sub(r"^\s*aula\s*\d+\s*-\s*", "", titulo, flags=re.I)
        candidatos.append(titulo_limpo)

    candidatos.extend(conteudos[:4])

    for obj in objetivos[:4]:
        obj_limpo = re.sub(
            r"^(explicar|reconhecer|analisar|comparar|avaliar|identificar|interpretar|planejar|aplicar|justificar)\s+",
            "",
            obj,
            flags=re.I,
        )
        candidatos.append(obj_limpo.strip(" ;:."))

    saida = []
    for candidato in candidatos:
        candidato = clean(candidato)
        if 4 <= len(candidato) <= 90:
            saida.append(candidato)

    return dedup(saida)[:6]


_REGRAS_PERFIL_LP = [
    ("texto_publicitario", [
        "anuncie aqui", "anuncio publicitario", "anúncio publicitário",
        "propaganda", "publicidade", "slogan", "jingle",
        "campanha publicitaria", "campanha publicitária",
        "advergame", "unboxing", "social advertising",
    ]),
    ("diario_pessoal", [
        "diario pessoal", "diÃ¡rio pessoal",
        "genero diario pessoal", "gÃªnero diÃ¡rio pessoal",
        "reflexoes do cotidiano", "reflexÃµes do cotidiano",
    ]),
    ("biografia", [
        "historia de uma vida", "história de uma vida",
        "biografia", "trajetoria", "trajetória",
        "vida de", "carreira", "nascimento",
        "mapa conceitual", "lygia fagundes telles",
    ]),
    ("noticia_multimodal", [
        "jornalismo em imagens", "fotojornalismo",
        "fotojornalistico", "fotojornalístico",
        "recursos visuais em textos jornalisticos",
        "recursos visuais em textos jornalísticos",
        "textos jornalisticos digitais",
        "textos jornalísticos digitais",
        "fotos e videos", "fotos e vídeos",
        "intencionalidade das imagens",
    ]),
    ("leitura_multimodal", [
        "cartaz", "campanha", "infografico", "infografico",
        "tirinha", "charge", "texto verbal", "texto nao verbal",
        "linguagem verbal e nao verbal", "multimodal",
        "multissemotico", "multissemiotico",
    ]),
    ("resumo_retextualizacao", [
        "resumir", "resumo", "retextualizacao",
        "esquema", "notas", "topicos",
        "topico frasal", "paragrafacao",
        "paragrafos", "coesao", "coerencia",
    ]),
    ("variacao_linguistica_registro", [
        "regionalismo", "registro formal",
        "registro informal", "giria", "girias",
        "preconceito linguistico", "biscoito", "bolacha",
    ]),
    ("argumentacao_debate", [
        "contra argumento", "contra-argumento",
        "debate", "refutar", "planejar debate",
        "celular em sala", "celular na escola",
    ]),
    ("texto_digital_blog", [
        "post de blog", "blog", "postagem", "internet",
        "comentario", "a voz da internet",
        "mulheres na universidade", "publico leitor",
    ]),
    ("analise_linguistica_ortografia", [
        "ortografia", "concordancia nominal",
        "discurso direto", "discurso indireto", "marcas linguisticas",
        "paragrafacao", "topico frasal", "x ou ch", "sc", "cedilha",
    ]),
    ("conto_distopico", [
        "conto distopico", "conto distópico",
        "narrativa distopica", "narrativa distópica",
        "distopia", "distopico", "distópico",
        "olhos por bugalhos",
        "uma narrativa pode moldar uma imagem",
    ]),
    ("literatura_prosa", [
        "prosa de 30", "prosa regionalista",
        "romance regionalista", "sertao", "sertão",
        "seca", "retirantes", "o quinze", "vidas secas",
        "capitaes da areia", "capitães da areia",
        "rachel de queiroz", "graciliano ramos", "jorge amado",
    ]),
    ("literatura_modernismo", [
        "semana de arte moderna", "vanguardas europeias",
        "vanguardas", "modernismo", "modernista",
        "mario de andrade", "mário de andrade",
        "oswald de andrade", "drummond", "murilo mendes",
        "manuel bandeira", "manifesto literario", "manifesto literário",
    ]),
    ("poema", [
        "poema", "soneto", "verso", "estrofe",
        "eu lirico", "eu lírico", "rima", "metrica", "métrica",
        "carpe diem", "fugere urbem",
    ]),
    ("cronica", ["cronica", "crônica", "genero cronica", "gênero crônica"]),
    ("editorial_argumentativo", ["editorial", "editoriais", "texto opinativo"]),
    ("artigo_opiniao", [
        "artigo de opiniao", "artigo de opinião",
        "construcao da opiniao", "construção da opinião",
        "tese", "argumentos", "posicionamento",
        "ponto de vista", "persuadir",
    ]),
    ("oralidade_entrevista", [
        "oralidade", "entrevista oral", "entrevista",
        "turnos de fala", "marcas de oralidade",
        "transcricao", "transcrição",
        "variacao linguistica", "variação linguística", "podcast",
    ]),
    ("texto_normativo", [
        "estatuto da pessoa idosa", "constituicao federal",
        "constituição federal", "texto normativo",
        "textos legais", "texto legal", "normas", "direitos assegurados",
    ]),
    ("gramatica_analise_linguistica", [
        "ordem direta", "ordem inversa", "hiperbato", "hipérbato",
        "conjuncoes", "conjunções", "regencia verbal", "regência verbal",
        "regencia nominal", "regência nominal",
        "oracoes subordinadas", "orações subordinadas",
        "modalizacao", "modalização",
        "analise sintatica", "análise sintática",
    ]),
]


def classificar_perfil(
    texto: str,
    titulo: str,
    conteudos: List[str],
    objetivos: List[str],
    blocos: Dict[str, str],
    perfil: str = None,
) -> str:
    """
    Classifica o perfil pedagógico da aula com base no conteúdo do PDF.
    Usa tabela de regras em ordem de prioridade.
    """
    base = " ".join([texto, titulo] + conteudos + objetivos)
    n = norm(base)

    # Verificar regras em ordem de prioridade
    perfis_lp_permitidos = {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}
    if perfil is None or perfil in perfis_lp_permitidos:
        if any(t in n for t in ["ortografia", "concordancia nominal", "discurso direto", "discurso indireto", "x ou ch"]):
            return "analise_linguistica_ortografia"
        if any(t in n for t in ["resumo", "retextualizacao", "topico frasal", "paragrafacao"]) and any(
            t in n for t in ["infografico", "esquema", "topicos", "paragrafos", "notas"]
        ):
            return "resumo_retextualizacao"
        if any(t in n for t in ["preconceito linguistico", "biscoito", "bolacha", "regionalismo"]) and any(
            t in n for t in ["variacao linguistica", "registro formal", "registro informal", "lingua viva"]
        ):
            return "variacao_linguistica_registro"
        if any(t in n for t in ["post de blog", "a voz da internet", "publico leitor"]) and any(
            t in n for t in ["comentario", "internet", "blog", "postagem"]
        ):
            return "texto_digital_blog"
        if any(t in n for t in ["contra argumento", "contra-argumento", "planejar debate", "celular em sala", "celular na escola"]):
            return "argumentacao_debate"
        for perfil_nome, termos in _REGRAS_PERFIL_LP:
            for termo in termos:
                termo_norm = norm(termo)
                if not termo_norm:
                    continue
                # Busca exata com limites de palavra
                if re.search(rf"(?<!\w){re.escape(termo_norm)}(?!\w)", n):
                    return perfil_nome

    # Regras compostas que dependem de múltiplos sinais
    tem_noticia = any(norm(p) in n for p in PALAVRAS_NOTICIA)
    tem_imagem = any(norm(p) in n for p in PALAVRAS_IMAGEM)
    tem_mapa = any(norm(p) in n for p in PALAVRAS_MAPA)
    tem_comparacao = any(norm(p) in n for p in PALAVRAS_COMPARACAO)
    tem_grafico = any(norm(p) in n for p in PALAVRAS_GRAFICO)
    tem_xenofobia = "xenofobia" in n
    tem_refugiado = "refugiado" in n or "refugiados" in n
    tem_migracao_legal_ilegal = "migracao legal e ilegal" in n or (
        "migrante legal" in n and "migrante ilegal" in n
    )
    tem_estado = any(t in n for t in [
        "estado", "documentos internacionais", "direitos",
        "restricoes", "restrições", "soberania", "fronteiras",
    ])

    if tem_xenofobia and tem_noticia:
        return "noticia_leitura_critica"
    if tem_migracao_legal_ilegal and (tem_imagem or "virem e conversem" in n) and tem_estado:
        return "imagem_debate_direitos"
    if tem_refugiado and tem_comparacao:
        return "comparacao_conceitual"
    if tem_mapa and "migracao" in n:
        return "mapa_fluxos_migratorios"
    if tem_grafico and tem_refugiado:
        return "grafico_fluxos_refugiados"
    if tem_comparacao:
        return "comparacao_conceitual"
    if tem_noticia:
        return "noticia_leitura_critica"
    if tem_imagem:
        return "imagem_debate"
    if "construindo o conceito" in n or blocos.get("Construindo o conceito"):
        return "conceito_reflexivo"

    return "geral"


def extrair_pistas(texto_pdf: str, titulo_aula: str, perfil: str = None) -> PistasPedagogicas:
    texto_pdf = texto_pdf or ""
    listas = extrair_conteudos_objetivos(texto_pdf)
    conteudos = listas["conteudos"]
    objetivos = listas["objetivos"]
    blocos = extrair_blocos_pedagogicos(texto_pdf)
    n = norm(texto_pdf)

    pistas = PistasPedagogicas(
        titulo=clean(titulo_aula),
        conteudos=conteudos,
        objetivos=objetivos,
        vocabulario_chave=extrair_vocabulario_chave(conteudos, objetivos, titulo_aula),

        tem_para_comecar=bool(blocos.get("Para comecar")) or ("para comecar" in n) or bool(blocos.get("Ponto de partida")),
        tem_relembre=bool(blocos.get("Relembre")) or ("relembre" in n),
        tem_foco_conteudo=bool(blocos.get("Foco no conteudo")) or ("foco no conteudo" in n) or bool(blocos.get("Construindo o conceito")),
        tem_pause_responda=bool(blocos.get("Pause e responda")) or ("pause e responda" in n),
        tem_atividade_final=bool(blocos.get("Na pratica")) or ("na pratica" in n or "desafio" in n),
        tem_video=("link para video" in n or "assista ao video" in n),

        tem_grafico=any(p in n for p in [norm(x) for x in PALAVRAS_GRAFICO]),
        tem_tabela=any(p in n for p in [norm(x) for x in PALAVRAS_TABELA]),
        tem_calculo=any(p in n for p in [norm(x) for x in PALAVRAS_CALCULO]),
        tem_comparacao=any(p in n for p in [norm(x) for x in PALAVRAS_COMPARACAO]),
        tem_estudo_caso=any(p in n for p in [norm(x) for x in PALAVRAS_ESTUDO_CASO]),
        tem_situacao_problema=("problema" in n or "questoes abaixo" in n or "responda às perguntas" in texto_pdf.lower() or "responda as perguntas" in n),
        tem_noticia=any(p in n for p in [norm(x) for x in PALAVRAS_NOTICIA]),
        tem_imagem_inicial=any(p in n for p in [norm(x) for x in PALAVRAS_IMAGEM]),
        tem_mapa=any(p in n for p in [norm(x) for x in PALAVRAS_MAPA]),
        tem_leitura_guiada=any(p in n for p in [norm(x) for x in PALAVRAS_LEITURA]),
        tem_construcao_conceito=any(p in n for p in [norm(x) for x in PALAVRAS_CONSTRUCAO_CONCEITO]),
        tem_analise_linguistica=any(p in n for p in [norm(x) for x in PALAVRAS_ANALISE_LINGUISTICA]),
        tecnicas_lemov=detectar_tecnicas(texto_pdf),
    )

    pistas.perfil = classificar_perfil(texto_pdf, titulo_aula, conteudos, objetivos, blocos, perfil=perfil)
    pistas.verbo_objetivo = detectar_verbo_objetivo(objetivos)
    return pistas


def sanitizar_texto_pedagogico(txt: str) -> str:
    txt = clean(txt)
    txt = txt.replace("..", ".")
    txt = re.sub(r"\s+,", ",", txt)
    txt = re.sub(r"\s+\.", ".", txt)
    # Remover apenas quando o termo está no início ou fim da frase,
    # ou isolado entre vírgulas/pontos — nunca no meio de uma frase
    txt = re.sub(r"(?:^|\.\s+)2o bimestre\b", "", txt, flags=re.I)
    txt = re.sub(r"(?:^|\.\s+)ensino medio\b", "", txt, flags=re.I)
    # "aula N" pode ser removido com segurança pois é sempre referência isolada
    txt = re.sub(r"\baula \d+\b\s*[-:–]?\s*", "", txt, flags=re.I)
    txt = txt.strip(" -:;,")
    txt = clean(txt)
    return sentenca(txt)


_FINAIS_INVALIDOS_FRASE = frozenset({
    "a", "as", "o", "os", "um", "uma",
    "de", "da", "do", "das", "dos",
    "em", "e", "com", "para", "por",
    "que", "se", "na", "no", "nas", "nos",
    "ao", "aos", "à", "às",
})


def validar_frase_completa(texto: str) -> bool:
    """
    Verifica se uma frase parece completa (não termina com preposição ou artigo).
    Retorna True se a frase parece completa, False se parece truncada.
    """
    texto = clean(texto).rstrip(".!?")
    if not texto:
        return False
    ultima_palavra = texto.split()[-1].lower().rstrip(".,;:")
    return ultima_palavra not in _FINAIS_INVALIDOS_FRASE


def sanitizar_e_validar(txt: str, fallback: str = "") -> str:
    """
    Sanitiza o texto pedagógico e verifica se está completo.
    Se truncado, retorna o fallback.
    """
    resultado = sanitizar_texto_pedagogico(txt)
    if not validar_frase_completa(resultado):
        return sanitizar_texto_pedagogico(fallback) if fallback else resultado
    return resultado


def bloquear_contaminacao_tematica(texto: str, pistas: PistasPedagogicas) -> str:
    n = norm(texto)

    if pistas.perfil in {
        "noticia_leitura_critica",
        "imagem_debate",
        "imagem_debate_direitos",
        "comparacao_conceitual",
        "conceito_reflexivo",
        "mapa_fluxos_migratorios",
    } and not pistas.tem_grafico and not pistas.tem_tabela:
        for termo in [
            "graficos, tabelas ou dados",
            "gráficos, tabelas ou dados",
            "eixos, valores",
            "localizar dados relevantes",
        ]:
            if norm(termo) in n:
                return ""
    return texto


def frase_inicial(p: PistasPedagogicas) -> str:
    opcoes = []

    if p.perfil == "texto_publicitario":
        return "Iniciar a aula retomando anúncios e campanhas conhecidos pelos estudantes, observando como linguagem verbal, imagem, som e contexto buscam persuadir o público."
    if p.perfil == "diario_pessoal":
        return "Iniciar a aula retomando situaÃ§Ãµes do cotidiano em que as pessoas registram vivÃªncias, sentimentos e reflexÃµes, preparando a turma para reconhecer caracterÃ­sticas do diÃ¡rio pessoal."
    if p.perfil == "diario_pessoal":
        return "Propor atividade de leitura e anÃ¡lise para que os estudantes identifiquem caracterÃ­sticas do diÃ¡rio pessoal, observem marcas de subjetividade e registrem como o autor organiza experiÃªncias e reflexÃµes."
    if p.perfil == "diario_pessoal":
        return "Propor atividade de leitura e analise para que os estudantes identifiquem caracteristicas do diario pessoal, observem marcas de subjetividade e registrem como o autor organiza experiencias e reflexoes."
    if p.perfil == "biografia":
        return "Iniciar a aula apresentando a trajetória da pessoa biografada e mobilizando conhecimentos prévios sobre como fatos de vida podem ser organizados em texto e mapa conceitual."
    if p.perfil == "noticia_multimodal":
        return "Iniciar a aula observando como notícias digitais articulam texto, fotos e vídeos para informar e produzir efeitos de sentido no leitor."
    if p.perfil == "leitura_multimodal":
        return "Iniciar a aula com observacao orientada de cartaz, infografico, tirinha ou imagem do material, mobilizando hipoteses sobre a mensagem, o publico e a finalidade comunicativa."
    if p.perfil == "resumo_retextualizacao":
        return "Iniciar a aula retomando o esquema, a lista ou o infografico do material para que a turma identifique quais informacoes merecem ser transformadas em texto organizado."
    if p.perfil == "variacao_linguistica_registro":
        return "Iniciar a aula apresentando situacoes reais de uso da lingua, aproximando a turma de exemplos de variacao, registro e adequacao ao contexto."
    if p.perfil == "argumentacao_debate":
        return "Iniciar a aula com tema polemico e proximo da vivencia da turma, incentivando os estudantes a diferenciar opiniao espontanea de argumento fundamentado."
    if p.perfil == "texto_digital_blog":
        return "Iniciar a aula retomando a leitura do post de blog e mobilizando conhecimentos previos sobre interlocutor, comentario, registro e circulacao do texto digital."
    if p.perfil == "analise_linguistica_ortografia":
        return "Iniciar a aula retomando trechos do proprio material para que a turma observe como escolhas ortograficas e linguisticas aparecem em uso real."
    if p.perfil == "leitura_multimodal":
        return "Propor atividade de leitura e registro para que os estudantes relacionem imagem, texto verbal, legenda e dados do material, justificando como esses elementos constroem a mensagem."
    if p.perfil == "resumo_retextualizacao":
        return "Propor atividade de retextualizacao para que os estudantes transformem topicos, listas ou informacoes do infografico em paragrafos coerentes, evitando copia mecanica."
    if p.perfil == "variacao_linguistica_registro":
        return "Propor atividade de classificacao e registro para que os estudantes identifiquem exemplos de variacao linguistica e expliquem a adequacao de cada uso ao contexto."
    if p.perfil == "argumentacao_debate":
        return "Propor atividade de analise e planejamento para que os estudantes selecionem argumentos e contra-argumentos, registrem evidencias e preparem posicionamento para debate."
    if p.perfil == "texto_digital_blog":
        return "Propor atividade de comentario ou resposta para que os estudantes retomem o post de blog, mobilizem argumentos e escrevam com clareza e respeito ao interlocutor."
    if p.perfil == "analise_linguistica_ortografia":
        return "Propor atividade aplicada para que os estudantes retomem palavras, frases ou trechos do material, analisem o recurso linguistico estudado e revisem a escrita em contexto."
    if p.perfil == "conto_distopico":
        return "Iniciar a aula situando a narrativa distópica e levantando hipóteses sobre narrador, personagens, conflito e atmosfera de tensão presentes no conto."
    if p.perfil == "literatura_prosa":
        return "Iniciar a aula situando o texto literário no contexto da obra, do autor e do período estudado, mobilizando conhecimentos prévios sobre a prosa brasileira."
    if p.perfil == "literatura_modernismo":
        return "Iniciar a aula contextualizando o movimento literário estudado, destacando rupturas estéticas, autores e relações com o momento histórico."
    if p.perfil == "poema":
        return "Iniciar a aula aproximando os estudantes do poema, observando título, organização em versos, voz poética e primeiras impressões de leitura."
    if p.perfil == "cronica":
        return "Iniciar a aula aproximando o tema da crônica de situações cotidianas conhecidas pelos estudantes, preparando a turma para observar linguagem, voz narrativa e efeitos de sentido."
    if p.perfil == "artigo_opiniao":
        return "Iniciar a aula mobilizando conhecimentos prévios sobre opinião, tese e argumentação, preparando a turma para reconhecer ponto de vista e estratégias persuasivas."
    if p.perfil == "editorial_argumentativo":
        return "Iniciar a aula apresentando o editorial como texto de opinião, mobilizando conhecimentos prévios sobre ponto de vista, argumentação e circulação social do gênero."
    if p.perfil == "oralidade_entrevista":
        return "Iniciar a aula apresentando a entrevista como prática de oralidade, destacando turnos de fala, perguntas, respostas e adequação da linguagem ao contexto."
    if p.perfil == "texto_normativo":
        return "Iniciar a aula retomando a função social dos textos normativos e legais, relacionando direitos, deveres e regras a situações concretas do cotidiano."
    if p.perfil == "gramatica_analise_linguistica":
        return "Iniciar a aula retomando exemplos de uso da língua no material, preparando a turma para observar forma, sentido e efeito das escolhas linguísticas."

    if p.tem_noticia:
        opcoes.append("Iniciar a aula com leitura guiada da notícia apresentada no material, mobilizando conhecimentos prévios e incentivando a turma a identificar o problema central discutido.")
    if p.tem_imagem_inicial:
        opcoes.append("Iniciar a aula com observação orientada das imagens do material, estimulando os estudantes a levantar hipóteses, identificar elementos importantes e relacioná-los ao tema.")
    if p.tem_mapa:
        opcoes.append("Iniciar a aula com exploração do mapa apresentado no material, orientando a turma a observar fluxos, regiões e possíveis explicações para os deslocamentos identificados.")
    if p.tem_estudo_caso or p.tem_situacao_problema:
        opcoes.append("Iniciar com a situação-problema do material, incentivando a turma a levantar hipóteses e antecipar possíveis caminhos de análise.")
    opcoes.append("Iniciar a aula apresentando o tema central e incentivando os estudantes a relacioná-lo a situações do cotidiano.")

    return deterministic_choice(opcoes, p.titulo + "|inicio")


def frase_foco(p: PistasPedagogicas) -> str:
    frase = ""
    if p.perfil == "texto_publicitario":
        frase = "Conduzir a análise do texto publicitário, destacando público-alvo, finalidade persuasiva, slogan, imagens, recursos sonoros ou audiovisuais e efeitos de sentido da campanha."
    elif p.perfil == "diario_pessoal":
        frase = "Conduzir a leitura orientada do diÃ¡rio pessoal, destacando escrita em primeira pessoa, organizaÃ§Ã£o temporal, marcas de intimidade, reflexÃµes do cotidiano e relaÃ§Ã£o entre experiÃªncia vivida e linguagem."
    elif p.perfil == "biografia":
        frase = "Conduzir a leitura orientada da biografia, destacando trajetória, fatos relevantes, organização temporal e uso do mapa conceitual como recurso para organizar informações."
    elif p.perfil == "noticia_multimodal":
        frase = "Conduzir a leitura crítica da notícia digital, destacando relação entre texto, fotos, vídeos, legenda, intencionalidade das imagens e efeitos de sentido no contexto jornalístico."
    elif p.perfil == "leitura_multimodal":
        frase = "Conduzir a leitura orientada do texto multimodal, destacando relacao entre imagem, texto verbal, dados, legenda e finalidade comunicativa."
    elif p.perfil == "resumo_retextualizacao":
        frase = "Explicar como selecionar informacoes principais do esquema ou infografico e transforma-las em paragrafos com topico frasal, coerencia e progressao de ideias."
    elif p.perfil == "variacao_linguistica_registro":
        frase = "Sistematizar a variacao linguistica presente no material, diferenciando usos regionais, sociais, historicos e situacionais sem reforcar preconceito linguistico."
    elif p.perfil == "argumentacao_debate":
        frase = "Conduzir a analise dos argumentos do material, destacando tese, contra-argumento, evidencias e criterios para sustentar posicionamentos com respeito."
    elif p.perfil == "texto_digital_blog":
        frase = "Conduzir a leitura orientada do post de blog, destacando tese, exemplos, registro de linguagem, interlocutor e efeitos de sentido no ambiente digital."
    elif p.perfil == "analise_linguistica_ortografia":
        frase = "Sistematizar o recurso linguistico ou ortografico do material, relacionando forma, clareza, adequacao ao contexto e construcao de sentido."
    elif p.perfil == "conto_distopico":
        frase = "Conduzir a leitura literária do conto distópico, destacando narrador, personagens, enredo, conflito, suspense e efeitos produzidos pelos tempos e modos verbais."
    elif p.perfil == "literatura_prosa":
        frase = "Conduzir a leitura orientada do texto literário do material, destacando contexto histórico, características da prosa, narrador, personagens, ambiente e efeitos de sentido construídos pela linguagem."
    elif p.perfil == "literatura_modernismo":
        frase = "Conduzir a análise do movimento literário estudado, relacionando contexto histórico, propostas estéticas, autores, obras e rupturas de linguagem presentes no material."
    elif p.perfil == "poema":
        frase = "Conduzir a leitura orientada do poema, destacando eu lírico, imagens poéticas, versos, estrofes, ritmo, escolhas lexicais e efeitos de sentido."
    elif p.perfil == "cronica":
        frase = "Conduzir a leitura orientada da crônica, destacando situação cotidiana, voz narrativa, marcas de linguagem, humor ou reflexão e relação entre experiência comum e construção literária."
    elif p.perfil == "artigo_opiniao":
        frase = "Conduzir a leitura orientada do artigo de opinião, destacando tese, argumentos, posicionamento do autor, estratégias persuasivas e relação com o público leitor."
    elif p.perfil == "editorial_argumentativo":
        frase = "Conduzir a leitura orientada do editorial, destacando tese, argumentos, ponto de vista, escolhas linguísticas e relação entre projeto editorial, contexto de circulação e leitor previsto."
    elif p.perfil == "oralidade_entrevista":
        frase = "Conduzir a análise da entrevista, destacando turnos de fala, organização das perguntas e respostas, marcas de oralidade, transcrição e variação linguística."
    elif p.perfil == "texto_normativo":
        frase = "Conduzir a leitura orientada do texto normativo ou legal do material, destacando finalidade, direitos, deveres, linguagem objetiva, contexto de circulação e efeitos das escolhas linguísticas."
    elif p.perfil == "gramatica_analise_linguistica":
        frase = "Sistematizar o fenômeno de análise linguística apresentado no material, relacionando forma, função, sentido e efeito produzido nos textos estudados."
    elif p.perfil == "noticia_leitura_critica":
        frase = "Conduzir a leitura orientada da notícia e das perguntas propostas, destacando informações principais, pontos de vista, formas de preconceito ou conflito e relações com o conceito central da aula."
    elif p.perfil == "imagem_debate":
        frase = "Explorar as imagens e questões iniciais do material, promovendo debate orientado e análise crítica das situações apresentadas antes da sistematização dos conceitos."
    elif p.perfil == "imagem_debate_direitos":
        frase = "Explorar as imagens, os questionamentos iniciais e os conceitos do material, destacando diferenças entre situações analisadas, riscos envolvidos, direitos, restrições e o papel do Estado."
    elif p.perfil == "comparacao_conceitual":
        frase = "Sistematizar os conceitos centrais da aula por meio de comparação orientada, ajudando a turma a distinguir termos próximos, reconhecer critérios e justificar diferenças com clareza."
    elif p.perfil == "mapa_fluxos_migratorios":
        frase = "Conduzir a leitura orientada do mapa e dos conceitos do material, destacando fluxos migratórios, causas dos deslocamentos e relações entre globalização, trabalho e qualidade de vida."
    elif p.perfil == "grafico_fluxos_refugiados":
        frase = "Conduzir a leitura orientada de gráficos, quadros ou informações visuais do material, ajudando a turma a interpretar os fluxos de refugiados e relacioná-los às causas do deslocamento forçado."
    elif p.perfil == "conceito_reflexivo":
        frase = "Sistematizar os conceitos centrais da aula com explicações claras, exemplos próximos da realidade dos estudantes e retomada do vocabulário principal."
    else:
        if p.tem_grafico and p.tem_tabela:
            frase = "Desenvolver o conteúdo central da aula por meio da análise orientada de gráficos e tabelas explicativas presentes no material."
        elif p.tem_grafico:
            frase = "Desenvolver o conteúdo central da aula por meio da leitura e interpretação orientada de gráficos e informações visuais do material."
        elif p.tem_tabela:
            frase = "Desenvolver o conteúdo central da aula por meio da análise de tabelas ou quadros comparativos do material."
        else:
            frase = "Desenvolver o conteúdo central da aula com explicação dialogada, exemplos do material e participação orientada da turma."

    if p.tem_analise_linguistica and p.perfil != "gramatica_analise_linguistica":
        frase += " Articular essa leitura à análise linguística indicada no material, mostrando como os recursos da língua contribuem para a construção de sentido."

    perfis_textuais = {
        "texto_publicitario",
        "diario_pessoal",
        "biografia",
        "noticia_multimodal",
        "leitura_multimodal",
        "resumo_retextualizacao",
        "variacao_linguistica_registro",
        "argumentacao_debate",
        "texto_digital_blog",
        "analise_linguistica_ortografia",
        "conto_distopico",
        "literatura_prosa",
        "literatura_modernismo",
        "poema",
        "cronica",
        "artigo_opiniao",
        "editorial_argumentativo",
        "oralidade_entrevista",
        "texto_normativo",
        "gramatica_analise_linguistica",
    }
    if (p.tem_grafico or p.tem_tabela) and p.perfil not in perfis_textuais:
        f_norm = norm(frase)
        if "grafico" not in f_norm and "tabela" not in f_norm and "quadro" not in f_norm:
            if p.tem_grafico and p.tem_tabela:
                frase += " Orientar a leitura e interpretação dos gráficos e tabelas presentes no material para fundamentar a análise."
            elif p.tem_grafico:
                frase += " Orientar a leitura e interpretação dos gráficos presentes no material."
            elif p.tem_tabela:
                frase += " Orientar a análise das tabelas ou quadros explicativos do material."

    return frase


def frase_pause(p: PistasPedagogicas) -> str:
    if p.tem_pause_responda:
        return "Realizar uma pausa de verificação da aprendizagem para que os estudantes justifiquem respostas, retomem conceitos e revisem o raciocínio antes de avançar."
    return ""


def frase_pratica(p: PistasPedagogicas) -> str:
    if p.perfil == "texto_publicitario":
        return "Propor atividade de análise multimodal para que os estudantes identifiquem público-alvo, estratégias de persuasão, relação entre elementos verbais e não verbais e efeitos da campanha."
    if p.perfil == "biografia":
        return "Propor atividade de leitura e organização de informações para que os estudantes selecionem fatos relevantes da biografia e os registrem em mapa conceitual ou esquema orientado."
    if p.perfil == "noticia_multimodal":
        return "Propor atividade de análise da notícia digital para que os estudantes relacionem texto, imagem e vídeo, discutindo intencionalidade, ética e efeitos de sentido no jornalismo."
    if p.perfil == "conto_distopico":
        return "Propor atividade de análise literária para que os estudantes retomem trechos do conto, identifiquem narrador, conflito, tempos verbais e expliquem como esses recursos constroem tensão."
    if p.perfil == "literatura_prosa":
        return "Propor atividade de análise literária para que os estudantes retomem trechos do material, registrem evidências do texto e expliquem como contexto, personagens e linguagem sustentam a interpretação."
    if p.perfil == "literatura_modernismo":
        return "Propor atividade de análise literária para que os estudantes relacionem características do movimento, autores, obras e recursos expressivos, registrando evidências do material."
    if p.perfil == "poema":
        return "Propor atividade de interpretação do poema para que os estudantes identifiquem voz poética, imagens, estrutura e escolhas linguísticas, justificando respostas com trechos do texto."
    if p.perfil == "cronica":
        return "Propor atividade de análise e registro em que os estudantes identifiquem elementos da crônica, relacionem cotidiano e linguagem e justifiquem os efeitos de sentido percebidos na leitura."
    if p.perfil == "artigo_opiniao":
        return "Propor atividade de análise argumentativa para que os estudantes identifiquem tese, argumentos, posicionamento e estratégias persuasivas, registrando conclusões com base no artigo lido."
    if p.perfil == "editorial_argumentativo":
        return "Propor atividade de análise argumentativa para que os estudantes identifiquem tese, argumentos e estratégias de persuasão, registrando conclusões com base no texto lido."
    if p.perfil == "oralidade_entrevista":
        return "Propor atividade de análise da entrevista para que os estudantes reconheçam turnos de fala, marcas de oralidade, variação linguística e relação entre pergunta, resposta e contexto."
    if p.perfil == "texto_normativo":
        return "Propor atividade de interpretação do texto normativo para que os estudantes retomem trechos, identifiquem direitos ou regras e relacionem a finalidade do texto ao contexto social discutido."
    if p.perfil == "gramatica_analise_linguistica":
        return "Propor atividade de aplicação para que os estudantes reconheçam o recurso linguístico em exemplos do material, expliquem seu efeito e registrem conclusões no caderno."
    if p.perfil == "noticia_leitura_critica":
        return "Propor atividade de análise e registro em que os estudantes retomem a notícia, respondam às questões e relacionem o caso discutido aos conceitos trabalhados na aula."
    if p.perfil == "imagem_debate":
        return "Encaminhar atividade de debate e registro para que a turma organize observações, formule respostas e relacione as imagens às ideias centrais estudadas."
    if p.perfil == "imagem_debate_direitos":
        return "Organizar atividade em que os estudantes comparem situações, registrem diferenças e justifiquem respostas com base nos conceitos, direitos e restrições discutidos."
    if p.perfil == "comparacao_conceitual":
        return "Propor atividade de comparação conceitual para que os estudantes organizem critérios, registrem diferenças e expliquem os conceitos com maior precisão."
    if p.perfil == "mapa_fluxos_migratorios":
        return "Propor atividade em que os estudantes interpretem o mapa, relacionem fluxos e causas das migrações e registrem conclusões com base nas discussões realizadas."
    if p.perfil == "grafico_fluxos_refugiados":
        return "Propor atividade de interpretação de informações visuais para que a turma relacione os fluxos de refugiados às causas e aos contextos geopolíticos estudados."
    return "Propor atividade de aplicação para que os estudantes retomem o conteúdo, organizem ideias principais e consolidem a aprendizagem."


def frase_encerramento(p: PistasPedagogicas) -> str:
    destaque = ", ".join(p.vocabulario_chave[:3])
    if destaque:
        return f"Encerrar a aula com síntese dos pontos principais, retomando especialmente {destaque} e verificando o que a turma conseguiu compreender."
    return "Encerrar a aula com síntese dos pontos principais e retomada das aprendizagens construídas."


def complemento_tecnica(tecnica: str, etapa: str) -> str:
    mapa = {
        ("Virem e conversem", "inicio"): "Aplicar a técnica Virem e conversem no momento inicial para ampliar a participação e socializar hipóteses.",
        ("Todo mundo escreve", "pratica"): "Utilizar a técnica Todo mundo escreve para favorecer a organização do pensamento antes da socialização das respostas.",
        ("Com suas palavras", "encerramento"): "Retomar a síntese final com a técnica Com suas palavras, incentivando os estudantes a reelaborarem o conteúdo com autonomia.",
        ("Um passo de cada vez", "foco"): "Conduzir a explicação com a técnica Um passo de cada vez, organizando o conteúdo em etapas claras e progressivas.",
        ("De olho no modelo", "foco"): "Utilizar a técnica De olho no modelo para apresentar um exemplo orientador antes da atividade principal.",
        ("Hora da leitura", "foco"): "Promover leitura orientada do material com a técnica Hora da leitura, destacando informações essenciais e pontos de atenção.",
        ("Pausa produtiva", "pause"): "Realizar uma Pausa produtiva para revisão breve do raciocínio antes da continuidade da atividade.",
    }
    return mapa.get((tecnica, etapa), "")


def _blocos_metodologia(p: PistasPedagogicas) -> List[Dict[str, str]]:
    blocos = []
    blocos.append({"titulo": "Para comecar", "texto": frase_inicial(p)})

    if "Virem e conversem" in p.tecnicas_lemov:
        comp = complemento_tecnica("Virem e conversem", "inicio")
        if comp:
            blocos.append({"titulo": "Interacao inicial", "texto": comp})

    blocos.append({"titulo": "Foco no conteudo", "texto": frase_foco(p)})

    for tecnica in ("Um passo de cada vez", "De olho no modelo", "Hora da leitura"):
        if tecnica in p.tecnicas_lemov:
            comp = complemento_tecnica(tecnica, "foco")
            if comp:
                blocos.append({"titulo": tecnica, "texto": comp})
                break

    pause = frase_pause(p)
    if pause:
        blocos.append({"titulo": "Pause e responda", "texto": pause})
        if "Pausa produtiva" in p.tecnicas_lemov:
            comp = complemento_tecnica("Pausa produtiva", "pause")
            if comp:
                blocos.append({"titulo": "Pausa produtiva", "texto": comp})

    blocos.append({"titulo": "Na pratica", "texto": frase_pratica(p)})

    if "Todo mundo escreve" in p.tecnicas_lemov:
        comp = complemento_tecnica("Todo mundo escreve", "pratica")
        if comp:
            blocos.append({"titulo": "Registro individual", "texto": comp})

    blocos.append({"titulo": "Encerramento", "texto": frase_encerramento(p)})

    if "Com suas palavras" in p.tecnicas_lemov:
        comp = complemento_tecnica("Com suas palavras", "encerramento")
        if comp:
            blocos.append({"titulo": "Com suas palavras", "texto": comp})

    saida = []
    for bloco in blocos:
        texto = bloquear_contaminacao_tematica(sanitizar_texto_pedagogico(bloco.get("texto", "")), p)
        if texto:
            saida.append({"titulo": bloco["titulo"], "texto": texto})

    uniq = []
    seen = set()
    for bloco in saida:
        chave = norm(bloco["titulo"] + " " + bloco["texto"])
        if chave and chave not in seen:
            seen.add(chave)
            uniq.append(bloco)

    if len(uniq) > 6:
        for idx in range(5, len(uniq)):
            if uniq[idx]["titulo"] in {"Encerramento", "Com suas palavras"}:
                return uniq[:5] + [uniq[idx]]
    return uniq[:6]


def gerar_metodologia(pistas: PistasPedagogicas) -> str:
    blocos = _blocos_metodologia(pistas)
    return "\n".join(f"{i+1}. {bloco['texto']}" for i, bloco in enumerate(blocos))


BANCO_ACOMPANHAMENTO = {
    "texto_publicitario": [
        "Verificar se os estudantes identificam público-alvo, finalidade persuasiva e recursos verbais, visuais ou audiovisuais da campanha.",
        "Observar se relacionam slogan, imagem, som e contexto aos efeitos de sentido produzidos no anúncio.",
        "Conferir se os registros finais diferenciam publicidade, propaganda e notícia, evitando confusões entre gêneros.",
        "Acompanhar se a turma justifica interpretações com elementos presentes no material publicitário."
    ],
    "diario_pessoal": [
        "Verificar se os estudantes identificam marcas de primeira pessoa, temporalidade, subjetividade e reflexÃ£o presentes no diÃ¡rio pessoal.",
        "Observar se relacionam experiÃªncias narradas, sentimentos e contexto de escrita ao sentido construÃ­do no texto.",
        "Conferir se os registros finais retomam caracterÃ­sticas do gÃªnero sem confundi-lo com biografia, memÃ³ria ou notÃ­cia.",
        "Acompanhar se a turma justifica interpretaÃ§Ãµes com trechos do diÃ¡rio e com elementos da linguagem analisada."
    ],
    "diario_pessoal": [
        "Realizar leitura compartilhada do diÃ¡rio em trechos curtos, com pausas para destacar quem escreve, para quem escreve e quais reflexÃµes aparecem no texto.",
        "Disponibilizar roteiro com perguntas objetivas sobre primeira pessoa, temporalidade, sentimentos e acontecimentos narrados.",
        "Permitir registro em tÃ³picos, grifos no texto, esquema simples ou resposta oral mediada.",
        "Retomar coletivamente a diferenÃ§a entre diÃ¡rio pessoal, biografia e relato informativo antes da atividade individual."
    ],
    "biografia": [
        "Verificar se os estudantes identificam fatos relevantes da trajetória da pessoa biografada e organizam informações com coerência.",
        "Observar se compreendem a função do mapa conceitual como organizador de ideias, sem tratá-lo como mapa geográfico.",
        "Conferir se os registros finais relacionam vida, obra, carreira e contexto da pessoa estudada.",
        "Acompanhar se a turma diferencia biografia de notícia ou reportagem."
    ],
    "noticia_multimodal": [
        "Verificar se os estudantes relacionam texto, foto, vídeo, legenda e intencionalidade das imagens na notícia digital.",
        "Observar se reconhecem efeitos de sentido produzidos pelos recursos multimodais no contexto jornalístico.",
        "Conferir se os registros finais analisam a notícia sem transformar a aula em leitura de gráfico, tabela ou reportagem.",
        "Acompanhar se a turma diferencia informação, imagem jornalística e entretenimento."
    ],
    "conto_distopico": [
        "Verificar se os estudantes identificam narrador, personagens, conflito, suspense e marcas da narrativa distópica.",
        "Observar se relacionam tempos e modos verbais aos efeitos de tensão, ponto de vista e construção do enredo.",
        "Conferir se os registros finais usam trechos do conto para sustentar interpretações.",
        "Acompanhar se a turma diferencia conto literário de notícia, artigo de opinião ou debate jornalístico."
    ],
    "literatura_prosa": [
        "Verificar se os estudantes relacionam trechos da obra ao contexto, aos personagens e aos efeitos de sentido construídos pela linguagem.",
        "Observar se utilizam evidências do texto literário para sustentar interpretações orais e escritas.",
        "Conferir se os registros apresentam compreensão de narrador, ambiente, conflito e características da prosa estudada.",
        "Acompanhar se a turma diferencia informação contextual e interpretação literária."
    ],
    "literatura_modernismo": [
        "Verificar se os estudantes reconhecem características do movimento literário, autores, obras e rupturas estéticas estudadas.",
        "Observar se relacionam contexto histórico e escolhas de linguagem presentes nos textos do material.",
        "Conferir se os registros finais usam evidências dos poemas, manifestos ou textos literários analisados.",
        "Acompanhar se a turma compreende as inovações modernistas sem confundi-las com gêneros jornalísticos."
    ],
    "poema": [
        "Verificar se os estudantes identificam voz poética, imagens, versos, estrofes e efeitos de sentido do poema.",
        "Observar se justificam interpretações com trechos e escolhas linguísticas do texto poético.",
        "Conferir se os registros apresentam compreensão da organização formal e temática do poema.",
        "Acompanhar se a turma diferencia leitura literal e interpretação poética."
    ],
    "cronica": [
        "Verificar se os estudantes identificam situação cotidiana, voz narrativa, marcas de linguagem e efeitos de humor, ironia ou reflexão.",
        "Observar se relacionam elementos da crônica à experiência comum e ao ponto de vista construído no texto.",
        "Conferir se os registros finais retomam evidências da crônica e explicam efeitos de sentido.",
        "Acompanhar se a turma reconhece especificidades do gênero sem tratá-lo como notícia ou reportagem."
    ],
    "artigo_opiniao": [
        "Verificar se os estudantes identificam tese, argumentos, posicionamento do autor e estratégias persuasivas do artigo.",
        "Observar se justificam respostas com evidências do texto e diferenciam opinião, argumento e exemplo.",
        "Conferir se os registros finais apresentam análise argumentativa coerente e retomada do tema discutido.",
        "Acompanhar se a turma reconhece a finalidade opinativa do gênero sem tratá-lo como notícia."
    ],
    "editorial_argumentativo": [
        "Verificar se os estudantes identificam tese, argumentos e posicionamento institucional presente no editorial.",
        "Observar se relacionam escolhas linguísticas, projeto editorial e público leitor às ideias defendidas no texto.",
        "Conferir se os registros finais sustentam conclusões com evidências do editorial analisado.",
        "Acompanhar se a turma diferencia editorial, notícia e artigo de opinião."
    ],
    "oralidade_entrevista": [
        "Verificar se os estudantes reconhecem turnos de fala, perguntas, respostas e marcas de oralidade presentes na entrevista.",
        "Observar se relacionam variação linguística, contexto de fala e adequação da linguagem à situação comunicativa.",
        "Conferir se os registros finais apresentam compreensão da organização da entrevista e de sua transcrição.",
        "Acompanhar se a turma diferencia análise da oralidade de leitura de notícia ou reportagem."
    ],
    "texto_normativo": [
        "Verificar se os estudantes compreendem finalidade, estrutura e linguagem objetiva do texto normativo ou legal.",
        "Observar se localizam direitos, deveres, regras ou artigos relevantes e explicam sua função social.",
        "Conferir se os registros finais relacionam trechos do texto legal ao contexto discutido na aula.",
        "Acompanhar se a turma diferencia texto normativo de notícia, artigo de opinião ou debate formal."
    ],
    "gramatica_analise_linguistica": [
        "Verificar se os estudantes reconhecem o recurso linguístico estudado e explicam seu funcionamento no texto.",
        "Observar se aplicam a análise de forma contextualizada, relacionando forma, sentido e efeito.",
        "Conferir se os registros finais apresentam exemplos corretos e justificativas claras.",
        "Acompanhar se a turma usa a nomenclatura gramatical como apoio para interpretar o texto, sem reduzir a aula à memorização."
    ],
    "noticia_leitura_critica": [
        "Verificar se os estudantes identificam informações principais, problema central e posicionamentos presentes na notícia analisada.",
        "Observar se relacionam o caso discutido aos conceitos trabalhados na aula, utilizando argumentos coerentes nas respostas orais e escritas.",
        "Conferir se os registros finais apresentam interpretação crítica, clareza na exposição das ideias e retomada do vocabulário principal.",
        "Acompanhar se a turma diferencia fatos do caso apresentado e interpretações construídas durante o debate."
    ],
    "imagem_debate": [
        "Verificar se os estudantes observam elementos relevantes das imagens e conseguem relacioná-los ao tema discutido na aula.",
        "Observar a participação nas discussões iniciais e a capacidade de formular hipóteses, perguntas e respostas com progressiva autonomia.",
        "Conferir se os registros finais retomam as ideias centrais construídas a partir da observação e do debate orientado.",
        "Acompanhar se a turma articula imagem, contexto e conceito de forma coerente."
    ],
    "imagem_debate_direitos": [
        "Verificar se os estudantes identificam diferenças entre as situações analisadas e compreendem os riscos, direitos e restrições envolvidos.",
        "Observar se justificam respostas com base nas imagens, nos conceitos trabalhados e nas discussões sobre o papel do Estado.",
        "Conferir se os registros finais apresentam comparação coerente, uso do vocabulário central e argumentação progressivamente mais precisa.",
        "Acompanhar se a turma reconhece relações entre migração, direitos humanos e políticas migratórias."
    ],
    "comparacao_conceitual": [
        "Verificar se os estudantes distinguem corretamente os conceitos trabalhados, evitando tratá-los como sinônimos.",
        "Observar se utilizam critérios de comparação para justificar respostas e explicar diferenças com maior precisão.",
        "Conferir se os registros finais evidenciam compreensão conceitual, organização das ideias e uso do vocabulário principal.",
        "Acompanhar se a turma relaciona os conceitos comparados aos exemplos e situações apresentados no material."
    ],
    "mapa_fluxos_migratorios": [
        "Verificar se os estudantes interpretam o mapa apresentado e identificam fluxos, entradas, saídas e possíveis explicações para os deslocamentos observados.",
        "Observar se relacionam as informações do material às causas das migrações e às discussões sobre globalização, trabalho e qualidade de vida.",
        "Conferir se os registros finais apresentam leitura coerente do mapa, justificativas plausíveis e retomada dos conceitos principais.",
        "Acompanhar se a turma utiliza a legenda e os elementos do mapa para sustentar suas respostas."
    ],
    "grafico_fluxos_refugiados": [
        "Verificar se os estudantes interpretam corretamente gráficos, quadros ou informações visuais sobre fluxos de refugiados.",
        "Observar se relacionam os dados analisados às causas do deslocamento forçado e aos contextos geopolíticos discutidos.",
        "Conferir se os registros finais articulam leitura visual, explicação conceitual e conclusão coerente.",
        "Acompanhar se a turma utiliza evidências do material para sustentar respostas e comparações."
    ],
    "conceito_reflexivo": [
        "Verificar se os estudantes compreendem os conceitos centrais da aula e conseguem explicá-los com suas próprias palavras.",
        "Observar a participação nas discussões e a retomada do vocabulário principal durante as intervenções orais e escritas.",
        "Conferir se os registros finais apresentam ideias organizadas, exemplos coerentes e compreensão progressiva do tema.",
        "Acompanhar se a turma diferencia corretamente os conceitos trabalhados, evitando confusões entre noções próximas."
    ],
    "geral": [
        "Verificar se os estudantes compreendem o tema central da aula e reconhecem as ideias principais trabalhadas.",
        "Observar a participação, os registros e a forma como justificam respostas ao longo das atividades propostas.",
        "Conferir se as produções finais apresentam clareza, coerência e retomada dos conceitos estudados.",
        "Acompanhar se os estudantes utilizam o vocabulário da aula de forma progressivamente mais autônoma."
    ],
}


BANCO_ACOMPANHAMENTO.update(
    {
        "diario_pessoal": [
            "Verificar se os estudantes identificam marcas de primeira pessoa, temporalidade, subjetividade e reflexao presentes no diario pessoal.",
            "Observar se relacionam experiencias narradas, sentimentos e contexto de escrita ao sentido construido no texto.",
            "Conferir se os registros finais retomam caracteristicas do genero sem confundi-lo com biografia, memoria ou noticia.",
            "Acompanhar se a turma justifica interpretacoes com trechos do diario e com elementos da linguagem analisada.",
        ],
        "leitura_multimodal": [
            "Verificar se os estudantes relacionam imagem, texto verbal, legenda, dados e organizacao visual na leitura do material multimodal.",
            "Observar se reconhecem a finalidade comunicativa e justificam interpretacoes com elementos concretos do cartaz, infografico, tirinha ou campanha.",
            "Conferir se os registros finais tratam a imagem como parte do texto, sem reduzi-la a ilustracao decorativa.",
            "Acompanhar se a turma explica como os recursos verbais e nao verbais constroem sentido em conjunto.",
        ],
        "resumo_retextualizacao": [
            "Verificar se os estudantes selecionam informacoes principais do esquema, lista ou infografico antes de escrever.",
            "Observar se transformam topicos em paragrafos coerentes, com articulacao entre ideias e sem copia mecanica.",
            "Conferir se os registros finais apresentam topico frasal, desenvolvimento e vocabulario adequado ao objetivo do resumo.",
            "Acompanhar se a turma revisa o proprio texto considerando clareza, coesao e fidelidade ao material-base.",
        ],
        "variacao_linguistica_registro": [
            "Verificar se os estudantes identificam exemplos de variacao linguistica e distinguem usos regionais, sociais, historicos e situacionais.",
            "Observar se explicam a adequacao do registro ao contexto sem tratar a variacao como erro.",
            "Conferir se os registros finais retomam evidencias do texto e evitam preconceito linguistico.",
            "Acompanhar se a turma usa vocabulario da aula para justificar classificacoes e comparacoes.",
        ],
        "argumentacao_debate": [
            "Verificar se os estudantes identificam tese, argumentos, contra-argumentos e evidencias no material-base.",
            "Observar se selecionam informacoes relevantes para sustentar posicionamentos sem depender apenas de opiniao espontanea.",
            "Conferir se os registros finais mostram planejamento do debate com argumentos favoraveis e contrarios.",
            "Acompanhar se a turma justifica escolhas com dados, exemplos ou trechos do texto lido.",
        ],
        "texto_digital_blog": [
            "Verificar se os estudantes reconhecem tese, argumentos, exemplos, registro de linguagem e publico leitor do post de blog.",
            "Observar se relacionam comentario, interlocutor e circulacao digital aos efeitos de sentido do texto.",
            "Conferir se os registros finais retomam o texto-base para sustentar respostas e comentarios.",
            "Acompanhar se a turma escreve com clareza e respeito ao interlocutor, sem perder o foco argumentativo.",
        ],
        "analise_linguistica_ortografia": [
            "Verificar se os estudantes reconhecem o recurso linguistico ou ortografico estudado em palavras, frases e trechos do material.",
            "Observar se explicam como a escolha analisada contribui para clareza, adequacao e sentido do texto.",
            "Conferir se os registros finais apresentam aplicacao contextualizada, e nao apenas repeticao de regra isolada.",
            "Acompanhar se a turma revisa a escrita com base em exemplos do proprio material.",
        ],
    }
)


def gerar_acompanhamento(pistas: PistasPedagogicas) -> List[str]:
    base = BANCO_ACOMPANHAMENTO.get(pistas.perfil, BANCO_ACOMPANHAMENTO["geral"])[:]
    rng = random.Random(pistas.titulo + "|acompanhamento|" + pistas.perfil)
    rng.shuffle(base)
    return [sentenca(item) for item in dedup(base)[:3]]


BANCO_ACESSIBILIDADE = {
    "texto_publicitario": [
        "Apresentar os elementos do anúncio em etapas, destacando público-alvo, slogan, imagem, som e finalidade persuasiva.",
        "Disponibilizar roteiro de análise multimodal com perguntas curtas sobre linguagem verbal, não verbal e efeito produzido.",
        "Permitir registro em tópicos, marcações no anúncio ou resposta oral mediada.",
        "Retomar coletivamente a diferença entre anúncio, notícia e artigo de opinião antes da atividade."
    ],
    "biografia": [
        "Realizar leitura compartilhada da biografia, destacando linha do tempo, fatos relevantes e palavras-chave da trajetória.",
        "Organizar o mapa conceitual passo a passo, mostrando que ele funciona como esquema de ideias, não como mapa geográfico.",
        "Permitir registro em tópicos, setas, esquema orientado ou resposta oral mediada.",
        "Oferecer banco de palavras com vida, obra, carreira, nascimento, contexto e contribuições."
    ],
    "noticia_multimodal": [
        "Orientar a observação de texto, foto, vídeo e legenda separadamente antes de relacionar os recursos.",
        "Disponibilizar perguntas-guia sobre intencionalidade da imagem, informação principal e efeito de sentido.",
        "Permitir registro em tópicos, marcações no material ou resposta oral mediada.",
        "Retomar coletivamente a diferença entre recurso visual jornalístico, imagem decorativa e gráfico de dados."
    ],
    "conto_distopico": [
        "Realizar leitura em trechos do conto, pausando para localizar narrador, personagens, conflito e clima de suspense.",
        "Destacar exemplos de tempos e modos verbais no próprio texto antes da atividade individual.",
        "Permitir registro em tópicos, marcações no conto ou explicação oral mediada.",
        "Oferecer roteiro com perguntas sobre enredo, ponto de vista, tensão narrativa e efeito dos verbos."
    ],
    "literatura_prosa": [
        "Oferecer leitura compartilhada de trechos selecionados, com pausas para explicar vocabulário, personagens, ambiente e contexto.",
        "Disponibilizar roteiro com perguntas sobre narrador, personagens, espaço, conflito e evidências do texto.",
        "Permitir registro em tópicos, marcações de trechos ou resposta oral mediada conforme as necessidades da turma.",
        "Retomar coletivamente passagens centrais antes da atividade individual."
    ],
    "literatura_modernismo": [
        "Disponibilizar linha do tempo, palavras-chave ou quadro de autores e características para apoiar a contextualização do movimento.",
        "Realizar leitura guiada dos textos modernistas, explicando vocabulário, rupturas de linguagem e referências históricas.",
        "Permitir registro por tópicos, esquema ou associação entre obra, autor e característica estética.",
        "Usar exemplos curtos do material para diferenciar movimento literário, obra e contexto."
    ],
    "poema": [
        "Realizar leitura em voz alta do poema, retomando versos e imagens poéticas com pausas para compreensão.",
        "Destacar visualmente eu lírico, palavras-chave, versos e estrofes antes da interpretação individual.",
        "Permitir registro em tópicos, marcações no texto ou resposta oral mediada.",
        "Oferecer perguntas orientadoras para apoiar a passagem da leitura literal para a interpretação poética."
    ],
    "cronica": [
        "Realizar leitura compartilhada da crônica, destacando situação cotidiana, voz narrativa e marcas de linguagem.",
        "Oferecer perguntas curtas para apoiar identificação de humor, ironia, reflexão ou ponto de vista.",
        "Permitir registro em tópicos, frases curtas ou resposta oral mediada.",
        "Retomar coletivamente trechos importantes antes da análise individual."
    ],
    "artigo_opiniao": [
        "Disponibilizar roteiro de leitura com campos para tese, argumentos, exemplos e posicionamento do autor.",
        "Destacar conectivos, expressões opinativas e palavras-chave que apoiem a compreensão da argumentação.",
        "Permitir registro em tópicos ou esquema tese-argumento-conclusão antes da resposta escrita.",
        "Retomar oralmente a diferença entre tema, opinião e argumento com exemplos simples."
    ],
    "editorial_argumentativo": [
        "Disponibilizar roteiro de análise com foco em tese, argumentos, posicionamento do veículo e público leitor.",
        "Destacar palavras-chave e marcas de modalização que ajudem a identificar o ponto de vista institucional.",
        "Permitir registro por tópicos, esquema argumentativo ou resposta oral mediada.",
        "Retomar coletivamente a diferença entre editorial, notícia e artigo de opinião antes da atividade."
    ],
    "oralidade_entrevista": [
        "Organizar a escuta ou leitura da entrevista em partes, destacando pergunta, resposta e turnos de fala.",
        "Disponibilizar roteiro com marcas de oralidade, variação linguística e adequação ao contexto.",
        "Permitir registro em tópicos, tabela de turnos de fala quando o material solicitar, ou resposta oral mediada.",
        "Retomar exemplos de fala e transcrição antes da análise individual."
    ],
    "texto_normativo": [
        "Oferecer leitura compartilhada do texto legal, explicando termos jurídicos, artigos, incisos e finalidade social.",
        "Disponibilizar glossário ou palavras-chave para apoiar a compreensão de direitos, deveres e regras.",
        "Permitir registro em tópicos, paráfrase de trechos ou resposta oral mediada.",
        "Retomar coletivamente a estrutura do texto normativo antes da atividade individual."
    ],
    "gramatica_analise_linguistica": [
        "Apresentar exemplos do próprio material com destaque visual para o recurso linguístico estudado.",
        "Organizar explicação passo a passo, relacionando nomenclatura, função e efeito de sentido.",
        "Permitir consulta a exemplos-modelo durante a atividade individual ou em duplas.",
        "Flexibilizar o registro, aceitando marcações no texto, tópicos ou explicação oral mediada."
    ],
    "noticia_leitura_critica": [
        "Oferecer leitura guiada da notícia com destaque para título, informações principais, personagens envolvidos e problema central discutido.",
        "Disponibilizar palavras-chave e perguntas orientadoras para apoiar a interpretação do texto e a organização das respostas.",
        "Permitir registro em tópicos, frases curtas ou resposta oral mediada, conforme as necessidades observadas na turma.",
        "Retomar coletivamente o sentido de trechos importantes antes do trabalho individual."
    ],
    "imagem_debate": [
        "Organizar observação orientada das imagens com perguntas curtas que ajudem a turma a identificar elementos relevantes antes da discussão.",
        "Utilizar apoio visual e retomadas coletivas para favorecer a relação entre imagem, contexto e conceito central da aula.",
        "Permitir diferentes formas de registro, como tópicos, frases curtas, esquema ou resposta oral mediada.",
        "Oferecer mediação individual na organização das ideias e na formulação das respostas."
    ],
    "imagem_debate_direitos": [
        "Apresentar comandos curtos e objetivos, com retomada coletiva das perguntas antes do registro individual.",
        "Organizar quadro comparativo simples para apoiar a distinção entre situações, riscos, direitos e restrições discutidos no material.",
        "Permitir registro em tópicos, frases curtas, esquema comparativo ou resposta oral mediada, conforme as necessidades observadas.",
        "Destacar visualmente conceitos centrais ligados a migração, documentação, direitos e papel do Estado."
    ],
    "comparacao_conceitual": [
        "Organizar quadro comparativo ou esquema visual para apoiar a distinção entre os conceitos trabalhados na aula.",
        "Retomar oralmente os critérios de comparação com exemplos simples antes da atividade autônoma.",
        "Permitir registro em tópicos, tabela simples, frases curtas ou resposta oral mediada, conforme as necessidades observadas.",
        "Destacar visualmente semelhanças e diferenças para apoiar a compreensão conceitual."
    ],
    "mapa_fluxos_migratorios": [
        "Disponibilizar leitura guiada do mapa com destaque para legenda, fluxos, regiões de entrada e saída e elementos visuais relevantes.",
        "Oferecer perguntas orientadoras para ajudar os estudantes a relacionar o mapa às causas das migrações e aos contextos discutidos na aula.",
        "Permitir diferentes formas de registro, como tópicos, setas, esquema simples ou resposta oral mediada.",
        "Retomar coletivamente como localizar informações essenciais no mapa antes do trabalho individual."
    ],
    "grafico_fluxos_refugiados": [
        "Disponibilizar leitura guiada de gráficos, quadros ou informações visuais, destacando título, categorias e comparação entre os dados apresentados.",
        "Oferecer apoio visual com palavras-chave e perguntas orientadoras para ajudar na interpretação das informações do material.",
        "Permitir diferentes formas de registro, como tópicos, respostas curtas, marcações no gráfico ou explicação oral mediada.",
        "Retomar coletivamente como localizar dados relevantes antes do trabalho individual."
    ],
    "conceito_reflexivo": [
        "Disponibilizar glossário com palavras-chave e exemplos simples para apoiar a compreensão do vocabulário da aula.",
        "Retomar oralmente os conceitos principais com apoio de esquema, quadro ou síntese visual construída com a turma.",
        "Permitir diferentes formas de expressão do entendimento, como tópicos, frases curtas, desenho explicativo ou resposta oral mediada.",
        "Utilizar exemplos concretos do cotidiano para apoiar a compreensão de termos mais abstratos."
    ],
    "geral": [
        "Disponibilizar roteiro com palavras-chave e perguntas orientadoras para apoiar a compreensão da atividade.",
        "Realizar retomadas coletivas dos comandos e oferecer mediação individual conforme as necessidades observadas.",
        "Permitir diferentes formas de registro, como tópicos, frases curtas, esquema, desenho ou resposta oral mediada.",
        "Organizar momentos de apoio em duplas para favorecer compreensão e participação."
    ],
}


BANCO_ACESSIBILIDADE.update(
    {
        "diario_pessoal": [
            "Realizar leitura compartilhada do diario em trechos curtos, com pausas para destacar quem escreve, para quem escreve e quais reflexoes aparecem no texto.",
            "Disponibilizar roteiro com perguntas objetivas sobre primeira pessoa, temporalidade, sentimentos e acontecimentos narrados.",
            "Permitir registro em topicos, grifos no texto, esquema simples ou resposta oral mediada.",
            "Retomar coletivamente a diferenca entre diario pessoal, biografia e relato informativo antes da atividade individual.",
        ],
        "leitura_multimodal": [
            "Orientar a observacao de imagem, legenda, texto verbal e dados em etapas, antes de solicitar interpretacao global do material multimodal.",
            "Disponibilizar perguntas-guia sobre finalidade comunicativa, informacoes principais e relacao entre elementos verbais e nao verbais.",
            "Permitir registro em topicos, marcacoes no material ou resposta oral mediada.",
            "Retomar coletivamente que a imagem faz parte do texto e precisa ser lida como fonte de sentido.",
        ],
        "resumo_retextualizacao": [
            "Destacar visualmente topicos, palavras-chave e informacoes principais antes da escrita em paragrafos.",
            "Oferecer modelo curto de topico frasal e roteiro de transformacao de lista em texto corrido.",
            "Permitir planejamento em topicos, setas ou frases-base antes da versao final.",
            "Organizar revisao com colega ou com o professor para verificar clareza e fidelidade ao material-base.",
        ],
        "variacao_linguistica_registro": [
            "Disponibilizar exemplos comparativos de registros e variacoes para apoiar a classificacao sem reforcar preconceito linguistico.",
            "Explicar com linguagem simples a diferenca entre adequado ao contexto e erro gramatical.",
            "Permitir resposta oral mediada, registro em topicos ou quadro comparativo antes da resposta final.",
            "Retomar coletivamente exemplos da propria turma, da familia ou da comunidade para concretizar o conceito.",
        ],
        "argumentacao_debate": [
            "Disponibilizar quadro com tese, argumento, contra-argumento e evidencias para apoiar o planejamento do debate.",
            "Oferecer modelo de resposta argumentativa curta antes da atividade autoral.",
            "Permitir planejamento em dupla e registro por topicos antes da fala ou do texto final.",
            "Retomar com a turma que o debate precisa de texto-base, dados e escuta respeitosa para acontecer com seguranca.",
        ],
        "texto_digital_blog": [
            "Organizar a leitura do post em partes, destacando tese, exemplos, comentario e relacao com o publico leitor.",
            "Disponibilizar roteiro com campos para tom do texto, argumento principal e comentario do estudante.",
            "Permitir registro em frases curtas, topicos ou resposta oral mediada antes da escrita final.",
            "Retomar coletivamente criterios de respeito ao interlocutor e adequacao ao genero digital.",
        ],
        "analise_linguistica_ortografia": [
            "Apresentar exemplos retirados do proprio material com destaque visual para a palavra, estrutura ou escolha linguistica estudada.",
            "Organizar explicacao passo a passo, ligando regra, efeito de sentido e contexto de uso.",
            "Permitir consulta a exemplos-modelo durante a atividade individual ou em dupla.",
            "Flexibilizar o registro com marcacoes no texto, topicos ou explicacao oral mediada quando necessario.",
        ],
    }
)


def gerar_acessibilidade(pistas: PistasPedagogicas) -> List[str]:
    base = BANCO_ACESSIBILIDADE.get(pistas.perfil, BANCO_ACESSIBILIDADE["geral"])[:]
    rng = random.Random(pistas.titulo + "|acessibilidade|" + pistas.perfil)
    rng.shuffle(base)
    return [sentenca(item) for item in dedup(base)[:3]]


def montar_colunas_pedagogicas(texto_pdf: str, titulo_aula: str, perfil: str = None) -> Dict[str, object]:
    pistas = extrair_pistas(texto_pdf, titulo_aula, perfil=perfil)
    return {
        "pistas": pistas,
        "desenvolvimento": gerar_metodologia(pistas),
        "metodologia_blocos": _blocos_metodologia(pistas),
        "acompanhamento_aprendizagem": gerar_acompanhamento(pistas),
        "acessibilidade": gerar_acessibilidade(pistas),
    }
