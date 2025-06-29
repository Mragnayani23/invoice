from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List, Optional
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
import os

app = FastAPI()

class Item(BaseModel):
    sr_no: str
    description: str
    units: str
    rate: str
    amount: str

class ShipmentField(BaseModel):
    label: str
    value: str

class InvoiceData(BaseModel):
    exporter: List[str]
    consignee: List[str]
    notify: List[str]
    invoice_no: str
    ie_code: str
    buyer_order: str
    shipment_details: List[ShipmentField]
    goods: List[Item]
    chargeable: str
    bin_number: str
    drawback_sr_no: Optional[str] = ""
    benefit_under_mems: Optional[str] = ""
    shipment_under_alq: Optional[str] = ""
    declaration: str
    logo_path: Optional[str] = None  # Optional logo image

@app.post("/generate-invoice/")
async def generate_invoice(data: InvoiceData):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleBH = ParagraphStyle(name='Heading', fontSize=14, alignment=1, fontName="Helvetica-Bold")
    elements = []

    # Header: Logo + Title
    if data.logo_path and os.path.exists(data.logo_path):
        im = Image(data.logo_path, width=70, height=35)
        header_table = Table([[im, Paragraph("INVOICE CUM PACKING LIST", styleBH)]], colWidths=[80, 400])
        header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.append(header_table)
    else:
        elements.append(Paragraph("INVOICE CUM PACKING LIST", styleBH))

    elements.append(Spacer(1, 10))

    # Exporter and Invoice Info
    exporter_block = [Paragraph("<b>EXPORTER</b>", styleN)] + [Paragraph(line, styleN) for line in data.exporter]
    invoice_info = [
        Paragraph(f"<b>Invoice No. & Date:</b> {data.invoice_no}", styleN),
        Paragraph(f"<b>I.E. Code No.:</b> {data.ie_code}", styleN),
        Paragraph(f"<b>Buyer's Order No. & Date:</b> {data.buyer_order}", styleN)
    ]
    row1 = [exporter_block, invoice_info]

    # Consignee and Notify
    consignee_block = [[Paragraph("<b>CONSIGNEE:</b>", styleN), Paragraph(data.consignee[0], styleN)]]
    consignee_block += [["", Paragraph(line, styleN)] for line in data.consignee[1:]]
    consignee_block.append([Paragraph("<b>NOTIFY:</b>", styleN), Paragraph("<br/>".join(data.notify), styleN)])

    elements.append(
        Table([row1] + consignee_block, colWidths=[280, 270], style=[
            ('BOX', (0, 0), (-1, -1), 0.7, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ])
    )

    # Shipment + Goods Table
    shipment_rows = [[field.label, field.value, '', '', ''] for field in data.shipment_details]

    goods_header = ["Sr No & Marks", "Description of Goods", "No. of Units", "Rate per Unit (USD)", "Amount (USD)"]
    goods_rows = [[
        item.sr_no,
        Paragraph(item.description, styleN),
        item.units,
        item.rate,
        item.amount
    ] for item in data.goods]

    combined_table = shipment_rows + [goods_header] + goods_rows
    col_widths = [100, 210, 80, 80, 80]
    elements.append(
        Table(combined_table, colWidths=col_widths, style=[
            ('BOX', (0, 0), (-1, -1), 0.7, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, len(shipment_rows)), (-1, len(shipment_rows)), colors.whitesmoke),
            ('FONTNAME', (0, len(shipment_rows)), (-1, len(shipment_rows)), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (2, len(shipment_rows)+1), (-1, len(shipment_rows)+1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ])
    )

    # Footer
    footer_rows = [
        ["Amount Chargeable:", data.chargeable],
        ["BIN No.:", data.bin_number],
        ["Drawback Sr. No.:", data.drawback_sr_no],
        ["Benefit under MEMS scheme:", data.benefit_under_mems],
        ["Shipment under ALQ scheme:", data.shipment_under_alq],
        ["DECLARATION:", Paragraph(data.declaration, styleN)]
    ]
    elements.append(
        KeepTogether(Table(footer_rows, colWidths=[150, 400], rowHeights=[25, 18, 18, 18, 18, 100], style=[
            ('BOX', (0, 0), (-1, -1), 0.7, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
    )

    doc.build(elements)
    buffer.seek(0)
    return Response(content=buffer.read(), media_type='application/pdf', headers={
        "Content-Disposition": "attachment; filename=invoice_codex_dynamic.pdf"
    })
