"""
Extrator de conteudo estruturado de PDFs.

Centraliza a logica de extracao de habilidades BNCC, conceitos,
atividades praticas e contexto de aula a partir do texto extraido.
"""

import re
import unicodedata

from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural


def _normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _limpar_trecho(texto: str) -> str:
    texto = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip(" -:;*"))
    texto = re.sub(r"\.{2,}", ".", texto)
    return texto.strip()


_TRECHOS_DESCARTAVEIS = (
    "freepik",
    "seduc-sp",
    "produzido pela",
    "veja no livro",
    "de olho no pnld",
    "link para",
    "disponivel em",
    "slide",
)

_FINS_FRAGMENTADOS = {
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
}


def _trecho_descartavel(texto: str) -> bool:
    texto = _limpar_trecho(texto)
    if not texto:
        return True
    normalizado = _normalizar_texto(texto)
    if any(marcador in normalizado for marcador in _TRECHOS_DESCARTAVEIS):
        return True
    if re.search(r"(?:https?://|www\.|[_?&](?:gl|ga|gcl)_?=|[?&][A-Za-z0-9_]+=|\*[A-Za-z0-9_]+)", texto, flags=re.I):
        return True
    if re.fullmatch(r"[A-Za-z0-9_*?&=.%/-]{18,}", texto) and not re.search(r"\s", texto):
        return True
    if not re.search(r"\s", texto) and re.search(r"\b[A-Za-z0-9]{10,}\b", texto) and not re.search(
        r"\b(?:EM|EF)\d{2}[A-Z]{2,4}\d{0,3}[A-Z]?\b",
        texto,
        flags=re.I,
    ):
        return True
    if any(seta in texto for seta in ["⬅", "←", "→"]):
        return True
    if texto.count("?") >= 2:
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    if palavras and _normalizar_texto(palavras[-1]) in _FINS_FRAGMENTADOS:
        return True
    primeira = texto[:1]
    inicio = _normalizar_texto(texto)
    if primeira.islower() and not inicio.startswith(
        ("a ", "o ", "as ", "os ", "um ", "uma ", "essa ", "esse ", "esta ", "este ")
    ):
        return True
    return False


def _trecho_seguro(texto: str, fallback: str, limite: int = 220) -> str:
    texto = _limpar_trecho(texto)
    if _trecho_descartavel(texto):
        return fallback
    if len(texto) <= limite:
        return texto
    recorte = limitar_texto_natural(texto, limite)
    return recorte if not _trecho_descartavel(recorte) else fallback


_PADRAO_CODIGO_BNCC = re.compile(
    r"\(?\b((?:EM|EF)\d{2}[A-Z]{2,4}\d{0,3}[A-Z]?)\b\)?",
    re.IGNORECASE,
)
_PADRAO_HABILIDADE = re.compile(
    r"(\(?\b(?:EM|EF)\d{2}[A-Z]{2,4}\d{0,3}[A-Z]?\b\)?|\bAE\s*\d+\b\s*[-–]?\s*[^\n]{10,})",
    re.IGNORECASE,
)
_PADRAO_HABILIDADE_TEXTO = re.compile(
    r"(?:habilidade|aprendizagem essencial|competencia|competência)[:\s]*([^\n]{20,})",
    re.IGNORECASE,
)
_PADRAO_TITULO_SECAO = re.compile(
    r"^(objetivos da aula|objetivos|conteudos|conteúdos|habilidades|recursos didaticos|recursos didáticos|duracao da aula|duração da aula)$",
    re.I,
)
_PADRAO_ETAPA_METODOLOGICA = re.compile(
    r"^(?:\d+\.\s+|trilha\b|pratica de linguagem\b|aula\s+\d+\b|sugestoes para conducao\b)",
    re.IGNORECASE,
)
_SECOES_PRIORITARIAS_PRATICA = [
    "na pratica",
    "atividade",
    "pause e responda",
    "foco no conteudo",
    "encerramento",
]
_SECOES_PARADA = {
    "para comecar",
    "relembre",
    "exploracao",
    "foco no conteudo",
    "pause e responda",
    "na pratica",
    "encerramento",
    "sistematizacao",
    "contextualizacao",
    "leitura analitica",
    "leitura e construcao do conteudo",
    "producao textual",
    "revisao e fechamento",
}

