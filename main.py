from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = FastAPI()

class Item(BaseModel):
    sr_no: str
    description: str
    units: str
    rate: str
    amount: str

class InvoiceData(BaseModel):
    exporter: str
    consignee: str
    notify_party: str
    invoice_no: str
    invoice_date: str
    ie_code: str
    buyer_order: str
    port_of_loading: str
    final_destination: str
    vessel_no: str
    terms_of_delivery: str
    container_no: str
    seal_no: str
    marks: str
    pre_carriage_by: str
    place_of_receipt: str
    country_of_final_destination: str
    port_of_discharge: str
    terms_of_payment: str
    goods: List[Item]
    declaration: str

@app.get("/")
def root():
    return {"message": "Invoice generator is live. Use POST /generate-invoice-pdf"}

@app.post("/generate-invoice-pdf/")
def generate_invoice(data: InvoiceData):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Draw background image
    import os
    bg_path = os.path.join(os.path.dirname(__file__), "invoicebg.jpg")

    c.drawImage(ImageReader(bg_path), 0, 0, width=width, height=height)

    # 🔹 Heading
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, 810, "INVOICE CUM PACKING LIST")

    c.setFont("Helvetica", 8)

    # 🔹 Invoice metadata (right)
    fields = [
        (data.invoice_no, 420, 725),
        (data.invoice_date, 420, 660),
        (data.ie_code, 200, 550),
        (data.buyer_order, 420, 600),
        (data.port_of_loading, 420, 550),
        (data.vessel_no, 420, 570),
        
       
       
    ]
    for val, x, y in fields:
        c.drawString(x, y, val)

    # 🔹 Multiline text blocks
    def draw_multiline(text, x, y_start):
        for i, line in enumerate(text.splitlines()):
            c.drawString(x, y_start - i * 10, line)

    draw_multiline(data.exporter, 50, 700)
    draw_multiline(data.consignee, 50, 600)
    draw_multiline(data.notify_party, 50, 550)

    # 🔹 New metadata (preserving coordinates)
    c.drawString(50, 530, f"Pre-Carriage By: {data.pre_carriage_by}")
    c.drawString(190, 530, f"Place of Receipt: {data.place_of_receipt}")
    c.drawString(310, 515, f"Country of Final Destination: {data.country_of_final_destination}")
    c.drawString(190, 500, f"Port of Discharge: {data.port_of_discharge}")
    c.drawString(50, 500, f"Terms of Payment: {data.terms_of_payment}")

    # 🔹 Goods Table Header
    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, 465, "Sr No.")
    c.drawString(200 ,465, "Description of Goods")
    c.drawString(370, 465, "No. of Units")
    c.drawString(425, 465, "Rate per")
    c.drawString(510, 465, "Amount (USD)")

    # 🔹 Goods Data Rows
    c.setFont("Helvetica", 7.5)
    goods_y = 450
    for item in data.goods:
        c.drawString(45, goods_y, item.sr_no)
        c.drawString(85, goods_y, item.description)
        c.drawString(300, goods_y, item.units)
        c.drawString(370, goods_y, item.rate)
        c.drawString(440, goods_y, item.amount)
        goods_y -= 15

    # 🔹 Declaration
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width / 2, 130, "DECLARATION")
    c.setFont("Helvetica", 7)
    y_decl = 115
    for line in data.declaration.splitlines():
        c.drawString(60, y_decl, line)
        y_decl -= 10

    # 🔹 Signature
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, 70, "For CODEX AUTOMATION KEY")
    c.line(width - 150, 60, width - 40, 60)
    c.drawRightString(width - 40, 50, "Authorised Signatory")

    # 🔹 Footer Branding
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString((width / 2) - 50, 25, "CODEX AUTOMATION KEY • docwise.codexautomationkey.com")

    c.save()
    buffer.seek(0)
    return Response(
        content=buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=invoice_codex.pdf"}
    )
