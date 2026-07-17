from typing import Protocol
from core.domain.models import GerarPlanoCommand, ContextoAula
from core.lib.classificador import perfil_disciplina
from core.lib.extrator_pdf import extrair_texto_pdf
from core.lib.extrator_titulo import _extrair_titulo_multilinha

class ContextBuilder(Protocol):
    def build(self, command: GerarPlanoCommand) -> ContextoAula: ...

class DefaultContextBuilder:
    def build(self, command: GerarPlanoCommand) -> ContextoAula:
        # Extrai o texto base
        texto_fonte = extrair_texto_pdf(str(command.arquivo))
        
        # Extrai os metadados do título
        tema = _extrair_titulo_multilinha(texto_fonte, command.disciplina)
        numero_aula = ""
        disciplina_base = command.disciplina
        
        # Define o perfil disciplinar
        perfil = perfil_disciplina(disciplina_base)
        
        return ContextoAula(
            comando=command,
            texto_fonte=texto_fonte,
            tema=tema,
            numero_aula=numero_aula,
            perfil=perfil,
        )