_FINAIS_TRUNCADOS_HABILIDADE = {
    "a", "as", "o", "os", "de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "que",
}


def _normalizar_rotulo_secao(texto: str) -> str:
    return _normalizar_texto(str(texto or "")).strip(" :-")


def _linha_secao(linha: str, nome_secao: str) -> bool:
    base = _normalizar_texto(linha).strip(" :-")
    alvo = _normalizar_texto(nome_secao).strip(" :-")
    return base == alvo


def _extrair_bloco_apos_secao(linhas: list[str], nome_secao: str, limite_linhas: int = 14) -> list[str]:
    bloco = []
    coletando = False

    for linha in linhas:
        if _linha_secao(linha, nome_secao):
            coletando = True
            continue

        if coletando and _PADRAO_TITULO_SECAO.match(linha.strip()):
            break

        if coletando:
            trecho = _limpar_trecho(linha)
            if trecho and not _trecho_descartavel(trecho):
                bloco.append(trecho)
                if len(bloco) >= limite_linhas:
                    break

    return bloco


def _texto_habilidade_truncado(texto: str) -> bool:
    base = _normalizar_texto(texto)
    if not base:
        return True

    palavras = re.findall(r"[a-zà-ÿA-ZÀ-ÿ]+", texto)
    if not palavras:
        return True

    ultimo = _normalizar_texto(palavras[-1])
    if ultimo in _FINAIS_TRUNCADOS_HABILIDADE:
        return True

    if len(texto.strip()) < 30:
        return True

    if texto.strip()[:1].islower():
        return True

    if re.match(r"^[a-zà-ÿ]\s", texto.strip(), flags=re.I):
        return True

    if base.startswith(("s para ", "e para ", "a para ")):
        return True

    return False


def _montar_habilidade_por_secao(linhas: list[str]) -> str:
    bloco = _extrair_bloco_apos_secao(linhas, "Habilidades", limite_linhas=8)
    if not bloco:
        return ""

    texto = _limpar_trecho(" ".join(bloco))
    texto = re.sub(r"^(habilidades?)\s*:\s*", "", texto, flags=re.I).strip()

    if _texto_habilidade_truncado(texto):
        return ""

    return f"Habilidade: {texto}"


def _extrair_objetivos_secao(linhas: list[str]) -> list[str]:
    return _extrair_bloco_apos_secao(linhas, "Objetivos da aula", limite_linhas=8)


def _extrair_conteudos_secao(linhas: list[str]) -> list[str]:
    return _extrair_bloco_apos_secao(linhas, "Conteúdos", limite_linhas=8) or _extrair_bloco_apos_secao(linhas, "Conteudos", limite_linhas=8)


def extrair_secao(linhas: list[str], inicio: str, paradas: set[str] | None = None) -> list[str]:
    coletando = False
    bloco = []
    inicio = _normalizar_rotulo_secao(inicio)
    paradas = paradas or set()

    for linha in linhas:
        normalizada = _normalizar_rotulo_secao(linha)

        if normalizada == inicio:
            coletando = True
            continue

        if coletando and normalizada in paradas:
            break

        if coletando and not _trecho_descartavel(linha):
            bloco.append(_limpar_trecho(linha))

    return bloco


