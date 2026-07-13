from typing import Dict, Any
from core.domain.models import ContextoAula
from core.resultados_aula import montar_resultado_aula_local
import logging

logger = logging.getLogger(__name__)

class LocalPlanGenerator:
    def generate(self, context: ContextoAula) -> Dict[str, Any]:
        logger.info(f"[LocalPlanGenerator] Gerando plano para: {context.tema}")
        return montar_resultado_aula_local(
            texto=context.texto_fonte,
            tema=context.tema,
            material_digital="Material Digital", # fallback if needed
            numero_aula=context.numero_aula,
            disciplina_base=context.comando.disciplina,
            turma=context.comando.turma,
            provedor_ia="",
            perfil=context.perfil,
            contexto_metodologico="Contexto Padrão" # This is a placeholder for the legacy logic
        )
