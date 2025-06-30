from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
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

class TransportDetail(BaseModel):
    label: str
    value: str

class PackingDetail(BaseModel):
    marks_and_numbers: str
    packing: str
    net_weight: str
    gross_weight: str

class InvoiceData(BaseModel):
    exporter: List[str]
    consignee: List[str]
    notify: List[str]
    invoice_no: str
    ie_code: str
    buyer_order: str
    lc_code: Optional[str] = ""
    shipment_details: List[ShipmentField]
    transport_info: List[TransportDetail]
    goods: List[Item]
    packing_details: List[PackingDetail]
    chargeable: str
    bin_number: str
    drawback_sr_no: Optional[str] = ""
    benefit_under_mems: Optional[str] = ""
    shipment_under_alq: Optional[str] = ""
    declaration: str
    logo_path: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Invoice generator is live. Use POST /generate-invoice-pdf"}

@app.post("/generate-invoice-pdf/")
async def generate_invoice(data: InvoiceData):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Logo
    if data.logo_path and os.path.exists(data.logo_path):
        try:
            c.drawImage(ImageReader(data.logo_path), 40, height - 80, width=70, height=35)
        except:
            pass

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, "INVOICE CUM PACKING LIST")

    def draw_block(title, lines, x, y_top, w=250):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 5, y_top - 15, title)
        y = y_top - 27
        c.setFont("Helvetica", 8)
        for line in lines:
            c.drawString(x + 10, y, line)
            y -= 10
        h = y_top - y
        c.rect(x, y_top - h, w, h)
        return y - 5

    y_top = height - 100
    y1 = draw_block("EXPORTER:", data.exporter, 40, y_top)
    y2 = draw_block("CONSIGNEE:", data.consignee, 40, y1)
    y3 = draw_block("NOTIFY PARTY:", data.notify, 40, y2)

    # Right Column
    x_info = 320
    y_info = y_top
    c.setFont("Helvetica", 8)
    c.drawString(x_info, y_info, f"Invoice No. & Date: {data.invoice_no}")
    c.drawString(x_info, y_info - 12, f"I.E. Code No.: {data.ie_code}")
    c.drawString(x_info, y_info - 24, f"Buyer's Order No. & Date: {data.buyer_order}")
    if data.lc_code:
        c.drawString(x_info, y_info - 36, f"L/C Code No. & Date: {data.lc_code}")
    y_ship = y_info - (60 if data.lc_code else 48)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_info, y_ship, "SHIPMENT DETAILS:")
    c.setFont("Helvetica", 8)
    y_ship -= 15
    for field in data.shipment_details:
        c.drawString(x_info + 10, y_ship, f"{field.label}: {field.value}")
        y_ship -= 10

    y_ship -= 10
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_info, y_ship, "TRANSPORT INFORMATION:")
    y_ship -= 15
    c.setFont("Helvetica", 8)
    for t in data.transport_info:
        c.drawString(x_info + 10, y_ship, f"{t.label}: {t.value}")
        y_ship -= 10

    # Goods Table
    y_table = y3 - 60
    headers = ["Sr No", "Description", "Units", "Rate (USD)", "Amount (USD)"]
    col_x = [40, 90, 330, 400, 470]
    col_widths = [50, 240, 70, 60, 60]
    row_height = 15

    c.setFillColor(colors.lightgrey)
    c.rect(40, y_table - row_height, width - 80, row_height, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8)
    for i, text in enumerate(headers):
        c.drawCentredString(col_x[i] + col_widths[i]/2, y_table - 11, text)

    y_table -= row_height
    c.setFont("Helvetica", 8)
    for item in data.goods:
        c.line(40, y_table, width - 40, y_table)
        c.drawCentredString(col_x[0] + col_widths[0]/2, y_table - 11, item.sr_no)
        c.drawString(col_x[1] + 2, y_table - 11, item.description)
        c.drawCentredString(col_x[2] + col_widths[2]/2, y_table - 11, item.units)
        c.drawCentredString(col_x[3] + col_widths[3]/2, y_table - 11, item.rate)
        c.drawCentredString(col_x[4] + col_widths[4]/2, y_table - 11, item.amount)
        y_table -= row_height
    c.line(40, y_table, width - 40, y_table)
    for x in col_x:
        c.line(x, y_table, x, y_table + (len(data.goods)+1)*row_height)
    c.line(width - 40, y_table, width - 40, y_table + (len(data.goods)+1)*row_height)

    c.setFont("Helvetica-Bold", 8)
    c.rect(col_x[3], y_table - 18, col_widths[3] + col_widths[4], 18)
    c.drawString(col_x[3] + 5, y_table - 6, "Total Amount (USD):")
    c.setFont("Helvetica", 8)
    c.drawRightString(col_x[4] + col_widths[4] - 5, y_table - 6, data.chargeable)

    # Packing
    y_table -= 40
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, y_table, "PACKING DETAILS")
    y_table -= 15
    c.setFont("Helvetica", 8)
    for p in data.packing_details:
        c.drawString(50, y_table, f"Marks & Numbers: {p.marks_and_numbers}")
        y_table -= 12
        c.drawString(50, y_table, f"Packing: {p.packing}")
        y_table -= 12
        c.drawString(50, y_table, f"Net Weight: {p.net_weight}   Gross Weight: {p.gross_weight}")
        y_table -= 20

    y_footer = y_table
    def draw_footer(label, value):
        nonlocal y_footer
        c.setFont("Helvetica-Bold", 8)
        c.drawString(40, y_footer, label)
        c.setFont("Helvetica", 8)
        c.drawString(180, y_footer, value)
        y_footer -= 12

    draw_footer("Amount Chargeable:", data.chargeable)
    draw_footer("BIN No.:", data.bin_number)
    if data.drawback_sr_no:
        draw_footer("Drawback Sr. No.:", data.drawback_sr_no)
    if data.benefit_under_mems:
        draw_footer("Benefit under MEIS scheme:", data.benefit_under_mems)
    if data.shipment_under_alq:
        draw_footer("Shipment under ALU scheme:", data.shipment_under_alq)

    y_footer -= 10
    dec_top = y_footer
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2, y_footer, "DECLARATION")
    y_footer -= 13
    c.setFont("Helvetica", 8)
    for line in data.declaration.splitlines():
        c.drawString(50, y_footer, line)
        c.drawString(50, y_footer, line)
        y_footer -= 10
    c.rect(40, y_footer - 5, width - 80, dec_top - y_footer + 15)

    # Signature Block
    y_footer -= 30
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 50, y_footer, "For CODEX AUTOMATION KEY")
    c.line(width - 150, y_footer - 15, width - 40, y_footer - 15)
    c.drawRightString(width - 50, y_footer - 30, "Authorised Signatory")

    # Optional Watermark
    c.setFont("Helvetica-Bold", 60)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, "DRAFT")
    c.restoreState()
    c.setFillColor(colors.black)

    # Footer Branding
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(width / 2, 20, "CODEX AUTOMATION KEY • docwise.codexautomationkey.com")

    # ✅ Return PDF with Download Header
    c.save()
    buffer.seek(0)
    return Response(
        content=buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=invoice_codex.pdf"}
    )

