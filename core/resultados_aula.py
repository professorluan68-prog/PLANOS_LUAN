from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class DependenciasResultadosAula:
    referencia_docx_por_perfil_fn: Callable[[str, str, str, str], dict | None]
    habilidade_referencia_docx_fn: Callable[[dict | None], str]
    origem_metodologia_por_referencia_fn: Callable[[str], str]
    deve_aplicar_referencia_docx_no_resultado_ia_fn: Callable[[str, dict | None], bool]
    sobrescrever_listas_pedagogicas_com_referencia_fn: Callable[[dict | None, list[str], list[str]], tuple[list[str], list[str]]]
    extracao_pdf_fn: Callable[..., dict]
    detectar_tipo_aula_fn: Callable[..., str]
    resolver_habilidade_portugues_fn: Callable[[str, str, str], str]
    montar_aprendizagem_inteligente_fn: Callable[..., str]
    tentar_gerador_colunas_pedagogicas_fn: Callable[..., dict | None]
    metodologia_leitura_redacao_modelo_fn: Callable[[str, str, str], list[dict]]
    detectar_tecnicas_lemov_fn: Callable[[str, str], list[str]]
    garantir_tecnicas_lemov_na_metodologia_fn: Callable[[list[dict], list[str]], list[dict]]
    variar_linguagem_metodologia_fn: Callable[[list[dict], str, str, str], list[dict]]
    ajustar_metodologia_por_sequencia_fn: Callable[..., list[dict]]
    revisar_metodologia_fn: Callable[..., tuple[list[dict], list[str]]]
    naturalizar_metodologia_professor_fn: Callable[[list[dict], str], list[dict]]
    adaptar_metodologia_eja_fn: Callable[[list[dict], str, str, str, list[str], Callable[[list[dict], list[str]], list[dict]]], list[dict]]
    texto_metodologia_fn: Callable[[object], str]
    gerar_acompanhamento_aprimorado_fn: Callable[..., list[str]]
    gerar_acessibilidade_aprimorada_fn: Callable[..., list[str]]
    normalizar_itens_contextuais_fn: Callable[[list[str], list[str], str, str], tuple[list[str], list[str]]]
    montar_etapas_metodologia_fn: Callable[..., list[dict]]
    aprimorar_historia_pos_processamento_fn: Callable[..., tuple[list[dict], list[str], list[str]]]
    detectar_recursos_reais_fn: Callable[[str], list[str]]
    higienizar_plano_fn: Callable[[list[dict], list[str], list[str], str, str, str, list[str]], tuple[list[dict], list[str], list[str]]]
    validar_aula_final_fn: Callable[[dict], list[str]]


def _extrair_base_pedagogica(
    *,
    texto: str,
    tema: str,
    disciplina_base: str,
    turma: str,
    numero_aula: str,
    bimestre: str,
    perfil: str,
    caminho_pdf: str,
    dependencias: DependenciasResultadosAula,
) -> dict:
    referencia_docx = dependencias.referencia_docx_por_perfil_fn(
        caminho_pdf,
        numero_aula,
        tema,
        perfil,
    )
    habilidade_referencia = dependencias.habilidade_referencia_docx_fn(referencia_docx)
    extracao = dependencias.extracao_pdf_fn(
        texto,
        tema,
        disciplina=disciplina_base,
        numero_aula=numero_aula,
        turma=turma,
        bimestre=bimestre,
    )
    tipo = dependencias.detectar_tipo_aula_fn(
        extracao.get("texto_prioritario") or texto,
        tema,
        disciplina_base,
        turma=turma,
    )
    habilidade = extracao.get("habilidade", "")
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        habilidade = dependencias.resolver_habilidade_portugues_fn(
            habilidade,
            caminho_pdf,
            numero_aula,
        )
    return {
        "referencia_docx": referencia_docx,
        "habilidade_referencia": habilidade_referencia,
        "extracao": extracao,
        "tipo": tipo,
        "habilidade": habilidade,
    }


