"""
Motor unificado de geração de metodologia (sem IA).

Substitui a geração fraca do inteligencia_local.py (5 etapas fixas)
pelo motor sofisticado que já existia no lote.py (etapas variáveis por perfil),
integrando as novas bibliotecas de técnicas e progressão.
"""

import re
from core.lib.classificador import perfil_disciplina, detectar_tipo_aula, normalizar_texto, contem_termos
from core.lib.tecnicas import SeletorTecnicas
from core.lib.progressao import ajustar_texto_por_posicao
from core.lib.extrator_pdf import ExtratorPDF
from core.orientacao_estudos_metodologia import montar_frases_orientacao_estudos
from core.qualidade_metodologica import (
    corrigir_mojibake,
    extrair_conceito_central,
    limitar_texto_natural,
    naturalizar_texto_metodologico,
)


_seletor_tecnicas = SeletorTecnicas()
_extrator = ExtratorPDF()


def _normalizar_termos_internos(texto: str) -> str:
    texto = str(texto or "")
    correcoes = {
        "evidências": "evidencias",
        "socialização": "socializacao",
    }
    for origem, destino in correcoes.items():
        texto = texto.replace(origem, destino)
        texto = texto.replace(origem.capitalize(), destino[:1].upper() + destino[1:])
    return texto


class ValidadorQualidade:
    """Remove etapas vazias e formata corretamente os blocos de texto."""

    def refinar(self, metodologia: list[dict]) -> list[dict]:
        validada = []
        for etapa in metodologia:
            if etapa.get("texto") and len(etapa["texto"].strip()) > 10:
                texto = naturalizar_texto_metodologico(corrigir_mojibake(etapa["texto"].strip()))
                texto = _normalizar_termos_internos(texto)
                if not texto.endswith('.'):
                    texto += '.'
                etapa["texto"] = texto
                validada.append(etapa)
        return validada


