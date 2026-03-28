import pandas as pd
import numpy as np
import joblib
import sklearn
import lightgbm

model = joblib.load('winning_demand_model.pkl')
cluster_df = pd.read_csv('cluster_mapping.csv')
samples = cluster_df.sample(200, random_state=42)

results = []
for _, row in samples.iterrows():
    s = int(row['store_nbr'])
    i = int(row['item_nbr'])
    c = int(row['cluster'])
    
    # Low scenario
    input_low = pd.DataFrame([{
        "store_nbr": s, "item_nbr": i, "cluster": c, "onpromotion": 0,
        "month": 2, "day": 1, "lag_1": 0.0, "lag_3": 0.0, "lag_7": 0.0, "roll_mean_7": 0.0
    }])
    pred_low = max(0, float(np.expm1(model.predict(input_low)[0])))
    
    # High scenario
    input_high = pd.DataFrame([{
        "store_nbr": s, "item_nbr": i, "cluster": c, "onpromotion": 1,
        "month": 12, "day": 5, "lag_1": 0.0, "lag_3": 0.0, "lag_7": 0.0, "roll_mean_7": 0.0
    }])
    pred_high = max(0, float(np.expm1(model.predict(input_high)[0])))
    
    results.append({'store': s, 'item': i, 'promo': 'No', 'date': '02/XX/2026', 'price': 5.99, 'units': int(round(pred_low)), 'rev': pred_low*5.99})
    results.append({'store': s, 'item': i, 'promo': 'Yes', 'date': '12/XX/2026', 'price': 299.99, 'units': int(round(pred_high)), 'rev': pred_high*299.99})

results.sort(key=lambda x: x['units'])
print("LOWEST:  ", results[0])
print("MEDIAN:  ", results[len(results)//2])
print("HIGHEST: ", results[-1])