class ExtratorPDF:
    """Extrai conteudo estruturado de texto de PDF."""

    _FILTROS = [
        "todo mundo escreve",
        "virem e conversem",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "link para video",
        "um passo de cada vez",
        "slide",
        "aula",
        "veja no livro",
        "freepik",
        "produzido pela",
        "seduc-sp",
        "de olho no pnld",
    ]

    def extrair(self, texto: str, tema: str) -> dict:
        linhas = [linha.strip() for linha in corrigir_mojibake(texto).split("\n") if linha.strip()]
        linhas_limpas = [_limpar_trecho(linha) for linha in linhas if not _trecho_descartavel(linha)]
        secoes = {
            secao: extrair_secao(linhas, secao, _SECOES_PARADA - {secao})
            for secao in _SECOES_PRIORITARIAS_PRATICA
        }

        conceito = self._extrair_conceito(linhas_limpas, tema)
        atividade_pratica = self._extrair_pratica(linhas_limpas, tema, secoes)
        contexto_aula = self._extrair_contexto(linhas_limpas)
        palavras_chave = self._extrair_palavras_chave(linhas_limpas)
        etapas_detectadas = self._detectar_etapas(linhas)
        texto_prioritario = " ".join(
            " ".join(secoes[nome]) for nome in _SECOES_PRIORITARIAS_PRATICA if secoes.get(nome)
        ).strip()
        objetivos_secao = _extrair_objetivos_secao(linhas)
        conteudos_secao = _extrair_conteudos_secao(linhas)

        from core.lib.classificador import detectar_recursos

        return {
            "conceito_extraido": _trecho_seguro(conceito, tema, 220),
            "atividade_extraida": _trecho_seguro(
                atividade_pratica,
                f"atividades propostas no material, articuladas ao tema {tema}",
                220,
            ),
            "habilidade": self._extrair_habilidade(linhas),
            "objetivos_secao": objetivos_secao,
            "conteudos_secao": conteudos_secao,
            "contexto_aula": _trecho_seguro(contexto_aula, "", 160),
            "palavras_chave": palavras_chave,
            "etapas_detectadas": etapas_detectadas,
            "recursos_detectados": detectar_recursos(texto_prioritario or " ".join(linhas_limpas), tema),
            "texto_prioritario": texto_prioritario,
            "linhas": linhas,
            "linhas_limpas": linhas_limpas,
            "secoes_extraidas": secoes,
        }

    def _linha_valida(self, linha: str) -> bool:
        ll = _normalizar_texto(linha)
        return len(linha) > 10 and not any(
            ll.startswith(f) or ll == f or f in ll for f in self._FILTROS
        )

    def _extrair_habilidade(self, linhas: list[str]) -> str:
        # 1) primeiro tenta BNCC/AE do jeito antigo
        for i, linha in enumerate(linhas):
            if _PADRAO_HABILIDADE.search(linha):
                habilidade = self._montar_bloco_habilidade(linhas, i)
                if habilidade and not _texto_habilidade_truncado(re.sub(r"^Habilidade:\s*", "", habilidade, flags=re.I)):
                    return habilidade

        # 2) depois tenta linha textual "Habilidade: ..."
        for linha in linhas:
            match = _PADRAO_HABILIDADE_TEXTO.search(linha)
            if match:
                texto = _limpar_trecho(match.group(1))
                if texto and not _texto_habilidade_truncado(texto):
                    return f"Habilidade: {texto}"

        # 3) por fim, tenta bloco estruturado da seção "Habilidades"
        habilidade_secao = _montar_habilidade_por_secao(linhas)
        if habilidade_secao:
            return habilidade_secao

        return ""

    def _montar_bloco_habilidade(self, linhas: list[str], indice: int) -> str:
        bloco = []
        for j in range(max(0, indice - 1), min(indice + 14, len(linhas))):
            linha = linhas[j].strip()
            if not linha:
                continue
            normalizada = _normalizar_texto(linha)
            if j < indice and "habilidade" not in normalizada and "aprendizagem essencial" not in normalizada:
                continue
            if j > indice and _PADRAO_HABILIDADE.search(linha):
                break
            if j > indice and self._fim_bloco_habilidade(linha):
                break
            bloco.append(linha)
            texto_parcial = _limpar_trecho(" ".join(bloco))
            if (
                _PADRAO_CODIGO_BNCC.search(texto_parcial)
                and len(texto_parcial) >= 80
                and texto_parcial.endswith((".", ";"))
            ):
                break

        texto = _limpar_trecho(" ".join(bloco))
        texto = re.sub(
            r"^(?:habilidades?\s+bncc\s+e\s+curriculo\s+paulista)\s*",
            "",
            texto,
            flags=re.I,
        )
        texto = re.sub(
            r"^(?:habilidades?|aprendizagem essencial|competencia|competência)\s*:\s*",
            "Habilidade: ",
            texto,
            flags=re.I,
        )
        if _PADRAO_CODIGO_BNCC.search(texto):
            texto = re.sub(
                r"^(?:habilidade|aprendizagem essencial|competencia|competência)\s*:\s*",
                "Habilidade: ",
                texto,
                flags=re.I,
            )
        return texto

    def _fim_bloco_habilidade(self, linha: str) -> bool:
        if _PADRAO_HABILIDADE.search(linha):
            return False
        normalizada = _normalizar_texto(linha).strip(" .:-")
        if _PADRAO_ETAPA_METODOLOGICA.match(normalizada):
            return True
        marcadores = {
            "slide",
            "tempo",
            "dinamica",
            "dinamica de conducao",
            "para comecar",
            "foco no conteudo",
            "na pratica",
            "pause e responda",
            "encerramento",
            "sistematizacao",
            "professor",
            "para professores",
            "recursos",
            "objetivo",
            "objetivos",
            "objeto do conhecimento",
            "conteudo",
            "conteudo principal",
            "tema",
            "titulo",
            "material",
        }
        return (
            normalizada in marcadores
            or normalizada.startswith("slide ")
            or normalizada.startswith("objetivo ")
            or normalizada.startswith("objeto ")
            or normalizada.startswith("conteudo ")
        )

    def _extrair_conceito(self, linhas: list[str], tema: str) -> str:
        marcadores = [
            "o que e",
            "definicao",
            "conceito",
            "e o uso de",
            "e uma estrategia",
            "consiste em",
            "refere-se a",
            "trata-se de",
            "podemos definir",
        ]
        for i, linha in enumerate(linhas):
            linha_lower = _normalizar_texto(linha)
            if any(m in linha_lower for m in marcadores):
                bloco = []
                if self._linha_valida(linha):
                    bloco.append(linha)
                for j in range(i + 1, min(i + 4, len(linhas))):
                    if self._linha_valida(linhas[j]):
                        bloco.append(linhas[j])
                if bloco:
                    return " ".join(bloco)[:300]
                break
        return tema

    def _extrair_pratica(self, linhas: list[str], tema: str, secoes: dict[str, list[str]] | None = None) -> str:
        secoes = secoes or {}
        for nome_secao in _SECOES_PRIORITARIAS_PRATICA:
            bloco = secoes.get(nome_secao) or []
            if bloco:
                return " ".join(bloco)[:300]

        marcadores = [
            "atividade",
            "exercicio",
            "na pratica",
            "analise",
            "compare",
            "identifique",
            "reescreva",
            "produz",
        ]
        for i, linha in enumerate(linhas):
            linha_lower = _normalizar_texto(linha)
            if any(m in linha_lower for m in marcadores) and len(linha) > 15:
                bloco = []
                if self._linha_valida(linha):
                    bloco.append(linha)
                for j in range(i + 1, min(i + 5, len(linhas))):
                    if self._linha_valida(linhas[j]):
                        bloco.append(linhas[j])
                if bloco:
                    return " ".join(bloco)[:300]
                break
        return "atividades propostas no material"

    def _extrair_contexto(self, linhas: list[str]) -> str:
        marcadores = [
            "voce ja",
            "pense em",
            "imagine",
            "o que as pessoas",
            "qual e a importancia",
            "como voce",
            "nas ultimas aulas",
        ]
        for linha in linhas:
            linha_lower = _normalizar_texto(linha)
            if any(m in linha_lower for m in marcadores) and len(linha) > 20:
                return _trecho_seguro(linha, "", 160)
        return ""

    def _extrair_palavras_chave(self, linhas: list[str]) -> list[str]:
        palavras_chave = []
        for linha in linhas:
            if 5 < len(linha) < 60 and not linha.startswith("AULA") and not linha.startswith("Slide"):
                palavras_chave.append(linha)
            if len(palavras_chave) >= 5:
                break
        return palavras_chave

    def _detectar_etapas(self, linhas: list[str]) -> list[str]:
        etapas_conhecidas = {
            "para comecar",
            "relembre",
            "exploracao",
            "foco no conteudo",
            "formalizacao",
            "pause e responda",
            "na pratica",
            "encerramento",
            "sistematizacao",
            "contextualizacao",
            "leitura analitica",
            "leitura e construcao do conteudo",
        }
        encontradas = []
        for linha in linhas:
            normalizada = _normalizar_rotulo_secao(linha)
            if normalizada in etapas_conhecidas:
                encontradas.append(normalizada)
        return encontradas
