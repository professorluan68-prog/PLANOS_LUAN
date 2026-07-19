#!/usr/bin/env python3
"""Planeja, aplica, valida e reverte a padronizacao de nomes dos PDFs oficiais.

O script trabalha somente dentro da raiz informada, nunca altera o conteudo dos
PDFs e exige um manifesto com hash SHA-256 antes de qualquer renomeacao.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ROOT = Path(r"C:\Users\Luan Dias\PLANOS_LUAN_DADOS\PDF_AULAS")
DEFAULT_MANIFEST_ROOT = DEFAULT_ROOT.parent / "MANIFESTOS_RENOMEACAO"
MANIFEST_VERSION = 1
MAX_FULL_PATH = 240
MAX_TITLE_LENGTH = 70

READY_STATUSES = {"ready_filename", "ready_json", "ready_pdf_text"}
TERMINAL_STATUSES = READY_STATUSES | {"already_normalized"}
PHASE_ONE_STATUSES = {"ready_filename", "ready_json"}
PHASE_TWO_STATUSES = {"ready_pdf_text"}

EXCLUDED_DIRECTORY_MARKERS = (
    "BACKUP",
    "COPIA",
    "ANTIGO",
    "ANTIGA",
    "EXCLUIR",
    "TEMPORARIO",
    "TEMPORARIA",
)

STAGE_MAP = {
    "AF": "EF_AF",
    "EF": "EF",
    "EM": "EM",
    "EJA": "EJA",
}

DISCIPLINE_ALIASES = {
    "BIOLOGIA": ("BIO",),
    "CIENCIAS": ("CIE",),
    "FISICA": ("FIS",),
    "GEOGRAFIA": ("GEO",),
    "HISTORIA": ("HIS",),
    "LINGUA_INGLESA": ("ING", "LI"),
    "LINGUA_PORTUGUESA": ("PORTUGUES", "LP"),
    "MATEMATICA": ("MAT",),
    "QUIMICA": ("QUI",),
}

GENERIC_TITLES = {
    "AULA",
    "AULA_KHAN",
    "COMPONENTE",
    "DISCIPLINA",
    "MATERIAL_DIGITAL",
    "SEM_TITULO",
    "MAPA_DO_COMPONENTE",
    "VOCE_ESTA_AQUI",
}

LESSON_RE = re.compile(
    r"(?i)(?:^|[^A-Z0-9])AULA[_\s-]*(\d{1,4})(?:[.,](\d+))?"
)
PAIR_RE = re.compile(
    r"(?i)AULAS?[_\s-]*(\d{1,4})"
    r"(?:[_\s-]+(?:E|A|ATE|&)[_\s-]+|_(?!_)|-|\s+)"
    r"(\d{1,4})(?:\D|$)"
)
BIMESTER_RE = re.compile(r"^(\d+)_BIMESTRE$", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ascii_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char))


def clean_component(value: Any) -> str:
    text = ascii_text(value).upper().replace("&", " E ")
    text = re.sub(r"[^A-Z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def clean_display_line(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def relative_text(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("/", "\\")


def safe_path(root: Path, relative: str) -> Path:
    root_resolved = root.resolve(strict=True)
    candidate = (root_resolved / Path(relative)).resolve(strict=False)
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Caminho fora da raiz autorizada: {relative}") from exc
    return candidate


def parse_structure(relative_pdf: Path) -> tuple[dict[str, str] | None, str]:
    parts = relative_pdf.parts
    directories = parts[:-1]
    normalized_dirs = [clean_component(part) for part in directories]

    if any(
        marker in directory
        for directory in normalized_dirs
        for marker in EXCLUDED_DIRECTORY_MARKERS
    ):
        return None, "pasta marcada como backup/copia/antiga"

    if len(parts) != 5:
        return None, "estrutura diferente de disciplina/etapa/bimestre/turma"

    discipline = clean_component(parts[0])
    stage_raw = clean_component(parts[1])
    bimester_match = BIMESTER_RE.fullmatch(clean_component(parts[2]))
    class_name = clean_component(parts[3])
    structure_type = "standard"

    if stage_raw in STAGE_MAP and bimester_match:
        pass
    elif BIMESTER_RE.fullmatch(clean_component(parts[1])) and clean_component(
        parts[2]
    ) in STAGE_MAP:
        structure_type = "bimester_before_stage"
        bimester_match = BIMESTER_RE.fullmatch(clean_component(parts[1]))
        stage_raw = clean_component(parts[2])
    elif discipline == "CDP_ENSINO_MEDIO" and BIMESTER_RE.fullmatch(
        clean_component(parts[2])
    ):
        structure_type = "cdp"
        discipline = clean_component(parts[1])
        stage_raw = "EM"
        bimester_match = BIMESTER_RE.fullmatch(clean_component(parts[2]))
        class_name = clean_component(parts[3])
    else:
        return None, "etapa ou bimestre nao reconhecido na estrutura"

    if not discipline or not class_name or not bimester_match:
        return None, "metadados estruturais incompletos"

    return (
        {
            "discipline": discipline,
            "stage": STAGE_MAP[stage_raw],
            "bimester": f"B{int(bimester_match.group(1))}",
            "class": class_name,
            "structure_type": structure_type,
        },
        "",
    )


def parse_lesson_from_name(stem: str) -> tuple[int | None, str]:
    pair = PAIR_RE.search(stem)
    if pair:
        return int(pair.group(1)), f"arquivo representa as aulas {pair.group(1)} e {pair.group(2)}"

    match = LESSON_RE.search(stem)
    if not match:
        return None, "numero de aula ausente no nome"
    if match.group(2):
        return int(match.group(1)), f"numero fracionado {match.group(1)}.{match.group(2)}"
    return int(match.group(1)), ""


def strip_lesson_prefix(value: str) -> str:
    text = clean_display_line(value)
    text = re.sub(
        r"(?i)^\s*AULA[_\s-]*\d{1,4}(?:[.,]\d+)?\s*[-:\u2013\u2014_]*\s*",
        "",
        text,
    )
    return text.strip(" -:\u2013\u2014_.,")


def metadata_suffixes(metadata: dict[str, str]) -> list[str]:
    discipline = metadata["discipline"]
    disciplines = {discipline, *DISCIPLINE_ALIASES.get(discipline, ())}
    stage = metadata["stage"]
    stages = {stage, stage.replace("_", "")}
    bimester = metadata["bimester"]
    number = re.sub(r"\D", "", bimester)
    bimesters = {bimester, f"{number}B", f"{number}_BIMESTRE"}
    class_name = metadata["class"]
    classes = {class_name, class_name.replace("_", "")}

    suffixes = []
    for disc in disciplines:
        for stage_value in stages:
            for bim in bimesters:
                for class_value in classes:
                    suffixes.append(
                        "_".join((disc, stage_value, bim, class_value))
                    )
    return sorted(set(suffixes), key=len, reverse=True)


def title_from_filename(stem: str, metadata: dict[str, str]) -> str:
    match = LESSON_RE.search(stem)
    if not match:
        return ""
    raw = stem[match.end() :].strip(" -:\u2013\u2014_.,")
    normalized = clean_component(raw)
    for suffix in metadata_suffixes(metadata):
        if normalized == suffix:
            return ""
        marker = f"_{suffix}"
        if normalized.endswith(marker):
            normalized = normalized[: -len(marker)].strip("_")
            break
    return normalized


def title_is_usable(title: str) -> bool:
    normalized = clean_component(title)
    if not normalized or normalized in GENERIC_TITLES:
        return False
    generic_patterns = (
        r"^\d+[OA]?_BIMESTRE$",
        r"^ENSINO_(?:MEDIO|FUNDAMENTAL)(?:_ANOS_FINAIS)?$",
        r"^PREMISSAS_DE_LEITURA(?:_\d+)?$",
        r"^SUGESTOES_PARA_(?:A_)?CONDUCAO$",
        r"^(?:REDACAO_E_LEITURA_)?GPS_GUIA_DE_PRATICAS_DE_SALA_DE_AULA(?:_|$).*$",
    )
    if any(re.fullmatch(pattern, normalized) for pattern in generic_patterns):
        return False
    letters = sum(character.isalpha() for character in normalized)
    return letters >= 4 and len(normalized) >= 5


def clean_extracted_title(title: str) -> str:
    normalized = clean_component(title)
    trailing_metadata = (
        r"_(?:(?:\d+[OA]?)_(?:SERIE|ANO)_)?"
        r"ENSINO_(?:MEDIO|FUNDAMENTAL)(?:_ANOS_FINAIS)?$"
    )
    normalized = re.sub(trailing_metadata, "", normalized)
    normalized = re.sub(r"(?:^|_)\d+[OA]?_BIMESTRE$", "", normalized)
    return normalized.strip("_")


def shorten_title(title: str, limit: int = MAX_TITLE_LENGTH) -> str:
    normalized = clean_component(title)
    if len(normalized) <= limit:
        return normalized
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8].upper()
    prefix_limit = max(12, limit - len(digest) - 1)
    prefix = normalized[:prefix_limit].rstrip("_")
    if "_" in prefix:
        word_prefix = prefix.rsplit("_", 1)[0]
        if len(word_prefix) >= max(12, prefix_limit // 2):
            prefix = word_prefix
    return f"{prefix}_{digest}"


def build_target_name(
    lesson: int,
    title: str,
    metadata: dict[str, str],
    parent: Path,
) -> tuple[str, str]:
    normalized_title = shorten_title(title)
    fixed_parts = (
        f"AULA_{lesson:03d}",
        normalized_title,
        metadata["discipline"],
        metadata["stage"],
        metadata["bimester"],
        metadata["class"],
    )
    filename = "__".join(fixed_parts) + ".pdf"
    full_path = parent / filename
    if len(str(full_path)) <= MAX_FULL_PATH:
        return filename, ""

    excess = len(str(full_path)) - MAX_FULL_PATH
    reduced_limit = MAX_TITLE_LENGTH - excess
    if reduced_limit < 20:
        return "", f"caminho proposto excede {MAX_FULL_PATH} caracteres"
    normalized_title = shorten_title(title, reduced_limit)
    filename = "__".join(
        (
            f"AULA_{lesson:03d}",
            normalized_title,
            metadata["discipline"],
            metadata["stage"],
            metadata["bimester"],
            metadata["class"],
        )
    ) + ".pdf"
    if len(str(parent / filename)) > MAX_FULL_PATH:
        return "", f"caminho proposto excede {MAX_FULL_PATH} caracteres"
    return filename, ""


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def sidecar_title(data: dict[str, Any] | None) -> str:
    if not data:
        return ""
    candidates = (
        data.get("tema"),
        data.get("material"),
        data.get("titulo"),
        data.get("material_digital"),
    )
    for candidate in candidates:
        title = strip_lesson_prefix(str(candidate or ""))
        if title_is_usable(title):
            return title
    return ""


def normalize_line_for_match(line: str) -> str:
    return re.sub(r"\s+", " ", ascii_text(line).upper()).strip()


def is_metadata_line(line: str, discipline: str, lesson: int | None) -> bool:
    normalized = normalize_line_for_match(line)
    compact = clean_component(line)
    if not normalized or re.fullmatch(r"[\d\s]+", normalized):
        return True
    if compact == discipline or compact in DISCIPLINE_ALIASES.get(discipline, ()):
        return True
    markers = (
        "BIMESTRE",
        "ENSINO MEDIO",
        "ENSINO FUNDAMENTAL",
        "ANOS FINAIS",
        "MAPA DO",
        "VOCE ESTA AQUI",
        "COMPONENTE CURRICULAR",
        "OBJETIVOS DA AULA",
        "OBJETIVO DA AULA",
        "HABILIDADE",
        "COMPETENCIAS",
        "QUESTAO ESSENCIAL",
        "PRATICA DE LINGUAGEM",
    )
    if any(marker in normalized for marker in markers):
        return True
    if re.search(r"\b\d+[AO]?\s+(?:SERIE|ANO)\b", normalized):
        return True
    if re.fullmatch(r"AULA\s*0*\d+", normalized):
        return True
    if lesson is not None and re.fullmatch(rf"AULA\s*0*{lesson}", normalized):
        return True
    if normalized in {"AULA KHAN", "PARASITOLOGIA"}:
        return True
    return False


def extract_pdf_lines(path: Path, max_pages: int = 2) -> tuple[list[str], str]:
    try:
        from pypdf import PdfReader

        logging.getLogger("pypdf").setLevel(logging.ERROR)
        reader = PdfReader(str(path))
        text = "\n".join(
            (page.extract_text() or "") for page in reader.pages[:max_pages]
        )
    except Exception as exc:  # noqa: BLE001 - erro precisa ir ao manifesto
        return [], f"falha ao extrair PDF: {type(exc).__name__}: {exc}"
    lines = [clean_display_line(line) for line in text.splitlines()]
    return [line for line in lines if line], ""


def extract_lesson_from_lines(lines: Iterable[str]) -> tuple[int | None, str]:
    numbers: list[int] = []
    for line in list(lines)[:80]:
        for match in re.finditer(r"(?i)\bAULA\s*0*(\d{1,4})\b", line):
            numbers.append(int(match.group(1)))
    unique = list(dict.fromkeys(numbers))
    if len(unique) == 1:
        return unique[0], ""
    if not unique:
        return None, "numero de aula nao encontrado no texto inicial"
    return None, f"mais de um numero de aula no texto inicial: {unique[:8]}"


def collect_adjacent_title(
    lines: list[str],
    start_index: int,
    discipline: str,
    lesson: int | None,
) -> str:
    collected: list[str] = []
    for line in lines[start_index : start_index + 7]:
        normalized = normalize_line_for_match(line)
        if collected and normalized in {
            "RESOLUCAO DE PROBLEMAS",
            "OBJETIVOS DA AULA",
            "OBJETIVO DA AULA",
        }:
            break
        if line.startswith(("\u25cf", "\u2022", "- ")):
            break
        if is_metadata_line(line, discipline, lesson):
            if collected:
                break
            continue
        if any(
            marker in normalized
            for marker in ("CONTEUDO", "OBJETIVO", "APRENDIZAGEM")
        ):
            break
        if len(line) > 180:
            break
        collected.append(line)
        if len(" ".join(collected)) >= 120:
            break
    return clean_display_line(" ".join(collected))


def extract_title_from_lines(
    lines: list[str],
    discipline: str,
    lesson: int | None,
) -> tuple[str, str, int]:
    for line in lines[:40]:
        match = re.match(
            r"(?i)^\s*AULA\s*0*(\d{1,4})\s*[-:\u2013\u2014]\s*(.+)$", line
        )
        if match and (lesson is None or int(match.group(1)) == lesson):
            title = clean_extracted_title(match.group(2))
            if title_is_usable(title):
                return title, "pdf_direct", 100

    discipline_variants = {
        discipline,
        *DISCIPLINE_ALIASES.get(discipline, ()),
    }
    for index, line in enumerate(lines[:35]):
        line_normalized = clean_component(line)
        if line_normalized not in discipline_variants:
            continue
        title = clean_extracted_title(
            collect_adjacent_title(lines, index + 1, discipline, lesson)
        )
        if title_is_usable(title):
            return title, "pdf_after_discipline", 95

    context_index = None
    for index, line in enumerate(lines[:15]):
        normalized = normalize_line_for_match(line)
        if (
            "ENSINO MEDIO" in normalized
            or "ENSINO FUNDAMENTAL" in normalized
            or re.search(r"\b\d+[AO]?\s+SERIE\b", normalized)
        ):
            context_index = index
            break
    if context_index and context_index > 0:
        candidates = [
            line
            for line in lines[:context_index]
            if not is_metadata_line(line, discipline, lesson)
            and not line.startswith(("\u25cf", "\u2022", "- "))
        ]
        title = clean_extracted_title(" ".join(candidates[:3]))
        if title_is_usable(title):
            return title, "pdf_before_context", 90

    return "", "", 0


def choose_sidecar_for_title(
    exact_data: dict[str, Any] | None,
    pdf_hash: str,
    sidecars_by_hash: dict[str, list[tuple[Path, dict[str, Any]]]],
) -> tuple[str, str]:
    if exact_data and exact_data.get("hash_pdf") == pdf_hash:
        title = sidecar_title(exact_data)
        if title:
            return title, "json_exact_hash"

    candidates = sidecars_by_hash.get(pdf_hash, [])
    titles = {
        clean_component(title)
        for _, data in candidates
        if (title := sidecar_title(data))
    }
    titles.discard("")
    if len(titles) == 1:
        return next(iter(titles)), "json_hash"
    return "", ""


def build_sidecar_index(root: Path) -> tuple[
    dict[Path, dict[str, Any]],
    dict[str, list[tuple[Path, dict[str, Any]]]],
    list[str],
]:
    sidecars: dict[Path, dict[str, Any]] = {}
    by_hash: dict[str, list[tuple[Path, dict[str, Any]]]] = defaultdict(list)
    invalid: list[str] = []
    for path in sorted(root.rglob("*.json")):
        data = load_json(path)
        if data is None:
            invalid.append(relative_text(path, root))
            continue
        sidecars[path.resolve(strict=False)] = data
        hash_pdf = str(data.get("hash_pdf") or "").strip().lower()
        if re.fullmatch(r"[0-9a-f]{64}", hash_pdf):
            by_hash[hash_pdf].append((path, data))
    return sidecars, by_hash, invalid


def initial_status(
    structure_reason: str,
    lesson_reason: str,
    title: str,
    title_source: str,
    exact_json_state: str,
) -> tuple[str, str]:
    if structure_reason:
        if "backup" in structure_reason:
            return "pending_backup", structure_reason
        return "pending_structure", structure_reason
    if lesson_reason:
        if "representa as aulas" in lesson_reason or "fracionado" in lesson_reason:
            return "pending_multi_lesson", lesson_reason
        return "pending_number", lesson_reason
    if not title:
        return "pending_title", "titulo pedagogico nao identificado"
    if exact_json_state in {"hash_mismatch", "missing_hash", "invalid"}:
        return "pending_json_conflict", f"JSON de mesmo nome: {exact_json_state}"
    if title_source == "filename":
        return "ready_filename", ""
    if title_source.startswith("json"):
        return "ready_json", ""
    if title_source.startswith("pdf"):
        return "ready_pdf_text", ""
    return "pending_title", "fonte do titulo nao reconhecida"


def plan_records(root: Path, extract_pdf_titles: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sidecars, sidecars_by_hash, invalid_jsons = build_sidecar_index(root)
    records: list[dict[str, Any]] = []

    pdf_paths = sorted(root.rglob("*.pdf"), key=lambda path: str(path).casefold())
    for index, pdf in enumerate(pdf_paths, start=1):
        relative = pdf.relative_to(root)
        metadata, structure_reason = parse_structure(relative)
        lesson, lesson_reason = parse_lesson_from_name(pdf.stem)
        pdf_hash = sha256_file(pdf)

        exact_json = pdf.with_suffix(".json")
        exact_data = sidecars.get(exact_json.resolve(strict=False))
        if exact_json.exists() and exact_data is None:
            exact_json_state = "invalid"
        elif exact_data:
            json_hash = str(exact_data.get("hash_pdf") or "").lower()
            if not json_hash:
                exact_json_state = "missing_hash"
            elif json_hash != pdf_hash:
                exact_json_state = "hash_mismatch"
            else:
                exact_json_state = "valid"
        else:
            exact_json_state = "none"

        title = title_from_filename(pdf.stem, metadata) if metadata else ""
        title_source = "filename" if title_is_usable(title) else ""
        title_confidence = 100 if title_source else 0

        if not title_source:
            json_title, json_source = choose_sidecar_for_title(
                exact_data, pdf_hash, sidecars_by_hash
            )
            if title_is_usable(json_title):
                title = json_title
                title_source = json_source
                title_confidence = 100 if json_source == "json_exact_hash" else 95

        extraction_error = ""
        if extract_pdf_titles and metadata and (lesson is None or not title_source):
            lines, extraction_error = extract_pdf_lines(pdf)
            if lesson is None and not lesson_reason.startswith("arquivo representa"):
                extracted_lesson, number_error = extract_lesson_from_lines(lines)
                if extracted_lesson is not None:
                    lesson = extracted_lesson
                    lesson_reason = ""
                elif number_error:
                    lesson_reason = number_error
            if not title_source:
                extracted_title, source, confidence = extract_title_from_lines(
                    lines, metadata["discipline"], lesson
                )
                if title_is_usable(extracted_title):
                    title = extracted_title
                    title_source = source
                    title_confidence = confidence

        normalized_title = clean_component(title) if title else ""
        proposed_name = ""
        target_relative = ""
        path_reason = ""
        if metadata and lesson is not None and normalized_title:
            proposed_name, path_reason = build_target_name(
                lesson, normalized_title, metadata, pdf.parent
            )
            if proposed_name:
                target_relative = relative_text(pdf.with_name(proposed_name), root)

        status, reason = initial_status(
            structure_reason,
            lesson_reason,
            normalized_title,
            title_source,
            exact_json_state,
        )
        if status in READY_STATUSES and path_reason:
            status, reason = "pending_path_length", path_reason

        record = {
            "index": index,
            "status": status,
            "reason": reason,
            "source_pdf": relative_text(pdf, root),
            "target_pdf": target_relative,
            "source_name": pdf.name,
            "target_name": proposed_name,
            "pdf_sha256": pdf_hash,
            "pdf_size": pdf.stat().st_size,
            "lesson": lesson,
            "title": normalized_title,
            "title_source": title_source,
            "title_confidence": title_confidence,
            "discipline": metadata["discipline"] if metadata else "",
            "stage": metadata["stage"] if metadata else "",
            "bimester": metadata["bimester"] if metadata else "",
            "class": metadata["class"] if metadata else "",
            "structure_type": metadata["structure_type"] if metadata else "",
            "source_json": (
                relative_text(exact_json, root) if exact_json.exists() else ""
            ),
            "target_json": (
                str(Path(target_relative).with_suffix(".json")).replace("/", "\\")
                if exact_json.exists() and target_relative
                else ""
            ),
            "json_state": exact_json_state,
            "json_sha256": sha256_file(exact_json) if exact_json.exists() else "",
            "extraction_error": extraction_error,
            "current_full_path_length": len(str(pdf)),
            "target_full_path_length": (
                len(str(root / Path(target_relative))) if target_relative else 0
            ),
        }
        records.append(record)

    mark_collisions(root, records)
    referenced_jsons = {
        record["source_json"].casefold()
        for record in records
        if record["source_json"]
    }
    orphan_jsons = [
        relative_text(path, root)
        for path in sorted(root.rglob("*.json"))
        if relative_text(path, root).casefold() not in referenced_jsons
    ]
    summary = {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": utc_now(),
        "root": str(root),
        "extract_pdf_titles": extract_pdf_titles,
        "pdf_count": len(records),
        "status_counts": dict(Counter(record["status"] for record in records)),
        "title_source_counts": dict(
            Counter(record["title_source"] or "none" for record in records)
        ),
        "paired_json_count": sum(bool(record["source_json"]) for record in records),
        "orphan_json_count": len(orphan_jsons),
        "invalid_json_count": len(invalid_jsons),
        "orphan_jsons": orphan_jsons,
        "invalid_jsons": invalid_jsons,
    }
    return records, summary


def mark_collisions(root: Path, records: list[dict[str, Any]]) -> None:
    targets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["target_pdf"]:
            targets[record["target_pdf"].casefold()].append(record)

    for group in targets.values():
        if len(group) > 1:
            for record in group:
                record["status"] = "pending_collision"
                record["reason"] = "mais de um PDF converge para o mesmo nome"

    source_keys = {record["source_pdf"].casefold() for record in records}
    for record in records:
        if record["status"] not in READY_STATUSES or not record["target_pdf"]:
            continue
        if record["target_pdf"].casefold() == record["source_pdf"].casefold():
            record["status"] = "already_normalized"
            record["reason"] = "arquivo ja segue a convencao"
            continue
        target = safe_path(root, record["target_pdf"])
        target_key = record["target_pdf"].casefold()
        source_key = record["source_pdf"].casefold()
        if target.exists() and target_key != source_key:
            record["status"] = "pending_collision"
            record["reason"] = "arquivo de destino ja existe"
        elif target_key in source_keys and target_key != source_key:
            record["status"] = "pending_collision"
            record["reason"] = "destino e nome atual de outro PDF"


def write_manifest(output_dir: Path, root: Path, records: list[dict[str, Any]], summary: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": summary["generated_at"],
        "root": str(root),
        "policy": {
            "filename": "AULA_NNN__TITULO__DISCIPLINA__ETAPA__BIMESTRE__TURMA.pdf",
            "max_title_length": MAX_TITLE_LENGTH,
            "max_full_path": MAX_FULL_PATH,
            "source_onedrive_untouched": True,
        },
        "summary": summary,
        "records": records,
    }
    manifest_path = output_dir / "manifest.json"
    atomic_json_write(manifest_path, manifest)
    atomic_json_write(output_dir / "summary.json", summary)

    fieldnames = list(records[0].keys()) if records else []
    with (output_dir / "manifest.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    with (output_dir / "pendencias.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            record for record in records if record["status"] not in TERMINAL_STATUSES
        )
    return manifest_path


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("manifest_version") != MANIFEST_VERSION:
        raise ValueError("Versao de manifesto nao suportada")
    return data


def update_sidecar_paths(json_path: Path, target_pdf: Path) -> None:
    data = load_json(json_path)
    if data is None:
        raise ValueError(f"JSON invalido: {json_path}")
    source_kind = str(data.get("fonte_extracao") or "pdf").strip().lower()
    if source_kind == "pdf":
        data["arquivo_fonte_extracao"] = str(target_pdf)
    principal_kind = str(data.get("fonte_principal") or source_kind).strip().lower()
    if principal_kind == "pdf":
        data["arquivo_fonte"] = str(target_pdf)
    if "caminho_pdf" in data:
        data["caminho_pdf"] = str(target_pdf)
    atomic_json_write(json_path, data)


def selected_records(manifest: dict[str, Any], statuses: set[str]) -> list[dict[str, Any]]:
    return [
        record
        for record in manifest["records"]
        if record["status"] in statuses
    ]


def preflight_apply(root: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        raise ValueError("Nenhum registro selecionado para aplicacao")
    target_keys: set[str] = set()
    for record in records:
        source = safe_path(root, record["source_pdf"])
        target = safe_path(root, record["target_pdf"])
        if not source.is_file():
            raise FileNotFoundError(f"PDF de origem ausente: {source}")
        if sha256_file(source) != record["pdf_sha256"]:
            raise ValueError(f"Hash do PDF mudou desde o manifesto: {source}")
        key = str(target).casefold()
        if key in target_keys:
            raise ValueError(f"Colisao entre destinos selecionados: {target}")
        target_keys.add(key)
        if target.exists() and source.resolve() != target.resolve():
            raise FileExistsError(f"Destino ja existe: {target}")

        if record.get("source_json"):
            source_json = safe_path(root, record["source_json"])
            target_json = safe_path(root, record["target_json"])
            if not source_json.is_file():
                raise FileNotFoundError(f"JSON associado ausente: {source_json}")
            if sha256_file(source_json) != record["json_sha256"]:
                raise ValueError(f"JSON mudou desde o manifesto: {source_json}")
            if target_json.exists() and source_json.resolve() != target_json.resolve():
                raise FileExistsError(f"Destino JSON ja existe: {target_json}")


def load_apply_report(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "apply_report.json"
    if not path.exists():
        return {"manifest_version": MANIFEST_VERSION, "operations": [], "phases": []}
    return json.loads(path.read_text(encoding="utf-8"))


def apply_records(manifest_path: Path, statuses: set[str], phase_name: str) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    root = Path(manifest["root"]).resolve(strict=True)
    records = selected_records(manifest, statuses)

    run_dir = manifest_path.parent
    backup_root = run_dir / "json_original"
    backup_root.mkdir(parents=True, exist_ok=True)
    report = load_apply_report(run_dir)
    incomplete = [
        operation
        for operation in report["operations"]
        if operation.get("state") != "applied"
    ]
    if incomplete:
        raise RuntimeError(
            "Existe operacao interrompida no relatorio. "
            "Execute rollback antes de uma nova aplicacao."
        )
    already_applied = {
        operation["source_pdf"].casefold() for operation in report["operations"]
    }
    duplicate = [
        record["source_pdf"]
        for record in records
        if record["source_pdf"].casefold() in already_applied
    ]
    if duplicate:
        raise ValueError(f"Registros ja aplicados: {duplicate[:3]}")
    preflight_apply(root, records)

    applied_now: list[dict[str, Any]] = []
    try:
        for record in records:
            source = safe_path(root, record["source_pdf"])
            target = safe_path(root, record["target_pdf"])
            source_json = (
                safe_path(root, record["source_json"])
                if record.get("source_json")
                else None
            )
            target_json = (
                safe_path(root, record["target_json"])
                if record.get("target_json")
                else None
            )
            backup_json = None
            backup_relative = None
            if source_json:
                backup_relative = Path("json_original") / Path(
                    record["source_json"]
                )
                backup_json = safe_path(run_dir, str(backup_relative))
                backup_json.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_json, backup_json)
                if sha256_file(backup_json) != record["json_sha256"]:
                    raise ValueError(f"Falha ao conferir backup JSON: {source_json}")

            operation = {
                "phase": phase_name,
                "state": "prepared",
                "prepared_at": utc_now(),
                "source_pdf": record["source_pdf"],
                "target_pdf": record["target_pdf"],
                "pdf_sha256": record["pdf_sha256"],
                "source_json": record.get("source_json") or "",
                "target_json": record.get("target_json") or "",
                "json_sha256_original": record.get("json_sha256") or "",
                "json_backup": (
                    str(backup_relative).replace("/", "\\")
                    if backup_relative
                    else ""
                ),
            }
            report["operations"].append(operation)
            applied_now.append(operation)
            atomic_json_write(run_dir / "apply_report.json", report)

            os.rename(source, target)
            operation["state"] = "pdf_renamed"
            atomic_json_write(run_dir / "apply_report.json", report)
            if source_json and target_json:
                os.rename(source_json, target_json)
                operation["state"] = "json_renamed"
                atomic_json_write(run_dir / "apply_report.json", report)
                update_sidecar_paths(target_json, target)

            if sha256_file(target) != record["pdf_sha256"]:
                raise ValueError(f"Hash mudou depois da renomeacao: {target}")
            if target_json:
                updated_data = load_json(target_json)
                if updated_data is None or str(
                    updated_data.get("hash_pdf") or ""
                ).lower() != record["pdf_sha256"]:
                    raise ValueError(f"JSON atualizado ficou inconsistente: {target_json}")

            operation["state"] = "applied"
            operation["applied_at"] = utc_now()
            atomic_json_write(run_dir / "apply_report.json", report)
    except Exception as original_error:
        try:
            rollback_operations(root, run_dir, reversed(applied_now))
        except Exception as rollback_error:
            report["phases"].append(
                {
                    "name": phase_name,
                    "failed_at": utc_now(),
                    "state": "rollback_failed",
                    "error": type(original_error).__name__,
                    "rollback_error": type(rollback_error).__name__,
                }
            )
            atomic_json_write(run_dir / "apply_report.json", report)
            raise RuntimeError(
                "A aplicacao falhou e a reversao automatica nao terminou. "
                "O relatorio foi preservado para recuperacao."
            ) from rollback_error

        applied_ids = {id(operation) for operation in applied_now}
        report["operations"] = [
            operation
            for operation in report["operations"]
            if id(operation) not in applied_ids
        ]
        report["phases"].append(
            {
                "name": phase_name,
                "failed_at": utc_now(),
                "state": "rolled_back",
                "error": type(original_error).__name__,
                "count": len(applied_now),
            }
        )
        atomic_json_write(run_dir / "apply_report.json", report)
        raise

    report["phases"].append(
        {
            "name": phase_name,
            "completed_at": utc_now(),
            "statuses": sorted(statuses),
            "count": len(applied_now),
        }
    )
    atomic_json_write(run_dir / "apply_report.json", report)
    return {"phase": phase_name, "count": len(applied_now)}


def rollback_operations(
    root: Path, run_dir: Path, operations: Iterable[dict[str, Any]]
) -> None:
    for operation in operations:
        source = safe_path(root, operation["source_pdf"])
        target = safe_path(root, operation["target_pdf"])
        source_exists = source.exists()
        target_exists = target.exists()
        if source_exists and target_exists and source.resolve() != target.resolve():
            raise FileExistsError(
                f"Origem e destino existem durante rollback: {source} | {target}"
            )
        if target_exists and not source_exists:
            if sha256_file(target) != operation["pdf_sha256"]:
                raise ValueError(f"Hash divergente antes do rollback: {target}")
            os.rename(target, source)
        elif source_exists:
            if sha256_file(source) != operation["pdf_sha256"]:
                raise ValueError(f"Hash divergente na origem restaurada: {source}")
        else:
            raise FileNotFoundError(
                f"PDF ausente na origem e no destino durante rollback: {source}"
            )

        if operation.get("source_json"):
            source_json = safe_path(root, operation["source_json"])
            target_json = safe_path(root, operation["target_json"])
            backup_json = safe_path(run_dir, operation["json_backup"])
            if not backup_json.is_file():
                raise FileNotFoundError(f"Backup JSON ausente: {backup_json}")
            expected_json_hash = operation.get("json_sha256_original") or ""
            if expected_json_hash and sha256_file(backup_json) != expected_json_hash:
                raise ValueError(f"Backup JSON divergente: {backup_json}")
            if source_json.exists() and target_json.exists():
                raise FileExistsError(
                    "JSON de origem e destino existem durante rollback: "
                    f"{source_json} | {target_json}"
                )
            if target_json.exists():
                target_json.unlink()
            if source_json.exists():
                if expected_json_hash and sha256_file(source_json) != expected_json_hash:
                    raise ValueError(f"JSON de origem foi alterado: {source_json}")
            else:
                source_json.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_json, source_json)


def rollback_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    root = Path(manifest["root"]).resolve(strict=True)
    run_dir = manifest_path.parent
    report = load_apply_report(run_dir)
    operations = list(report.get("operations", []))
    rollback_operations(root, run_dir, reversed(operations))
    rollback_report = {
        "rolled_back_at": utc_now(),
        "count": len(operations),
    }
    atomic_json_write(run_dir / "rollback_report.json", rollback_report)
    report["operations"] = []
    report["phases"].append(
        {"name": "rollback", "completed_at": utc_now(), "count": len(operations)}
    )
    atomic_json_write(run_dir / "apply_report.json", report)
    return rollback_report


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    root = Path(manifest["root"]).resolve(strict=True)
    report = load_apply_report(manifest_path.parent)
    errors: list[str] = []
    checked = 0
    operations = report.get("operations", [])
    if not operations:
        errors.append("nenhuma operacao registrada para validar")
    for operation in operations:
        if operation.get("state") != "applied":
            errors.append(
                "operacao incompleta: "
                f"{operation['source_pdf']} ({operation.get('state', 'sem estado')})"
            )
        target = safe_path(root, operation["target_pdf"])
        source = safe_path(root, operation["source_pdf"])
        if source.exists():
            errors.append(f"origem ainda existe: {operation['source_pdf']}")
        if not target.is_file():
            errors.append(f"destino ausente: {operation['target_pdf']}")
            continue
        if sha256_file(target) != operation["pdf_sha256"]:
            errors.append(f"hash divergente: {operation['target_pdf']}")
        if operation.get("target_json"):
            target_json = safe_path(root, operation["target_json"])
            source_json = safe_path(root, operation["source_json"])
            if source_json.exists():
                errors.append(f"JSON de origem ainda existe: {operation['source_json']}")
            data = load_json(target_json)
            if data is None:
                errors.append(f"JSON ausente/invalido: {operation['target_json']}")
            elif str(data.get("hash_pdf") or "").lower() != operation[
                "pdf_sha256"
            ]:
                errors.append(f"hash_pdf divergente: {operation['target_json']}")
            else:
                source_kind = str(data.get("fonte_extracao") or "pdf").lower()
                if source_kind == "pdf" and data.get(
                    "arquivo_fonte_extracao"
                ) != str(target):
                    errors.append(
                        "arquivo_fonte_extracao desatualizado: "
                        f"{operation['target_json']}"
                    )
                principal_kind = str(
                    data.get("fonte_principal") or source_kind
                ).lower()
                if principal_kind == "pdf" and data.get("arquivo_fonte") != str(
                    target
                ):
                    errors.append(
                        f"arquivo_fonte desatualizado: {operation['target_json']}"
                    )
                if "caminho_pdf" in data and data.get("caminho_pdf") != str(target):
                    errors.append(
                        f"caminho_pdf desatualizado: {operation['target_json']}"
                    )
        checked += 1

    completed_phases = [
        phase
        for phase in report.get("phases", [])
        if phase.get("state", "completed") == "completed"
        and "completed_at" in phase
        and phase.get("name") != "rollback"
    ]
    expected_count = sum(int(phase.get("count", 0)) for phase in completed_phases)
    if expected_count != len(operations):
        errors.append(
            "quantidade do relatorio diverge das fases concluidas: "
            f"operacoes={len(operations)}, fases={expected_count}"
        )

    result = {
        "validated_at": utc_now(),
        "checked": checked,
        "errors": errors,
        "ok": not errors,
    }
    atomic_json_write(manifest_path.parent / "validation_report.json", result)
    return result


def command_plan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(strict=True)
    manifest_root = Path(args.manifest_root).resolve(strict=False)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = manifest_root / f"renomeacao_pdfs_{stamp}"
    records, summary = plan_records(root, args.extract_pdf_titles)
    manifest_path = write_manifest(output_dir, root, records, summary)
    print(json.dumps({"manifest": str(manifest_path), **summary}, ensure_ascii=False))
    return 0


def command_apply(args: argparse.Namespace) -> int:
    if args.phase == "alta_confianca":
        statuses = PHASE_ONE_STATUSES
    elif args.phase == "titulos_extraidos":
        statuses = PHASE_TWO_STATUSES
    else:
        raise ValueError(f"Fase desconhecida: {args.phase}")
    result = apply_records(Path(args.manifest), statuses, args.phase)
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    result = validate_manifest(Path(args.manifest))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 2


def command_rollback(args: argparse.Namespace) -> int:
    result = rollback_manifest(Path(args.manifest))
    print(json.dumps(result, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--root", default=str(DEFAULT_ROOT))
    plan_parser.add_argument(
        "--manifest-root", default=str(DEFAULT_MANIFEST_ROOT)
    )
    plan_parser.add_argument("--extract-pdf-titles", action="store_true")
    plan_parser.set_defaults(func=command_plan)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--manifest", required=True)
    apply_parser.add_argument(
        "--phase", choices=("alta_confianca", "titulos_extraidos"), required=True
    )
    apply_parser.set_defaults(func=command_apply)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--manifest", required=True)
    validate_parser.set_defaults(func=command_validate)

    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--manifest", required=True)
    rollback_parser.set_defaults(func=command_rollback)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:  # noqa: BLE001 - CLI precisa falhar fechado
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
