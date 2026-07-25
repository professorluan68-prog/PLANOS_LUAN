import hashlib
import json
import logging
from core.referencias_metodologia import get_titulos_proibidos
from core.lib.classificador import normalizar_texto
import re
from pathlib import Path
from config import BASE_DIR

from core.qualidade_metodologica import extrair_conceito_central
from core.listas_pedagogicas import (
    itens_lista_pedagogica,
    problemas_lista_exatamente_tres,
)
from core.models import PlanoCompleto
from core.validador_plano import validar_aula_final, calcular_aderencia_pdf

VERSAO_GERADOR_ATUAL = "1.2.13"

# CORREÇÃO FALHA #8 — Score mínimo aceitável para entrega sem regeneração
SCORE_MINIMO_ACEITAVEL = 70

logger = logging.getLogger(__name__)

_LIMITES_CHARS_POR_ETAPA = {
    "historia": 300,
    "geografia": 300,
    "lingua_portuguesa": 300,
    "lingua_portuguesa_ef": 300,
    "lingua_portuguesa_em": 300,
    "leitura_redacao": 300,
    "redacao": 300,
}
_LIMITE_CHARS_DEFAULT = 300


def _limpar_tema_final(tema: str) -> str:
    texto = extrair_conceito_central(str(tema or "").strip())
    if not texto:
        return ""
    texto = re.sub(
        r"^(?:da\s+natureza|ciencias?\s+da\s+natureza)\b\s*[-:\u2013\u2014]?\s*",
        "",
        texto,
        flags=re.I,
    )
    return texto.strip(" ,;:-")


