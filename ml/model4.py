import os
import numpy as np
import xgboost as xgb

os.makedirs("../models", exist_ok=True)

# Dummy data
X = np.array([
    [0.4, 5, 10, 300, 0.3, 0.1, 0.5],
    [0.7, 8, 15, 500, 0.5, 0.2, 0.8],
    [0.2, 2, 4, 150, 0.1, 0.05, 0.3]
])

y = np.array([0.3, 0.8, 0.2])

hotspot_model = xgb.XGBRegressor(
    objective="reg:squarederror",
    tree_method="hist",
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05
)

hotspot_model.fit(X, y)
hotspot_model.save_model("../models/model4.json")

print("✅ model4.json created successfully")
