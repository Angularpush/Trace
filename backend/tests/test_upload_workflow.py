import io
import os
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_dummy_image(format="PNG", text="Sample"):
    file_bytes = io.BytesIO()
    img = Image.new("RGB", (300, 100), color="white")
    img.save(file_bytes, format=format)
    file_bytes.seek(0)
    return file_bytes

def test_upload_allowed_extensions_and_workflow():
    # 1. Create a dummy PNG, JPG, and text PO file
    png_bytes = create_dummy_image("PNG")
    jpeg_bytes = create_dummy_image("JPEG")
    po_text = (
        "PURCHASE ORDER\n"
        "PO Number: PO-2024-TEST-99\n"
        "Date: 2024-03-01\n"
        "Vendor: Test Dynamics Ltd\n"
        "Total Amount: INR 50000.00\n"
    ).encode("utf-8")

    files = [
        ("files", ("test_image.png", png_bytes, "image/png")),
        ("files", ("test_photo.jpg", jpeg_bytes, "image/jpeg")),
        ("files", ("po_sample.txt", io.BytesIO(po_text), "text/plain"))
    ]

    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["file_type"] == "png"
    assert data[1]["file_type"] == "jpg"
    assert data[2]["doc_type"] == "PURCHASE_ORDER"

def test_upload_invalid_extension_rejected():
    exe_file = io.BytesIO(b"MZBINARYEXE")
    files = [
        ("files", ("malicious_payload.exe", exe_file, "application/octet-stream"))
    ]

    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    err = response.json()
    assert "Unsupported file format" in err["detail"]

def test_auto_link_and_reconcile_cycle():
    # Test auto link
    link_resp = client.post("/api/v1/transactions/auto-link")
    assert link_resp.status_code == 200
    txns = link_resp.json()
    assert isinstance(txns, list)
