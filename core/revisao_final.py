import hashlib
import json
import re
from pathlib import Path
from config import BASE_DIR

from core.qualidade_metodologica import extrair_conceito_central
from core.listas_pedagogicas import (
    itens_lista_pedagogica,
    problemas_lista_exatamente_tres,
)
from core.validador_plano import validar_aula_final, calcular_aderencia_pdf

VERSAO_GERADOR_ATUAL = "1.2.9"


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

def revisar_aula_gerada(aula: dict, perfil: str) -> dict:
    """
    Executa a auditoria pedagógica final e atribui um score de qualidade (confidence_score).
    """
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
    if avisos_aderencia:
        # Se for muito baixa, puxamos a nota final pra baixo com força
        # penalizando 10 pontos fixos + a diferença percentual abaixo de 80
        penalidade = 10 + (80 - aderencia)
        deducoes += penalidade
        avisos.extend(avisos_aderencia)

    # 7. Atualizar dicionário
    aula["confidence_score"] = int(max(0, 100 - deducoes))
    
    # Travar máximo em 75% caso tenha falhado fortemente na aderência
    if aderencia < 80:
        aula["confidence_score"] = min(aula["confidence_score"], 75)
        
    aula["avisos_validacao"] = sorted(list(set(avisos)))
    aula["versao_gerador"] = VERSAO_GERADOR_ATUAL
    aula["perfil"] = perfil
    return aula

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


def gravar_sidecar_json(caminho_pdf: str | Path, aula: dict, hash_pdf: str) -> Path | None:
    """Grava o arquivo JSON do plano de aula ao lado do PDF correspondente contendo metadados de auditoria."""
    if not caminho_pdf:
        return None

    try:
        caminho_json = Path(caminho_pdf).with_suffix(".json")
        dados_salvar = {
            "disciplina": aula.get("disciplina") or "",
            "tema": aula.get("tema") or "",
            "material": aula.get("material") or Path(caminho_pdf).name,
            "numero_aula": aula.get("numero_aula") or "",
            "aprendizagem": aula.get("aprendizagem") or "",
            "metodologia": aula.get("metodologia") or [],
            "acompanhamento": aula.get("acompanhamento") or [],
            "acessibilidade": aula.get("acessibilidade") or [],
            "ia_usada": aula.get("ia_usada", False),
            "ia_provedor": aula.get("ia_provedor") or "",
            "ia_erro": aula.get("ia_erro") or "",
            "fonte_extracao": aula.get("fonte_extracao") or "pdf",
            "arquivo_fonte_extracao": _normalizar_caminho_relativo(aula.get("arquivo_fonte_extracao") or caminho_pdf),
            "hash_fonte_extracao": aula.get("hash_fonte_extracao") or hash_pdf,
            "fonte_principal": aula.get("fonte_principal") or aula.get("fonte_extracao") or "pdf",
            "arquivo_fonte": _normalizar_caminho_relativo(aula.get("arquivo_fonte") or aula.get("arquivo_fonte_extracao") or caminho_pdf),
            "cache_reutilizado": bool(aula.get("cache_reutilizado", False)),
            "origem_metodologia": aula.get("origem_metodologia") or "",
            "fonte_referencia_metodologia": _normalizar_caminho_relativo(aula.get("fonte_referencia_metodologia") or ""),
            "perfil_metodologico": aula.get("perfil_metodologico") or "",
            "versao_prompt": aula.get("versao_prompt") or "",
            "etapas_detectadas": aula.get("etapas_detectadas") or [],
            # Metadados de auditoria e integridade
            "hash_pdf": hash_pdf,
            "confidence_score": aula.get("confidence_score", 100),
            "avisos_validacao": aula.get("avisos_validacao") or [],
            "versao_gerador": aula.get("versao_gerador", VERSAO_GERADOR_ATUAL),
            "perfil": aula.get("perfil") or "",
            "fingerprint_contexto": aula.get("fingerprint_contexto") or "",
            "recursos_detectados": aula.get("recursos_detectados") or [],
            "texto_fonte": aula.get("texto_fonte") or "",
            "diagnostico_geracao": aula.get("diagnostico_geracao") or {},
        }
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(dados_salvar, f, ensure_ascii=False, indent=2)
        return caminho_json
    except Exception:
        return None
