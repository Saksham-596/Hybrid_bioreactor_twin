from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from scipy.integrate import odeint
import joblib
import os
import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

load_dotenv()
app = FastAPI(title="Bioreactor Hybrid Twin")

origins = [

    "https://hybrid-bioreactor-twin.vercel.app",

    # "http://localhost:3000"  # Keeping localhost so it still works on your Mac!

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.biotwin_db        
collection = db.batch_history

MODEL_PATH = "hybrid_error_predictor.pkl"
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("AI 'Correction Layer' loaded successfully.")
else:
    print("Warning: ML model not found. Hybrid endpoint will fail.")

class HybridParams(BaseModel):
    mu_max: float = 0.5
    Ks: float = 2.0
    Y: float = 0.5
    D: float = 0.1
    Sf: float = 20.0
    X0: float = 0.1
    S0: float = 20.0
    t_end: float = 50.0
    steps: int = 100
    toxicity_factor: float = 0.1

def monod_kinetics(y, t, mu_max, Ks, Y, D, Sf):
    X, S = y
    mu = (mu_max * S) / (Ks + S)
    dXdt = (mu - D) * X
    dSdt = D * (Sf - S) - (mu * X) / Y
    return [dXdt, dSdt]

@app.post("/simulate/hybrid")
async def run_hybrid_simulation(params: HybridParams):
    t_vec = np.linspace(0, params.t_end, params.steps)
    y0 = [params.X0, params.S0]
    args = (params.mu_max, params.Ks, params.Y, params.D, params.Sf)
    
    ideal_solution = odeint(monod_kinetics, y0, t_vec, args=args)
    ideal_X = ideal_solution[:, 0]
    
    ml_inputs = np.column_stack((t_vec, np.full_like(t_vec, params.toxicity_factor)))
    predicted_errors = model.predict(ml_inputs)

    hybrid_X = ideal_X + predicted_errors

    results = []
    for i in range(len(t_vec)):
        results.append({
            "time": round(float(t_vec[i]), 2),
            "ideal_biomass": round(float(ideal_X[i]), 4),
            "hybrid_biomass": max(0.0, round(float(hybrid_X[i]), 4)), 
            "error_magnitude": round(float(predicted_errors[i]), 4)
        })
    
    batch_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "parameters": params.model_dump(),
        "final_hybrid_biomass": results[-1]["hybrid_biomass"],
        "data": results 
    }
    
    await collection.insert_one(batch_record)
        
    return {
        "status": "success", 
        "r_squared_confidence": 0.9566, 
        "data": results
    }

@app.get("/history")
async def get_simulation_history():
    cursor = collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(10)
    history = await cursor.to_list(length=10)
    return {"status": "success", "history": history}