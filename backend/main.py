from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from backend.config import Config
from backend.db import get_db_connection
from backend.models import (
    LoginRequest,
    AppointmentRequest,
    PatientDetailsResponse,
    MedicalHistoryResponse
)
from backend.preprocess import preprocess_text
from backend.langgraph_llm_agents import build_graph

# ---------------------------------------------------
# App Setup
# ---------------------------------------------------

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[Config.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Load AI Models (on startup)
# ---------------------------------------------------

model = None
index = None
terms = None


@app.on_event("startup")
def load_ai_components():
    global model, index, terms

    logger.info("Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Load FAISS index if exists
    if os.path.exists("backend/faiss_index.bin") and os.path.exists("backend/terms.npy"):
        logger.info("Loading FAISS index...")
        index = faiss.read_index("backend/faiss_index.bin")
        terms = np.load("backend/terms.npy", allow_pickle=True)
        logger.info("FAISS index loaded successfully.")
    else:
        logger.warning("FAISS index files not found. /normalize endpoint will not work.")


# ---------------------------------------------------
# Database Dependency
# ---------------------------------------------------

def get_cursor():
    conn = get_db_connection()
    try:
        yield conn.cursor(), conn
    finally:
        conn.close()


# ---------------------------------------------------
# Routes
# ---------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Welcome to the Healthcare Agent API!"}


# ---------------- LOGIN ----------------

@app.post("/login")
def login(request: LoginRequest, db=Depends(get_cursor)):
    cur, conn = db
    try:
        cur.execute(
            "SELECT * FROM sp_login_user(%s::TEXT, %s::TEXT)",
            (request.email, request.password)
        )
        user = cur.fetchone()
    except Exception as e:
        conn.rollback()
        logger.error(f"Login DB error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

    if user:
        return {"message": "Login successful", "user_id": user[0]}

    raise HTTPException(status_code=401, detail="Invalid credentials")


# ---------------- PATIENT DETAILS ----------------

@app.get("/patient-details/{user_id}", response_model=PatientDetailsResponse)
def get_patient_details(user_id: int, db=Depends(get_cursor)):
    cur, conn = db
    try:
        cur.execute("SELECT * FROM sp_get_patient_details(%s);", (user_id,))
        row = cur.fetchone()
    except Exception as e:
        conn.rollback()
        logger.error(f"Patient details DB error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    if row:
        return {
            "name": row[0],
            "date_of_birth": row[1],
            "gender": row[2],
            "contact_number": row[3],
            "medical_record_number": row[4],
            "blood_group": row[5],
            "marital_status": row[6],
            "id": row[7],
        }

    raise HTTPException(status_code=404, detail="Patient not found")


# ---------------- MEDICAL HISTORY ----------------

@app.get("/medical-history/{user_id}", response_model=MedicalHistoryResponse)
def get_medical_history(user_id: int, db=Depends(get_cursor)):
    cur, conn = db
    try:
        cur.execute("SELECT * FROM sp_get_patient_id(%s);", (user_id,))
        patient_row = cur.fetchone()

        if not patient_row:
            raise HTTPException(status_code=404, detail="Patient not found")

        patient_id = patient_row[0]

        cur.execute("SELECT * FROM sp_get_medical_history(%s);", (patient_id,))
        row = cur.fetchone()

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Medical history DB error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    if row:
        return {
            "past_diagnoses": row[0],
            "surgeries": row[1],
            "hospital_admissions": row[2],
            "immunization_records": row[3],
            "family_medical_history": row[4],
            "lifestyle_factors": row[5],
        }

    raise HTTPException(status_code=404, detail="Medical history not found")


# ---------------- NORMALIZE (FAISS) ----------------

@app.post("/normalize")
async def normalize(request: Request):
    if not model or not index:
        raise HTTPException(status_code=500, detail="FAISS not initialized")

    data = await request.json()
    phrases = data.get("phrases", [])

    results = []

    for phrase in phrases:
        cleaned = preprocess_text(phrase)
        if not cleaned:
            continue

        emb = model.encode([cleaned])
        D, I = index.search(np.array(emb), 1)

        distance = D[0][0]
        match = terms[I[0][0]]

        if distance > 1.0:
            continue

        results.append({
            "original": phrase,
            "cleaned": cleaned,
            "match": match,
            "score": float(distance)
        })

    return {"results": results}


# ---------------- LANGGRAPH ----------------

@app.post("/run_langgraph")
async def run_langgraph(request: Request):
    data = await request.json()
    phrases = data.get("phrases", [])

    if not phrases:
        raise HTTPException(status_code=400, detail="No phrases provided.")

    graph = build_graph()
    final_state = graph.invoke({"phrases": phrases})

    return {
        "phrases": final_state.get("phrases", []),
        "normalized_symptoms": final_state.get("normalized_symptoms", []),
        "specialists": final_state.get("specialists", []),
        "recommended_specialists": final_state.get("recommended_specialists", []),
        "doctors": final_state.get("doctors", []),
    }


# ---------------- APPOINTMENTS ----------------

@app.post("/appointments")
def create_appointment(req: AppointmentRequest, db=Depends(get_cursor)):
    cur, conn = db
    try:
        cur.execute(
            "SELECT * FROM sp_create_appointment(%s, %s, %s, %s)",
            (req.patient_id, req.doctor_id, req.slot_id, req.reason)
        )
        appointment_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Appointment created", "appointment_id": appointment_id}

    except Exception as e:
        conn.rollback()
        logger.error(f"Appointment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")