from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from core.estrutura_metodologia import validar_etapas_obrigatorias
from core.refino_referencia_docx import validar_refino_ia_do_docx


@dataclass
class DependenciasResultadosAula:
    referencia_docx_por_perfil_fn: Callable[[str, str, str, str], dict | None]
    localizar_docx_referencia_por_perfil_fn: Callable[[str, str, str], object | None]
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
    adaptar_listas_eja_fn: Callable[[list[str], list[str], str, str], tuple[list[str], list[str]]] | None = None


_CDP_MAX_DESENVOLVIMENTO_CHARS = 1200
_CDP_MAX_ETAPA_CHARS = 330
_CDP_MAX_ITEM_CHARS = 180


def _encurtar_texto_cdp(texto: str, limite: int) -> str:
    """Mantem frases completas e evita colunas longas no modelo Word."""
    texto = re.sub(r"\s+", " ", str(texto or "")).strip(" ,;:-")
    if len(texto) <= limite:
        return texto
    frases = re.split(r"(?<=[.!?])\s+", texto)
    acumulado = ""
    for frase in frases:
        candidato = f"{acumulado} {frase}".strip()
        if len(candidato) > limite:
            break
        acumulado = candidato
    if acumulado:
        return acumulado.rstrip(" ,;:-")
    corte = texto[: max(1, limite - 1)].rsplit(" ", 1)[0].strip(" ,;:-")
    return corte or texto[:limite].rstrip(" ,;:-")


def _sanitizar_agrupamento_cdp(texto: str) -> str:
    texto = re.sub(
        r"\b(?:debate|debates|discussao|discussao|conversa)\s+(?:entre|com)\s+(?:colegas?|estudantes?)\b",
        "reflexao individual",
        texto,
        flags=re.I,
    )
    texto = re.sub(
        r"\b(?:em|nas?|nos?)\s+(?:duplas?|pares?|grupos?|equipes?)(?:\s+de\s+\w+)?",
        "individualmente",
        texto,
        flags=re.I,
    )
    texto = re.sub(
        r"\b(?:grupos?|equipes?|duplas?|pares?)\s+(?:de|para)\s+\w+",
        "atividade individual",
        texto,
        flags=re.I,
    )
    texto = re.sub(r"\b(?:com|entre)\s+colegas?\b", "individualmente", texto, flags=re.I)
    texto = re.sub(r"\b(?:colaborativa(?:mente)?|cooperativa(?:mente)?)\b", "individual", texto, flags=re.I)
    return re.sub(r"\s+", " ", texto).strip()


def _normalizar_colunas_cdp(
    acompanhamento: list[str],
    acessibilidade: list[str],
    *,
    perfil: str,
    tema: str,
) -> tuple[list[str], list[str]]:
    """Aplica as restricoes institucionais do CDP nas duas listas finais.

    A IA deve escrever as listas, mas esta ultima camada garante que uma
    resposta que mencione tecnologia, Lemov ou agrupamentos nao chegue ao
    documento final e que o contrato de tres itens seja mantido.
    """
    from core.cdp.gerador_cdp import (
        acompanhamento_cdp_contextual,
        acessibilidade_cdp_contextual,
    )
    from core.qualidade_metodologica import sanitizar_texto_cdp_estrito

    def preparar(itens: list[str], fallback: list[str]) -> list[str]:
        saida: list[str] = []
        vistos: set[str] = set()
        for item in list(itens or []):
            texto = _sanitizar_agrupamento_cdp(
                sanitizar_texto_cdp_estrito(str(item or ""))
            )
            texto = _encurtar_texto_cdp(texto, _CDP_MAX_ITEM_CHARS)
            if texto and not texto.endswith((".", "!", "?")):
                texto += "."
            chave = re.sub(r"\s+", " ", texto).strip().casefold()
            if texto and chave not in vistos:
                vistos.add(chave)
                saida.append(texto)
        for item in fallback:
            texto = _encurtar_texto_cdp(
                _sanitizar_agrupamento_cdp(sanitizar_texto_cdp_estrito(str(item or ""))),
                _CDP_MAX_ITEM_CHARS,
            )
            if texto and not texto.endswith((".", "!", "?")):
                texto += "."
            chave = re.sub(r"\s+", " ", texto).strip().casefold()
            if texto and chave not in vistos:
                vistos.add(chave)
                saida.append(texto)
            if len(saida) >= 3:
                break
        return saida[:3]

    fallback_acompanhamento = acompanhamento_cdp_contextual(perfil, tema, tema, 0)
    fallback_acessibilidade = acessibilidade_cdp_contextual(perfil, tema, tema, 0)
    return (
        preparar(acompanhamento, fallback_acompanhamento),
        preparar(acessibilidade, fallback_acessibilidade),
    )


