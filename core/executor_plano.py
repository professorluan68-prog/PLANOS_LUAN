from __future__ import annotations

from typing import Callable, Sequence

from core.models import PlanoCompleto
from core.revisao_final import gravar_sidecar_json, revisar_aula_gerada


def finalizar_plano_aula(
    resultado_final: dict | PlanoCompleto,
    *,
    caminho_pdf: str = "",
    perfil: str = "",
    fonte_extracao: str = "pdf",
    arquivo_fonte_extracao: str = "",
    hash_fonte_extracao: str = "",
    fingerprint_contexto: str = "",
    perfil_metodologico: str = "",
    versao_gerador: str = "",
    hash_pdf: str = "",
    enriquecer_callback: Callable[[dict, str], None] | None = None,
) -> dict:
    plano = PlanoCompleto.from_any(resultado_final)
    plano.fonte_extracao = fonte_extracao or plano.fonte_extracao or "pdf"
    plano.arquivo_fonte_extracao = arquivo_fonte_extracao or plano.arquivo_fonte_extracao
    plano.hash_fonte_extracao = hash_fonte_extracao or plano.hash_fonte_extracao or hash_pdf
    plano.fingerprint_contexto = fingerprint_contexto or plano.fingerprint_contexto
    plano.versao_gerador = versao_gerador or plano.versao_gerador
    plano.cache_reutilizado = False
    plano.fonte_principal = plano.fonte_extracao
    plano.arquivo_fonte = arquivo_fonte_extracao or plano.arquivo_fonte
    plano.perfil_metodologico = perfil_metodologico or plano.perfil_metodologico
    if not plano.etapas_detectadas:
        plano.etapas_detectadas = plano.etapas_metodologia()
    if not plano.versao_prompt:
        plano.versao_prompt = ""

    dados_runtime = plano.to_dict()
    if enriquecer_callback and caminho_pdf:
        enriquecer_callback(dados_runtime, caminho_pdf)

    try:
        dados_runtime = revisar_aula_gerada(dados_runtime, perfil)
        plano = PlanoCompleto.from_any(dados_runtime)
        if caminho_pdf and hash_pdf:
            gravar_sidecar_json(caminho_pdf, plano, hash_pdf)
    except Exception:
        plano = PlanoCompleto.from_any(dados_runtime)

    return plano.to_dict()


def processar_lote_pdfs(
    caminhos_pdf: Sequence[str] | None,
    *,
    gerar_aula_callback: Callable[[str, int, int, bool], dict],
    dividir_metodologia: bool = False,
    dividir_por_pdf: list[bool] | None = None,
    progress_callback=None,
    texto_metodologia_fn: Callable[[object], str] | None = None,
    dividir_texto_fn: Callable[[str], tuple[str, str]] | None = None,
    metodologia_por_texto_fn: Callable[[str], list[dict]] | None = None,
) -> list[dict]:
    aulas = []
    total_aulas = len(caminhos_pdf or [])
    for idx, caminho in enumerate(caminhos_pdf or []):
        if progress_callback:
            try:
                progress_callback(idx, total_aulas, caminho)
            except Exception:
                pass

        dividir_aula_atual = (
            bool(dividir_por_pdf[idx])
            if dividir_por_pdf and idx < len(dividir_por_pdf)
            else dividir_metodologia
        )
        aula = gerar_aula_callback(caminho, idx, total_aulas, dividir_aula_atual)

        if dividir_aula_atual:
            if not (
                texto_metodologia_fn
                and dividir_texto_fn
                and metodologia_por_texto_fn
            ):
                raise ValueError(
                    "Funções de divisão de metodologia são obrigatórias quando dividir_metodologia estiver ativo."
                )
            texto = texto_metodologia_fn(aula["metodologia"])
            parte1, parte2 = dividir_texto_fn(texto)
            aula_primeiro = dict(aula)
            aula_primeiro["metodologia"] = metodologia_por_texto_fn(parte1)

            aula_segundo = dict(aula)
            aula_segundo["tema"] = f"{aula['tema']} - continuidade"
            aula_segundo["metodologia"] = metodologia_por_texto_fn(parte2)

            aulas.extend([aula_primeiro, aula_segundo])
        else:
            aulas.append(aula)
    return aulas
