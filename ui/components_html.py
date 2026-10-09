# ui/components_html.py
"""
Biblioteca de componentes HTML reutilizáveis para o design system v2.0.
Uso: st.markdown(card_secao(...), unsafe_allow_html=True)
"""

def hero_section(
    titulo: str = "Planos de Aula",
    subtitulo: str = "Geração automatizada de planejamento escolar com IA",
    stats: list[dict] | None = None,
    features: list[str] | None = None,
) -> str:
    """
    Renderiza o hero da tela inicial.
    stats: [{"valor": "23", "label": "Disciplinas"}, ...]
    features: ["📘 Leitura de PDFs", "📎 Processamento em lote", ...]
    """
    stats = stats or []
    features = features or []

    stats_html = "".join(
        f"""<div class="stat-item">
              <span class="stat-value">{s['valor']}</span>
              <span class="stat-label">{s['label']}</span>
            </div>"""
        for s in stats
    )

    features_html = "".join(
        f'<div class="feature-pill">{f}</div>'
        for f in features
    )

    return f"""
    <div class="hero-container animate-fade-in-up">
        <div class="hero-badge">
            <span class="status-dot green"></span>
            SISTEMA ATIVO — SEDUC
        </div>
        <div class="hero-title">{titulo}</div>
        <div class="hero-subtitle">{subtitulo}</div>
        <div class="feature-pills">{features_html}</div>
        <div class="stats-grid">{stats_html}</div>
    </div>
    """


def card_secao(
    titulo: str,
    subtitulo: str = "",
    icone: str = "📋",
    cor: str = "blue",
    conteudo_html: str = "",
    status: str = "",          # "success" | "warning" | "ai" | ""
) -> str:
    """
    Card de seção com cabeçalho colorido e conteúdo livre.
    cor: "blue" | "purple" | "green" | "amber" | "red"
    """
    classe_card = f"card card-{status}" if status else "card"
    subtitulo_html = f'<div class="card-subtitle">{subtitulo}</div>' if subtitulo else ""
    return f"""
    <div class="{classe_card} animate-fade-in-up">
        <div class="card-header">
            <div class="card-icon {cor}">{icone}</div>
            <div>
                <div class="card-title">{titulo}</div>
                {subtitulo_html}
            </div>
        </div>
        {conteudo_html}
    </div>
    """


def badge(texto: str, cor: str = "blue", icone: str = "") -> str:
    """
    Badge/chip colorido.
    cor: "blue" | "green" | "amber" | "red" | "purple"
    """
    icone_html = f"{icone} " if icone else ""
    return f'<span class="badge badge-{cor}">{icone_html}{texto}</span>'


