"""
Minimal FastAPI teaching app for cloud evaluation.

This file is intentionally incomplete. Students must implement:
- Cloud SQL (PostgreSQL) integration
- Cloud Storage integration
- Firestore integration
"""
from dotenv import load_dotenv
load_dotenv()
import os # para leer las variables del entorno
from google.cloud import firestore # el SDK oficial de Google para hablar con Firestore desde Python
from datetime import datetime # para registrar en qué momento exacto ocurrió cada evento
from fastapi import FastAPI
from pydantic import BaseModel

db = firestore.Client() # inicializar el cliente de Firestore
AUDIT_COLLECTION = os.getenv("FIRESTORE_COLLECTION_AUDIT_EVENTS", "audit_events")

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
def upload_product_image(product_id: int):
    # TODO: Accept an image upload and store it in Cloud Storage.
    # Save metadata or URL reference in Cloud SQL as needed.
    # Students should implement secure bucket access and object naming.
    pass


@app.post("/products/{product_id}/comments")
def add_product_comment(product_id: int, payload: CommentCreate):
    
    # Armamos el documento que vamos a guardar en Firestore
    comment_doc = {
        "product_id": product_id,
        "author": payload.author,
        "text": payload.text,
        "timestamp": datetime.now()
    }
    
    # Lo guardamos en la colección "comments"
    # .add() crea un documento nuevo con ID automático
    db.collection("comments").add(comment_doc)
    
    # También registramos en auditoría que se agregó un comentario
    db.collection(AUDIT_COLLECTION).add({
        "event": "comment_added",
        "product_id": product_id,
        "timestamp": datetime.now()
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
