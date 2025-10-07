from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage, Spacer, Table, TableStyle
from reportlab.lib import colors
import os

def build_catalog(pdf_path, rows, design="classic", show_logo=True, logo_path=None, show_company=True, company_name="ÖZKUL ELEKTRONİK"):
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    story = []
    if show_logo and logo_path and os.path.exists(logo_path):
        try:
            story.append(RLImage(logo_path, width=120, height=40))
        except Exception:
            pass
    if show_company and company_name:
        story.append(Paragraph(f"<b>{company_name}</b>", styles['Title']))
    story.append(Spacer(1, 6*mm))

    cards = []
    data = []
    col_count = 2 if design == "classic" else (3 if design == "modern" else 1)
    cell_w = (A4[0] - 24*mm) / col_count

    # Build simple product cards
    card_style = styles['Normal']
    for p in rows:
        parts = []
        img_path = None
        if p['images']:
            img_path = p['images'][0]
        if img_path and os.path.exists(img_path):
            try:
                parts.append(RLImage(img_path, width=cell_w-10, height= (cell_w-10) * 0.75))
            except Exception:
                pass
        parts.append(Paragraph(f"<b>{p['name']}</b>", styles['Heading4']))
        parts.append(Paragraph(f"SKU: {p['sku']}", card_style))
        if p.get('price') is not None:
            parts.append(Paragraph(f"Fiyat: {p['price']} ₺", card_style))
        if p.get('description'):
            parts.append(Paragraph(p['description'][:240], card_style))
        tbl = Table([[parts]], colWidths=[cell_w])
        tbl.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.25,colors.grey),
                                 ('VALIGN',(0,0),(-1,-1),'TOP'),
                                 ('PADDING',(0,0),(-1,-1),6)]))
        data.append(tbl)
        if len(data) == col_count:
            story.append(Table([data], colWidths=[cell_w]*col_count, hAlign='LEFT', style=TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('BOTTOMPADDING',(0,0),(-1,-1),10)])))
            data = []
    if data:
        # last row
        story.append(Table([data], colWidths=[cell_w]*len(data), hAlign='LEFT'))

    doc.build(story)