def _normalizar_metodologia_cdp(metodologia: list[dict]) -> list[dict]:
    """Limpa sobras deixadas ao retirar recursos proibidos no CDP."""
    from core.qualidade_metodologica import sanitizar_texto_cdp_estrito

    saida: list[dict] = []
    caracteres_restantes = _CDP_MAX_DESENVOLVIMENTO_CHARS
    for item in list(metodologia or []):
        if not isinstance(item, dict):
            continue
        texto = _sanitizar_agrupamento_cdp(
            sanitizar_texto_cdp_estrito(str(item.get("texto", "")))
        )
        # Retirar finais como "e fazer" quando a ação seguinte era um nome
        # de técnica que acabou de ser removido.
        texto = re.sub(
            r"\s+(?:e|ou|para)\s+(?:fazer|realizar|discutir|compartilhar)\s*[.!?]?$",
            ".",
            texto,
            flags=re.I,
        )
        texto = re.sub(r"\s+([.,;:?])", r"\1", texto).strip(" ,;:-")
        limite_etapa = min(_CDP_MAX_ETAPA_CHARS, caracteres_restantes)
        texto = _encurtar_texto_cdp(texto, limite_etapa)
        if texto and not texto.endswith((".", "!", "?")):
            texto += "."
        if texto:
            saida.append({"titulo": str(item.get("titulo") or "Desenvolvimento").strip(), "texto": texto})
            caracteres_restantes -= len(texto)
            if caracteres_restantes <= 0:
                break
    return saida


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
    arquivo_referencia_docx = dependencias.localizar_docx_referencia_por_perfil_fn(
        caminho_pdf,
        disciplina_base,
        turma,
    )
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
        habilidade_pdf_ou_planilha = dependencias.resolver_habilidade_portugues_fn(
            habilidade,
            caminho_pdf,
            numero_aula,
        )
        habilidade = habilidade_pdf_ou_planilha or habilidade_referencia
    return {
        "referencia_docx": referencia_docx,
        "arquivo_referencia_docx": str(arquivo_referencia_docx or ""),
        "habilidade_referencia": habilidade_referencia,
        "extracao": extracao,
        "tipo": tipo,
        "habilidade": habilidade,
    }


def _registrar_proveniencia_docx(
    aula: dict,
    *,
    referencia_docx: dict | None,
    arquivo_referencia_docx: str,
    status_sucesso: str = "",
    literal: bool = False,
) -> dict:
    fonte = str((referencia_docx or {}).get("fonte") or arquivo_referencia_docx or "").strip()
    if referencia_docx:
        aula["status_referencia_docx"] = status_sucesso or "docx_literal"
        aula["arquivo_referencia_docx"] = fonte
        aula["motivo_referencia_docx"] = ""
        aula["texto_central_copiado_literalmente"] = bool(literal)
        return aula

    aula["arquivo_referencia_docx"] = fonte
    aula["texto_central_copiado_literalmente"] = False
    if fonte:
        aula["status_referencia_docx"] = "aula_ausente_ou_incompleta"
        aula["motivo_referencia_docx"] = (
            "A aula correspondente nao foi encontrada completa no DOCX externo. "
            "Foi utilizado o motor local para esta aula."
        )
    else:
        aula["status_referencia_docx"] = "docx_ausente"
        aula["motivo_referencia_docx"] = (
            "Nenhum DOCX externo de metodologia foi localizado na pasta do PDF. "
            "Foi utilizado o motor local para esta aula."
        )
    return aula


