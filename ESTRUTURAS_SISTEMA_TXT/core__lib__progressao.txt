"""
Módulo de progressão entre aulas sequenciais.

Evita que aulas com o mesmo tema ou da mesma sequência
gerem textos idênticos em acompanhamento, acessibilidade e metodologia.
"""

import hashlib


# ── Verbos de ação com variação por posição ─────────────────────────────────

VERBOS_OBSERVACAO = [
    "Observar",
    "Verificar",
    "Identificar",
    "Perceber",
    "Notar",
    "Acompanhar",
]

VERBOS_VERIFICACAO = [
    "Verificar",
    "Checar",
    "Conferir",
    "Avaliar",
    "Examinar",
    "Constatar",
]

VERBOS_ACOMPANHAMENTO = [
    "Acompanhar",
    "Monitorar",
    "Observar ao longo da aula",
    "Registrar",
    "Documentar",
    "Mapear",
]

CONECTORES_PROGRESSAO = {
    0: "durante as discussões e atividades propostas",
    1: "ao longo das etapas de trabalho",
    2: "nos registros e nas interações",
    3: "nas respostas e justificativas apresentadas",
    4: "na resolução e na socialização das atividades",
}

# ── Frases de progressão por posição na sequência ──────────────────────────

FOCO_PROGRESSAO = {
    0: "introduzir e explorar",
    1: "aprofundar e aplicar",
    2: "consolidar e sistematizar",
    3: "avaliar e retomar",
}


def _indice_hash(partes: list[str], total: int) -> int:
    if total <= 1:
        return 0
    chave = "|".join(str(p or "") for p in partes)
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    return int(digest, 16) % total


def verbo_observacao(indice_aula: int, seed: str = "") -> str:
    """Retorna um verbo de observação variado pela posição da aula."""
    idx = (indice_aula + _indice_hash([seed], 3)) % len(VERBOS_OBSERVACAO)
    return VERBOS_OBSERVACAO[idx]


def verbo_verificacao(indice_aula: int, seed: str = "") -> str:
    """Retorna um verbo de verificação variado pela posição da aula."""
    idx = (indice_aula + _indice_hash([seed, "ver"], 3)) % len(VERBOS_VERIFICACAO)
    return VERBOS_VERIFICACAO[idx]


def verbo_acompanhamento(indice_aula: int, seed: str = "") -> str:
    """Retorna um verbo de acompanhamento variado pela posição da aula."""
    idx = (indice_aula + _indice_hash([seed, "acomp"], 3)) % len(VERBOS_ACOMPANHAMENTO)
    return VERBOS_ACOMPANHAMENTO[idx]


def conector_progressao(indice_aula: int) -> str:
    """Retorna um conector de progressão pela posição da aula."""
    return CONECTORES_PROGRESSAO.get(indice_aula % len(CONECTORES_PROGRESSAO), CONECTORES_PROGRESSAO[0])


def foco_progressao(indice_aula: int) -> str:
    """Retorna o foco pedagógico pela posição na sequência."""
    return FOCO_PROGRESSAO.get(indice_aula % len(FOCO_PROGRESSAO), FOCO_PROGRESSAO[0])


VARIACOES_VERIFICACAO_EF = [
    "Realizar uma parada estratégica propondo uma pergunta objetiva sobre {tema}: os estudantes devem justificar suas respostas com base no conteúdo discutido.",
    "Propor uma questão de verificação sobre {tema}, pedindo que os alunos relacionem a resposta a um exemplo do cotidiano financeiro.",
    "Fazer uma checagem rápida sobre {tema}: cada aluno registra individualmente sua resposta antes da correção coletiva.",
    "Verificar a compreensão sobre {tema} com uma pergunta direta, coletando respostas orais e identificando pontos que precisam de retomada.",
]

VARIACOES_RETOMADA = [
    "Retomar brevemente os conceitos explorados na aula anterior sobre {tema_anterior} para garantir a base necessária para as atividades de hoje.",
    "Revisitar os registros produzidos na aula anterior sobre {tema_anterior}, conectando-os ao foco prático do dia.",
    "Recuperar as aprendizagens construídas sobre {tema_anterior}, destacando os pontos que serão aplicados na atividade de hoje.",
    "Reativar os conhecimentos sobre {tema_anterior} com uma pergunta rápida de sondagem antes de iniciar a prática.",
    "Resgatar as ideias centrais discutidas no último encontro sobre {tema_anterior}, preparando a turma para os novos desafios.",
    "Iniciar relembrando os principais pontos trabalhados anteriormente sobre {tema_anterior}, garantindo a continuidade do raciocínio.",
]


