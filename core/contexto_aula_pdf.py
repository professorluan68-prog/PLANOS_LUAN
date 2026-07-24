from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable


@dataclass
class DependenciasContextoAulaPDF:
    logger: Any
    extrair_texto_pdf_fn: Callable[[str], str]
    tema_por_texto_fn: Callable[[str, str, str], str]
    material_digital_por_texto_fn: Callable[[str, str, str, str], str]
    rotulo_aula_material_fn: Callable[[str, str], str]
    eh_cenario_piloto_pptx_fn: Callable[[str, str], bool]
    encontrar_pptx_correspondente_fn: Callable[[str, str, str], str | None]
    extrair_estrutura_pptx_fn: Callable[[str], dict]
    estrutura_pptx_para_dados_aula_fn: Callable[[dict], dict]
    eh_cdp_contextual_disciplina_fn: Callable[[str], bool]
    disciplina_base_cdp_por_cadastro_fn: Callable[[str], str]
    disciplina_base_cdp_contextual_fn: Callable[[str, str, str], str]
    perfil_disciplina_fn: Callable[..., str]
    obter_dados_aprofundamento_fn: Callable[..., dict | None]
    resolver_contexto_orientacao_estudos_fn: Callable[..., tuple[str, str, str]]
    buscar_objetivos_orientacao_estudos_fn: Callable[..., list[str]]
    formatar_objetivos_orientacao_estudos_fn: Callable[[list[str]], str]
    extracao_pdf_fn: Callable[..., dict]
    detectar_tipo_aula_fn: Callable[..., str]
    metodologia_fixa_pdf_especial_fn: Callable[[str, str, str], list[dict] | None]
    metodologia_por_blocos_estruturados_fn: Callable[[dict[str, str] | None], list[dict]]
    perfil_suporta_eja_fn: Callable[[str], bool]
    eh_cdp_fn: Callable[[str], bool]
    detectar_contexto_metodologico_fn: Callable[..., str]
    buscar_item_projeto_vida_fn: Callable[[str, str, str], dict]
    montar_aprendizagem_projeto_vida_fn: Callable[[dict], str]
    referencia_docx_por_perfil_fn: Callable[[str, str, str, str], dict | None]
    habilidade_referencia_docx_fn: Callable[[dict | None], str]
    material_aula_com_titulo_fn: Callable[[str, str], str]
    titulo_escopo_projeto_vida_confiavel_fn: Callable[[str], bool]


def _numero_aula_rotulo(
    texto: str,
    caminho_pdf: str,
    dependencias: DependenciasContextoAulaPDF,
) -> str:
    return (
        dependencias.rotulo_aula_material_fn(texto, caminho_pdf)
        .replace("AULA", "", 1)
        .strip()
    )


def _resolver_fonte_extracao(
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    caminho_pptx_correspondente: str | None,
    dependencias: DependenciasContextoAulaPDF,
) -> tuple[str, str, str, str, dict[str, str]]:
    texto_pdf = dependencias.extrair_texto_pdf_fn(caminho_pdf)
    texto = texto_pdf
    fonte_extracao = "pdf"
    arquivo_fonte_extracao = caminho_pdf
    blocos_pptx: dict[str, str] = {}

    tema = dependencias.tema_por_texto_fn(texto_pdf, caminho_pdf, disciplina)
    material_digital = dependencias.material_digital_por_texto_fn(
        texto_pdf,
        caminho_pdf,
        disciplina,
        tema,
    )
    numero_aula = _numero_aula_rotulo(texto_pdf, caminho_pdf, dependencias)

    usar_pptx = dependencias.eh_cenario_piloto_pptx_fn(disciplina, turma)
    caminho_pptx = caminho_pptx_correspondente if usar_pptx else None
    if usar_pptx and not caminho_pptx:
        caminho_pptx = dependencias.encontrar_pptx_correspondente_fn(
            caminho_pdf,
            disciplina,
            turma,
        )

    if usar_pptx and caminho_pptx:
        try:
            estrutura_pptx = dependencias.extrair_estrutura_pptx_fn(caminho_pptx)
            dados_pptx = dependencias.estrutura_pptx_para_dados_aula_fn(estrutura_pptx)
            texto = dados_pptx.get("texto_base") or texto_pdf
            tema = dados_pptx.get("tema") or tema
            material_digital = dados_pptx.get("material") or material_digital
            blocos_pptx = dados_pptx.get("blocos_pedagogicos") or {}
            numero_pptx = _numero_aula_rotulo(texto, caminho_pdf, dependencias)
            numero_aula = numero_pptx or numero_aula
            fonte_extracao = "pptx"
            arquivo_fonte_extracao = caminho_pptx
            dependencias.logger.info("[EXTRACAO] Fonte usada: PPTX")
            dependencias.logger.info(
                "[EXTRACAO] PPTX correspondente encontrado: %s",
                caminho_pptx,
            )
        except Exception as exc:
            dependencias.logger.warning(
                "[EXTRACAO] Falha ao ler PPTX %s: %s",
                caminho_pptx,
                exc,
            )
            texto = texto_pdf
            tema = dependencias.tema_por_texto_fn(texto_pdf, caminho_pdf, disciplina)
            material_digital = dependencias.material_digital_por_texto_fn(
                texto_pdf,
                caminho_pdf,
                disciplina,
                tema,
            )
            numero_aula = _numero_aula_rotulo(texto_pdf, caminho_pdf, dependencias)
            fonte_extracao = "pdf"
            arquivo_fonte_extracao = caminho_pdf
    else:
        dependencias.logger.info("[EXTRACAO] Fonte usada: PDF")

    return texto, tema, material_digital, numero_aula, {
        "fonte_extracao": fonte_extracao,
        "arquivo_fonte_extracao": arquivo_fonte_extracao,
        "blocos_pptx": blocos_pptx,
    }


