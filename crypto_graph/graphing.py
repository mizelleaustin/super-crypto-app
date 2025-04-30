# %% graphing, candlestick, line
import plotly.graph_objects as go

def plot_candlestick_from_store(crypto_data_store, ticker):
    """
    Plots a candlestick chart for the given ticker from a preloaded data store.

    Parameters:
    - crypto_data_store (dict): Dictionary of DataFrames keyed by ticker symbol.
    - ticker (str): The ticker symbol to plot.
    """
    df = crypto_data_store[ticker]

    if df is None or df.empty:
        print(f"No data found for ticker: {ticker}")
        return

    df = df.sort_values(by='Date' if 'Date' in df.columns else df.index.name)
    x_values = df['Date'] if 'Date' in df.columns else df.index

    fig = go.Figure(data=[go.Candlestick(
        x=x_values,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=ticker
    )])

    fig.update_layout(
        title=f'Candlestick Chart for {ticker}',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        xaxis_rangeslider_visible=False,
        template='plotly_dark'
    )

    return fig


def plot_line_chart_from_store(crypto_data_store, ticker):
    """
    Plots a line chart of the closing price for a given ticker.

    Parameters:
    - crypto_data_store (dict): Dictionary of DataFrames keyed by ticker symbol.
    - ticker (str): The ticker symbol to plot.
    """
    df = crypto_data_store[ticker]

    if df is None or df.empty:
        print(f"No data found for ticker: {ticker}")
        return

    df = df.sort_values(by='Date' if 'Date' in df.columns else df.index.name)
    x_values = df['Date'] if 'Date' in df.columns else df.index

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_values,
        y=df['Close'],
        mode='lines',
        name='Close Price'
    ))

    fig.update_layout(
        title=f'Line Chart of Closing Price for {ticker}',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        template='plotly_dark'
    )

    return fig

