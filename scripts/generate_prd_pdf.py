#!/usr/bin/env python3
"""
Generates a sanitized, publication-grade executive PDF of the Grubhub Merchant PRD.
Converts Markdown to HTML with KaTeX math, Mermaid.js diagrams, and Grubhub brand styling,
then renders to PDF using headless Google Chrome.
"""

import re
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension

INPUT_MD = PROJECT_ROOT / "PRD_MERCHANT_MENU_IMAGE_PLATFORM.md"
OUTPUT_HTML = PROJECT_ROOT / "results" / "PRD_MERCHANT_MENU_IMAGE_PLATFORM.html"
OUTPUT_PDF = PROJECT_ROOT / "PRD_MERCHANT_MENU_IMAGE_PLATFORM.pdf"
RESULTS_PDF = PROJECT_ROOT / "results" / "PRD_MERCHANT_MENU_IMAGE_PLATFORM.pdf"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Product Requirements Document (PRD) — Grubhub Merchant Menu Image Platform</title>
  
  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  
  <!-- KaTeX Math -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
  
  <!-- Mermaid Diagrams -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  
  <style>
    :root {
      --gh-orange: #FF5500;
      --gh-orange-soft: rgba(255, 85, 0, 0.08);
      --gh-iris: #572AF8;
      --gh-iris-soft: rgba(87, 42, 248, 0.08);
      --ink: #111827;
      --ink-soft: #374151;
      --muted: #6B7280;
      --dim: #9CA3AF;
      --surface: #FFFFFF;
      --surface-subtle: #F8FAFC;
      --border: #E2E8F0;
      --border-dark: #CBD5E1;
      --pass: #059669;
      --pass-bg: #ECFDF5;
      --review: #D97706;
      --review-bg: #FFFBEB;
      --reject: #DC2626;
      --reject-bg: #FEF2F2;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 12.5px;
      line-height: 1.65;
      color: var(--ink);
      background: #FFFFFF;
      padding: 24px 36px;
      max-width: 1100px;
      margin: 0 auto;
      text-rendering: optimizeLegibility;
      -webkit-font-smoothing: antialiased;
    }

    /* Print & Page Setup */
    @page {
      size: letter;
      margin: 16mm 14mm 16mm 14mm;
    }

    @media print {
      body {
        padding: 0;
        max-width: 100%;
        font-size: 11.5px;
        line-height: 1.55;
      }
      
      .no-print { display: none !important; }
      
      h1, h2 {
        break-after: avoid;
        page-break-after: avoid;
      }
      
      h2 {
        break-before: auto;
      }
      
      table, pre, .mermaid-container, .alert, blockquote {
        break-inside: avoid;
        page-break-inside: avoid;
      }

      a {
        color: var(--ink) !important;
        text-decoration: none !important;
      }
    }

    /* Header Banner */
    .doc-header {
      border-bottom: 3px solid var(--gh-orange);
      padding-bottom: 20px;
      margin-bottom: 30px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .doc-badge-strip {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 10.5px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .badge-primary { background: var(--gh-orange); color: #FFF; }
    .badge-secondary { background: var(--gh-iris); color: #FFF; }
    .badge-outline { background: var(--surface-subtle); color: var(--ink-soft); border: 1px solid var(--border-dark); }

    .doc-title {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.15;
      color: #0F172A;
    }

    .doc-subtitle {
      font-size: 14.5px;
      font-weight: 500;
      color: var(--muted);
      line-height: 1.45;
    }

    .doc-meta-bar {
      display: flex;
      align-items: center;
      gap: 18px;
      font-size: 11px;
      color: var(--muted);
      margin-top: 4px;
      border-top: 1px solid var(--border);
      padding-top: 8px;
      flex-wrap: wrap;
    }

    .doc-meta-item strong {
      color: var(--ink);
    }

    /* Typography */
    h1 {
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.025em;
      color: #0F172A;
      margin-top: 32px;
      margin-bottom: 14px;
      padding-bottom: 6px;
      border-bottom: 2px solid var(--border);
    }

    h2 {
      font-size: 16.5px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #0F172A;
      margin-top: 28px;
      margin-bottom: 12px;
      padding-bottom: 6px;
      border-bottom: 1.5px solid var(--border);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    h2::before {
      content: '';
      display: inline-block;
      width: 4px;
      height: 16px;
      background: var(--gh-orange);
      border-radius: 2px;
    }

    h3 {
      font-size: 14px;
      font-weight: 700;
      letter-spacing: -0.015em;
      color: #1E293B;
      margin-top: 22px;
      margin-bottom: 8px;
    }

    h4 {
      font-size: 12.5px;
      font-weight: 700;
      color: #334155;
      margin-top: 16px;
      margin-bottom: 6px;
    }

    p {
      margin-bottom: 10px;
      text-wrap: pretty;
    }

    ul, ol {
      margin-bottom: 12px;
      padding-left: 20px;
    }

    li {
      margin-bottom: 4px;
    }

    strong {
      font-weight: 700;
      color: #0F172A;
    }

    hr {
      border: 0;
      height: 1px;
      background: var(--border);
      margin: 26px 0;
    }

    /* Images and Visual Plates */
    img {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 16px auto;
      border-radius: 8px;
      border: 1px solid var(--border);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.07);
      page-break-inside: avoid;
      break-inside: avoid;
    }

    /* Tables */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0 20px 0;
      font-size: 10.5px;
      line-height: 1.4;
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }

    th {
      background: #0F172A;
      color: #FFFFFF;
      font-weight: 700;
      text-align: left;
      padding: 8px 10px;
      font-size: 10.5px;
      letter-spacing: 0.02em;
      border: 1px solid #1E293B;
    }

    td {
      padding: 7px 10px;
      border: 1px solid var(--border);
      vertical-align: top;
    }

    tr:nth-child(even) {
      background: #F8FAFC;
    }

    tr:hover {
      background: #F1F5F9;
    }

    /* Code & Pre */
    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      background: #F1F5F9;
      color: #C2410C;
      padding: 2px 4px;
      border-radius: 4px;
      border: 1px solid #E2E8F0;
    }

    pre {
      background: #0F172A;
      color: #F8FAFC;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10.5px;
      line-height: 1.5;
      padding: 12px 14px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 12px 0 16px 0;
      border: 1px solid #1E293B;
    }

    pre code {
      background: transparent;
      color: inherit;
      padding: 0;
      border: none;
      font-size: inherit;
    }

    /* GitHub Alert Callout Boxes */
    .alert {
      border-left: 4px solid;
      padding: 10px 14px;
      border-radius: 6px;
      margin: 14px 0 18px 0;
      background: var(--surface-subtle);
    }

    .alert-note {
      border-color: #2563EB;
      background: #EFF6FF;
      color: #1E3A8A;
    }

    .alert-tip {
      border-color: var(--pass);
      background: var(--pass-bg);
      color: #064E3B;
    }

    .alert-important {
      border-color: var(--gh-iris);
      background: #F5F3FF;
      color: #4C1D95;
    }

    .alert-warning {
      border-color: #D97706;
      background: var(--review-bg);
      color: #78350F;
    }

    .alert-caution {
      border-color: var(--reject);
      background: var(--reject-bg);
      color: #7F1D1D;
    }

    .alert-title {
      font-weight: 700;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .alert-body p {
      margin-bottom: 0;
    }

    /* Mermaid Container */
    .mermaid-container {
      background: #FAFAFA;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px 12px;
      margin: 16px 0;
      display: flex;
      justify-content: center;
      overflow: hidden;
    }

    .mermaid {
      width: 100%;
      display: flex;
      justify-content: center;
    }

    .mermaid svg {
      max-width: 100% !important;
      height: auto !important;
    }

    /* Blockquotes */
    blockquote {
      border-left: 3px solid var(--gh-orange);
      padding: 6px 14px;
      background: var(--gh-orange-soft);
      margin: 12px 0;
      font-style: italic;
      color: #374151;
    }
  </style>
</head>
<body>

  <!-- Executive Document Banner -->
  <header class="doc-header">
    <div class="doc-badge-strip">
      <span class="badge badge-primary">GRUBHUB</span>
      <span class="badge badge-secondary">MERCHANT PLATFORM</span>
      <span class="badge badge-outline">GEMINI NANO BANANA 2.1 & GEMINI 3.8 FLASH</span>
      <span class="badge badge-outline">SANITIZED SPECIFICATION (v5.2)</span>
    </div>
    <div class="doc-title">Grubhub Merchant Menu Image Enhancement & Moderation Platform</div>
    <div class="doc-subtitle">Production Architecture on Google Cloud Powered by Gemini 3.8 Flash & Gemini Nano Banana 2.1</div>
    <div class="doc-meta-bar">
      <div class="doc-meta-item">Status: <strong>Production Reference Build (v5.2)</strong></div>
      <div class="doc-meta-item">Cloud Runtime: <strong>Google Cloud Run (us-central1)</strong></div>
      <div class="doc-meta-item">Storage: <strong>Google Cloud Storage</strong></div>
      <div class="doc-meta-item">Classification: <strong>Architecture & Product Requirements</strong></div>
    </div>
  </header>

  <!-- Main PRD Body -->
  <main class="doc-body">
<!-- BODY_HTML_PLACEHOLDER -->
  </main>

  <footer style="margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--border); font-size: 9.5px; color: var(--dim); display: flex; justify-content: space-between;">
    <div>Grubhub Inc. & Google Cloud AI • Confidential Product Requirements Document</div>
    <div>Powered by Google Cloud Vertex AI, Gemini 3.8 Flash & Gemini Nano Banana 2.1</div>
  </footer>

  <script>
    // Initialize KaTeX and Mermaid
    function initDiagramsAndMath() {
      if (window.renderMathInElement) {
        renderMathInElement(document.body, {
          delimiters: [
            {left: "$$", right: "$$", display: true},
            {left: "$", right: "$", display: false}
          ],
          ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
          throwOnError: false
        });
      }
      
      if (window.mermaid) {
        mermaid.initialize({
          startOnLoad: false,
          theme: 'neutral',
          securityLevel: 'loose',
          themeVariables: {
            primaryColor: '#F8FAFC',
            primaryTextColor: '#0F172A',
            primaryBorderColor: '#572AF8',
            lineColor: '#64748B',
            secondaryColor: '#EFF6FF',
            tertiaryColor: '#FEF3C7',
            fontFamily: 'Plus Jakarta Sans, sans-serif',
            fontSize: '11px'
          },
          flowchart: {
            curve: 'basis',
            useMaxWidth: true,
            htmlLabels: true
          }
        });
        mermaid.run();
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener("DOMContentLoaded", initDiagramsAndMath);
    } else {
      initDiagramsAndMath();
    }
    window.addEventListener("load", initDiagramsAndMath);
  </script>
</body>
</html>
"""

def preprocess_markdown(text: str, mermaid_blocks: list) -> str:
    """Preprocesses raw markdown for Mermaid blocks, GitHub alerts, and clean formatting."""
    # Stash Mermaid code blocks with placeholders
    def stash_mermaid(match):
        idx = len(mermaid_blocks)
        diagram_code = match.group(1).strip()
        mermaid_blocks.append(diagram_code)
        return f'\n\n<!-- MERMAID_STASH_BLOCK_{idx} -->\n\n'

    text = re.sub(r'```mermaid\s*\n(.*?)\n```', stash_mermaid, text, flags=re.DOTALL)

    # Convert GitHub alerts: > [!NOTE], > [!TIP], > [!IMPORTANT], > [!WARNING], > [!CAUTION]
    def replace_alert(match):
        alert_type = match.group(1).upper()
        content = match.group(2).strip()
        icon_map = {
            "NOTE": ("ℹ️", "NOTE", "alert-note"),
            "TIP": ("💡", "TIP", "alert-tip"),
            "IMPORTANT": ("📌", "IMPORTANT", "alert-important"),
            "WARNING": ("⚠️", "WARNING", "alert-warning"),
            "CAUTION": ("🛑", "CAUTION", "alert-caution")
        }
        icon, label, css_class = icon_map.get(alert_type, ("ℹ️", alert_type, "alert-note"))
        # Strip leading "> " from each line of content
        cleaned_content = "\n".join(re.sub(r'^\s*>\s?', '', line) for line in content.split('\n'))
        return f'<div class="alert {css_class}"><div class="alert-title"><span class="alert-icon">{icon}</span> {label}</div><div class="alert-body">{cleaned_content}</div></div>'

    alert_pattern = r'^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:^\s*>[^\n]*\n?)+)'
    text = re.sub(alert_pattern, replace_alert, text, flags=re.IGNORECASE | re.MULTILINE)

    return text

def main():
    print(f"Reading markdown from: {INPUT_MD}")
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        raw_md = f.read()

    # Preprocess markdown
    print("Preprocessing markdown for Mermaid diagrams and GitHub alerts...")
    mermaid_blocks = []
    preprocessed_md = preprocess_markdown(raw_md, mermaid_blocks)

    # Convert markdown to HTML
    print("Converting markdown to HTML...")
    md_converter = markdown.Markdown(
        extensions=[
            TableExtension(),
            FencedCodeExtension(),
            CodeHiliteExtension(guess_lang=False, css_class="highlight"),
            TocExtension(permalink=False),
            'attr_list',
            'def_list'
        ]
    )
    body_html = md_converter.convert(preprocessed_md)

    # Restore Mermaid blocks into clean <pre class="mermaid"> containers
    for idx, code in enumerate(mermaid_blocks):
        replacement = f'<div class="mermaid-container"><pre class="mermaid">\n{code}\n</pre></div>'
        body_html = body_html.replace(f'<!-- MERMAID_STASH_BLOCK_{idx} -->', replacement)

    # Insert into template
    full_html = HTML_TEMPLATE.replace("<!-- BODY_HTML_PLACEHOLDER -->", body_html)

    # Inline local images as base64 for reliable Chrome print rendering
    import base64
    def embed_images_as_base64(html_str):
        def repl(m):
            src = m.group(1)
            if src.startswith("data:") or src.startswith("http://") or src.startswith("https://"):
                return m.group(0)
            target = (PROJECT_ROOT / src).resolve()
            if target.exists():
                ext = target.suffix.lower().replace(".", "")
                mime = "image/png" if ext == "png" else ("image/jpeg" if ext in ["jpg", "jpeg"] else "image/svg+xml")
                with open(target, "rb") as img_f:
                    b64 = base64.b64encode(img_f.read()).decode("utf-8")
                return f'src="data:{mime};base64,{b64}"'
            return m.group(0)
        return re.sub(r'src="([^"]+)"', repl, html_str)

    print("Embedding visual plate images as base64 data URIs...")
    full_html = embed_images_as_base64(full_html)

    # Save HTML output
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Saved styled HTML to: {OUTPUT_HTML}")

    # Render to PDF using Google Chrome Headless
    print("Rendering HTML to PDF via headless Google Chrome...")
    chrome_cmd = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--virtual-time-budget=10000",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUTPUT_PDF}",
        f"file://{OUTPUT_HTML.resolve()}"
    ]

    res = subprocess.run(chrome_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Error rendering PDF: {res.stderr}")
        sys.exit(1)

    # Copy to results directory as well
    if OUTPUT_PDF.exists():
        import shutil
        shutil.copy(OUTPUT_PDF, RESULTS_PDF)
        pdf_size_kb = round(OUTPUT_PDF.stat().st_size / 1024, 1)
        print(f"✅ Successfully generated PDF: {OUTPUT_PDF} ({pdf_size_kb} KB)")
        print(f"✅ Mirrored to: {RESULTS_PDF}")
    else:
        print("❌ PDF file was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
