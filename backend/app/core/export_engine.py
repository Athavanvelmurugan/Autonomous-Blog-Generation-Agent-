import io
import re
import html
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    Preformatted,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


# ============================================================================
# 1. Numbered Canvas for Dynamic Page Counts and Running Headers/Footers
# ============================================================================
class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that computes the total number of pages and draws
    consistent running headers and footers with 'Page X of Y'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header on page 2+ (suppress on hero cover page 1)
        if self._pageNumber > 1:
            header_text = getattr(self, "article_title", "Educational Publication")
            if len(header_text) > 60:
                header_text = header_text[:57] + "..."
            self.drawString(45, 755, header_text)
            self.drawRightString(567, 755, "Autonomous Educational Series")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.6)
            self.line(45, 747, 567, 747)

        # Running Footer on all pages
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawString(45, 30, "Autonomous Blog Generation Agent • Verified Educational Series")
        self.drawRightString(567, 30, page_str)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.6)
        self.line(45, 40, 567, 40)

        self.restoreState()


# ============================================================================
# 2. Modern HTML Export Generator (Inspired by howtolearnmachinelearning.com)
# ============================================================================
def generate_article_html(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Renders publication-quality, standalone, responsive HTML with modern typography,
    styled tables, monospaced code blocks with copy action, anchor-linked table of contents,
    and clean metadata chips.
    Inspired by modern educational engineering publications like howtolearnmachinelearning.com.
    """
    metadata = metadata or {}
    topic = metadata.get("topic", title)
    audience = metadata.get("target_audience", "Beginner")
    tone = metadata.get("tone", "Educational")
    word_count = metadata.get("word_count") or len(re.findall(r"\b\w+\b", content))
    reading_time = max(1, round(word_count / 200))
    pub_date = metadata.get("created_at") or datetime.now(timezone.utc).strftime("%B %d, %Y")

    # Strip duplicate leading H1 from content if present, since it is rendered in hero header
    content_clean = content.strip()
    if content_clean.startswith("# "):
        lines = content_clean.split("\n", 1)
        first_line = lines[0].lstrip("# ").strip()
        if len(first_line) > 3:
            content_clean = lines[1].lstrip("\n") if len(lines) > 1 else ""

    # Ensure all markdown headers ## Title {#slug} or ## Title have anchor IDs
    def _slugify(text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_-]+", "-", s)
        return s.strip("-")

    # Convert Markdown to HTML with rich extensions
    md_converter = markdown.Markdown(
        extensions=[
            "extra",
            "tables",
            "fenced_code",
            "toc",
            "sane_lists",
            "smarty",
        ],
        output_format="html5",
    )
    rendered_body = md_converter.convert(content_clean)

    # Post-process rendered HTML to ensure all h2 and h3 have IDs for Table of Contents links
    def _add_heading_id(match):
        tag = match.group(1)
        existing_attrs = match.group(2) or ""
        inner_html = match.group(3)
        if 'id="' in existing_attrs:
            return match.group(0)
        # Extract clean text from inner HTML to generate slug
        plain_text = re.sub(r"<[^>]+>", "", inner_html)
        # Strip trailing {#...} if left over
        plain_text = re.sub(r"\s*\{#[^}]+\}\s*$", "", plain_text).strip()
        slug = _slugify(plain_text)
        return f'<{tag} id="{slug}"{existing_attrs}>{inner_html}</{tag}>'

    rendered_body = re.sub(r"<(h[2-4])([^>]*)>([\s\S]*?)<\/\1>", _add_heading_id, rendered_body)

    # Wrap code blocks in educational card with header and copy button
    def _enhance_pre(match):
        code_content = match.group(1)
        return (
            '<div class="code-block-container">'
            '  <div class="code-block-header">'
            '    <div class="code-lang-tag"><span>Python 3 &bull; Runnable Demonstration</span></div>'
            '    <button class="copy-code-btn" onclick="copyCode(this)">Copy Code</button>'
            '  </div>'
            f'  <pre><code>{code_content}</code></pre>'
            '</div>'
        )

    rendered_body = re.sub(r"<pre><code>([\s\S]*?)<\/code><\/pre>", _enhance_pre, rendered_body)

    html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} | Educational Engineering Guide</title>
  <meta name="description" content="In-depth educational guide on {html.escape(topic)} for {html.escape(audience)} learners.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --primary-light: #eff6ff;
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-subtle: #64748b;
      --bg-body: #f8fafc;
      --bg-card: #ffffff;
      --border-color: #e2e8f0;
      --code-bg: #0f172a;
      --code-text: #f1f5f9;
      --accent-badge: #e0e7ff;
      --accent-badge-text: #3730a3;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    html {{
      scroll-behavior: smooth;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg-body);
      color: var(--text-main);
      line-height: 1.75;
      font-size: 16px;
      -webkit-font-smoothing: antialiased;
      padding: 2.5rem 1rem;
    }}

    .article-container {{
      max-width: 840px;
      margin: 0 auto;
      background: var(--bg-card);
      border-radius: 16px;
      border: 1px solid var(--border-color);
      box-shadow: 0 4px 24px -2px rgba(15, 23, 42, 0.06);
      padding: 3.5rem 3.5rem;
    }}

    @media (max-width: 768px) {{
      body {{
        padding: 1rem 0.5rem;
      }}
      .article-container {{
        padding: 2rem 1.25rem;
        border-radius: 12px;
      }}
    }}

    /* Header & Hero Section */
    .article-header {{
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 2rem;
      margin-bottom: 2.5rem;
    }}

    .badge-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1.25rem;
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.25rem 0.75rem;
      font-size: 0.8rem;
      font-weight: 600;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .badge-category {{
      background-color: var(--primary-light);
      color: var(--primary);
    }}

    .badge-audience {{
      background-color: #fef3c7;
      color: #92400e;
    }}

    .badge-reading {{
      background-color: #f1f5f9;
      color: var(--text-muted);
    }}

    .article-title {{
      font-size: 2.35rem;
      line-height: 1.25;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.025em;
      margin-bottom: 1.25rem;
    }}

    .article-meta {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.75rem;
      font-size: 0.88rem;
      color: var(--text-subtle);
    }}

    .author-info {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--text-muted);
    }}

    .author-avatar {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: var(--primary);
      color: #ffffff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 700;
    }}

    /* Typography in Article Content */
    .article-content {{
      color: var(--text-main);
      font-size: 1.05rem;
      line-height: 1.8;
    }}

    .article-content h1 {{
      display: none; /* Hide duplicate title if rendered inside markdown body */
    }}

    .article-content h2 {{
      font-size: 1.65rem;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 2.75rem;
      margin-bottom: 1.25rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border-color);
      letter-spacing: -0.015em;
    }}

    .article-content h3 {{
      font-size: 1.3rem;
      font-weight: 600;
      color: var(--text-main);
      margin-top: 2rem;
      margin-bottom: 0.85rem;
      letter-spacing: -0.01em;
    }}

    .article-content p {{
      margin-bottom: 1.4rem;
      color: #334155;
    }}

    /* Table of Contents Highlight */
    .article-content .toc,
    .article-content ul:has(a[href^="#"]) {{
      background: #f8fafc;
      border: 1px solid var(--border-color);
      border-left: 4px solid var(--primary);
      border-radius: 10px;
      padding: 1.25rem 1.5rem 1.25rem 2.25rem;
      margin: 2rem 0;
    }}

    .article-content .toc a,
    .article-content ul:has(a[href^="#"]) a {{
      color: var(--primary);
      text-decoration: none;
      font-weight: 500;
    }}

    .article-content .toc a:hover,
    .article-content ul:has(a[href^="#"]) a:hover {{
      text-decoration: underline;
    }}

    /* Lists */
    .article-content ul,
    .article-content ol {{
      margin-bottom: 1.4rem;
      padding-left: 1.75rem;
    }}

    .article-content li {{
      margin-bottom: 0.5rem;
    }}

    /* Links */
    .article-content a {{
      color: var(--primary);
      text-decoration: underline;
      text-underline-offset: 3px;
      transition: color 0.15s ease;
    }}

    .article-content a:hover {{
      color: var(--primary-hover);
    }}

    /* Code Blocks */
    .code-block-container {{
      margin: 1.75rem 0;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid #1e293b;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
      background: var(--code-bg);
    }}

    .code-block-header {{
      background: #1e293b;
      padding: 0.5rem 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #334155;
      font-family: 'Inter', sans-serif;
      font-size: 0.78rem;
    }}

    .code-lang-tag {{
      color: #94a3b8;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .copy-code-btn {{
      background: #334155;
      color: #f1f5f9;
      border: none;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .copy-code-btn:hover {{
      background: var(--primary);
    }}

    .article-content pre {{
      background: var(--code-bg);
      color: var(--code-text);
      padding: 1.25rem 1.5rem;
      overflow-x: auto;
      font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
      font-size: 0.88rem;
      line-height: 1.6;
      margin: 0;
    }}

    .article-content code {{
      font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
      font-size: 0.88em;
      background: #f1f5f9;
      color: #0f172a;
      padding: 0.2rem 0.45rem;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}

    .article-content pre code {{
      background: transparent;
      color: inherit;
      padding: 0;
      border: none;
      font-size: 1em;
    }}

    /* Tables */
    .article-content table {{
      width: 100%;
      border-collapse: collapse;
      margin: 2rem 0;
      font-size: 0.92rem;
      background: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border-color);
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}

    .article-content th,
    .article-content td {{
      padding: 0.85rem 1.15rem;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }}

    .article-content th {{
      background: #1e293b;
      font-weight: 600;
      color: #ffffff;
      border-bottom: 2px solid var(--border-color);
    }}

    .article-content tr:nth-child(even) td {{
      background: #fcfdfe;
    }}

    .article-content tr:hover td {{
      background: #f8fafc;
    }}

    /* Blockquotes / Callout Cards */
    .article-content blockquote {{
      border-left: 4px solid var(--primary);
      background: var(--primary-light);
      padding: 1rem 1.25rem;
      margin: 1.75rem 0;
      border-radius: 0 8px 8px 0;
      color: #1e3a8a;
      font-style: normal;
    }}

    .article-content blockquote p {{
      margin-bottom: 0;
      color: inherit;
    }}

    /* Footer */
    .article-footer {{
      margin-top: 3.5rem;
      padding-top: 2rem;
      border-top: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      font-size: 0.88rem;
      color: var(--text-subtle);
    }}

    .footer-actions {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}

    .back-to-top {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
    }}

    .back-to-top:hover {{
      text-decoration: underline;
    }}

    @media print {{
      body {{
        background: #ffffff;
        padding: 0;
      }}
      .article-container {{
        box-shadow: none;
        border: none;
        padding: 0;
        max-width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <article class="article-container" id="top">
    <!-- Header -->
    <header class="article-header">
      <div class="badge-bar">
        <span class="badge badge-category">Educational Series</span>
        <span class="badge badge-audience">Audience: {html.escape(audience)}</span>
        <span class="badge badge-reading">{reading_time} min read</span>
      </div>
      <h1 class="article-title">{html.escape(title)}</h1>
      <div class="article-meta">
        <div class="author-info">
          <div class="author-avatar">AI</div>
          <span><strong>Autonomous Educational Blog Engine</strong></span>
        </div>
        <span>&bull;</span>
        <time datetime="{pub_date}">{pub_date}</time>
        <span>&bull;</span>
        <span>{word_count:,} words</span>
      </div>
    </header>

    <!-- Main Content -->
    <main class="article-content">
      {rendered_body}
    </main>

    <!-- Footer -->
    <footer class="article-footer">
      <div class="footer-actions">
        <span>Grounded in verified research citations &bull; Autonomous Blog Generation Agent</span>
        <a href="#top" class="back-to-top">&uarr; Back to top</a>
      </div>
    </footer>
  </article>

  <script>
    function copyCode(btn) {{
      const pre = btn.closest('.code-block-container').querySelector('pre');
      navigator.clipboard.writeText(pre.innerText).then(() => {{
        const originalText = btn.innerText;
        btn.innerText = 'Copied!';
        setTimeout(() => btn.innerText = originalText, 2000);
      }});
    }}
  </script>
</body>
</html>
"""
    return html_document


# ============================================================================
# 3. ReportLab PDF Export Generator (Typeset Educational Publication)
# ============================================================================
def _format_inline_markdown(text: str) -> str:
    """
    Converts inline Markdown (code, bold, italic, links, math) into ReportLab XML markup.
    Protects inline code first so underscores inside variable/code names are preserved.
    """
    # 0. Clean double-bracket citations like [[F4: geeksforgeeks.org]](url) -> [geeksforgeeks.org](url)
    text = re.sub(r"\[\[(?:F\d+:\s*)?([^\]]+)\]\]\(([^)]+)\)", r"[\1](\2)", text)
    text = re.sub(r"\[\[(?:F\d+:\s*)?([^\]]+)\]\]", r"\1", text)

    # 1. Normalize unicode punctuation so Helvetica doesn't render black square glyphs
    for ch in ['\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2212', '\ufe63', '\uff0d']:
        text = text.replace(ch, '-')
    for ch in ['\u2018', '\u2019']:
        text = text.replace(ch, "'")
    for ch in ['\u201c', '\u201d']:
        text = text.replace(ch, '"')

    # 2. Escape XML characters
    text = html.escape(text, quote=False)

    # 3. Bullets: replace unicode bullets with &bull; entity for ReportLab
    for ch in ['\u2022', '\u2023', '\u25e6', '\u2043', '\u2219']:
        text = text.replace(ch, '&bull;')

    # 2. Extract and protect inline code `code` first to prevent mangling of underscores
    code_placeholders = []
    def _code_repl(m):
        raw_c = m.group(1)
        code_placeholders.append(raw_c)
        return f"XYZCODEPH{len(code_placeholders)-1}XYZ"

    text = re.sub(r"`([^`]+)`", _code_repl, text)

    # 3. Math variables: $X$ -> <i>X</i>
    text = re.sub(r"\$([a-zA-Z0-9_\^\+\-]+)\$", r"<i>\1</i>", text)

    # 4. Bold **text** -> <b>text</b>
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    # 5. Italic *text* or _text_ -> <i>text</i>
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<i>\1</i>", text)

    # 6. Links [text](url) -> Clickable link or styled text
    def _link_sub(match):
        anchor_text = match.group(1)
        url = match.group(2).strip()
        if url.startswith("http://") or url.startswith("https://"):
            return f'<a href="{url}" color="#2563eb"><u>{anchor_text}</u></a>'
        return f'<font color="#2563eb"><b>{anchor_text}</b></font>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link_sub, text)

    # 7. Restore protected inline code
    for idx, raw_c in enumerate(code_placeholders):
        formatted_code = f'<font name="Courier" color="#0f172a"><b>{raw_c}</b></font>'
        text = text.replace(f"XYZCODEPH{idx}XYZ", formatted_code)

    return text


def generate_article_pdf(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generates a publication-quality PDF from the educational blog post.
    Features:
    - Dark readable body text and clear typography hierarchy
    - Title banner with publication date, target audience, reading time
    - Table of Contents formatting
    - Monospaced code blocks with soft shaded backgrounds
    - Neatly formatted comparison tables with proportional column widths
    - Running header and 'Page X of Y' dynamic footers
    """
    metadata = metadata or {}
    audience = metadata.get("target_audience", "Beginner")
    pub_date = metadata.get("created_at") or datetime.now(timezone.utc).strftime("%B %d, %Y")
    word_count = metadata.get("word_count") or len(re.findall(r"\b\w+\b", content))
    reading_time = max(1, round(word_count / 200))

    # Strip duplicate leading H1 from content if matching or similar to title
    content_clean = content.strip()
    # Normalize unicode hyphens and quotes in body
    for ch in ['\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2212', '\ufe63', '\uff0d']:
        content_clean = content_clean.replace(ch, '-')
    for ch in ['\u2018', '\u2019']:
        content_clean = content_clean.replace(ch, "'")
    for ch in ['\u201c', '\u201d']:
        content_clean = content_clean.replace(ch, '"')

    if content_clean.startswith("# "):
        lines = content_clean.split("\n", 1)
        first_line = lines[0].lstrip("# ").strip()
        if len(first_line) > 3:
            content_clean = lines[1].lstrip("\n") if len(lines) > 1 else ""

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=52,
        bottomMargin=50,
    )

    # Styles
    styles = getSampleStyleSheet()

    hero_category_style = ParagraphStyle(
        "PDF_HeroCat",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=4,
    )

    title_style = ParagraphStyle(
        "PDF_Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=25,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10,
        keepWithNext=True,
    )

    meta_style = ParagraphStyle(
        "PDF_MetaBar",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "PDF_H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "PDF_H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )

    h3_style = ParagraphStyle(
        "PDF_H3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "PDF_Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13.8,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "PDF_Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=14,
        spaceAfter=3,
    )

    toc_item_style = ParagraphStyle(
        "PDF_TOCItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12.5,
        textColor=colors.HexColor("#1d4ed8"),
        leftIndent=10,
        spaceAfter=2.5,
    )

    callout_style = ParagraphStyle(
        "PDF_Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e3a8a"),
    )

    code_line_style = ParagraphStyle(
        "PDF_CodeLine",
        fontName="Courier",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#0f172a"),
    )

    table_cell_style = ParagraphStyle(
        "PDF_TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1e293b"),
    )

    table_header_style = ParagraphStyle(
        "PDF_TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#ffffff"),
    )

    story = []

    # 1. Opening Section / Hero Banner
    story.append(Paragraph("EDUCATIONAL TECHNICAL PUBLICATION &bull; COMPREHENSIVE GUIDE", hero_category_style))
    story.append(Paragraph(title, title_style))
    meta_text = (
        f"<b>AUDIENCE:</b> {audience.upper()} &nbsp;|&nbsp; "
        f"<b>READING TIME:</b> {reading_time} MIN READ ({word_count:,} words) &nbsp;|&nbsp; "
        f"<b>PUBLISHED:</b> {pub_date}"
    )
    story.append(Paragraph(meta_text, meta_style))
    story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor("#2563eb"), spaceAfter=12))

    # Parse content line by line
    lines = content_clean.split("\n")
    i = 0
    in_code_block = False
    code_lines: List[str] = []
    in_toc_section = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 1. Code blocks ```
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                wrapped_code = []
                for cl in code_lines:
                    if len(cl) > 85:
                        chunks = [cl[j:j+85] for j in range(0, len(cl), 85)]
                        wrapped_code.extend(chunks)
                    else:
                        wrapped_code.append(cl)
                code_text = "\n".join(wrapped_code)
                for ch in ['\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2212', '\ufe63', '\uff0d']:
                    code_text = code_text.replace(ch, '-')
                for ch in ['\u2018', '\u2019']:
                    code_text = code_text.replace(ch, "'")
                for ch in ['\u201c', '\u201d']:
                    code_text = code_text.replace(ch, '"')
                code_lines = []

                code_pre = Preformatted(code_text, code_line_style)
                header_p = Paragraph("<b>Python Implementation &bull; Runnable Demonstration</b>", ParagraphStyle(
                    "CodeHeader", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=colors.HexColor("#cbd5e1")
                ))

                code_box = Table(
                    [[header_p], [code_pre]],
                    colWidths=[522]
                )
                code_box.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
                    ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                    ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#334155")),
                    ('TOPPADDING', (0, 0), (-1, 0), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 1), (-1, 1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
                ]))
                story.append(Spacer(1, 4))
                story.append(KeepTogether(code_box))
                story.append(Spacer(1, 6))
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # 2. Markdown Tables
        if stripped.startswith("|") and "|" in stripped[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row_str = lines[i].strip()
                if not re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", row_str):
                    table_lines.append(row_str)
                i += 1

            if table_lines:
                parsed_table_data = []
                for row_idx, row in enumerate(table_lines):
                    raw_cells = [c.strip() for c in row.strip("|").split("|")]
                    if not raw_cells:
                        continue
                    row_cells = []
                    is_header = (row_idx == 0)
                    for c in raw_cells:
                        formatted_cell = _format_inline_markdown(c)
                        c_style = table_header_style if is_header else table_cell_style
                        row_cells.append(Paragraph(formatted_cell, c_style))
                    parsed_table_data.append(row_cells)

                if parsed_table_data:
                    num_cols = max(len(r) for r in parsed_table_data)
                    col_char_counts = [0] * num_cols
                    for r in parsed_table_data:
                        for col_idx, cell in enumerate(r):
                            text_len = len(str(getattr(cell, "text", "")))
                            col_char_counts[col_idx] = max(col_char_counts[col_idx], text_len)

                    total_chars = max(sum(col_char_counts), 1)
                    calc_widths = [max(65, min(200, (c / total_chars) * 522)) for c in col_char_counts]
                    scale_ratio = 522 / max(sum(calc_widths), 1)
                    final_col_widths = [w * scale_ratio for w in calc_widths]

                    t = Table(parsed_table_data, colWidths=final_col_widths)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ]))
                    story.append(Spacer(1, 4))
                    if len(parsed_table_data) <= 8:
                        story.append(KeepTogether(t))
                    else:
                        story.append(t)
                    story.append(Spacer(1, 6))
            continue

        # 3. Empty lines
        if not stripped:
            i += 1
            continue

        # 3b. Horizontal rules
        if re.match(r"^[-*_]{3,}$", stripped):
            in_toc_section = False
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#e2e8f0"), spaceAfter=8))
            i += 1
            continue

        # 4. Headings
        clean_heading = re.sub(r"\s*\{#[^}]+\}\s*$", "", stripped)
        clean_heading = re.sub(r"\s*#+\s*$", "", clean_heading)

        if clean_heading.startswith("### "):
            in_toc_section = False
            text = _format_inline_markdown(clean_heading[4:])
            story.append(Paragraph(text, h3_style))
            i += 1
            continue
        elif clean_heading.startswith("## "):
            text = _format_inline_markdown(clean_heading[3:])
            if "table of contents" in text.lower():
                in_toc_section = True
            else:
                in_toc_section = False
            story.append(Paragraph(text, h2_style))
            i += 1
            continue
        elif clean_heading.startswith("# "):
            in_toc_section = False
            text = _format_inline_markdown(clean_heading[2:])
            story.append(Paragraph(text, h1_style))
            i += 1
            continue

        # 5. Blockquotes (starts with '>')
        if stripped.startswith(">"):
            in_toc_section = False
            quote_text = stripped.lstrip("> ").strip()
            formatted_quote = _format_inline_markdown(quote_text)
            callout_box = Table(
                [[Paragraph(formatted_quote, callout_style)]],
                colWidths=[522]
            )
            callout_box.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
                ('LINELEFT', (0,0), (0,0), 3.0, colors.HexColor("#2563eb")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(KeepTogether(callout_box))
            story.append(Spacer(1, 4))
            i += 1
            continue

        # 6. Bullets (- or * or numbered 1.)
        bullet_match = re.match(r"^(\*|-|\d+\.)\s+(.+)$", stripped)
        if bullet_match:
            bullet_body = bullet_match.group(2)
            bullet_sym = "• " if bullet_match.group(1) in ("*", "-") else f"{bullet_match.group(1)} "
            formatted_bullet = _format_inline_markdown(bullet_sym + bullet_body)
            use_style = toc_item_style if in_toc_section else bullet_style
            story.append(Paragraph(formatted_bullet, use_style))
            i += 1
            continue

        # 7. Standard Paragraph
        in_toc_section = False
        formatted_paragraph = _format_inline_markdown(stripped)
        story.append(Paragraph(formatted_paragraph, body_style))
        i += 1

    # Build Document with NumberedCanvas
    def _canvas_factory(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.article_title = title
        return c

    doc.build(story, canvasmaker=_canvas_factory)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
