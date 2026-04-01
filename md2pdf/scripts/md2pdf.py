#!/usr/bin/env python3
"""
md2pdf — Convert Markdown to professionally typeset PDF.

Features:
  - CJK/Latin mixed text with automatic font switching
  - Fenced code blocks with preserved indentation and line breaks
  - Markdown tables with smart proportional column widths
  - Cover page, clickable TOC, PDF bookmarks, page numbers
  - Frontispiece (full-page image after cover) and back cover (banner branding)
  - Configurable color themes
  - Watermark support
  - Running header with report title + chapter name
  - Footer with author/brand, page number, date

Usage:
  python md2pdf.py --input report.md --output report.pdf --title "My Report"

Dependencies:
  pip install reportlab --break-system-packages
"""

import re, os, sys, json, argparse
from datetime import date
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Table, TableStyle, NextPageTemplate, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ═══════════════════════════════════════════════════════════════════════
# FONTS — register system fonts (adjust paths if on different OS)
# ═══════════════════════════════════════════════════════════════════════
import platform as _platform
_IS_MAC = _platform.system() == "Darwin"

# macOS: Palatino (book serif), Songti SC (CJK serif), Menlo (code), Arial (sans)
# Linux: Liberation/Carlito/Droid/DejaVu fallbacks
FONT_PATHS_MAC = {
    "Sans":     "/System/Library/Fonts/Supplemental/Arial.ttf",
    "SansBold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "SansIt":   "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
    "SansBI":   "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
    "Serif":    ("/System/Library/Fonts/Palatino.ttc", 0),
    "SerifBold":("/System/Library/Fonts/Palatino.ttc", 2),
    "SerifIt":  ("/System/Library/Fonts/Palatino.ttc", 1),
    "SerifBI":  ("/System/Library/Fonts/Palatino.ttc", 3),
    "CJK":      ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),    # Songti SC Regular
    "CJKBold":  ("/System/Library/Fonts/Supplemental/Songti.ttc", 1),    # Songti SC Bold
    "Mono":     ("/System/Library/Fonts/Menlo.ttc", 0),
    "MonoBold": ("/System/Library/Fonts/Menlo.ttc", 1),
}
FONT_PATHS_LINUX = {
    "Sans":     "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",
    "SansBold": "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf",
    "SansIt":   "/usr/share/fonts/truetype/crosextra/Carlito-Italic.ttf",
    "SansBI":   "/usr/share/fonts/truetype/crosextra/Carlito-BoldItalic.ttf",
    "Serif":    "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    "SerifBold":"/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
    "SerifIt":  "/usr/share/fonts/truetype/liberation2/LiberationSerif-Italic.ttf",
    "SerifBI":  "/usr/share/fonts/truetype/liberation2/LiberationSerif-BoldItalic.ttf",
    "CJK":      "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "Mono":     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "MonoBold": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}

def register_fonts():
    font_map = FONT_PATHS_MAC if _IS_MAC else FONT_PATHS_LINUX
    for name, spec in font_map.items():
        try:
            if isinstance(spec, tuple):
                path, idx = spec
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
            else:
                pdfmetrics.registerFont(TTFont(name, spec))
        except Exception as e:
            print(f"Warning: Font {name} — {e}", file=sys.stderr)
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="SansBold",
                                  italic="SansIt", boldItalic="SansBI")
    pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="SerifBold",
                                  italic="SerifIt", boldItalic="SerifBI")

# ═══════════════════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════════════════
THEMES = {
    "warm-academic": {
        "canvas":"#F9F9F7","canvas_sec":"#F0EEE6","ink":"#181818","ink_faded":"#87867F",
        "accent":"#CC785C","accent_light":"#D99A82","border":"#E8E6DC",
        "watermark_rgba":(0.82,0.80,0.76,0.12)
    },
    "nord-frost": {
        "canvas":"#ECEFF4","canvas_sec":"#E5E9F0","ink":"#2E3440","ink_faded":"#4C566A",
        "accent":"#5E81AC","accent_light":"#81A1C1","border":"#D8DEE9",
        "watermark_rgba":(0.74,0.78,0.85,0.10)
    },
    "github-light": {
        "canvas":"#FFFFFF","canvas_sec":"#F6F8FA","ink":"#1F2328","ink_faded":"#656D76",
        "accent":"#0969DA","accent_light":"#218BFF","border":"#D0D7DE",
        "watermark_rgba":(0.80,0.82,0.85,0.08)
    },
    "solarized-light": {
        "canvas":"#FDF6E3","canvas_sec":"#EEE8D5","ink":"#657B83","ink_faded":"#93A1A1",
        "accent":"#CB4B16","accent_light":"#DC322F","border":"#EEE8D5",
        "watermark_rgba":(0.85,0.82,0.72,0.10)
    },
    "paper-classic": {
        "canvas":"#FFFFFF","canvas_sec":"#FAFAFA","ink":"#000000","ink_faded":"#666666",
        "accent":"#CC0000","accent_light":"#FF3333","border":"#DDDDDD",
        "watermark_rgba":(0.85,0.85,0.85,0.08)
    },
    "ocean-breeze": {
        "canvas":"#F0F7F4","canvas_sec":"#E0EDE8","ink":"#1A2E35","ink_faded":"#5A7D7C",
        "accent":"#2A9D8F","accent_light":"#64CCBF","border":"#C8DDD6",
        "watermark_rgba":(0.75,0.85,0.80,0.10)
    },
    "monokai-warm": {
        "canvas":"#272822","canvas_sec":"#1E1F1C","ink":"#F8F8F2","ink_faded":"#75715E",
        "accent":"#F92672","accent_light":"#FD971F","border":"#49483E",
        "watermark_rgba":(0.30,0.30,0.28,0.08)
    },
    "dracula-soft": {
        "canvas":"#282A36","canvas_sec":"#21222C","ink":"#F8F8F2","ink_faded":"#6272A4",
        "accent":"#BD93F9","accent_light":"#FF79C6","border":"#44475A",
        "watermark_rgba":(0.35,0.30,0.45,0.08)
    },
}

