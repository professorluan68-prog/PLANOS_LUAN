import sys
import os
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.lote import processar_varios_pdfs
from docx_generator.preencher import preencher_documento
from core.modelos_docx import caminho_template_por_contexto
from io import BytesIO

def main():
    base_dir = Path(r"D:\PDF novos\LINGUA_PORTUGUESA\EM\3_BIMESTRE")
    out_dir = Path(r"D:\PLANOS_LUAN\Planos feitos\LINGUA_PORTUGUESA_EM")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    anos = ["1_ANO", "2_ANO", "3_ANO"]
    
    for ano in anos:
        print(f"\nProcessando {ano}...")
        dir_ano = base_dir / ano
        if not dir_ano.exists():
            continue
            
        pdfs = list(dir_ano.glob("*.pdf"))
        if not pdfs:
            continue
            
        # Ordenar PDFs por aula
        pdfs.sort(key=lambda p: p.name)
        
        # Mock CLI parameters
        disciplina = "Língua Portuguesa"
        turma = f"{ano.split('_')[0]}º ANO"
        professor = "PROFESSOR PADRAO" # Pode ser trocado depois na revisão final
        bimestre = "3º Bimestre"
        mes = "AGOSTO"
        
        caminhos_str = [str(p) for p in pdfs]
        
        print(f"Extraindo dados de {len(caminhos_str)} PDFs...")
        aulas = processar_varios_pdfs(
            caminhos_pdf=caminhos_str,
            disciplina=disciplina,
            turma=turma,
            bimestre=bimestre,
            usar_ia=False,
            professor=professor
        )
        
        # Gerar DOCX
        print(f"Gerando DOCX para {ano}...")
        template_path = caminho_template_por_contexto("egle", disciplina)
        with open(template_path, "rb") as f:
            modelo_bytes = f.read()
            
        docx_bytes = preencher_documento(
            BytesIO(modelo_bytes),
            aulas,
            escola="ESCOLA PADRÃO",
            professor=professor,
            disciplina=disciplina,
            turma=turma,
            mes=mes,
            bimestre=bimestre,
            semana="Semana Padrão"
        )
        
        out_file = out_dir / f"Planos_LP_{ano}.docx"
        with open(out_file, "wb") as f:
            f.write(docx_bytes.getvalue() if hasattr(docx_bytes, 'getvalue') else docx_bytes)
        print(f"Salvo em: {out_file}")

if __name__ == "__main__":
    main()
