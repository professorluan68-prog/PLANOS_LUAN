from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.lib.classificador import perfil_disciplina
from core.validador_plano import validar_aula_final

@dataclass
class ResultadoReusoCachePlano:
    aula_reutilizada: dict | None
    dados_json_antigos: dict | None


def _montar_aula_reutilizada(
    *,
    dados_json: dict,
    disciplina: str,
    hash_atual: str,
    perfil_metodologico: str,
    tema_cache: str,
    material_cache: str,
    numero_cache: str,
    aprendizagem_cache: str,
    metodologia_cache,
    acompanhamento_cache,
    acessibilidade_cache,
    fonte_cache: str,
    arquivo_cache: str,
    hash_fonte_salva: str,
    fingerprint_salvo,
    fingerprint_resultado: str,
    assinatura_conteudo_cache: str,
    versao_cache: str,
    origem_metodologia_cache: str,
    fonte_referencia_cache: str,
    perfil_resultado: str,
    reutilizacao_por_conteudo: bool,
) -> dict:
    aula_gerada = {
        "disciplina": dados_json.get("disciplina") or disciplina,
        "tema": tema_cache,
        "material": material_cache,
        "numero_aula": numero_cache,
        "aprendizagem": aprendizagem_cache,
        "metodologia": metodologia_cache,
        "acompanhamento": acompanhamento_cache,
        "acessibilidade": acessibilidade_cache,
        "ia_usada": dados_json.get("ia_usada", False),
        "ia_provedor": dados_json.get("ia_provedor", ""),
        "ia_erro": dados_json.get("ia_erro", ""),
        "hash_pdf": dados_json.get("hash_pdf") or hash_atual,
        "fonte_extracao": fonte_cache,
        "arquivo_fonte_extracao": arquivo_cache,
        "hash_fonte_extracao": hash_fonte_salva,
        "confidence_score": dados_json.get("confidence_score", 100),
        "avisos_validacao": dados_json.get("avisos_validacao") or [],
        "fingerprint_contexto": fingerprint_resultado,
        "assinatura_conteudo_cache": assinatura_conteudo_cache,
        "versao_gerador": versao_cache,
        "cache_reutilizado": True,
        "cache_reutilizado_por_conteudo": reutilizacao_por_conteudo,
        "fonte_principal": dados_json.get("fonte_principal") or fonte_cache,
        "arquivo_fonte": dados_json.get("arquivo_fonte") or arquivo_cache,
        "origem_metodologia": origem_metodologia_cache,
        "fonte_referencia_metodologia": fonte_referencia_cache,
        "status_referencia_docx": dados_json.get("status_referencia_docx") or "",
        "arquivo_referencia_docx": dados_json.get("arquivo_referencia_docx") or "",
        "motivo_referencia_docx": dados_json.get("motivo_referencia_docx") or "",
        "texto_central_copiado_literalmente": bool(
            dados_json.get("texto_central_copiado_literalmente", False)
        ),
        "perfil_metodologico": perfil_resultado,
        "etapas_detectadas": dados_json.get("etapas_detectadas") or [],
        "versao_prompt": dados_json.get("versao_prompt") or "",
        "recursos_detectados": dados_json.get("recursos_detectados") or [],
        "texto_fonte": dados_json.get("texto_fonte") or "",
        "diagnostico_geracao": dados_json.get("diagnostico_geracao") or {},
    }
    if "avisos_validacao" not in dados_json:
        aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
    return aula_gerada