def _finalizar_resultado(
    *,
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    perfil: str,
    provedor_ia: str,
    aprendizagem: str,
    metodologia: list[dict],
    acompanhamento: list[str],
    acessibilidade: list[str],
    referencia_docx: dict | None,
    aplicar_referencia_docx: bool,
    marcar_origem_referencia: bool,
    origem_sem_referencia: str,
    ia_usada: bool,
    ia_provedor_registrado: str,
    ia_erro: str,
    indice_aula: int,
    total_aulas: int,
    diagnostico_geracao: dict,
    dependencias: DependenciasResultadosAula,
) -> dict:
    recursos_reais = dependencias.detectar_recursos_reais_fn(texto)
    metodologia, acompanhamento, acessibilidade = dependencias.higienizar_plano_fn(
        metodologia,
        acompanhamento,
        acessibilidade,
        perfil,
        disciplina_base,
        tema,
        recursos_reais,
    )
    if referencia_docx and aplicar_referencia_docx:
        acompanhamento, acessibilidade = (
            dependencias.sobrescrever_listas_pedagogicas_com_referencia_fn(
                referencia_docx,
                acompanhamento,
                acessibilidade,
            )
        )

    if perfil == "historia":
        metodologia, acompanhamento, acessibilidade = (
            dependencias.aprimorar_historia_pos_processamento_fn(
                metodologia,
                acompanhamento,
                acessibilidade,
                texto=texto,
                tema=tema,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
            )
        )

    aula_gerada = {
        "disciplina": disciplina_base,
        "tema": tema,
        "material": material_digital,
        "numero_aula": numero_aula,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
        "acompanhamento": acompanhamento,
        "acessibilidade": acessibilidade,
        "origem_metodologia": (
            dependencias.origem_metodologia_por_referencia_fn(perfil)
            if referencia_docx and marcar_origem_referencia
            else origem_sem_referencia
        ),
        "fonte_referencia_metodologia": (referencia_docx or {}).get("fonte", ""),
        "ia_usada": ia_usada,
        "ia_provedor": ia_provedor_registrado,
        "ia_erro": ia_erro,
        "recursos_detectados": recursos_reais,
        "texto_fonte": texto,
        "diagnostico_geracao": diagnostico_geracao,
    }
    aula_gerada["avisos_validacao"] = dependencias.validar_aula_final_fn(aula_gerada)
    return aula_gerada


