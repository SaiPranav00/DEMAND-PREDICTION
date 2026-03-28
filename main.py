from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import sklearn
import lightgbm
import warnings

warnings.filterwarnings('ignore')

app = FastAPI(title="Demand Model API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model
MODEL_PATH = r"c:\Users\saipr\Desktop\IDS\backend\winning_demand_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Failed to load model from {MODEL_PATH}: {e}")
    model = None

# Load cluster mapping
MAPPING_PATH = r"c:\Users\saipr\Desktop\IDS\backend\cluster_mapping.csv"
try:
    cluster_df = pd.read_csv(MAPPING_PATH)
    print("Cluster mapping loaded successfully.")
except Exception as e:
    print(f"Failed to load cluster mapping: {e}")
    cluster_df = None

class DemandRequest(BaseModel):
    Store: int
    Item: int
    Date: str
    OnPromotion: bool
    UnitPrice: float

@app.post("/predict")
async def predict_demand(data: DemandRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model failed to load.")
    
    assigned_cluster = 0
    if cluster_df is not None:
        match = cluster_df[(cluster_df['store_nbr'] == data.Store) & (cluster_df['item_nbr'] == data.Item)]
        if not match.empty:
            assigned_cluster = int(match['cluster'].iloc[0])

    dt = pd.to_datetime(data.Date)
    
    on_promo = 1 if data.OnPromotion else 0

    # Default lags to 0 since we do not have historical data in the API request
    input_data = pd.DataFrame([{
        "store_nbr": data.Store,
        "item_nbr": data.Item,
        "cluster": assigned_cluster,
        "onpromotion": on_promo,
        "month": dt.month,
        "day": dt.dayofweek,  # Using dayofweek as in training script
        "lag_1": 0.0,
        "lag_3": 0.0,
        "lag_7": 0.0,
        "roll_mean_7": 0.0
    }])
    
    try:
        # Predict uses expm1 since training target was log1p
        import numpy as np
        log_pred = model.predict(input_data)[0]
        units_pred = max(0, float(np.expm1(log_pred)))
        revenue_pred = units_pred * data.UnitPrice
        
        return {
            "prediction_units": round(units_pred),
            "prediction_revenue": round(revenue_pred, 2)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