def status_bar(
    label: str,
    valor: str,
    cor: str = "blue",
    icone: str = "●",
) -> str:
    """Linha de status com indicador colorido."""
    cores_map = {
        "blue":   "#3B82F6",
        "green":  "#10B981",
        "amber":  "#F59E0B",
        "red":    "#EF4444",
        "purple": "#8B5CF6",
    }
    cor_hex = cores_map.get(cor, "#3B82F6")
    return f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
                padding:10px 14px; background:#112952; border-radius:10px;
                border:1px solid #1A3A6B; margin-bottom:6px;">
        <span style="font-size:0.8rem; color:#9CA3AF; font-weight:500;">{label}</span>
        <span style="font-size:0.85rem; color:{cor_hex}; font-weight:600;">{icone} {valor}</span>
    </div>
    """


def step_indicator(
    numero: int,
    titulo: str,
    descricao: str = "",
    concluido: bool = False,
) -> str:
    """Indicador de passo numerado."""
    classe = "step-number completed" if concluido else "step-number"
    icone = "✓" if concluido else str(numero)
    desc_html = f'<div class="step-desc">{descricao}</div>' if descricao else ""
    return f"""
    <div class="step-container">
        <div class="{classe}">{icone}</div>
        <div class="step-content">
            <div class="step-title">{titulo}</div>
            {desc_html}
        </div>
    </div>
    """


def divider(texto: str = "") -> str:
    """Divisor horizontal com texto opcional."""
    if texto:
        return f"""
        <div style="display:flex; align-items:center; gap:12px; margin:20px 0;">
            <div style="flex:1; height:1px; background:linear-gradient(90deg,transparent,#1A3A6B);"></div>
            <span style="font-size:0.7rem; color:#4B5563; font-weight:600;
                         text-transform:uppercase; letter-spacing:0.1em;">{texto}</span>
            <div style="flex:1; height:1px; background:linear-gradient(90deg,#1A3A6B,transparent);"></div>
        </div>
        """
    return '<hr style="border:none;height:1px;background:linear-gradient(90deg,transparent,#1A3A6B,transparent);margin:20px 0;">'


def alerta_customizado(
    mensagem: str,
    tipo: str = "info",   # "success" | "warning" | "error" | "info" | "ai"
    icone: str = "",
    titulo: str = "",
) -> str:
    """Alerta customizado com mais personalidade que st.info/success/error."""
    config = {
        "success": {"bg": "rgba(5,150,105,0.1)",  "border": "#10B981", "cor": "#D1FAE5", "icone_pad": "✅"},
        "warning": {"bg": "rgba(217,119,6,0.1)",  "border": "#F59E0B", "cor": "#FEF3C7", "icone_pad": "⚠️"},
        "error":   {"bg": "rgba(220,38,38,0.1)",  "border": "#EF4444", "cor": "#FEE2E2", "icone_pad": "❌"},
        "info":    {"bg": "rgba(37,99,235,0.1)",  "border": "#3B82F6", "cor": "#DBEAFE", "icone_pad": "ℹ️"},
        "ai":      {"bg": "rgba(124,58,237,0.1)", "border": "#8B5CF6", "cor": "#EDE9FE", "icone_pad": "🤖"},
    }
    c = config.get(tipo, config["info"])
    icone_final = icone or c["icone_pad"]
    titulo_html = f'<div style="font-weight:700;margin-bottom:4px;">{titulo}</div>' if titulo else ""
    return f"""
    <div style="background:{c['bg']}; border:1px solid {c['border']}; border-left:4px solid {c['border']};
                border-radius:12px; padding:14px 18px; margin:8px 0; color:{c['cor']}; font-size:0.875rem;">
        <div style="display:flex; gap:10px; align-items:flex-start;">
            <span style="font-size:1.1rem; flex-shrink:0;">{icone_final}</span>
            <div>
                {titulo_html}
                {mensagem}
            </div>
        </div>
    </div>
    """


def kpi_row(items: list[dict]) -> str:
    """
    Linha de KPIs coloridos.
    items: [{"valor": "12", "label": "Última aula", "cor": "#3B82F6", "icone": "📚"}, ...]
    """
    cards = []
    for item in items:
        cor = item.get("cor", "#3B82F6")
        cards.append(f"""
        <div style="flex:1; background:linear-gradient(145deg,#0D1F3C,#112952);
                    border:1px solid #1A3A6B; border-top:3px solid {cor};
                    border-radius:12px; padding:16px; text-align:center;
                    transition:all 0.3s ease; min-width:100px;">
            <div style="font-size:1.5rem; margin-bottom:4px;">{item.get('icone','')}</div>
            <div style="font-size:1.5rem; font-weight:800; color:{cor};">{item['valor']}</div>
            <div style="font-size:0.7rem; color:#9CA3AF; font-weight:500;
                        text-transform:uppercase; letter-spacing:0.06em; margin-top:4px;">
                {item['label']}
            </div>
        </div>
        """)
    return f"""
    <div style="display:flex; gap:12px; margin:16px 0; flex-wrap:wrap;">
        {''.join(cards)}
    </div>
    """


def sidebar_logo() -> str:
    """Logo e identidade visual da sidebar."""
    return """
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">📚</div>
        <div class="sidebar-logo-text">
            <div class="sidebar-logo-title">Planos Luan</div>
            <div class="sidebar-logo-subtitle">SEDUC · v1.2.14</div>
        </div>
    </div>
    """


def sidebar_section(label: str) -> str:
    """Rótulo de seção na sidebar."""
    return f'<div class="sidebar-section-label">{label}</div>'


def botao_cta_html(texto: str, icone: str = "🚀") -> str:
    """
    HTML de botão CTA grande (usar com st.markdown + JS ou substituir st.button).
    NOTA: Para ação real, usar st.button() com CSS aplicado via classe.
    Este HTML é apenas para exibição visual — o clique real deve ser via st.button().
    """
    return f"""
    <div style="background:linear-gradient(135deg,#1E4D8C,#2563EB,#7C3AED);
                border-radius:14px; padding:16px 32px; text-align:center;
                font-size:1rem; font-weight:700; color:#FFFFFF; cursor:pointer;
                box-shadow:0 6px 24px rgba(37,99,235,0.4); margin:16px 0;
                letter-spacing:0.03em; transition:all 0.3s ease;">
        {icone} {texto}
    </div>
    """


def progress_steps(
    passos: list[str],
    atual: int = 0,
) -> str:
    """
    Indicador de progresso em passos horizontais.
    atual: índice do passo atual (0-based)
    """
    items = []
    for i, passo in enumerate(passos):
        if i < atual:
            cor = "#10B981"; bg = "rgba(5,150,105,0.15)"; icone = "✓"
        elif i == atual:
            cor = "#3B82F6"; bg = "rgba(37,99,235,0.15)"; icone = str(i+1)
        else:
            cor = "#4B5563"; bg = "rgba(75,85,99,0.1)"; icone = str(i+1)

        items.append(f"""
        <div style="display:flex; flex-direction:column; align-items:center; gap:6px; flex:1;">
            <div style="width:32px; height:32px; border-radius:50%; background:{bg};
                        border:2px solid {cor}; color:{cor}; font-size:0.8rem; font-weight:700;
                        display:flex; align-items:center; justify-content:center;">
                {icone}
            </div>
            <span style="font-size:0.65rem; color:{cor}; font-weight:600;
                         text-align:center; text-transform:uppercase; letter-spacing:0.05em;">
                {passo}
            </span>
        </div>
        """)

    conectores = []
    for i in range(len(passos) - 1):
        cor_linha = "#10B981" if i < atual - 1 else ("#3B82F6" if i == atual - 1 else "#1A3A6B")
        conectores.append(f"""
        <div style="flex:1; height:2px; background:{cor_linha};
                    margin-top:15px; border-radius:1px;"></div>
        """)

    # Intercalar items e conectores
    elementos = []
    for i, item in enumerate(items):
        elementos.append(item)
        if i < len(conectores):
            elementos.append(conectores[i])

    return f"""
    <div style="display:flex; align-items:flex-start; gap:0; padding:16px 0; margin-bottom:8px;">
        {''.join(elementos)}
    </div>
    """