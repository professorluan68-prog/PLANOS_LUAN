#!/usr/bin/env python3
"""
Baixa em lote os PDFs do Centro de Midias usando uma aba do Edge ja aberta.

Use primeiro o arquivo ABRIR_PORTAL_CENTRO_MIDIAS.bat. Depois de entrar no portal
e chegar na lista de aulas, execute BAIXAR_PDFS_CENTRO_MIDIAS.bat.
"""

from __future__ import annotations

import base64
import logging
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORTA_EDGE = 9222
SITE_BASE = "https://repositorio.educacao.sp.gov.br/midia"
PASTA_DOWNLOAD_PADRAO = Path.home() / "Downloads" / "PDFs_CentroMidias"


JS_COLETAR_PDFS = r"""
() => {
  const out = [];
  const seen = new Set();

  function clean(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
  }

  function push(url, title, source) {
    url = clean(url);
    if (!url || seen.has(url)) return;
    seen.add(url);
    out.push({ href: url, titulo: clean(title), origem: source || "" });
  }

  function cardTitle(el) {
    const card = el.closest(".card, .panel, .box, li, article, section, tr, div");
    if (!card) return clean(el.textContent);
    const titleEl = card.querySelector("h1,h2,h3,h4,h5,.title,strong,b");
    const text = clean(titleEl ? titleEl.textContent : card.textContent);
    const match = text.match(/Aula\s+\d+[^]*?(?=(Arquivo|Localizador|Avaliar|PDF|PPTX|$))/i);
    return clean(match ? match[0] : text);
  }

  for (const a of Array.from(document.querySelectorAll("a[href]"))) {
    const href = a.getAttribute("href") || "";
    const label = clean(a.textContent);
    if (/\.pdf($|[?#])/i.test(href) || /^pdf$/i.test(label)) {
      push(href, cardTitle(a), "a[href]");
    }
  }

  for (const el of Array.from(document.querySelectorAll("[onclick], [data-url], [data-href], [href]"))) {
    const attrs = [
      el.getAttribute("onclick"),
      el.getAttribute("data-url"),
      el.getAttribute("data-href"),
      el.getAttribute("href"),
    ].filter(Boolean);
    const text = clean(el.textContent);
    for (const attr of attrs) {
      const pdfs = String(attr).match(/https?:\/\/[^'")\s]+\.pdf(?:[?#][^'")\s]+)?|\/[^'")\s]+\.pdf(?:[?#][^'")\s]+)?/gi) || [];
      for (const pdf of pdfs) push(pdf, cardTitle(el), "attribute");
      if (/pdf/i.test(text + " " + attr)) {
        const ids = String(attr).match(/\b\d{5,}\b/g) || [];
        for (const id of ids) {
          push(`/midia/Download?codigo=${id}&tipo=PDF`, cardTitle(el), "id-guess");
        }
      }
    }
  }

  return out;
}
"""


def _slug(texto: str) -> str:
    """Converte texto em slug seguro para nome de arquivo."""
    texto = (texto or "").strip().lower()
    texto = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE)
    texto = re.sub(r"[\s_-]+", "_", texto)
    return texto.strip("_") or "arquivo"


def _nome_pdf(url: str, titulo: str, ordem: int) -> str:
    """Gera nome seguro para arquivo PDF."""
    nome_original = Path(unquote(urlparse(url).path)).name
    if nome_original.lower().endswith(".pdf") and len(nome_original) > 4:
        return f"{ordem:02d}_{_slug(nome_original[:-4])}.pdf"
    return f"{ordem:02d}_{_slug(titulo)}.pdf"


def _escolher_pagina(browser):
    """Escolhe a página mais apropriada do navegador para download."""
    paginas = []
    for contexto in browser.contexts:
        paginas.extend(contexto.pages)

    candidatas = [
        page for page in paginas
        if "repositorio.educacao.sp.gov.br" in (page.url or "")
    ]
    if candidatas:
        return candidatas[-1]
    return paginas[-1] if paginas else None