def ajustar_texto_por_posicao(texto: str, indice_aula: int, total_aulas: int, tema: str = "") -> str:
    """
    Ajusta sutilmente o texto de uma etapa com base na posição
    da aula na sequência, para evitar repetição.
    """
    if total_aulas <= 1:
        return texto

    texto_lower = texto.lower()
    if any(term in texto_lower for term in ["retomar", "revisitar", "recuperar", "reativar", "para começar", "para comecar"]):
        idx = (indice_aula + _indice_hash([tema, "retomada"], 4)) % len(VARIACOES_RETOMADA)
        return VARIACOES_RETOMADA[idx].format(tema_anterior=tema)

    tema_lower = (tema or "").lower()
    is_ef = "financeir" in tema_lower or "poupan" in tema_lower or "orcament" in tema_lower or "orçament" in tema_lower or "gasto" in tema_lower or "credito" in tema_lower or "crédito" in tema_lower or "consum" in tema_lower or "investimento" in tema_lower or "cesta basica" in tema_lower or "cesta básica" in tema_lower or "preços" in tema_lower or "precos" in tema_lower

    if is_ef:
        if any(term in texto_lower for term in ["pause", "pausa de checagem", "verificação", "verificacao", "conferir a compreensão", "conferir a compreensao"]):
            idx = (indice_aula + _indice_hash([tema, "verificacao"], 4)) % len(VARIACOES_VERIFICACAO_EF)
            return VARIACOES_VERIFICACAO_EF[idx].format(tema=tema)

    posicao = indice_aula % len(FOCO_PROGRESSAO)

    # Adiciona marca de continuidade a partir da 2ª aula
    if posicao == 1 and "retomar" not in texto.lower():
        texto = texto.replace(
            "Retomar conhecimentos prévios",
            "Retomar os conceitos trabalhados na aula anterior",
            1,
        )
    elif posicao == 2 and "consolidar" not in texto.lower():
        texto = texto.replace(
            "Promover discussão inicial",
            "Retomar e consolidar as discussões anteriores",
            1,
        )
    elif posicao >= 3 and "avaliar" not in texto.lower()[:80]:
        texto = texto.replace(
            "Promover discussão inicial",
            "Avaliar, por meio de discussão, a compreensão acumulada",
            1,
        )

    return texto


def variar_inicio_frase(texto: str, indice_aula: int, tema: str) -> str:
    """
    Substitui os verbos e expressões mais repetidos no início das etapas
    de metodologia sem IA por variantes naturais, usando hash determinístico.
    """
    if not texto:
        return texto

    import re
    # Hashing determinístico para escolher a variante
    chave = f"{tema}_{texto[:40]}_{indice_aula}"
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    hash_val = int(digest, 16)

    # Lista de mapeamentos de início (case-insensitive para casar)
    mapa_variacoes = [
        (r"^[Ii]niciar a aula com", [
            "Começar a aula com", 
            "Dar início à aula com", 
            "Abrir a aula apresentando", 
            "Introduzir o tema da aula com"
        ]),
        (r"^[Rr]etomar com a turma", [
            "Relembrar com os estudantes", 
            "Revisitar com a turma", 
            "Recuperar com os alunos", 
            "Retornar com a turma a"
        ]),
        (r"^[Rr]etomar os conceitos", [
            "Revisitar os conceitos", 
            "Relembrar os conceitos", 
            "Recuperar os conceitos", 
            "Rever as ideias"
        ]),
        (r"^[Cc]onduzir a leitura", [
            "Orientar a leitura", 
            "Guiar a leitura", 
            "Mediar a leitura", 
            "Coordenar a leitura"
        ]),
        (r"^[Cc]onduzir a explicacao", [
            "Mediar a explicação", 
            "Apresentar a explicação", 
            "Desenvolver a explicação", 
            "Guiar a explicação"
        ]),
        (r"^[Cc]onduzir a resolucao", [
            "Orientar a resolução", 
            "Guiar a resolução", 
            "Mediar a resolução", 
            "Acompanhar a resolução"
        ]),
        (r"^[Ee]xplicar o procedimento", [
            "Apresentar o procedimento", 
            "Expor o procedimento", 
            "Demonstrar o procedimento", 
            "Esclarecer o procedimento"
        ]),
        (r"^[Ee]xplicar os conceitos", [
            "Apresentar os conceitos", 
            "Expor os conceitos", 
            "Sistematizar os conceitos", 
            "Esclarecer os conceitos"
        ]),
        (r"^[Oo]rientar a resolucao", [
            "Guiar a resolução", 
            "Instruir a resolução", 
            "Mediar a resolução", 
            "Direcionar a resolução"
        ]),
        (r"^[Oo]rientar a atividade", [
            "Guiar a atividade", 
            "Conduzir a atividade", 
            "Mediar a atividade", 
            "Acompanhar a atividade"
        ]),
        (r"^[Pp]ropor atividade", [
            "Apresentar atividade", 
            "Sugerir atividade", 
            "Lançar atividade", 
            "Trazer atividade"
        ]),
        (r"^[Ee]ncerrar a aula com", [
            "Finalizar a aula com", 
            "Concluir a aula com", 
            "Fechar a aula com", 
            "Terminar a aula com"
        ]),
        (r"^[Ee]ncerrar com", [
            "Finalizar com", 
            "Concluir com", 
            "Fechar com", 
            "Terminar com"
        ]),
        (r"^[Ss]intetizar os aprendizados", [
            "Resumir os aprendizados", 
            "Consolidar os aprendizados", 
            "Reunir os aprendizados", 
            "Sistematizar os aprendizados"
        ]),
    ]

    for padrao, variantes in mapa_variacoes:
        if re.match(padrao, texto):
            variante = variantes[hash_val % len(variantes)]
            texto = re.sub(padrao, variante, texto, count=1)
            break

    return texto