def _registrar_aviso_referencia_metodologica_ia(aula: dict, plano_ia: dict) -> dict:
    """Leva para a conferencia o aviso da referencia complementar ausente."""
    aviso = str((plano_ia or {}).get("_aviso_referencia_metodologica") or "").strip()
    if not aviso:
        return aula

    avisos = list(aula.get("avisos_validacao") or [])
    if aviso not in avisos:
        avisos.append(aviso)
    aula["avisos_validacao"] = avisos

    diagnostico = dict(aula.get("diagnostico_geracao") or {})
    diagnostico["referencia_metodologica"] = {
        "status": "ausente",
        "aviso": aviso,
    }
    aula["diagnostico_geracao"] = diagnostico
    return aula


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
    modalidade_eja_ativa: bool = False,
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

    if modalidade_eja_ativa and dependencias.adaptar_listas_eja_fn:
        acompanhamento, acessibilidade = dependencias.adaptar_listas_eja_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
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


def _montar_resultado_referencia_docx_exata(
    *,
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    perfil: str,
    aprendizagem: str,
    referencia_docx: dict,
    provedor_ia: str,
    usar_ia: bool,
    ia_erro: str,
    indice_aula: int,
    total_aulas: int,
    dependencias: DependenciasResultadosAula,
    aviso_sucesso: str,
    modalidade_eja_ativa: bool = False,
) -> dict:
    metodologia = list(referencia_docx.get("metodologia") or [])
    if not usar_ia:
        limite_metodologia = 350
        etapas_excedentes = []
        for item in metodologia:
            if isinstance(item, dict):
                txt = str(item.get("texto", "")).strip()
                if len(txt) > limite_metodologia:
                    tit = str(item.get("titulo", "Etapa")).strip()
                    etapas_excedentes.append(f"'{tit}' ({len(txt)} caracteres)")
        if etapas_excedentes:
            fonte = str(referencia_docx.get("fonte") or "DOCX de referência").strip()
            detalhes = ", ".join(etapas_excedentes)
            mensagem_limite = (
                f"O arquivo .docx de referência ({fonte}) contém etapa(s) da metodologia "
                f"que excede(m) o limite máximo de 350 caracteres: {detalhes}. "
                f"Para prosseguir, selecione a opção 'Com IA' para que o sistema refine a metodologia "
                f"automaticamente até 350 caracteres, ou edite o arquivo .docx ajustando o tamanho do texto."
            )
            raise ValueError(mensagem_limite.replace("350 caracteres", f"{limite_metodologia} caracteres"))
    metodologia_valida, motivo_metodologia = validar_etapas_obrigatorias(metodologia)
    if not metodologia_valida:
        raise ValueError(motivo_metodologia)
    acompanhamento = list(referencia_docx.get("acompanhamento") or [])[:3]
    acessibilidade = list(referencia_docx.get("acessibilidade") or [])[:3]
    listas_ausentes = len(acompanhamento) < 3 or len(acessibilidade) < 3
    if listas_ausentes:
        desenvolvimento = dependencias.texto_metodologia_fn(metodologia)
        etapas_titulos = [item.get("titulo", "") for item in metodologia if isinstance(item, dict)]
        acompanhamento = dependencias.gerar_acompanhamento_aprimorado_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo="regular",
            habilidade=aprendizagem,
            etapas_metodologia=etapas_titulos,
        )
        acessibilidade = dependencias.gerar_acessibilidade_aprimorada_fn(
            tema=tema,
            aprendizagem=aprendizagem,
            desenvolvimento=desenvolvimento,
            disciplina=disciplina_base,
            perfil=perfil,
            tipo="regular",
            habilidade=aprendizagem,
            etapas_metodologia=etapas_titulos,
        )
    literal = not modalidade_eja_ativa
    if modalidade_eja_ativa and dependencias.adaptar_listas_eja_fn:
        metodologia = dependencias.adaptar_metodologia_eja_fn(
            metodologia,
            perfil,
            tema,
            texto,
            dependencias.detectar_tecnicas_lemov_fn(texto, tema),
            dependencias.garantir_tecnicas_lemov_na_metodologia_fn,
        )
        acompanhamento, acessibilidade = dependencias.adaptar_listas_eja_fn(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    recursos_reais = dependencias.detectar_recursos_reais_fn(texto)
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
            or "docx_referencia_externa"
        ),
        "fonte_referencia_metodologia": referencia_docx.get("fonte", ""),
        "ia_usada": False,
        "ia_provedor": provedor_ia if usar_ia else "",
        "ia_erro": ia_erro if not usar_ia else "",
        "recursos_detectados": recursos_reais,
        "texto_fonte": texto,
        "diagnostico_geracao": {
            "metodologia_local": metodologia,
            "metodologia_ia_crua": [],
            "metodologia_higienizada": metodologia,
            "metodologia_final": metodologia,
        },
        "indice_aula": indice_aula,
        "total_aulas": total_aulas,
    }
    aula_gerada["avisos_validacao"] = list(
        dependencias.validar_aula_final_fn(aula_gerada) or []
    )
    aula_gerada["avisos_validacao"].append(
        "Metodologia, acompanhamento e acessibilidade do DOCX foram refinados para EJA."
        if modalidade_eja_ativa
        else (
            "Metodologia copiada do DOCX; acompanhamento e acessibilidade foram gerados pelo sistema."
            if listas_ausentes
            else aviso_sucesso
        )
    )
    return _registrar_proveniencia_docx(
        aula_gerada,
        referencia_docx=referencia_docx,
        arquivo_referencia_docx=str(referencia_docx.get("fonte") or ""),
        status_sucesso="docx_refinado_eja" if modalidade_eja_ativa else "docx_literal",
        literal=literal,
    )


