from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, PageBreak, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import re

W, H = A4

# ── Themenfarben ─────────────────────────────────────────────────────────────
SECTIONS = [
    ("GRUNDLAGEN IT",                  "#1A6B3C"),
    ("TECHNISCHE INFORMATIK",          "#1A4A8A"),
    ("BETRIEBSSYSTEME & RECHNERNETZE", "#7B3F00"),
    ("DATENBANKEN",                    "#6B1A6B"),
    ("OOP",                            "#8A1A1A"),
    ("SYSTEMANALYSE",                  "#1A6B6B"),
    ("ELEKTRONIK",                     "#5A5A00"),
]

def section_color(title):
    for name, hex_col in SECTIONS:
        if name in title.upper():
            return colors.HexColor(hex_col)
    return colors.HexColor("#333333")

def lighten(col, factor=0.88):
    """Helle Version einer Farbe (für Unterabschnitt-Hintergrund)."""
    r = int(col.red   * (1 - factor) * 255 + factor * 255)
    g = int(col.green * (1 - factor) * 255 + factor * 255)
    b = int(col.blue  * (1 - factor) * 255 + factor * 255)
    return colors.HexColor("#{:02x}{:02x}{:02x}".format(
        min(255, r), min(255, g), min(255, b)
    ))

# ── Sonderzeichen → Latin-1 ──────────────────────────────────────────────────
def esc(s):
    """XML-Escape + Ersetze Nicht-Latin-1-Unicode durch ASCII-Äquivalente."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    replacements = {
        "→": "->",    # →
        "↔": "<->",   # ↔
        "▸": ">",     # ▸
        "–": "-",     # –
        "—": "--",    # —
        "‘": "'",     # '
        "’": "'",     # '
        "“": '"',     # "
        "”": '"',     # "
        "Ω": "Ohm",   # Ω
        "μ": "u",     # μ
        "≈": "~",     # ≈
        "µ": "u",     # µ (Mikro)
    }
    for uni, rep in replacements.items():
        s = s.replace(uni, rep)
    return s

# ── Seiten-Templates ─────────────────────────────────────────────────────────
def title_page_template(canvas, doc):
    """Seite 1: kein Header/Footer."""
    pass

def content_page_template(canvas, doc):
    """Alle anderen Seiten: schmaler Header + Fußzeile mit Seitenzahl."""
    canvas.saveState()
    # Header-Balken
    canvas.setFillColor(colors.HexColor("#EBEBEB"))
    canvas.rect(0, H - 1.0 * cm, W, 1.0 * cm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor("#333333"))
    canvas.drawString(1.5 * cm, H - 0.68 * cm, "MPP  |  Mündliche Prüfungsfragen")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(W - 1.5 * cm, H - 0.68 * cm, "Prüfungsvorbereitung")
    # Fußzeile
    canvas.setFillColor(colors.HexColor("#EBEBEB"))
    canvas.rect(0, 0, W, 0.85 * cm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(W / 2, 0.3 * cm, f"Seite  {doc.page}")
    canvas.restoreState()

# ── Deckblatt bauen ──────────────────────────────────────────────────────────
def build_cover(story):
    # Oberer farbiger Balken
    header_data = [[Paragraph(
        "<font color='white' size='20'><b>Prüfungsfragen</b></font><br/>"
        "<font color='#DDDDDD' size='11'>Mündliche Prüfung  ·  MPP</font>",
        ParagraphStyle("ch", alignment=TA_CENTER, leading=28)
    )]]
    header_tbl = Table(header_data, colWidths=[W - 3 * cm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#1A1A2E")),
        ("TOPPADDING",    (0, 0), (-1, -1), 28),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 28),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS",(0, 0), (-1, -1), 6),
    ]))
    story.append(Spacer(1, 1.8 * cm))
    story.append(header_tbl)
    story.append(Spacer(1, 1.0 * cm))

    # Untertitel
    story.append(Paragraph(
        "Geordnet nach Themenbereichen der Lernunterlagen",
        ParagraphStyle("cs", fontName="Helvetica", fontSize=10,
                       textColor=colors.HexColor("#555555"), alignment=TA_CENTER,
                       spaceAfter=0)
    ))
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="60%", thickness=0.8,
                             color=colors.HexColor("#CCCCCC"), hAlign="CENTER"))
    story.append(Spacer(1, 0.8 * cm))

    # Themenübersicht als Kacheln
    story.append(Paragraph(
        "Themenbereiche",
        ParagraphStyle("clabel", fontName="Helvetica-Bold", fontSize=9,
                       textColor=colors.HexColor("#888888"), alignment=TA_CENTER,
                       spaceAfter=6)
    ))
    story.append(Spacer(1, 0.2 * cm))

    # Kacheln: 2 Spalten
    tile_style = ParagraphStyle(
        "tile", fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.white, alignment=TA_CENTER, leading=13
    )
    rows = []
    for i in range(0, len(SECTIONS), 2):
        row = []
        for name, hex_col in SECTIONS[i:i+2]:
            cell = Table(
                [[Paragraph(name, tile_style)]],
                colWidths=[(W - 3 * cm) / 2 - 0.3 * cm]
            )
            cell.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(hex_col)),
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ]))
            row.append(cell)
        if len(row) == 1:
            row.append("")
        rows.append(row)

    grid = Table(rows,
                 colWidths=[(W - 3 * cm) / 2 - 0.15 * cm,
                            (W - 3 * cm) / 2 - 0.15 * cm],
                 rowHeights=[1.1 * cm] * len(rows))
    grid.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(grid)
    story.append(PageBreak())

# ── Stile ────────────────────────────────────────────────────────────────────
SECTION_HDR = ParagraphStyle(
    "SHdr", fontName="Helvetica-Bold", fontSize=13,
    textColor=colors.white, leading=18
)
SECTION_SUB = ParagraphStyle(
    "SSub", fontName="Helvetica", fontSize=10,
    textColor=colors.HexColor("#DDDDDD"), leading=14, spaceAfter=4
)
SUBSEC_HDR = ParagraphStyle(
    "SubHdr", fontName="Helvetica-Bold", fontSize=9.5,
    leading=13, spaceAfter=2
)
QUESTION = ParagraphStyle(
    "Q", fontName="Helvetica", fontSize=9,
    textColor=colors.HexColor("#111111"),
    spaceBefore=2, spaceAfter=2,
    leftIndent=16, firstLineIndent=-16,
    leading=13
)
INDENT = ParagraphStyle(
    "Ind", fontName="Helvetica", fontSize=9,
    textColor=colors.HexColor("#444444"),
    spaceBefore=1, spaceAfter=1,
    leftIndent=30, leading=12
)

# ── Hauptparser ──────────────────────────────────────────────────────────────
def parse_and_build(txt_path, pdf_path):
    story = []
    build_cover(story)

    with open(txt_path, encoding="utf-8") as f:
        lines = f.readlines()

    current_color = colors.HexColor("#333333")
    i = 0
    first_section = True

    while i < len(lines):
        raw     = lines[i].rstrip("\n")
        stripped = raw.strip()

        # ── Abschnittsheader (====...====) ───────────────────────────────────
        if stripped.startswith("====") and stripped.endswith("===="):
            title_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            sub_line   = lines[i + 2].strip() if i + 2 < len(lines) else ""

            current_color = section_color(title_line)

            if not first_section:
                story.append(PageBreak())
            first_section = False

            # Farbiger Titelbalken
            cell_content = [Paragraph(esc(title_line), SECTION_HDR)]
            if sub_line.startswith("("):
                cell_content.append(Paragraph(esc(sub_line), SECTION_SUB))

            tbl = Table([[ cell_content ]], colWidths=[W - 3 * cm])
            tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), current_color),
                ("LEFTPADDING",   (0, 0), (-1, -1), 14),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.35 * cm))

            # Überspringe: öffnende ====, Titel, Untertitel, schließende ====
            skip = 1
            if i + 1 < len(lines) and not lines[i+1].strip().startswith("="):
                skip += 1
            if i + 2 < len(lines) and not lines[i+2].strip().startswith("="):
                skip += 1
            if i + skip < len(lines) and lines[i+skip].strip().startswith("===="):
                skip += 1
            i += skip
            continue

        # ── Unterabschnitt (--- Name ---) ────────────────────────────────────
        if stripped.startswith("---") and stripped.endswith("---"):
            label  = stripped.strip("-").strip()
            bg_col = lighten(current_color, 0.88)

            sub_style = ParagraphStyle(
                "SubS", fontName="Helvetica-Bold", fontSize=9.5,
                textColor=current_color, leading=13
            )
            tbl = Table([[Paragraph("> " + esc(label), sub_style)]],
                        colWidths=[W - 3 * cm])
            tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), bg_col),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW",     (0, 0), (-1, -1), 0.8, current_color),
            ]))
            story.append(Spacer(1, 0.25 * cm))
            story.append(tbl)
            story.append(Spacer(1, 0.1 * cm))
            i += 1
            continue

        # ── Fragen (Zahl + Punkt) ─────────────────────────────────────────────
        m = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if m:
            num, text = m.group(1), m.group(2)
            story.append(Paragraph(f"<b>{num}.</b>  {esc(text)}", QUESTION))
            i += 1
            continue

        # ── Eingerückte Fortsetzungszeile ─────────────────────────────────────
        if raw.startswith("    ") and stripped:
            story.append(Paragraph(esc(stripped), INDENT))
            i += 1
            continue

        # ── Leerzeile ─────────────────────────────────────────────────────────
        if not stripped:
            story.append(Spacer(1, 0.08 * cm))
            i += 1
            continue

        i += 1

    # ── PDF ausgeben ─────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.1 * cm,
        title="MPP Prüfungsfragen",
        author="Prüfungsvorbereitung",
    )
    doc.build(
        story,
        onFirstPage=title_page_template,
        onLaterPages=content_page_template,
    )
    print(f"PDF erstellt: {pdf_path}")


if __name__ == "__main__":
    parse_and_build(
        "/Users/kangon/Documents/Uni/MPP/fragen.txt",
        "/Users/kangon/Documents/Uni/MPP/fragen.pdf",
    )
