import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')
model = joblib.load(MODEL_PATH)

def predict(features):
    result = model.predict([features])
    return result[0]