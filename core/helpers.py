import io
import re
import unicodedata
from pathlib import Path
from collections.abc import Iterable


DISCIPLINA_PASTA_ALIASES = {
    "PORTUGUES": "LINGUA_PORTUGUESA",
    "LINGUA_PORTUGUESA": "LINGUA_PORTUGUESA",
    "APROF_EM_BIOLOGIA": "APROFUNDAMENTO_EM_BIOLOGIA",
    "APROFUNDAMENTO_BIOLOGIA": "APROFUNDAMENTO_EM_BIOLOGIA",
    "APROFUNDAMENTO_EM_BIOLOGIA": "APROFUNDAMENTO_EM_BIOLOGIA",
    "APROF_EM_GEOGRAFIA": "APROFUNDAMENTO_EM_GEOGRAFIA",
    "APROFUNDAMENTO_GEOGRAFIA": "APROFUNDAMENTO_EM_GEOGRAFIA",
    "APROFUNDAMENTO_EM_GEOGRAFIA": "APROFUNDAMENTO_EM_GEOGRAFIA",
    "LIDERANCA_ORATORIA": "LIDERANCA_E_ORATORIA",
    "LIDERANCA_E_ORATORIA": "LIDERANCA_E_ORATORIA",
    "LIDERANCA_E_ORATORIAEJA": "LIDERANCA_E_ORATORIA",
    "LIDERANCA_ORATORIAEJA": "LIDERANCA_E_ORATORIA",
    "LIDERANA_E_ORATRIA": "LIDERANCA_E_ORATORIA",
    "LIDERANA_E_ORATRIAEJA": "LIDERANCA_E_ORATORIA",
    "LIDERANCA_CDP": "LIDERANCA_E_ORATORIA",
    "CDPENSINO_MEDIO": "CDP_ENSINO_MEDIO",
    "CDP_ENSINO_MEDIO": "CDP_ENSINO_MEDIO",
    "CDPENSINO_FUNDAMENTAL": "CDP_ENSINO_FUNDAMENTAL",
    "CDP_ENSINO_FUNDAMENTAL": "CDP_ENSINO_FUNDAMENTAL",
    "BIOLOGIAEJA": "BIOLOGIA_EJA",
    "BIOLOGIA_EJA": "BIOLOGIA_EJA",
    "INGLES": "LINGUA_INGLESA",
    "LINGUA_INGLESA_EJA": "LINGUA_INGLESA_EJA",
    "LINGUA_INGLESAEJA": "LINGUA_INGLESA_EJA",
    "INGLES_EJA": "LINGUA_INGLESA_EJA",
    "INGLESEJA": "LINGUA_INGLESA_EJA",
    "HISTORIA_CDP": "HISTORIA_CDP",
    "HISTORIA_CDP_EJA_MULTISSERIADO": "HISTORIA_CDP",
    "HISTORIA_EM_CDP": "HISTORIA_CDP",
    "HISTORIA_EF_CDP": "HISTORIA_CDP",
    "HISTORIA_EM_TURMA_E_MULTISSERIADO": "HISTORIA_CDP",
    "HISTORIA_EM_TURMA_J_MULTISSERIADO": "HISTORIA_CDP",
    "HISTORIA_EM_TURMA_E": "HISTORIA_CDP",
    "HISTORIA_EM_TURMA_J": "HISTORIA_CDP",
    "HISTORIA_EF_TURMA_J_MULTISSERIADO": "HISTORIA_CDP",
    "HISTORIA_EF_TURMA_E_MULTISSERIADO": "HISTORIA_CDP",
    "HISTORIA_EF_TURMA_J": "HISTORIA_CDP",
    "HISTORIA_EF_TURMA_E": "HISTORIA_CDP",
    "HISTORIA_EF_MULTISSERIADO": "HISTORIA_CDP",
    "HISTORIACDP": "HISTORIA_CDP",
    "CIENCIAS_CDP": "CIENCIAS_CDP",
    "CIENCIAS_CDP_EJA_MULTISSERIADO": "CIENCIAS_CDP",
    "CIENCIASCDP": "CIENCIAS_CDP",
    "CIENCIAS_CDP_EF": "CIENCIAS_CDP",
    "CIENCIAS_CDP_MULTISSERIADO_6_7_EF": "CIENCIAS_CDP",
    "CIENCIAS_CDP_MULTISSERIADO_8_9_EF": "CIENCIAS_CDP",
    "MATEMATICA_CDP": "MATEMATICA_CDP",
    "MATEMATICA_CDP_EJA_MULTISSERIADO": "MATEMATICA_CDP",
    "MATEMATICACDP": "MATEMATICA_CDP",
    "MATEMATICA_EM_EJA_CDP": "MATEMATICA_CDP",
    "MATEMATICA_EM_CDP": "MATEMATICA_CDP",
    "MATEMATICA_EF_CDP": "MATEMATICA_CDP",
    "GEOGRAFIA_CDP": "GEOGRAFIA_CDP",
    "GEOGRAFIA_CDP_EJA_MULTISSERIADO": "GEOGRAFIA_CDP",
    "GEOGRAFIA_EM_CDP": "GEOGRAFIA_CDP",
    "GEOGRAFIA_EMCDP": "GEOGRAFIA_CDP",
    "GEOGRAFIA_EM_TURMA_J": "GEOGRAFIA_CDP",
    "GEOGRAFIA_TURMA_J": "GEOGRAFIA_CDP",
    "SOCIOLOGIA_CDP": "SOCIOLOGIA_CDP_MULTISSERIADO",
    "SOCIOLOGIA_CDP_EJA_MULTISSERIADO": "SOCIOLOGIA_CDP_MULTISSERIADO",
    "SOCIOLOGIA_CDP_MULTISSERIADO": "SOCIOLOGIA_CDP_MULTISSERIADO",
    "SOCIOLOGIA_CDP_MULTISSERIADA": "SOCIOLOGIA_CDP_MULTISSERIADO",
    "SOCIOLOGIA_MULTISSERIADO": "SOCIOLOGIA_CDP_MULTISSERIADO",
    "SOCIOLOGIA_MULTISSERIADA": "SOCIOLOGIA_CDP_MULTISSERIADO",
    "LIDERANCA_E_ORATORIA_CDP_EJA_MULTISSERIADO": "LIDERANCA_E_ORATORIA",
    "ORATORIA_E_LIDERANCA_CDP_EJA_MULTISSERIADO": "LIDERANCA_E_ORATORIA",
    "LINGUA_PORTUGUESA_CDP_EJA_MULTISSERIADO": "LINGUA_PORTUGUESA",
    "ARTE_CDP_EJA_MULTISSERIADO": "ARTE",
}

