from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class GerarPlanoCommand:
    arquivo: Path
    disciplina: str
    turma: str
    bimestre: str = ""
    professor: str = ""
    modalidade_eja: bool = False
    permitir_ia: bool = False

@dataclass(frozen=True)
class ContextoAula:
    comando: GerarPlanoCommand
    texto_fonte: str
    tema: str
    numero_aula: str
    perfil: str
    # extracao: "ExtracaoEstruturada" # Will be added later when ExtracaoEstruturada is created
