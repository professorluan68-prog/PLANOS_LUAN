import os
import re

base_dir = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN'
dados_dir = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN_DADOS'

guia_path = os.path.join(dados_dir, "Guia de Redesign UI — PLANOS LUAN.md")
with open(guia_path, 'r', encoding='utf-8') as f:
    guia = f.read()

def extrair_bloco(padrao):
    match = re.search(padrao, guia, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

print("Iniciando aplicação do Redesign v2.0...")

# 1. assets/style.css
css = extrair_bloco(r"```css\n(.*?)```")
os.makedirs(os.path.join(base_dir, "assets"), exist_ok=True)
with open(os.path.join(base_dir, "assets", "style.css"), 'w', encoding='utf-8') as f:
    f.write(css)
print("✅ assets/style.css")

# 2. ui/design_tokens.py
tokens = extrair_bloco(r"```python\n# ui/design_tokens.py\n(.*?)```")
with open(os.path.join(base_dir, "ui", "design_tokens.py"), 'w', encoding='utf-8') as f:
    f.write("# ui/design_tokens.py\n" + tokens)
print("✅ ui/design_tokens.py")

# 3. ui/components_html.py
html_comp = extrair_bloco(r"```python\n# ui/components_html.py\n(.*?)```")
with open(os.path.join(base_dir, "ui", "components_html.py"), 'w', encoding='utf-8') as f:
    f.write("# ui/components_html.py\n" + html_comp)
print("✅ ui/components_html.py")

# 4. ui/tela_inicial_moderna.py
tela_inic = extrair_bloco(r"```python\n# ui/tela_inicial_moderna.py\n(.*?)```")
with open(os.path.join(base_dir, "ui", "tela_inicial_moderna.py"), 'w', encoding='utf-8') as f:
    f.write("# ui/tela_inicial_moderna.py\n" + tela_inic)
print("✅ ui/tela_inicial_moderna.py")

# 5. .streamlit/config.toml
toml = extrair_bloco(r"```toml\n(.*?)```")
os.makedirs(os.path.join(base_dir, ".streamlit"), exist_ok=True)
with open(os.path.join(base_dir, ".streamlit", "config.toml"), 'w', encoding='utf-8') as f:
    f.write(toml)
print("✅ .streamlit/config.toml")

# 6. Atualizar render_sidebar em ui/ui_components.py
ui_comp_path = os.path.join(base_dir, "ui", "ui_components.py")
if os.path.exists(ui_comp_path):
    with open(ui_comp_path, 'r', encoding='utf-8') as f:
        content_ui_comp = f.read()
    nova_sidebar = extrair_bloco(r"```python\n(def render_sidebar.*?)\n```")
    # substituir a antiga função pela nova
    content_ui_comp = re.sub(r'def render_sidebar.*?$', nova_sidebar, content_ui_comp, flags=re.DOTALL | re.MULTILINE)
    with open(ui_comp_path, 'w', encoding='utf-8') as f:
        f.write(content_ui_comp)
    print("✅ ui/ui_components.py (render_sidebar)")

# 7. Atualizar option_menu em planos_luan_app.py
app_path = os.path.join(base_dir, "planos_luan_app.py")
if os.path.exists(app_path):
    with open(app_path, 'r', encoding='utf-8') as f:
        content_app = f.read()
    
    # Extrair novo menu do guia (a partir de modo_tela = option_menu ate a chave key="menu_principal",))
    novo_menu = extrair_bloco(r"```python\n# Substituir a chamada atual do option_menu por:\nfrom streamlit_option_menu import option_menu\n\n(modo_tela = option_menu.*?key=\"menu_principal\",\n\))\n```")
    
    if novo_menu:
        # Tentar substituir o menu existente em planos_luan_app.py
        # Vamos assumir que a variável modo_tela = option_menu(...) está lá.
        content_app = re.sub(r'modo_tela\s*=\s*option_menu\s*\(.*?\)', novo_menu, content_app, flags=re.DOTALL)
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(content_app)
        print("✅ planos_luan_app.py (option_menu)")

print("\n🎉 Redesign aplicado com sucesso! Inicie o aplicativo para ver o novo layout.")
