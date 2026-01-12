import os
import numpy as np
from xgboost import XGBRanker

os.makedirs("../models", exist_ok=True)

# Dummy data
X = np.array([
    [1.2, 3, 0.8],
    [0.5, 5, 0.6],
    [2.0, 2, 0.9],
    [1.0, 4, 0.7]
])

y = np.array([1, 0, 1, 0])
group = np.array([2, 2])  # two ATMs per complaint

ranking_model = XGBRanker(
    objective="rank:pairwise",
    tree_method="hist",
    max_depth=5,
    learning_rate=0.1,
    n_estimators=100
)

ranking_model.fit(X, y, group=group)
ranking_model.save_model("../models/model2.json")

print("✅ model2.json created successfully")
