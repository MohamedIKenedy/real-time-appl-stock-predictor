import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

df = pd.read_csv(r'application/excel_and_csv/nasdaq.csv')
n=len(df)
nasdaq=[]
df1=df[['Symbol','Name']]
df1.loc[:,'Name'] = df1.loc[:,'Name'].str.capitalize()
df1.sort_values(by='Name', inplace=True)
df1.reset_index(drop=True, inplace=True)

for i in range(n):
    strin = df1.loc[i,'Name']
    if len(strin)>130:
        df1.loc[i,'Name'] = strin[:130]

for i in range(n):
    nasdaq.append((df1.loc[i,'Symbol'],df1.loc[i,'Name']))