# Subpastas usadas quando a modalidade EJA é selecionada na interface.
# Mantemos a resolução por modalidade separada do nome da disciplina para
# evitar que a seleção EJA continue lendo silenciosamente os PDFs regulares.
PASTAS_EJA_POR_DISCIPLINA = {
    "BIOLOGIA": "EJA_BIOLOGIA",
    "BIOLOGIA_EJA": "EJA_BIOLOGIA",
    "LINGUA_INGLESA": "EJA_EM",
    "LINGUA_INGLESA_EJA": "EJA_EM",
    "INGLES": "EJA_EM",
    "INGLES_EJA": "EJA_EM",
    "LIDERANCA_E_ORATORIA": "EJA_EM",
    "LIDERANA_E_ORATRIA": "EJA_EM",
}


def horario_para_plano(horario) -> str:
    if isinstance(horario, tuple) and len(horario) >= 2:
        return f"{horario[0]}\n{horario[1]}"
    return str(horario or "")


def arquivos_na_ordem_de_envio(arquivos) -> list:
    """Preserva a ordem exata em que os arquivos chegam da interface.

    Em alguns planos a sequência pedagógica não acompanha a numeração do
    material. Por isso, o sistema não deve reordenar os PDFs pelo nome.
    """
    return list(arquivos or [])


def texto_lista(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, Iterable) and not isinstance(valor, (bytes, bytearray, dict)):
        return "\n".join(f"- {item}" for item in valor if str(item).strip())
    return str(valor)


def listar_falhas_ia(aulas, exigir_ia: bool = True) -> list[str]:
    if not exigir_ia:
        return []

    falhas = []
    for idx, aula in enumerate(aulas or [], start=1):
        if aula.get("ia_usada"):
            continue
        origem = str(aula.get("origem_metodologia") or "").strip()
        if origem.startswith("docx_referencia_"):
            continue
        erro = str(aula.get("ia_erro") or "").strip()
        tema = str(aula.get("tema") or f"Aula {idx}").strip()
        if erro:
            falhas.append(f"Aula {idx} ({tema}): {erro}")
        else:
            falhas.append(f"Aula {idx} ({tema}): a IA não retornou desenvolvimento completo.")
    return falhas


def resumir_falhas_ia(falhas_ia) -> str:
    falhas = [str(item).strip() for item in falhas_ia or [] if str(item).strip()]
    if not falhas:
        return ""
    if len(falhas) == 1:
        return (
            "A IA não concluiu 1 aula e o sistema usou o motor local nessa aula. "
            "Revise esse trecho com mais atenção: "
            f"{falhas[0]}"
        )
    return (
        f"A IA não concluiu {len(falhas)} aula(s) e o sistema usou o motor local nesses casos. "
        "Revise essas aulas com mais atenção: "
        + " | ".join(falhas)
    )


def montar_relatorio_geracao(aulas, disciplina: str, turma: str, bimestre: str, mes: str) -> str:
    linhas = [
        "RELATORIO DE CONFERENCIA DO PLANO",
        f"Disciplina: {disciplina}",
        f"Turma: {turma}",
        f"Bimestre: {bimestre}",
        f"Mes: {mes}",
        f"Total de aulas: {len(aulas or [])}",
        "",
    ]
    for idx, aula in enumerate(aulas or [], start=1):
        erro_ia = str(aula.get("ia_erro") or "").strip()
        linhas.extend(
            [
                f"Aula {idx}",
                f"Tema: {aula.get('tema', '')}",
                f"Data: {aula.get('data', '')}",
                f"Horario: {str(aula.get('horario', '')).replace(chr(10), ' - ')}",
                f"IA usada: {'sim' if aula.get('ia_usada') else 'nao'}",
            ]
        )
        if erro_ia:
            linhas.append(f"Observacao IA: {erro_ia}")
        linhas.append("")
    return "\n".join(linhas)


