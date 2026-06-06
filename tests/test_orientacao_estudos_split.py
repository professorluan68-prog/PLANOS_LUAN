from pathlib import Path
import pytest
from core import lote
from core import helpers

TEXTO_TESTE_MULTIPLAS_ETAPAS = """
MISSAO 6 - Uma palavra puxa a outra
Etapa 1
Texto da Etapa 1. Conectivos e conjunções.

Etapa 2
Texto da Etapa 2. Elementos adverbiais.

Etapa 3
Texto da Etapa 3. O vendedor de picolé.

Etapa final
Texto da Etapa Final. Conclusão e comentário.
"""

def test_lote_detecta_etapa_por_nome_arquivo(monkeypatch):
    monkeypatch.setattr(lote, "_extrair_texto_pdf", lambda caminho: TEXTO_TESTE_MULTIPLAS_ETAPAS)

    # Caso 1: Nome do arquivo contem ETAPA_2, indice_aula = 0 (deveria forçar Etapa 2 ao invés de usar idx 0/Etapa 1)
    aula_etapa_2 = lote._aula_por_pdf(
        "AULA_01_ETAPA_2.pdf",
        "Orientação de Estudos",
        "6º ano A",
        "2º bimestre",
        usar_ia=False,
        provedor_ia="",
        indice_aula=0,
        total_aulas=4,
    )
    assert "ETAPA 2" in aula_etapa_2["tema"]
    assert "expressoes adverbiais" in " ".join(item.get("texto", "") for item in aula_etapa_2["metodologia"] if isinstance(item, dict)).lower()

    # Caso 2: Nome do arquivo contem ETAPA_FINAL, indice_aula = 0
    aula_etapa_final = lote._aula_por_pdf(
        "AULA_01_ETAPA_FINAL.pdf",
        "Orientação de Estudos",
        "6º ano A",
        "2º bimestre",
        usar_ia=False,
        provedor_ia="",
        indice_aula=0,
        total_aulas=4,
    )
    assert "ETAPA FINAL" in aula_etapa_final["tema"]
    assert "diagrama" in " ".join(item.get("texto", "") for item in aula_etapa_final["metodologia"] if isinstance(item, dict)).lower()

    # Caso 3: Nome do arquivo nao contem etapa, deveria usar indice_aula (retrocompatibilidade)
    aula_retrocompativel = lote._aula_por_pdf(
        "AULA_01.pdf",
        "Orientação de Estudos",
        "6º ano A",
        "2º bimestre",
        usar_ia=False,
        provedor_ia="",
        indice_aula=2, # Deveria pegar Etapa 3
        total_aulas=4,
    )
    assert "ETAPA 3" in aula_retrocompativel["tema"]
    assert "picole" in " ".join(item.get("texto", "") for item in aula_retrocompativel["metodologia"] if isinstance(item, dict)).lower()


def test_resolver_pasta_pdfs_com_caminho_direto(tmp_path):
    # Cria uma pasta mock no local de destino
    pasta_disciplina = tmp_path / "ORIENTACAO_DE_ESTUDOS"
    pasta_turma = pasta_disciplina / "6_ANO_A"
    pasta_turma.mkdir(parents=True, exist_ok=True)

    # Executa a resolucao com a turma que possui pasta direta
    res = helpers.resolver_pasta_pdfs(
        base_dir=str(tmp_path),
        disciplina="Orientação de Estudos",
        turma="6º ANO A",
        bimestre="1º Bimestre"
    )

    assert res == pasta_turma
    assert res.exists()

    # Executa a resolucao com uma turma que nao possui pasta direta (caminho padrão)
    res_padrao = helpers.resolver_pasta_pdfs(
        base_dir=str(tmp_path),
        disciplina="Orientação de Estudos",
        turma="9º ANO A",
        bimestre="1º Bimestre"
    )

    # O caminho padrão deveria cair na estrutura convencional: AF / 1_BIMESTRE / 9_ANO
    pasta_esperada_padrao = pasta_disciplina / "AF" / "1_BIMESTRE" / "9_ANO"
    assert res_padrao == pasta_esperada_padrao
