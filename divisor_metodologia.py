import re
from enum import Enum
from typing import List, Tuple


class EstrategiaDivisao(Enum):
    DENSIDADE = "densidade"
    TIPO_ATIVIDADE = "tipo_atividade"
    COMPLEXIDADE = "complexidade"


class SecaoMetodologia:
    def __init__(self, nome: str, conteudo: str):
        self.nome = nome
        self.conteudo = conteudo
        self.tipo = self._inferir_tipo(nome)

    def _inferir_tipo(self, nome: str) -> str:
        n = nome.lower()
        if "comecar" in n or "abertura" in n or "disparo inicial" in n:
            return "introducao"
        if (
            "exploracao" in n
            or "leitura" in n
            or "conteudo" in n
            or "teoria" in n
            or "analise" in n
            or "sistematizacao" in n
            or "pause e responda" in n
        ):
            return "teoria"
        if (
            "pratica" in n
            or "atividade" in n
            or "producao" in n
            or "revisao" in n
            or "submissao" in n
        ):
            return "pratica"
        if "encerramento" in n or "finalizacao" in n or "fechamento" in n:
            return "conclusao"
        return "outros"


class CriteriosDivisao:
    def __init__(self, secoes: List[SecaoMetodologia]):
        self.quantidade_secoes = len(secoes)
        self.volume_teorico = sum(len(s.conteudo) for s in secoes if s.tipo == "teoria")
        self.quantidade_atividades = sum(1 for s in secoes if s.tipo == "pratica")
        self.tem_pratica = self.quantidade_atividades > 0


class DivisorMetodologia:
    def __init__(self):
        self.marcadores = [
            "Para comecar:",
            "Para começar:",
            "Disparo inicial / contextualizacao:",
            "Disparo inicial / contextualização:",
            "Leitura ou exploracao inicial:",
            "Leitura ou exploração inicial:",
            "Leitura compartilhada ou individual:",
            "Predicao guiada:",
            "Predição guiada:",
            "Analise guiada:",
            "Análise guiada:",
            "Sistematizacao:",
            "Sistematização:",
            "Foco no conteudo:",
            "Foco no conteúdo:",
            "Pause e responda:",
            "Na pratica:",
            "Na prática:",
            "Producao textual:",
            "Produção textual:",
            "Revisao orientada:",
            "Revisão orientada:",
            "Escrita da versao final:",
            "Escrita da versão final:",
            "Submissao e socializacao:",
            "Submissão e socialização:",
            "Revisao e fechamento:",
            "Revisão e fechamento:",
            "Encerramento:",
        ]

    def extrair_secoes(self, texto: str) -> List[SecaoMetodologia]:
        padrao = "(" + "|".join(re.escape(m) for m in self.marcadores) + ")"
        partes = re.split(padrao, texto)

        secoes = []
        i = 1
        while i < len(partes):
            nome = partes[i].strip()
            conteudo = partes[i + 1].strip() if (i + 1) < len(partes) else ""
            secoes.append(SecaoMetodologia(nome, conteudo))
            i += 2

        if not secoes:
            blocos = [b.strip() for b in texto.split("\n\n") if b.strip()]
            for idx, bloco in enumerate(blocos):
                secoes.append(SecaoMetodologia(f"Parte {idx + 1}:", bloco))

        return secoes

    def dividir(self, texto: str) -> Tuple[str, str]:
        secoes = self.extrair_secoes(texto)

        if len(secoes) <= 1:
            meio = len(texto) // 2
            ponto = texto.find(".", meio)
            if ponto == -1:
                ponto = meio
            else:
                ponto += 1
            return texto[:ponto].strip(), texto[ponto:].strip()

        idx_pratica = -1
        for idx, secao in enumerate(secoes):
            if secao.tipo == "pratica":
                idx_pratica = idx
                break

        if idx_pratica > 0:
            secoes_dia1 = secoes[:idx_pratica]
            secoes_dia2 = secoes[idx_pratica:]
        else:
            meio = len(secoes) // 2
            secoes_dia1 = secoes[:meio]
            secoes_dia2 = secoes[meio:]

        metodologia_dia1 = self._formatar_dia(secoes_dia1, dia=1)
        metodologia_dia2 = self._formatar_dia(secoes_dia2, dia=2)
        return metodologia_dia1, metodologia_dia2

    def _formatar_dia(self, secoes: List[SecaoMetodologia], dia: int) -> str:
        texto = ""
        for secao in secoes:
            texto += f"{secao.nome}\n{secao.conteudo}\n\n"

        texto = texto.strip()

        if dia == 1 and not any(secao.tipo == "conclusao" for secao in secoes):
            texto += (
                "\n\nEncerramento:\nRetomar os principais pontos abordados nesta primeira parte da aula "
                "e preparar os estudantes para a aplicacao pratica no proximo encontro."
            )

        if dia == 2 and not any(secao.tipo == "introducao" for secao in secoes):
            texto = (
                "Para comecar:\nRetomar brevemente os conceitos explorados na aula anterior para garantir "
                "a base necessaria para as atividades de hoje.\n\n" + texto
            )

        return texto


def processar_pdf_e_dividir_metodologia(texto_metodologia: str) -> Tuple[str, str]:
    divisor = DivisorMetodologia()
    return divisor.dividir(texto_metodologia)
