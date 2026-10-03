# PLANOS_LUAN — Leia-me rápido

Sistema de planos de aula mensais em Word (Python/Streamlit). Documentação completa em `README.md`, `AGENTS.md` e `GEMINI.md`.

## Como abrir

Execute `AbrirPLANOS_LUAN.ps1` (ou `ABRIR_PLANOS_LUAN.vbs`). Para reiniciar use `ReiniciarPLANOS_LUAN.bat`; para fechar, `FecharPLANOS_LUAN.bat`.

## Como reinstalar dependências

Execute `InstalarPLANOS_LUAN.bat` (usa `requirements.txt`).

## Estrutura importante

- Aplicativo principal: `planos_luan_app.py` (telas em `ui/`)
- Ambiente virtual: `.venv`
- Modelos Word: `templates`
- Dados (fora do Git): `C:\Users\LuanDias\PLANOS_LUAN_DADOS`
  - Banco de dados: `planos_luan.db`
  - PDFs pedagógicos: `PDF_AULAS`
  - Planos prontos: `Planos feitos\PROFESSOR\DISCIPLINA\MES\`
  - Referências metodológicas: `REFERENCIAS_METODOLOGICAS`

## Abas

Planos gerais · CDP-EF/EM · EJA · Cadastro · Diagnóstico · Histórico · **Conferência Mensal** (professor + mês → planos feitos ✅ e pendentes ⬜).

*Atualizado em 03/10/2026.*
