import re
import unicodedata
from pathlib import Path


def _normalizar(texto: str = "") -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.lower()
    return re.sub(r"\s+", " ", texto).strip()


_CATALOGO_OBJETIVOS = {
    ("missao", 1): [
        "Compreender as características de uma regra de jogo.",
        "Relacionar linguagem verbal e não verbal para compreender regras de jogo.",
    ],
    ("missao", 2): [
        "Compreender as características das histórias em quadrinhos.",
        "Analisar as expectativas criadas no leitor e os elementos que levam à quebra da expectativa.",
        "Concluir como o humor é construído nas histórias em quadrinhos.",
    ],
    ("missao", 3): [
        "Compreender as características dos gêneros textuais notícia e charge.",
        "Reconhecer a semelhança temática entre dois gêneros textuais distintos.",
        "Identificar a diferença na abordagem do mesmo tema em charges e notícias.",
    ],
    ("missao", 4): [
        "Identificar a ideia central do texto.",
        "Reconhecer como é construído o humor nas tirinhas.",
    ],
    ("missao", 5): [
        "Compreender as características de reportagens e identificar sua função sociocomunicativa.",
        "Estabelecer relações de causa e consequência entre os fatos relatados.",
        "Construir sentidos com base nas relações de causa e consequência identificadas.",
    ],
    ("missao", 6): [
        "Compreender as características do gênero textual reportagem.",
        "Reconhecer conjunções e advérbios como recursos de coesão textual.",
        "Analisar a relação de sentido de conjunções e advérbios nos textos.",
    ],
    ("missao", 7): [
        "Compreender as características de um texto de divulgação científica.",
        "Localizar palavras que retomam informações.",
        "Conhecer a importância de elementos coesivos para a continuidade textual.",
    ],
    ("missao", 8): [
        "Compreender as características de um verbete de enciclopédia.",
        "Analisar as características de um verbete de enciclopédia.",
        "Reconhecer a função de verbetes de enciclopédia.",
    ],
    ("missao", 9): [
        "Identificar o tema (ideia central) e localizar informações explícitas no conto.",
        "Reconhecer elementos do enredo (conflito, clímax, desfecho) e o ponto de vista (narrador).",
        "Reconhecer efeitos de pontuação na construção de sentido e de humor.",
        "Identificar pronomes e seus referentes (coesão referencial).",
        "Distinguir prosa (parágrafos) e poema (versos/estrofes), antecipando traços de cordel e poema narrativo.",
    ],
    ("missao", 10): [
        "Compreender as características de um poema.",
        "Analisar as marcas linguísticas de poemas para inferir quem é o eu lírico e com quem ele dialoga.",
    ],
    ("missao", 11): [
        "Compreender as características de um texto de cordel.",
        "Reconhecer as marcas linguísticas que permitem inferir informações.",
        "Inferir as características de personagens por meio da análise de suas ações.",
    ],
    ("missao", 12): [
        "Compreender as características de um poema e sua função sociocomunicativa.",
        "Reconhecer os efeitos de sentido decorrentes do emprego de pontuação e outras notações.",
    ],
    ("missao", 13): [
        "Identificar o tema (ideia central) e localizar informações explícitas em textos narrativos curtos.",
        "Reconhecer elementos do enredo (conflito, clímax, desfecho) e o ponto de vista (narrador).",
        "Inferir informações implícitas e o sentido de expressões com base no contexto.",
        "Reconhecer relação entre pronomes e seus referentes em narrativas, bem como a variação linguística que revela características dos locutores e dos interlocutores.",
    ],
    ("missao", 14): [
        "Compreender as características de fábulas e identificar sua função sociocomunicativa.",
        "Analisar a construção do enredo nas fábulas.",
    ],
    ("missao", 15): [
        "Compreender as características de um texto teatral.",
        "Localizar pontuações empregadas de forma expressiva no texto.",
        "Inferir o efeito de sentido do emprego de pontuações e outras notações em textos teatrais.",
    ],
    ("jornada", 13): [
        "Entender como os recursos gráficos contribuem para a composição, a estrutura e a linguagem de diferentes gêneros textuais, promovendo leitura crítica e reflexiva.",
        "Analisar a importância dos elementos gráficos na comunicação midiática e pública, destacando seu papel na transmissão de informações e na mobilização social.",
    ],
    ("jornada", 14): [
        "Compreender que a língua está viva e apresenta variedades linguísticas em diferentes tempos, lugares e grupos sociais.",
        "Analisar marcas de variação linguística e usos de registro formal e informal em diferentes gêneros e situações comunicativas.",
        "Refletir criticamente sobre preconceito linguístico, plurilinguismo e diversidade de formas de dizer.",
    ],
}


def _familia_numero(texto: str = "") -> tuple[str, int]:
    base = _normalizar(texto)
    for familia in ("missao", "trilha", "jornada"):
        match = re.search(rf"{familia}[_\s-]*(\d{{1,2}})", base)
        if match:
            return familia, int(match.group(1))
    return "", 0


def buscar_objetivos_orientacao_estudos(caminho_pdf: str = "", tema: str = "") -> list[str]:
    candidatos = [tema, Path(str(caminho_pdf or "")).stem, str(caminho_pdf or "")]
    for candidato in candidatos:
        familia, numero = _familia_numero(candidato)
        if familia and numero:
            objetivos = _CATALOGO_OBJETIVOS.get((familia, numero))
            if objetivos:
                return list(objetivos)
    return []


def formatar_objetivos_orientacao_estudos(objetivos: list[str] | tuple[str, ...] | None) -> str:
    itens = [re.sub(r"\s+", " ", str(item or "")).strip(" .;:-") for item in list(objetivos or []) if str(item or "").strip()]
    if not itens:
        return ""
    return " • ".join(f"{item}." if item[-1] not in ".!?" else item for item in itens)