def _ajustar_contexto_por_perfil(
    *,
    caminho_pdf: str,
    numero_aula: str,
    perfil: str,
    tema: str,
    material_digital: str,
    objetivos_orientacao: list[str],
    aprendizagem_orientacao: str,
    escopo_pv: dict,
    dependencias: DependenciasContextoAulaPDF,
) -> tuple[str, str, str, list[str], str]:
    if perfil in {"ingles", "lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        referencia_docx_perfil = dependencias.referencia_docx_por_perfil_fn(
            caminho_pdf,
            numero_aula,
            tema,
            perfil,
        )
        titulo_referencia = str((referencia_docx_perfil or {}).get("titulo") or "").strip()
        if titulo_referencia:
            if not numero_aula and (referencia_docx_perfil or {}).get("numero"):
                numero_aula = str(referencia_docx_perfil.get("numero"))
            tema = titulo_referencia
            material_digital = dependencias.material_aula_com_titulo_fn(numero_aula, tema)

    if perfil == "orientacao_estudos":
        referencia_docx_oe = dependencias.referencia_docx_por_perfil_fn(
            caminho_pdf,
            numero_aula,
            tema,
            perfil,
        )
        titulo_referencia = str((referencia_docx_oe or {}).get("titulo") or "").strip()
        habilidade_referencia = dependencias.habilidade_referencia_docx_fn(
            referencia_docx_oe,
        )
        if titulo_referencia:
            if not numero_aula and (referencia_docx_oe or {}).get("numero"):
                numero_aula = str(referencia_docx_oe.get("numero"))
            tema = titulo_referencia
            material_digital = dependencias.material_aula_com_titulo_fn(
                numero_aula,
                tema,
            )
        if habilidade_referencia:
            objetivos_orientacao = []
            aprendizagem_orientacao = habilidade_referencia

    if perfil == "projeto_de_vida":
        referencia_docx_pv = dependencias.referencia_docx_por_perfil_fn(
            caminho_pdf,
            numero_aula,
            tema,
            perfil,
        )
        titulo_referencia = str((referencia_docx_pv or {}).get("titulo") or "").strip()
        titulo_escopo = str((escopo_pv or {}).get("titulo") or "").strip()
        if titulo_referencia:
            tema = titulo_referencia
            material_digital = dependencias.material_aula_com_titulo_fn(
                numero_aula,
                tema,
            )
        elif dependencias.titulo_escopo_projeto_vida_confiavel_fn(titulo_escopo):
            tema = titulo_escopo
            material_digital = dependencias.material_aula_com_titulo_fn(
                numero_aula,
                tema,
            )

    return numero_aula, tema, material_digital, objetivos_orientacao, aprendizagem_orientacao


