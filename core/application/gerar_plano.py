from core.domain.models import GerarPlanoCommand
from core.extraction.context_builder import ContextBuilder
from core.generation import PlanGenerator
import logging

logger = logging.getLogger(__name__)

class GerarPlanoService:
    def __init__(self, context_builder: ContextBuilder, generator: PlanGenerator):
        self.context_builder = context_builder
        self.generator = generator

    def execute(self, command: GerarPlanoCommand) -> dict:
        logger.info("[GerarPlanoService] Executando comando via Strangler Fig...")
        context = self.context_builder.build(command)
        plan = self.generator.generate(context)
        
        # Aqui, no futuro, injetaremos as lógicas do Finalizer (refinamento)
        return plan