def _montar_resultado_sem_referencia_docx(
    *,
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    perfil: str,
    aprendizagem: str,
    origem_sem_referencia: str,
    provedor_ia: str,
    usar_ia: bool,
    ia_erro: str,
    indice_aula: int,
    total_aulas: int,
    dependencias: DependenciasResultadosAula,
    aviso_ausencia: str,
) -> dict:
    recursos_reais = dependencias.detectar_recursos_reais_fn(texto)
    aula_gerada = {
        "disciplina": disciplina_base,
        "tema": tema,
        "material": material_digital,
        "numero_aula": numero_aula,
        "aprendizagem": aprendizagem,
        "metodologia": [],
        "acompanhamento": [],
        "acessibilidade": [],
        "origem_metodologia": origem_sem_referencia,
        "fonte_referencia_metodologia": "",
        "ia_usada": False,
        "ia_provedor": provedor_ia if usar_ia else "",
        "ia_erro": ia_erro if not usar_ia else "",
        "recursos_detectados": recursos_reais,
        "texto_fonte": texto,
        "diagnostico_geracao": {
            "metodologia_local": [],
            "metodologia_ia_crua": [],
            "metodologia_higienizada": [],
            "metodologia_final": [],
        },
        "indice_aula": indice_aula,
        "total_aulas": total_aulas,
    }
    aula_gerada["avisos_validacao"] = list(
        dependencias.validar_aula_final_fn(aula_gerada) or []
    )
    aula_gerada["avisos_validacao"].append(aviso_ausencia)
    return _registrar_proveniencia_docx(
        aula_gerada,
        referencia_docx=None,
        arquivo_referencia_docx="",
    )


def _perfil_referencia_docx_estrita(
    dependencias: DependenciasResultadosAula,
    perfil: str,
) -> bool:
    return bool(dependencias.origem_metodologia_por_referencia_fn(perfil))


def _origem_sem_referencia_docx(
    dependencias: DependenciasResultadosAula,
    perfil: str,
) -> str:
    origem = str(dependencias.origem_metodologia_por_referencia_fn(perfil) or "").strip()
    if origem.startswith("docx_referencia_"):
        return origem.replace("docx_referencia_", "referencia_docx_", 1) + "_ausente"
    if perfil:
        return f"referencia_docx_{perfil}_ausente"
    return "referencia_docx_ausente"


