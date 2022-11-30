import pandas as pd
import numpy as np
import openpyxl
from imblearn.over_sampling import SMOTE #Overcome imbalanced dataset
 
# training model
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score

# save model
import joblib
import os

df = pd.read_excel("Data.xlsx")
df.columns = ['Tanggal', 'Waktu', 'Suhu(*C)', 'Kelembaban_Udara(%)', 'Intensitas_Cahaya(Lux)', 'Label', 'Keterangan']
df = df[6:]

#Oversampling the data
label = df['Label'].astype('int')
smote = SMOTE(random_state = 101, k_neighbors = 1)
X, y = smote.fit_resample(df[['Suhu(*C)', 'Kelembaban_Udara(%)', 'Intensitas_Cahaya(Lux)']], label)
#Creating a new Oversampling Data Frame
df_oversampler = pd.DataFrame(X, columns = ['Suhu(*C)', 'Kelembaban_Udara(%)', 'Intensitas_Cahaya(Lux)'])
df_oversampler['label'] = y

# Splitting dataset
x = df_oversampler.iloc[:,:-1]
y = df_oversampler.iloc[:,-1]
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.2, random_state = 12)

# --------------------- Training Section -------------------
# KNN
model = KNeighborsClassifier(n_neighbors = 4, weights = 'distance', p = 1)
model.fit(x_train, y_train)
y_pred = model.predict(x_test)
accuracy = accuracy_score(y_pred, y_test)
print(f'akurasi K-NN : {accuracy*100} %')
joblib.dump(model, "./knn.joblib")

# random forest
rf = RandomForestClassifier(class_weight='balanced',random_state=42)
rf.fit(x_train,y_train)
y_pred2 = rf.predict(x_test)
print(f'akurasi Random Forest: {rf.score(x_test, y_test)*100} %')
joblib.dump(rf, "./random_forest.joblib")