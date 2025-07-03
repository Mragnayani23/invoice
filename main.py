from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import os

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
    country_origin: str 
    port_of_discharge: str
    terms_of_payment: str
    amount_chargeable: str
    bin_no: str
    drawback_sr_no: str
    benefits_under_mems: str
    shipment_under_alq: str
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

    # 🔹 Background
    bg_path = os.path.join(os.path.dirname(__file__), "invoicebg.jpg")
    c.drawImage(ImageReader(bg_path), 0, 0, width=width, height=height)

    # 🔹 Main Heading
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, 810, "INVOICE CUM PACKING LIST")

    # 🔹 Metadata (right side)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(300, 730, "Invoice No.:")
    c.drawString(300, 720, "I.E. Code No.:")
    c.setFont("Helvetica", 8)
    c.drawString(420, 725, data.invoice_no or "")
    c.drawString(420, 730, data.ie_code or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(300, 685, "Buyer's Order No.:")
    c.setFont("Helvetica", 8)
    c.drawString(420, 660, data.buyer_order or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(300, 645, "Notify Party:")
    c.setFont("Helvetica", 8)
    c.drawString(420, 600, data.notify_party or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(300, 590, "Country of Origin")
    c.setFont("Helvetica", 8)
    c.drawString(420, 570, data.country_origin or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(300, 560, "Country of final destination")
    c.setFont("Helvetica", 8)
    c.drawString(420, 550, data.country_of_final_destination or "")

    # 🔹 Left-side multiline fields
    def draw_multiline(text, x, y_start):
        for i, line in enumerate(text.splitlines()):
            c.drawString(x, y_start - i * 10, line)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, 730, "Exporter:")
    c.setFont("Helvetica", 8)
    draw_multiline(data.exporter, 50, 700)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, 645, "Consignee:")
    c.setFont("Helvetica", 8)
    draw_multiline(data.consignee, 50, 600)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, 560, "Pre-Carriage By:")
    c.setFont("Helvetica", 8)
    draw_multiline(data.pre_carriage_by, 50, 550)

    # 🔹 Bottom metadata
    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, 530, "Vessel/Voyage")
    c.setFont("Helvetica", 8)
    c.drawString(70, 518, data.vessel_no or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(165, 530, "Port of Loading")
    c.setFont("Helvetica", 8)
    c.drawString(220, 518, data.port_of_loading or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(300, 530, "Terms of Payment ")
    c.setFont("Helvetica", 8)
    c.drawString(430, 503, data.terms_of_payment or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(165, 500, "Final Destination")
    c.setFont("Helvetica", 8)
    c.drawString(220, 490, data.final_destination or "")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, 500, "Port of Discharge:")
    c.setFont("Helvetica", 8)
    c.drawString(70, 490, data.port_of_discharge or "")

    # 🔹 Table Header
    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, 465, "Sr No.")
    c.drawString(200, 465, "Description of Goods")
    c.drawString(370, 465, "No. of Units")
    c.drawString(425, 465, "Rate per")
    c.drawString(510, 465, "Amount (USD)")

    # 🔹 Table Rows
    c.setFont("Helvetica", 7.5)
    goods_y = 400
    for item in data.goods:
        c.drawString(45, goods_y, item.sr_no)
        c.drawString(155, goods_y, item.description)
        c.drawString(370, goods_y, item.units)
        c.drawString(420, goods_y, item.rate)
        c.drawString(510, goods_y, item.amount)
        goods_y -= 30

    # 🔹 Amount Chargeable
    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, goods_y, "Amount Chargeable:")
    c.setFont("Helvetica", 8)
    c.drawString(160, goods_y, data.amount_chargeable)
    goods_y -= 20

    # 🔹 Extra Metadata
    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, goods_y, "BIN NO:")
    c.setFont("Helvetica", 8)
    c.drawString(90, goods_y, data.bin_no)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(200, goods_y, "Drawback Sr. No.:")
    c.setFont("Helvetica", 8)
    c.drawString(300, goods_y, data.drawback_sr_no)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, goods_y - 15, "Benefits under MEMS scheme:")
    c.setFont("Helvetica", 8)
    c.drawString(200, goods_y - 15, data.benefits_under_mems)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, goods_y - 30, "Shipment under ALQ scheme:")
    c.setFont("Helvetica", 8)
    c.drawString(200, goods_y - 30, data.shipment_under_alq)

    goods_y -= 50

    # 🔹 Declaration (Adjusted)
    y_decl = goods_y - 15
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width / 2, goods_y, "DECLARATION")
    c.setFont("Helvetica", 7)
    for line in data.declaration.splitlines():
        c.drawString(60, y_decl, line)
        y_decl -= 10

    # 🔹 Signature
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, 70, "For CODEX AUTOMATION KEY")
    c.line(width - 150, 60, width - 40, 60)
    c.drawRightString(width - 40, 50, "Authorised Signatory")

    # 🔹 Footer
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString((width / 2) - 50, 25, "CODEX AUTOMATION KEY • docwise.codexautomationkey.com")

    # Finalize
    c.save()
    buffer.seek(0)
    return Response(
        content=buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=invoice_codex.pdf"}
    )

