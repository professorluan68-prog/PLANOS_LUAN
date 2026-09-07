# tela_inicial_moderna.py
# Constantes de modernizacao visual — Tema Verde Educacional + Roxo Índigo
# Identidade: PLANOS DE AULA — SEDUC

HERO_CSS = """
<meta name="google" content="notranslate">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    :root {
        --app-bg-dark:    #0F1A12;
        --app-bg-mid:     #162518;
        --app-bg-deep:    #0A1510;
        --ink-light:      #F1FDF4;
        --ink-muted:      #86EFAC;
        --ink-dim:        #4ADE80;
        --brand-accent:   #7C3AED;
        --brand-purple:   #A78BFA;
        --brand-green:    #22C55E;
        --brand-lime:     #86EFAC;
        --font-main:      'Inter', sans-serif;
    }

    /* ── Fundo da aplicação ─────────────────────────────── */
    .stApp {
        background: linear-gradient(180deg, var(--app-bg-dark) 0%, var(--app-bg-mid) 50%, var(--app-bg-deep) 100%);
        color: var(--ink-light);
        font-family: var(--font-main);
    }

    /* ── Scrollbar ──────────────────────────────────────── */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(10, 21, 16, 0.6); }
    ::-webkit-scrollbar-thumb { background: rgba(124, 58, 237, 0.45); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(124, 58, 237, 0.75); }

    /* ── Hero section ───────────────────────────────────── */
    .app-hero {
        position: relative;
        background: linear-gradient(135deg, #162518 0%, #1A2F1D 55%, #1B2540 100%);
        padding: 36px 40px;
        border-radius: 18px;
        margin-bottom: 22px;
        border: 1px solid rgba(34, 197, 94, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5),
                    inset 0 0 40px rgba(124, 58, 237, 0.04);
        backdrop-filter: blur(10px);
        overflow: hidden;
        animation: fadeInUp 0.7s ease-out forwards;
    }

    /* Brilho radial roxo no canto direito */
    .app-hero::before {
        content: '';
        position: absolute;
        top: -40%;
        right: -15%;
        width: 55%;
        height: 150%;
        background: radial-gradient(ellipse, rgba(124, 58, 237, 0.12), transparent 65%);
        pointer-events: none;
    }

    /* Brilho verde no canto inferior esquerdo */
    .app-hero::after {
        content: '';
        position: absolute;
        bottom: -30%;
        left: -5%;
        width: 45%;
        height: 90%;
        background: radial-gradient(ellipse, rgba(34, 197, 94, 0.08), transparent 60%);
        pointer-events: none;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Eyebrow + ponto pulsante ───────────────────────── */
    .app-hero__eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.80rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: var(--brand-green);
        text-transform: uppercase;
        margin-bottom: 14px;
        background: rgba(34, 197, 94, 0.10);
        padding: 5px 14px;
        border-radius: 20px;
        border: 1px solid rgba(34, 197, 94, 0.22);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background-color: var(--brand-green);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--brand-green);
        animation: pulse 2s infinite;
        flex-shrink: 0;
    }

    @keyframes pulse {
        0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
        70%  { transform: scale(1);    box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    /* ── Título com gradiente ───────────────────────────── */
    .app-title {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0 0 4px 0;
        line-height: 1.08;
        background: linear-gradient(90deg, #FFFFFF 0%, #86EFAC 42%, #C4B5FD 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }

    /* ── Subtítulo institucional ────────────────────────── */
    .app-title-sub {
        font-size: 1.0rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--brand-purple);
        margin: 0 0 16px 0;
        opacity: 0.9;
    }

    .app-subtitle {
        font-size: 1.0rem;
        color: var(--ink-muted);
        max-width: 780px;
        line-height: 1.65;
        margin-bottom: 26px;
    }

    /* ── Pills de features ──────────────────────────────── */
    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .hero-pill {
        background: rgba(26, 47, 29, 0.75);
        color: var(--brand-purple);
        padding: 7px 15px;
        border-radius: 24px;
        font-size: 0.87rem;
        font-weight: 600;
        border: 1px solid rgba(124, 58, 237, 0.22);
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        gap: 7px;
        cursor: default;
    }

    .hero-pill:hover {
        background: rgba(124, 58, 237, 0.15);
        border-color: var(--brand-accent);
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.2);
    }

    /* ── Stats Bar ──────────────────────────────────────── */
    .stats-bar {
        display: flex;
        justify-content: space-between;
        background: rgba(26, 47, 29, 0.55);
        border: 1px solid rgba(45, 74, 48, 0.7);
        border-radius: 12px;
        padding: 18px 28px;
        margin-bottom: 28px;
        backdrop-filter: blur(6px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }

    .stat-item {
        text-align: center;
        flex: 1;
        border-right: 1px solid rgba(45, 74, 48, 0.5);
        padding: 0 8px;
    }

    .stat-item:last-child { border-right: none; }

    .stat-number {
        font-size: 1.85rem;
        font-weight: 800;
        color: var(--ink-light);
        margin-bottom: 3px;
        line-height: 1;
    }

    .stat-number.accent { color: var(--brand-purple); }

    .stat-label {
        font-size: 0.76rem;
        color: var(--ink-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }

    /* ── Section header ─────────────────────────────────── */
    .section-header-modern {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 28px 0 20px 0;
        padding-bottom: 14px;
        border-bottom: 1px solid rgba(45, 74, 48, 0.55);
    }

    .section-title-modern {
        font-size: 1.42rem;
        font-weight: 700;
        color: var(--ink-light);
        margin: 0;
    }

    .section-badge {
        background: rgba(124, 58, 237, 0.15);
        color: var(--brand-purple);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        border: 1px solid rgba(124, 58, 237, 0.28);
        letter-spacing: 0.08em;
    }

    /* ── Botões Streamlit ───────────────────────────────── */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #6D28D9 0%, #7C3AED 100%) !important;
        border-color: transparent !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4) !important;
        transition: all 0.22s ease !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover,
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(124, 58, 237, 0.55) !important;
        background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%) !important;
    }

    .stButton > button[kind="secondary"] {
        background: rgba(26, 47, 29, 0.65) !important;
        border: 1px solid rgba(45, 74, 48, 0.8) !important;
        color: var(--ink-light) !important;
        backdrop-filter: blur(4px) !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: rgba(124, 58, 237, 0.12) !important;
        border-color: var(--brand-accent) !important;
        color: var(--brand-purple) !important;
    }

    /* ── Checkboxes, Radios ─────────────────────────────── */
    [data-testid="stRadio"] label p,
    [data-testid="stCheckbox"] label p,
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {
        color: #F1FDF4 !important;
    }

    [data-testid="stRadio"] [aria-checked="true"] p,
    [data-testid="stCheckbox"] [aria-checked="true"] p {
        color: #A78BFA !important;
        font-weight: 600 !important;
    }

    /* ── Inputs nativos ─────────────────────────────────── */
    [data-baseweb="select"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: rgba(15, 26, 18, 0.85) !important;
        color: var(--ink-light) !important;
        border: 1px solid rgba(45, 74, 48, 0.8) !important;
        border-radius: 6px !important;
    }

    /* Glow roxo no foco */
    [data-baseweb="select"] div:focus-within,
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--brand-accent) !important;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.25), 0 0 10px rgba(124, 58, 237, 0.15) !important;
    }

    /* ── Textos dos labels ──────────────────────────────── */
    /* Nota: 'p' removido — evita sobrescrever cores inline de alertas HTML */
    .stMarkdown, .stText, label {
        color: var(--ink-light) !important;
    }


    /* ── Sidebar ────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A1510 0%, #162518 100%) !important;
        border-right: 1px solid rgba(45, 74, 48, 0.6) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--ink-light);
    }

    /* ── Divisores de seção ─────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(45, 74, 48, 0.5) !important;
        margin: 20px 0 !important;
    }
</style>
"""

