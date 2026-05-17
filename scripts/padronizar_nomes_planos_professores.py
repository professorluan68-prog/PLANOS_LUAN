from __future__ import annotations

from pathlib import Path

from core.professores_planos import PASTA_PLANOS_PROFESSORES, extrair_info_plano, nome_padronizado_plano


def _destino_unico(pasta: Path, nome: str, origem: Path) -> Path:
    destino = pasta / nome
    if destino == origem:
        return destino
    if not destino.exists():
        return destino
    stem = destino.stem
    suffix = destino.suffix
    contador = 2
    while True:
        candidato = pasta / f"{stem} ({contador}){suffix}"
        if candidato == origem or not candidato.exists():
            return candidato
        contador += 1


def padronizar_nomes() -> None:
    total = 0
    renomeados = 0
    ignorados = 0

    for pasta_professor in sorted(p for p in PASTA_PLANOS_PROFESSORES.iterdir() if p.is_dir() and not p.name.startswith("_")):
        for caminho in sorted(pasta_professor.glob("*.docx")):
            total += 1
            try:
                info = extrair_info_plano(caminho, pasta_professor.name)
            except Exception as exc:
                print(f"IGNORADO;{pasta_professor.name};{caminho.name};erro ao ler: {exc}")
                ignorados += 1
                continue

            disciplina = str(info.get("disciplina") or "").strip()
            turma = str(info.get("turma") or "").strip()
            if not disciplina or not turma:
                print(f"IGNORADO;{pasta_professor.name};{caminho.name};sem disciplina/turma no cabecalho")
                ignorados += 1
                continue

            novo_nome = nome_padronizado_plano(disciplina, turma)
            destino = _destino_unico(pasta_professor, novo_nome, caminho)
            if destino == caminho:
                continue
            caminho.rename(destino)
            renomeados += 1
            print(f"RENOMEADO;{pasta_professor.name};{caminho.name};{destino.name}")

    print(f"Planos encontrados: {total}")
    print(f"Planos renomeados: {renomeados}")
    print(f"Planos ignorados: {ignorados}")


if __name__ == "__main__":
    padronizar_nomes()
