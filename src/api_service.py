from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, status
import src.auth as auth

# 🟢 Impor RELATIF untuk Agen (menggunakan nama file yang benar)
from .NovelChemicalDiscoveryAgent import NovelChemicalDiscoveryAgent 

# ==============================================================================
# 1. ⚙️ KONFIGURASI FASTAPI
# ==============================================================================

app = FastAPI(title="Chemical Discovery Agent API", version="1.0.0")

# Konfigurasi CORS
origins = ["http://127.0.0.1", "http://localhost:8000", "http://localhost:3000", "http://127.0.0.1:3000"] 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inisialisasi Agen (Memuat model dan Gemini Client saat startup)
agent = NovelChemicalDiscoveryAgent()


# ==============================================================================
# 2. 📚 DEFINISI SKEMA DATA (Pydantic)
# ==============================================================================

class CriteriaInput(BaseModel):
    Solubility: float
    Viscosity_cP: float
    ThermalStability_Score: float
    BoilingPoint_C: float

class CompoundProperties(BaseModel):
    SMILES: str
    IUPAC: str
    InChI: str
    InChIKey: str
    MolWeight: float
    ExactMass: float
    HBondDonors: int
    HBondAcceptors: int
    TPSA: float
    LogP: float
    RotatableBonds: int

class RecommendedCompound(BaseModel):
    SMILES: str
    Properties: CompoundProperties
    Structure_2D_Path: Optional[str]
    Structure_3D_Path: Optional[str]

class DiscoveryResponse(BaseModel):
    recommended_compound: RecommendedCompound
    justification_ai: str


# ==============================================================================
# 3. 🗺️ ENDPOINT API
# ==============================================================================

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Chemical Discovery Agent API is running."}

@app.post("/register")
def register(user: auth.UserRegister):
    print(f"DEBUG: Register endpoint called for {user.username}")
    user_found = auth.get_user_by_username(user.username)
    if user_found:
        print(f"DEBUG: Register failed - User {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    try:
        hashed_password = auth.get_password_hash(user.password)
        success = auth.create_user(user.username, hashed_password)
        if not success:
            print(f"DEBUG: Register failed - Database creation returned False")
            raise HTTPException(status_code=500, detail="Failed to create user")
        print(f"DEBUG: Register success for {user.username}")
        return {"message": "User created successfully"}
    except Exception as e:
        print(f"DEBUG: Exception in register: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/token", response_model=auth.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"DEBUG: Login attempted for {form_data.username}")
    user = auth.get_user_by_username(form_data.username)
    if not user:
        print(f"DEBUG: Login failed - User not found")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # user[1] is hashed_password from sqlite tuple
    try:
        is_valid = auth.verify_password(form_data.password, user[1])
        if not is_valid:
             print(f"DEBUG: Login failed - Password mismatch")
             raise HTTPException(status_code=401, detail="Incorrect username or password")
    except Exception as e:
         print(f"DEBUG: Exception verifying password: {e}")
         raise HTTPException(status_code=500, detail=f"Crypto Error: {str(e)}")
    
    print(f"DEBUG: Login success for {form_data.username}")
    access_token = auth.create_access_token(data={"sub": user[0]})
    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    username = auth.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


@app.post("/discover", response_model=DiscoveryResponse)
async def discover_compound(criteria: CriteriaInput, current_user: str = Depends(get_current_user)):
    if agent.predictor is None or agent.client is None:
        raise HTTPException(status_code=503, detail="Layanan tidak siap.")

    compound_data_raw = agent.predict_and_lookup(criteria.dict())
    justification = agent.get_justification(criteria.dict(), compound_data_raw)
    
    final_response = {
        "recommended_compound": compound_data_raw["recommended_compound"],
        "justification_ai": justification
    }
    
    return final_response


@app.get("/results/{filename}")
async def get_results_file(filename: str):
    file_path = os.path.join(agent.RESULTS_DIR, filename)
    
    if not os.path.exists(file_path) or not file_path.startswith(agent.RESULTS_DIR):
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")
    
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".mol"):
        media_type = "chemical/x-mol"
    else:
        media_type = "application/octet-stream"

    return FileResponse(file_path, media_type=media_type)