# from unittest import result

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import numpy as np
# from scipy.integrate import odeint
# import joblib
# import os
# import certifi
# from dotenv import load_dotenv
# from motor.motor_asyncio import AsyncIOMotorClient
# from datetime import datetime

# load_dotenv()
# app = FastAPI(title="Bioreactor Hybrid Twin")

# origins = [

#     "https://hybrid-bioreactor-twin.vercel.app",

#     # "http://localhost:3000"  # Keeping localhost so it still works on your Mac!

# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# MONGO_URI = os.getenv("MONGO_URI")
# client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
# db = client.biotwin_db        
# collection = db.batch_history

# MODEL_PATH = "bio_twin_model.pkl"
# if os.path.exists(MODEL_PATH):
#     model = joblib.load(MODEL_PATH)
#     print("AI 'Correction Layer' loaded successfully.")
# else:
#     print("Warning: ML model not found. Hybrid endpoint will fail.")

# class HybridParams(BaseModel):
#     session_id :str ="anonymous"
#     mu_max: float = 0.5
#     Ks: float = 2.0
#     Y: float = 0.5
#     D: float = 0.1
#     Sf: float = 20.0
#     X0: float = 0.1
#     S0: float = 20.0
#     t_end: float = 50.0
#     steps: int = 100
#     toxicity_factor: float = 0.1

# def monod_kinetics(y, t, mu_max, Ks, Y, D, Sf):
#     X, S = y
#     mu = (mu_max * S) / (Ks + S)
#     dXdt = (mu - D) * X
#     dSdt = D * (Sf - S) - (mu * X) / Y
#     return [dXdt, dSdt]

# @app.post("/simulate/hybrid")
# async def run_hybrid_simulation(params: HybridParams):
#     t_vec = np.linspace(0, params.t_end, params.steps)
#     y0 = [params.X0, params.S0]
#     args = (params.mu_max, params.Ks, params.Y, params.D, params.Sf)
    
#     ideal_solution = odeint(monod_kinetics, y0, t_vec, args=args)
#     ideal_X = ideal_solution[:, 0]
    
#     ml_inputs = np.column_stack((t_vec, np.full_like(t_vec, params.toxicity_factor)))
#     predicted_errors = model.predict(ml_inputs)

#     hybrid_X = ideal_X + predicted_errors

#     results = []
#     for i in range(len(t_vec)):
#         results.append({
#             "time": round(float(t_vec[i]), 2),
#             "ideal_biomass": round(float(ideal_X[i]), 4),
#             "hybrid_biomass": max(0.0, round(float(hybrid_X[i]), 4)), 
#             "error_magnitude": round(float(predicted_errors[i]), 4)
#         })
    
#     batch_record = {
#         "session_id": params.session_id,
#         "timestamp": datetime.utcnow().isoformat(),
#         "parameters": params.model_dump(),
#         "final_hybrid_biomass": results[-1]["hybrid_biomass"],
#         "data": results 
#     }
    
#     await collection.insert_one(batch_record)
        
#     return {
#         "status": "success", 
#         "r_squared_confidence": 0.9566, 
#         "data": results
#     }

# @app.get("/history")
# async def get_simulation_history(session_id: str="anonymous"):
#     cursor = collection.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", -1).limit(10)
#     history = await cursor.to_list(length=10)
#     return {"status": "success", "history": history}

# @app.delete("/history/clear")
# async def clear_simulation_history(session_id: str ="anonymous"):
#     result = await collection.delete_many({"session_id": session_id})
#     return {"status": "success", "delete_count": result.deleted_count}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import pandas as pd
import joblib
import os
import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from scipy.integrate import odeint

load_dotenv()
app = FastAPI(title="Bioreactor Hybrid Twin")

origins = [
    "https://hybrid-bioreactor-twin.vercel.app",
    "http://localhost:3000"  
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

MODEL_PATH = "bio_twin_model.pkl"
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("XGBoost Digital Twin Engine loaded successfully.")
else:
    print("Warning: bio_twin_model.pkl not found. Endpoint will fail.")

#(Monod Kinetics)
def monod_kinetics(y, t, mu_max, Ks, Y, D, Sf):
    X, S = y
    mu = (mu_max * S) / (Ks + S)
    dXdt = (mu - D) * X
    dSdt = D * (Sf - S) - (mu * X) / Y
    return [dXdt, dSdt]

class TwinParams(BaseModel):
    session_id: str = "anonymous"
    Aeration_rate: float = 60.0              
    Vessel_Weight: float = 60000.0           
    Air_head_pressure: float = 1.1           
    DO2: float = 15.0                        
    Oil_flow: float = 20.0                   
    Vessel_Volume: float = 60000.0           
    Substrate_concentration: float = 10.0    
    O2_percent_outgas: float = 18.0          
    
    t_end: float = 250.0 
    steps: int = 500     

@app.post("/simulate/hybrid")
async def run_twin_simulation(params: TwinParams):
    t_vec = np.linspace(0, params.t_end, params.steps)
    
    
    y0 = [0.1, params.Substrate_concentration] 
    args = (0.5, 2.0, 1.5, 0.05, params.Substrate_concentration*1.6) 
    ideal_solution = odeint(monod_kinetics, y0, t_vec, args=args)
    ideal_X = ideal_solution[:, 0]

    #  (With Smoothing)
    input_df = pd.DataFrame({
        'Time (h)': t_vec,
        'Aeration rate(Fg:L/h)': params.Aeration_rate,
        'Vessel Weight(Wt:Kg)': params.Vessel_Weight,
        'Air head pressure(pressure:bar)': params.Air_head_pressure,
        'Dissolved oxygen concentration(DO2:mg/L)': params.DO2,
        'Oil flow(Foil:L/hr)': params.Oil_flow,
        'Vessel Volume(V:L)': params.Vessel_Volume,
        'Substrate concentration(S:g/L)': params.Substrate_concentration,
        'Oxygen in percent in off-gas(O2:O2  (%))': params.O2_percent_outgas
    })
    
    raw_predictions = model.predict(input_df)
    smoothed_predictions = pd.Series(raw_predictions).ewm(span=40).mean().values

    
    results = []
    for i in range(len(t_vec)):
        ml_val = max(0.0, float(smoothed_predictions[i]))
        ideal_val = max(0.0, float(ideal_X[i]))
        results.append({
            "time": round(float(t_vec[i]), 2),
            "predicted_biomass_g_L": round(ml_val, 4),
            "ideal_biomass": round(ideal_val, 4) 
        })
    
    batch_record = {
        "session_id": params.session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "parameters": params.model_dump(),
        "final_predicted_biomass": results[-1]["predicted_biomass_g_L"],
        "data": results 
    }
    
    await collection.insert_one(batch_record)
        
    return {
        "status": "success", 
        "r_squared_confidence": 0.9868, 
        "data": results
    }

@app.get("/history")
async def get_simulation_history(session_id: str="anonymous"):
    cursor = collection.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", -1).limit(10)
    history = await cursor.to_list(length=10)
    return {"status": "success", "history": history}

@app.delete("/history/clear")
async def clear_simulation_history(session_id: str ="anonymous"):
    result = await collection.delete_many({"session_id": session_id})
    return {"status": "success", "delete_count": result.deleted_count}