def calcular_sha256(caminho_pdf: str | Path) -> str:
    """Calcula o hash SHA-256 de um arquivo PDF para validação de integridade do cache."""
    sha256 = hashlib.sha256()
    try:
        with open(caminho_pdf, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""


def _titulo_etapa(item) -> str:
    if isinstance(item, dict):
        return str(item.get("titulo") or "").strip()
    return str(getattr(item, "titulo", "") or "").strip()


def _texto_etapa(item) -> str:
    if isinstance(item, dict):
        return str(item.get("texto") or "").strip()
    if isinstance(item, str):
        return item.strip()
    return str(getattr(item, "texto", "") or "").strip()


def _validar_titulos_proibidos(metodologia, perfil: str) -> tuple[int, list[str]]:
    avisos = []
    deducoes = 0
    titulos_proibidos = set(get_titulos_proibidos(perfil) or [])
    if not titulos_proibidos:
        return deducoes, avisos

    for item in metodologia or []:
        titulo = _titulo_etapa(item)
        if not titulo:
            continue
        titulo_norm = normalizar_texto(titulo).lower().strip()
        if titulo_norm in titulos_proibidos:
            deducoes += 10
            avisos.append(f"Etapa '{titulo}': título incompatível com o perfil {perfil}.")
    return deducoes, avisos


def _validar_tamanho_etapas(metodologia, perfil: str) -> tuple[int, list[str]]:
    avisos = []
    deducoes = 0
    limite = _LIMITES_CHARS_POR_ETAPA.get(perfil, _LIMITE_CHARS_DEFAULT)

    for item in metodologia or []:
        texto = _texto_etapa(item)
        titulo = _titulo_etapa(item) or "Etapa sem título"
        if not texto:
            deducoes += 5
            avisos.append(f"Etapa '{titulo}': texto vazio.")
            continue
        if len(texto) > limite:
            deducoes += 5
            avisos.append(
                f"Etapa '{titulo}': excede o limite de {limite} caracteres para o perfil {perfil}."
            )
    return deducoes, avisos

def revisar_aula_gerada(
    aula: dict | PlanoCompleto, 
    perfil: str,
    _max_regeneracoes: int = 1
) -> dict:
    """
    Executa a auditoria pedagógica final e atribui um score de qualidade (confidence_score).
    """
    aula = PlanoCompleto.from_any(aula).to_dict()
    tentativas_regeneracao = aula.get("_tentativas_regeneracao", 0)
    avisos = []
    deducoes = 0

    # 1. Validar Tema e Aprendizagem
    tema = _limpar_tema_final(aula.get("tema") or "")
    aula["tema"] = tema
    if not tema:
        deducoes += 30
        avisos.append("Tema não identificado.")

    aprendizagem = str(aula.get("aprendizagem") or "").strip()
    if not aprendizagem:
        deducoes += 30
        avisos.append("Campo de aprendizagem vazio.")

    # 2. Validar Metodologia
    metodologia = aula.get("metodologia") or []
    if len(metodologia) < 3:
        deducoes += 15
        avisos.append("Metodologia com poucas etapas.")

    ded_titulos, avisos_titulos = _validar_titulos_proibidos(metodologia, perfil)
    if ded_titulos:
        deducoes += ded_titulos
        avisos.extend(avisos_titulos)

    ded_tamanho, avisos_tamanho = _validar_tamanho_etapas(metodologia, perfil)
    if ded_tamanho:
        deducoes += ded_tamanho
        avisos.extend(avisos_tamanho)

    # 3. Validar Acompanhamento da Aprendizagem
    acompanhamento = aula.get("acompanhamento") or []
    itens_acompanhamento = itens_lista_pedagogica(acompanhamento)
    problemas_acompanhamento = problemas_lista_exatamente_tres(
        "Acompanhamento da aprendizagem",
        itens_acompanhamento,
    )
    if problemas_acompanhamento:
        deducoes += 15
        avisos.extend(problemas_acompanhamento)

    # 4. Validar Acessibilidade e detectar placeholders
    acessibilidade = aula.get("acessibilidade") or []
    itens_acessibilidade = itens_lista_pedagogica(acessibilidade)
    problemas_acessibilidade = problemas_lista_exatamente_tres(
        "Acessibilidade",
        itens_acessibilidade,
    )
    if problemas_acessibilidade:
        deducoes += 15
        avisos.extend(problemas_acessibilidade)

    for item in itens_acessibilidade:
        # Detecta o placeholder específico "informação do material simples"
        if "informação do material simples" in item.lower() or "informacao do material simples" in item.lower():
            deducoes += 20
            avisos.append("Placeholder residual em acessibilidade: 'informação do material simples'.")
            break

    # 5. Executar as validações semânticas centrais de validar_aula_final()
    avisos_semanticos = validar_aula_final(aula) or []
    for aviso in avisos_semanticos:
        deducoes += 10
        avisos.append(aviso)

    # 6. Calcular aderência lexical ao PDF (Alerte e puna se < 80%)
    aderencia, avisos_aderencia = calcular_aderencia_pdf(aula)
    if aderencia < 80:
        penalidade = max(1, int(80 - aderencia))
        deducoes += penalidade
        if avisos_aderencia:
            avisos.extend(avisos_aderencia)

    # 6.5. Validar aderência de palavras-chave destacadas em amarelo (DOCX)
    palavras_chave_esperadas = aula.get("palavras_chave_esperadas") or []
    origem_metodologia = aula.get("origem_metodologia", "")
    pdf_requer_validacao = "pdf" in origem_metodologia.lower()

    if palavras_chave_esperadas:
        from core.validador_plano import validar_aderencia_palavras_chave
        resultado_pc = validar_aderencia_palavras_chave(aula, palavras_chave_esperadas)
        aula["valido_palavras_chave"] = resultado_pc["valido"]
        aula["cobertura_palavras_chave"] = resultado_pc["cobertura"]
        aula["palavras_chave_encontradas"] = resultado_pc["palavras_encontradas"]
        aula["palavras_chave_ausentes"] = resultado_pc["palavras_ausentes"]
        
        if not resultado_pc["valido"]:
            taxa = resultado_pc["cobertura"]
            penalidade_pc = max(1, int(100 - taxa))
            deducoes += penalidade_pc
            avisos.append(
                f"Aderência de palavras-chave baixa ({taxa:.1f}%). "
                f"As seguintes palavras-chave obrigatórias estão ausentes: {', '.join(resultado_pc['palavras_ausentes'][:8])}."
            )
    elif pdf_requer_validacao and not aula.get("extracao_palavras_chave_ok", True):
        avisos.append("ATENÇÃO: Extração de palavras-chave falhou. Verifique o material original.")
        deducoes += 10

    # 7. Atualizar dicionário
    aula["confidence_score"] = int(max(0, 100 - deducoes))
    
    # CORREÇÃO FALHA #8 — Regeneração seletiva quando score < mínimo aceitável
    if (
        aula["confidence_score"] < SCORE_MINIMO_ACEITAVEL
        and tentativas_regeneracao < _max_regeneracoes
        and not aula.get("texto_central_copiado_literalmente", False)
    ):
        etapas_problematicas = _identificar_etapas_com_aviso(avisos)
        if etapas_problematicas and perfil == "historia":
            aula_corrigida = _regenerar_etapas_historia(aula, etapas_problematicas)
            if aula_corrigida:
                aula_corrigida["_tentativas_regeneracao"] = tentativas_regeneracao + 1
                logger.info(f"Regeneração seletiva: tentativa {tentativas_regeneracao + 1}/{_max_regeneracoes}")
                return revisar_aula_gerada(aula_corrigida, perfil, _max_regeneracoes)

    aula["avisos_validacao"] = sorted(list(set(avisos)))
    aula["versao_gerador"] = VERSAO_GERADOR_ATUAL
    aula["perfil"] = perfil
    # Limpar campo interno de controle
    aula.pop("_tentativas_regeneracao", None)
    return PlanoCompleto.from_any(aula).to_dict()


def _identificar_etapas_com_aviso(avisos: list[str]) -> list[str]:
    """
    CORREÇÃO FALHA #8 — Extrai os nomes das etapas mencionadas nos avisos de validação.
    Ex: "Etapa 'Encerramento': não descreve..." → "Encerramento"
    """
    etapas = set()
    for aviso in avisos:
        match = re.search(r"Etapa '([^']+)'", aviso)
        if match:
            etapas.add(match.group(1))
    return sorted(etapas)


def _regenerar_etapas_historia(aula: dict, etapas_problematicas: list[str]) -> dict | None:
    from core.qualidade_metodologica import extrair_conceito_central

    metodologia = aula.get("metodologia") or []
    tema = aula.get("tema", "")
    houve_correcao = False

    titulos_proibidos = get_titulos_proibidos("historia")
    metodologia_limpa = []
    for etapa in metodologia:
        if not isinstance(etapa, dict):
            metodologia_limpa.append(etapa)
            continue
        titulo_norm = normalizar_texto(_titulo_etapa(etapa)).lower().strip()
        if titulo_norm in titulos_proibidos:
            logger.info(
                "Regeneração: etapa proibida '%s' removida da metodologia de História.",
                _titulo_etapa(etapa),
            )
            houve_correcao = True
        else:
            metodologia_limpa.append(etapa)

    metodologia = metodologia_limpa

    for idx, etapa in enumerate(metodologia):
        if not isinstance(etapa, dict):
            continue
        titulo = str(etapa.get("titulo", "")).strip()
        titulo_lower = titulo.lower()

        if titulo_lower == "encerramento" and "Encerramento" in etapas_problematicas:
            texto_atual = str(etapa.get("texto", "")).strip()
            termos_genericos = [
                "momento de síntese",
                "verificação dos aprendizados",
                "expressam o que compreenderam",
                "síntese coletiva",
                "retomada dos principais",
            ]
            is_generico = any(t in texto_atual.lower() for t in termos_genericos)
            is_curto = len(texto_atual) < 80

            if is_generico or is_curto:
                conceito = extrair_conceito_central(tema) or tema or "o conteúdo da aula"
                novo_texto = (
                    f'Para encerrar a aula, os alunos refletem e respondem "COM SUAS PALAVRAS" '
                    f"sobre as perguntas finais relacionadas a {conceito}, "
                    f"consolidando os principais conceitos trabalhados e registrando suas conclusões no caderno."
                )
                metodologia[idx] = {"titulo": titulo, "texto": novo_texto}
                houve_correcao = True
                logger.info("Encerramento genérico substituído por versão específica com COM SUAS PALAVRAS.")

        elif titulo_lower == "para começar" and "Para começar" in etapas_problematicas:
            texto_atual = str(etapa.get("texto", "")).strip()
            conceito = extrair_conceito_central(tema) or tema
            if conceito and conceito.lower() not in texto_atual.lower():
                novo_texto = texto_atual.rstrip(". ") + f", contextualizando o tema {conceito}."
                metodologia[idx] = {"titulo": titulo, "texto": novo_texto}
                houve_correcao = True

    if houve_correcao:
        aula["metodologia"] = metodologia
        return aula
    return None

def _normalizar_caminho_relativo(caminho) -> str:
    """Normaliza um caminho absoluto para que seja relativo ao BASE_DIR se possível."""
    if not caminho:
        return ""
    try:
        caminho_abs = Path(caminho).resolve()
        base_abs = Path(BASE_DIR).resolve()
        return str(caminho_abs.relative_to(base_abs))
    except (ValueError, TypeError, AttributeError):
        return str(caminho)


def gravar_sidecar_json(
    caminho_pdf: str | Path,
    aula: dict | PlanoCompleto,
    hash_pdf: str,
) -> Path | None:
    """Grava o arquivo JSON do plano de aula ao lado do PDF correspondente contendo metadados de auditoria."""
    if not caminho_pdf:
        return None

    try:
        caminho_json = Path(caminho_pdf).with_suffix(".json")
        plano = PlanoCompleto.from_any(aula)
        if not plano.versao_gerador:
            plano.versao_gerador = VERSAO_GERADOR_ATUAL
        dados_salvar = plano.to_sidecar_dict(
            caminho_pdf,
            hash_pdf,
            normalizar_caminho=_normalizar_caminho_relativo,
        )
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(dados_salvar, f, ensure_ascii=False, indent=2)
        return caminho_json
    except Exception:
        return None