def _etapas_por_perfil(perfil: str, tipo: str, contexto_geracao: dict | None = None) -> list[tuple[str, str]]:
    """Define as etapas metodológicas adequadas ao perfil e tipo de aula."""
    tipo_aula = contexto_geracao.get("tipo_aula", "simples") if contexto_geracao else "simples"

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"} and tipo_aula == "dupla":
        return [
            ("Para começar", "para_comecar"),
            ("Hora da leitura", "hora_leitura"),
            ("Foco no conteúdo", "foco"),
            ("Na prática", "pratica"),
            ("Socialização", "socializacao"),
            ("Encerramento", "encerramento"),
        ]


    if perfil == "ingles":
        if tipo == "leitura_em":
            return [
                ("Para começar", "para_comecar_virem_e_conversem"),
                ("Vocabulário", "vocabulario_pre_leitura"),
                ("Hora da leitura", "leitura_texto_principal"),
                ("Foco no conteúdo", "foco_conteudo_estrategia"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "questoes_vestibular"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "gramatica":
            return [
                ("Relembre", "relembre_ou_para_comecar"),
                ("Na prática — Vocabulário", "listening_ou_vocabulario"),
                ("Foco no conteúdo", "foco_conteudo_gramatica"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática — Exercícios", "exercicios_estruturados"),
                ("Produção oral", "producao_oral_duplas"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "listening":
            return [
                ("Para começar", "para_comecar_virem_e_conversem"),
                ("Vocabulário", "vocabulario_pre_escuta"),
                ("Na prática", "listening_atividade"),
                ("Foco no conteúdo", "foco_conteudo"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "pratica_adicional"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "producao_oral":
            return [
                ("Relembre", "relembre"),
                ("Vocabulário", "vocabulario_expressoes"),
                ("De olho no modelo", "modelo_dialogo"),
                ("Na prática", "pratica_em_duplas"),
                ("Produção própria", "producao_propria"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "leitura_literaria":
            return [
                ("Para começar", "para_comecar_virem_e_conversem"),
                ("Foco no conteúdo", "foco_conteudo_estrategia_literaria"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "atividades_leitura"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "musica":
            return [
                ("Relembre", "relembre_ou_para_comecar"),
                ("Na prática", "listening_musica"),
                ("De olho no modelo", "analise_letra"),
                ("Foco no conteúdo", "foco_conteudo_gramatica"),
                ("Pause e responda", "pause_e_responda"),
                ("Na prática", "exercicios_pratica"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        if tipo == "revisao":
            return [
                ("Relembre", "relembre_sintese"),
                ("Na prática", "atividades_revisao_multiplas"),
                ("Encerramento", "encerramento_com_suas_palavras")
            ]
        # vocabulario e fallback geral
        return [
            ("Para começar", "para_comecar"),
            ("Vocabulário", "vocabulario"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Encerramento", "encerramento")
        ]

    if perfil == "lingua_portuguesa_ef":
        if tipo == "autoavaliacao":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Na pratica", "pratica"),
                ("Socializacao", "socializacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "pratica_oral":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Planejamento da apresentacao", "planejamento_oral"),
                ("Na pratica", "pratica"),
                ("Socializacao", "socializacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "leitura_multimodal":
            return [
                ("Para comecar", "para_comecar"),
                ("Hora da leitura", "hora_leitura"),
                ("Foco no conteudo", "foco"),
                ("Na pratica", "pratica"),
                ("Correcao dialogada", "socializacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "resumo_retextualizacao":
            return [
                ("Para comecar", "para_comecar"),
                ("Hora da leitura", "hora_leitura"),
                ("Foco no conteudo", "foco"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Todo mundo escreve", "todo_mundo_escreve"),
                ("Na pratica", "pratica"),
                ("Revisao com colega", "revisao_colega"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "variacao_linguistica":
            return [
                ("Para comecar", "para_comecar"),
                ("Hora da leitura", "hora_leitura"),
                ("Foco no conteudo", "foco"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "argumentacao_debate":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco"),
                ("Pause e responda", "pause"),
                ("Hora da leitura", "hora_leitura"),
                ("Planejamento do debate", "planejamento_debate"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "texto_digital_blog":
            return [
                ("Relembre", "relembre"),
                ("Hora da leitura", "hora_leitura"),
                ("Foco no conteudo", "foco"),
                ("Todo mundo escreve", "todo_mundo_escreve"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo in {"analise_linguistica_ortografia", "gramatica_contextualizada"}:
            return [
                ("Relembre", "relembre"),
                ("Hora da leitura", "hora_leitura"),
                ("Foco no conteudo", "foco"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "leitura_jornalistica":
            return [
                ("Para comecar", "para_comecar"),
                ("Hora da leitura", "hora_leitura"),
                ("Foco no conteudo", "foco"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "producao_textual":
            return [
                ("Para comecar", "para_comecar"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Todo mundo escreve", "todo_mundo_escreve"),
                ("Na pratica", "pratica"),
                ("Revisao com colega", "revisao_colega"),
                ("Encerramento", "encerramento"),
            ]
        return [
            ("Para comecar", "para_comecar"),
            ("Hora da leitura", "hora_leitura"),
            ("Foco no conteudo", "foco"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "lingua_portuguesa_em":
        # Etapas várias por tipo de aula LP Ensino Médio
        if tipo == "autoavaliacao":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco"),
                ("Na prática", "pratica"),
                ("Socialização", "socializacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "pratica_oral":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco"),
                ("Planejamento da apresentação", "planejamento_oral"),
                ("Na prática", "pratica"),
                ("Socialização", "socializacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "pratica_oral":
            return [
                ("Relembre", "relembre"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo in {"literatura", "genero_textual", "producao_textual", "gramatica_integrada"}:
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        # Fallbacks antigos para compatibilidade
        if tipo == "gramatica_contextualizada":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco"),
                ("Pause e responda", "pause"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "producao_textual_antigo":
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco"),
                ("Na prática", "pratica"),
                ("Compartilhamento", "compartilhamento"),
                ("Encerramento", "encerramento"),
            ]
        return [
            ("Para começar", "para_comecar"),
            ("Foco no conteúdo", "foco"),
            ("Na prática", "pratica"),
            ("Encerramento", "encerramento"),
        ]


    if perfil in {"leitura_redacao"} and tipo == "producao":
        return [
            ("Para começar", "para_comecar"),
            ("Leitura e construção do conteúdo", "leitura"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Revisão e reescrita", "encerramento"),
        ]

    if perfil == "orientacao_estudos":
        return [
            ("Para comecar", "para_comecar"),
            ("Leitura e construcao do conteudo", "leitura"),
            ("Foco no conteudo", "foco"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "ciencias_ef":
        if tipo == "analise_dados":
            return [
                ("Para comecar", "para_comecar"),
                ("Analise de dados", "analise_dados"),
                ("Foco no conteudo", "foco"),
                ("Na pratica", "pratica"),
                ("Correcao dialogada", "correcao_dialogada"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "modelagem_cientifica":
            return [
                ("Relembre", "relembre"),
                ("Observacao inicial", "observacao_inicial"),
                ("Mao na massa", "mao_na_massa"),
                ("Socializacao", "socializacao"),
                ("Correcao dialogada", "correcao_dialogada"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "situacao_problema":
            return [
                ("Relembre", "relembre"),
                ("Situacao-problema", "situacao_problema"),
                ("Na pratica", "pratica"),
                ("Socializacao", "socializacao"),
                ("Correcao dialogada", "correcao_dialogada"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "pratica_experimental":
            return [
                ("Relembre", "relembre"),
                ("Para comecar", "para_comecar"),
                ("Mao na massa", "mao_na_massa"),
                ("Na pratica", "pratica"),
                ("Correcao dialogada", "correcao_dialogada"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "investigativa":
            return [
                ("Para comecar", "para_comecar"),
                ("Observacao inicial", "observacao_inicial"),
                ("Na pratica", "pratica"),
                ("Foco no conteudo", "foco"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "impacto_socioambiental":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco"),
                ("Analise de dados", "analise_dados"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "revisao_retomada":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Exercicio resolvido", "modelo"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "producao_projeto":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Na pratica", "producao"),
                ("Compartilhamento", "compartilhamento"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "leitura_analise":
            return [
                ("Para comecar", "para_comecar"),
                ("Hora da leitura", "leitura"),
                ("Foco no conteudo", "foco"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "estudo_caso":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco"),
                ("Estudo de caso", "estudo_caso"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        return [
            ("Para comecar", "para_comecar"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "biologia":
        if tipo == "etico_biotecnologico":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco_1"),
                ("Foco no conteudo", "foco_2"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "molecular_genetico":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco_1"),
                ("Foco no conteudo", "foco_2"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "debate_critico":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco_1"),
                ("Na pratica", "pratica"),
                ("Foco no conteudo", "foco_2"),
                ("Pause e responda", "pause"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "aplicacao_biotecnologica":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco_1"),
                ("Foco no conteudo", "foco_2"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "revisao_aprofundamento":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco_1"),
                ("Pause e responda", "pause"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "aula_desafio":
            return [
                ("Desafio da semana", "desafio"),
                ("Entendendo o problema", "entendendo_problema"),
                ("Solucao em acao", "solucao_acao"),
                ("Hora da verdade", "hora_verdade"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "aula_pratica":
            return [
                ("Relembre", "relembre"),
                ("Na pratica", "pratica"),
                ("Discussao dos resultados", "discussao_resultados"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "revisao_consolidacao":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteudo", "foco"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "impacto_socioambiental":
            return [
                ("Para comecar", "para_comecar"),
                ("Foco no conteudo", "foco"),
                ("De olho no modelo", "de_olho_modelo"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        return [
            ("Para comecar", "para_comecar"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "educacao_financeira":
        if tipo == "aula_pratica_continuidade":
            return [
                ("Para começar", "retomada_conceitual"),
                ("Foco no conteúdo", "contextualizacao_pratica"),
                ("Na prática", "atividade_central"),
                ("Encerramento", "encerramento_reflexivo"),
            ]
        etapas = [
            ("Para começar", "para_comecar"),
            ("Análise de caso", "analise_caso"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
        ]
        if tipo in {"credito_endividamento", "investimento_poupanca", "analise_percentuais_noticias"}:
            etapas.append(("Cálculos financeiros", "calculos"))
            etapas.append(("Na prática", "pratica"))
        elif tipo == "orcamento_planejamento":
            etapas.append(("Planejamento orçamentário", "planejamento"))
        elif tipo == "empreendedorismo":
            etapas.append(("Projeto empreendedor", "projeto"))
        else:
            etapas.append(("Na prática", "pratica"))
        etapas.append(("Encerramento", "encerramento"))
        return etapas

    if perfil == "projeto_de_vida":
        if tipo == "futureme":
            return [
                ("Para começar", "ponto_de_partida"),
                ("Foco no conteúdo", "construindo_o_conceito"),
                ("Na prática", "acesso_plataforma"),
                ("Compartilhamento", "compartilhamento"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "producao_coletiva":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco_no_tema"),
                ("Na prática", "producao_em_grupos"),
                ("Compartilhamento", "apresentacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "convivencia":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "foco_no_tema"),
                ("Na prática", "circulo_ou_votacao"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "consciencia_social":
            return [
                ("Para começar", "para_comecar"),
                ("Foco no conteúdo", "foco_no_tema"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if tipo == "encerramento":
            return [
                ("Relembre", "relembre"),
                ("Foco no conteúdo", "sintese_do_percurso"),
                ("Na prática", "producao_final"),
                ("Encerramento", "encerramento"),
            ]
        # autoconhecimento / default
        return [
            ("Para começar", "ponto_de_partida"),
            ("Foco no conteúdo", "construindo_o_conceito"),
            ("Na prática", "colocando_em_pratica"),
            ("Compartilhamento", "virem_e_conversem"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "historia":
        return [
            ("Para começar", "para_comecar"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    # Padrão geral
    return [
        ("Para começar", "para_comecar"),
        ("Leitura e construção do conteúdo", "leitura"),
        ("Foco no conteúdo", "foco"),
        ("Pause e responda", "pause"),
        ("Na prática", "pratica"),
        ("Encerramento", "encerramento"),
    ]


_PRIORIDADE_RECURSO = [
    "producao_textual",
    "calculo_resolucao",
    "analise_grafico",
    "analise_geografica",
    "analise_imagem",
    "experimentacao",
    "debate_oral",
    "leitura_texto",
]


def _recurso_principal(recursos_detectados: list[str] | None) -> str:
    recursos = [normalizar_texto(recurso) for recurso in list(recursos_detectados or [])]
    for prioridade in _PRIORIDADE_RECURSO:
        if prioridade in recursos:
            return prioridade
    return recursos[0] if recursos else ""


def _ajustar_por_recurso(base: dict[str, str], recurso_principal: str, tema: str, atividade_extraida: str) -> None:
    atividade = corrigir_mojibake(atividade_extraida or "")
    if recurso_principal == "analise_grafico":
        base["foco"] = (
            f"Conduzir a leitura de gráficos ou tabelas relacionados a {tema}, destacando título, legenda, eixos, categorias, variações e comparação de dados antes da interpretação."
        )
        base["pratica"] = (
            f"Orientar a análise dos dados em etapas, retomando o que a atividade pede e solicitando registros sobre padrões, comparações e conclusões. Atividade central do material: {atividade or 'interpretar informações numéricas e justificar respostas.'}"
        )
    elif recurso_principal == "analise_geografica":
        base["foco"] = (
            f"Explorar o mapa como linguagem principal da aula, destacando título, legenda, escala, localização e o fenômeno espacial relacionado a {tema}."
        )
        base["pratica"] = (
            f"Orientar leitura guiada do mapa e registro das observações no caderno, solicitando localização, comparação e explicação do fenômeno analisado. Atividade central do material: {atividade or 'interpretar informações do mapa com apoio do professor.'}"
        )
    elif recurso_principal == "analise_imagem":
        base["leitura"] = (
            "Explorar a imagem, charge, fotografia ou esquema do material com leitura mediada, destacando elementos visuais, pistas de sentido e relações com o tema da aula."
        )
        base["pratica"] = (
            f"Orientar a observação guiada da imagem e a construção de respostas com base em evidências visuais, articulando descrição, interpretação e justificativa. Atividade central do material: {atividade or 'analisar a imagem e registrar as conclusões mais importantes.'}"
        )
    elif recurso_principal == "producao_textual":
        base["foco"] = (
            f"Retomar as características do gênero ou proposta de escrita relacionada a {tema}, destacando finalidade, interlocutor, organização das ideias e critérios de qualidade."
        )
        base["pratica"] = (
            f"Organizar a atividade em planejamento, escrita, revisão e reescrita, com mediação do professor durante o processo. Atividade central do material: {atividade or 'produzir um texto coerente com o gênero e revisar a versão inicial.'}"
        )
    elif recurso_principal == "calculo_resolucao":
        base["foco"] = (
            f"Explicar o procedimento central de {tema} com exemplo resolvido passo a passo, destacando leitura dos dados, escolha da operação e conferência do resultado."
        )
        base["pratica"] = (
            f"Orientar a resolução das questões em etapas, solicitando registro do raciocínio e comparação de estratégias. Atividade central do material: {atividade or 'resolver os cálculos e justificar o procedimento utilizado.'}"
        )
    elif recurso_principal == "experimentacao":
        base["foco"] = (
            f"Apresentar o fenômeno relacionado a {tema} por meio de observação orientada, hipótese inicial e organização das etapas do experimento ou demonstração."
        )
        base["pratica"] = (
            f"Conduzir a atividade experimental com registro de observações, comparação de resultados e conclusão baseada em evidências. Atividade central do material: {atividade or 'observar, registrar e concluir a partir da prática proposta.'}"
        )
def _tema_base_ciencias(tema: str) -> str:
    tema_limpo = corrigir_mojibake(str(tema or "")).strip(" .:-\"")
    return extrair_conceito_central(tema_limpo) or tema_limpo or "o tema da aula"


def _texto_extraido_ruidoso_ciencias(texto: str) -> bool:
    texto_limpo = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip())
    base = normalizar_texto(texto_limpo)
    if not texto_limpo:
        return True
    if len(texto_limpo) > 180:
        return True
    if texto_limpo.count("?") >= 2:
        return True
    if any(
        marcador in base
        for marcador in [
            "referencias",
            "tempo",
            "expectativas de resposta",
            "dinamica de conducao",
            "correcao",
            "responda a questao",
            "responda a pergunta",
            "atividade 2",
            "atividade 3",
            "link para video",
            "aplicativo",
            "simulador",
            "desenho explicacao",
        ]
    ):
        return True
    if re.search(r"(?:^|[\s(])[123]\)", texto_limpo):
        return True
    if any(simbolo in texto_limpo for simbolo in ["●", "•"]):
        return True
    return False


def _conceito_ciencias_seguro(conceito: str, tema: str) -> str:
    tema_base = _tema_base_ciencias(tema)
    conceito_limpo = corrigir_mojibake(str(conceito or "")).strip(" .:-\"")
    conceito_norm = normalizar_texto(conceito_limpo)
    if conceito_norm in {"", "ciencias", "ciencia", "geral"}:
        return tema_base
    if conceito_norm == normalizar_texto(tema_base):
        return tema_base
    if _texto_extraido_ruidoso_ciencias(conceito_limpo):
        return tema_base
    return limitar_texto_natural(conceito_limpo, limite=110).strip(" .:-\"")


def _atividade_ciencias_segura(atividade_extraida: str, tema: str) -> str:
    tema_base = _tema_base_ciencias(tema)
    fallback = f'atividades propostas no material, articuladas ao tema "{tema_base}"'
    atividade_limpa = corrigir_mojibake(str(atividade_extraida or "")).strip()
    atividade_limpa = re.sub(
        r"^(?:atividade\s*\d+|correcao|hora da leitura|na pratica|situacao-problema)\s*[:\-]?\s*",
        "",
        atividade_limpa,
        flags=re.I,
    )
    atividade_limpa = re.sub(
        r"\b(?:responda a questao a seguir|responda a pergunta a seguir)\b[:\-]?\s*",
        "",
        atividade_limpa,
        flags=re.I,
    )
    atividade_limpa = re.sub(r"\s{2,}", " ", atividade_limpa).strip(" .:-")
    if _texto_extraido_ruidoso_ciencias(atividade_limpa):
        return fallback
    return limitar_texto_natural(atividade_limpa, limite=150).strip(" .:-")


def _conceito_projeto_vida(conceito: str, tema: str, texto_base: str, atividade_extraida: str) -> str:
    conceito_limpo = corrigir_mojibake(str(conceito or "")).strip(" .:-")
    conceito_norm = normalizar_texto(conceito_limpo)
    tema_norm = normalizar_texto(tema)
    base_contexto = normalizar_texto(" ".join([atividade_extraida or "", texto_base or "", tema or ""]))

    generico = (
        not conceito_norm
        or conceito_norm == tema_norm
        or any(
            marcador in conceito_norm
            for marcador in [
                "questao essencial",
                "habilidade",
                "competencia",
                "competencias",
                "tema da aula",
                "conteudo da aula",
            ]
        )
        or (conceito_norm.split()[-1:] and conceito_norm.split()[-1] in {"a", "as", "o", "os", "de", "da", "do", "e", "em", "com", "para", "por"})
    )
    if not generico:
        return conceito_limpo

    if any(termo in base_contexto for termo in ["autoconhecimento", "quem sou", "identidade"]):
        return "autoconhecimento e cuidado consigo"
    if any(termo in base_contexto for termo in ["opiniao", "opinioes", "ponto de vista", "pontos de vista", "conviv", "respeito"]):
        return "pontos de vista, respeito e convivencia"
    if any(termo in base_contexto for termo in ["print", "post", "postar", "digital", "rede", "online", "internet"]):
        return "exposicao e responsabilidade no ambiente digital"
    return "escolhas, convivencia e responsabilidade"


def _metodologia_matematica(texto_base: str, tema: str, tipo: str, turma: str = "", tecnicas: dict = None) -> list[dict]:
    """Gerador especializado de etapas para o perfil Matemática.

    Retorna lista de dicts {titulo, text} diferenciada por tipo de aula:
    'conceito_novo', 'verificacao', 'khan', 'modelagem', 'grafico',
    'resolucao_problemas', 'tecnologia'.

    Chame este gerador a partir de _frases_por_contexto quando perfil=='matematica'.
    A lista retornada sobrepõe o dicionário base de frases usado pelo motor geral.
    """
    # 0. Normalização e Detecção dos perfis matemáticos (regras 1 a 12)
    tema_lower = (tema or "").lower()
    texto_lower = (texto_base or "").lower()
    combinado = tema_lower + " " + texto_lower

    # Regra 01: Estatística ou Porcentagem
    is_stat = any(p in combinado for p in ["estatistica", "porcentagem", "porcent", "media", "ponderada", "amplitude", "variancia", "desvio"])
    # Regra 02: Álgebra ou Equações
    is_algebra = any(p in combinado for p in ["algebra", "equacao", "equacoes", "sistema", "incognita", "variavel", "adicao", "substituicao"])
    # Regra 03: Geometria ou Medidas
    is_geometry = any(p in combinado for p in ["geometria", "medida", "volume", "prisma", "cilindro", "triangulo", "pitagoras", "retangulo", "aresta", "face", "raio", "circulo", "area", "figuras planas"])
    # Regra 04: Funções e Gráficos
    is_functions = any(p in combinado for p in ["funcao", "funcoes", "grafico", "parabola", "concavidade", "vertice", "raizes", "exponencial", "logarit"])
    # Regra 05: Probabilidade ou Análise Combinatória
    is_prob = any(
        p in combinado
        for p in [
            "probabilidade", "combinatoria", "arranjo", "combinacao", "permutacao",
            "fatorial", "contagem", "multiplicativo", "possibilidades",
            "arvore de possibilidades", "principio aditivo", "principio multiplicativo",
            "espaco amostral", "evento favoravel", "diagrama de arvore",
            "principios de contagem",
        ]
    )
    # Regra 06: Khan Academy
    is_khan = tipo == "khan" or "khan" in combinado
    # Regra 07: Novo / Regra 08: Revisão
    is_new_topic = tipo == "conceito_novo" or any(p in combinado for p in ["introducao", "conceito de", "definicao", "propriedade", "parte 1"])
    is_revision = tipo in {"revisao", "verificacao"} or any(
        p in combinado for p in ["revisao", "retomada", "consolidar", "trilha", "parte 2", "parte 3", "parte 4"]
    )

    # Regra 11: Ensino Fundamental / Regra 12: Ensino Médio
    turma_lower = (turma or "").lower()
    is_ef = any(f"{i}" in turma_lower for i in [6, 7, 8, 9]) or "fundamental" in turma_lower
    is_em = any(f"{i}" in turma_lower for i in [1, 2, 3]) or "medio" in turma_lower or "médio" in turma_lower or "em" in turma_lower
    if not is_ef and not is_em:
        is_em = True # default to EM

    # Recupera técnicas lemov ou usa fallback
    tecnicas = tecnicas or {}
    t_disc = tecnicas.get("abertura", "Virem e conversem")
    t_reg = tecnicas.get("registro", "Todo mundo escreve")
    t_sint = tecnicas.get("sintese", "Com suas palavras")
    t_verif = tecnicas.get("verificacao", "Pause e responda")

    # Constantes das etapas
    # Para começar
    if is_stat:
        para_comecar_txt = f"Iniciar a aula com a leitura estruturada de um gráfico ou tabela real sobre {tema}, orientando os estudantes a identificarem de forma clara e explícita o título, os eixos, a fonte dos dados e o período de coleta antes de realizar qualquer cálculo."
    elif is_algebra:
        para_comecar_txt = f"Iniciar a aula apresentando uma situação-problema sobre {tema} narrada inteiramente em linguagem cotidiana e sem a utilização de símbolos matemáticos, estimulando a intuição inicial dos estudantes."
    else:
        para_comecar_txt = f"Iniciar a aula apresentando uma situação contextualizada ou pergunta disparadora sobre {tema} para aproximar o conceito da realidade da turma."

    if is_new_topic:
        para_comecar_txt += " Propor uma pergunta de sondagem de conhecimentos prévios para levantar as hipóteses iniciais dos estudantes."
    elif is_revision:
        para_comecar_txt += f" Retomar brevemente o conceito central da aula anterior solicitando que os estudantes o expliquem por meio da técnica {t_sint}."

    if is_algebra:
        para_comecar_txt += f" Solicitar um registro inicial individual por meio da técnica {t_reg}, para que cada estudante anote a hipótese de resolução antes da socialização."

    para_comecar_txt += f" Utilizar a técnica {t_disc} para socializar as ideias iniciais antes da formalização."

    if is_ef:
        para_comecar_txt += " Adote uma linguagem simples e situações familiares do universo juvenil."
    elif is_em:
        para_comecar_txt += " Conectar brevemente o tema a conceitos do Ensino Fundamental que servem de base para a aula."

    # Foco no conteúdo
    if is_khan:
        foco_txt = f"Contextualizar brevemente o conteúdo de {tema} na lousa por 5 a 7 minutos com um exemplo rápido, apresentando a trilha da aula. Em seguida, orientar os estudantes sobre o login e a navegação na plataforma Khan Academy."
    elif is_algebra:
        foco_txt = f"Desenvolver o conceito de {tema} no quadro de forma progressiva e dialogada, modelando explicitamente o processo de tradução da linguagem natural para a linguagem algébrica, convertendo cada sentença do problema em expressões matemáticas equivalentes."
    else:
        foco_txt = f"Sistematizar o conceito de {tema} de forma progressiva, conectando a explicação e propriedades aos exemplos práticos."

    if is_functions:
        foco_txt += " Conduzir de forma organizada a construção de uma tabela de valores numéricos na lousa antes de traçar o esboço do gráfico correspondente no plano cartesiano."

    # Regra 09: Múltiplas representações
    if is_functions or is_stat or any(p in combinado for p in ["representacao", "representacoes", "tabela", "grafico"]):
        foco_txt += " Demonstrar de forma explícita a transição entre múltiplas representações (tabular, algébrica e gráfica), verbalizando o que muda e o que permanece igual em cada caso."

    if is_em:
        foco_txt += f" Apresentar a formalização matemática precisa de {tema}, contendo sua definição correta, notações formais e propriedades fundamentais."

    foco_txt += f" Conduzir a explanação utilizando a técnica Um passo de cada vez para estruturar o raciocínio em etapas claras."

    # De olho no modelo
    if is_geometry:
        modelo_txt = f"Apresentar um problema-modelo sobre {tema} resolvido de forma detalhada na lousa. Desenhar de forma cuidadosa e organizada a figura geométrica correspondente antes de iniciar qualquer cálculo, identificando e nomeando elementos como base, altura, raio, arestas ou ângulos retos."
    elif is_prob:
        modelo_txt = f"Apresentar um exemplo-modelo comentado na lousa sobre {tema}, construindo de forma visual um diagrama de árvore ou uma tabela de possibilidades para tornar o processo de contagem e a organização do espaço amostral visualmente explícitos antes de aplicar qualquer fórmula."
    else:
        modelo_txt = f"Apresentar um problema-modelo sobre {tema} resolvido de forma detalhada na lousa como referência orientadora."

    if is_new_topic:
        modelo_txt += " Apresentar o exemplo mais simples possível do tópico, sem variações complexas ou casos especiais, para fixar as bases conceituais."
    
    if is_ef:
        modelo_txt += " Demonstrar as operações e os cálculos passo a passo de forma exclusivamente manual, reforçando a importância de não usar a calculadora nesta etapa."

    modelo_txt += " Utilizar a técnica De olho no modelo para explicitar o raciocínio clínico completo (leitura, dados, estratégia, execução e verificação)."

    # Pause e responda
    pause_txt = f"Realizar uma parada estratégica curta propondo uma pergunta objetiva de checagem formativa sobre {tema} para verificar a compreensão em tempo real."
    # Regra 10: Retomada se > 40% de insegurança
    pause_txt += " Caso mais de 40% da turma demonstre insegurança ou dúvidas, pausar o avanço e propor a retomada imediata com um segundo exemplo focado no ponto de maior dificuldade."

    # Na prática
    if is_khan:
        pratica_txt = f"Orientar os estudantes a realizarem as atividades de {tema} na plataforma Khan Academy. O professor deve realizar circulação ativa de forma sistemática pela sala, observando as telas, mapeando erros comuns e apoiando prioritariamente os estudantes que estão travados."
    else:
        pratica_txt = f"Propor que os estudantes resolvam os exercícios de {tema} no caderno, aplicando o procedimento estudado."

    if is_functions:
        pratica_txt += " Garantir que a atividade prática inclua pelo menos uma questão de interpretação crítica de gráfico além dos cálculos numéricos."

    if is_revision:
        pratica_txt += " Organizar a prática de forma progressiva, partindo dos exercícios mais simples de fixação até desafios de maior complexidade."

    if is_ef:
        pratica_txt += " Orientar a resolução manual e minuciosa dos cálculos passo a passo, evitando o uso de calculadora."

    pratica_txt += f" Utilizar a técnica {t_reg} para que os estudantes registrem individualmente o raciocínio antes de qualquer comparação."

    # Encerramento
    if is_khan:
        encerramento_txt = f"Finalizar a aula projetando os relatórios de progresso da plataforma Khan Academy, destacando os pontos de avanço da turma e identificando as principais dificuldades para orientar os próximos planejamentos."
    else:
        encerramento_txt = f"Conduzir a síntese coletiva dos aprendizados sobre {tema}, organizando o resumo das ideias no quadro."

    encerramento_txt += f" Aplicar a técnica {t_sint}, solicitando que os estudantes expliquem com suas palavras o conceito ou procedimento estudado na aula antes do fechamento final."

    # 1. Ajustes por tipos de aula
    if tipo == "khan":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "verificacao":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "modelagem":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "grafico":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "resolucao_problemas":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Pause e responda", "texto": pause_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    if tipo == "tecnologia" or tipo == "tecnologia_matematica":
        return [
            {"titulo": "Para começar", "texto": para_comecar_txt},
            {"titulo": "Foco no conteúdo", "texto": foco_txt},
            {"titulo": "De olho no modelo", "texto": modelo_txt},
            {"titulo": "Na prática", "texto": pratica_txt},
            {"titulo": "Encerramento", "texto": encerramento_txt},
        ]

    # default: conceito_novo / matematica_padrao
    return [
        {"titulo": "Para começar", "texto": para_comecar_txt},
        {"titulo": "Foco no conteúdo", "texto": foco_txt},
        {"titulo": "De olho no modelo", "texto": modelo_txt},
        {"titulo": "Pause e responda", "texto": pause_txt},
        {"titulo": "Na prática", "texto": pratica_txt},
        {"titulo": "Encerramento", "texto": encerramento_txt},
    ]


# Repertórios controlados de variação pedagógica
REPERTORIO_RETOMADA = {
    "LEITURA INVESTIGATIVA": "recuperar a pergunta ou problema central da aula anterior para orientar nossa analise de hoje",
    "COMPARAÇÃO E DIÁLOGO": "reler a sintese anterior e revisar palavras-chave coletivamente para situar a turma",
    "ANÁLISE MODELADA": "comparar duas respostas ou registros anteriores dos estudantes para tirar duvidas e mapear progressos",
    "ESCRITA E AUTORIA": "retomar brevemente um trecho estudado ou reconstruir uma ideia em esquema no quadro"
}

REPERTORIO_LEITURA = {
    "LEITURA INVESTIGATIVA": "leitura silenciosa com marcacao individual de termos-chave e evidencias textuais",
    "COMPARAÇÃO E DIÁLOGO": "leitura comparativa e atenta entre dois trechos, imagens ou elementos linguisticos do material",
    "ANÁLISE MODELADA": "leitura em partes com pausas para perguntas de compreensao orientadas pelo professor",
    "ESCRITA E AUTORIA": "leitura expressiva e compartilhada do texto de referencia, observando as escolhas do autor"
}

REPERTORIO_REGISTRO = {
    "LEITURA INVESTIGATIVA": "registro de anotacao de evidencias e elaboracao de resposta fundamentada no caderno",
    "COMPARAÇÃO E DIÁLOGO": "construcao de um quadro comparativo ou esquema destacando semelhancas e diferencas encontradas",
    "ANÁLISE MODELADA": "sintese em duas frases ou resumo estruturado das ideias principais do texto",
    "ESCRITA E AUTORIA": "elaboracao de um pequeno comentario interpretativo ou planejamento do rascunho de escrita"
}

REPERTORIO_ENCERRAMENTO = {
    "LEITURA INVESTIGATIVA": "anotacao de uma evidencia textual conclusiva no caderno",
    "COMPARAÇÃO E DIÁLOGO": "revisao colaborativa em dupla e explicacao do aprendizado com as proprias palavras",
    "ANÁLISE MODELADA": "registro de uma pergunta de continuidade para orientar o proximo estudo",
    "ESCRITA E AUTORIA": "preenchimento de um bilhete de saida com resposta sintetica a questao central da aula"
}

def _metodologia_lingua_portuguesa(
    texto_base: str,
    tema: str,
    tipo: str,
    perfil_metodologico: str = None,
    tipo_aula: str = "simples"
) -> dict[str, str] | None:
    """Gerador especializado de frases para o perfil Lingua Portuguesa com variacao controlada."""
    # Obter perfil de variacao pedagogica
    if not perfil_metodologico:
        perfil_metodologico = "LEITURA INVESTIGATIVA"

    retomada = REPERTORIO_RETOMADA.get(perfil_metodologico, REPERTORIO_RETOMADA["LEITURA INVESTIGATIVA"])
    leitura = REPERTORIO_LEITURA.get(perfil_metodologico, REPERTORIO_LEITURA["LEITURA INVESTIGATIVA"])
    registro = REPERTORIO_REGISTRO.get(perfil_metodologico, REPERTORIO_REGISTRO["LEITURA INVESTIGATIVA"])
    encerramento = REPERTORIO_ENCERRAMENTO.get(perfil_metodologico, REPERTORIO_ENCERRAMENTO["LEITURA INVESTIGATIVA"])

    # Se for aula dupla, retornamos a estrutura de 6 etapas
    if tipo_aula == "dupla":
        if tipo == "autoavaliacao":
            return {
                "para_comecar": f"Retomar o percurso de estudo de {tema} e {retomada} para ativar os conhecimentos.",
                "hora_leitura": f"Conduzir {leitura} dos criterios de autoavaliacao estabelecidos no material.",
                "foco": f"Apresentar a definicao e o proposito de cada criterio de avaliacao sobre {tema}.",
                "pratica": f"Orientar o preenchimento da autoavaliacao ou rubrica de forma individual com {registro}.",
                "socializacao": "Promover devolutiva e socializacao breve das percepcoes da turma, trocando estrategias de estudo.",
                "encerramento": f"Encerrar sistematizando metas coletivas e realizando {encerramento}."
            }
        if tipo == "literatura":
            return {
                "para_comecar": f"Apresentar imagens, contexto historico ou perguntas sobre {tema} e {retomada} para aquecimento.",
                "hora_leitura": f"Conduzir {leitura} de trechos literarios selecionados para analise critica.",
                "foco": f"Apresentar a estetica, autores e marcas literarias de {tema} integradas ao contexto social.",
                "pratica": f"Orientar exercicio aplicado de analise de recursos expressivos com {registro}.",
                "socializacao": "Promover socializacao em duplas comparando percepcoes e efeitos de sentido identificados.",
                "encerramento": f"Finalizar consolidando a sintese dos aprendizados esteticos com {encerramento}."
            }
        if tipo == "genero_textual":
            return {
                "para_comecar": f"Iniciar conectando o genero de {tema} ao cotidiano e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de um texto modelo do genero para identificar sua estrutura.",
                "foco": f"Apresentar a definicao, marcas linguisticas, publico-alvo e circulacao social do genero de {tema}.",
                "pratica": f"Propor exercicios praticos de interpretacao e analise linguistica com {registro}.",
                "socializacao": "Organizar socializacao das respostas em pequenos grupos para discussao das marcas do genero.",
                "encerramento": f"Finalizar sistematizando a funcao social do genero com {encerramento}."
            }
        if tipo == "producao_textual":
            return {
                "para_comecar": f"Apresentar a proposta de escrita sobre {tema} e realizar {retomada} dos objetivos.",
                "hora_leitura": f"Conduzir {leitura} das referencias de escrita e instrucoes de producao.",
                "foco": f"Apresentar os criterios de qualidade e roteiro de planejamento estrutural do texto de {tema}.",
                "pratica": f"Orientar as etapas de planejamento e escrita do rascunho autoral com {registro}.",
                "socializacao": "Organizar revisao colaborativa entre pares para troca de sugestoes de aprimoramento.",
                "encerramento": f"Finalizar estimulando a reflexao sobre o processo de reescrita e aplicar {encerramento}."
            }
        if tipo == "pratica_oral":
            return {
                "para_comecar": f"Retomar a finalidade da pratica oral de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de roteiros, exemplos de apresentacao ou guias de escuta ativa.",
                "foco": f"Sistematizar os recursos de linguagem oral de {tema}, como entonacao, postura e clareza.",
                "pratica": f"Orientar a preparacao e o ensaio ou apresentacao dos estudantes com {registro}.",
                "socializacao": "Promover apresentacao e socializacao das producoes orais com devolutiva respeitosa da turma.",
                "encerramento": f"Encerrar avaliando como a oralidade colaborou para expressar o tema e aplicar {encerramento}."
            }
        if tipo == "gramatica_integrada":
            return {
                "para_comecar": f"Apresentar pergunta motivadora ou trecho curto sobre o fenomeno de {tema} e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} do texto-base localizando o fenomeno gramatical em foco.",
                "foco": f"Sistematizar o conteudo gramatical de {tema} conectando a regra aos efeitos de sentido.",
                "pratica": f"Propor exercicios aplicados de identificacao e escrita com {registro}.",
                "socializacao": "Realizar correcao dialogada e compartilhamento de duvidas comuns sobre {tema}.",
                "encerramento": f"Finalizar sintetizando a importancia da convencao estudada e realizar {encerramento}."
            }
        if tipo == "leitura_multimodal":
            return {
                "para_comecar": f"Iniciar analisando cartaz, imagem ou infografico sobre {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} do texto multimodal articulando os diferentes modos de linguagem.",
                "foco": f"Sistematizar como recursos verbais e visuais constroem sentido no material sobre {tema}.",
                "pratica": f"Propor atividade aplicada de analise de elementos visuais com {registro}.",
                "socializacao": "Promover correcao dialogada comparando as diferentes leituras e hipoteses da turma.",
                "encerramento": f"Finalizar destacando a leitura critica do texto multimodal e aplicar {encerramento}."
            }
        if tipo == "resumo_retextualizacao":
            return {
                "para_comecar": f"Apresentar esquema, cartaz ou infografico de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} do texto-base destacando topicos, palavras-chave e dados centrais.",
                "foco": f"Explicar como transformar informacoes do material em texto coerente e autoral sobre {tema}.",
                "pratica": f"Orientar a producao de resumo ou retextualizacao no caderno com {registro}.",
                "socializacao": "Organizar leitura cruzada entre duplas para verificacao de coesao e fidelidade ao original.",
                "encerramento": f"Finalizar consolidando os criterios de resumo e realizar {encerramento}."
            }
        if tipo == "variacao_linguistica":
            return {
                "para_comecar": f"Iniciar apresentando situacao real de uso da lingua sobre {tema} e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} destacando exemplos de variacao regional, social ou historica.",
                "foco": f"Sistematizar o conceito de variacao linguistica em {tema} contra o preconceito linguistico.",
                "pratica": f"Propor atividade de classificacao, analise e {registro} no caderno.",
                "socializacao": "Promover discussao dialogada sobre a adequacao da fala aos diferentes contextos de uso.",
                "encerramento": f"Finalizar reforcando que adequacao e diferente de erro e realizar {encerramento}."
            }
        if tipo == "argumentacao_debate":
            return {
                "para_comecar": f"Apresentar tema polemico sobre {tema} e realizar {retomada} para aquecimento.",
                "hora_leitura": f"Conduzir {leitura} de artigo de opiniao ou editorial localizando a tese e argumentos.",
                "foco": "Explicar a estrutura da argumentacao (tese, argumentos, contra-argumentos e evidencias).",
                "pratica": f"Orientar a definicao e o registro de posicionamentos fundamentados com {registro}.",
                "socializacao": "Organizar debate regrado ou roda de conversa para socializacao dos argumentos da turma.",
                "encerramento": f"Finalizar sintetizando a importancia de argumentar com respeito e aplicar {encerramento}."
            }
        if tipo == "texto_digital_blog":
            return {
                "para_comecar": f"Retomar a leitura anterior e os registros sobre {tema} fazendo {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de post de blog ou postagem analisando o tom do texto e o leitor.",
                "foco": f"Sistematizar a organizacao e a linguagem do texto digital sobre {tema}.",
                "pratica": f"Orientar a escrita de um comentario ou resposta argumentativa com {registro}.",
                "socializacao": "Promover compartilhamento dos comentarios e devolutiva coletiva sobre clareza e respeito.",
                "encerramento": f"Finalizar discutindo a leitura critica no meio digital e aplicar {encerramento}."
            }
        if tipo == "analise_linguistica_ortografia":
            return {
                "para_comecar": f"Retomar exemplos linguisticos do texto estudado em {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} focalizando palavras ou marcas especificas a serem analisadas.",
                "foco": f"Sistematizar a regra ortografica ou recurso linguistico em {tema} e seu efeito de sentido.",
                "pratica": f"Orientar atividade aplicada de analise de palavras e revisao escrita com {registro}.",
                "socializacao": "Realizar correcao comentada no quadro tirando duvidas recorrentes.",
                "encerramento": f"Finalizar sintetizando como o estudo da escrita amplia a expressividade com {encerramento}."
            }
        # Fallback de dupla
        return {
            "para_comecar": f"Iniciar a aula conectando {tema} aos conhecimentos previos e realizar {retomada}.",
            "hora_leitura": f"Conduzir {leitura} de trechos selecionados do material de {tema}.",
            "foco": f"Sistematizar os principais conceitos de {tema} com base em exemplos contextualizados.",
            "pratica": f"Orientar a resolucao das questoes propostas com {registro} no caderno.",
            "socializacao": "Promover correcao dialogada e partilha de duvidas.",
            "encerramento": f"Finalizar sintetizando as aprendizagens centrais e aplicar {encerramento}."
        }
    else:
        # AULA SIMPLES (Garante as chaves específicas que o motor de etapas necessita)
        if tipo == "autoavaliacao":
            return {
                "para_comecar": f"Retomar com a turma o percurso de {tema} e {retomada}.",
                "foco": f"Apresentar os criterios de autoavaliacao estabelecidos para {tema}.",
                "pratica": f"Orientar a autoavaliacao de forma individual com {registro}.",
                "socializacao": "Promover partilha das impressoes e autoavaliacoes em duplas.",
                "encerramento": f"Finalizar discutindo as metas individuais de avanco e aplicar {encerramento}."
            }
        if tipo == "literatura":
            return {
                "para_comecar": f"Apresentar imagens ou contexto do autor de {tema} e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} dos trechos literarios ou fragmentos selecionados.",
                "foco": f"Explorar a estetica, marcas literarias e construcao de sentidos em {tema}.",
                "pratica": f"Orientar exercicio de analise critica do texto com {registro}.",
                "encerramento": f"Finalizar com reflexao sobre o tema estetico e aplicar {encerramento}."
            }
        if tipo == "genero_textual":
            return {
                "para_comecar": f"Iniciar conectando o genero de {tema} ao cotidiano e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de um texto modelo representativo do genero.",
                "foco": f"Apresentar definicao, suporte, publico-alvo e marcas do genero de {tema}.",
                "pratica": f"Propor exercicios praticos de interpretacao do genero com {registro}.",
                "encerramento": f"Finalizar sintetizando a funcao social do genero e aplicar {encerramento}."
            }
        if tipo == "producao_textual":
            return {
                "para_comecar": f"Apresentar a proposta de escrita sobre {tema} e {retomada} dos objetivos.",
                "foco": f"Apresentar os criterios de qualidade e roteiro de planejamento para {tema}.",
                "pratica": f"Conduzir {leitura} e orientar planejamento e rascunho com {registro}.",
                "encerramento": f"Finalizar refletindo sobre a escrita e revisao, aplicando {encerramento}."
            }
        if tipo == "pratica_oral":
            return {
                "relembre": f"Retomar a finalidade da atividade oral sobre {tema} e {retomada}.",
                "foco": f"Sistematizar resources da linguagem oral de {tema}, como entonacao e clareza.",
                "planejamento_oral": f"Orientar a organizacao do roteiro ou dos topicos de fala sobre {tema}.",
                "pratica": f"Conduzir a preparacao e a apresentacao oral com base em {leitura} e {registro}.",
                "socializacao": "Promover devolutiva coletiva valorizando clareza e respeito.",
                "encerramento": f"Finalizar sintetizando as percepcoes orais coletivas e aplicando {encerramento}."
            }
        if tipo == "gramatica_integrada":
            return {
                "para_comecar": f"Apresentar pergunta motivadora ou trecho curto sobre {tema} e realizar {retomada}.",
                "foco": f"Sistematizar o conteudo gramatical de {tema} relacionando a regra ao texto.",
                "pratica": f"Conduzir {leitura} e propor exercicios praticos com {registro}.",
                "encerramento": f"Finalizar consolidando o uso correto da convencao estudada com {encerramento}."
            }
        if tipo == "leitura_multimodal":
            return {
                "para_comecar": f"Iniciar analisando imagem, cartaz ou infografico sobre {tema} e realizar {retomada}.",
                "foco": f"Sistematizar como recursos verbais e visuais constroem sentido em {tema}.",
                "pratica": f"Conduzir {leitura} orientada do texto multimodal seguida de {registro}.",
                "socializacao": "Promover compartilhamento de leituras e visões sobre o texto multimodal.",
                "encerramento": f"Finalizar destacando a leitura critica do texto e aplicar {encerramento}."
            }
        if tipo == "resumo_retextualizacao":
            return {
                "para_comecar": f"Apresentar esquema, cartaz ou infografico de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} guiada e orientar a producao do resumo com {registro}.",
                "foco": f"Explicar a transformacao de dados do material em texto coerente sobre {tema}.",
                "de_olho_modelo": f"Apresentar exemplo estruturado de resumo para orientar a producao.",
                "todo_mundo_escreve": f"Solicitar escrita de topicos-chave para estruturacao do texto.",
                "pratica": f"Propor exercicios praticos de sintese baseados em {leitura}.",
                "revisao_colega": f"Promover a troca de resumos para revisao gramatical e textual simples.",
                "encerramento": f"Finalizar consolidando os criterios de resumo e realizar {encerramento}."
            }
        if tipo == "variacao_linguistica":
            return {
                "para_comecar": f"Iniciar apresentando situacao real de uso da lingua de {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} destacando exemplos de variacao regional, social ou historica.",
                "foco": f"Sistematizar conceito de variacao em {tema} contra preconceitos.",
                "pause": f"Realizar pausa formativa para classificar casos de adequacao contextual.",
                "pratica": f"Propor atividade de classificacao, analise e {registro} no caderno.",
                "encerramento": f"Finalizar reforcando a adequacao ao contexto e aplicar {encerramento}."
            }
        if tipo == "argumentacao_debate":
            return {
                "para_comecar": f"Apresentar tema polemico sobre {tema} e realizar {retomada}.",
                "foco": f"Explicar a estrutura da argumentacao (tese, argumentos e evidencias) em {tema}.",
                "pause": f"Realizar checagem objetiva dos tipos de argumentos identificados.",
                "hora_leitura": f"Conduzir {leitura} do texto argumentativo ou de opiniao estudado.",
                "planejamento_debate": f"Organizar roteiro simples de argumentos e contra-argumentos.",
                "pratica": f"Orientar o registro de posicionamento com {registro} e discussao.",
                "encerramento": f"Finalizar incentivando a argumentacao respeitosa e aplicar {encerramento}."
            }
        if tipo == "texto_digital_blog":
            return {
                "para_comecar": f"Retomar a leitura anterior e os registros sobre {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de post de blog analisando a linguagem e interlocutores.",
                "foco": f"Sistematizar a organizacao e linguagem do texto digital de {tema}.",
                "todo_mundo_escreve": f"Orientar elaboracao de comentario curto ou resposta argumentativa.",
                "pratica": f"Orientar escrita do comentario final no caderno com {registro}.",
                "encerramento": f"Finalizar com discussao critica sobre leitura digital e aplicar {encerramento}."
            }
        if tipo == "analise_linguistica_ortografia":
            return {
                "para_comecar": f"Retomar marcas ou palavras do texto estudado em {tema} e realizar {retomada}.",
                "hora_leitura": f"Conduzir {leitura} focada nas palavras a serem analisadas.",
                "foco": f"Sistematizar recurso linguistico ou ortografico de {tema} e seus efeitos.",
                "pratica": f"Conduzir {leitura} e propor exercicio de analise ortografica com {registro}.",
                "socializacao": f"Realizar correcao dialogada comparando registros no quadro.",
                "encerramento": f"Finalizar sintetizando o estudo contextualizado com {encerramento}."
            }

        # Fallbacks antigos para compatibilidade
        if tipo == "gramatica_contextualizada":
            return {
                "relembre": f"Retomar conhecimentos sobre o fenomeno gramatical e realizar {retomada}.",
                "foco": f"Explicar a norma-padrao ou variacao linguistica em {tema} conectando regra e sentido.",
                "pause": f"Realizar pausas para analise de trechos especificos do material.",
                "pratica": f"Orientar aplicacao dos conceitos com {registro} no caderno.",
                "encerramento": f"Sintetizar regra ou norma estudada em {tema} e aplicar {encerramento}."
            }
        if tipo == "leitura_jornalistica":
            return {
                "para_comecar": f"Mobilizar conhecimentos sobre {tema} a partir de manchetes e {retomada}.",
                "hora_leitura": f"Conduzir {leitura} de texto jornalistico identificando lide e dados.",
                "pratica": f"Propor questoes de compreensao e analise com {registro}.",
                "foco": f"Explorar papel do jornalismo e construcao de sentidos em {tema}.",
                "encerramento": f"Sintetizar as percepcoes sobre leitura e aplicar {encerramento}."
            }

        return None
    return None


def _metodologia_projeto_de_vida(texto_base: str, tema: str, tipo: str, conceito: str, atividade_extraida: str) -> dict[str, str] | None:
    """Gerador especializado de frases para o perfil Projeto de Vida.

    Retorna dicionário de frases por chave de etapa (para integração no motor
    geral via _frases_por_contexto). Cobre 6 tipos de aula:
    'autoconhecimento', 'futureme', 'producao_coletiva',
    'convivencia', 'consciencia_social', 'encerramento'.
    """
    import re
    texto_norm = normalizar_texto(texto_base)

    # Questão essencial
    match_q = re.search(r"(?:questao essencial|pergunta disparadora)[:\s]*([^\n?]+\??)", texto_base, re.I)
    questao = match_q.group(1).strip() if match_q else f"como as escolhas de hoje influenciam o amanhã em relação a {tema}?"

    # Música ou Vídeo disparador
    match_mv = re.search(r"(?:musica|m%C3%BAsica|clipe|video|v%C3%ADdeo|cancao|can%C3%A7ao|can%C3%A7%C3%A3o)[:\s]*([^\n,.]+)", texto_base, re.I)
    midia_nome = match_mv.group(1).strip() if match_mv else ""

    # Extração de perguntas adicionais
    perguntas = re.findall(r"([^?\n]{15,100}\?)", texto_base)
    p1 = perguntas[0].strip() if len(perguntas) > 0 else f"O que você pensa sobre {tema}?"
    p2 = perguntas[1].strip() if len(perguntas) > 1 else "Como isso se aplica no seu dia a dia?"

    # Construção do conceito
    conceito_seguro = _conceito_projeto_vida(conceito, tema, texto_base, atividade_extraida)

    # Atividade prática
    atividade = atividade_extraida or f"mapeamento e reflexão sobre {tema}"

    if tipo == "futureme":
        match_act = re.search(r"(?:questionario de perfil|questionario de personalidade|mapa de oportunidades|podio dos cursos|podio das profissoes)", texto_norm)
        act_name = match_act.group(0).title() if match_act else "Questionário de Perfil Profissional"
        return {
            "ponto_de_partida": (
                f"Iniciar a aula retomando a proposta de {tema} e convidando os estudantes a refletirem sobre o "
                f"que esperam descobrir sobre si mesmos. Conectar a atividade ao projeto bimestral de autoconhecimento "
                f"profissional e abrir para breve troca em duplas: '{questao}'."
            ),
            "construindo_o_conceito": (
                f"Apresentar o conceito de {conceito_seguro} de forma dialogada, esclarecendo que os resultados da "
                f"plataforma são pontos de partida para reflexão — não rótulos definitivos. Reforçar que "
                f"personalidade e habilidades se desenvolvem ao longo da vida."
            ),
            "acesso_plataforma": (
                f"Orientar os estudantes a acessarem a plataforma FutureMe e seguirem o passo a passo para o "
                f"{act_name}, garantindo que todos consigam navegar com autonomia, apoiando individualmente quem "
                f"tiver dificuldade. Após a conclusão, pedir que leiam o relatório com atenção."
            ),
            "compartilhamento": (
                f"Organizar trios para a troca dos resultados: em quais partes do relatório você mais se reconheceu? "
                f"O que não fez sentido? Com base no seu perfil, que tipos de profissões parecem combinar mais com você? "
                f"Alguns trios compartilham com a turma."
            ),
            "encerramento": (
                f"Encerrar com síntese: o relatório é apenas um ponto de partida. O que você pretende investigar "
                f"mais sobre {tema}? Propor registro individual no caderno."
            ),
        }

    if tipo == "producao_coletiva":
        match_prod = re.search(r"(?:biomapa|campanha|mostra|painel|caixa dos vinculos|video|festival do minuto|hq)", texto_norm)
        prod_name = match_prod.group(0).title() if match_prod else "projeto do bimestre"
        return {
            "relembre": (
                f"Retomar o projeto bimestral e o que foi produzido nas aulas anteriores, conectando ao foco "
                f"da aula: {tema}. Verificar onde cada grupo parou e o que precisa avançar."
            ),
            "foco_no_tema": (
                f"Apresentar a proposta de {tema}, esclarecendo o produto esperado — {prod_name} —, os critérios "
                f"de qualidade e os próximos passos. Analisar coletivamente o modelo, identificando os elementos "
                f"que devem estar presentes na produção."
            ),
            "producao_em_grupos": (
                f"Organizar a turma em grupos, distribuir materiais e orientar a produção passo a passo, garantindo "
                f"que todos participem com funções definidas. Circular pela sala apoiando os grupos e incentivando "
                f"o uso dos recursos indicados."
            ),
            "apresentacao": (
                f"Promover o compartilhamento das produções com a turma, valorizando as escolhas de cada grupo. "
                f"Propor avaliação coletiva com base nos critérios combinados."
            ),
            "encerramento": (
                f"Encerrar com registro individual: o que você aprendeu ao produzir {tema} em grupo? Como esse "
                f"processo se conecta à sua trajetória e projeto de vida?"
            ),
        }

    if tipo == "convivencia":
        return {
            "relembre": (
                f"Retomar o Painel de Convivência ou produto anterior, revisitando os acordos coletivos e o que foi "
                f"discutido nas aulas anteriores sobre {tema}."
            ),
            "foco_no_tema": (
                f"Apresentar o dilema ou tema de reflexão coletiva sobre {conceito_seguro}, explicando como as "
                f"decisões de cada um afetam o grupo e ajudando a turma a relacionar sentir, pensar e agir de "
                f"forma respeitosa na convivência escolar."
            ),
            "circulo_ou_votacao": (
                f"Organizar a turma em círculo, definir os papéis (mediador, secretário, guardião do tempo) e conduzir "
                f"o debate sobre {tema} com rodadas de fala respeitosas, levantamento de soluções e avaliação de "
                f"consequências. Registrar a decisão coletiva no Painel de Convivência."
            ),
            "encerramento": (
                f"Encerrar com compromisso individual escrito: o que você pode fazer concretamente para contribuir "
                f"com {tema} no cotidiano da escola e da sua comunidade?"
            ),
        }


    if tipo == "consciencia_social":
        return {
            "para_comecar": (
                f"Iniciar com dinâmica corporal ou leitura de dados que evidenciem diferenças de condições de vida "
                f"relacionadas a {tema}. Conduzir sem julgamento individual, garantindo um ambiente de respeito e "
                f"acolhimento."
            ),
            "foco_no_tema": (
                f"Apresentar dados e reportagens sobre {tema} de forma dialogada, conectando as informações à "
                f"realidade dos estudantes. Convidar à análise crítica sobre privilégios, desvantagens e o papel "
                f"de cada um como agente de transformação."
            ),
            "pratica": (
                f"Propor atividade de análise: mapa do ambiente digital, leitura crítica de mídia, revisão de HQ "
                f"ou registro no livro sobre {tema}. Orientar os estudantes a identificar padrões, questionar "
                f"representações e propor perspectivas mais inclusivas."
            ),
            "encerramento": (
                f"Encerrar com reflexão individual: reconhecer {tema} muda o que você faz? O que você pode começar "
                f"a fazer de diferente a partir de hoje?"
            ),
        }

    if tipo == "encerramento":
        match_prod = re.search(r"(?:caixa dos vinculos|painel de convivencia|mostra|pacto final|video|biomapa)", texto_norm)
        prod_name = match_prod.group(0).title() if match_prod else "projeto do bimestre"
        return {
            "relembre": (
                f"Abrir simbolicamente o projeto bimestral — {prod_name} — revisitando o percurso completo. "
                f"Convidar os estudantes a lembrarem das aulas, das reflexões e das produções realizadas ao longo "
                f"do bimestre."
            ),
            "sintese_do_percurso": (
                f"Propor síntese coletiva: o que aprendemos sobre {tema} neste bimestre? Quais foram os momentos "
                f"mais marcantes? O que mudou na forma de pensar sobre o futuro?"
            ),
            "producao_final": (
                f"Orientar a produção final do projeto bimestral — vídeo, mostra, pacto, post-it com palavras-chave — "
                f"garantindo que cada estudante contribua com sua perspectiva pessoal."
            ),
            "encerramento": (
                f"Reservar tempo para a síntese individual escrita, com perguntas que conectem o aprendizado à vida "
                f"fora da escola: o que você leva deste bimestre? O que pretende fazer de diferente? Encerrar com "
                f"ritual coletivo — depositar palavras na caixa, assinar o painel ou compartilhar com a turma — "
                f"reforçando que esse gesto representa um pacto pessoal e coletivo com os aprendizados do bimestre."
            ),
        }

    # autoconhecimento / default
    if midia_nome:
        ponto_partida_str = (
            f"Iniciar a aula com a escuta/exibição da música ou vídeo '{midia_nome}', convidando os estudantes "
            f"a perceberem as emoções e ideias despertadas, sem exigir exposicao pessoal. Propor que conversem "
            f"em duplas sobre as questões: '{p1}' e '{p2}'."
        )
    else:
        ponto_partida_str = (
            f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. "
            f"Propor que os estudantes reflitam sobre a pergunta: '{questao.rstrip('?')}', "
            f"respeitando diferentes ritmos de participacao."
        )

    return {
        "ponto_de_partida": ponto_partida_str,
        "construindo_o_conceito": (
            f"Apresentar o conceito de {tema} de forma dialogada, convidando os estudantes a relacionarem as "
            f"ideias às suas próprias experiências, valores e percepções. Destacar os pontos centrais do tema "
            f"com perguntas que incentivem a participação."
        ),
        "colocando_em_pratica": (
            f"Orientar a elaboração individual de {atividade}, com instruções passo a passo. Garantir que a "
            f"socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas."
        ),
        "virem_e_conversem": (
            f"Organizar duplas para o compartilhamento das produções: cada estudante apresenta seu registro, "
            f"explica suas escolhas e ouve as percepções do colega sobre {tema}, praticando a escuta ativa."
        ),
        "socializacao": (
            "Promover correcao dialogada e socializacao de diferentes respostas, comparando caminhos de leitura e retomando "
            "as evidencias mais consistentes do material."
        ),
        "planejamento_debate": (
            "Organizar a selecao de argumentos e contra-argumentos, definindo quais evidencias podem sustentar cada "
            "posicionamento antes do debate."
        ),
        "revisao_colega": (
            "Orientar revisao em dupla ou com colega, verificando clareza, coerencia, organizacao das ideias e adequacao "
            "ao genero antes da versao final."
        ),
        "fica_a_dica": (
            "Destacar uma dica importante para evitar erros recorrentes e ajudar a turma a aplicar o conceito com mais seguranca."
        ),
        "encerramento": (
            f"Encerrar a aula com síntese pessoal escrita no caderno: o que você descobriu sobre {conceito_seguro}? "
            f"O que esse aprendizado muda na forma como você pensa sobre seu futuro?"
        ),
    }


def _metodologia_projeto_vida(
    texto_base: str,
    tema: str,
    tipo: str,
    conceito: str = "",
    atividade_extraida: str = "",
) -> list[dict]:
    """Adapter de Projeto de Vida em `list[dict]`, com fonte unica de conteudo."""

    tipo_normalizado = tipo or "autoconhecimento"
    frases = _metodologia_projeto_de_vida(
        texto_base=texto_base,
        tema=tema,
        tipo=tipo_normalizado,
        conceito=conceito,
        atividade_extraida=atividade_extraida,
    )
    if not frases:
        return []

    etapas = []
    for titulo, chave in _etapas_por_perfil("projeto_de_vida", tipo_normalizado):
        texto = frases.get(chave)
        if texto:
            etapas.append({"titulo": titulo, "texto": texto})
    return etapas


def _metodologia_ingles(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "") -> dict[str, str] | None:
    import re
    texto_norm = normalizar_texto(texto_base)

    # Extrair perguntas se houver
    perguntas = re.findall(r"([^?\n]{15,100}\?)", texto_base)
    pergunta_str = f" \"{perguntas[0].strip()}\"" if perguntas else ""

    atividade = atividade_extraida or "as atividades propostas"

    if tipo == "leitura_em":
        return {
            "para_comecar_virem_e_conversem": (
                f"Iniciar a aula com a técnica Virem e conversem, propondo perguntas sobre {tema} para ativar o conhecimento "
                f"prévio dos estudantes:{pergunta_str if pergunta_str else ' como o tema se relaciona com o cotidiano deles?'} "
                f"Socializar as respostas com a turma antes de avançar para o texto principal."
            ),
            "vocabulario_pre_leitura": (
                f"Apresentar o vocabulário temático da aula com apoio visual e prática de pronúncia (listen and repeat), "
                f"incentivando os estudantes a registrarem as novas palavras no caderno. Destacar palavras cognatas e falsos amigos."
            ),
            "leitura_texto_principal": (
                f"Conduzir a leitura orientada do texto da aula sobre {tema}, explorando cognatas, palavras-chave e estratégias "
                f"de inferência pelo contexto. Atividade central: {atividade}."
            ),
            "foco_conteudo_estrategia": (
                f"Apresentar e praticar as estratégias de leitura para o tipo de texto da aula: identificação de cognatas, "
                f"busca por palavras-chave, inferência pelo contexto e análise das imagens para consolidar a compreensão."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de verificação da aprendizagem com a questão de múltipla escolha do material, "
                f"solicitando que os estudantes respondam individualmente e justifiquem sua escolha antes da correção coletiva."
            ),
            "questoes_vestibular": (
                f"Propor a resolução de questão de vestibular (ENEM/SARESP/UNESP) presente no material sobre {tema}, "
                f"orientando os estudantes a aplicar as estratégias de leitura estudadas (eliminação de alternativas e busca de evidências)."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar a aula com a técnica Com suas palavras, solicitando que os estudantes respondam em inglês "
                f"às perguntas de síntese do material. Registrar os pontos que precisarão ser retomados."
            )
        }

    if tipo == "gramatica":
        conteudo_gramatica = conceito or tema
        return {
            "relembre_ou_para_comecar": (
                f"Retomar com a turma os principais conceitos ou vocabulário trabalhados na aula anterior relacionados a {tema}, "
                f"com exemplos e síntese visual no quadro."
            ),
            "listening_ou_vocabulario": (
                f"Conduzir a escuta do áudio de introdução ou apresentar o vocabulário inicial de {tema}, "
                f"praticando a pronúncia das palavras novas com a técnica listen and repeat."
            ),
            "foco_conteudo_gramatica": (
                f"Retomar os exemplos do texto/áudio e identificar com a turma a estrutura gramatical de {conteudo_gramatica}. "
                f"Apresentar a regra de forma clara e contextualizada, com exemplos retirados do material."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de verificação com a questão do material, solicitando que os estudantes decidam "
                f"e justifiquem a resposta antes da correção coletiva."
            ),
            "exercicios_estruturados": (
                f"Conduzir as atividades de fixação (fill in the blanks, matching ou reorganização de frases) no caderno, "
                f"orientando o uso do material de apoio. Atividade: {atividade}."
            ),
            "producao_oral_duplas": (
                f"Organizar os estudantes em duplas para a prática oral utilizando o modelo de diálogo e o banco de palavras "
                f"do material (técnica In pairs), estimulando a troca de papéis."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar a aula com a técnica Com suas palavras, solicitando que os estudantes produzam uma frase curta "
                f"em inglês usando a estrutura gramatical trabalhada ({conteudo_gramatica})."
            )
        }

    if tipo == "listening":
        return {
            "para_comecar_virem_e_conversem": (
                f"Iniciar com a técnica Virem e conversem para que os estudantes compartilhem o que já sabem sobre o tema {tema}, "
                f"levantando hipóteses a partir de imagens."
            ),
            "vocabulario_pre_escuta": (
                f"Apresentar as palavras-chave do áudio de {tema} com foco na pronúncia e no significado, preparando a turma "
                f"para a escuta atenta."
            ),
            "listening_atividade": (
                f"Conduzir a escuta atenta do áudio (técnica Listen to the audio), orientando os estudantes a identificar informações "
                f"específicas da atividade: {atividade}. Garantir script para estudantes surdos."
            ),
            "foco_conteudo": (
                f"Explicar as estruturas gramaticais e expressões centrais identificadas na conversa gravada, conectando ao uso prático."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de checagem de compreensão com questão rápida do material antes de avançar para as demais atividades."
            ),
            "pratica_adicional": (
                f"Propor atividade prática baseada no áudio (exercício de true/false ou preenchimento de tabela), em duplas ou individualmente."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar solicitando que os estudantes citem pelo menos duas informações-chave ouvidas no áudio, utilizando o inglês "
                f"para sintetizar."
            )
        }

    if tipo == "producao_oral":
        return {
            "relembre": (
                f"Relembrar expressões e vocabulário úteis para situações cotidianas semelhantes a {tema}, "
                f"praticando brevemente a pronúncia com a classe."
            ),
            "vocabulario_expressoes": (
                f"Apresentar as expressões idiomáticas ou alterações de conversação do material úteis para a interação oral sobre {tema}."
            ),
            "modelo_dialogo": (
                f"Apresentar o modelo de diálogo do material e conduzir a leitura em voz alta com toda a classe (listen and repeat) "
                f"para fixar entonação e pronúncia."
            ),
            "pratica_em_duplas": (
                f"Organizar a prática oral do diálogo em duplas (In pairs), orientando que troquem de papéis e variem as informações "
                f"do diálogo conforme as opções do material."
            ),
            "producao_propria": (
                f"Propor que as duplas criem e encenem sua própria versão do diálogo ou realizem a produção oral solicitada: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Pedir que algumas duplas voluntárias encenem o diálogo para a classe. Valorizar a comunicação e o esforço de fala em inglês."
            )
        }

    if tipo == "leitura_literaria":
        return {
            "para_comecar_virem_e_conversem": (
                f"Iniciar a aula ativando o conhecimento dos alunos sobre o autor ou gênero literário do trecho a ser lido em {tema}, "
                f"propondo hipóteses com base em ilustrações ou títulos."
            ),
            "foco_conteudo_estrategia_literaria": (
                f"Apresentar estratégias de leitura literária: identificação de personagens, cenários, adjetivos de descrição "
                f"física ou psicológica, e análise do tom positivo ou negativo do autor."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa de verificação sobre o fragmento literário lido, pedindo que os estudantes justifiquem "
                f"a resposta correta."
            ),
            "atividades_leitura": (
                f"Orientar a análise detalhada do trecho literário proposto, localizando adjetivos e descrições cruciais. "
                f"Atividade principal: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar pedindo que os estudantes resumam o conflito do personagem ou a ideia principal do trecho literário "
                f"com suas palavras em inglês."
            )
        }

    if tipo == "musica":
        return {
            "relembre_ou_para_comecar": (
                f"Iniciar a aula conectando com o artista ou tema da canção de hoje relacionada a {tema}, "
                f"despertando o interesse e a familiaridade dos estudantes com a música."
            ),
            "listening_musica": (
                f"Conduzir a escuta de um fragmento ou da música completa (usando lyric video no YouTube), incentivando "
                f"a turma a acompanhar a letra e cantar junto."
            ),
            "analise_letra": (
                f"Conduzir a leitura e análise de trechos da letra da música, identificando o tema central e os novos "
                f"vocabulários no contexto lírico."
            ),
            "foco_conteudo_gramatica": (
                f"Destacar a estrutura gramatical de {conceito or tema} presente nos versos da canção, analisando a regra a partir do uso real."
            ),
            "pause_e_responda": (
                f"Realizar uma pausa formativa para discutir o significado de versos específicos da música ou sobre a estrutura gramatical estudada."
            ),
            "exercicios_pratica": (
                f"Propor exercícios práticos como matching de versos, completar lacunas da letra da música (fill in the blanks) "
                f"ou ordenação de estrofes. Atividade: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Encerrar pedindo aos alunos para expressarem sua opinião sobre a música usando uma frase simples em inglês "
                f"(ex: 'I like this song because...')."
            )
        }

    if tipo == "revisao":
        return {
            "relembre_sintese": (
                f"Iniciar a aula revisando os principais pontos lexicais e gramaticais trabalhados nas últimas aulas relacionados a {tema}, "
                f"usando esquemas resumidos no quadro."
            ),
            "atividades_revisao_multiplas": (
                f"Conduzir a resolução das atividades de revisão e consolidação do bloco (exercícios práticos e simulados). Atividade: {atividade}."
            ),
            "encerramento_com_suas_palavras": (
                f"Pedir que os estudantes citem pelo menos 3 coisas (regras, palavras ou frases) que aprenderam a fazer em inglês neste bloco."
            )
        }

    # Fallback / Vocabulário
    return {
        "para_comecar": (
            f"Iniciar a aula ativando os conhecimentos prévios sobre o vocabulário de {tema}. Propor discussão rápida em duplas."
        ),
        "vocabulario": (
            f"Apresentar o vocabulário de {tema} com apoio de imagens e prática de pronúncia usando a técnica listen and repeat."
        ),
        "foco": (
            f"Formalizar o vocabulário e as expressões do material no quadro, explicando classe gramatical e usos."
        ),
        "todo_mundo_escreve": (
            f"Solicitar {t_reg} para que cada estudante registre individualmente respostas, comentarios, topicos ou paragrafos "
            "antes da socializacao, retomando o texto-base para justificar as ideias."
        ),
        "de_olho_modelo": (
            "Apresentar um modelo comentado de resposta, paragrafo, argumento ou procedimento de analise, explicando os "
            "criterios que a turma devera observar antes da atividade autonoma."
        ),
        "pause": (
            f"Realizar uma pausa para checagem rápida de vocabulário com perguntas direcionadas aos estudantes."
        ),
        "pratica": (
            f"Conduzir a atividade prática com o banco de palavras e exercícios do material. Atividade: {atividade}."
        ),
        "encerramento": (
            f"Encerrar pedindo aos estudantes que usem 3 palavras novas da aula de hoje em inglês em frases curtas no caderno."
        )
    }



def _metodologia_ciencias(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "") -> dict[str, str] | None:
    """Gerador especializado de frases para Ciencias EF."""
    base = normalizar_texto(" ".join([tema, texto_base, atividade_extraida]))
    tema_base = _tema_base_ciencias(tema)
    conceito_seguro = _conceito_ciencias_seguro(conceito, tema_base)
    atividade = _atividade_ciencias_segura(atividade_extraida, tema_base)
    eh_rpg_manejo = any(
        marcador in base
        for marcador in [
            "rpg",
            "plano de manejo",
            "papel do governo",
            "papel da comunidade",
            "papel dos pesquisadores",
            "unidade de conservacao",
            "grupos assumem",
        ]
    )

    contexto = "uma situacao concreta do cotidiano, imagem, noticia ou dado apresentado no material"
    recurso_visual = "a imagem, o esquema, o instrumento ou o modelo apresentado no material"
    fonte_dados = "graficos, tabelas, mapas, infograficos ou dados apresentados no material"
    if any(k in base for k in ["inpe", "ibge", "detran", "fapesp", "jornal da usp", "g1", "cnn", "onu", "anvisa", "fiocruz"]):
        contexto = "o dado ou a fonte real apresentada no material"
        fonte_dados = "a fonte real e os dados apresentados no material"
    elif any(k in base for k in ["sao paulo", "cantareira", "aricanduva", "praca da se", "goiania", "brasil"]):
        contexto = "o exemplo local ou brasileiro apresentado no material"
    if any(k in base for k in ["modelo tridimensional", "modelo celular", "maquete", "representacao tridimensional"]):
        recurso_visual = "o modelo cientifico ou a representacao construida no material"
    elif "mapa" in base:
        recurso_visual = "a imagem, o esquema, o mapa ou o modelo apresentado no material"
    if any(k in base for k in ["anemometro", "barometro", "pluviometro", "termometro", "umidade relativa", "estacao meteorologica"]):
        fonte_dados = "os instrumentos e as medidas apresentados no material"

    if tipo == "analise_dados":
        return {
            "para_comecar": (
                f"Contextualizar {tema} com {contexto}, mobilizando conhecimentos previos e levantando hipoteses sobre o que os dados podem revelar."
            ),
            "analise_dados": (
                f"Orientar a leitura de {fonte_dados}, destacando titulo, fonte, legenda, unidades, comparacoes e tendencias antes da formulacao das conclusoes."
            ),
            "foco": (
                f"Sistematizar {conceito_seguro}, relacionando os dados observados a explicacoes cientificas, relacoes de causa e consequencia e vocabulario proprio da area."
            ),
            "pratica": (
                f"Organizar a analise em duplas ou grupos, solicitando que a turma utilize os dados do material para justificar respostas e explicar o fenomeno estudado. Atividade central: {atividade}."
            ),
            "correcao_dialogada": (
                "Comparar as interpretacoes produzidas pela turma, corrigindo leituras apressadas dos dados e reforcando como as evidencias sustentam as conclusoes."
            ),
            "encerramento": (
                f"Encerrar retomando o que os dados ajudaram a compreender sobre {tema}, com sintese curta em linguagem cientifica."
            ),
        }

    if tipo == "modelagem_cientifica":
        return {
            "relembre": (
                f"Retomar com a turma o que ja foi estudado sobre {tema}, destacando os componentes e as relacoes que precisarao aparecer na representacao."
            ),
            "observacao_inicial": (
                f"Orientar a observacao de {recurso_visual}, identificando partes, funcoes e limites da representacao antes da construcao ou comparacao do modelo."
            ),
            "mao_na_massa": (
                "Conduzir a construcao ou montagem do modelo passo a passo, utilizando apenas os materiais e orientacoes presentes no material e acompanhando o registro das escolhas do grupo."
            ),
            "socializacao": (
                "Promover a apresentacao dos modelos, comparando semelhancas, diferencas, componentes identificados e a forma como cada grupo representou o processo ou a estrutura estudada."
            ),
            "correcao_dialogada": (
                f"Retomar coletivamente os componentes de {conceito_seguro}, ajustando imprecisoes e reforcando que o modelo simplifica a realidade para favorecer a compreensao."
            ),
            "encerramento": (
                f"Encerrar pedindo que os estudantes expliquem o que o modelo ajudou a compreender sobre {tema} e quais limites essa representacao apresenta."
            ),
        }

    if tipo == "situacao_problema":
        situacao_problema_txt = (
            f"Apresentar o cenario do material e orientar os grupos a identificar problema central, causas, consequencias, agentes envolvidos e criterios para propor solucoes."
        )
        pratica_txt = (
            f"Organizar o trabalho em equipes para elaborar respostas, plano de acao ou proposta de intervencao, exigindo justificativas apoiadas em conceitos e evidencias do material. Atividade central: {atividade}."
        )
        socializacao_txt = (
            "Mediar a apresentacao das propostas, estimulando perguntas entre os grupos e comparacao entre solucoes, responsabilidades e impactos considerados."
        )
        correcao_txt = (
            "Integrar as contribuicoes da turma, corrigindo simplificacoes, reforcando a complexidade do problema e validando as propostas com base nos conceitos cientificos."
        )
        encerramento_txt = (
            f"Finalizar retomando por que a analise de {tema} exige acao coletiva, argumentacao baseada em evidencias e articulacao entre diferentes agentes."
        )

        if eh_rpg_manejo:
            situacao_problema_txt = (
                "Apresentar a situacao-problema do RPG e explicitar que os grupos assumirao papeis diferentes, como governo, comunidade local e pesquisadores, para analisar interesses, responsabilidades e limites de cada agente."
            )
            pratica_txt = (
                f"Organizar os grupos por papel e orientar a construcao coletiva do plano de manejo, solicitando que cada equipe analise impactos, prioridades, evidencias do material e medidas viaveis antes de negociar a proposta final. Atividade central: {atividade}."
            )
            socializacao_txt = (
                "Mediar a apresentacao e a negociacao entre os grupos, comparando argumentos, conflitos de interesse, medidas de protecao e responsabilidades assumidas por cada papel."
            )
            correcao_txt = (
                "Retomar com a turma quais propostas ficaram mais coerentes com as evidencias cientificas, com os impactos observados e com a necessidade de preservar a unidade de conservacao."
            )
            encerramento_txt = (
                "Encerrar sintetizando os pontos principais do RPG, retomando as propostas para o plano de manejo e verificando quais argumentos foram mais fundamentados em evidencias cientificas."
            )

        return {
            "relembre": (
                f"Retomar os conceitos necessarios para analisar {tema}, recuperando o que a turma ja sabe sobre causas, impactos e agentes envolvidos."
            ),
            "situacao_problema": situacao_problema_txt,
            "pratica": pratica_txt,
            "socializacao": socializacao_txt,
            "correcao_dialogada": correcao_txt,
            "encerramento": encerramento_txt,
        }

    if tipo == "pratica_experimental":
        return {
            "relembre": (
                f"Retomar o conceito central de {tema} e o que a turma precisa observar para compreender o fenomeno durante a pratica."
            ),
            "para_comecar": (
                "Apresentar a questao investigativa, os materiais e os cuidados necessarios, esclarecendo o procedimento antes do inicio da atividade."
            ),
            "mao_na_massa": (
                "Conduzir o procedimento passo a passo, utilizando apenas os materiais e etapas indicados no material e acompanhando o registro das observacoes feitas pelos estudantes."
            ),
            "pratica": (
                f"Orientar a comparacao dos resultados observados, solicitando que a turma relacione o que ocorreu ao conceito cientifico estudado. Atividade central: {atividade}."
            ),
            "correcao_dialogada": (
                "Retomar as observacoes registradas pela turma, corrigindo interpretacoes precipitadas e reforcando como as evidencias ajudam a explicar o fenomeno."
            ),
            "encerramento": (
                f"Encerrar com sintese breve sobre o que a pratica permitiu compreender a respeito de {tema}, sem antecipar resultados nao observados no material."
            ),
        }

    if tipo == "investigativa":
        return {
            "para_comecar": (
                f"Lancar a questao investigativa relacionada a {tema}, pedindo que os estudantes formulem hipoteses iniciais antes da explicacao formal."
            ),
            "observacao_inicial": (
                f"Orientar a observacao de {recurso_visual}, destacando o que precisa ser registrado como evidencia durante a investigacao."
            ),
            "pratica": (
                f"Conduzir o registro das evidencias e a comparacao entre hipoteses, incentivando a turma a justificar respostas com base no que observou. Atividade central: {atividade}."
            ),
            "foco": (
                f"Sistematizar {conceito_seguro} a partir das evidencias levantadas, articulando observacao, explicacao cientifica e vocabulario proprio da aula."
            ),
            "encerramento": (
                f"Retomar a pergunta inicial e solicitar que os estudantes expliquem como as evidencias analisadas ajudaram a compreender {tema}."
            ),
        }

    if tipo == "impacto_socioambiental":
        return {
            "para_comecar": (
                f"Apresentar {contexto} sobre {tema}, mobilizando conhecimentos previos e perguntas sobre impactos, responsabilidades e possiveis formas de enfrentamento."
            ),
            "foco": (
                f"Explicar {conceito_seguro}, relacionando a aula a causas e consequencias, uso de recursos, saude, ambiente e responsabilidade coletiva."
            ),
            "analise_dados": (
                f"Orientar a leitura de {fonte_dados}, relacionando os dados, as evidencias e os exemplos do material aos impactos discutidos."
            ),
            "pratica": (
                f"Organizar a turma para analisar medidas possiveis, responsabilidades dos agentes envolvidos e propostas de acao, exigindo justificativas baseadas nos conceitos estudados. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar com sintese sobre como {tema} envolve ciencia, ambiente, sociedade e tomada de decisao responsavel, retomando as perguntas iniciais da aula."
            ),
        }

    if tipo == "revisao_retomada":
        return {
            "relembre": (
                f"Retomar com a turma os conceitos ja estudados sobre {tema}, usando uma pergunta curta em duplas para identificar o que ficou consolidado e o que precisa ser aprofundado."
            ),
            "foco": (
                f"Reorganizar {conceito_seguro} de forma progressiva, estabelecendo conexoes entre os conteudos anteriores, exemplos do material e novas aplicacoes cientificas."
            ),
            "modelo": (
                "Apresentar o exercicio resolvido ou exemplo comentado passo a passo, destacando o raciocinio cientifico usado para interpretar dados, esquemas ou situacoes-problema."
            ),
            "pause": (
                "Propor uma verificacao formativa rapida, com questao objetiva, verdadeiro ou falso ou pergunta curta, e corrigir coletivamente antes de seguir para a atividade."
            ),
            "pratica": (
                f"Orientar a atividade de retomada com registro escrito, solicitando que os estudantes justifiquem as respostas com base nos conceitos revisados. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar com sintese em linguagem propria, pedindo que os estudantes expliquem a relacao entre {tema} e os conceitos retomados na aula."
            ),
        }

    if tipo == "leitura_analise":
        return {
            "para_comecar": (
                f"Apresentar {contexto} sobre {tema} e propor que os estudantes levantem hipoteses em duplas, relacionando o assunto ao cotidiano e a questoes de ciencia, sociedade, saude ou ambiente."
            ),
            "leitura": (
                f"Realizar leitura compartilhada do texto, noticia, dado ou fonte sobre {tema}, identificando informacoes centrais, vocabulario cientifico e evidencias usadas para sustentar as ideias."
            ),
            "foco": (
                f"Explicar {conceito_seguro} articulando o texto lido aos conceitos cientificos, destacando relacoes de causa, consequencia, comparacao e impacto social ou ambiental."
            ),
            "pause": (
                "Fazer uma pausa de verificacao com pergunta objetiva ou verdadeiro/falso, solicitando que os estudantes justifiquem a resposta antes da correcao coletiva."
            ),
            "pratica": (
                f"Propor atividade escrita de interpretacao e analise critica, orientando a retomada do texto para localizar evidencias e construir respostas fundamentadas. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Retomar as hipoteses iniciais e solicitar uma sintese curta sobre o que o texto ajudou a compreender a respeito de {tema}."
            ),
        }

    if tipo == "estudo_caso":
        return {
            "para_comecar": (
                f"Apresentar o caso ou situacao-problema relacionado a {tema}, pedindo que os estudantes identifiquem o problema central e levantem explicacoes iniciais."
            ),
            "foco": (
                f"Sistematizar os conceitos necessarios para analisar o caso, explicando {conceito_seguro} com apoio de esquemas, dados ou exemplos do material."
            ),
            "estudo_caso": (
                "Conduzir a analise do caso em etapas: identificar os elementos envolvidos, explicar as relacoes cientificas e discutir consequencias para a saude, o ambiente ou a sociedade."
            ),
            "pause": (
                "Realizar checagem formativa antes da resposta final, verificando se a turma compreendeu quais evidencias sustentam a explicacao do caso."
            ),
            "pratica": (
                f"Orientar o registro escrito da solucao ou explicacao do caso, solicitando justificativa cientifica e retomada dos conceitos estudados. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Fechar a aula socializando algumas respostas e destacando como o raciocinio cientifico ajudou a interpretar {tema}."
            ),
        }

    if tipo == "producao_projeto":
        return {
            "relembre": (
                f"Retomar com a turma o percurso ja realizado sobre {tema}, recuperando os conceitos e criterios que deverao aparecer na producao ou apresentacao."
            ),
            "foco": (
                f"Explicar os criterios de qualidade da producao cientifica, destacando clareza das informacoes, uso correto de {conceito_seguro}, organizacao visual e relacao com a vida cotidiana."
            ),
            "producao": (
                f"Organizar os estudantes em grupos ou individualmente para finalizar, revisar ou apresentar a producao proposta no material. Atividade central: {atividade}."
            ),
            "compartilhamento": (
                "Promover socializacao das producoes, garantindo escuta da turma, perguntas breves e retomada dos criterios combinados."
            ),
            "encerramento": (
                f"Conduzir reflexao final sobre o que foi aprendido durante a producao e como esse conhecimento se relaciona a ciencia, sociedade, saude ou ambiente."
            ),
        }

    return {
        "para_comecar": (
            f"Apresentar {contexto} relacionado a {tema}, mobilizando conhecimentos previos, perguntas iniciais e relacoes com situacoes observaveis no cotidiano."
        ),
        "foco": (
            f"Explicar {conceito_seguro}, retomando exemplos, imagens, esquemas ou comparacoes presentes no material para que a turma compreenda estrutura, processo ou funcionamento com vocabulario cientifico adequado."
        ),
        "pause": (
            "Realizar uma pausa de checagem com pergunta objetiva, associacao entre conceito e exemplo ou explicacao curta, corrigindo duvidas antes da atividade principal."
        ),
        "pratica": (
            f"Orientar as atividades do material, pedindo que os estudantes utilizem evidencias, esquemas, dados ou observacoes da aula para explicar {tema} com clareza. Atividade central: {atividade}."
        ),
        "encerramento": (
            f"Encerrar retomando o que foi compreendido sobre {tema}, solicitando uma sintese curta que relacione conceito, exemplo observado e aplicacao no cotidiano."
        ),
    }

def _metodologia_biologia(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "", habilidade: str = "") -> dict[str, str] | None:
    """Gerador especializado de frases para Biologia."""
    base = normalizar_texto(" ".join([tema, texto_base, atividade_extraida, habilidade]))
    conceito_seguro = conceito if normalizar_texto(conceito) not in {"biologia", "geral", ""} else tema
    atividade = atividade_extraida or "as atividades propostas no material"

    # Extração inteligente de vídeo
    video_titulo = "informativo sobre o tema"
    video_canal = "de divulgação científica"
    video_minutos = "com duração sugerida no material"
    
    # Buscar padrões no texto_base para encontrar títulos de vídeos e canais
    aspas = re.findall(r'["\'“‘]([^"\'”’\n]{3,100})["\'”’]', texto_base)
    # Order alternation from longest to shortest to prevent eager partial matching (e.g. matching 'assista' first)
    video_match = re.search(r'(?:assista ao vídeo|assista ao video|vídeo|video)\s+["\'“‘]?([^"\'”’\n]{3,100})["\'”’]?', texto_base, re.IGNORECASE)
    
    if aspas:
        video_titulo = f'"{aspas[0].strip()}"'
    elif video_match:
        video_titulo = f'"{video_match.group(1).strip()}"'

    canal_match = re.search(r'(?:canal|veiculado pelo canal|do canal|youtube)\s+[:\-]?\s*([A-ZÀ-ÿa-z0-9\s]{3,30})', texto_base, re.IGNORECASE)
    if canal_match:
        video_canal = canal_match.group(1).strip()
    else:
        if "butantan" in base:
            video_canal = "Instituto Butantan"
        elif "fiocruz" in base:
            video_canal = "Fiocruz"
        elif "nerdologia" in base:
            video_canal = "Nerdologia"
        elif "atila" in base or "iamarino" in base:
            video_canal = "Átila Iamarino"

    minutos_match = re.search(r'(?:minuto|minutos|duracao|duração|tempo|de|ate|até)\s+(\d+(?:\'\d+)?(?:\s*(?:a|à|ao|min|s|seg|-\d+))*)', texto_base, re.IGNORECASE)
    if minutos_match:
        video_minutos = minutos_match.group(1).strip()
        if not ("minuto" in video_minutos or "tempo" in video_minutos or "duracao" in video_minutos):
            video_minutos = f"do início ao minuto {video_minutos}"
    else:
        video_minutos = "com duração sugerida no material"

    # Extração de perguntas do texto
    perguntas = [p.strip() for p in re.findall(r'([^?\n.]{10,120}\?)', texto_base)]
    perguntas = [re.sub(r'^[^\w\s]+', '', p).strip() for p in perguntas]
    perguntas = [p for p in perguntas if not re.match(r'^[a-eA-E0-9]\)', p)]

    pergunta_slide = perguntas[0] if len(perguntas) > 0 else f"Como o conhecimento sobre {tema} se aplica no dia a dia?"
    pergunta_sintese_1 = perguntas[-2] if len(perguntas) > 1 else f"Quais são os conceitos principais de {tema} estudados na aula?"
    pergunta_sintese_2 = perguntas[-1] if len(perguntas) > 0 else f"Como as implicações bioéticas e sociais se relacionam com {tema}?"
    if len(perguntas) == 1:
        pergunta_sintese_1 = perguntas[0]
        pergunta_sintese_2 = f"Qual é a importância biológica e social de {tema}?"

    # Extração de palavras-chave
    palavras_chave_match = re.search(r'(?:palavras-chave|palavras chave|termos-chave)[:\-]?\s*([^\n\.]+)', texto_base, re.IGNORECASE)
    if palavras_chave_match:
        palavras_chave_str = palavras_chave_match.group(1).strip()
    else:
        palavras_sugeridas = [w.strip() for w in re.split(r'[,;\s]+', conceito_seguro) if len(w.strip()) > 3]
        if len(palavras_sugeridas) < 2:
            palavras_sugeridas.append(tema)
        palavras_chave_str = ", ".join(palavras_sugeridas[:4])

    # Detecção de ferramenta genética
    ferramenta_genetica = "quadro de Punnett"
    if "heredograma" in base:
        ferramenta_genetica = "heredograma"

    contexto = "uma imagem, noticia, dado ou situacao concreta apresentada no material"
    if any(k in base for k in ["reportagem", "noticia", "amazonia", "inpe", "ods", "matriz energetica", "saude publica", "desmatamento"]):
        contexto = "um dado real, noticia ou problema socioambiental apresentado no material"
    elif any(k in base for k in ["grafico", "infografico", "esquema", "de olho no modelo"]):
        contexto = "o modelo visual cientifico apresentado no material"

    # 1. etico_biotecnologico
    if tipo == "etico_biotecnologico":
        return {
            "para_comecar": (
                f"Iniciar a aula com a exibição do vídeo {video_titulo}, do canal {video_canal} ({video_minutos}), "
                f"propondo a questão: '{pergunta_slide}'. Solicitar que os estudantes registrem suas percepções iniciais e "
                f"abrir para breve discussão coletiva, coletando os conhecimentos prévios da turma sobre o tema."
            ),
            "foco_1": (
                f"Apresentar, de forma dialogada, as informações científicas básicas e o desenvolvimento histórico associados a "
                f"{conceito_seguro}, explicando o mecanismo biológico de forma progressiva e contextualizada."
            ),
            "foco_2": (
                f"Discutir as implicações éticas, legais ou sociais envolvidas, abordando aspectos de bioética, autonomia e consentimento "
                f"associados a {conceito_seguro}, conectando com a atuação de comitês de ética e a dignidade humana."
            ),
            "pause": (
                f"Propor questão de verificação formativa sobre os conceitos éticos ou biológicos discutidos. "
                f"Aguardar as respostas antes de revelar o gabarito e explicar o raciocínio correto."
            ),
            "pratica": (
                f"Organizar os estudantes em duplas para análise do estudo de caso ou texto sobre {tema}. Orientar a leitura e "
                f"a resolução da atividade: {atividade}. Corrigir coletivamente destacando as palavras-chave: {palavras_chave_str}."
            ),
            "encerramento": (
                f"Encerrar com as perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Solicitar que diferentes estudantes respondam, sistematizando as respostas com as palavras-chave centrais: {palavras_chave_str}."
            ),
        }

    # 2. molecular_genetico
    if tipo == "molecular_genetico":
        return {
            "relembre": (
                f"Retomar com os estudantes os conceitos básicos necessários estudados na aula anterior sobre {tema}, "
                f"utilizando esquema ou tabela comparativa como apoio visual para verificar dúvidas antes de avançar."
            ),
            "foco_1": (
                f"Explicar {conceito_seguro} na escala celular e molecular, descrevendo as etapas do processo biológico. "
                f"Utilizar animação ou imagem detalhada do material para ilustrar as estruturas envolvidas."
            ),
            "foco_2": (
                f"Conectar o processo molecular estudado ao seu funcionamento prático no organismo e às suas manifestações fenotípicas, "
                f"explicando a relação de causa e consequência biológica de forma progressiva."
            ),
            "pause": (
                f"Propor questão de múltipla escolha para verificação formativa sobre a estrutura molecular ou cruzamento genético discutido. "
                f"Aguardar as respostas antes de revelar o gabarito e explicar o raciocínio correto."
            ),
            "pratica": (
                f"Orientar a resolução del problema genético ou atividade molecular em duplas, auxiliando na construção do {ferramenta_genetica}. "
                f"Atividade central: {atividade}. Estimular que os estudantes apresentem suas soluções na lousa."
            ),
            "encerramento": (
                f"Finalizar respondendo às perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Sistematizar os resultados na lousa, confirmando os genótipos, fenótipos e proporções esperadas."
            ),
        }

    # 3. debate_critico
    if tipo == "debate_critico":
        return {
            "para_comecar": (
                f"Iniciar a aula com uma imagem provocadora ou trecho de notícia do material sobre {tema}, propondo a questão disparadora: "
                f"'{pergunta_slide}'. Estimular a expressão livre de opiniões e hipóteses iniciais dos estudantes antes do conceito formal."
            ),
            "foco_1": (
                f"Explicar {conceito_seguro} a partir de uma contextualização histórica e social detalhada, demonstrando como teorias pseudocientíficas "
                f"(como eugenia, determinismo biológico ou darwinismo social) foram construídas e desmistificadas pela ciência moderna."
            ),
            "foco_2": (
                f"Aprofundar a base científica sobre a variabilidade genética humana, demonstrando a inexistência de raças biológicas sob a perspectiva "
                f"da genética moderna. Sistematizar os conceitos de ancestralidade e diversidade genética."
            ),
            "pause": (
                f"Propor um Pause e responda com tempo breve para que os estudantes se posicionem individualmente com argumentos científicos antes da correção dialogada."
            ),
            "pratica": (
                f"Organizar grupos para debater as evidências científicas contra preconceitos históricos ou analisar criticamente o texto proposto. "
                f"Orientar a elaboração de um plano de ação ou síntese coletiva sobre a diversidade genética. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Finalizar coletando as sínteses dos grupos e respondendo às perguntas de reflexão: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Sistematizar com as palavras-chave de direitos e ciência: {palavras_chave_str}."
            ),
        }

    # 4. aplicacao_biotecnologica
    if tipo == "aplicacao_biotecnologica":
        return {
            "para_comecar": (
                f"Iniciar a aula com a apresentação de um caso clínico real ou notícia recente sobre {tema}, propondo a questão disparadora: '{pergunta_slide}'. "
                f"Permitir que os estudantes compartilhem suas opiniões e vivências cotidianas com a tecnologia em foco."
            ),
            "foco_1": (
                f"Explicar o conceito de {conceito_seguro} e descrever as etapas do processo biotecnológico envolvido (como produção de vacinas, soros, clonagem ou terapia gênica). "
                f"Exibir o vídeo informativo {video_titulo} do canal {video_canal} ({video_minutos}) para ilustrar a produção real."
            ),
            "foco_2": (
                f"Destacar o papel de instituições públicas de pesquisa do Brasil (como Instituto Butantan, Fiocruz e universidades públicas) na soberania científica e "
                f"saúde coletiva. Discutir aspectos de propriedade intelectual (patentes) e equidade de acesso (SUS)."
            ),
            "pause": (
                f"Propor questão de verificação formativa sobre as etapas de produção ou mecanismos de ação biológicos discutidos. Corrigir revelando o gabarito e detalhando a resposta."
            ),
            "pratica": (
                f"Orientar os estudantes a analisarem em duplas o estudo de caso ou atividade clínica aplicada no material. Propor o preenchimento dos esquemas ou lacunas "
                f"para fixar o vocabulário científico e a lógica do processo. Realizar correção coletiva destacando as palavras-chave: {palavras_chave_str}."
            ),
            "encerramento": (
                f"Encerrar respondendo às perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Destacar como o conhecimento biotecnológico se traduz em bem-estar social e imunidade coletiva."
            ),
        }

    # 5. revisao_aprofundamento
    if tipo == "revisao_aprofundamento":
        return {
            "relembre": (
                f"Retomar os conceitos fundamentais de aulas anteriores sobre {tema} por meio de uma tabela comparativa ou imagem de síntese na lousa. "
                f"Conduzir uma breve arguição diagnóstica para verificar o que foi consolidado."
            ),
            "foco_1": (
                f"Aprofundar os aspectos mais complexos de {conceito_seguro}, utilizando novos exemplos ou contextos que integrem os conhecimentos moleculares e celulares revisados."
            ),
            "pause": (
                f"Realizar um Pause e responda com questões de vestibular ou do material para checagem rápida de consolidação dos tópicos. Discutir a resolução coletivamente."
            ),
            "pratica": (
                f"Propor a resolução em duplas de uma situação-problema mais complexa que integre múltiplos conceitos revisados ou questões de exames (ENEM/vestibulares). "
                f"Conduzir a correção passo a passo na lousa, validando os raciocínios dos estudantes. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Finalizar com perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}', esclarecendo dúvidas remanescentes antes do encerramento."
            ),
        }

    # Fallbacks para compatibilidade com tipos antigos
    if tipo == "aula_desafio":
        return {
            "desafio": (
                f"Apresentar o caso real relacionado a {tema}, destacando os dados mais impactantes e convidando a turma a levantar hipoteses iniciais sem corrigi-las neste momento."
            ),
            "entendendo_problema": (
                f"Conduzir a analise das evidencias em etapas, revelando gradualmente as informacoes do caso e explicando {conceito_seguro} com apoio do raciocinio cientifico, sempre um passo de cada vez."
            ),
            "solucao_acao": (
                f"Organizar duplas ou grupos para elaborar hipoteses, comparar explicacoes e propor respostas fundamentadas para o caso, usando como base {atividade}."
            ),
            "hora_verdade": (
                "Retomar as hipoteses construidas pelos grupos, apresentar as respostas esperadas e discutir por que algumas explicacoes se aproximam mais das evidencias do que outras."
            ),
            "encerramento": (
                f"Encerrar com Com suas palavras, pedindo que os estudantes expliquem o que o caso ajudou a compreender sobre {tema} e quais medidas ou conclusoes cientificas podem ser defendidas."
            ),
        }

    if tipo == "aula_pratica":
        return {
            "relembre": (
                f"Retomar com a turma os conceitos necessarios para observar o fenomeno relacionado a {tema}, recuperando equacoes, etapas ou ideias-chave antes da pratica."
            ),
            "pratica": (
                f"Apresentar os materiais e orientar a montagem da atividade experimental em etapas curtas, pedindo que os estudantes observem, registrem e relacionem o que ocorre com {conceito_seguro}. Atividade central: {atividade}."
            ),
            "discussao_resultados": (
                "Conduzir a discussao dos resultados com Todo mundo escreve, comparando observacoes, confirmando ou revendo hipoteses e explicitando as evidencias mais importantes."
            ),
            "encerramento": (
                f"Finalizar solicitando que os estudantes expliquem, com suas palavras, o que foi observado e como a pratica ajudou a compreender {tema}."
            ),
        }

    if tipo == "revisao_consolidacao":
        return {
            "relembre": (
                f"Retomar termos e conceitos ja estudados sobre {tema}, pedindo que a turma explique com suas palavras o que lembra antes da correcao formal."
            ),
            "foco": (
                f"Conduzir a revisao por meio de quiz, comparacoes e retomada dos conceitos centrais de {conceito_seguro}, esclarecendo diferencas, relacoes e exemplos."
            ),
            "pratica": (
                f"Orientar leitura, classificacao ou resolucao das questoes de consolidacao, solicitando que os estudantes voltem ao material para localizar evidencias e justificar respostas. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar com perguntas comparativas e Com suas palavras, consolidando o que foi retomado sobre {tema} e identificando duvidas que ainda precisam de reforco."
            ),
        }

    if tipo == "impacto_socioambiental":
        return {
            "para_comecar": (
                f"Iniciar a aula apresentando {contexto} sobre {tema}, propondo uma pergunta disparadora que ajude a turma a relacionar fenomenos biologicos, sociedade e ambiente."
            ),
            "foco": (
                f"Explicar {conceito_seguro} de forma progressiva, relacionando o conteudo a impactos ambientais, saude publica, sustentabilidade ou responsabilidade coletiva, sempre um passo de cada vez."
            ),
            "de_olho_modelo": (
                "Apresentar o grafico, infografico, mapa ou esquema do material e orientar a leitura, pedindo que os estudantes identifiquem dados-chave, comparacoes e implicacoes do modelo visual."
            ),
            "pratica": (
                f"Propor atividade de analise de caso, texto ou dados, solicitando registro individual com base em evidencias e conexoes entre ciência, ambiente e vida cotidiana. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar retomando a conexao entre {tema} e suas implicacoes sociais, ambientais ou de saude, com perguntas de sintese em Com suas palavras."
            ),
        }

    # Fallback Geral (Conceito Novo)
    return {
        "para_comecar": (
            f"Iniciar a aula com {contexto} relacionado a {tema}, propondo a questão disparadora: '{pergunta_slide}'. "
            f"Convidar os estudantes a levantar hipóteses e ativar conhecimentos prévios."
        ),
        "foco": (
            f"Explicar {conceito_seguro} em etapas sequenciais, destacando processos, relações de causa e consequência "
            f"e exemplos biológicos reais de forma dialógica e progressiva."
        ),
        "pause": (
            "Propor um Pause e responda antes da atividade prática, com tempo breve para resposta individual e correção dialogada "
            "baseada no conceito central."
        ),
        "pratica": (
            f"Orientar a aplicação do conceito em leitura, classificação, interpretação de modelo ou atividade investigativa em duplas. "
            f"Atividade central: {atividade}."
        ),
        "encerramento": (
            f"Finalizar com as perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}', "
            f"sistematizando o aprendizado com as palavras-chave: {palavras_chave_str}."
        ),
    }

def _metodologia_historia(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "") -> dict[str, str] | None:
    """Gerador especializado de frases para História EF."""
    if tipo == "fonte_historica":
        return {
            "para_comecar": (
                f"Iniciar a aula desenhando uma linha do tempo na lousa para situar o período de {tema}. "
                "Fazer uma pergunta provocativa sobre o que a turma já conhece a respeito dessa época."
            ),
            "foco": (
                f"Apresentar o contexto histórico de {conceito}, identificando os sujeitos históricos, "
                "o tempo, o espaço e os conflitos sociais envolvidos. Explicitar a importância de se "
                "analisar documentos de época para compreender as intencionalidades dos agentes do passado."
            ),
            "pratica": (
                "Orientar a análise crítica de fontes históricas presentes no material (textos de lei, diários, cartas, charges ou imagens). "
                "Mediar o trabalho com três perguntas norteadoras: "
                "1. Quem produziu essa fonte e em qual contexto? "
                "2. Qual a mensagem ou ponto de vista implícito do autor? "
                "3. Como esse documento nos ajuda a compreender o período estudado? "
                "Pedir que os estudantes registrem suas evidências individualmente."
            ),
            "pause": (
                "Socializar as análises dos estudantes, destacando a diferença entre fato histórico "
                "e interpretação, e mediando a leitura crítica dos discursos presentes nas fontes."
            ),
            "encerramento": (
                f"Encerrar a aula conectando {tema} à atualidade, identificando permanências, "
                "legados ou rupturas desse processo histórico em nossa sociedade atual."
            )
        }

    if tipo == "debate_critico":
        return {
            "para_comecar": (
                f"Traçar uma linha do tempo na lousa localizando o contexto de {tema}. "
                "Propor uma questão-problema sobre pontos de vista conflitantes do período para motivar a discussão."
            ),
            "foco": (
                f"Expor de forma dialogada os conceitos centrais de {conceito}, explicitando que a História é construída "
                "a partir de diferentes narrativas e interesses em disputa, situando os agentes sociais e seus discursos."
            ),
            "pratica": (
                f"Organizar a turma para analisar os discursos ou narrativas em conflito sobre {tema}. "
                "Orientar que identifiquem os argumentos de cada lado e os confrontem com as fontes do material. "
                "Estimular a argumentação crítica e fundamentada em evidências históricas."
            ),
            "pause": (
                "Mediar a socialização dos debates, garantindo que os estudantes percebam que os conflitos do passado "
                "possuem intencionalidades claras de seus agentes, evitando anacronismos na avaliação histórica."
            ),
            "encerramento": (
                f"Encerrar refletindo sobre como a disputa de narrativas em {tema} deixou marcas, legados "
                "ou lições que influenciam as discussões e direitos civis do presente."
            )
        }

    if tipo == "analise_geografica":
        return {
            "para_comecar": (
                f"Inserir a coordenada temporal de {tema} em uma linha do tempo na lousa. "
                "Propor uma análise rápida de um mapa histórico ou de uma rota de deslocamento para ativar a curiosidade."
            ),
            "foco": (
                f"Explicar {conceito} com foco na dimensão espacial da História: rotas comerciais, fronteiras, "
                "expansão territorial ou fluxos migratórios. Relacionar as transformações no espaço às decisões políticas e econômicas de época."
            ),
            "pratica": (
                "Orientar a leitura crítica do mapa histórico ou recurso visual do material. "
                "Solicitar que os estudantes localizem os territórios, identifiquem as transformações espaciais "
                "e registrem as relações de causa e consequência observadas."
            ),
            "pause": (
                "Conduzir a correção dialogada da leitura cartográfica, relacionando a ocupação do espaço "
                "aos conflitos e dinâmicas sociais da época estudada."
            ),
            "encerramento": (
                f"Concluir relacionando a configuração territorial do período de {tema} com a geografia política "
                "atual, identificando legados históricos na fronteira ou na ocupação do espaço hoje."
            )
        }

    if tipo == "producao_projeto":
        return {
            "para_comecar": (
                f"Localizar temporalmente {tema} na lousa com uma linha do tempo. "
                "Apresentar a proposta do produto que será elaborado (painel, cartaz, mapa mental ou linha do tempo coletiva)."
            ),
            "foco": (
                f"Apresentar de maneira sintetizada os fatos, sujeitos e conceitos de {conceito} necessários para fundamentar "
                "a produção prática da turma, tirando dúvidas conceituais antes da atividade."
            ),
            "pratica": (
                "Orientar a elaboração do trabalho prático em equipes. Acompanhar a seleção de fontes e evidências "
                "do material pelos grupos para compor o produto, estimulando a autonomia e o trabalho colaborativo."
            ),
            "pause": (
                "Mediar o andamento das produções, tirando dúvidas sobre a organização cronológica e a fidedignidade "
                "histórica das informações selecionadas."
            ),
            "encerramento": (
                f"Promover o compartilhamento das produções e finalizar conectando as conclusões do projeto sobre {tema} "
                "a reflexões críticas sobre a atualidade."
            )
        }

    # Fallback / Leitura
    return {
        "para_comecar": (
            f"Iniciar a aula desenhando uma linha do tempo na lousa para situar o período de {tema}. "
            "Propor que os estudantes compartilhem o que sabem ou imaginam sobre esse contexto histórico."
        ),
        "foco": (
            f"Conduzir a explicação dialogada sobre {conceito}, situando os sujeitos históricos, "
            "as relações de poder, tempo, espaço e conflitos característicos desse período."
        ),
        "pratica": (
            "Orientar a leitura orientada dos textos e fontes documentais do material. Solicitar que os estudantes "
            "registrem individualmente as informações principais e respondam às questões de interpretação histórica."
        ),
        "pause": (
            "Realizar a correção dialogada, confrontando as respostas dos estudantes com as evidências do texto "
            "e mediando a compreensão do contexto histórico."
        ),
        "encerramento": (
            f"Finalizar a aula identificando permanências, rupturas ou legados do período de {tema} "
            "na nossa organização social atual."
        )
    }


def _metodologia_arte(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "", tecnicas: dict = None) -> dict[str, str] | None:
    """Gerador especializado de frases para Arte AF."""
    if not tecnicas:
        tecnicas = {}
    t_disc = tecnicas.get("abertura", "Virem e conversem")
    t_reg = tecnicas.get("registro", "Todo mundo escreve")
    t_sint = tecnicas.get("sintese", "Com suas palavras")
    t_verif = tecnicas.get("verificacao", "Pause e responda")

    if tipo == "dobradura_origami":
        return {
            "para_comecar": (
                f"Apresentar um example visual ou modelo físico de dobradura relacionado a {tema}. "
                f"Propor {t_disc} para instigar a turma sobre como formas geométricas bidimensionais se transformam em objetos tridimensionais com dobras."
            ),
            "foco": (
                f"Explicar o conceito de {conceito}, demonstrando a importância cultural, a precisão geométrica e os "
                "passos fundamentais para a criação da dobradura (origami)."
            ),
            "pratica": (
                f"Propor a experimentação e confecção prática de dobraduras pelos estudantes, seguindo o passo a passo ilustrado do material. "
                f"Solicitar {t_reg} no diário de bordo e incentivar a colaboração mútua no manuseio do papel."
            ),
            "pause": (
                f"Propor {t_verif} acompanhando os estudantes que enfrentam dificuldades nos vincos e dobras, "
                "estimulando a persistência e valorizando o processo de aprendizagem prática."
            ),
            "encerramento": (
                f"Conduzir {t_sint} reunindo as dobraduras produzidas para refletir sobre a composição visual final obtida e "
                "como a repetição de dobras cria volume e significado artístico."
            )
        }

    if tipo == "stop_motion_flipbook":
        return {
            "para_comecar": (
                f"Apresentar uma animação rápida ou um flipbook físico para demonstrar a ilusão de movimento em imagens estáticas. "
                f"Propor {t_disc} para provocar a reflexão sobre como percebemos o movimento no cinema."
            ),
            "foco": (
                f"Explicar a técnica de animação ligada a {conceito}, abordando a persistência da visão, a estrutura de quadros (frames) "
                "e a sequência narrativa necessária para criar movimento."
            ),
            "pratica": (
                f"Orientar os estudantes na elaboração prática do flipbook ou na captura de quadros para o stop-motion. "
                f"Solicitar {t_reg} registrando pequenas variações entre os desenhos ou objetos e estimulando a paciência no processo criativo."
            ),
            "pause": (
                f"Propor {t_verif} para ajudar os grupos a verificar se a fluidez do movimento está funcionando e se a narrativa faz sentido quadro a quadro."
            ),
            "encerramento": (
                f"Conduzir {t_sint} para compartilhar as animações ou flipbooks produzidos, discutindo como o tempo e o espaço são manipulados na linguagem audiovisual."
            )
        }

    if tipo == "assemblage_mosaico":
        return {
            "para_comecar": (
                f"Exibir imagens de obras que utilizam colagem de objetos ou fragmentos tridimensionais (assemblage/mosaico). "
                f"Propor {t_disc} provocando a reflexão se objetos comuns do cotidiano podem se tornar obras de arte."
            ),
            "foco": (
                f"Desenvolver a reflexão sobre {conceito}, abordando como a ressignificação de objetos e resíduos (como na obra de Vik Muniz) "
                "amplia o conceito de montagem, textura e bidimensionalidade/tridimensionalidade."
            ),
            "pratica": (
                f"Orientar a criação de uma assemblage pessoal ou mosaico utilizando materiais alternativos, recortes ou objetos descartados. "
                f"Solicitar {t_reg} no diário de bordo registrando as escolhas dos materiais e explorando texturas e relevos."
            ),
            "pause": (
                f"Propor {t_verif} para que os estudantes compartilhem suas ideias e experimentem combinações inusitadas de objetos em suas composições."
            ),
            "encerramento": (
                f"Conduzir {t_sint} refletindo sobre como a assemblage recontextualiza o descarte em produções expressivas, "
                "discutindo o impacto ambiental e poético da escolha de materiais."
            )
        }

    if tipo == "muralismo_grafite":
        return {
            "para_comecar": (
                f"Exibir fotografias de intervenções urbanas (muralismo, grafite, stickers, lambe-lambe). "
                f"Propor {t_disc} para debater com a turma a diferença entre arte na galeria e arte na rua."
            ),
            "foco": (
                f"Apresentar os conceitos de {conceito}, abordando a história da arte urbana, a dimensão pública do muralismo, "
                "o uso de suportes alternativos e a relação entre arte e espaço urbano."
            ),
            "pratica": (
                f"Orientar o planejamento de um mural ou intervenção artística em papel (projeto/esboço), integrando desenhos, letras 3D ou lambe-lambes. "
                f"Solicitar {t_reg} focando na mensagem social ou poética que o grupo deseja transmitir."
            ),
            "pause": (
                f"Propor {t_verif} mediando a produção coletiva ou individual dos esboços, auxiliando na harmonia estética das letras e elementos visuais integrados."
            ),
            "encerramento": (
                f"Conduzir {t_sint} para socializar as propostas de murais, discutindo como a arte urbana ressignifica os espaços coletivos."
            )
        }

    if tipo == "arte_indigena":
        return {
            "para_comecar": (
                f"Apresentar um padrão de grafismo indígena, máscara ou objeto tradicional (como o Manto Tupinambá). "
                f"Propor {t_disc} para convidar a turma a pensar sobre o papel e significado desses objetos em sua cultura de origem."
            ),
            "foco": (
                f"Explicar os conceitos de {conceito}, valorizando a arte indígena (grafismo, cerâmica, adornos), sua importância cosmológica, "
                "simbólica e a diferença fundamental entre artesanato utilitário e arte sagrada."
            ),
            "pratica": (
                f"Propor a experimentação prática com argila, modelagem ou composição de grafismos geométricos utilizando materiais alternativos. "
                f"Solicitar {t_reg} no diário de bordo acompanhando a exploração tátil e visual dos estudantes."
            ),
            "pause": (
                f"Propor {t_verif} acompanhando o manuseio dos materiais e a aplicação das técnicas de modelagem, estimulando a criatividade e o respeito às técnicas tradicionais."
            ),
            "encerramento": (
                f"Conduzir {t_sint} reunindo as produções para debater sobre a repatriação de objetos históricos sagrados e "
                "a valorização da arte dos povos originários na cultura brasileira contemporânea."
            )
        }

    if tipo == "fotografia_composicao":
        return {
            "para_comecar": (
                f"Exibir imagens de enquadramentos fotográficos, gravuras ou obras clássicas de {tema}. "
                f"Propor {t_disc} estimulando a percepção de luz, sombra, cor e perspectiva que dão sensação de profundidade."
            ),
            "foco": (
                f"Apresentar {conceito}, abordando conceitos de enquadramento fotográfico, profundidade em gravura (como xilogravura), "
                "luz e sombra, e a representação tridimensional em superfícies bidimensionais."
            ),
            "pratica": (
                f"Orientar os estudantes em atividades de captura fotográfica na escola ou na criação de desenhos que simulem a técnica de gravura. "
                f"Solicitar {t_reg} estimulando a exploração do espaço e do enquadramento."
            ),
            "pause": (
                f"Propor {t_verif} orientando os estudantes nos ajustes de luz, enquadramento ou textura das composições."
            ),
            "encerramento": (
                f"Conduzir {t_sint} socializando as composições visuais ou fotografias, analisando como escolhas de enquadramento e iluminação transformam o olhar."
            )
        }

    if tipo == "exposicao_revisao":
        return {
            "para_comecar": (
                f"Apresentar a proposta de montagem de uma exposição colaborativa ou feira de trocas com as produções de {tema}. "
                f"Propor {t_disc} discutindo a importância de expor e partilhar produções artísticas com a comunidade."
            ),
            "foco": (
                f"Explicar os papéis da curadoria, expografia e mediação cultural em {conceito}, orientando os estudantes a pensar em como organizar "
                "o espaço para a exposição das obras."
            ),
            "pratica": (
                f"Organizar a montagem prática da exposição coletiva. Orientar a fixação das obras, a elaboração de etiquetas explicativas "
                f"e solicitar {t_reg} no diário de bordo sobre o trajeto e organização da visitação."
            ),
            "pause": (
                f"Propor {t_verif} mediando a curadoria do espaço para garantir visibilidade e respeito a todas as produções dos estudantes."
            ),
            "encerramento": (
                f"Conduzir {t_sint} realizando a apreciação coletiva das produções expostas, permitindo que a turma reflita criticamente sobre a jornada criativa vivenciada no bimestre."
            )
        }

    # Fallback / Geral
    return {
        "para_comecar": (
            f"Apresentar referências visuais ou sonoras relacionadas a {tema} para sensibilizar os estudantes. "
            f"Propor {t_disc} para colher as diferentes percepções iniciais da turma."
        ),
        "foco": (
            f"Explicar os conceitos centrais de {conceito}, contextualizando historicamente a linguagem artística em questão "
            "e integrando teoria e appreciation estética."
        ),
        "pratica": (
            f"Propor experimentação prática, criação ou apreciação orientada relacionada a {tema}. "
            f"Solicitar {t_reg} no diário de bordo socializando as produções ou percepções dos estudantes."
        ),
        "pause": (
            f"Propor {t_verif} acompanhando os processos individuais ou coletivos dos estudantes, mediando dúvidas estéticas e estimulando a autonomia."
        ),
        "encerramento": (
            f"Conduzir {t_sint} finalizando com um momento de reflexão coletiva sobre as produções ou discussões realizadas, "
            "valorizando a diversidade de olhares e leituras expressivas."
        )
    }


def _frases_por_contexto(
    perfil: str, tipo: str, tema: str, conceito: str,
    turma: str, tecnicas: dict, texto_base: str = "",
    atividade_extraida: str = "",
    recursos_detectados: list[str] | None = None,
    etapas_detectadas: list[str] | None = None,
    habilidade: str = "",
    contexto_geracao: dict | None = None,
) -> dict[str, str]:
    """Gera frases contextualizadas para cada etapa da metodologia."""

    t_disc = tecnicas.get("abertura", "Virem e conversem")
    t_reg = tecnicas.get("registro", "Todo mundo escreve")
    t_sint = tecnicas.get("sintese", "Com suas palavras")
    t_verif = tecnicas.get("verificacao", "Pause e responda")

    base = {
        "para_comecar": (
            f"Retomar conhecimentos prévios da turma sobre {tema}. Propor {t_disc} "
            "para levantar hipóteses, exemplos e dúvidas iniciais."
        ),
        "relembre": (
            f"Retomar os registros e conceitos ja trabalhados sobre {tema}, pedindo que a turma explique com suas palavras "
            "o que precisa ser lembrado para avancar na sequencia."
        ),
        "leitura": (
            "Realizar leitura guiada dos textos, imagens, comandos e/ou exemplos do material, fazendo pausas "
            "para destacar informações relevantes. Organizar no quadro as ideias principais e as palavras-chave "
            "que orientam a atividade."
        ),
        "hora_leitura": (
            f"Conduzir leitura orientada do texto-base sobre {tema}, fazendo pausas para destacar informacoes principais, "
            "vocabulario relevante, relacao entre linguagem verbal e nao verbal e pistas que sustentam a compreensao."
        ),
        "contextualizacao": (
            f"Contextualizar {tema} a partir de situações do cotidiano, repertórios culturais ou exemplos do "
            "material, ajudando a turma a compreender por que esse conteúdo é relevante e como ele circula "
            "socialmente."
        ),
        "leitura_analitica": (
            "Conduzir leitura analítica do texto, imagem, dado ou situação apresentada, destacando escolhas de "
            "linguagem, organização das ideias, pistas visuais e informações que sustentam a compreensão."
        ),
        "foco": (
            f"Analisar {conceito}, relacionando o conteúdo ao objetivo da aula. Explicar os pontos centrais de "
            "forma dialogada e verificar se a turma compreende as relações entre conceito, exemplo e atividade."
        ),
        "pratica": (
            f"Orientar a resolução das atividades propostas, usando {t_reg} para garantir registro "
            "individual. Circular pela sala, mediar dúvidas e solicitar justificativas para as respostas."
        ),
        "pause": (
            f"Socializar algumas respostas e realizar correção dialogada com {t_verif}, retomando trechos do "
            "material, registros dos estudantes e dúvidas comuns antes de avançar."
        ),
        "encerramento": (
            f"Finalizar com {t_sint}, retomando os aprendizados sobre {tema} e registrando uma síntese "
            "curta no quadro ou no caderno."
        ),
    }

    recurso_principal = _recurso_principal(recursos_detectados)
    _ajustar_por_recurso(base, recurso_principal, tema, atividade_extraida)

    # Ajustes por perfil
    if perfil == "ingles":
        _frases_ingles = _metodologia_ingles(texto_base, tema, tipo, conceito, atividade_extraida)
        if _frases_ingles is not None:
            base.update(_frases_ingles)
            return base

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        # Delegar para o gerador especializado de LP se o tipo for reconhecido
        perf_met = contexto_geracao.get("perfil_metodologico") if contexto_geracao else None
        tipo_a = contexto_geracao.get("tipo_aula", "simples") if contexto_geracao else "simples"
        _frases_lp = _metodologia_lingua_portuguesa(
            texto_base, tema, tipo, perfil_metodologico=perf_met, tipo_aula=tipo_a
        )
        if _frases_lp is not None:
            base.update(_frases_lp)
            return base

        # Fallback antigo para tipos não cobertos pelo gerador especializado
        if tipo == "producao":
            base["leitura"] = (
                "Apresentar a proposta de produção e realizar leitura guiada dos comandos, destacando finalidade, "
                "interlocutor, gênero textual e critérios de qualidade. Organizar no quadro um roteiro de planejamento."
            )
            base["foco"] = (
                f"Analisar as características do gênero relacionado a {tema}, observando estrutura, linguagem, "
                "organização das ideias e marcas que orientam a escrita."
            )
            base["pratica"] = (
                f"Orientar o planejamento, a escrita do rascunho e a revisão, solicitando {t_reg}. Solicitar que os estudantes confiram "
                "se o texto atende à finalidade, ao público e aos critérios combinados."
            )
        elif tipo == "argumentacao":
            base["foco"] = (
                f"Analisar tese, opinião, argumentos e estratégias persuasivas presentes em {conceito}. Destacar "
                "como escolhas de linguagem e exemplos ajudam a sustentar o ponto de vista."
            )
        else:
            base["foco"] = (
                f"Analisar {conceito}, destacando gênero, finalidade, público-alvo, recursos de linguagem e pistas "
                "textuais ou visuais que ajudam na compreensão."
            )

    elif perfil in {"orientacao_estudos"}:
        frases_orientacao = montar_frases_orientacao_estudos(tema, texto_base)
        base.update(frases_orientacao)
        if not frases_orientacao.get("_e_especifico", False):
            if recurso_principal == "producao_textual":
                base["foco"] = (
                    f"Retomar as caracteristicas da proposta relacionada a {tema}, mostrando como planejar a escrita, selecionar ideias "
                    "centrais e revisar o texto com base em criterios simples e visiveis."
                )
                base["pratica"] = (
                    "Organizar a atividade em planejamento, rascunho, revisao e versao final, com apoio do professor para transformar "
                    "os comandos do material em passos concretos de estudo e producao."
                )
            elif recurso_principal == "analise_grafico":
                base["foco"] = (
                    f"Explorar {conceito} ensinando a turma a ler titulo, legendas, linhas, colunas, valores e comparacoes antes de tirar conclusoes."
                )
                base["pratica"] = (
                    "Orientar a leitura dos dados em etapas, pedindo que os estudantes registrem o que observaram, comparem informacoes "
                    "e expliquem como chegaram as respostas."
                )
            elif recurso_principal == "analise_imagem":
                base["foco"] = (
                    f"Explorar {conceito} a partir da leitura de imagens, tirinhas, charges ou esquemas, ajudando a turma a descrever, "
                    "interpretar pistas visuais e relaciona-las ao texto verbal."
                )
            if "de olho no saeb" in normalizar_texto(texto_base):
                base["pratica"] += (
                    " Quando o material trouxer DE OLHO NO SAEB, conduzir a resolucao de forma guiada, explicando como ler "
                    "o enunciado, localizar pistas e revisar alternativas sem transformar a aula em treino mecanico."
                )

    elif perfil == "ciencias_ef":
            _frases_ciencias = _metodologia_ciencias(texto_base, tema, tipo, conceito, atividade_extraida)
            if _frases_ciencias is not None:
                base.update(_frases_ciencias)
                return base

    elif perfil == "biologia":
            _frases_biologia = _metodologia_biologia(texto_base, tema, tipo, conceito, atividade_extraida, habilidade)
            if _frases_biologia is not None:
                base.update(_frases_biologia)
                return base

    elif perfil == "historia":
            _frases_historia = _metodologia_historia(texto_base, tema, tipo, conceito, atividade_extraida)
            if _frases_historia is not None:
                base.update(_frases_historia)
                return base

    elif perfil in {"quimica", "fisica"}:
            base["para_comecar"] = (
                f"Contextualizar {tema} com uma situação-problema, imagem, dado ou exemplo do cotidiano. Propor "
                f"{t_disc} para que os estudantes antecipem explicações e levantem evidências."
            )
            base["foco"] = (
                f"Explicar {conceito} de forma progressiva, relacionando fenômeno, causa, consequência e exemplos. "
                "Usar esquemas no quadro para diferenciar observação, hipótese e conceito científico."
            )
            base["pratica"] = (
                f"Orientar leitura de texto, imagem, modelo ou atividade investigativa, solicitando {t_reg}. "
                "Retomar as evidências usadas pelos estudantes para justificar as respostas."
            )



    elif perfil == "geografia":
            base["foco"] = (
                f"Analisar {conceito} considerando paisagem, território, escala, localização e relações entre sociedade "
                "e natureza. Usar mapa, imagem, tabela ou gráfico como apoio para a explicação."
            )
            base["pratica"] = (
                f"Orientar leitura de mapas, imagens, gráficos ou situações-problema, solicitando {t_reg} para que os estudantes "
                "identifiquem elementos espaciais e expliquem relações de causa e consequência."
            )

    elif perfil == "arte":
        _frases_arte = _metodologia_arte(texto_base, tema, tipo, conceito, atividade_extraida, tecnicas)
        if _frases_arte is not None:
            base.update(_frases_arte)
            return base

    elif perfil == "ingles":
            base["para_comecar"] = (
                f"Retomar vocabulário conhecido relacionado a {tema} com repetição oral breve e exemplos no quadro. "
                "Estimular que os estudantes tentem pronunciar e reconhecer palavras antes da sistematização."
            )
            base["leitura"] = (
                "Apresentar o texto, diálogo, imagem ou situação comunicativa, alternando leitura em voz alta, escuta "
                "e repetição. Destacar vocabulário-chave e estruturas em inglês com apoio em exemplos."
            )
            base["foco"] = (
                f"Explorar o uso comunicativo de {conceito}, mostrando quando e como empregar as expressões estudadas. "
                "Registrar no quadro exemplos curtos em inglês e seus sentidos em contexto."
            )
            base["pratica"] = (
                f"Organizar prática oral e escrita em pares, com {t_reg} (repetição, preenchimento, pequenas respostas ou diálogos). "
                "Acompanhar pronúncia, compreensão e uso funcional das expressões."
            )

    elif perfil == "arte":
            base["foco"] = (
                f"Apresentar referências artísticas relacionadas a {conceito}, orientando apreciação de elementos visuais, "
                "sonoros, corporais ou culturais. Valorizar percepções diferentes sem reduzir a aula a explicação teórica."
            )
            base["pratica"] = (
                f"Propor experimentação, criação ou apreciação orientada, com {t_reg} no diário de bordo. Acompanhar "
                "processos criativos, escolhas dos estudantes e socialização das produções ou percepções."
            )

    elif perfil == "projeto_de_vida":
            _frases_pv = _metodologia_projeto_de_vida(texto_base, tema, tipo, conceito, atividade_extraida)
            if _frases_pv is not None:
                base.update(_frases_pv)
                return base

    elif perfil == "lideranca_oratoria":
            conceito_seguro = _conceito_projeto_vida(conceito, tema, texto_base, atividade_extraida)
            base["para_comecar"] = (
                f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. Propor "
                "troca em duplas ou roda de conversa breve, respeitando diferentes ritmos de participacao."
            )
            base["foco"] = (
                f"Construir a reflexao sobre {conceito_seguro} por meio de exemplos escolares e cotidianos, ajudando a turma a "
                "relacionar sentir, pensar e agir de forma respeitosa."
            )
            base["pratica"] = (
                "Orientar atividade reflexiva com registro individual, escolha pessoal ou planejamento simples. Garantir "
                "que a socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas."
            )
            base["encerramento"] = (
                f"Encerrar com um compromisso simples ou observacao para a semana, relacionado a {tema}, reforcando "
                "autonomia, respeito e cuidado nas relacoes."
            )

    elif perfil == "educacao_financeira":
            conceito_seguro = tema if normalizar_texto(conceito) in {"educacao financeira", "financeira"} else conceito
            situacoes = {
                "orcamento_planejamento": "uma situação de organização de renda, gastos e prioridades para cumprir uma meta simples",
                "consumo_consciente": "um dilema de consumo em que a turma precise comparar necessidade, desejo, preço, durabilidade e impacto da escolha",
                "investimento_poupanca": "uma situação de poupança ou reserva de emergência em que pequenos valores acumulados ajudam a lidar com imprevistos",
                "credito_endividamento": "uma compra parcelada ou oferta de crédito em que seja necessário comparar valor à vista, juros, parcelas e custo total",
                "empreendedorismo": "um pequeno projeto de venda, serviço ou solução para a comunidade escolar, analisando custos, preço e viabilidade",
                "analise_percentuais_noticias": "uma noticia, manchete ou grafico em que a turma precise interpretar percentuais e relacionar os dados a uma situacao real",
                "governo_economia": "uma situacao cotidiana sobre como a acao do governo influencia precos, servicos, impostos e a vida economica da populacao",
                "impacto_decisoes_economicas": "uma situacao do cotidiano em que escolhas economicas afetam consumo, planejamento, prioridades e bem-estar",
                "cidadania_financeira": "uma situação de consumo que envolva direitos, responsabilidades, comprovantes, garantia ou uso seguro de serviços financeiros",
                "instituicoes_financeiras": "uma situação cotidiana sobre onde guardar, movimentar e proteger o dinheiro com segurança",
            }
            situacao = situacoes.get(tipo, f"uma situação financeira real relacionada a {tema}")
            base["retomada_conceitual"] = (
                f"Retomar brevemente os conceitos e os registros da aula anterior sobre {tema} para garantir a base necessária para as atividades de hoje."
            )
            base["contextualizacao_pratica"] = (
                f"Apresentar o foco prático do dia ligado a {tema}, explicando como aplicar os conceitos em um cenário de tomada de decisão ou simulação financeira."
            )
            base["atividade_central"] = (
                f"Orientar os estudantes na realização da atividade prática do material, como elaborar tabelas, simular gastos, realizar pesquisas ou comparar alternativas em duplas ou individualmente."
            )
            base["encerramento_reflexivo"] = (
                f"Conduzir uma reflexão rápida sobre as escolhas feitas na atividade, estimulando a socialização das conclusões financeiras e das estratégias utilizadas."
            )
            base["para_comecar"] = (
                f"Apresentar {situacao}, sem exigir relatos pessoais nem julgamentos sobre hábitos financeiros familiares. "
                "Convidar os estudantes a levantar hipóteses sobre escolhas, riscos, prioridades e consequências antes da sistematização."
            )
            base["analise_caso"] = (
                f"Conduzir a análise do caso ligado a {tema}, identificando dados importantes, alternativas possíveis, "
                "critérios de decisão e consequências de curto e longo prazo. Registrar no quadro as perguntas que ajudam a decidir com responsabilidade."
            )
            base["foco"] = (
                f"Desenvolver {conceito_seguro} de forma contextualizada, relacionando o conceito a situações reais de consumo, "
                "planejamento, poupança, crédito ou organização de recursos. Explicar o vocabulário financeiro necessário e construir critérios claros para a tomada de decisão."
            )
            base["pause"] = (
                "Promover uma pausa para que a turma compare alternativas, justifique escolhas e avalie impactos financeiros, "
                "retomando dados do material e dúvidas comuns antes de seguir para a aplicação."
            )
            base["calculos"] = (
                "Orientar cálculos financeiros de forma guiada, destacando dados, operações, porcentagens, juros, parcelas, saldo ou custo total conforme o material. "
                "Relacionar cada resultado numérico a uma decisão possível, evitando que a atividade fique apenas mecânica."
            )
            base["planejamento"] = (
                "Orientar a elaboração ou análise de um planejamento financeiro simulado, organizando receita, despesas, prioridades, metas e saldo. "
                "Acompanhar os registros para que os estudantes expliquem os critérios usados nas escolhas."
            )
            base["simulacao"] = (
                "Organizar uma simulação financeira ou análise de alternativas, aplicando os critérios construídos na aula para escolher, comparar, planejar ou revisar uma decisão. "
                "Solicitar registro de cálculos, justificativas e possíveis consequências."
            )
            base["projeto"] = (
                "Orientar a organização de um projeto empreendedor simples, levantando recursos necessários, custos, preço, público, viabilidade e cuidados éticos. "
                "Solicitar que os estudantes justifiquem as decisões tomadas no planejamento."
            )
            base["pratica"] = (
                "Orientar a resolução das atividades do material com registro individual ou em dupla, acompanhando leitura de dados, comparação de alternativas e justificativa das decisões. "
                "Retomar vocabulário financeiro e critérios de escolha sempre que surgirem dúvidas."
            )

            if tipo == "orcamento_planejamento":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} como estratégia de organização financeira, relacionando receitas, despesas, gastos, prioridades e metas. "
                    "Construir com a turma critérios para controlar recursos e ajustar escolhas conforme limites e objetivos."
                )
                base["pratica"] = base["planejamento"]
            elif tipo == "consumo_consciente":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} a partir de critérios de consumo consciente, diferenciando necessidade, desejo, prioridade, custo-benefício e impacto da escolha. "
                    "Evitar tom moralista e conduzir a análise com base em argumentos, dados e consequências."
                )
            elif tipo == "investimento_poupanca":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} relacionando poupança, reserva, rendimento, constância e planejamento de metas. "
                    "Mostrar como a organização dos recursos ajuda a lidar com imprevistos e objetivos de curto ou longo prazo."
                )
                base["pratica"] = base["simulacao"]
            elif tipo == "credito_endividamento":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} com foco no uso responsável do crédito, analisando juros, parcelas, custo total, riscos de endividamento e critérios para decidir. "
                    "Comparar alternativas sem estimular consumo, priorizando avaliação crítica e planejamento."
                )
                base["pratica"] = base["simulacao"]
            elif tipo == "empreendedorismo":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} articulando oportunidade, necessidade, produto ou serviço, custos, preço, lucro e viabilidade. "
                    "Relacionar a proposta a planejamento, responsabilidade e análise do contexto."
                )
                base["pratica"] = base["projeto"]
            elif tipo == "analise_percentuais_noticias":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} por meio da leitura de noticias, manchetes, tabelas e graficos, ajudando a turma a interpretar percentuais, "
                    "comparar dados e perceber como os numeros influenciam a compreensao dos fatos."
                )
                base["calculos"] = (
                    "Orientar calculos de porcentagem e comparacao de variacoes com apoio do quadro, destacando o significado de cada dado antes do procedimento numerico. "
                    "Retomar passo a passo como localizar o valor de referencia, calcular percentuais e interpretar o resultado no contexto da noticia analisada."
                )
                base["pratica"] = (
                    "Propor leitura guiada de noticias ou situacoes semelhantes, seguida de registros no caderno com interpretacao dos percentuais, comparacao de informacoes "
                    "e justificativa sobre o que os dados revelam."
                )
            elif tipo == "governo_economia":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} relacionando arrecadacao, servicos publicos, regulacao e impactos economicos no cotidiano. "
                    "Conduzir a turma a perceber como decisoes do governo interferem em precos, circulacao de dinheiro e acesso a direitos."
                )
                base["pratica"] = (
                    "Orientar a analise de exemplos concretos, comparando situacoes em que a acao do governo influencia consumo, trabalho, precos ou servicos. "
                    "Solicitar registros curtos com explicacao das relacoes observadas."
                )
            elif tipo == "impacto_decisoes_economicas":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} por meio de escolhas economicas do cotidiano, relacionando recursos disponiveis, prioridades, consumo e consequencias de curto e longo prazo. "
                    "Estimular a turma a comparar alternativas com base em criterios claros e realistas."
                )
                base["pratica"] = (
                    "Propor situacoes-problema simples para que os estudantes comparem escolhas, antecipem impactos e justifiquem decisoes com base nos dados apresentados. "
                    "Retomar o vocabulario financeiro necessario sempre que surgirem duvidas."
                )
            elif tipo == "cidadania_financeira":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} relacionando direitos do consumidor, responsabilidades, segurança, comprovantes, garantias e autonomia nas decisões financeiras. "
                    "Orientar a turma a identificar formas de proteção e uso consciente de serviços financeiros."
                )
            elif tipo == "instituicoes_financeiras":
                base["foco"] = (
                    f"Desenvolver {conceito_seguro} explicando a função das instituições financeiras na guarda, movimentação, controle e proteção do dinheiro. "
                    "Comparar exemplos como banco, conta digital, poupança e outros serviços, destacando segurança e planejamento."
                )

            base["encerramento"] = (
                f"Sintetizar os aprendizados financeiros relacionados a {tema}, retomando critérios de decisão, organização e responsabilidade. "
                "Propor um fechamento com planejamento de aplicação no cotidiano, sem solicitar exposição de informações financeiras pessoais."
            )

    elif perfil == "tecnologia_inovacao":
            base["para_comecar"] = (
                f"Ativar os conhecimentos previos da turma sobre {tema}, retomando exemplos do cotidiano escolar e digital que ajudem a dar sentido ao conteudo."
            )
            base["leitura"] = (
                "Realizar leitura guiada dos slides, explicando vocabulario, comandos, funcoes e exemplos de forma pausada, com registro no quadro das ideias principais."
            )
            base["foco"] = (
                f"Explorar {conceito} de forma concreta, relacionando o funcionamento da tecnologia, os usos no cotidiano e as escolhas dos estudantes durante a aula."
            )
            base["pause"] = (
                "Promover perguntas rapidas para verificar a compreensao, retomar respostas da turma e corrigir coletivamente possiveis duvidas antes da atividade principal."
            )
            base["pratica"] = (
                f"Orientar a atividade pratica com {t_reg}, acompanhando leitura dos comandos, organizacao dos registros e execucao passo a passo."
            )
            base["encerramento"] = (
                f"Retomar os aprendizados sobre {tema}, socializar algumas respostas ou producoes da turma e finalizar com uma sintese simples sobre o que foi descoberto na aula."
            )

            if tipo == "dispositivos_entrada_saida":
                base["para_comecar"] = (
                    f"Ativar os conhecimentos previos da turma sobre {tema}, convidando os estudantes a observar os equipamentos tecnologicos presentes na escola e a dizer para que servem."
                )
                base["foco"] = (
                    "Explorar a diferenca entre dispositivos de entrada e de saida, classificando coletivamente exemplos como teclado, mouse, microfone, camera, monitor, impressora, projetor e caixa de som."
                )
                base["pratica"] = (
                    f"Orientar a classificacao dos dispositivos em colunas ou esquemas com {t_reg}, acompanhando as justificativas dos estudantes sobre a funcao de cada equipamento."
                )
            elif tipo == "programacao_inicial":
                base["para_comecar"] = (
                    f"Retomar situacoes em que o teclado, o mouse ou botoes de inicio sao usados para dar comandos, conectando o tema {tema} a experiencias proximas da turma."
                )
                base["foco"] = (
                    "Explicar o uso do teclado e dos comandos iniciais de programacao no StartLab, destacando teclas importantes, a bandeira verde, blocos de eventos e o bloco diga como formas de criar mensagens interativas."
                )
                base["pratica"] = (
                    f"Orientar a montagem de comandos simples no ambiente de programacao com {t_reg}, demonstrando uma etapa no quadro ou projetor e acompanhando a execucao individual ou em dupla."
                )
            elif tipo == "cultura_digital":
                base["para_comecar"] = (
                    f"Ativar os conhecimentos previos sobre {tema}, comparando formas antigas e atuais de comunicacao e incentivando a turma a pensar sobre convivencia nos ambientes digitais."
                )
                base["foco"] = (
                    "Explorar atitudes respeitosas e inadequadas na internet, relacionando emocoes, convivencia online, responsabilidade e cuidado nas interacoes digitais."
                )
                base["pratica"] = (
                    f"Orientar a analise de situacoes do cotidiano digital com {t_reg}, acompanhando a construcao de regras, exemplos e propostas de convivencia respeitosa."
                )
            elif tipo == "comunicacao_digital":
                base["para_comecar"] = (
                    f"Apresentar uma situacao de duvida ou mensagem pouco clara relacionada a {tema}, convidando a turma a identificar por que a comunicacao nao funcionou."
                )
                base["foco"] = (
                    "Explorar como fazer perguntas claras, objetivas, respeitosas e completas em ambientes digitais, mostrando quais informacoes ajudam a receber respostas mais precisas."
                )
                base["pratica"] = (
                    f"Orientar a reescrita de perguntas e mensagens com {t_reg}, usando modelos simples no quadro e acompanhando a organizacao das informacoes pelos estudantes."
                )
            elif tipo == "consumo_tecnologia":
                base["para_comecar"] = (
                    f"Apresentar um exemplo do cotidiano relacionado a {tema}, como celular, fone, carregador ou televisao, para provocar a reflexao sobre durabilidade, descarte e consumo."
                )
                base["foco"] = (
                    "Explicar o conceito de obsolescencia programada e relaciona-lo ao lixo eletronico, ao consumo excessivo e a necessidade de escolhas mais conscientes no uso da tecnologia."
                )
                base["pratica"] = (
                    f"Orientar a producao de listas, cartazes, campanhas ou propostas de solucao com {t_reg}, acompanhando a formulacao de dicas viaveis de consumo consciente e descarte correto."
                )

    elif perfil == "sociologia":
            base["para_comecar"] = (
                f"Apresentar um fenômeno social ligado a {tema} por meio de situação, imagem, dado ou relato, "
                "provocando estranhamento e questionamentos iniciais."
            )
            base["foco"] = (
                f"Analisar {conceito} sociologicamente, articulando teoria, conceitos e exemplos da realidade social "
                "para superar leituras baseadas apenas no senso comum."
            )

    return base


class MotorMetodologico:
    """Motor unificado de geração de metodologia sem IA."""

    def __init__(self):
            self.extrator = _extrator
            self.validador = ValidadorQualidade()
            self.seletor = _seletor_tecnicas

    def gerar(
            self,
            texto_pdf: str,
            disciplina: str,
            turma: str,
            tema: str,
            indice_aula: int = 0,
            total_aulas: int = 1,
            contexto_geracao: dict | None = None,
    ) -> list[dict]:
            """
            Gera metodologia completa com etapas variáveis por perfil.

            Usa o motor sofisticado (equivalente ao _montar_etapas_metodologia
            do lote.py) em vez do motor fraco do inteligencia_local.py.
            """
            # 1. Classificar
            perfil = perfil_disciplina(disciplina, turma=turma)
            tipo = detectar_tipo_aula(texto_pdf, tema, disciplina, turma=turma)

            # 2. Extrair conceito
            extracao = self.extrator.extrair(texto_pdf, tema)
            conceito = extracao["conceito_extraido"]
            atividade = extracao.get("atividade_extraida", "")
            recursos = extracao.get("recursos_detectados", [])
            etapas_pdf = extracao.get("etapas_detectadas", [])
            habilidade = extracao.get("habilidade", "")

            # 3. Selecionar técnicas com variação
            tecnicas = self.seletor.selecionar_para_aula(perfil, tipo, tema, indice_aula)

            # 4. Gerar frases contextualizadas
            frases = _frases_por_contexto(
                perfil,
                tipo,
                tema,
                conceito,
                turma,
                tecnicas,
                texto_pdf,
                atividade_extraida=atividade,
                recursos_detectados=recursos,
                etapas_detectadas=etapas_pdf,
                habilidade=habilidade,
                contexto_geracao=contexto_geracao,
            )

            # 5. Montar etapas
            etapas_config = _etapas_por_perfil(perfil, tipo, contexto_geracao=contexto_geracao)
            metodologia = []
            for titulo, chave in etapas_config:
                texto_etapa = frases.get(chave, "").strip()
                if texto_etapa:
                    # Aplicar progressão entre aulas
                    texto_etapa = ajustar_texto_por_posicao(
                        texto_etapa, indice_aula, total_aulas, tema
                    )
                    metodologia.append({"titulo": titulo, "texto": texto_etapa})

            # 6. Validar
            return self.validador.refinar(metodologia)

    def extrair_dados(self, texto_pdf: str, tema: str) -> dict:
            """Expõe a extração de dados para uso por outros módulos."""
            return self.extrator.extrair(texto_pdf, tema)
