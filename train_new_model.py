import pandas as pd
import numpy as np
import os
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from lightgbm import LGBMRegressor

print("Step 1: Preparing High-Accuracy Dataset...")
df = pd.read_csv('../mini_train.csv')
df['date'] = pd.to_datetime(df['date'])
df = df[df['unit_sales'] >= 0].copy()
df = df.sort_values(['store_nbr', 'item_nbr', 'date'])

cluster_base = df.groupby(['store_nbr', 'item_nbr'])['unit_sales'].mean().reset_index()
scaler_cluster = RobustScaler()
scaled_val = scaler_cluster.fit_transform(cluster_base[['unit_sales']])
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
cluster_base['cluster'] = kmeans.fit_predict(scaled_val)
df = df.merge(cluster_base[['store_nbr', 'item_nbr', 'cluster']], on=['store_nbr', 'item_nbr'], how='left')

print("Step 3: Engineering Memory & Trend Features...")
df['lag_1'] = df.groupby(['store_nbr', 'item_nbr'])['unit_sales'].shift(1).fillna(0)
df['lag_3'] = df.groupby(['store_nbr', 'item_nbr'])['unit_sales'].shift(3).fillna(0)
df['lag_7'] = df.groupby(['store_nbr', 'item_nbr'])['unit_sales'].shift(7).fillna(0)
df['roll_mean_7'] = df.groupby(['store_nbr', 'item_nbr'])['unit_sales'].transform(
    lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()).fillna(0)
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.dayofweek
df['onpromotion'] = df['onpromotion'].fillna(0).astype(int)

df['target'] = np.log1p(df['unit_sales'])

features = ['store_nbr', 'item_nbr', 'cluster', 'onpromotion', 'month', 'day', 'lag_1', 'lag_3', 'lag_7', 'roll_mean_7']
X = df[features]
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

print("Step 5: Running Competition...")
models = {
    "Linear": LinearRegression(),
    "LightGBM (Elite)": LGBMRegressor(n_estimators=1000, learning_rate=0.05)
}

results = []
for name, model in models.items():
    model.fit(X_train, y_train)
    actuals = np.expm1(y_test)
    preds = np.expm1(model.predict(X_test))
    r2 = r2_score(actuals, preds)
    mse = mean_squared_error(actuals, preds)
    mae = mean_absolute_error(actuals, preds)
    results.append({"Name": name, "R2": r2, "MSE": mse, "MAE": mae, "Model": model})
    print(f"{name:<18} | {r2:<10.4f}")

winner = max(results, key=lambda x: x['R2'])
print(f"\nTHE WINNING MODEL: {winner['Name']} with R2 of {winner['R2']:.4f}")

joblib.dump(winner['Model'], 'winning_demand_model.pkl')
cluster_base.to_csv('cluster_mapping.csv', index=False)
print("Saved winning_demand_model.pkl and cluster_mapping.csv")
