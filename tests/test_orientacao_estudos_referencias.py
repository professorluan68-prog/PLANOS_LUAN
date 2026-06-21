from docx import Document

from core import lote
from core.helpers import resolver_pasta_pdfs
from core.referencias_orientacao_estudos import (
    localizar_docx_referencia_orientacao_estudos,
    referencia_orientacao_estudos_por_pdf,
    titulos_referencia_orientacao_estudos_por_docx,
)


def _criar_docx_referencia_orientacao(caminho):
    doc = Document()
    doc.add_paragraph("METODOLOGIAS - ORIENTACAO DE ESTUDOS - 3ª SERIE DO ENSINO MEDIO")

    doc.add_paragraph("AULA 1 — Informações em infográficos, gráficos, tabelas e esquemas")
    doc.add_paragraph("Metodologia")
    doc.add_paragraph("Para começar: Apresentar infográficos e discutir como dados visuais podem informar ou manipular.")
    doc.add_paragraph("Foco no conteúdo: Explicar leitura crítica de gráficos, tabelas e esquemas com atenção às fontes.")
    doc.add_paragraph("Na prática: Analisar textos multissemióticos e identificar tema, fonte e organização visual.")
    doc.add_paragraph("Encerramento: Socializar conclusões sobre verificação de fontes e cidadania digital.")
    doc.add_paragraph("Acompanhamento da aprendizagem")
    doc.add_paragraph("☑ Verificar se os estudantes diferenciam a finalidade dos infográficos apresentados.")
    doc.add_paragraph("☑ Observar se identificam a origem e a confiabilidade das fontes de dados.")
    doc.add_paragraph("☑ Acompanhar se relacionam linguagem verbal e não-verbal na análise.")
    doc.add_paragraph("Acessibilidade")
    doc.add_paragraph("☑ Disponibilizar glossário visual simples para apoiar a leitura dos infográficos.")
    doc.add_paragraph("☑ Oferecer roteiro simplificado com perguntas norteadoras.")
    doc.add_paragraph("☑ Permitir respostas por palavras-chave, esquemas ou registro oral mediado.")

    doc.add_paragraph("AULA 2 — Desenhando para entender melhor")
    doc.add_paragraph("Metodologia")
    doc.add_paragraph("Para começar: Retomar formas de organizar e apresentar conhecimentos.")
    doc.add_paragraph("Acompanhamento da aprendizagem")
    doc.add_paragraph("☑ Verificar se reconhecem características dos gêneros visuais.")
    doc.add_paragraph("☑ Observar se identificam estratégia visual e público-alvo.")
    doc.add_paragraph("☑ Acompanhar se localizam dados específicos no material.")
    doc.add_paragraph("Acessibilidade")
    doc.add_paragraph("☑ Disponibilizar banco de termos no quadro.")
    doc.add_paragraph("☑ Oferecer versão ampliada dos infográficos.")
    doc.add_paragraph("☑ Permitir registro por tópicos, símbolos ou resposta oral.")

    doc.add_paragraph("AULA 3 — Seleção de informações e argumentação em textos multissemióticos")
    doc.add_paragraph("Metodologia")
    doc.add_paragraph("Para começar: Apresentar questão de exame com leitura de texto verbal e visual.")
    doc.add_paragraph("Acompanhamento da aprendizagem")
    doc.add_paragraph("☑ Verificar se relacionam recursos verbais e não-verbais.")
    doc.add_paragraph("☑ Observar se identificam dados usados para sustentar argumentos.")
    doc.add_paragraph("☑ Acompanhar se analisam alternativas com base em evidências.")
    doc.add_paragraph("Acessibilidade")
    doc.add_paragraph("☑ Disponibilizar diagramas ampliados com marcações.")
    doc.add_paragraph("☑ Permitir resolução em duplas com tempo ampliado.")
    doc.add_paragraph("☑ Oferecer perguntas mediadoras para leitura dos gráficos.")
    doc.save(caminho)


def test_referencia_orientacao_estudos_le_docx_da_pasta_do_pdf(tmp_path):
    caminho_docx = tmp_path / "Metodologias_Orientacao_de_Estudos_3_Ano_Ensino_Medio.docx"
    caminho_pdf = tmp_path / "PDF1_com_habilidade_essencial.pdf"
    _criar_docx_referencia_orientacao(caminho_docx)
    caminho_pdf.write_bytes(b"%PDF-1.4\n")

    referencia = referencia_orientacao_estudos_por_pdf(caminho_pdf, "")

    assert localizar_docx_referencia_orientacao_estudos(caminho_pdf) == caminho_docx
    assert referencia["numero"] == 1
    assert referencia["titulo"] == "Informações em infográficos, gráficos, tabelas e esquemas"
    assert [etapa["titulo"] for etapa in referencia["metodologia"]][:3] == [
        "Para começar",
        "Foco no conteúdo",
        "Na prática",
    ]
    assert len(referencia["acompanhamento"]) == 3
    assert len(referencia["acessibilidade"]) == 3


def test_titulos_orientacao_estudos_por_docx(tmp_path):
    caminho_docx = tmp_path / "Metodologias_Orientacao_de_Estudos_3_Ano_Ensino_Medio.docx"
    _criar_docx_referencia_orientacao(caminho_docx)

    titulos = titulos_referencia_orientacao_estudos_por_docx(caminho_docx)

    assert titulos == {
        1: "Informações em infográficos, gráficos, tabelas e esquemas",
        2: "Desenhando para entender melhor",
        3: "Seleção de informações e argumentação em textos multissemióticos",
    }


def test_orientacao_estudos_resultado_usa_docx_e_titulo_oficial(tmp_path, monkeypatch):
    caminho_docx = tmp_path / "Metodologias_Orientacao_de_Estudos_3_Ano_Ensino_Medio.docx"
    caminho_pdf = tmp_path / "PDF1_com_habilidade_essencial.pdf"
    _criar_docx_referencia_orientacao(caminho_docx)
    caminho_pdf.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        lote,
        "_extrair_texto_pdf",
        lambda caminho: (
            "LINGUA PORTUGUESA\nMATERIAL DE APOIO PEDAGOGICO\n"
            "Habilidade essencial: Compreender criticamente textos de divulgacao cientifica."
        ),
    )

    aula = lote._aula_por_pdf(
        str(caminho_pdf),
        "Orientação de Estudos",
        "3º ANO A",
        "3º Bimestre",
        usar_ia=False,
        provedor_ia="",
    )

    assert aula["tema"] == "Informações em infográficos, gráficos, tabelas e esquemas"
    assert aula["material"] == "AULA 1 - Informações em infográficos, gráficos, tabelas e esquemas"
    assert aula["origem_metodologia"] == "docx_referencia_orientacao_estudos"
    assert "fontes" in aula["metodologia"][1]["texto"].lower()
    assert len(aula["acompanhamento"]) == 3
    assert len(aula["acessibilidade"]) == 3


def test_resolver_pasta_pdfs_orientacao_estudos_em_sem_pasta_bimestre(tmp_path):
    pasta = tmp_path / "ORIENTACAO_DE_ESTUDOS" / "EM" / "3_ANO"
    pasta.mkdir(parents=True)
    (pasta / "PDF1_com_habilidade_essencial.pdf").write_bytes(b"%PDF-1.4\n")

    resolvida = resolver_pasta_pdfs(
        str(tmp_path),
        "Orientação de Estudos",
        "3º ANO A",
        "3º Bimestre",
    )

    assert resolvida == pasta