def preparar_contexto_aula_pdf(
    *,
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    bimestre: str,
    indice_aula: int,
    modalidade_eja: bool,
    dependencias: DependenciasContextoAulaPDF,
    caminho_pptx_correspondente: str | None = None,
) -> dict:
    texto, tema, material_digital, numero_aula, metadados_fonte = (
        _resolver_fonte_extracao(
            caminho_pdf,
            disciplina,
            turma,
            caminho_pptx_correspondente,
            dependencias,
        )
    )
    fonte_extracao = metadados_fonte["fonte_extracao"]
    arquivo_fonte_extracao = metadados_fonte["arquivo_fonte_extracao"]
    blocos_pptx = metadados_fonte["blocos_pptx"]

    # Algumas turmas CDP usam o cadastro disciplinar comum (por exemplo,
    # ``Geografia``) e se diferenciam apenas pela pasta dos PDFs (``CDP_EM``
    # ou ``CDP_EF``).  O caminho faz parte do contexto da aula e precisa
    # ativar as mesmas regras do cadastro explícito de CDP, sem contaminar as
    # pastas regulares da disciplina.
    cdp_disciplina_cadastrada = dependencias.eh_cdp_contextual_disciplina_fn(disciplina)
    caminho_pdf_contextual = caminho_pdf
    cdp_caminho_pdf = dependencias.eh_cdp_contextual_disciplina_fn(caminho_pdf)
    if not cdp_caminho_pdf:
        # Uploads manuais recebem um caminho temporario e, so pelo nome, nao
        # revelam se vieram de ``CDP_EM``/``CDP_EF``. Recuperamos o PDF oficial
        # pelo nome antes de decidir qual pipeline e qual referencia usar.
        try:
            from core.seletor_referencias import resolver_caminho_pdf_original

            caminho_resolvido = resolver_caminho_pdf_original(
                caminho_pdf,
                disciplina,
                turma,
            )
        except Exception:
            caminho_resolvido = None
        if caminho_resolvido:
            caminho_pdf_contextual = str(caminho_resolvido)
            cdp_caminho_pdf = dependencias.eh_cdp_contextual_disciplina_fn(
                caminho_pdf_contextual
            )
    cdp_contextual = cdp_disciplina_cadastrada or cdp_caminho_pdf
    disciplina_base_cadastro = dependencias.disciplina_base_cdp_por_cadastro_fn(disciplina)
    if disciplina_base_cadastro:
        disciplina_base = disciplina_base_cadastro
    elif cdp_caminho_pdf and not cdp_disciplina_cadastrada:
        # Quando o cadastro usa o nome comum ("Geografia", "História" etc.),
        # ele é a fonte confiável da disciplina; o caminho só acrescenta o
        # contexto CDP. Isso evita que palavras do texto do livro mudem o
        # componente curricular.
        disciplina_base = disciplina
    else:
        disciplina_base = (
            dependencias.disciplina_base_cdp_contextual_fn(texto, tema, caminho_pdf)
            if cdp_contextual
            else disciplina
        )
    perfil = dependencias.perfil_disciplina_fn(disciplina_base, turma=turma)

    dados_plan = dependencias.obter_dados_aprofundamento_fn(
        disciplina_base,
        numero_aula,
        turma=turma,
        bimestre=bimestre,
    )
    if dados_plan and dados_plan.get("titulo"):
        tema = dados_plan["titulo"]
        material_digital = f"AULA {numero_aula} - {tema}"

    # Nos PDFs CDP, o nome do arquivo e a fonte mais confiavel para o titulo:
    # o texto interno pode misturar unidade, pagina e cabecalhos do livro.
    if cdp_contextual and cdp_caminho_pdf:
        from core.cdp.gerador_cdp import titulo_cdp_por_caminho

        titulo_arquivo_cdp = titulo_cdp_por_caminho(caminho_pdf)
        if titulo_arquivo_cdp:
            tema = titulo_arquivo_cdp
            material_digital = titulo_arquivo_cdp

    if perfil == "orientacao_estudos":
        texto, tema, material_digital = dependencias.resolver_contexto_orientacao_estudos_fn(
            caminho_pdf=caminho_pdf,
            texto=texto,
            tema=tema,
            material_digital=material_digital,
            indice_aula=indice_aula,
        )

    objetivos_orientacao = (
        dependencias.buscar_objetivos_orientacao_estudos_fn(
            caminho_pdf=caminho_pdf,
            tema=tema,
        )
        if perfil == "orientacao_estudos"
        else []
    )
    aprendizagem_orientacao = dependencias.formatar_objetivos_orientacao_estudos_fn(
        objetivos_orientacao,
    )
    extracao_pdf = dependencias.extracao_pdf_fn(
        texto,
        tema,
        disciplina=disciplina_base,
        numero_aula=numero_aula,
        turma=turma,
        bimestre=bimestre,
    )
    texto_prioritario_pdf = extracao_pdf.get("texto_prioritario") or texto
    if not str(numero_aula or "").strip():
        # Os PDFs CDP de Geografia usam nomes como ``01 - ATIVIDADE ...`` em
        # vez de ``AULA_01``. Preserve a ordem no plano final usando esse
        # prefixo numérico quando o conteúdo não traz um rótulo próprio.
        match_numero = re.match(r"^\s*(\d{1,3})(?:\s*[-_.])", Path(caminho_pdf).stem)
        if match_numero:
            numero_aula = str(int(match_numero.group(1)))
    tipo = dependencias.detectar_tipo_aula_fn(
        texto_prioritario_pdf,
        tema,
        disciplina_base,
        turma=turma,
    )
    metodologia_fixa_pdf = dependencias.metodologia_fixa_pdf_especial_fn(
        texto,
        disciplina_base,
        tema,
    )
    if not metodologia_fixa_pdf and fonte_extracao == "pptx":
        metodologia_fixa_pdf = dependencias.metodologia_por_blocos_estruturados_fn(
            blocos_pptx,
        )

    modalidade_eja_ativa = bool(
        modalidade_eja and dependencias.perfil_suporta_eja_fn(perfil)
    )
    eh_cdp_real = cdp_contextual or dependencias.eh_cdp_fn(disciplina)
    if eh_cdp_real:
        contexto_metodologico = "cdp_eja"
    elif modalidade_eja_ativa:
        contexto_metodologico = "eja_regular"
    else:
        contexto_metodologico = "regular"

    escopo_pv = (
        dependencias.buscar_item_projeto_vida_fn(turma, bimestre, numero_aula)
        if perfil == "projeto_de_vida"
        else {}
    )
    aprendizagem_pv = (
        dependencias.montar_aprendizagem_projeto_vida_fn(escopo_pv)
        if escopo_pv
        else ""
    )

    (
        numero_aula,
        tema,
        material_digital,
        objetivos_orientacao,
        aprendizagem_orientacao,
    ) = _ajustar_contexto_por_perfil(
        caminho_pdf=caminho_pdf,
        numero_aula=numero_aula,
        perfil=perfil,
        tema=tema,
        material_digital=material_digital,
        objetivos_orientacao=objetivos_orientacao,
        aprendizagem_orientacao=aprendizagem_orientacao,
        escopo_pv=escopo_pv,
        dependencias=dependencias,
    )

    # O extrator principal já entrega as palavras-chave candidatas do PDF.
    # A flag precisa indicar explicitamente quando a extração não produziu dados.
    palavras_chave_brutas = extracao_pdf.get("palavras_chave")
    palavras_chave_esperadas: list[str] = []
    if isinstance(palavras_chave_brutas, (list, tuple, set)):
        vistos_palavras_chave: set[str] = set()
        for palavra in palavras_chave_brutas:
            texto_palavra = str(palavra or "").strip()
            chave_palavra = texto_palavra.casefold()
            if texto_palavra and chave_palavra not in vistos_palavras_chave:
                vistos_palavras_chave.add(chave_palavra)
                palavras_chave_esperadas.append(texto_palavra)
    esboco_pdf: list[str] = []
    ancoras_pdf: list[str] = []
    caminho_docx_aux = None
    extracao_palavras_chave_ok = bool(palavras_chave_esperadas)

    return {
        "texto": texto,
        "tema": tema,
        "material_digital": material_digital,
        "numero_aula": numero_aula,
        "cdp_contextual": cdp_contextual,
        "caminho_pdf_contextual": caminho_pdf_contextual,
        "disciplina_base": disciplina_base,
        "perfil": perfil,
        "objetivos_orientacao": objetivos_orientacao,
        "aprendizagem_orientacao": aprendizagem_orientacao,
        "extracao_pdf": extracao_pdf,
        "tipo": tipo,
        "metodologia_fixa_pdf": metodologia_fixa_pdf,
        "modalidade_eja_ativa": modalidade_eja_ativa,
        "contexto_metodologico": contexto_metodologico,
        "escopo_pv": escopo_pv,
        "aprendizagem_pv": aprendizagem_pv,
        "fonte_extracao": fonte_extracao,
        "arquivo_fonte_extracao": arquivo_fonte_extracao,
        "palavras_chave_esperadas": palavras_chave_esperadas,
        "extracao_palavras_chave_ok": extracao_palavras_chave_ok,
        "caminho_docx_auxiliar": str(caminho_docx_aux) if caminho_docx_aux else None,
        "esboco_pdf": esboco_pdf,
        "ancoras_pdf": ancoras_pdf,
    }