def montar_resultado_aula_ia(
    *,
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    turma: str,
    provedor_ia: str,
    perfil: str,
    contexto_metodologico: str,
    indice_aula: int,
    total_aulas: int,
    modalidade_eja_ativa: bool,
    plano_ia: dict,
    metodologia_fixa_pdf: list[dict],
    aprendizagem_pv: str,
    objetivos_orientacao: list[str],
    aprendizagem_orientacao: str,
    dependencias: DependenciasResultadosAula,
    caminho_pdf: str = "",
    bimestre: str = "",
    rascunho_base: dict | None = None,
) -> dict:
    base = _extrair_base_pedagogica(
        texto=texto,
        tema=tema,
        disciplina_base=disciplina_base,
        turma=turma,
        numero_aula=numero_aula,
        bimestre=bimestre,
        perfil=perfil,
        caminho_pdf=caminho_pdf,
        dependencias=dependencias,
    )
    referencia_docx = base["referencia_docx"]
    habilidade_referencia = base["habilidade_referencia"]
    extracao = base["extracao"]
    tipo = base["tipo"]
    habilidade_pdf = base["habilidade"]

    objetivos_secao = extracao.get("objetivos_secao") or []
    conteudos_secao = extracao.get("conteudos_secao") or []
    if objetivos_orientacao:
        objetivos_secao = list(objetivos_orientacao)

    if aprendizagem_pv:
        aprendizagem = aprendizagem_pv
    elif perfil == "orientacao_estudos" and habilidade_referencia:
        aprendizagem = habilidade_referencia
        habilidade_pdf = habilidade_referencia
    elif perfil == "orientacao_estudos" and aprendizagem_orientacao:
        aprendizagem = aprendizagem_orientacao
        habilidade_pdf = aprendizagem_orientacao
    else:
        aprendizagem = dependencias.montar_aprendizagem_inteligente_fn(
            habilidade_pdf=habilidade_pdf or plano_ia.get("aprendizagem", ""),
            tema=tema,
            conceito=extracao.get("conceito_extraido", tema),
            perfil=perfil,
            objetivos_secao=objetivos_secao,
            conteudos_secao=conteudos_secao,
        )

    colunas_planejamento = dependencias.tentar_gerador_colunas_pedagogicas_fn(
        texto=texto,
        titulo_aula=material_digital or tema,
        disciplina=disciplina_base,
        turma=turma,
        tema=tema,
        perfil=perfil,
        contexto_metodologico=contexto_metodologico,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        modalidade_eja_ativa=modalidade_eja_ativa,
    )

    metodologia_local = rascunho_base.get("metodologia", []) if rascunho_base else []
    metodologia_ia_crua = plano_ia.get("metodologia", []) if plano_ia else []
    metodologia_higienizada_temp = []

    metodologia_ia = plano_ia.get("metodologia", [])
    if perfil == "leitura_redacao":
        metodologia_ia = dependencias.metodologia_leitura_redacao_modelo_fn(
            texto,
            tema,
            turma=turma,
        )
    if metodologia_ia:
        tecnicas_lemov_pdf = dependencias.detectar_tecnicas_lemov_fn(texto, tema)
        if perfil not in {"projeto_de_vida", "lideranca_oratoria"}:
            metodologia_ia = dependencias.garantir_tecnicas_lemov_na_metodologia_fn(
                metodologia_ia,
                tecnicas_lemov_pdf,
            )
        metodologia_ia = dependencias.variar_linguagem_metodologia_fn(
            metodologia_ia,
            disciplina_base,
            turma,
            tema,
        )
        if perfil != "leitura_redacao":
            metodologia_ia = dependencias.ajustar_metodologia_por_sequencia_fn(
                metodologia_ia,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                tema=tema,
            )
        metodologia_ia, _ = dependencias.revisar_metodologia_fn(
            metodologia_ia,
            perfil=perfil,
            tema=tema,
            contexto=contexto_metodologico,
        )
        metodologia_higienizada_temp = list(metodologia_ia)
        metodologia_ia = dependencias.naturalizar_metodologia_professor_fn(
            metodologia_ia,
            perfil=perfil,
        )
        if modalidade_eja_ativa:
            metodologia_ia = dependencias.adaptar_metodologia_eja_fn(
                metodologia_ia,
                perfil,
                tema,
                texto,
                tecnicas_lemov_pdf,
                dependencias.garantir_tecnicas_lemov_na_metodologia_fn,
            )

    if metodologia_fixa_pdf:
        metodologia = metodologia_fixa_pdf
        desenvolvimento = dependencias.texto_metodologia_fn(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = dependencias.gerar_acompanhamento_aprimorado_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo=tipo,
            habilidade=habilidade_pdf,
            etapas_metodologia=etapas_titulos,
        )
        acessibilidade = dependencias.gerar_acessibilidade_aprimorada_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo=tipo,
            recursos_detectados=extracao.get("recursos_detectados"),
        )
        acompanhamento, acessibilidade = dependencias.normalizar_itens_contextuais_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    elif metodologia_ia:
        metodologia = metodologia_ia
        desenvolvimento = dependencias.texto_metodologia_fn(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento_ia = plano_ia.get("acompanhamento") or []
        acessibilidade_ia = plano_ia.get("acessibilidade") or []
        if len(acompanhamento_ia) >= 2:
            acompanhamento = acompanhamento_ia
        else:
            acompanhamento = dependencias.gerar_acompanhamento_aprimorado_fn(
                tema=tema,
                aprendizagem=aprendizagem,
                desenvolvimento=desenvolvimento,
                disciplina=disciplina_base,
                perfil=perfil,
                tipo=tipo,
                habilidade=habilidade_pdf,
                etapas_metodologia=etapas_titulos,
            )
        if len(acessibilidade_ia) >= 2:
            acessibilidade = acessibilidade_ia
        else:
            acessibilidade = dependencias.gerar_acessibilidade_aprimorada_fn(
                tema=tema,
                aprendizagem=aprendizagem,
                desenvolvimento=desenvolvimento,
                disciplina=disciplina_base,
                perfil=perfil,
                tipo=tipo,
                recursos_detectados=extracao.get("recursos_detectados"),
            )
        acompanhamento, acessibilidade = dependencias.normalizar_itens_contextuais_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    elif colunas_planejamento:
        metodologia = colunas_planejamento["metodologia"]
        if modalidade_eja_ativa:
            tecnicas_lemov_pdf = dependencias.detectar_tecnicas_lemov_fn(texto, tema)
            metodologia = dependencias.adaptar_metodologia_eja_fn(
                metodologia,
                perfil,
                tema,
                texto,
                tecnicas_lemov_pdf,
                dependencias.garantir_tecnicas_lemov_na_metodologia_fn,
            )
        acompanhamento = colunas_planejamento["acompanhamento"]
        acessibilidade = colunas_planejamento["acessibilidade"]
        acompanhamento, acessibilidade = dependencias.normalizar_itens_contextuais_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    else:
        metodologia = metodologia_ia
        desenvolvimento = dependencias.texto_metodologia_fn(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento_ia = plano_ia.get("acompanhamento") or []
        acessibilidade_ia = plano_ia.get("acessibilidade") or []
        if len(acompanhamento_ia) >= 2:
            acompanhamento = acompanhamento_ia
        else:
            acompanhamento = dependencias.gerar_acompanhamento_aprimorado_fn(
                tema=tema,
                aprendizagem=aprendizagem,
                desenvolvimento=desenvolvimento,
                disciplina=disciplina_base,
                perfil=perfil,
                tipo=tipo,
                habilidade=habilidade_pdf,
                etapas_metodologia=etapas_titulos,
            )
        if len(acessibilidade_ia) >= 2:
            acessibilidade = acessibilidade_ia
        else:
            acessibilidade = dependencias.gerar_acessibilidade_aprimorada_fn(
                tema=tema,
                aprendizagem=aprendizagem,
                desenvolvimento=desenvolvimento,
                disciplina=disciplina_base,
                perfil=perfil,
                tipo=tipo,
                recursos_detectados=extracao.get("recursos_detectados"),
            )
        acompanhamento, acessibilidade = dependencias.normalizar_itens_contextuais_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )

    aplicar_referencia_docx = bool(
        referencia_docx
        and dependencias.deve_aplicar_referencia_docx_no_resultado_ia_fn(
            perfil,
            plano_ia,
        )
    )
    if aplicar_referencia_docx:
        metodologia = dependencias.naturalizar_metodologia_professor_fn(
            referencia_docx.get("metodologia") or [],
            perfil=perfil,
        )
        acompanhamento = list(referencia_docx.get("acompanhamento") or [])[:3]
        acessibilidade = list(referencia_docx.get("acessibilidade") or [])[:3]

    diagnostico_geracao = {
        "metodologia_local": metodologia_local,
        "metodologia_ia_crua": metodologia_ia_crua,
        "metodologia_higienizada": (
            metodologia_higienizada_temp or (metodologia_ia if metodologia_ia else [])
        ),
        "metodologia_final": metodologia,
    }

    return _finalizar_resultado(
        texto=texto,
        tema=tema,
        material_digital=material_digital,
        numero_aula=numero_aula,
        disciplina_base=disciplina_base,
        perfil=perfil,
        provedor_ia=provedor_ia,
        aprendizagem=aprendizagem,
        metodologia=metodologia,
        acompanhamento=acompanhamento,
        acessibilidade=acessibilidade,
        referencia_docx=referencia_docx,
        aplicar_referencia_docx=aplicar_referencia_docx,
        marcar_origem_referencia=bool(referencia_docx),
        origem_sem_referencia="ia_refinada",
        ia_usada=True,
        ia_provedor_registrado=provedor_ia,
        ia_erro="",
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        diagnostico_geracao=diagnostico_geracao,
        dependencias=dependencias,
    )


def montar_resultado_aula_local(
    *,
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    turma: str,
    provedor_ia: str,
    perfil: str,
    contexto_metodologico: str,
    indice_aula: int,
    total_aulas: int,
    modalidade_eja_ativa: bool,
    metodologia_fixa_pdf: list[dict],
    aprendizagem_pv: str,
    objetivos_orientacao: list[str],
    aprendizagem_orientacao: str,
    usar_ia: bool,
    ia_erro: str,
    dependencias: DependenciasResultadosAula,
    contexto_geracao: dict | None = None,
    caminho_pdf: str = "",
    bimestre: str = "",
) -> dict:
    base = _extrair_base_pedagogica(
        texto=texto,
        tema=tema,
        disciplina_base=disciplina_base,
        turma=turma,
        numero_aula=numero_aula,
        bimestre=bimestre,
        perfil=perfil,
        caminho_pdf=caminho_pdf,
        dependencias=dependencias,
    )
    referencia_docx = base["referencia_docx"]
    habilidade_referencia = base["habilidade_referencia"]
    extracao = base["extracao"]
    tipo = base["tipo"]
    habilidade = base["habilidade"]
    conceito = extracao.get("conceito_extraido", tema)
    recursos = extracao.get("recursos_detectados", [])
    objetivos_secao = extracao.get("objetivos_secao") or []
    conteudos_secao = extracao.get("conteudos_secao") or []
    if objetivos_orientacao:
        objetivos_secao = list(objetivos_orientacao)

    if aprendizagem_pv:
        aprendizagem = aprendizagem_pv
        habilidade = aprendizagem_pv
    elif perfil == "orientacao_estudos" and habilidade_referencia:
        aprendizagem = habilidade_referencia
        habilidade = habilidade_referencia
    elif perfil == "orientacao_estudos" and aprendizagem_orientacao:
        aprendizagem = aprendizagem_orientacao
        habilidade = aprendizagem_orientacao
    else:
        aprendizagem = dependencias.montar_aprendizagem_inteligente_fn(
            habilidade_pdf=habilidade,
            tema=tema,
            conceito=conceito,
            perfil=perfil,
            objetivos_secao=objetivos_secao,
            conteudos_secao=conteudos_secao,
        )

    if (
        perfil == "orientacao_estudos"
        and not aprendizagem_orientacao
        and re.search(r"(?i)\betapa\s+(\d+|final)\b", str(tema or "").strip())
    ):
        aprendizagem = (
            f"Desenvolver estrategias de leitura, interpretacao e registro em {tema}, "
            "com foco em autonomia de estudo e resolucao orientada das atividades."
        )

    colunas_planejamento = dependencias.tentar_gerador_colunas_pedagogicas_fn(
        texto=texto,
        titulo_aula=material_digital or tema,
        disciplina=disciplina_base,
        turma=turma,
        tema=tema,
        perfil=perfil,
        contexto_metodologico=contexto_metodologico,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        modalidade_eja_ativa=modalidade_eja_ativa,
    )

    metodologia_local = []
    metodologia_higienizada_temp = []

    if metodologia_fixa_pdf:
        metodologia_local = list(metodologia_fixa_pdf)
        metodologia = metodologia_fixa_pdf
        desenvolvimento = dependencias.texto_metodologia_fn(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = dependencias.gerar_acompanhamento_aprimorado_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo=tipo,
            habilidade=habilidade,
            etapas_metodologia=etapas_titulos,
        )
        acessibilidade = dependencias.gerar_acessibilidade_aprimorada_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo=tipo,
            recursos_detectados=recursos,
        )
        acompanhamento, acessibilidade = dependencias.normalizar_itens_contextuais_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
        metodologia_higienizada_temp = list(metodologia)
    elif colunas_planejamento:
        metodologia_local = list(colunas_planejamento["metodologia"])
        metodologia = colunas_planejamento["metodologia"]
        if modalidade_eja_ativa:
            tecnicas_lemov_pdf = dependencias.detectar_tecnicas_lemov_fn(texto, tema)
            metodologia = dependencias.adaptar_metodologia_eja_fn(
                metodologia,
                perfil,
                tema,
                texto,
                tecnicas_lemov_pdf,
                dependencias.garantir_tecnicas_lemov_na_metodologia_fn,
            )
        acompanhamento = colunas_planejamento["acompanhamento"]
        acessibilidade = colunas_planejamento["acessibilidade"]
        acompanhamento, acessibilidade = dependencias.normalizar_itens_contextuais_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
        metodologia_higienizada_temp = list(metodologia)
    else:
        metodologia = dependencias.montar_etapas_metodologia_fn(
            texto,
            disciplina_base,
            turma,
            tema,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            contexto_geracao=contexto_geracao,
        )
        metodologia_local = list(metodologia)
        tecnicas_lemov_pdf = dependencias.detectar_tecnicas_lemov_fn(texto, tema)
        if perfil not in {"projeto_de_vida", "lideranca_oratoria"}:
            metodologia = dependencias.garantir_tecnicas_lemov_na_metodologia_fn(
                metodologia,
                tecnicas_lemov_pdf,
            )
        metodologia = dependencias.variar_linguagem_metodologia_fn(
            metodologia,
            disciplina_base,
            turma,
            tema,
        )
        metodologia, _ = dependencias.revisar_metodologia_fn(
            metodologia,
            perfil=perfil,
            tema=tema,
            contexto=contexto_metodologico,
        )
        metodologia_higienizada_temp = list(metodologia)
        metodologia = dependencias.naturalizar_metodologia_professor_fn(
            metodologia,
            perfil=perfil,
        )
        if modalidade_eja_ativa:
            metodologia = dependencias.adaptar_metodologia_eja_fn(
                metodologia,
                perfil,
                tema,
                texto,
                tecnicas_lemov_pdf,
                dependencias.garantir_tecnicas_lemov_na_metodologia_fn,
            )

        desenvolvimento = dependencias.texto_metodologia_fn(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = dependencias.gerar_acompanhamento_aprimorado_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo=tipo,
            habilidade=habilidade,
            etapas_metodologia=etapas_titulos,
        )
        acessibilidade = dependencias.gerar_acessibilidade_aprimorada_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo=tipo,
            recursos_detectados=recursos,
        )
        acompanhamento, acessibilidade = dependencias.normalizar_itens_contextuais_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )

    aplicar_referencia_docx = bool(referencia_docx)
    if aplicar_referencia_docx:
        metodologia = dependencias.naturalizar_metodologia_professor_fn(
            referencia_docx.get("metodologia") or [],
            perfil=perfil,
        )
        acompanhamento = list(referencia_docx.get("acompanhamento") or [])[:3]
        acessibilidade = list(referencia_docx.get("acessibilidade") or [])[:3]

    diagnostico_geracao = {
        "metodologia_local": metodologia_local,
        "metodologia_ia_crua": [],
        "metodologia_higienizada": metodologia_higienizada_temp or (metodologia if metodologia else []),
        "metodologia_final": metodologia,
    }

    return _finalizar_resultado(
        texto=texto,
        tema=tema,
        material_digital=material_digital,
        numero_aula=numero_aula,
        disciplina_base=disciplina_base,
        perfil=perfil,
        provedor_ia=provedor_ia,
        aprendizagem=aprendizagem,
        metodologia=metodologia,
        acompanhamento=acompanhamento,
        acessibilidade=acessibilidade,
        referencia_docx=referencia_docx,
        aplicar_referencia_docx=aplicar_referencia_docx,
        marcar_origem_referencia=bool(referencia_docx),
        origem_sem_referencia="motor_local",
        ia_usada=False,
        ia_provedor_registrado=provedor_ia if usar_ia else "",
        ia_erro=ia_erro,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        diagnostico_geracao=diagnostico_geracao,
        dependencias=dependencias,
    )
