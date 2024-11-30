import pandas as pd
# from fbprophet import Prophet
# from fbprophet.plot import plot_plotly
from plotly import graph_objs as go



def predict_data(n_days,path_upload, path_to_save,extension_to_save='CSV'):
    # period = n_days
    # excsel_file = path_upload.endswith('xlsx')
    # if excsel_file:
    #     data=pd.read_excel(path_upload)
    # else:
    #     data=pd.read_csv(path_upload)

    # #preprocessing data
    # df_train = data[['Date', 'Close']]
    # df_train = df_train.rename(columns={'Date': 'ds', 'Close': 'y'})

    # #training the model
    # m = Prophet()
    # m.fit(df_train)

    # #predicting results
    # future = m.make_future_dataframe(periods=period)
    # forecast = m.predict(future)
    # forecast.drop(['additive_terms', 'additive_terms_lower', 'additive_terms_upper', 'multiplicative_terms', 'multiplicative_terms_lower', 'multiplicative_terms_upper'], axis=1, inplace=True)
    # if extension_to_save=='XLSX':
    #     forecast.to_excel(path_to_save + 'forecast.xlsx', index=False)
    # elif extension_to_save=='CSV':
    #     forecast.to_csv(path_to_save + 'forecast.csv', index=False)

    # fig1 = plot_plotly(m, forecast)
    # fig1.layout.update(
    #     title_text=f"Time Series of Forecasted Data",
    #     xaxis_rangeslider_visible=True,
    #     autosize=False,
    #     width=1000,
    #     height=700,
    #     xaxis_title="Date Time",
    #     yaxis_title="Close Price"
    # )
    # forecast.rename(columns={'ds':'Date Time', 'y':'Close Price'}, inplace=True)
    # return forecast, data.loc[0,'Company Symbol'], fig1
    return None