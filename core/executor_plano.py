from __future__ import annotations

import logging
import json
import hashlib
import os
import tempfile
import threading
from pathlib import Path
from typing import Callable, Mapping, Sequence

from core.models import PlanoCompleto
from core.revisao_final import gravar_sidecar_json, revisar_aula_gerada
from core.seguranca_upload import PREFIXO_PDF_TEMPORARIO, nomes_pdf_original_possiveis

logger = logging.getLogger(__name__)

_CHECKPOINT_SCHEMA_VERSION = 2
_CHECKPOINT_LOCK = threading.RLock()


def finalizar_plano_aula(
    resultado_final: dict | PlanoCompleto,
    *,
    caminho_pdf: str = "",
    perfil: str = "",
    fonte_extracao: str = "pdf",
    arquivo_fonte_extracao: str = "",
    hash_fonte_extracao: str = "",
    fingerprint_contexto: str = "",
    assinatura_conteudo_cache: str = "",
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
    plano.assinatura_conteudo_cache = (
        assinatura_conteudo_cache or plano.assinatura_conteudo_cache
    )
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
    except Exception:
        logger.exception(
            "Falha na revisão final do plano; mantendo dados gerados e gravando sidecar bruto."
        )
    finally:
        plano = PlanoCompleto.from_any(dados_runtime)
        if caminho_pdf and hash_pdf:
            gravar_sidecar_json(caminho_pdf, plano, hash_pdf)

    return plano.to_dict()


def _json_estavel(valor: object) -> str:
    return json.dumps(
        valor,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _caminho_normalizado(caminho: str) -> str:
    return os.path.normcase(str(Path(caminho).resolve(strict=False)))


def _identidade_caminho_execucao(caminho: str) -> str:
    arquivo = Path(caminho)
    if arquivo.parent.name.startswith(PREFIXO_PDF_TEMPORARIO):
        candidatos = nomes_pdf_original_possiveis(arquivo.name)
        nome_original = candidatos[-1] if candidatos else arquivo.name
        return f"upload:{os.path.normcase(nome_original)}"
    return _caminho_normalizado(caminho)


def _hash_conteudo_arquivo(caminho: str) -> str:
    arquivo = Path(caminho)
    if not arquivo.is_file():
        return hashlib.sha256(_caminho_normalizado(caminho).encode("utf-8")).hexdigest()

    digest = hashlib.sha256()
    with arquivo.open("rb") as stream:
        for bloco in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _chave_execucao(
    caminhos_pdf: Sequence[str],
    divisoes: Sequence[bool],
    contexto: Mapping[str, object] | None,
) -> str:
    identidade = {
        "schema_version": _CHECKPOINT_SCHEMA_VERSION,
        "caminhos": [_identidade_caminho_execucao(caminho) for caminho in caminhos_pdf],
        "divisoes": list(divisoes),
        "contexto": dict(contexto or {}),
    }
    return hashlib.sha256(_json_estavel(identidade).encode("utf-8")).hexdigest()


def _obter_checkpoint_path(
    chave_execucao: str,
    checkpoint_dir: str | Path | None = None,
) -> Path:
    if checkpoint_dir is None:
        from config import BASE_DIR

        diretorio = BASE_DIR / ".checkpoints"
    else:
        diretorio = Path(checkpoint_dir)
    return diretorio / f"{chave_execucao}.json"


def _carregar_checkpoint(caminho: Path, chave_execucao: str) -> dict:
    if not caminho.exists():
        return {}
    try:
        with caminho.open("r", encoding="utf-8") as stream:
            dados = json.load(stream)
    except (OSError, ValueError, TypeError):
        logger.warning("Checkpoint inválido ignorado: %s", caminho)
        return {}
    if (
        not isinstance(dados, dict)
        or dados.get("schema_version") != _CHECKPOINT_SCHEMA_VERSION
        or dados.get("execution_key") != chave_execucao
        or not isinstance(dados.get("items"), dict)
    ):
        return {}
    return dados


def _gravar_json_atomico(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=caminho.parent,
            prefix=f".{caminho.stem}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporario = Path(stream.name)
            json.dump(dados, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink(missing_ok=True)


def _salvar_item_checkpoint(
    caminho: Path,
    chave_execucao: str,
    chave_item: str,
    item: dict,
) -> dict:
    with _CHECKPOINT_LOCK:
        dados = _carregar_checkpoint(caminho, chave_execucao)
        if not dados:
            dados = {
                "schema_version": _CHECKPOINT_SCHEMA_VERSION,
                "execution_key": chave_execucao,
                "items": {},
            }
        dados["items"][chave_item] = item
        _gravar_json_atomico(caminho, dados)
        return dados


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
    checkpoint_contexto: Mapping[str, object] | None = None,
    checkpoint_dir: str | Path | None = None,
    aula_restaurada_callback: Callable[[dict], None] | None = None,
) -> list[dict]:
    aulas = []
    caminhos = list(caminhos_pdf or [])
    total_aulas = len(caminhos)
    divisoes = [
        (
            bool(dividir_por_pdf[idx])
            if dividir_por_pdf and idx < len(dividir_por_pdf)
            else dividir_metodologia
        )
        for idx in range(total_aulas)
    ]
    chave_execucao = _chave_execucao(caminhos, divisoes, checkpoint_contexto)
    checkpoint_path = _obter_checkpoint_path(chave_execucao, checkpoint_dir)
    with _CHECKPOINT_LOCK:
        checkpoint_data = _carregar_checkpoint(checkpoint_path, chave_execucao)
    itens_checkpoint = checkpoint_data.get("items", {})

    for idx, caminho in enumerate(caminhos):
        if progress_callback:
            try:
                progress_callback(idx, total_aulas, caminho)
            except Exception:
                pass

        dividir_aula_atual = divisoes[idx]
        hash_conteudo = _hash_conteudo_arquivo(caminho)
        chave_item = f"{idx}:{hash_conteudo}:{int(dividir_aula_atual)}"

        item_restaurado = itens_checkpoint.get(chave_item)
        if item_restaurado and item_restaurado.get("dividir") == dividir_aula_atual:
            logger.info("Restaurando aula do checkpoint para: %s", caminho)
            aula_restaurada = item_restaurado["aula"]
            if dividir_aula_atual:
                aulas.extend(aula_restaurada)
                aula_para_callback = aula_restaurada[0] if aula_restaurada else None
            else:
                aulas.append(aula_restaurada)
                aula_para_callback = aula_restaurada
            if aula_restaurada_callback and isinstance(aula_para_callback, dict):
                try:
                    aula_restaurada_callback(aula_para_callback)
                except Exception:
                    logger.warning(
                        "Falha ao restaurar o estado derivado da aula em checkpoint: %s",
                        caminho,
                        exc_info=True,
                    )
            continue

        aula = gerar_aula_callback(caminho, idx, total_aulas, dividir_aula_atual)

        resultado_salvar = None
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

            resultado_salvar = [aula_primeiro, aula_segundo]
            aulas.extend(resultado_salvar)
        else:
            resultado_salvar = aula
            aulas.append(aula)
            
        item_checkpoint = {
            "caminho": str(caminho),
            "hash_conteudo": hash_conteudo,
            "dividir": dividir_aula_atual,
            "aula": resultado_salvar
        }
        try:
            checkpoint_data = _salvar_item_checkpoint(
                checkpoint_path,
                chave_execucao,
                chave_item,
                item_checkpoint,
            )
            itens_checkpoint = checkpoint_data["items"]
        except Exception as exc:
            logger.warning("Falha ao salvar checkpoint: %s", exc)

    with _CHECKPOINT_LOCK:
        try:
            checkpoint_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            logger.warning("Falha ao remover checkpoint concluído: %s", exc)

    return aulas
