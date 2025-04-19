import pandas as pd
import os
import matplotlib.pyplot as plt
import datetime
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
#cwd = os.chdir('/Users/anishrayaguru/Desktop/SCLU')
#df = pd.read_csv('/workexcelsheets/27300penifty_regress.csv')
df = pd.read_csv('/Users/anishrayaguru/Desktop/SCLU/workexcelsheets/27300penifty_regress.csv')

#print(df['oi'])
#print(df['oi'][0])
#print(df.head(5))
oi = df['oi'][66:77]
print(oi)
index = df['index'][66:77]


#x = list()
print(len(oi))
#for i in range(len(oi)):
#    x.append(i)

model = LinearRegression()
model.fit(index, oi)

oi_pred = model.predict(df[index][66:77])

forecast = model.predict(df.index[75:80])

plt.scatter(df['index'],df['oi'], color = 'blue')
plt.plot(df[index][75:80], forecast, color = "red")
#plt.plot(df['oi'])
plt.show()