def load_theme(name, theme_file=None):
    if theme_file and os.path.exists(theme_file):
        with open(theme_file) as f:
            t = json.load(f)
    elif name in THEMES:
        t = THEMES[name]
    else:
        print(f"Unknown theme '{name}', falling back to warm-academic", file=sys.stderr)
        t = THEMES["warm-academic"]
    return {
        "canvas":    HexColor(t["canvas"]),
        "canvas_sec":HexColor(t["canvas_sec"]),
        "ink":       HexColor(t["ink"]),
        "ink_faded": HexColor(t["ink_faded"]),
        "accent":    HexColor(t["accent"]),
        "accent_light":HexColor(t.get("accent_light", t["accent"])),
        "border":    HexColor(t["border"]),
        "wm_color":  Color(*t.get("watermark_rgba", (0.82,0.80,0.76,0.12))),
    }

# ═══════════════════════════════════════════════════════════════════════
# CJK DETECTION + FONT WRAPPING
# ═══════════════════════════════════════════════════════════════════════
_CJK_RANGES = [
    (0x4E00,0x9FFF),(0x3400,0x4DBF),(0xF900,0xFAFF),(0x3000,0x303F),
    (0xFF00,0xFFEF),(0x2E80,0x2EFF),(0x2F00,0x2FDF),(0xFE30,0xFE4F),
    (0x20000,0x2A6DF),(0x2A700,0x2B73F),(0x2B740,0x2B81F),
]

def _is_cjk(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _CJK_RANGES)

def _font_wrap(text):
    """Wrap CJK runs in <font name='CJK'> tags for reportlab Paragraph."""
    out, buf, in_cjk = [], [], False
    for ch in text:
        c = _is_cjk(ch)
        if c != in_cjk and buf:
            seg = ''.join(buf)
            out.append(f"<font name='CJK'>{seg}</font>" if in_cjk else seg)
            buf = []
        buf.append(ch); in_cjk = c
    if buf:
        seg = ''.join(buf)
        out.append(f"<font name='CJK'>{seg}</font>" if in_cjk else seg)
    return ''.join(out)

def _draw_mixed(c, x, y, text, size, anchor="left"):
    """Draw mixed CJK/Latin text on canvas with font switching."""
    segs, buf, in_cjk = [], [], False
    for ch in text:
        cj = _is_cjk(ch)
        if cj != in_cjk and buf:
            segs.append(("CJK" if in_cjk else "Sans", ''.join(buf))); buf = []
        buf.append(ch); in_cjk = cj
    if buf: segs.append(("CJK" if in_cjk else "Sans", ''.join(buf)))
    total_w = sum(c.stringWidth(t, f, size) for f, t in segs)
    if anchor == "right": x -= total_w
    elif anchor == "center": x -= total_w / 2
    for font, txt in segs:
        c.setFont(font, size); c.drawString(x, y, txt)
        x += c.stringWidth(txt, font, size)

def _draw_mixed_segs(c, x, y, segs):
    """Draw pre-defined (font, text, size) segments on canvas.
    Used for mixed-font subtitle rendering."""
    total_w = sum(c.stringWidth(txt, font, sz) for font, txt, sz in segs)
    x = x - total_w / 2  # always centered
    for font, txt, sz in segs:
        c.setFont(font, sz)
        c.drawString(x, y, txt)
        x += c.stringWidth(txt, font, sz)