def _conteudo_pdf_por_url(request_context, url: str) -> bytes:
    """Baixa conteúdo PDF por URL com validação."""
    try:
        resp = request_context.get(url, timeout=60000)
        content_type = (resp.headers.get("content-type") or "").lower()
        body = resp.body()
        
        if not resp.ok or (b"%PDF" not in body[:20] and "pdf" not in content_type):
            raise RuntimeError(f"HTTP {resp.status} / {content_type}")
        
        return body
    except Exception as e:
        logger.error(f"Erro ao baixar PDF de {url}: {e}")
        raise


def _conteudo_pdf_por_blob(pdf_page) -> bytes:
    """Extrai conteúdo PDF de blob da página."""
    try:
        data_b64 = pdf_page.evaluate(
            """
            async () => {
              const resp = await fetch(location.href);
              const blob = await resp.blob();
              return await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
                reader.onerror = reject;
                reader.readAsDataURL(blob);
              });
            }
            """
        )
        body = base64.b64decode(data_b64)
        if b"%PDF" not in body[:20]:
            raise RuntimeError("conteudo blob nao parece PDF")
        return body
    except Exception as e:
        logger.error(f"Erro ao extrair PDF de blob: {e}")
        raise


def _urls_pdf_da_aba(pdf_page) -> list[str]:
    """Coleta todas as URLs de PDF visíveis na página."""
    urls = [pdf_page.url]
    urls.extend(
        pdf_page.evaluate(
            """
            () => Array.from(document.querySelectorAll("embed[src], iframe[src], object[data], a[href]"))
              .map(el => el.getAttribute("src") || el.getAttribute("data") || el.getAttribute("href") || "")
              .filter(Boolean)
            """
        )
    )
    saida = []
    vistos = set()
    for url in urls:
        url = urljoin(pdf_page.url, str(url or "").strip())
        if url and url not in vistos:
            vistos.add(url)
            saida.append(url)
    return saida


def _salvar_pdf_de_aba(pdf_page, request_context, destino: Path) -> None:
    """Salva PDF aberto em aba do navegador."""
    pdf_page.wait_for_load_state("domcontentloaded", timeout=20000)
    pdf_page.wait_for_timeout(1000)

    for url in _urls_pdf_da_aba(pdf_page):
        if url.startswith("blob:"):
            destino.write_bytes(_conteudo_pdf_por_blob(pdf_page))
            return
        if url.startswith("http"):
            try:
                destino.write_bytes(_conteudo_pdf_por_url(request_context, url))
                return
            except Exception as e:
                logger.warning(f"Falha ao baixar de {url}: {e}")
                continue

    raise RuntimeError("nao consegui extrair o PDF da aba aberta")


def _baixar_por_cliques(page, pasta_destino: Path) -> tuple[int, int]:
    """Modo alternativo de download: clica em botões PDF."""
    botoes_pdf = page.get_by_text(re.compile(r"^\s*PDF\s*$", re.I))
    total = botoes_pdf.count()
    if total == 0:
        return 0, 0

    logger.info(f"Tentando modo alternativo por clique em {total} botao(oes) PDF...")
    baixados = 0
    falhas = 0
    contexto = page.context
    request_context = contexto.request

    for i in range(total):
        botao = botoes_pdf.nth(i)
        try:
            titulo = botao.evaluate(
                """
                (el) => {
                  const card = el.closest(".card, .panel, .box, li, article, section, tr, div");
                  const text = (card ? card.textContent : el.textContent || "").replace(/\\s+/g, " ").trim();
                  const match = text.match(/Aula\\s+\\d+.*?(?=(Arquivo|Localizador|Avaliar|PDF|PPTX|$))/i);
                  return (match ? match[0] : text || "aula").trim();
                }
                """
            )
            nome = f"{i + 1:02d}_{_slug(titulo)}.pdf"
            destino = pasta_destino / nome
            botao.scroll_into_view_if_needed(timeout=10000)
            try:
                with contexto.expect_page(timeout=8000) as nova_aba_info:
                    botao.click(timeout=15000)
                nova_aba = nova_aba_info.value
                _salvar_pdf_de_aba(nova_aba, request_context, destino)
                nova_aba.close()
            except Exception:
                with page.expect_download(timeout=30000) as download_info:
                    botao.click(timeout=15000)
                download_info.value.save_as(str(destino))
            baixados += 1
            logger.info(f"[OK] {nome}")
        except Exception as exc:
            falhas += 1
            logger.error(f"[FALHA] clique PDF {i + 1} ({exc})")

    return baixados, falhas


