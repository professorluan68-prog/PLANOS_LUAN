import re
import unicodedata
from enum import Enum
from typing import List, Tuple


class EstrategiaDivisao(Enum):
    """Estratégias disponíveis para divisão de metodologia."""
    DENSIDADE = "densidade"
    TIPO_ATIVIDADE = "tipo_atividade"
    COMPLEXIDADE = "complexidade"


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto removendo acentos e normalizando espaços.
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        Texto normalizado em minúsculas
    """
    if not texto:
        return ""
    
    # Remove acentos
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    
    # Normaliza espaços e converte para minúscula
    texto = re.sub(r'\s+', ' ', texto).strip().lower()
    return texto


class SecaoMetodologia:
    """Representa uma seção de metodologia extraída do texto."""
    
    def __init__(self, nome: str, conteudo: str):
        """
        Inicializa uma seção de metodologia.
        
        Args:
            nome: Nome/título da seção
            conteudo: Conteúdo da seção
        """
        self.nome = nome
        self.conteudo = conteudo
        self.tipo = self._inferir_tipo(nome)

    def _inferir_tipo(self, nome: str) -> str:
        """
        Infere o tipo de seção baseado no nome.
        
        Args:
            nome: Nome da seção
            
        Returns:
            Tipo da seção (introducao, teoria, pratica, conclusao ou outros)
        """
        n = normalizar_texto(nome)
        
        if any(palavra in n for palavra in ["comecar", "abertura", "disparo inicial"]):
            return "introducao"
        
        if any(palavra in n for palavra in [
            "exploracao", "leitura", "conteudo", "teoria", 
            "analise", "sistematizacao", "pause e responda"
        ]):
            return "teoria"
        
        if any(palavra in n for palavra in [
            "pratica", "atividade", "producao", "revisao", "submissao"
        ]):
            return "pratica"
        
        if any(palavra in n for palavra in ["encerramento", "finalizacao", "fechamento"]):
            return "conclusao"
        
        return "outros"


class CriteriosDivisao:
    """Critérios para divisão de metodologia."""
    
    def __init__(self, secoes: List[SecaoMetodologia]):
        """
        Inicializa os critérios de divisão.
        
        Args:
            secoes: Lista de seções de metodologia
        """
        self.quantidade_secoes = len(secoes)
        self.volume_teorico = sum(len(s.conteudo) for s in secoes if s.tipo == "teoria")
        self.quantidade_atividades = sum(1 for s in secoes if s.tipo == "pratica")
        self.tem_pratica = self.quantidade_atividades > 0


class DivisorMetodologia:
    """Divide a metodologia em dois momentos pedagógicos."""
    
    def __init__(self):
        """Inicializa o divisor com os marcadores conhecidos."""
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
        # Pré-compilar padrão para melhor performance
        self._compilar_padrao()

    def _compilar_padrao(self) -> None:
        """Compila o padrão regex uma vez para evitar recompilação."""
        padrao_str = "(" + "|".join(re.escape(m) for m in self.marcadores) + ")"
        self.padrao_compilado = re.compile(padrao_str)

    def extrair_secoes(self, texto: str) -> List[SecaoMetodologia]:
        """
        Extrai seções de metodologia do texto.
        
        Args:
            texto: Texto contendo a metodologia
            
        Returns:
            Lista de seções extraídas
        """
        if not texto or not texto.strip():
            return []
        
        partes = self.padrao_compilado.split(texto)

        secoes = []
        i = 1
        while i < len(partes):
            nome = partes[i].strip() if i < len(partes) else ""
            conteudo = partes[i + 1].strip() if (i + 1) < len(partes) else ""
            
            if nome:
                secoes.append(SecaoMetodologia(nome, conteudo))
            i += 2

        # Fallback: se não encontrou nenhuma seção, divide por parágrafos
        if not secoes:
            blocos = [b.strip() for b in texto.split("\n\n") if b.strip()]
            for idx, bloco in enumerate(blocos, start=1):
                secoes.append(SecaoMetodologia(f"Parte {idx}:", bloco))

        return secoes

    def dividir(self, texto: str) -> Tuple[str, str]:
        """
        Divide a metodologia em dois momentos.
        
        Args:
            texto: Texto da metodologia a dividir
            
        Returns:
            Tupla contendo (primeiro_momento, segundo_momento)
        """
        if not texto or not texto.strip():
            return "", ""
        
        secoes = self.extrair_secoes(texto)

        if len(secoes) <= 1:
            return self._dividir_por_tamanho(texto)

        idx_pratica = self._encontrar_primeira_pratica(secoes)

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

    def _dividir_por_tamanho(self, texto: str) -> Tuple[str, str]:
        """
        Divide o texto por tamanho quando não há seções bem definidas.
        
        Args:
            texto: Texto a dividir
            
        Returns:
            Tupla contendo (primeira_parte, segunda_parte)
        """
        meio = len(texto) // 2
        ponto = texto.find(".", meio)
        
        if ponto == -1:
            ponto = meio
        else:
            ponto += 1
        
        return texto[:ponto].strip(), texto[ponto:].strip()

    def _encontrar_primeira_pratica(self, secoes: List[SecaoMetodologia]) -> int:
        """
        Encontra o índice da primeira seção prática.
        
        Args:
            secoes: Lista de seções
            
        Returns:
            Índice da primeira prática, ou -1 se não encontrar
        """
        for idx, secao in enumerate(secoes):
            if secao.tipo == "pratica":
                return idx
        return -1

    def _formatar_dia(self, secoes: List[SecaoMetodologia], dia: int) -> str:
        """
        Formata as seções para um dia específico.
        
        Args:
            secoes: Seções a formatar
            dia: Número do dia (1 ou 2)
            
        Returns:
            Texto formatado para o dia
        """
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
    """
    Processa PDF e divide a metodologia em dois momentos.
    
    Args:
        texto_metodologia: Texto de metodologia a processar
        
    Returns:
        Tupla contendo (primeiro_momento, segundo_momento)
    """
    divisor = DivisorMetodologia()
    return divisor.dividir(texto_metodologia)