# ═══════════════════════════════════════════════════════════════════════
# INLINE MARKDOWN + ESCAPING
# ═══════════════════════════════════════════════════════════════════════
def esc(text):
    return text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def esc_code(text):
    """Escape for code blocks: preserve indentation and newlines."""
    out = []
    for line in text.split('\n'):
        e = esc(line)
        stripped = e.lstrip(' ')
        indent = len(e) - len(stripped)
        out.append('&nbsp;' * indent + stripped)
    return '<br/>'.join(out)

def md_inline(text, accent_hex="#CC785C"):
    text = esc(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`(.+?)`',
        rf"<font name='Mono' size='8' color='{accent_hex}'>\1</font>", text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'<u>\1</u>', text)
    return _font_wrap(text)

# ═══════════════════════════════════════════════════════════════════════
# CUSTOM FLOWABLES
# ═══════════════════════════════════════════════════════════════════════
_anchor_counter = [0]
_outline_level = [-1]
_cur_chapter = [""]

class ChapterMark(Flowable):
    width = height = 0
    def __init__(self, t, level=0):
        Flowable.__init__(self); self.title = t; self.level = level
        _anchor_counter[0] += 1; self.key = f"anchor_{_anchor_counter[0]}"
    def draw(self):
        _cur_chapter[0] = self.title
        self.canv.bookmarkPage(self.key)
        target = min(self.level, _outline_level[0] + 1)
        _outline_level[0] = target
        self.canv.addOutlineEntry(self.title, self.key, level=target, closed=(target==0))

class HRule(Flowable):
    def __init__(self, w, thick=0.5, clr=None):
        Flowable.__init__(self)
        self.width = w; self.height = 4*mm; self._t = thick; self._c = clr or HexColor("#E8E6DC")
    def draw(self):
        self.canv.setStrokeColor(self._c); self.canv.setLineWidth(self._t)
        self.canv.line(0, 2*mm, self.width, 2*mm)

class HRuleCentered(Flowable):
    """Horizontally centered rule within the frame width."""
    def __init__(self, frame_w, rule_w, thick=0.5, clr=None):
        Flowable.__init__(self)
        self.width = frame_w; self.height = 4*mm
        self._rw = rule_w; self._t = thick; self._c = clr or HexColor("#E8E6DC")
    def draw(self):
        self.canv.setStrokeColor(self._c); self.canv.setLineWidth(self._t)
        x0 = (self.width - self._rw) / 2
        self.canv.line(x0, 2*mm, x0 + self._rw, 2*mm)

class ClayDot(Flowable):
    """Small accent-colored dot separator."""
    def __init__(self, w, clr=None):
        Flowable.__init__(self)
        self.width = w; self.height = 6*mm
        self._c = clr or HexColor("#CC785C")
    def draw(self):
        self.canv.setFillColor(self._c)
        cx = self.width / 2
        self.canv.circle(cx, 3*mm, 1.5*mm, fill=1, stroke=0)

