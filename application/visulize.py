import pandas as pd
from plotly import graph_objs as go
# from fbprophet import Prophet
# from fbprophet.plot import plot_plotly

def plot_raw_data(file_path,company_symbol):
    if file_path.endswith('csv'):
        data = pd.read_csv(file_path)
    elif file_path.endswith('xlsx'):
        data = pd.read_excel(file_path)
    fig = go.Figure()
    fig.add_trace( go.Scatter(x=data['Date'], y=data['Open'], name='stock_open'))
    fig.add_trace( go.Scatter(x=data['Date'], y=data['Close'], name='stock_close'))
    fig.layout.update(
        title_text=f"Time Series Data of {company_symbol}",
        xaxis_rangeslider_visible=True,
        autosize=False,
        width=1000,
        height=700,
    )
    return fig