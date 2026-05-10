"""
Minimal FastAPI teaching app for cloud evaluation.

This file is intentionally incomplete. Students must implement:
- Cloud SQL (PostgreSQL) integration
- Cloud Storage integration
- Firestore integration
"""
import os # para leer las variables del entorno
import psycopg2
import uuid
from google.cloud import firestore # el SDK oficial de Google para hablar con Firestore desde Python
from google.cloud import storage   # el SDK oficial de Google para hablar con Cloud Storage desde Python
from datetime import datetime # para registrar en qué momento exacto ocurrió cada evento
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import HTTPException


load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

db = firestore.Client() # inicializar el cliente de Firestore
AUDIT_COLLECTION = os.getenv("FIRESTORE_COLLECTION_AUDIT_EVENTS", "audit_events")

app = FastAPI(title="Cloud Computing Evaluation API (Starter)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("static/index.html")

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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, description, price) VALUES (%s, %s, %s) RETURNING id",
        (payload.name, payload.description, payload.price)
    )
    product_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

     # Auditoría del evento
    db.collection(AUDIT_COLLECTION).add({
        "event": "product_added",
        "product_id": product_id,
        "name": payload.name,
        "description": payload.description,
        "price": payload.price,
        "timestamp": datetime.utcnow()
    })

    return {"id": product_id, "message": "Producto creado"}


@app.get("/products")
def list_products():
    # TODO: Read and return product records from Cloud SQL (PostgreSQL).
    # Consider pagination and filtering in the final implementation.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, price, image_url, created_at FROM products")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "description": r[2], "price": r[3], "image_url": r[4], "created_at": str(r[5])}
        for r in rows
    ]


@app.post("/products/{product_id}/image")
async def upload_product_image(product_id: int, file: UploadFile = File(...)):
    # TODO: Accept an image upload and store it in Cloud Storage.
    # Save metadata or URL reference in Cloud SQL as needed.
    # Students should implement secure bucket access and object naming.
    client = storage.Client()
    bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))

    blob = bucket.blob(
        f"products/{uuid.uuid4()}-{file.filename}"
    )

    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()

    image_url = blob.public_url
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE products SET image_url = %s WHERE id = %s",
        (image_url, product_id)
    )

    conn.commit()
    cur.close()
    conn.close()

     # Auditoría del evento
    db.collection(AUDIT_COLLECTION).add({
        "event": "image_uploaded",
        "product_id": product_id,
        "image_url": image_url,
        "timestamp": datetime.utcnow()
    })

    return {
        "product_id": product_id,
        "image_url": image_url
    }


@app.post("/products/{product_id}/comments")
def add_product_comment(product_id: int, payload: CommentCreate):
    # Validar que el producto exista
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()

    if not product:
        raise HTTPException(status_code=404, detail="El producto no existe")
        
    # Construir comentario
    comment_doc = {
        "product_id": product_id,
        "author": payload.author,
        "text": payload.text,
        "timestamp": datetime.utcnow()
    }

    # Guardar comentario en Firestore
    db.collection("comments").add(comment_doc)

    # Auditoría del evento
    db.collection(AUDIT_COLLECTION).add({
        "event": "comment_added",
        "product_id": product_id,
        "author": payload.author,
        "text": payload.text,
        "timestamp": datetime.utcnow()
    })

    return {"message": "Comentario agregado correctamente"}

@app.get("/audit/events")
def get_audit_events():
    
    # Leemos todos los documentos de audit_events
    # ordenados del más reciente al más viejo
    docs = db.collection(AUDIT_COLLECTION)\
             .order_by("timestamp", direction=firestore.Query.DESCENDING)\
             .limit(50)\
             .stream()
    
    events = []
    for doc in docs:
        data = doc.to_dict()      # convierte el documento a diccionario Python
        data["id"] = doc.id       # agrega el ID del documento
        
        # Firestore guarda fechas como objetos especiales
        # hay que convertirlos a texto para que JSON los entienda
        if "timestamp" in data:
            data["timestamp"] = data["timestamp"].isoformat()
        
        events.append(data)
    
    return {"events": events}