# ═══════════════════════════════════════════════════════════════════════
# PDF BUILDER
# ═══════════════════════════════════════════════════════════════════════
class PDFBuilder:
    def __init__(self, config):
        self.cfg = config
        self.T = config["theme"]  # resolved theme colors
        self.page_w, self.page_h = config["page_size"]
        self.lm, self.rm, self.tm, self.bm = 25*mm, 22*mm, 28*mm, 25*mm
        self.body_w = self.page_w - self.lm - self.rm
        self.body_h = self.page_h - self.tm - self.bm
        self.accent_hex = config.get("accent_hex", "#CC785C")
        self.ST = self._build_styles()

    def _build_styles(self):
        T = self.T
        s = {}
        s['part'] = ParagraphStyle('Part', fontName="Serif", fontSize=26, leading=36,
            textColor=T["ink"], alignment=TA_CENTER, spaceBefore=0, spaceAfter=0)
        s['chapter'] = ParagraphStyle('Ch', fontName="Serif", fontSize=18, leading=26,
            textColor=T["ink"], alignment=TA_CENTER, spaceBefore=0, spaceAfter=0)
        s['h3'] = ParagraphStyle('H3', fontName="SansBold", fontSize=12, leading=17,
            textColor=T["accent"], alignment=TA_LEFT, spaceBefore=10, spaceAfter=4)
        s['body'] = ParagraphStyle('Body', fontName="Serif", fontSize=10.5, leading=17,
            textColor=T["ink"], alignment=TA_JUSTIFY, spaceBefore=2, spaceAfter=4,
            wordWrap='CJK')
        s['body_indent'] = ParagraphStyle('BI', parent=s['body'],
            leftIndent=14, rightIndent=14, textColor=T["ink_faded"],
            borderColor=T["accent"], borderWidth=0, borderPadding=4)
        s['bullet'] = ParagraphStyle('Bul', fontName="Serif", fontSize=10.5, leading=17,
            textColor=T["ink"], alignment=TA_LEFT, spaceBefore=1, spaceAfter=1,
            leftIndent=18, bulletIndent=6, wordWrap='CJK')
        s['code'] = ParagraphStyle('Code', fontName="Mono", fontSize=7.5, leading=10.5,
            textColor=HexColor("#3D3D3A"), alignment=TA_LEFT, spaceBefore=4, spaceAfter=4,
            leftIndent=8, rightIndent=8, backColor=T["canvas_sec"],
            borderColor=T["border"], borderWidth=0.5, borderPadding=6)
        s['toc1'] = ParagraphStyle('T1', fontName="Serif", fontSize=12, leading=20,
            textColor=T["ink"], leftIndent=0, spaceBefore=6, spaceAfter=2)
        s['toc2'] = ParagraphStyle('T2', fontName="Sans", fontSize=10, leading=16,
            textColor=T["ink_faded"], leftIndent=16, spaceBefore=1, spaceAfter=1)
        s['th'] = ParagraphStyle('TH', fontName="SansBold", fontSize=8.5, leading=12,
            textColor=white, alignment=TA_CENTER)
        s['tc'] = ParagraphStyle('TC', fontName="Sans", fontSize=8, leading=11,
            textColor=T["ink"], alignment=TA_LEFT)
        return s

    # ── Page callbacks ──
    def _draw_bg(self, c):
        c.setFillColor(self.T["canvas"])
        c.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

    def _cover_page(self, c, doc):
        c.saveState(); self._draw_bg(c)
        T = self.T; cx = self.page_w / 2

        # Top accent bar
        c.setFillColor(T["accent"])
        c.rect(0, self.page_h - 3*mm, self.page_w, 3*mm, fill=1, stroke=0)

        # Main title — centered in upper-mid area
        title_y = self.page_h * 0.62
        c.setFillColor(T["ink"])
        _draw_mixed(c, cx, title_y, self.cfg.get("title", "Document"), 38, anchor="center")

        # Version tag below title
        ver = self.cfg.get("version", "")
        if ver:
            c.setFillColor(T["accent"]); c.setFont("Sans", 13)
            c.drawCentredString(cx, title_y - 30, ver)

        # Short accent rule
        rule_y = title_y - 52
        c.setStrokeColor(T["accent"]); c.setLineWidth(1.5)
        c.line(cx - 17*mm, rule_y, cx + 17*mm, rule_y)

        # Subtitle — supports mixed-font segments via subtitle_segs config
        sub = self.cfg.get("subtitle", "")
        sub_segs = self.cfg.get("subtitle_segs")  # list of (font, text, size) tuples
        if sub_segs:
            c.setFillColor(T["ink_faded"])
            _draw_mixed_segs(c, cx, rule_y - 32, sub_segs)
        elif sub:
            c.setFillColor(T["ink"])
            _draw_mixed(c, cx, rule_y - 32, sub, 20, anchor="center")

        # Stats line (optional) — e.g. "1,884 files · 394,222 lines · 54 tools"
        stats = self.cfg.get("stats_line", "")
        stats2 = self.cfg.get("stats_line2", "")
        if stats or stats2:
            c.setFillColor(T["ink_faded"])
            stats_y = rule_y - 72
            if stats:
                _draw_mixed(c, cx, stats_y, stats, 9.5, anchor="center")
            if stats2:
                _draw_mixed(c, cx, stats_y - 18, stats2, 9.5, anchor="center")

        # Bottom area — thin border rule
        c.setStrokeColor(T["border"]); c.setLineWidth(0.5)
        c.line(self.lm + 20*mm, 52*mm, self.page_w - self.rm - 20*mm, 52*mm)

        # Author — centered
        author = self.cfg.get("author", "")
        if author:
            c.setFillColor(T["ink_faded"])
            _draw_mixed(c, cx, 38*mm, author, 10, anchor="center")

        # Date — centered below
        dt = self.cfg.get("date", str(date.today()))
        c.setFillColor(T["ink_faded"])
        _draw_mixed(c, cx, 28*mm, dt, 9, anchor="center")

        # Edition line (optional) — e.g. "v0.019 · 30+ Chapters · 6 Appendices"
        edition = self.cfg.get("edition_line", "")
        if edition:
            c.setFillColor(T["ink_faded"])
            _draw_mixed(c, cx, 20*mm, edition, 7.5, anchor="center")

        # Bottom accent bar
        c.setFillColor(T["accent"])
        c.rect(0, 0, self.page_w, 3*mm, fill=1, stroke=0)

        c.restoreState()

    def _frontispiece_page(self, c, doc):
        """Full-page image page after cover."""
        c.saveState(); self._draw_bg(c)
        fp = self.cfg.get("frontispiece", "")
        if fp and os.path.exists(fp):
            margin = 18*mm
            avail_w = self.page_w - 2 * margin
            avail_h = self.page_h - 2 * margin
            try:
                c.drawImage(fp, margin, margin, width=avail_w, height=avail_h,
                            preserveAspectRatio=True, anchor='c', mask='auto')
            except Exception:
                pass
        c.restoreState()

    def _backcover_page(self, c, doc):
        """Back cover with banner branding."""
        c.saveState(); self._draw_bg(c)
        T = self.T; cx = self.page_w / 2

        # Top accent
        c.setFillColor(T["accent"])
        c.rect(0, self.page_h - 3*mm, self.page_w, 3*mm, fill=1, stroke=0)

        # Banner image — centered
        banner = self.cfg.get("banner", "")
        if banner and os.path.exists(banner):
            cy = self.page_h / 2
            banner_w = 150*mm
            banner_h = banner_w / 2.57
            banner_x = (self.page_w - banner_w) / 2
            banner_y = cy - banner_h / 2 + 15*mm
            try:
                c.drawImage(banner, banner_x, banner_y, width=banner_w,
                            height=banner_h, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        # Bottom disclaimer
        disclaimer = self.cfg.get("disclaimer", "")
        if disclaimer:
            c.setFillColor(T["ink_faded"])
            _draw_mixed(c, cx, 32*mm, disclaimer, 8.5, anchor="center")

        # Copyright
        copyright_text = self.cfg.get("copyright", "")
        if copyright_text:
            c.setFillColor(T["ink_faded"])
            _draw_mixed(c, cx, 20*mm, copyright_text, 8.5, anchor="center")

        # Bottom accent
        c.setFillColor(T["accent"])
        c.rect(0, 0, self.page_w, 3*mm, fill=1, stroke=0)

        c.restoreState()

    def _normal_page(self, c, doc):
        self._draw_bg(c); pg = c.getPageNumber()
        c.saveState()
        T = self.T

        # Watermark
        wm = self.cfg.get("watermark", "")
        if wm:
            c.setFont("CJK", 52); c.setFillColor(T["wm_color"])
            c.translate(self.page_w/2, self.page_h/2); c.rotate(35)
            for dy in range(-300, 400, 160):
                for dx in range(-400, 500, 220):
                    c.drawCentredString(dx, dy, wm)
            c.rotate(-35); c.translate(-self.page_w/2, -self.page_h/2)

        # Header line
        c.setStrokeColor(T["border"]); c.setLineWidth(0.5)
        c.line(self.lm, self.page_h - 20*mm, self.page_w - self.rm, self.page_h - 20*mm)
        c.setFillColor(T["ink_faded"])

        # Header left: report title (if provided)
        header_title = self.cfg.get("header_title", "")
        if header_title:
            _draw_mixed(c, self.lm, self.page_h - 18*mm, header_title, 8)

        # Header right: current chapter name
        ch = _cur_chapter[0]
        if ch:
            _draw_mixed(c, self.page_w - self.rm, self.page_h - 18*mm, ch[:40], 8, anchor="right")

        # Footer line
        c.setStrokeColor(T["border"])
        c.line(self.lm, self.bm - 8*mm, self.page_w - self.rm, self.bm - 8*mm)

        # Footer center: page number with accent
        c.setFillColor(T["accent"]); c.setFont("Serif", 9)
        c.drawCentredString(self.page_w/2, self.bm - 16*mm, f"\u2014  {pg}  \u2014")

        # Footer left: author/brand (if provided)
        footer_left = self.cfg.get("footer_left", self.cfg.get("author", ""))
        if footer_left:
            c.setFillColor(T["ink_faded"])
            _draw_mixed(c, self.lm, self.bm - 16*mm, footer_left, 8)

        # Footer right: date
        c.setFillColor(T["ink_faded"])
        _draw_mixed(c, self.page_w - self.rm, self.bm - 16*mm,
                    self.cfg.get("date", str(date.today())), 8, anchor="right")
        c.restoreState()

    def _toc_page(self, c, doc):
        self._draw_bg(c); pg = c.getPageNumber()
        c.saveState()
        T = self.T

        # Header line
        c.setStrokeColor(T["border"]); c.setLineWidth(0.5)
        c.line(self.lm, self.page_h - 20*mm, self.page_w - self.rm, self.page_h - 20*mm)
        c.setFillColor(T["ink_faded"])

        # Header left: report title
        header_title = self.cfg.get("header_title", "")
        if header_title:
            _draw_mixed(c, self.lm, self.page_h - 18*mm, header_title, 8)

        # Header right: "目  录"
        c.setFont("CJK", 8)
        c.drawRightString(self.page_w - self.rm, self.page_h - 18*mm, "\u76ee  \u5f55")

        # Footer
        c.setStrokeColor(T["border"])
        c.line(self.lm, self.bm - 8*mm, self.page_w - self.rm, self.bm - 8*mm)
        c.setFillColor(T["accent"]); c.setFont("Serif", 9)
        c.drawCentredString(self.page_w/2, self.bm - 16*mm, f"\u2014  {pg}  \u2014")

        c.restoreState()

    # ── Table parser ──
    def parse_table(self, lines):
        rows = []
        for l in lines:
            l = l.strip().strip('|')
            rows.append([c.strip() for c in l.split('|')])
        if len(rows) < 2: return None
        header = rows[0]
        data = [r for r in rows[1:] if not all(set(c.strip()) <= set('-: ') for c in r)]
        if not data: return None
        nc = len(header)
        ST = self.ST
        td = [[Paragraph(md_inline(h, self.accent_hex), ST['th']) for h in header]]
        for r in data:
            while len(r) < nc: r.append("")
            td.append([Paragraph(md_inline(c, self.accent_hex), ST['tc']) for c in r[:nc]])
        avail = self.body_w - 4*mm
        max_lens = [max((len(r[ci]) if ci < len(r) else 0) for r in [header]+data) for ci in range(nc)]
        max_lens = [max(m, 2) for m in max_lens]
        total = sum(max_lens)
        cw = [avail * m / total for m in max_lens]
        min_w = 18*mm
        for ci in range(nc):
            if cw[ci] < min_w:
                deficit = min_w - cw[ci]; cw[ci] = min_w
                widest = sorted(range(nc), key=lambda x: -cw[x])
                for oi in widest:
                    if oi != ci: cw[oi] -= deficit; break
        T = self.T
        t = Table(td, colWidths=cw, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), T["accent"]),
            ('TEXTCOLOR',(0,0),(-1,0), white),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [white, T["canvas_sec"]]),
            ('GRID',(0,0),(-1,-1), 0.5, T["border"]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ]))
        return t

    # ── Markdown → Story ──
    @staticmethod
    def _preprocess_md(md):
        """Normalize markdown: split merged headings like '# Part## Chapter'."""
        lines = md.split('\n')
        out = []
        in_code = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code = not in_code
            if in_code:
                out.append(line); continue
            # Split where a non-# char is followed by ## (heading marker)
            # e.g. "# 第一部分：背景与概览## 第1章" or "---## 第2章"
            parts = re.split(r'(?<=[^#\s])\s*(?=#{1,3}\s)', line)
            if len(parts) > 1:
                for p in parts:
                    p = p.strip()
                    if p:
                        out.append(p)
            else:
                out.append(line)
        return '\n'.join(out)

    def parse_md(self, md):
        story, toc = [], []
        md = self._preprocess_md(md)
        lines = md.split('\n')
        i, in_code, code_buf = 0, False, []
        ST = self.ST; ah = self.accent_hex
        code_max = self.cfg.get("code_max_lines", 30)

        while i < len(lines):
            line = lines[i]; stripped = line.strip()
            # Code blocks
            if stripped.startswith('```'):
                if in_code:
                    ct = '\n'.join(code_buf)
                    if ct.strip():
                        cl = ct.split('\n')
                        if len(cl) > code_max:
                            cl = cl[:code_max - 2] + ['  // ... (truncated)']
                            ct = '\n'.join(cl)
                        story.append(Paragraph(_font_wrap(esc_code(ct)), ST['code']))
                    code_buf = []; in_code = False
                else: in_code = True; code_buf = []
                i += 1; continue
            if in_code: code_buf.append(line); i += 1; continue
            if stripped in ('---','\\newpage','') or stripped.startswith(('title:','subtitle:','author:','date:')):
                i += 1; continue

            # H1 — Part heading: full divider page, vertically + horizontally centered
            if re.match(r'^# (第.+部分|附录)', stripped) or \
               (re.match(r'^# .+', stripped) and not stripped.startswith('## ')):
                if re.match(r'^# .+', stripped):
                    title = stripped.lstrip('#').strip()
                    story.append(PageBreak())
                    cm = ChapterMark(title, level=0); story.append(cm)
                    # Vertically center: push content to ~40% from top
                    story.append(Spacer(1, self.body_h * 0.35))
                    story.append(HRuleCentered(self.body_w, 40*mm, 0.8, self.T["accent"]))
                    story.append(Spacer(1, 8*mm))
                    story.append(Paragraph(md_inline(title, ah), ST['part']))
                    story.append(Spacer(1, 8*mm))
                    story.append(HRuleCentered(self.body_w, 25*mm, 0.8, self.T["accent"]))
                    toc.append(('part', title, cm.key))
                    i += 1; continue

            # H2 — Chapter heading: centered with accent decoration
            if stripped.startswith('## '):
                title = stripped[3:].strip()
                story.append(PageBreak())
                cm = ChapterMark(title, level=1); story.append(cm)
                story.append(Spacer(1, self.body_h * 0.30))
                story.append(Paragraph(md_inline(title, ah), ST['chapter']))
                story.append(Spacer(1, 5*mm))
                story.append(HRuleCentered(self.body_w, 35*mm, 1.2, self.T["accent"]))
                toc.append(('chapter', title, cm.key))
                i += 1; continue

            # H3 = Section
            if stripped.startswith('### '):
                story.append(Spacer(1, 3*mm))
                story.append(Paragraph(md_inline(stripped[4:].strip(), ah), ST['h3']))
                story.append(Spacer(1, 1*mm))
                i += 1; continue

            # Tables
            if stripped.startswith('|'):
                tl = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    tl.append(lines[i]); i += 1
                t = self.parse_table(tl)
                if t: story.append(Spacer(1,2*mm)); story.append(t); story.append(Spacer(1,2*mm))
                continue

            # Bullets
            if stripped.startswith('- ') or stripped.startswith('* '):
                story.append(Paragraph(f"\u2022  {md_inline(stripped[2:].strip(), ah)}", ST['bullet']))
                i += 1; continue

            # Numbered list
            m = re.match(r'^(\d+)\.\s+(.+)', stripped)
            if m:
                story.append(Paragraph(f"{m.group(1)}.  {md_inline(m.group(2), ah)}", ST['bullet']))
                i += 1; continue

            # Blockquote
            if stripped.startswith('> '):
                story.append(Paragraph(md_inline(stripped[2:].strip(), ah), ST['body_indent']))
                i += 1; continue

            # Paragraph — join consecutive lines; skip space between CJK characters
            plines = []
            while i < len(lines):
                l = lines[i].strip()
                if not l or l.startswith('#') or l.startswith('```') or l.startswith('|') or \
                   l.startswith('- ') or l.startswith('* ') or l.startswith('> ') or re.match(r'^\d+\.\s', l):
                    break
                plines.append(l); i += 1
            if plines:
                merged = plines[0]
                for pl in plines[1:]:
                    # If prev line ends with CJK and next starts with CJK, join directly (no space)
                    if merged and pl and _is_cjk(merged[-1]) and _is_cjk(pl[0]):
                        merged += pl
                    else:
                        merged += ' ' + pl
                story.append(Paragraph(md_inline(merged, ah), ST['body']))
            continue

        return story, toc

    def build_toc(self, toc):
        ST = self.ST; ah = self.accent_hex; ink = self.T["ink"]
        s = [Spacer(1, 15*mm)]
        s.append(Paragraph(md_inline("\u76ee    \u5f55", ah), ST['part']))
        s.append(HRule(self.body_w * 0.12, 1, self.T["accent"]))
        s.append(Spacer(1, 8*mm))
        ink_hex = f"#{int(ink.red*255):02x}{int(ink.green*255):02x}{int(ink.blue*255):02x}" if hasattr(ink,'red') else "#181818"
        for etype, title, key in toc:
            style = ST['toc1'] if etype == 'part' else ST['toc2']
            linked = f"<a href=\"#{key}\" color=\"{ink_hex}\">{_font_wrap(esc(title))}</a>"
            s.append(Paragraph(linked, style))
        return s

    # ── Build PDF ──
    def build(self, md_text, output_path):
        register_fonts()
        print("Parsing markdown...")
        story_content, toc = self.parse_md(md_text)
        print(f"  {len(story_content)} elements, {len(toc)} TOC entries")

        body_frame = Frame(self.lm, self.bm, self.body_w, self.body_h, id='body')
        full_frame = Frame(0, 0, self.page_w, self.page_h, leftPadding=0,
                           rightPadding=0, topPadding=0, bottomPadding=0, id='full')

        doc = BaseDocTemplate(output_path, pagesize=(self.page_w, self.page_h),
                              leftMargin=self.lm, rightMargin=self.rm,
                              topMargin=self.tm, bottomMargin=self.bm,
                              title=self.cfg.get("title", ""),
                              author=self.cfg.get("author", ""))

        templates = [
            PageTemplate(id='normal', frames=[body_frame], onPage=self._normal_page),
        ]

        story = []
        has_frontis = self.cfg.get("frontispiece") and os.path.exists(self.cfg["frontispiece"])
        has_banner = self.cfg.get("banner") and os.path.exists(self.cfg["banner"])
        has_toc = self.cfg.get("toc", True) and toc

        # Cover page
        if self.cfg.get("cover", True):
            templates.insert(0, PageTemplate(id='cover', frames=[full_frame], onPage=self._cover_page))
            story.append(Spacer(1, self.page_h))

            # Determine next page after cover
            if has_frontis:
                templates.append(PageTemplate(id='frontis', frames=[full_frame], onPage=self._frontispiece_page))
                story.append(NextPageTemplate('frontis'))
                story.append(PageBreak())
                story.append(Spacer(1, self.page_h))
                # After frontispiece, go to toc or normal
                if has_toc:
                    templates.append(PageTemplate(id='toc', frames=[body_frame], onPage=self._toc_page))
                    story.append(NextPageTemplate('toc'))
                else:
                    story.append(NextPageTemplate('normal'))
                story.append(PageBreak())
            elif has_toc:
                templates.append(PageTemplate(id='toc', frames=[body_frame], onPage=self._toc_page))
                story.append(NextPageTemplate('toc'))
                story.append(PageBreak())
            else:
                story.append(NextPageTemplate('normal'))
                story.append(PageBreak())
        elif has_toc:
            templates.append(PageTemplate(id='toc', frames=[body_frame], onPage=self._toc_page))
            story.append(NextPageTemplate('toc'))

        # TOC
        if has_toc:
            story.extend(self.build_toc(toc))
            story.append(NextPageTemplate('normal'))
            story.append(PageBreak())

        # Strip leading PageBreak from body content to avoid blank page
        while story_content and isinstance(story_content[0], (PageBreak, Spacer)):
            if isinstance(story_content[0], PageBreak):
                story_content.pop(0)
                break
            story_content.pop(0)

        story.extend(story_content)

        # Back cover
        if has_banner:
            templates.append(PageTemplate(id='backcover', frames=[full_frame], onPage=self._backcover_page))
            story.append(NextPageTemplate('backcover'))
            story.append(PageBreak())
            story.append(Spacer(1, 1))

        doc.addPageTemplates(templates)
        print("Building PDF...")
        doc.build(story)
        size = os.path.getsize(output_path)
        print(f"Done! {output_path} ({size/1024/1024:.1f} MB)")

# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="md2pdf \u2014 Markdown to Professional PDF")
    parser.add_argument("--input", "-i", required=True, help="Input markdown file")
    parser.add_argument("--output", "-o", default="output.pdf", help="Output PDF path")
    parser.add_argument("--title", default="", help="Cover page title")
    parser.add_argument("--subtitle", default="", help="Cover page subtitle")
    parser.add_argument("--author", default="", help="Author name")
    parser.add_argument("--date", default=str(date.today()), help="Date string")
    parser.add_argument("--version", default="", help="Version string on cover")
    parser.add_argument("--watermark", default="", help="Watermark text (empty = none)")
    parser.add_argument("--theme", default="warm-academic", help="Theme name")
    parser.add_argument("--theme-file", default=None, help="Custom theme JSON file path")
    parser.add_argument("--cover", default=True, type=lambda x: x.lower() != 'false', help="Generate cover page")
    parser.add_argument("--toc", default=True, type=lambda x: x.lower() != 'false', help="Generate TOC")
    parser.add_argument("--page-size", default="A4", choices=["A4","Letter"], help="Page size")
    parser.add_argument("--frontispiece", default="", help="Path to full-page image after cover")
    parser.add_argument("--banner", default="", help="Path to back cover banner image")
    parser.add_argument("--header-title", default="", help="Report title shown in page header (left)")
    parser.add_argument("--footer-left", default="", help="Brand/author text in footer (left)")
    parser.add_argument("--stats-line", default="", help="Stats line on cover (e.g. '1,884 files ...')")
    parser.add_argument("--stats-line2", default="", help="Second stats line on cover")
    parser.add_argument("--edition-line", default="", help="Edition line at cover bottom")
    parser.add_argument("--disclaimer", default="", help="Back cover disclaimer text")
    parser.add_argument("--copyright", default="", help="Back cover copyright text")
    parser.add_argument("--code-max-lines", default=30, type=int, help="Max lines per code block before truncation")
    args = parser.parse_args()

    with open(args.input, encoding='utf-8') as f:
        md_text = f.read()

    # Extract title from first H1 if not provided
    title = args.title
    if not title:
        m = re.search(r'^# (.+)$', md_text, re.MULTILINE)
        title = m.group(1).strip() if m else "Document"

    theme = load_theme(args.theme, args.theme_file)
    a = theme['accent']
    accent_hex = f"#{int(a.red*255):02x}{int(a.green*255):02x}{int(a.blue*255):02x}" \
        if hasattr(a, 'red') else "#CC785C"

    config = {
        "title": title,
        "subtitle": args.subtitle,
        "author": args.author,
        "date": args.date,
        "version": args.version,
        "watermark": args.watermark,
        "theme": theme,
        "accent_hex": accent_hex,
        "cover": args.cover,
        "toc": args.toc,
        "page_size": A4 if args.page_size == "A4" else LETTER,
        "frontispiece": args.frontispiece,
        "banner": args.banner,
        "header_title": args.header_title,
        "footer_left": args.footer_left or args.author,
        "stats_line": args.stats_line,
        "stats_line2": args.stats_line2,
        "edition_line": args.edition_line,
        "disclaimer": args.disclaimer,
        "copyright": args.copyright,
        "code_max_lines": args.code_max_lines,
    }

    builder = PDFBuilder(config)
    builder.build(md_text, args.output)

if __name__ == "__main__":
    main()
