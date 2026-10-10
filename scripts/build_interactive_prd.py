#!/usr/bin/env python3
"""
Builds the Full Interactive PRD Portal with embedded interactive system diagrams,
all PRD functional sections, interactive Likert calculator, prompt/schema viewers,
and instant search.
"""

import os
import sys
import re
import json
import html
import base64
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension

MD_PATH = PROJECT_ROOT / "PRD_MERCHANT_MENU_IMAGE_PLATFORM.md"
OUTPUT_HTML = PROJECT_ROOT / "interactive_prd" / "index.html"
RESULTS_HTML = PROJECT_ROOT / "results" / "PRD_INTERACTIVE_PLATFORM.html"

# Encode diagram plates as Base64 data URIs for resilient, offline-ready rendering
def get_b64_img(rel_path):
    p = PROJECT_ROOT / rel_path
    if p.exists():
        ext = p.suffix.lower().replace(".", "")
        mime = "image/png" if ext == "png" else "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('utf-8')}"
    return rel_path

ARCH_PLATE_B64 = get_b64_img("assets/diagram_plates/architecture_plate.png")
DATAFLOW_PLATE_B64 = get_b64_img("assets/diagram_plates/dataflow_plate.png")
SEQUENCE_PLATE_B64 = get_b64_img("assets/diagram_plates/sequence_plate.png")

# Load diagram JSONs and HTMLs
ARCH_JSON = (PROJECT_ROOT / "interactive_prd" / "diagrams" / "architecture.json").read_text()
DATAFLOW_JSON = (PROJECT_ROOT / "interactive_prd" / "diagrams" / "ingestion_dataflow.json").read_text()
SEQUENCE_JSON = (PROJECT_ROOT / "interactive_prd" / "diagrams" / "merchant_sequence.json").read_text()

ARCH_HTML = (PROJECT_ROOT / "interactive_prd" / "diagrams" / "architecture.html").read_text()
DATAFLOW_HTML = (PROJECT_ROOT / "interactive_prd" / "diagrams" / "ingestion_dataflow.html").read_text()
SEQUENCE_HTML = (PROJECT_ROOT / "interactive_prd" / "diagrams" / "merchant_sequence.html").read_text()

# Read Markdown
raw_md = MD_PATH.read_text(encoding="utf-8")

# Convert GitHub alerts (including indented callouts)
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
    cleaned_content = "\n".join(re.sub(r'^\s*>\s?', '', line) for line in content.split('\n'))
    return f'<div class="alert {css_class}"><div class="alert-title"><span class="alert-icon">{icon}</span> {label}</div><div class="alert-body">{cleaned_content}</div></div>'

alert_pattern = r'^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:^\s*>[^\n]*\n?)+)'
processed_md = re.sub(alert_pattern, replace_alert, raw_md, flags=re.IGNORECASE | re.MULTILINE)

# Extract and stash Mermaid code blocks to protect them from Markdown entity-encoding
mermaid_blocks = []
def stash_mermaid(match):
    idx = len(mermaid_blocks)
    diagram_code = match.group(1).strip()
    mermaid_blocks.append(diagram_code)
    return f"\n\n<!-- MERMAID_STASH_BLOCK_{idx} -->\n\n"

mermaid_pattern = r'```mermaid\s*\n([\s\S]*?)\n```'
processed_md = re.sub(mermaid_pattern, stash_mermaid, processed_md)

# Convert Markdown to HTML
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
body_html = md_converter.convert(processed_md)

# Restore Mermaid blocks into clean <pre class="mermaid"> containers
for idx, code in enumerate(mermaid_blocks):
    replacement = f'<div class="mermaid-container"><pre class="mermaid">\n{code}\n</pre></div>'
    body_html = body_html.replace(f'<!-- MERMAID_STASH_BLOCK_{idx} -->', replacement)

# Replace relative plate image sources with Base64 data URIs
body_html = body_html.replace('src="assets/diagram_plates/architecture_plate.png"', f'src="{ARCH_PLATE_B64}"')
body_html = body_html.replace('src="assets/diagram_plates/dataflow_plate.png"', f'src="{DATAFLOW_PLATE_B64}"')
body_html = body_html.replace('src="assets/diagram_plates/sequence_plate.png"', f'src="{SEQUENCE_PLATE_B64}"')

