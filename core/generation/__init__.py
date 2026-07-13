from typing import Protocol, Dict, Any
from core.domain.models import ContextoAula

class PlanGenerator(Protocol):
    def generate(self, context: ContextoAula) -> Dict[str, Any]:
        """Gera o plano (retornando um dict legado por enquanto para manter compatibilidade)"""
        ...