def _resultado_referencia_docx_estrita(
    *,
    texto: str,
    tema: str,
    material_digital: str,
    numero_aula: str,
    disciplina_base: str,
    perfil: str,
    aprendizagem: str,
    referencia_docx: dict | None,
    provedor_ia: str,
    usar_ia: bool,
    ia_erro: str,
    indice_aula: int,
    total_aulas: int,
    dependencias: DependenciasResultadosAula,
) -> dict:
    nome_disciplina = str(disciplina_base or perfil or "Disciplina").strip() or "Disciplina"
    if referencia_docx:
        return _montar_resultado_referencia_docx_exata(
            texto=texto,
            tema=tema,
            material_digital=material_digital,
            numero_aula=numero_aula,
            disciplina_base=disciplina_base,
            perfil=perfil,
            aprendizagem=aprendizagem,
            referencia_docx=referencia_docx,
            provedor_ia=provedor_ia,
            usar_ia=usar_ia,
            ia_erro=ia_erro,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            dependencias=dependencias,
            aviso_sucesso=(
                f"{nome_disciplina}: metodologia, acompanhamento da aprendizagem e "
                "acessibilidade foram copiados exatamente do arquivo .docx de referencia da pasta."
            ),
        )
    return _montar_resultado_sem_referencia_docx(
        texto=texto,
        tema=tema,
        material_digital=material_digital,
        numero_aula=numero_aula,
        disciplina_base=disciplina_base,
        perfil=perfil,
        aprendizagem=aprendizagem,
        origem_sem_referencia=_origem_sem_referencia_docx(dependencias, perfil),
        provedor_ia=provedor_ia,
        usar_ia=usar_ia,
        ia_erro=ia_erro,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        dependencias=dependencias,
        aviso_ausencia=(
            f"{nome_disciplina}: nao encontrei o arquivo .docx de referencia na pasta do PDF. "
            "Sem essa referencia, a disciplina nao gera metodologia interna."
        ),
    )


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
    arquivo_referencia_docx = base["arquivo_referencia_docx"]
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

    if (
        _perfil_referencia_docx_estrita(dependencias, perfil)
        and not referencia_docx
    ):
        return _resultado_referencia_docx_estrita(
            texto=texto,
            tema=tema,
            material_digital=material_digital,
            numero_aula=numero_aula,
            disciplina_base=disciplina_base,
            perfil=perfil,
            aprendizagem=aprendizagem,
            referencia_docx=None,
            provedor_ia=provedor_ia,
            usar_ia=True,
            ia_erro="",
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            dependencias=dependencias,
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
    if metodologia_ia:
        tecnicas_lemov_pdf = dependencias.detectar_tecnicas_lemov_fn(texto, tema)
        if (
            perfil not in {"projeto_de_vida", "lideranca_oratoria", "sociologia"}
            and contexto_metodologico != "cdp_eja"
        ):
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
            consolidar=(
                perfil != "leitura_redacao"
                and not modalidade_eja_ativa
                and contexto_metodologico != "cdp_eja"
            ),
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
        if modalidade_eja_ativa:
            metodologia = dependencias.adaptar_metodologia_eja_fn(
                metodologia,
                perfil,
                tema,
                texto,
                dependencias.detectar_tecnicas_lemov_fn(texto, tema),
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

    refino_docx_valido, motivo_refino_docx = validar_refino_ia_do_docx(
        referencia_docx,
        plano_ia,
    )
    if referencia_docx and not refino_docx_valido:
        metodologia = list(referencia_docx.get("metodologia") or [])
        acompanhamento = list(referencia_docx.get("acompanhamento") or [])[:3]
        acessibilidade = list(referencia_docx.get("acessibilidade") or [])[:3]

    aplicar_referencia_docx = bool(
        referencia_docx
        and (
            not refino_docx_valido
            or dependencias.deve_aplicar_referencia_docx_no_resultado_ia_fn(
                perfil,
                plano_ia,
            )
        )
    )
    if aplicar_referencia_docx:
        sobrescrever_metodologia = False
        if sobrescrever_metodologia or not metodologia:
            metodologia = dependencias.naturalizar_metodologia_professor_fn(
                referencia_docx.get("metodologia") or [],
                perfil=perfil,
            )
        if not acompanhamento:
            acompanhamento = list(referencia_docx.get("acompanhamento") or [])[:3]
        if not acessibilidade:
            acessibilidade = list(referencia_docx.get("acessibilidade") or [])[:3]

    if contexto_metodologico == "cdp_eja":
        metodologia = _normalizar_metodologia_cdp(metodologia)
        acompanhamento, acessibilidade = _normalizar_colunas_cdp(
            acompanhamento,
            acessibilidade,
            perfil=perfil,
            tema=tema,
        )

    diagnostico_geracao = {
        "metodologia_local": metodologia_local,
        "metodologia_ia_crua": metodologia_ia_crua,
        "metodologia_higienizada": (
            metodologia_higienizada_temp or (metodologia_ia if metodologia_ia else [])
        ),
        "metodologia_final": metodologia,
        "refino_referencia_docx": {
            "valido": refino_docx_valido,
            "motivo": motivo_refino_docx,
        },
    }

    resultado = _finalizar_resultado(
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
        modalidade_eja_ativa=modalidade_eja_ativa,
    )
    resultado = _registrar_proveniencia_docx(
        resultado,
        referencia_docx=referencia_docx,
        arquivo_referencia_docx=arquivo_referencia_docx,
        status_sucesso=(
            "docx_refinado_ia"
            if refino_docx_valido
            else "docx_preservado_refino_ia_invalido"
        ),
        literal=False,
    )
    return _registrar_aviso_referencia_metodologica_ia(resultado, plano_ia)


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
    arquivo_referencia_docx = base["arquivo_referencia_docx"]
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

    if (
        _perfil_referencia_docx_estrita(dependencias, perfil)
        and not referencia_docx
    ):
        return _resultado_referencia_docx_estrita(
            texto=texto,
            tema=tema,
            material_digital=material_digital,
            numero_aula=numero_aula,
            disciplina_base=disciplina_base,
            perfil=perfil,
            aprendizagem=aprendizagem,
            referencia_docx=None,
            provedor_ia=provedor_ia,
            usar_ia=usar_ia,
            ia_erro=ia_erro,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            dependencias=dependencias,
        )

    if referencia_docx:
        return _montar_resultado_referencia_docx_exata(
            texto=texto,
            tema=tema,
            material_digital=material_digital,
            numero_aula=numero_aula,
            disciplina_base=disciplina_base,
            perfil=perfil,
            aprendizagem=aprendizagem,
            referencia_docx=referencia_docx,
            provedor_ia=provedor_ia,
            usar_ia=usar_ia,
            ia_erro=ia_erro,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            dependencias=dependencias,
            aviso_sucesso=(
                f"{disciplina_base}: metodologia, acompanhamento da aprendizagem e "
                "acessibilidade foram copiados literalmente do DOCX externo."
            ),
            modalidade_eja_ativa=modalidade_eja_ativa,
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
        if modalidade_eja_ativa:
            metodologia = dependencias.adaptar_metodologia_eja_fn(
                metodologia,
                perfil,
                tema,
                texto,
                dependencias.detectar_tecnicas_lemov_fn(texto, tema),
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
        if (
            perfil not in {"projeto_de_vida", "lideranca_oratoria", "sociologia"}
            and contexto_metodologico != "cdp_eja"
        ):
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
            consolidar=(
                not modalidade_eja_ativa
                and contexto_metodologico != "cdp_eja"
            ),
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

    if contexto_metodologico == "cdp_eja":
        metodologia = _normalizar_metodologia_cdp(metodologia)
        acompanhamento, acessibilidade = _normalizar_colunas_cdp(
            acompanhamento,
            acessibilidade,
            perfil=perfil,
            tema=tema,
        )

    diagnostico_geracao = {
        "metodologia_local": metodologia_local,
        "metodologia_ia_crua": [],
        "metodologia_higienizada": metodologia_higienizada_temp or (metodologia if metodologia else []),
        "metodologia_final": metodologia,
    }

    resultado = _finalizar_resultado(
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
        aplicar_referencia_docx=False,
        marcar_origem_referencia=False,
        origem_sem_referencia="motor_local",
        ia_usada=False,
        ia_provedor_registrado=provedor_ia if usar_ia else "",
        ia_erro=ia_erro,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        diagnostico_geracao=diagnostico_geracao,
        dependencias=dependencias,
        modalidade_eja_ativa=modalidade_eja_ativa,
    )
    return _registrar_proveniencia_docx(
        resultado,
        referencia_docx=None,
        arquivo_referencia_docx=arquivo_referencia_docx,
    )
