import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import joblib
import numpy as np

data = pd.read_csv("dataset.csv")
data = pd.concat([data]*20, ignore_index=True)
data['LOC'] += np.random.randint(-10, 10, size=len(data))
data['Loops'] += np.random.randint(-2, 3, size=len(data))
data['Conditions'] += np.random.randint(-2, 3, size=len(data))
data['Complexity'] += np.random.randint(-5, 5, size=len(data))

data[['LOC','Loops','Conditions','Complexity']] = data[['LOC','Loops','Conditions','Complexity']].clip(lower=0)

print("Total rows:", len(data))

print("\nLabel distribution:\n", data['Label'].value_counts())

X = data[['LOC','Loops','Conditions','Complexity']]
y = data['Label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, zero_division=0))

scores = cross_val_score(model, X, y, cv=5)
print("\nCross-validation scores:", scores)
print("Average accuracy:", scores.mean())

joblib.dump(model, "model.pkl")

print("\nModel trained and saved!")