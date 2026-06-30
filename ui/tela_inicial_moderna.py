# tela_inicial_moderna.py
# Constantes de modernizacao visual

HERO_CSS = """
<meta name="google" content="notranslate">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    :root { 
        --app-bg-dark: #0D1B2A; 
        --app-bg-mid: #112236; 
        --app-bg-deep: #0A1628; 
        --ink-light: #F0F6FF; 
        --ink-muted: #8AA4B7;
        --brand-neon: #00F0FF;
        --brand-blue: #2563EB;
        --brand-green: #00E676;
        --font-main: 'Inter', sans-serif; 
    }
    
    /* Fundo da aplicacao */
    .stApp { 
        background: linear-gradient(180deg, var(--app-bg-dark) 0%, var(--app-bg-mid) 48%, var(--app-bg-deep) 100%); 
        color: var(--ink-light); 
        font-family: var(--font-main); 
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(10, 22, 40, 0.5);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(37, 99, 235, 0.5);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(37, 99, 235, 0.8);
    }
    
    /* Hero section */
    .app-hero { 
        position: relative;
        background: rgba(17, 34, 54, 0.6); 
        padding: 40px; 
        border-radius: 16px; 
        margin-bottom: 24px; 
        border: 1px solid rgba(37, 99, 235, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 0 20px rgba(0, 240, 255, 0.05);
        backdrop-filter: blur(10px);
        overflow: hidden;
        animation: fadeInUp 0.8s ease-out forwards;
    }
    
    /* Brilho radial nos cantos do hero */
    .app-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at top right, rgba(0, 240, 255, 0.1), transparent 30%),
                    radial-gradient(circle at bottom left, rgba(37, 99, 235, 0.15), transparent 40%);
        pointer-events: none;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Eyebrow e ponto pulsante */
    .app-hero__eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: var(--brand-neon);
        text-transform: uppercase;
        margin-bottom: 16px;
        background: rgba(0, 240, 255, 0.1);
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid rgba(0, 240, 255, 0.2);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: var(--brand-green);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--brand-green);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(0, 230, 118, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }
    
    /* Título com gradiente */
    .app-title { 
        font-size: 3rem; 
        font-weight: 800; 
        margin: 0 0 16px 0; 
        color: #F0F6FF; /* fallback */
        background: linear-gradient(90deg, #FFFFFF, var(--brand-neon), var(--brand-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }
    
    .app-subtitle { 
        font-size: 1.15rem; 
        color: var(--ink-muted); 
        max-width: 800px;
        line-height: 1.6;
        margin-bottom: 32px;
    }
    
    /* Pills de features */
    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
    }
    
    .hero-pill {
        background: rgba(13, 27, 42, 0.7);
        color: var(--ink-light);
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 0.9rem;
        font-weight: 600;
        border: 1px solid rgba(138, 164, 183, 0.2);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: default;
    }
    
    .hero-pill:hover {
        background: rgba(37, 99, 235, 0.2);
        border-color: var(--brand-blue);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* Stats Bar */
    .stats-bar {
        display: flex;
        justify-content: space-between;
        background: rgba(17, 34, 54, 0.5);
        border: 1px solid rgba(138, 164, 183, 0.15);
        border-radius: 12px;
        padding: 20px 32px;
        margin-bottom: 32px;
        animation: fadeInUp 1s ease-out forwards;
        backdrop-filter: blur(5px);
    }
    
    .stat-item {
        text-align: center;
        flex: 1;
        border-right: 1px solid rgba(138, 164, 183, 0.15);
    }
    
    .stat-item:last-child {
        border-right: none;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        color: var(--ink-light);
        margin-bottom: 4px;
        line-height: 1;
    }
    
    .stat-number.accent {
        color: var(--brand-neon);
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: var(--ink-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Section header */
    .section-header-modern {
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 32px 0 24px 0;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(138, 164, 183, 0.2);
    }
    
    .section-title-modern {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--ink-light);
        margin: 0;
    }
    
    .section-badge {
        background: rgba(37, 99, 235, 0.2);
        color: var(--brand-neon);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        border: 1px solid rgba(37, 99, 235, 0.4);
    }
    
    /* Componentes nativos Streamlit - Inputs e Botões */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
        border-color: transparent !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover,
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6) !important;
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: rgba(17, 34, 54, 0.6) !important;
        border: 1px solid rgba(138, 164, 183, 0.3) !important;
        color: var(--ink-light) !important;
        backdrop-filter: blur(4px) !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(37, 99, 235, 0.15) !important;
        border-color: var(--brand-blue) !important;
        color: var(--brand-neon) !important;
    }
    
    /* Checkboxes, Radios, Selects */
    [data-testid="stRadio"] label p,
    [data-testid="stCheckbox"] label p,
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {
        color: #F0F6FF !important;
    }
    
    [data-testid="stRadio"] [aria-checked="true"] p,
    [data-testid="stCheckbox"] [aria-checked="true"] p {
        color: #00F0FF !important;
        font-weight: 600 !important;
    }
    
    /* Fundo dos inputs nativos */
    [data-baseweb="select"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: rgba(17, 34, 54, 0.8) !important;
        color: var(--ink-light) !important;
        border: 1px solid rgba(138, 164, 183, 0.3) !important;
        border-radius: 6px !important;
    }
    
    /* Glow no foco */
    [data-baseweb="select"] div:focus-within,
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--brand-neon) !important;
        box-shadow: 0 0 0 1px var(--brand-neon), 0 0 10px rgba(0, 240, 255, 0.2) !important;
    }
    
    /* Textos dos labels */
    .stMarkdown, .stText, label, p {
        color: var(--ink-light) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--app-bg-deep) !important;
        border-right: 1px solid rgba(138, 164, 183, 0.15) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: var(--ink-light);
    }
</style>
"""

HERO_HTML = """
<div class="app-hero">
    <div class="app-hero__eyebrow">
        <div class="status-dot"></div>
        SISTEMA ATIVO
    </div>
    <div class="app-title">Plano de Aula Inteligente</div>
    <div class="app-subtitle">
        Geração automatizada de planejamento escolar com integração IA, 
        processamento de guias priorizados e formatação Word nativa.
    </div>
    <div class="hero-pills">
        <span class="hero-pill">📘 Leitura automática</span>
        <span class="hero-pill">📎 Processamento em lote</span>
        <span class="hero-pill">✏️ Convalidação manual</span>
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
        "background-color": "rgba(17, 34, 54, 0.7)",
        "border-radius": "10px",
        "border": "1px solid rgba(138, 164, 183, 0.2)",
        "backdrop-filter": "blur(10px)",
    },
    "icon": {"color": "#8AA4B7", "font-size": "16px"},
    "nav-link": {
        "font-size": "14px",
        "text-align": "center",
        "margin": "0px 4px",
        "font-weight": "600",
        "color": "#8AA4B7",
        "--hover-color": "rgba(37, 99, 235, 0.15)",
        "border-radius": "8px",
        "transition": "all 0.2s ease"
    },
    "nav-link-selected": {
        "background": "linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%)",
        "color": "#ffffff",
        "font-weight": "700",
        "box-shadow": "0 4px 12px rgba(37, 99, 235, 0.3)"
    },
}
