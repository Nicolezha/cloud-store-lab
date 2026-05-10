"""
Minimal FastAPI teaching app for cloud evaluation.

This file is intentionally incomplete. Students must implement:
- Cloud SQL (PostgreSQL) integration
- Cloud Storage integration
- Firestore integration
"""

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import UploadFile, File
from google.cloud import storage
import uuid
import os

app = FastAPI(title="Cloud Computing Evaluation API (Starter)")


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float


class CommentCreate(BaseModel):
    author: str
    text: str


@app.get("/health")
def health():
    # TODO: Return service status and optionally dependency status.
    # Keep this endpoint simple for uptime checks.
    return {"status": "ok",
            "service": "cloud-store-lab"}
    pass


@app.post("/products")
def create_product(payload: ProductCreate):
    # TODO: Validate and store product data in Cloud SQL (PostgreSQL).
    # Do not keep products in memory for the final solution.
    # Students should use psycopg2 and proper SQL schema design.
    pass


@app.get("/products")
def list_products():
    # TODO: Read and return product records from Cloud SQL (PostgreSQL).
    # Consider pagination and filtering in the final implementation.
    pass


@app.post("/products/{product_id}/image")
async def upload_product_image(product_id: int, file: UploadFile = File(...)):
    # TODO: Accept an image upload and store it in Cloud Storage.
    # Save metadata or URL reference in Cloud SQL as needed.
    # Students should implement secure bucket access and object naming.
    client = storage.Client()

    bucket = client.bucket(
        os.getenv("GCS_BUCKET_NAME")
    )

    blob = bucket.blob(
        f"products/{uuid.uuid4()}-{file.filename}"
    )

    blob.upload_from_file(
        file.file,
        content_type=file.content_type
    )

    blob.make_public()

    return {
        "url": blob.public_url
    }


@app.post("/products/{product_id}/comments")
def add_product_comment(product_id: int, payload: CommentCreate):
    # TODO: Write comment/audit-style data to Firestore.
    # Students should design a document structure and validation rules.
    pass


@app.get("/audit/events")
def get_audit_events():
    # TODO: Read audit events from Firestore and return them.
    # Students should think about ordering, limits, and filtering.
    pass