def tentar_reutilizar_cache_plano(
    *,
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    usar_ia: bool,
    caminho_pptx_correspondente: str | None,
    hash_atual: str,
    hash_fonte_extracao_esperada: str,
    fingerprint_atual: str,
    versao_gerador_atual: str,
    perfil_metodologico: str,
    referencia_docx_por_perfil_fn: Callable[[str, str, str, str], dict | None],
    referencia_docx_sobrescreve_metadados_fn: Callable[[str], bool],
    habilidade_referencia_docx_fn: Callable[[dict | None], str],
    material_aula_com_titulo_fn: Callable[[str, str], str],
    sobrescrever_listas_pedagogicas_com_referencia_fn: Callable[[dict | None, list[str], list[str]], tuple[list[str], list[str]]],
    origem_metodologia_por_referencia_fn: Callable[[str], str],
    perfil_docx_somente_colunas_pedagogicas_fn: Callable[[str], bool],
    assinatura_conteudo_atual: str = "",
) -> ResultadoReusoCachePlano:
    if not caminho_pdf:
        return ResultadoReusoCachePlano(None, None)

    try:
        caminho_json = Path(caminho_pdf).with_suffix(".json")
        if not caminho_json.exists():
            return ResultadoReusoCachePlano(None, None)

        with open(caminho_json, "r", encoding="utf-8") as arquivo_json:
            dados_json = json.load(arquivo_json)

        if not isinstance(dados_json, dict) or "metodologia" not in dados_json:
            return ResultadoReusoCachePlano(None, None)

        perfil_cache = perfil_disciplina(disciplina, turma=turma)
        hash_salvo = dados_json.get("hash_pdf")
        hash_fonte_salva = dados_json.get("hash_fonte_extracao") or ""
        versao_cache = str(dados_json.get("versao_gerador") or "")
        fonte_cache = str(dados_json.get("fonte_extracao") or "pdf").lower()
        arquivo_cache = str(dados_json.get("arquivo_fonte_extracao") or caminho_pdf)
        fingerprint_salvo = dados_json.get("fingerprint_contexto")
        assinatura_conteudo_salva = str(
            dados_json.get("assinatura_conteudo_cache") or ""
        )
        metodologia_cache = dados_json["metodologia"]
        acompanhamento_cache = dados_json.get("acompanhamento") or []
        acessibilidade_cache = dados_json.get("acessibilidade") or []
        aprendizagem_cache = dados_json.get("aprendizagem") or ""
        tema_cache = dados_json.get("tema") or ""
        material_cache = dados_json.get("material") or Path(caminho_pdf).name
        numero_cache = dados_json.get("numero_aula") or ""

        referencia_docx_cache = referencia_docx_por_perfil_fn(
            caminho_pdf,
            dados_json.get("numero_aula") or "",
            dados_json.get("tema") or "",
            perfil_cache,
        )
        if (
            referencia_docx_cache
            and referencia_docx_sobrescreve_metadados_fn(perfil_cache)
            and not dados_json.get("ia_usada", False)
        ):
            numero_ref_cache = referencia_docx_cache.get("numero")
            titulo_ref_cache = str(referencia_docx_cache.get("titulo") or "").strip()
            habilidade_ref_cache = habilidade_referencia_docx_fn(referencia_docx_cache)
            if numero_ref_cache:
                numero_cache = str(numero_ref_cache)
            if titulo_ref_cache:
                tema_cache = titulo_ref_cache
                material_cache = material_aula_com_titulo_fn(numero_cache, tema_cache)
            if habilidade_ref_cache:
                aprendizagem_cache = habilidade_ref_cache
            metodologia_cache = referencia_docx_cache.get("metodologia") or metodologia_cache
            acompanhamento_cache, acessibilidade_cache = (
                sobrescrever_listas_pedagogicas_com_referencia_fn(
                    referencia_docx_cache,
                    acompanhamento_cache,
                    acessibilidade_cache,
                )
            )

        origem_metodologia_cache = (
            origem_metodologia_por_referencia_fn(perfil_cache)
            if referencia_docx_cache
            else dados_json.get("origem_metodologia") or ""
        )
        fonte_referencia_cache = dados_json.get("fonte_referencia_metodologia") or (
            referencia_docx_cache or {}
        ).get("fonte", "")

        invalida_cache = False
        if hash_salvo and hash_atual and hash_salvo != hash_atual:
            invalida_cache = True
        elif caminho_pptx_correspondente and fonte_cache != "pptx":
            invalida_cache = True
        elif caminho_pptx_correspondente and Path(arquivo_cache) != Path(caminho_pptx_correspondente):
            invalida_cache = True
        elif caminho_pptx_correspondente and hash_fonte_extracao_esperada and hash_fonte_salva != hash_fonte_extracao_esperada:
            invalida_cache = True
        elif not caminho_pptx_correspondente and fonte_cache == "pptx":
            invalida_cache = True
        elif versao_cache != versao_gerador_atual:
            invalida_cache = True
        elif usar_ia != dados_json.get("ia_usada", False):
            invalida_cache = True
        elif perfil_docx_somente_colunas_pedagogicas_fn(perfil_cache) and referencia_docx_cache:
            invalida_cache = True
        reutilizacao_por_conteudo = bool(
            assinatura_conteudo_atual
            and assinatura_conteudo_salva == assinatura_conteudo_atual
            and fingerprint_salvo != fingerprint_atual
        )
        if fingerprint_salvo != fingerprint_atual and not reutilizacao_por_conteudo:
            invalida_cache = True
        if invalida_cache:
            return ResultadoReusoCachePlano(None, dados_json)

        aula_reutilizada = _montar_aula_reutilizada(
            dados_json=dados_json,
            disciplina=disciplina,
            hash_atual=hash_atual,
            perfil_metodologico=perfil_metodologico,
            tema_cache=tema_cache,
            material_cache=material_cache,
            numero_cache=numero_cache,
            aprendizagem_cache=aprendizagem_cache,
            metodologia_cache=metodologia_cache,
            acompanhamento_cache=acompanhamento_cache,
            acessibilidade_cache=acessibilidade_cache,
            fonte_cache=fonte_cache,
            arquivo_cache=arquivo_cache,
            hash_fonte_salva=hash_fonte_salva,
            fingerprint_salvo=fingerprint_salvo,
            fingerprint_resultado=(
                fingerprint_atual if reutilizacao_por_conteudo else fingerprint_salvo
            ),
            assinatura_conteudo_cache=(
                assinatura_conteudo_atual or assinatura_conteudo_salva
            ),
            versao_cache=versao_cache,
            origem_metodologia_cache=origem_metodologia_cache,
            fonte_referencia_cache=fonte_referencia_cache,
            perfil_resultado=(
                perfil_metodologico
                if reutilizacao_por_conteudo
                else dados_json.get("perfil_metodologico") or perfil_metodologico
            ),
            reutilizacao_por_conteudo=reutilizacao_por_conteudo,
        )
        return ResultadoReusoCachePlano(aula_reutilizada, dados_json)
    except Exception:
        return ResultadoReusoCachePlano(None, None)