class LocalFileWrapper(io.BytesIO):
    """Wrapper para PDFs locais simular o comportamento de st.file_uploader."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        try:
            content = path.read_bytes()
        except OSError:
            content = b""
        super().__init__(content)


def normalizar_para_pasta(texto: str) -> str:
    t = str(texto or "")
    t = re.sub(r"(\d)\s*[º°ª]\s*", r"\1_", t)
    texto_norm = unicodedata.normalize("NFKD", t)
    texto_norm = "".join(ch for ch in texto_norm if not unicodedata.combining(ch))
    texto_norm = re.sub(r"[^\w\s]", "", texto_norm).upper().strip()
    texto_norm = re.sub(r"\s+", "_", texto_norm)
    # Ajustar entradas comuns como "1o ano" e "2a serie".
    return re.sub(r"(\d)[OA]_", r"\1_", texto_norm)




def _normalizar_disciplina_para_pasta(disciplina: str) -> str:
    disciplina_norm = normalizar_para_pasta(disciplina)
    if "SOCIOLOGIA" in disciplina_norm and ("MULTISSERIAD" in disciplina_norm or "CDP" in disciplina_norm):
        return "SOCIOLOGIA_CDP_MULTISSERIADO"
    if "GEOGRAFIA" in disciplina_norm and ("TURMA_J" in disciplina_norm or "TURMA_E" in disciplina_norm or "CDP" in disciplina_norm or "MULTISSERIAD" in disciplina_norm):
        return "GEOGRAFIA_CDP"
    if "HISTORIA" in disciplina_norm and ("TURMA_E" in disciplina_norm or "TURMA_J" in disciplina_norm or "CDP" in disciplina_norm or "MULTISSERIAD" in disciplina_norm):
        return "HISTORIA_CDP"
    if "CIENCIAS" in disciplina_norm and ("CDP" in disciplina_norm or "MULTISSERIAD" in disciplina_norm):
        return "CIENCIAS_CDP"
    if "MATEMATICA" in disciplina_norm and ("CDP" in disciplina_norm or "MULTISSERIAD" in disciplina_norm):
        return "MATEMATICA_CDP"
    if ("LIDERANCA" in disciplina_norm or "ORATORIA" in disciplina_norm) and ("CDP" in disciplina_norm or "MULTISSERIAD" in disciplina_norm):
        return "LIDERANCA_E_ORATORIA"
    # O cadastro pode usar um rotulo descritivo, como
    # "HISTORIA - E.F - 8o/9o - TURMA H". Para localizar os materiais,
    # somente o componente curricular deve definir a raiz da disciplina.
    if (disciplina_norm == "HISTORIA" or disciplina_norm.startswith("HISTORIA_")) and "CDP" not in disciplina_norm:
        return "HISTORIA"
    if "CDP" in disciplina_norm and (
        "ENSINO_MEDIO" in disciplina_norm
        or disciplina_norm.endswith("_CDP_EM")
        or disciplina_norm.endswith("CDP_EM")
        or disciplina_norm.endswith("_EM_CDP")
        or disciplina_norm.endswith("EM_CDP")
    ):
        return "CDP_ENSINO_MEDIO"
    if "CDP" in disciplina_norm and (
        "ENSINO_FUNDAMENTAL" in disciplina_norm
        or disciplina_norm.endswith("_CDP_EF")
        or disciplina_norm.endswith("CDP_EF")
        or disciplina_norm.endswith("_EF_CDP")
        or disciplina_norm.endswith("EF_CDP")
    ):
        return "CDP_ENSINO_FUNDAMENTAL"
    return DISCIPLINA_PASTA_ALIASES.get(disciplina_norm, disciplina_norm)


def _nome_pasta_normalizado(valor: str | Path) -> str:
    return normalizar_para_pasta(Path(str(valor)).name)


def resolver_raiz_disciplina_pdfs(
    base_dir: str | Path,
    disciplina: str,
    modalidade_eja: bool = False,
) -> Path:
    """Resolve a raiz de busca da disciplina dentro de ``PDF_AULAS``."""
    base_path = Path(base_dir)
    disc_folder = _normalizar_disciplina_para_pasta(disciplina)
    eja_solicitado = bool(modalidade_eja or "EJA" in disc_folder)

    if eja_solicitado:
        disciplina_base_eja = re.sub(r"_?EJA$", "", disc_folder) or disc_folder
        subpasta_eja = PASTAS_EJA_POR_DISCIPLINA.get(disciplina_base_eja) or PASTAS_EJA_POR_DISCIPLINA.get(disc_folder)
        candidatas_eja = [
            base_path / f"{disciplina_base_eja}_EJA",
            base_path / disc_folder,
        ]
        if subpasta_eja:
            candidatas_eja.append(base_path / disciplina_base_eja / subpasta_eja)
        for raiz_eja in candidatas_eja:
            if raiz_eja.exists():
                return raiz_eja

    # Candidatos diretos conhecidos (com underline, hifen, etc.)
    candidatos_diretos = [
        base_path / disc_folder,
        base_path / disc_folder.replace("_", "-"),
        base_path / disc_folder.replace("-", "_"),
        base_path / "CDP_ENSINO_MEDIO" / disc_folder,
        base_path / "CDP_ENSINO_MEDIO" / disc_folder.replace("_", "-"),
        base_path / "CDP_ENSINO_MEDIO" / disc_folder.replace("-", "_"),
        base_path / "CDP_ENSINO_FUNDAMENTAL" / disc_folder,
        base_path / "CDP_ENSINO_FUNDAMENTAL" / disc_folder.replace("_", "-"),
        base_path / "CDP_ENSINO_FUNDAMENTAL" / disc_folder.replace("-", "_"),
    ]
    for c in candidatos_diretos:
        if c.exists():
            return c

    disc_chave = normalizar_para_pasta(disc_folder).replace("_", "")
    if base_path.exists():
        for candidata in base_path.iterdir():
            if candidata.is_dir() and normalizar_para_pasta(candidata.name).replace("_", "") == disc_chave:
                return candidata

    return candidatos_diretos[0]



def _pasta_tem_pdfs(caminho: Path) -> bool:
    if not caminho.exists() or not caminho.is_dir():
        return False
    try:
        return any(arquivo.is_file() and arquivo.suffix.lower() == ".pdf" for arquivo in caminho.iterdir())
    except OSError:
        return False


def _localizar_subpasta_cdp(caminho_bimestre: Path, nivel: str) -> Path | None:
    """Localiza CDP_EM/CDP_EF mesmo quando a pasta usa hifen ou subpasta de turma."""
    nomes_esperados = {"CDPEM"} if nivel == "EM" else {"CDPEF"}
    # Algumas disciplinas do Ensino Medio usam apenas ``CDP`` dentro do
    # bimestre. Como o nivel ja foi resolvido pela turma, esse nome e uma
    # variante inequivoca de ``CDP_EM`` nesse ponto do fluxo.
    if nivel == "EM":
        nomes_esperados.add("CDP")
    try:
        candidatos = sorted(
            (
                caminho
                for caminho in caminho_bimestre.iterdir()
                if caminho.is_dir()
                and _nome_pasta_normalizado(caminho).replace("_", "") in nomes_esperados
            ),
            key=lambda caminho: str(caminho).casefold(),
        )
    except OSError:
        return None

    for candidato in candidatos:
        if _pasta_tem_pdfs(candidato):
            return candidato
        try:
            descendentes = sorted(
                (
                    caminho
                    for caminho in candidato.rglob("*")
                    if caminho.is_dir() and _pasta_tem_pdfs(caminho)
                ),
                key=lambda caminho: str(caminho).casefold(),
            )
        except OSError:
            descendentes = []
        if descendentes:
            return descendentes[0]
    return None


def _tokens_serie_turma(turma_norm: str) -> list[str]:
    tokens = [turma_norm] if turma_norm else []

    # Extrair agrupamentos de dígitos como 1/2/3, 6/7, 8/9, 123, 67, 89, 1_2_3, 6_7, 8_9
    anos = []
    match_multisseriada = re.fullmatch(
        r"((?:[1-9][OA_]?)+)(?:_(?:EF|EM|[A-Z]))?(?:_[A-Z])?",
        turma_norm,
    )
    if match_multisseriada:
        anos = re.findall(r"[1-9]", match_multisseriada.group(1))

    if len(anos) < 2:
        prefixo_ano = turma_norm.split("_ANO")[0] if "_ANO" in turma_norm else turma_norm
        digitos_prefixo = re.findall(r"[1-9]", prefixo_ano)
        if len(digitos_prefixo) >= 2:
            anos = digitos_prefixo

    if len(anos) < 2:
        anos_multi = re.findall(r"\b([1-9])\b", turma_norm.replace("_", " "))
        if len(anos_multi) >= 2:
            anos = anos_multi

    if len(anos) >= 2:
        tokens.append("_".join(f"{ano}_ANO" for ano in anos))
        tokens.append("_".join(anos) + "_ANO")
        tokens.append("_E_".join(anos) + "_ANO")
        tokens.append("_E_".join(anos))
        tokens.append("_".join(anos))
        if len(anos) == 2:
            tokens.append(f"{anos[0]}_E_{anos[1]}_ANO")
            tokens.append(f"{anos[0]}_E_{anos[1]}_ANO_MULTISSERIADO")
            tokens.append(f"{anos[0]}_{anos[1]}_ANO_MULTISSERIADO")
        elif len(anos) == 3:
            tokens.append(f"{anos[0]}_{anos[1]}_E_{anos[2]}_ANO")
            tokens.append(f"{anos[0]}_{anos[1]}_E_{anos[2]}_ANO_MULTISSERIADO")
            tokens.append(f"{anos[0]}_{anos[1]}_{anos[2]}_ANO_MULTISSERIADO")
            tokens.append(f"{anos[0]}_E_{anos[1]}_E_{anos[2]}_ANO_MULTISSERIADO")
        tokens.extend(f"{ano}_ANO" for ano in anos)
        return [token for token in dict.fromkeys(tokens) if token]

    match_ano = re.search(r"(\d)_ANO(?:_([A-Z]))?", turma_norm)
    match_serie = re.search(r"(\d)_SERIE(?:_([A-Z]))?", turma_norm)
    match_termo = re.search(r"(\d)_TERMO(?:_([A-Z]))?", turma_norm)
    match = match_ano or match_serie or match_termo
    if not match:
        if turma_norm in {"C", "TURMA_C"}:
            tokens.extend([
                "6_E_7_ANO_MULTISSERIADO",
                "6_E_7_ANO",
                "6_7_ANO_MULTISSERIADO",
                "6_ANO_7_ANO",
                "6_7_ANO",
                "6_ANO",
                "7_ANO",
            ])
        elif turma_norm in {"H", "TURMA_H"}:
            tokens.extend([
                "8_E_9_ANO_MULTISSERIADO",
                "8_E_9_ANO",
                "8_9_ANO_MULTISSERIADO",
                "8_ANO_9_ANO",
                "8_9_ANO",
                "8_ANO",
                "9_ANO",
            ])
        elif turma_norm in {"J", "E", "TURMA_J", "TURMA_E"}:
            tokens.extend([
                "1_2_E_3_ANO_MULTISSERIADO",
                "1_ANO_2_ANO_3_ANO",
                "1_2_3_ANO_MULTISSERIADO",
                "1_2_3_ANO",
                "8_E_9_ANO_MULTISSERIADO",
                "8_E_9_ANO",
                "8_9_ANO_MULTISSERIADO",
                "8_ANO_9_ANO",
                "8_9_ANO",
                "1_ANO",
                "2_ANO",
                "3_ANO",
                "8_ANO",
                "9_ANO",
            ])
        elif "MULTISSERIAD" in turma_norm:
            if "EM" in turma_norm or "MEDIO" in turma_norm:
                tokens.extend([
                    "1_ANO_2_ANO_3_ANO",
                    "1_2_3_ANO",
                    "1_2_3_ANO_MULTISSERIADO",
                    "1_ANO_2_ANO_3_ANO_MULTISSERIADO",
                    "1_2_E_3_ANO_MULTISSERIADO",
                ])
            elif "EF" in turma_norm or "FUNDAMENTAL" in turma_norm:
                if any(x in turma_norm for x in ["8", "9", "TURMA_J", "TURMA_E"]):
                    tokens.extend([
                        "8_E_9_ANO_MULTISSERIADO",
                        "8_9_ANO_MULTISSERIADO",
                        "8_ANO_9_ANO",
                    ])
                elif any(x in turma_norm for x in ["6", "7", "TURMA_C", "TURMA_H"]):
                    tokens.extend([
                        "6_E_7_ANO_MULTISSERIADO",
                        "6_7_ANO_MULTISSERIADO",
                        "6_ANO_7_ANO",
                    ])
                else:
                    tokens.extend([
                        "8_E_9_ANO_MULTISSERIADO",
                        "8_9_ANO_MULTISSERIADO",
                        "6_E_7_ANO_MULTISSERIADO",
                        "6_7_ANO_MULTISSERIADO",
                    ])
            else:
                tokens.extend([
                    "1_ANO_2_ANO_3_ANO",
                    "6_7_ANO_MULTISSERIADO",
                    "6_E_7_ANO_MULTISSERIADO",
                    "8_9_ANO_MULTISSERIADO",
                    "8_E_9_ANO_MULTISSERIADO",
                ])
        return [token for token in dict.fromkeys(tokens) if token]

    numero = match.group(1)
    letra = match.group(2)
    sufixo = "TERMO" if match == match_termo else ("SERIE" if match == match_serie else "ANO")
    tokens.extend([f"{numero}_{sufixo}"])
    if sufixo != "TERMO":
        tokens.append(f"{numero}_SERIE" if sufixo == "ANO" else f"{numero}_ANO")
    if letra:
        tokens.extend([f"{numero}_{sufixo}_{letra}"])
    return [token for token in dict.fromkeys(tokens) if token]


def _nivel_preferido_para_turma(turma_norm: str) -> str:
    if turma_norm in {"C", "H"}:
        return "AF"
    if (
        "EM" in turma_norm
        or "ENSINO_MEDIO" in turma_norm
        or "SERIE" in turma_norm
        or "TERMO" in turma_norm
        or "EJA" in turma_norm
        or "123" in turma_norm
        or "1_2_3" in turma_norm
    ):
        if not ("EF" in turma_norm or "FUNDAMENTAL" in turma_norm or re.search(r"^[6789]", turma_norm)):
            return "EM"
    if "EF" in turma_norm:
        return "AF"
    if re.search(r"^[6789]_ANO", turma_norm) or re.search(r"^[6789]", turma_norm):
        return "AF"
    if "FUNDAMENTAL" in turma_norm:
        return "AF"
    return "EM"



def _pontuar_pasta_pdf(
    caminho: Path,
    disciplina_root: Path,
    nivel_preferido: str,
    bimestre_token: str,
    serie_tokens: list[str],
    turma_norm: str,
) -> tuple[int, int]:
    try:
        rel_parts = caminho.relative_to(disciplina_root).parts
    except ValueError:
        rel_parts = caminho.parts

    partes_norm = [_nome_pasta_normalizado(parte) for parte in rel_parts]
    partes_set = set(partes_norm)

    if bimestre_token:
        outros_bimestres = {f"{b}_BIMESTRE" for b in range(1, 5)} - {bimestre_token}
        if any(b in partes_set for b in outros_bimestres):
            return -100, len(rel_parts)

    score = 0
    if nivel_preferido in partes_set:
        score += 40
    if bimestre_token and bimestre_token in partes_set:
        score += 100
    if turma_norm and turma_norm in partes_set:
        score += 90
    tokens_multisseriados = [
        token for token in serie_tokens if token.count("_ANO") > 1 or "_E_" in token
    ]
    if any(token in partes_set for token in tokens_multisseriados):
        score += 120
    elif any(token in partes_set for token in serie_tokens):
        score += 70
    if rel_parts:
        ultimo = partes_norm[-1]
        if turma_norm and ultimo == turma_norm:
            score += 30
        elif any(token == ultimo for token in tokens_multisseriados):
            score += 50
        elif any(token == ultimo for token in serie_tokens):
            score += 20

    return score, len(rel_parts)


def _buscar_pasta_pdf_flexivel(
    disciplina_root: Path,
    nivel_preferido: str,
    bimestre_token: str,
    serie_tokens: list[str],
    turma_norm: str,
) -> Path | None:
    if not disciplina_root.exists():
        return None

    melhor: tuple[int, int, Path] | None = None
    for caminho in disciplina_root.rglob("*"):
        if not caminho.is_dir() or not _pasta_tem_pdfs(caminho):
            continue
        score, profundidade = _pontuar_pasta_pdf(
            caminho,
            disciplina_root,
            nivel_preferido,
            bimestre_token,
            serie_tokens,
            turma_norm,
        )
        if score <= 0:
            continue
        candidato = (score, -profundidade, caminho)
        if melhor is None or candidato > melhor:
            melhor = candidato

    return melhor[2] if melhor else None


def arquivo_parece_id_seduc(arquivo) -> bool:
    nome = getattr(arquivo, "name", None) or Path(str(arquivo)).name
    nome_base = Path(nome).stem.strip()
    return bool(re.fullmatch(r"\d{5,}", nome_base))


def arquivo_parece_referencia_nao_aula(arquivo) -> bool:
    nome = getattr(arquivo, "name", None) or Path(str(arquivo)).name
    nome_norm = normalizar_para_pasta(Path(nome).stem)
    marcadores = (
        "MATRIZ_DE_REFERENCIA",
        "MATRIZ_REFERENCIA",
        "REFERENCIAL_CURRICULAR",
    )
    return any(marcador in nome_norm for marcador in marcadores)


def numero_aula_pdf(arquivo) -> int | None:
    nome = getattr(arquivo, "name", None) or Path(str(arquivo)).name
    nome_base = Path(nome).stem
    
    # Limpar sufixos de cópia comuns
    nome_base = re.sub(r"\s*\(\d+\)$", "", nome_base)  # remove " (1)"
    nome_base = re.sub(r"(?i)\s*-\s*c[oó]pia$", "", nome_base)  # remove " - copia"
    nome_base = re.sub(r"(?i)\s*-\s*copy$", "", nome_base)  # remove " - copy"
    nome_base = nome_base.strip()

    # 1. Tentar encontrar padrão de número associado a "AULA" primeiro (prioridade máxima)
    match = re.search(r"\bAULA[_\s-]*(\d{1,4})\b", str(nome), flags=re.I)
    if match:
        return int(match.group(1))
        
    # 2. Tentar encontrar padrão de número no final precedido de _, -, ou espaço (ex: Nome_01)
    match_end = re.search(r"[\s_.-]\s*(\d{1,4})$", nome_base)
    if match_end:
        return int(match_end.group(1))
    
    # 3. Fallback geral, evitando IDs longos da SEDUC como "1612757.pdf".
    if arquivo_parece_id_seduc(nome):
        return None
    match_any = re.search(r"(?<!\d)(\d{1,3})(?!\d)", nome_base)
    if match_any:
        return int(match_any.group(1))
    return None


def filtrar_pdfs_para_aulas(arquivos) -> list:
    lista = list(arquivos or [])
    legiveis = [
        arquivo
        for arquivo in lista
        if not arquivo_parece_id_seduc(arquivo)
        and not arquivo_parece_referencia_nao_aula(arquivo)
    ]
    return legiveis or lista


def ordenar_pdfs_por_numero(arquivos) -> list:
    return sorted(
        list(arquivos or []),
        key=lambda arquivo: (
            numero_aula_pdf(arquivo) is None,
            numero_aula_pdf(arquivo) or 10**9,
            getattr(arquivo, "name", None) or Path(str(arquivo)).name,
        ),
    )


def ordenar_pdfs_por_sequencia(arquivos, sequencia_esperada, limite: int | None = None) -> list:
    arquivos_ordenados = ordenar_pdfs_por_numero(arquivos)
    por_numero = {numero_aula_pdf(arquivo): arquivo for arquivo in arquivos_ordenados if numero_aula_pdf(arquivo) is not None}
    sequencia = [int(numero) for numero in (sequencia_esperada or [])]

    selecionados = []
    usados = set()
    for numero in sequencia:
        arquivo = por_numero.get(numero)
        if arquivo is None:
            continue
        selecionados.append(arquivo)
        usados.add(arquivo)

    restantes = [arquivo for arquivo in arquivos_ordenados if arquivo not in usados]
    resultado = selecionados + restantes
    return resultado[:limite] if limite else resultado


def numeros_pdfs_faltantes(arquivos, sequencia_esperada) -> list[int]:
    disponiveis = {numero_aula_pdf(arquivo) for arquivo in (arquivos or [])}
    return [int(numero) for numero in (sequencia_esperada or []) if int(numero) not in disponiveis]


def _usa_aprofundamento_biologia_silvana(professor: str, disciplina: str, turma_norm: str) -> bool:
    professor_norm = normalizar_para_pasta(professor)
    disciplina_norm = normalizar_para_pasta(disciplina)
    return (
        "SILVANA" in professor_norm
        and "MARIANO" in professor_norm
        and "BIOLOGIA" in disciplina_norm
        and turma_norm == "2_ANO_A"
    )


def _pasta_aprofundamento_biologia_2ano_a(base_dir: str, bimestre_token: str) -> Path | None:
    raiz = Path(base_dir) / "APROFUNDAMENTO_EM_BIOLOGIA" / "EM"
    candidatos = []
    if bimestre_token:
        candidatos.extend(
            [
                raiz / bimestre_token / "2_ANO_A",
                raiz / bimestre_token / "3_ANO",
            ]
        )
    candidatos.extend([raiz / "2_ANO_A", raiz / "3_ANO"])
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    return candidatos[0] if candidatos else None


def _alias_pasta_biologia_eja_mesmo_conteudo(
    raiz_eja: Path,
    turma_norm: str,
    bimestre_token: str,
) -> Path | None:
    """Biologia EJA 2º e 3º termo compartilham a mesma pasta de conteúdos."""
    if "EJA_BIOLOGIA" not in str(raiz_eja).upper():
        return None
    if turma_norm not in {"2_TERMO", "3_TERMO"}:
        return None

    candidatos = []
    if bimestre_token:
        candidatos.append(raiz_eja / bimestre_token / "2_TERMO")
    candidatos.append(raiz_eja / "2_TERMO")

    for caminho in candidatos:
        if caminho.exists():
            return caminho
    return candidatos[0] if candidatos else None


def resolver_pasta_pdfs(
    base_dir: str,
    disciplina: str,
    turma: str,
    bimestre: str,
    professor: str = "",
    modalidade_eja: bool = False,
) -> Path:
    r"""Monta uma subpasta de PDFs a partir da raiz informada."""
    disciplina_entrada = str(disciplina or "")
    # Redirecionamento customizado para a professora Marta de Araújo
    prof_norm = normalizar_para_pasta(professor)
    disc_norm = _normalizar_disciplina_para_pasta(disciplina)
    turma_norm = normalizar_para_pasta(turma)

    if "MARTA" in prof_norm and "ARAUJO" in prof_norm:
        if disc_norm == "EDUCACAO_FINANCEIRA" and turma_norm in {"2_ANO_A", "3_ANO_A"}:
            turma = "8º ANO"

    if disc_norm in {"HISTORIA", "HISTORIA_CDP", "HISTORIACDP"}:
        if (
            "MULTISSERIAD" in disc_norm
            or "MULTISSERIAD" in turma_norm
            or "TURMA_E" in disc_norm
            or "TURMA_J" in disc_norm
            or "TURMA_E" in turma_norm
            or "TURMA_J" in turma_norm
            or "123" in turma_norm
            or "1_2_3" in turma_norm
            or turma_norm in {"1O2O3_EM", "123_C", "123_E"}
        ) and (
            (Path(base_dir) / "HISTORIA_CDP").exists()
            or (Path(base_dir) / "HISTORIACDP").exists()
            or (Path(base_dir) / "HISTÓRIACDP").exists()
        ):
            disciplina = "HISTORIA_CDP"

    if disc_norm == "GEOGRAFIA":
        if (
            "TURMA_J" in turma_norm
            or "TURMA_E" in turma_norm
            or "123" in turma_norm
            or "1_2_3" in turma_norm
            or "MULTISSERIAD" in turma_norm
        ) and (
            (Path(base_dir) / "GEOGRAFIA_CDP").exists()
            or (Path(base_dir) / "GEOGRAFIA-CDP").exists()
        ):
            disciplina = "GEOGRAFIA_CDP"

    disc_folder = _normalizar_disciplina_para_pasta(disciplina)

    eja_solicitado = bool(modalidade_eja or "EJA" in disc_folder)
    if eja_solicitado:
        raiz_eja_resolvida = resolver_raiz_disciplina_pdfs(
            base_dir,
            disciplina,
            modalidade_eja=True,
        )
        if raiz_eja_resolvida.exists():
            if _pasta_tem_pdfs(raiz_eja_resolvida):
                return raiz_eja_resolvida

            nivel_eja = _nivel_preferido_para_turma(normalizar_para_pasta(turma))
            turma_eja = normalizar_para_pasta(turma)
            bim_eja_match = re.search(r"(\d)_BIMESTRE", normalizar_para_pasta(bimestre))
            bim_eja = bim_eja_match.group(1) + "_BIMESTRE" if bim_eja_match else ""
            pasta_alias_biologia_eja = _alias_pasta_biologia_eja_mesmo_conteudo(
                raiz_eja_resolvida,
                turma_eja,
                bim_eja,
            )
            if pasta_alias_biologia_eja and _pasta_tem_pdfs(pasta_alias_biologia_eja):
                return pasta_alias_biologia_eja
            serie_eja = _tokens_serie_turma(turma_eja)
            pasta_flexivel_eja = _buscar_pasta_pdf_flexivel(
                raiz_eja_resolvida,
                nivel_preferido=nivel_eja,
                bimestre_token=bim_eja,
                serie_tokens=serie_eja,
                turma_norm=turma_eja,
            )
            if pasta_flexivel_eja:
                return pasta_flexivel_eja

        disciplina_base_eja = (
            re.sub(r"_?EJA$", "", disc_folder) or disc_folder
        )
        subpasta_eja = PASTAS_EJA_POR_DISCIPLINA.get(disciplina_base_eja) or PASTAS_EJA_POR_DISCIPLINA.get(disc_folder)
        if subpasta_eja:
            raiz_eja = Path(base_dir) / disciplina_base_eja / subpasta_eja
            if raiz_eja.exists():
                if _pasta_tem_pdfs(raiz_eja):
                    return raiz_eja

                nivel_eja = _nivel_preferido_para_turma(normalizar_para_pasta(turma))
                turma_eja = normalizar_para_pasta(turma)
                bim_eja_match = re.search(r"(\d)_BIMESTRE", normalizar_para_pasta(bimestre))
                bim_eja = bim_eja_match.group(1) + "_BIMESTRE" if bim_eja_match else ""
                serie_eja = _tokens_serie_turma(turma_eja)
                pasta_flexivel_eja = _buscar_pasta_pdf_flexivel(
                    raiz_eja,
                    nivel_preferido=nivel_eja,
                    bimestre_token=bim_eja,
                    serie_tokens=serie_eja,
                    turma_norm=turma_eja,
                )
                if pasta_flexivel_eja:
                    return pasta_flexivel_eja

                # As pastas EJA tambem podem receber os PDFs diretamente em
                # um subdiretorio sem a hierarquia regular de nivel/bimestre.
                for candidata in sorted(raiz_eja.rglob("*"), key=lambda item: str(item).casefold()):
                    if candidata.is_dir() and _pasta_tem_pdfs(candidata):
                        return candidata

                # Se a pasta foi criada, mas ainda está vazia, mantemos sua
                # resolução para não cair silenciosamente nos PDFs regulares.
                return raiz_eja

    turma_norm = normalizar_para_pasta(turma)
    bimestre_norm = normalizar_para_pasta(bimestre)
    match_bim = re.search(r"(\d)_BIMESTRE", bimestre_norm)
    bim = match_bim.group(1) + "_BIMESTRE" if match_bim else ""

    if disc_folder == "HISTORIA":
        if "6" in turma_norm and "7" in turma_norm:
            caminho_historia_cdp = Path(base_dir) / "HISTÓRIACDP" / "EF" / bim / "6_7_ANO_MULTISSERIADO"
            if caminho_historia_cdp.exists():
                return caminho_historia_cdp
        elif "8" in turma_norm and "9" in turma_norm:
            caminho_historia_cdp = Path(base_dir) / "HISTÓRIACDP" / "EF" / bim / "8_9_ANO_MULTISSERIADO"
            if caminho_historia_cdp.exists():
                return caminho_historia_cdp

    if _usa_aprofundamento_biologia_silvana(professor, disciplina, turma_norm):
        pasta_aprofundamento = _pasta_aprofundamento_biologia_2ano_a(base_dir, bim)
        if pasta_aprofundamento:
            return pasta_aprofundamento

    # Caso especial: se a pasta organizada diretamente por turma existir, usá-la
    if turma_norm:
        caminho_direto = Path(base_dir) / disc_folder / turma_norm
        if caminho_direto.exists():
            return caminho_direto

    disc_norm_entrada = normalizar_para_pasta(disciplina_entrada)
    if ("EF" in disc_norm_entrada or "FUNDAMENTAL" in disc_norm_entrada) and not ("EM" in turma_norm or "MEDIO" in turma_norm):
        nivel = "EF"
    else:
        nivel = _nivel_preferido_para_turma(turma_norm)

    raiz_resolvida = resolver_raiz_disciplina_pdfs(base_dir, disciplina)
    if nivel == "AF" and (raiz_resolvida / "EF").exists() and not (raiz_resolvida / "AF").exists():
        nivel = "EF"
    elif nivel == "EF" and (raiz_resolvida / "AF").exists() and not (raiz_resolvida / "EF").exists():
        nivel = "AF"

    serie = ""

    match_ano = re.search(r"(\d)_ANO", turma_norm)
    match_serie = re.search(r"(\d)_SERIE", turma_norm)
    serie_tokens = _tokens_serie_turma(turma_norm)
    if not any(token.count("_ANO") > 1 or "_E_" in token for token in serie_tokens):
        disc_tokens = _tokens_serie_turma(disc_norm_entrada)
        for tok in disc_tokens:
            if tok not in serie_tokens:
                serie_tokens.append(tok)

    if nivel == "EM" and (
        "MULTISSERIAD" in disc_norm_entrada
        or "MULTISSERIAD" in turma_norm
        or "CDP" in disc_folder
        or "TURMA_E" in turma_norm
        or "TURMA_J" in turma_norm
    ):
        if "1_ANO_2_ANO_3_ANO" not in serie_tokens:
            serie_tokens.append("1_ANO_2_ANO_3_ANO")
    elif nivel in {"EF", "AF"} and (
        "MULTISSERIAD" in disc_norm_entrada
        or "MULTISSERIAD" in turma_norm
        or "CDP" in disc_folder
    ):
        if (
            "8" in disc_norm_entrada
            or "9" in disc_norm_entrada
            or "8" in turma_norm
            or "9" in turma_norm
            or "TURMA_J" in disc_norm_entrada
            or "TURMA_J" in turma_norm
            or "TURMA_E" in disc_norm_entrada
            or "TURMA_E" in turma_norm
        ):
            for tok in ["8_E_9_ANO_MULTISSERIADO", "8_9_ANO_MULTISSERIADO", "8_ANO_9_ANO"]:
                if tok not in serie_tokens:
                    serie_tokens.append(tok)
        if (
            "6" in disc_norm_entrada
            or "7" in disc_norm_entrada
            or "6" in turma_norm
            or "7" in turma_norm
            or "TURMA_C" in disc_norm_entrada
            or "TURMA_C" in turma_norm
            or "TURMA_H" in disc_norm_entrada
            or "TURMA_H" in turma_norm
        ):
            for tok in ["6_E_7_ANO_MULTISSERIADO", "6_7_ANO_MULTISSERIADO", "6_ANO_7_ANO"]:
                if tok not in serie_tokens:
                    serie_tokens.append(tok)

    serie_multisseriada = next(
        (token for token in serie_tokens if token.count("_ANO") > 1 or "_E_" in token),
        "",
    )
    if serie_multisseriada:
        serie = serie_multisseriada
    elif match_ano:
        serie = match_ano.group(1) + "_ANO"
    elif match_serie:
        serie = match_serie.group(1) + "_ANO"

    raiz_resolvida = resolver_raiz_disciplina_pdfs(base_dir, disciplina)

    # A turma multisseriada 1º/2º/3º E.M pertence ao fluxo CDP. Sem esta
    # prioridade, a busca flexível pode escolher uma pasta regular (por
    # exemplo, ``3_ANO``) porque ela coincide com um dos anos da turma.
    if nivel == "EM" and serie_multisseriada == "1_ANO_2_ANO_3_ANO":
        caminho_bimestre = raiz_resolvida / nivel / bim
        if caminho_bimestre.exists():
            caminho_serie_especifica = caminho_bimestre / "1_ANO_2_ANO_3_ANO"
            if caminho_serie_especifica.exists() and _pasta_tem_pdfs(caminho_serie_especifica):
                return caminho_serie_especifica
            subpasta_cdp_em = _localizar_subpasta_cdp(caminho_bimestre, "EM")
            if subpasta_cdp_em:
                return subpasta_cdp_em
            if _pasta_tem_pdfs(caminho_bimestre):
                return caminho_bimestre

    if serie_multisseriada:
        candidatos_serie = [
            s for s in [serie] + serie_tokens
            if s and (s.count("_ANO") > 1 or "_E_" in s or "MULTISSERIADO" in s)
        ]
    else:
        candidatos_serie = [s for s in [serie] + serie_tokens if s]

    for candidata_serie in candidatos_serie:
        caminho_candidato = raiz_resolvida / nivel / bim / candidata_serie
        if caminho_candidato.exists():
            if _pasta_tem_pdfs(caminho_candidato):
                return caminho_candidato
            subpasta_cdp = _localizar_subpasta_cdp(caminho_candidato, nivel)
            if subpasta_cdp:
                return subpasta_cdp
            return caminho_candidato

    caminho_padrao = raiz_resolvida / nivel / bim / serie
    if caminho_padrao.exists():
        if _pasta_tem_pdfs(caminho_padrao):
            return caminho_padrao

        # Algumas disciplinas comuns (por exemplo, Geografia) usam uma
        # subpasta CDP_EM/CDP_EF dentro do mesmo bimestre. Quando a pasta do
        # bimestre não tem PDFs diretamente, essa subpasta é a fonte concreta
        # dos arquivos e deve ser priorizada pela busca automática.
        subpasta_cdp = _localizar_subpasta_cdp(caminho_padrao, nivel)
        if subpasta_cdp:
            return subpasta_cdp

        return caminho_padrao

    caminho_bimestre_direto = raiz_resolvida / nivel / bim
    if caminho_bimestre_direto.exists() and _pasta_tem_pdfs(caminho_bimestre_direto):
        return caminho_bimestre_direto

    caminho_flexivel = _buscar_pasta_pdf_flexivel(
        raiz_resolvida,
        nivel_preferido=_nivel_preferido_para_turma(turma_norm),
        bimestre_token=bim,
        serie_tokens=serie_tokens,
        turma_norm=turma_norm,
    )
    if caminho_flexivel:
        return caminho_flexivel

    if caminho_bimestre_direto.exists():
        subpasta_cdp = _localizar_subpasta_cdp(caminho_bimestre_direto, nivel)
        if subpasta_cdp:
            return subpasta_cdp
        for sub in sorted(caminho_bimestre_direto.iterdir(), key=lambda x: str(x).casefold()):
            if sub.is_dir() and _pasta_tem_pdfs(sub):
                return sub
        return caminho_bimestre_direto

    return caminho_padrao


def garantir_caminho_na_raiz(caminho: str | Path, raiz: str | Path) -> Path:
    """Resolve ``caminho`` e rejeita qualquer resultado fora de ``raiz``."""
    raiz_resolvida = Path(raiz).resolve(strict=False)
    caminho_resolvido = Path(caminho).resolve(strict=False)
    try:
        caminho_resolvido.relative_to(raiz_resolvida)
    except ValueError as exc:
        raise ValueError(
            f"Caminho fora da raiz autorizada de PDFs: {caminho_resolvido}"
        ) from exc
    return caminho_resolvido
