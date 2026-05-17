
import re
from enum import Enum
from typing import List, Tuple, Dict, Optional

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
        if "comecar" in n or "abertura" in n: return "introducao"
        if "conteudo" in n or "teoria" in n: return "teoria"
        if "pratica" in n or "atividade" in n: return "pratica"
        if "encerramento" in n or "finalizacao" in n: return "conclusao"
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
            "Para começar:",
            "Foco no conteúdo:",
            "Na prática:",
            "Encerramento:",
            "Pause e responda:"
        ]

    def extrair_secoes(self, texto: str) -> List[SecaoMetodologia]:
        """Divide o texto da metodologia em seções baseadas em marcadores padrão."""
        padrao = "(" + "|".join(re.escape(m) for m in self.marcadores) + ")"
        partes = re.split(padrao, texto)
        
        secoes = []
        # O split retorna [texto_antes, marcador1, texto1, marcador2, texto2, ...]
        i = 1
        while i < len(partes):
            nome = partes[i].strip()
            conteudo = partes[i+1].strip() if (i+1) < len(partes) else ""
            secoes.append(SecaoMetodologia(nome, conteudo))
            i += 2
            
        # Se não encontrou marcadores, tenta dividir por parágrafos ou marcadores de slide
        if not secoes:
            blocos = [b.strip() for b in texto.split('\n\n') if b.strip()]
            for idx, b in enumerate(blocos):
                secoes.append(SecaoMetodologia(f"Parte {idx+1}:", b))
                
        return secoes

    def dividir(self, texto: str) -> Tuple[str, str]:
        """Divide a metodologia em dois dias."""
        secoes = self.extrair_secoes(texto)
        
        if len(secoes) <= 1:
            # Fallback para divisão por texto se houver apenas uma seção gigante
            meio = len(texto) // 2
            # Tentar quebrar em um ponto final
            ponto = texto.find('.', meio)
            if ponto == -1: ponto = meio
            else: ponto += 1
            return texto[:ponto].strip(), texto[ponto:].strip()

        # Estratégia: Se houver "Na prática", ela inicia o Dia 2
        idx_pratica = -1
        for idx, s in enumerate(secoes):
            if s.tipo == "pratica":
                idx_pratica = idx
                break
        
        if idx_pratica != -1:
            # Dia 1: Tudo até antes da prática
            # Dia 2: Da prática em diante
            secoes_dia1 = secoes[:idx_pratica]
            secoes_dia2 = secoes[idx_pratica:]
        else:
            # Divisão equilibrada por quantidade de seções
            meio = len(secoes) // 2
            secoes_dia1 = secoes[:meio]
            secoes_dia2 = secoes[meio:]

        # Formatação final com reforços pedagógicos
        metodologia_dia1 = self._formatar_dia(secoes_dia1, dia=1)
        metodologia_dia2 = self._formatar_dia(secoes_dia2, dia=2)
        
        return metodologia_dia1, metodologia_dia2

    def _formatar_dia(self, secoes: List[SecaoMetodologia], dia: int) -> str:
        texto = ""
        for s in secoes:
            texto += f"{s.nome}\n{s.conteudo}\n\n"
        
        texto = texto.strip()
        
        # Adicionar fechamento ao Dia 1 se não tiver
        if dia == 1 and not any(s.tipo == "conclusao" for s in secoes):
            texto += "\n\nEncerramento:\nRetomar os principais pontos abordados nesta primeira parte da aula e preparar os estudantes para a aplicação prática no próximo encontro."
            
        # Adicionar abertura ao Dia 2 se não tiver
        if dia == 2 and not any(s.tipo == "introducao" for s in secoes):
            texto = "Para começar:\nRetomar brevemente os conceitos explorados na aula anterior para garantir a base necessária para as atividades de hoje.\n\n" + texto
            
        return texto

def processar_pdf_e_dividir_metodologia(texto_metodologia: str) -> Tuple[str, str]:
    divisor = DivisorMetodologia()
    return divisor.dividir(texto_metodologia)