def main() -> int:
    """Função principal para baixar PDFs."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright nao encontrado. Rode: python -m pip install playwright")
        return 1

    pasta_destino = PASTA_DOWNLOAD_PADRAO
    pasta_destino.mkdir(parents=True, exist_ok=True)

    logger.info("\n=== BAIXADOR DE PDFs - CENTRO DE MIDIAS ===")
    logger.info("Este modo conecta no Edge que voce ja abriu pelo atalho do portal.")
    logger.info(f"Pasta de destino: {pasta_destino}")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA_EDGE}")
        except Exception as e:
            logger.error(f"Erro ao conectar no Edge: {e}")
            logger.error("Nao consegui encontrar o Edge preparado para download.")
            logger.error("Abra primeiro o arquivo ABRIR_PORTAL_CENTRO_MIDIAS.bat, entre no portal e tente de novo.")
            return 1

        page = _escolher_pagina(browser)
        if page is None:
            logger.error("Nao encontrei nenhuma aba aberta no Edge.")
            browser.close()
            return 1

        page.bring_to_front()
        logger.info(f"\nAba encontrada:\n{page.url}")
        if "sso.acesso.gov.br" in page.url:
            logger.warning("\nVoce ainda esta na tela do gov.br.")
            logger.warning("Termine o login, abra a lista de aulas do repositorio e rode este baixador de novo.")
            browser.close()
            return 1

        input("\nCom a lista de aulas aberta nessa aba, pressione ENTER para baixar...")

        itens = page.evaluate(JS_COLETAR_PDFS)
        urls_unicas = []
        vistos = set()
        for item in itens or []:
            href = str(item.get("href") or "").strip()
            if not href:
                continue
            url = urljoin(page.url or SITE_BASE, href)
            if url in vistos:
                continue
            vistos.add(url)
            urls_unicas.append({
                "url": url,
                "titulo": str(item.get("titulo") or "aula").strip(),
            })

        if not urls_unicas:
            logger.warning("\nNao encontrei links PDF visiveis nessa pagina.")
            baixados, falhas = _baixar_por_cliques(page, pasta_destino)
            if baixados or falhas:
                logger.info("\n=== FINALIZADO ===")
                logger.info(f"Baixados: {baixados}")
                logger.info(f"Falhas:   {falhas}")
                logger.info(f"Pasta:    {pasta_destino}")
                browser.close()
                return 0 if baixados else 1
            logger.warning("Deixe a lista de aulas aberta, com os botoes PDF aparecendo, e tente novamente.")
            browser.close()
            return 1

        logger.info(f"\nEncontrei {len(urls_unicas)} PDF(s). Baixando...")

        baixados = 0
        falhas = 0
        request_context = browser.contexts[0].request

        for i, item in enumerate(urls_unicas, start=1):
            url = item["url"]
            nome = _nome_pdf(url, item["titulo"], i)
            destino = pasta_destino / nome
            try:
                destino.write_bytes(_conteudo_pdf_por_url(request_context, url))
                baixados += 1
                logger.info(f"[OK] {nome}")
            except Exception as exc:
                falhas += 1
                logger.error(f"[FALHA] {nome} ({exc})")

        if baixados == 0:
            logger.warning("\nOs links encontrados nao eram PDFs baixaveis direto.")
            baixados, falhas = _baixar_por_cliques(page, pasta_destino)

        logger.info("\n=== FINALIZADO ===")
        logger.info(f"Baixados: {baixados}")
        logger.info(f"Falhas:   {falhas}")
        logger.info(f"Pasta:    {pasta_destino}")
        browser.close()

    return 0 if (baixados > 0 or falhas == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
