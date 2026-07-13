import re


_PADROES_INFINITIVO_METODOLOGIA = [
    (r"\bO professor inicia a aula\b", "Iniciar a aula"),
    (r"\bO professor inicia\b", "Iniciar"),
    (r"\bO professor retoma\b", "Retomar"),
    (r"\bO professor apresenta\b", "Apresentar"),
    (r"\bO professor explica\b", "Explicar"),
    (r"\bO professor organiza\b", "Organizar"),
    (r"\bO professor orienta\b", "Orientar"),
    (r"\bO professor propõe\b", "Propor"),
    (r"\bO professor propoe\b", "Propor"),
    (r"\bO professor conduz\b", "Conduzir"),
    (r"\bO professor solicita\b", "Solicitar"),
    (r"\bO professor finaliza\b", "Finalizar"),
    (r"\bO professor desenvolve\b", "Desenvolver"),
    (r"\bO professor realiza\b", "Realizar"),
    (r"\bO professor utiliza\b", "Utilizar"),
    (r"\bO professor promove\b", "Promover"),
    (r"\bO professor observa\b", "Observar"),
    (r"\bO professor registra\b", "Registrar"),
    (r"\bOs alunos realizam\b", "Realizar"),
    (r"\bOs alunos registram\b", "Registrar"),
    (r"\bOs alunos respondem\b", "Responder"),
    (r"\bOs alunos analisam\b", "Analisar"),
    (r"\bOs alunos produzem\b", "Produzir"),
    (r"\bA turma analisa\b", "Analisar"),
    (r"\bA turma realiza\b", "Realizar"),
    (r"\bA turma registra\b", "Registrar"),
    (r"\bA aula começa com\b", "Iniciar a aula com"),
    (r"\bA aula inicia com\b", "Iniciar a aula com"),
    (r"\bInicie a aula\b", "Iniciar a aula"),
    (r"\bInicie\b", "Iniciar"),
    (r"\bApresente\b", "Apresentar"),
    (r"\bExplique\b", "Explicar"),
    (r"\bOrganize\b", "Organizar"),
    (r"\bOriente\b", "Orientar"),
    (r"\bProponha\b", "Propor"),
    (r"\bConduza\b", "Conduzir"),
    (r"\bSolicite\b", "Solicitar"),
    (r"\bFinalize\b", "Finalizar"),
    (r"\bRealize\b", "Realizar"),
    (r"\bUtilize\b", "Utilizar"),
    (r"\bPromova\b", "Promover"),
    (r"\bObserve\b", "Observar"),
    (r"\bRegistre\b", "Registrar"),
    (r"\bProjete\b", "Projetar"),
    (r"\bPeça\b", "Pedir"),
    (r"\bFaça\b", "Fazer"),
    (r"\bDivida\b", "Dividir"),
    (r"\bSugira\b", "Sugerir"),
    (r"\bDistribua\b", "Distribuir"),
    (r"\bMostre\b", "Mostrar"),
    (r"\bDiga\b", "Dizer"),
    (r"\bLeia\b", "Ler"),
    (r"\bEscreva\b", "Escrever"),
    (r"\bPeçam\b", "Pedir"),
    (r"\bEnfatize\b", "Enfatizar"),
]


def ajustar_verbos_para_infinitivo(texto: str) -> str:
    texto_final = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto_final:
        return ""

    for padrao, substituicao in _PADROES_INFINITIVO_METODOLOGIA:
        texto_final = re.sub(
            rf"(^|(?<=[.!?]\s)|(?<=\|\s)){padrao}",
            lambda m, s=substituicao: f"{m.group(1)}{s}",
            texto_final,
            flags=re.I,
        )
    return texto_final