# Safe JSON serializer that prevents HTML parser breakages inside <script> tags
def safe_js_str(s: str) -> str:
    return json.dumps(s).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

PORTAL_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>Grubhub Merchant Menu Image Platform — Interactive PRD & Architecture Portal (v5.2 • Gemini Nano Banana 2.1)</title>
  
  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  
  <!-- Mermaid & KaTeX -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
  
  <style>
    :root {{
      --gh-orange: #FF5500;
      --gh-orange-hover: #E04B00;
      --gh-orange-soft: rgba(255, 85, 0, 0.08);
      --gh-iris: #572AF8;
      --gh-iris-soft: rgba(87, 42, 248, 0.08);
      --bg-page: #F8FAFC;
      --bg-card: #FFFFFF;
      --bg-sidebar: #0F172A;
      --ink: #0F172A;
      --ink-soft: #334155;
      --muted: #64748B;
      --dim: #94A3B8;
      --border: #E2E8F0;
      --border-dark: #CBD5E1;
      --pass: #10B981;
      --pass-bg: #ECFDF5;
      --review: #F59E0B;
      --review-bg: #FFFBEB;
      --reject: #EF4444;
      --reject-bg: #FEF2F2;
      --font-body: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    body.dark-mode {{
      --bg-page: #0B0F19;
      --bg-card: #151D2F;
      --bg-sidebar: #070A12;
      --ink: #F1F5F9;
      --ink-soft: #CBD5E1;
      --muted: #94A3B8;
      --dim: #64748B;
      --border: #243048;
      --border-dark: #334155;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: var(--font-body);
      background: var(--bg-page);
      color: var(--ink);
      line-height: 1.6;
      font-size: 14px;
      transition: background 0.2s ease, color 0.2s ease;
    }}

    /* Top Navigation Bar */
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border);
      padding: 12px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}

    .topbar-brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: var(--ink);
    }}

    .gh-logo-pill {{
      background: var(--gh-orange);
      color: #FFF;
      font-weight: 800;
      font-size: 14px;
      padding: 6px 12px;
      border-radius: 8px;
      letter-spacing: -0.02em;
    }}

    .topbar-title-block strong {{
      font-size: 15px;
      font-weight: 700;
      display: block;
      color: var(--ink);
    }}

    .topbar-title-block span {{
      font-size: 11px;
      color: var(--muted);
      font-family: var(--font-mono);
    }}

    .topbar-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .search-box {{
      position: relative;
      width: 260px;
    }}

    .search-box input {{
      width: 100%;
      padding: 7px 12px 7px 32px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg-page);
      color: var(--ink);
      font-size: 12.5px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.15s ease;
    }}

    .search-box input:focus {{
      border-color: var(--gh-orange);
      background: var(--bg-card);
    }}

    .search-box::before {{
      content: '🔍';
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 12px;
      opacity: 0.6;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      font-family: inherit;
    }}

    .btn-primary {{
      background: var(--gh-orange);
      color: #FFF;
    }}
    .btn-primary:hover {{ background: var(--gh-orange-hover); }}

    .btn-outline {{
      background: var(--bg-card);
      color: var(--ink);
      border-color: var(--border);
    }}
    .btn-outline:hover {{
      border-color: var(--gh-orange);
      color: var(--gh-orange);
    }}

    /* Main Layout */
    .app-layout {{
      display: flex;
      min-height: calc(100vh - 57px);
    }}

    /* Sidebar */
    .sidebar {{
      width: 290px;
      background: var(--bg-card);
      border-right: 1px solid var(--border);
      padding: 24px 16px;
      position: sticky;
      top: 57px;
      height: calc(100vh - 57px);
      overflow-y: auto;
      flex-shrink: 0;
    }}

    .nav-group-title {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin: 16px 8px 8px 8px;
    }}

    .nav-list {{
      list-style: none;
    }}

    .nav-item {{
      margin-bottom: 2px;
    }}

    .nav-link {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 7px 10px;
      border-radius: 6px;
      color: var(--ink-soft);
      text-decoration: none;
      font-size: 12.5px;
      font-weight: 500;
      transition: all 0.15s ease;
    }}

    .nav-link:hover, .nav-link.active {{
      background: var(--gh-orange-soft);
      color: var(--gh-orange);
      font-weight: 600;
    }}

    .nav-badge {{
      margin-left: auto;
      font-size: 10px;
      font-family: var(--font-mono);
      padding: 2px 6px;
      border-radius: 4px;
      background: var(--bg-page);
      border: 1px solid var(--border);
    }}

    /* Content Area */
    .main-content {{
      flex: 1;
      padding: 32px 48px 80px 48px;
      max-width: 1180px;
      margin: 0 auto;
    }}

    /* Diagram Studio Showcase Card */
    .diagram-showcase {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
      margin-bottom: 40px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }}

    .diagram-header {{
      padding: 16px 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 14px;
      background: var(--bg-card);
    }}

    .diagram-tabs {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-page);
      padding: 4px;
      border-radius: 8px;
      border: 1px solid var(--border);
    }}

    .tab-btn {{
      padding: 6px 14px;
      border-radius: 6px;
      border: none;
      background: transparent;
      color: var(--ink-soft);
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
      transition: all 0.15s ease;
    }}

    .tab-btn.active {{
      background: var(--bg-card);
      color: var(--gh-orange);
      box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}

    .diagram-toolbar {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .diagram-viewport {{
      position: relative;
      width: 100%;
      height: 650px;
      background: #0B0F19;
    }}

    .diagram-viewport:fullscreen {{
      width: 100vw !important;
      height: 100vh !important;
      background: #0B0F19 !important;
      margin: 0 !important;
      border-radius: 0 !important;
    }}

    .diagram-viewport:fullscreen .diagram-iframe {{
      width: 100vw !important;
      height: 100vh !important;
      border: none !important;
    }}

    .diagram-viewport:fullscreen .diagram-plate-view {{
      width: 100vw !important;
      height: 100vh !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      padding: 20px !important;
    }}

    .diagram-iframe {{
      width: 100%;
      height: 100%;
      border: none;
      display: block;
    }}

    .diagram-plate-view {{
      display: none;
      width: 100%;
      height: 100%;
      overflow: auto;
      background: var(--bg-card);
      text-align: center;
      padding: 24px;
    }}

    .diagram-plate-view img {{
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }}

    .spec-drawer {{
      display: none;
      background: #0F172A;
      color: #E2E8F0;
      padding: 20px;
      max-height: 400px;
      overflow-y: auto;
      font-family: var(--font-mono);
      font-size: 11.5px;
      border-top: 1px solid var(--border);
    }}

    .spec-drawer pre {{ margin: 0; }}

    /* Markdown Body Typography */
    .prose {{
      color: var(--ink);
    }}

    .prose h1 {{
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-bottom: 8px;
      color: var(--ink);
    }}

    .prose h2 {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-top: 48px;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border);
      color: var(--ink);
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .prose h3 {{
      font-size: 18px;
      font-weight: 700;
      margin-top: 28px;
      margin-bottom: 12px;
      color: var(--ink);
    }}

    .prose h4 {{
      font-size: 15px;
      font-weight: 600;
      margin-top: 20px;
      margin-bottom: 8px;
      color: var(--ink);
    }}

    .prose p {{
      margin-bottom: 16px;
      font-size: 14px;
      line-height: 1.7;
      color: var(--ink-soft);
    }}

    .prose ul, .prose ol {{
      margin-bottom: 16px;
      padding-left: 24px;
      color: var(--ink-soft);
    }}

    .prose li {{
      margin-bottom: 6px;
      font-size: 14px;
      line-height: 1.6;
    }}

    .prose table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0 28px 0;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      background: var(--bg-card);
      font-size: 13px;
    }}

    .prose th {{
      background: #0F172A;
      color: #FFFFFF;
      font-weight: 700;
      text-align: left;
      padding: 10px 14px;
      font-size: 12px;
      letter-spacing: 0.02em;
    }}

    .prose td {{
      padding: 10px 14px;
      border: 1px solid var(--border);
      color: var(--ink-soft);
      vertical-align: top;
    }}

    .prose tr:nth-child(even) td {{
      background: var(--bg-page);
    }}

    .prose pre {{
      background: #0F172A;
      color: #F8FAFC;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.55;
      margin: 16px 0 24px 0;
      border: 1px solid #1E293B;
    }}

    .prose code {{
      font-family: var(--font-mono);
      font-size: 12px;
      background: var(--gh-orange-soft);
      color: var(--gh-orange);
      padding: 2px 6px;
      border-radius: 4px;
    }}

    .prose pre code {{
      background: transparent;
      color: inherit;
      padding: 0;
    }}

    .prose hr {{
      border: 0;
      height: 1px;
      background: var(--border);
      margin: 36px 0;
    }}

    /* GitHub Alerts */
    .alert {{
      border-radius: 8px;
      padding: 14px 18px;
      margin: 18px 0;
      border-left: 4px solid;
      background: var(--bg-card);
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }}
    .alert-title {{
      font-weight: 700;
      font-size: 13px;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .alert-body {{
      font-size: 13.5px;
      line-height: 1.6;
    }}
    .alert-note {{ border-color: #3B82F6; background: #EFF6FF; color: #1E3A8A; }}
    .alert-tip {{ border-color: #10B981; background: #ECFDF5; color: #064E3B; }}
    .alert-important {{ border-color: var(--gh-iris); background: #F5F3FF; color: #4C1D95; }}
    .alert-warning {{ border-color: #F59E0B; background: #FFFBEB; color: #78350F; }}
    .alert-caution {{ border-color: #EF4444; background: #FEF2F2; color: #7F1D1D; }}

    /* Mermaid */
    .mermaid-container {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0;
      overflow-x: auto;
      text-align: center;
    }}

    /* Interactive Likert Calculator */
    .calc-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      margin: 24px 0;
      box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }}

    .calc-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}

    .calc-control label {{
      display: block;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 6px;
    }}

    .calc-control select {{
      width: 100%;
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg-page);
      color: var(--ink);
      font-family: inherit;
      font-size: 13px;
    }}

    .calc-result {{
      margin-top: 20px;
      padding: 16px;
      border-radius: 8px;
      background: var(--bg-page);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      border: 1px solid var(--border);
    }}

    .score-badge {{
      font-size: 24px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: var(--gh-orange);
    }}

    .decision-pill {{
      padding: 6px 14px;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .decision-pill.pass {{ background: var(--pass-bg); color: var(--pass); border: 1px solid var(--pass); }}
    .decision-pill.review {{ background: var(--review-bg); color: var(--review); border: 1px solid var(--review); }}
    .decision-pill.reject {{ background: var(--reject-bg); color: var(--reject); border: 1px solid var(--reject); }}
  </style>
</head>
<body>

  <!-- Topbar -->
  <header class="topbar">
    <a href="#" class="topbar-brand">
      <span class="gh-logo-pill">GRUBHUB</span>
      <div class="topbar-title-block">
        <strong>Merchant Menu Image Platform PRD <span style="font-size:11px; background:#F5F3FF; color:#5B21B6; border:1px solid #DDD6FE; padding:2px 7px; border-radius:999px; margin-left:6px; vertical-align:middle;">v5.2 • Gemini 3.8 Flash + Nano Banana 2.1</span></strong>
        <span>Production Architecture & Interactive System Specification (12-Gate Moderation • ≥0.35 Floor)</span>
      </div>
    </a>
    <div class="topbar-actions">
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search PRD specifications..." oninput="filterContent(this.value)">
      </div>
      <button class="btn btn-outline" onclick="toggleDarkMode()">🌓 Mode</button>
      <a href="/prd.pdf?v=5.2" onclick="if(window.location.protocol==='file:'){{this.href='../PRD_MERCHANT_MENU_IMAGE_PLATFORM.pdf';}}" class="btn btn-primary" download="PRD_MERCHANT_MENU_IMAGE_PLATFORM.pdf">📄 Download PDF</a>
    </div>
  </header>

  <div class="app-layout">
    
    <!-- Sidebar Navigation -->
    <aside class="sidebar">
      <div class="nav-group-title">Interactive Diagrams</div>
      <ul class="nav-list">
        <li class="nav-item"><a href="#interactive-studio" class="nav-link" onclick="switchTab('architecture')">🏗️ Architecture Topology <span class="nav-badge">Live</span></a></li>
        <li class="nav-item"><a href="#interactive-studio" class="nav-link" onclick="switchTab('dataflow')">🔄 5-Stage Ingestion Flow <span class="nav-badge">Live</span></a></li>
        <li class="nav-item"><a href="#interactive-studio" class="nav-link" onclick="switchTab('sequence')">⏱️ Merchant Journey Sequence <span class="nav-badge">Live</span></a></li>
      </ul>

      <div class="nav-group-title">PRD Specifications</div>
      <ul class="nav-list">
        <li class="nav-item"><a href="#1-executive-summary-vision" class="nav-link">1. Executive Summary & Vision</a></li>
        <li class="nav-item"><a href="#2-capability-matrix" class="nav-link">2. Capability Matrix</a></li>
        <li class="nav-item"><a href="#3-end-to-end-system-architecture" class="nav-link">3. End-to-End Architecture</a></li>
        <li class="nav-item"><a href="#4-detailed-functional-specifications" class="nav-link">4. Functional Specs (Phases A–D)</a></li>
        <li class="nav-item"><a href="#likert-tool" class="nav-link">📐 Likert 1–5 Calibration Tool</a></li>
        <li class="nav-item"><a href="#5-platform-architecture-merchant-ingestion-experience-current-implementation" class="nav-link">5. Platform Architecture & Experience</a></li>
        <li class="nav-item"><a href="#6-api-specifications-data-contracts" class="nav-link">6. API Specs & Data Contracts</a></li>
        <li class="nav-item"><a href="#7-gemini-30-nano-banana-21-prompt-engineering-system-instructions-model-roles" class="nav-link">7. Gemini 3.0+ & Nano Banana 2.1 Prompts</a></li>
        <li class="nav-item"><a href="#8-empirical-benchmark-findings-across-the-50-sample-photos" class="nav-link">8. Empirical Benchmark (50 Photos)</a></li>
        <li class="nav-item"><a href="#9-ai-evaluation-observability-quality-assurance-framework" class="nav-link">9. Evaluation & Observability</a></li>
        <li class="nav-item"><a href="#10-production-latency-token-economics-sku-cost-profile-october-2026" class="nav-link">10. Latency, Token & SKU Cost Profile</a></li>
        <li class="nav-item"><a href="#11-merchant-customer-user-journeys-grubhub-merchant-portal-ui" class="nav-link">11. Merchant User Journeys & UI</a></li>
      </ul>
    </aside>

    <!-- Main Content -->
    <main class="main-content">

      <!-- Interactive Studio Showcase -->
      <section id="interactive-studio" class="diagram-showcase">
        <div class="diagram-header">
          <div class="diagram-tabs">
            <button class="tab-btn active" id="tab-btn-architecture" onclick="switchTab('architecture')">🏗️ Architecture Topology</button>
            <button class="tab-btn" id="tab-btn-dataflow" onclick="switchTab('dataflow')">🔄 5-Stage Ingestion Dataflow</button>
            <button class="tab-btn" id="tab-btn-sequence" onclick="switchTab('sequence')">⏱️ Journey Sequence Flow</button>
          </div>
          <div class="diagram-toolbar">
            <button class="btn btn-outline" onclick="toggleViewMode()" id="viewModeBtn">🖼️ View Static Plate</button>
            <button class="btn btn-outline" onclick="toggleDiagramToolbar()" id="toolbarToggleBtn" title="Toggle internal floating controls (Dark, Style, Present, Export)">🎛️ Diagram Controls</button>
            <button class="btn btn-outline" onclick="toggleSpecDrawer()">📜 System JSON IR</button>
            <button class="btn btn-outline" onclick="openDiagramFullscreen()">⛶ Fullscreen</button>
          </div>
        </div>

        <div class="diagram-viewport" id="viewport">
          <iframe id="diagramIframe" class="diagram-iframe" srcdoc="" allow="fullscreen; clipboard-read; clipboard-write; download" allowfullscreen="true"></iframe>
          <div class="diagram-plate-view" id="plateView">
            <img id="plateImg" src="{ARCH_PLATE_B64}" alt="System Diagram Plate">
          </div>
        </div>

        <div class="spec-drawer" id="specDrawer">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong id="specTitle">System Topology Specification (JSON IR)</strong>
            <button class="btn btn-outline" style="padding: 3px 8px; font-size: 11px;" onclick="copySpecJson()">📋 Copy JSON</button>
          </div>
          <pre><code id="specCode"></code></pre>
        </div>
      </section>

      <!-- Interactive Likert Calculator Widget -->
      <div id="likert-tool" class="calc-card">
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px;">
          <h3 style="margin: 0; font-size: 18px; font-weight: 700;">📐 Interactive Likert 1–5 Quality Gate Calculator</h3>
          <span class="badge badge-primary">Rule B8 Gate</span>
        </div>
        <p style="font-size: 13px; color: var(--muted); margin: 0;">
          Simulate merchant camera intake scoring. Evaluates Focus, Lighting, Composition, and Clutter against calibrated thresholds (1 → 0.20, 2 → 0.50, 3 → 0.70, 4 → 0.85, 5 → 1.00) with a minimum quality floor at 0.35 (0.35–0.54 borderline review band; ≥ 0.55 eligible for studio reshoot).
        </p>
        
        <div class="calc-grid">
          <div class="calc-control">
            <label>Focus / Sharpness</label>
            <select id="calc-focus" onchange="computeQuality()">
              <option value="1">1 — Unrecoverable Blur (0.20)</option>
              <option value="2">2 — Soft / Minor Blur (0.50)</option>
              <option value="3" selected>3 — Good Sharpness (0.70)</option>
              <option value="4">4 — Commercial Crisp (0.85)</option>
              <option value="5">5 — Studio Reference (1.00)</option>
            </select>
          </div>
          <div class="calc-control">
            <label>Lighting Harmonization</label>
            <select id="calc-light" onchange="computeQuality()">
              <option value="1">1 — Severely Underexposed (0.20)</option>
              <option value="2">2 — Harsh Fluorescent (0.50)</option>
              <option value="3" selected>3 — Balanced Commercial (0.70)</option>
              <option value="4">4 — Studio Directional (0.85)</option>
              <option value="5">5 — Magazine Quality (1.00)</option>
            </select>
          </div>
          <div class="calc-control">
            <label>Plating & Framing</label>
            <select id="calc-comp" onchange="computeQuality()">
              <option value="1">1 — Severely Clipped (0.20)</option>
              <option value="2">2 — Off-Center / Awkward (0.50)</option>
              <option value="3" selected>3 — Centered 1:1 Framing (0.70)</option>
              <option value="4">4 — Hero Dish Focus (0.85)</option>
              <option value="5">5 — Golden Ratio Presentation (1.00)</option>
            </select>
          </div>
          <div class="calc-control">
            <label>Kitchen Background Clutter</label>
            <select id="calc-clutter" onchange="computeQuality()">
              <option value="1">1 — Extreme (Trash / Hands) (0.20)</option>
              <option value="2">2 — Distracting Utensils (0.50)</option>
              <option value="3" selected>3 — Neutral Tabletop (0.70)</option>
              <option value="4">4 — Clean Studio Surface (0.85)</option>
              <option value="5">5 — Pristine Minimalist (1.00)</option>
            </select>
          </div>
        </div>

        <div class="calc-result">
          <div>
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--muted);">Calibrated Quality Score</div>
            <div class="score-badge" id="calcScore">0.70</div>
          </div>
          <div>
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--muted); margin-bottom: 4px;">Automated Decision Gate</div>
            <span class="decision-pill pass" id="calcDecision">AUTO_APPROVE (Eligible for Studio Reshoot)</span>
          </div>
        </div>
      </div>

      <!-- Markdown Prose Container -->
      <article class="prose" id="proseBody">
        {body_html}
      </article>

    </main>
  </div>

  <script>
    // Tab Specifications & HTML mapping
    const specs = {{
      architecture: {{
        title: "System Architecture Specification (JSON IR)",
        json: {safe_js_str(ARCH_JSON)},
        srcdoc: {safe_js_str(ARCH_HTML)},
        plate: "{ARCH_PLATE_B64}"
      }},
      dataflow: {{
        title: "5-Stage Ingestion Dataflow Specification (JSON IR)",
        json: {safe_js_str(DATAFLOW_JSON)},
        srcdoc: {safe_js_str(DATAFLOW_HTML)},
        plate: "{DATAFLOW_PLATE_B64}"
      }},
      sequence: {{
        title: "Merchant Journey Sequence Specification (JSON IR)",
        json: {safe_js_str(SEQUENCE_JSON)},
        srcdoc: {safe_js_str(SEQUENCE_HTML)},
        plate: "{SEQUENCE_PLATE_B64}"
      }}
    }};

    let currentTab = 'architecture';
    let isPlateMode = false;

    function switchTab(tabKey) {{
      currentTab = tabKey;
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById('tab-btn-' + tabKey);
      if (activeBtn) activeBtn.classList.add('active');

      const data = specs[tabKey];
      const iframe = document.getElementById('diagramIframe');
      iframe.srcdoc = data.srcdoc;
      document.getElementById('plateImg').src = data.plate;
      document.getElementById('specTitle').innerText = data.title;
      document.getElementById('specCode').innerText = JSON.stringify(JSON.parse(data.json), null, 2);

      iframe.onload = function() {{
        try {{
          if (iframe.contentDocument) {{
            const isDark = document.body.classList.contains('dark-mode');
            iframe.contentDocument.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
            const label = iframe.contentDocument.getElementById('theme-label');
            if (label) label.textContent = isDark ? 'Light' : 'Dark';
            const btn = iframe.contentDocument.getElementById('btn-theme');
            if (btn) btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
          }}
        }} catch (_) {{}}
      }};
    }}

    function toggleDiagramToolbar() {{
      const iframe = document.getElementById('diagramIframe');
      if (iframe && iframe.contentDocument) {{
        const tb = iframe.contentDocument.querySelector('.toolbar');
        if (tb) {{
          const isHidden = tb.style.display === 'none';
          tb.style.display = isHidden ? '' : 'none';
          const btn = document.getElementById('toolbarToggleBtn');
          if (btn) btn.classList.toggle('active', !isHidden);
        }}
      }}
    }}

    function toggleViewMode() {{
      isPlateMode = !isPlateMode;
      const iframe = document.getElementById('diagramIframe');
      const plate = document.getElementById('plateView');
      const btn = document.getElementById('viewModeBtn');

      if (isPlateMode) {{
        iframe.style.display = 'none';
        plate.style.display = 'block';
        btn.innerHTML = '⚡ View Interactive';
      }} else {{
        iframe.style.display = 'block';
        plate.style.display = 'none';
        btn.innerHTML = '🖼️ View Static Plate';
      }}
    }}

    function toggleSpecDrawer() {{
      const drawer = document.getElementById('specDrawer');
      drawer.style.display = drawer.style.display === 'block' ? 'none' : 'block';
    }}

    function copySpecJson() {{
      const code = document.getElementById('specCode').innerText;
      navigator.clipboard.writeText(code).then(() => {{
        alert('System Topology JSON IR copied to clipboard!');
      }});
    }}

    function openDiagramFullscreen() {{
      const viewport = document.getElementById('viewport');
      if (viewport.requestFullscreen) {{
        viewport.requestFullscreen();
      }}
    }}

    function toggleDarkMode() {{
      document.body.classList.toggle('dark-mode');
      const isDark = document.body.classList.contains('dark-mode');
      try {{
        const iframe = document.getElementById('diagramIframe');
        if (iframe && iframe.contentDocument) {{
          const doc = iframe.contentDocument;
          doc.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
          const label = doc.getElementById('theme-label');
          if (label) label.textContent = isDark ? 'Light' : 'Dark';
          const btn = doc.getElementById('btn-theme');
          if (btn) btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
        }}
      }} catch (_) {{}}
    }}

    // Likert Score Calculation
    const likertMap = {{ "1": 0.20, "2": 0.50, "3": 0.70, "4": 0.85, "5": 1.00 }};

    function computeQuality() {{
      const f = likertMap[document.getElementById('calc-focus').value];
      const l = likertMap[document.getElementById('calc-light').value];
      const c = likertMap[document.getElementById('calc-comp').value];
      const cl = likertMap[document.getElementById('calc-clutter').value];

      const score = (f * 0.40) + (l * 0.25) + (c * 0.20) + (cl * 0.15);
      const rounded = score.toFixed(2);
      document.getElementById('calcScore').innerText = rounded;

      const decisionEl = document.getElementById('calcDecision');
      if (score >= 0.75) {{
        decisionEl.className = 'decision-pill pass';
        decisionEl.innerText = 'AUTO_APPROVE (Commercial Studio Standard)';
      }} else if (score >= 0.55) {{
        decisionEl.className = 'decision-pill pass';
        decisionEl.innerText = 'AUTO_APPROVE (Eligible for Studio Reshoot)';
      }} else if (score >= 0.35) {{
        decisionEl.className = 'decision-pill review';
        decisionEl.innerText = 'FLAG_FOR_REVIEW (Borderline Margin Band)';
      }} else {{
        decisionEl.className = 'decision-pill reject';
        decisionEl.innerText = 'AUTO_REJECT (Fast-Fail Unrecoverable Defect <0.35)';
      }}
    }}

    // Real-time Text Search Filter
    function filterContent(query) {{
      const q = query.toLowerCase().trim();
      const sections = document.querySelectorAll('.prose h2, .prose h3, .prose p, .prose tr');
      if (!q) {{
        sections.forEach(el => el.style.display = '');
        return;
      }}
      sections.forEach(el => {{
        const text = el.innerText.toLowerCase();
        if (el.tagName === 'TR') {{
          el.style.display = text.includes(q) ? '' : 'none';
        }}
      }});
    }}

    // Initialize default spec view
    switchTab('architecture');

    // Initialize KaTeX and Mermaid
    function initDiagramsAndMath() {{
      if (window.renderMathInElement) {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{left: "$$", right: "$$", display: true}},
            {{left: "$", right: "$", display: false}}
          ],
          ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
          throwOnError: false
        }});
      }}
      if (window.mermaid) {{
        mermaid.initialize({{
          startOnLoad: false,
          theme: 'neutral',
          securityLevel: 'loose'
        }});
        mermaid.run();
      }}
    }}

    if (document.readyState === 'loading') {{
      document.addEventListener("DOMContentLoaded", initDiagramsAndMath);
    }} else {{
      initDiagramsAndMath();
    }}
    window.addEventListener("load", initDiagramsAndMath);
  </script>
</body>
</html>
"""

# Save Interactive PRD to interactive_prd/index.html
OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_HTML.write_text(PORTAL_TEMPLATE, encoding="utf-8")
print(f"✅ Generated Interactive PRD: {OUTPUT_HTML} ({round(OUTPUT_HTML.stat().st_size / 1024, 1)} KB)")

# Mirror to results/PRD_INTERACTIVE_PLATFORM.html
RESULTS_HTML.parent.mkdir(parents=True, exist_ok=True)
RESULTS_HTML.write_text(PORTAL_TEMPLATE, encoding="utf-8")
print(f"✅ Mirrored to: {RESULTS_HTML} ({round(RESULTS_HTML.stat().st_size / 1024, 1)} KB)")

print("Done building Interactive PRD Portal!")