HERO_HTML = """
<div class="app-hero">
    <div class="app-hero__eyebrow">
        <div class="status-dot"></div>
        SISTEMA ATIVO — SEDUC
    </div>
    <div class="app-title">Planos de Aula</div>
    <div class="app-title-sub">Secretaria de Educação — SEDUC</div>
    <div class="app-subtitle">
        Geração automatizada de planejamento escolar com integração IA,
        processamento de guias pedagógicos e formatação Word padronizada pela SEDUC.
    </div>
    <div class="hero-pills">
        <span class="hero-pill">📘 Leitura automática de PDFs</span>
        <span class="hero-pill">📎 Processamento em lote</span>
        <span class="hero-pill">✏️ Revisão e convalidação</span>
        <span class="hero-pill">📄 Saída DOCX padronizada</span>
        <span class="hero-pill">🤖 IA Integrada</span>
    </div>
</div>
"""

STATS_HTML = """
<div class="stats-bar">
    <div class="stat-item">
        <div class="stat-number accent">23</div>
        <div class="stat-label">Disciplinas</div>
    </div>
    <div class="stat-item">
        <div class="stat-number">3</div>
        <div class="stat-label">Modelos DOCX</div>
    </div>
    <div class="stat-item">
        <div class="stat-number accent">2</div>
        <div class="stat-label">Motores IA</div>
    </div>
    <div class="stat-item">
        <div class="stat-number">5</div>
        <div class="stat-label">Modos de Uso</div>
    </div>
    <div class="stat-item">
        <div class="stat-number accent">+3K</div>
        <div class="stat-label">Aulas Mapeadas</div>
    </div>
</div>
"""

SECTION_HEADER_HTML = """
<div class="section-header-modern">
    <h2 class="section-title-modern">Área de Trabalho</h2>
    <span class="section-badge">Configuração</span>
</div>
"""

OPTION_MENU_STYLES = {
    "container": {
        "padding": "5px !important",
        "background-color": "rgba(26, 47, 29, 0.7)",
        "border-radius": "12px",
        "border": "1px solid rgba(45, 74, 48, 0.6)",
        "backdrop-filter": "blur(10px)",
    },
    "icon": {"color": "#86EFAC", "font-size": "16px"},
    "nav-link": {
        "font-size": "14px",
        "text-align": "center",
        "margin": "0px 4px",
        "font-weight": "600",
        "color": "#86EFAC",
        "--hover-color": "rgba(124, 58, 237, 0.15)",
        "border-radius": "8px",
        "transition": "all 0.2s ease",
    },
    "nav-link-selected": {
        "background": "linear-gradient(135deg, #6D28D9 0%, #7C3AED 100%)",
        "color": "#ffffff",
        "font-weight": "700",
        "box-shadow": "0 4px 14px rgba(124, 58, 237, 0.35)",
    },
}
