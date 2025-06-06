import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Define the column names based on the JSON structure
CSV_COLUMNS = ["Timestamp", "sellPrice", "sellCount", "biddingPrice", "biddingCount", "turnOver", "volume", "existingCount"]

def create_interactive_chart(json_file_path):
    """
    Reads data from a JSON file, creates an interactive Plotly chart with subplots,
    and saves it as an HTML file.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {json_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}")
        return

    if not data or 'data' not in data or not isinstance(data['data'], list):
        print(f"Error: Invalid data structure in {json_file_path}")
        return

    # Convert the list of lists to a pandas DataFrame
    raw_data = data['data']
    if not raw_data or len(raw_data[0]) != len(CSV_COLUMNS):
         print(f"Error: Data in {json_file_path} does not have the expected number of columns.")
         return

    df = pd.DataFrame(raw_data, columns=CSV_COLUMNS)

    # Convert timestamp to datetime objects (assuming Unix timestamps in seconds)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')

    # Create subplots: 2 rows, 1 column. Share the x-axis.
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('价格趋势', '数量及成交趋势')
    )

    # Add price traces to the top subplot (row 1)
    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['sellPrice'],
        mode='lines',
        name='在售价',
        visible=True
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['biddingPrice'],
        mode='lines',
        name='求购价',
        visible='legendonly' # Default hidden
    ), row=1, col=1)

    # Add count/volume/turnover traces to the bottom subplot (row 2)
    # volume as bar chart, others as line chart (default hidden)
    fig.add_trace(go.Bar(
        x=df['Timestamp'],
        y=df['volume'],
        name='成交量',
        visible=True
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['sellCount'],
        mode='lines',
        name='在售数',
        visible=True
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['biddingCount'],
        mode='lines',
        name='求购数',
        visible='legendonly' # Default hidden
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['turnOver'],
        mode='lines',
        name='成交额',
        visible='legendonly' # Default hidden
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['existingCount'],
        mode='lines',
        name='库存',
        visible='legendonly' # Default hidden
    ), row=2, col=1)

    # Update layout
    fig.update_layout(
        title_text='饰品趋势分析',
        hovermode='x unified'
    )

    # Add range slider to the shared x-axis
    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    # Update y-axis titles for each subplot
    fig.update_yaxes(title_text="价格 (¥)", row=1, col=1)
    fig.update_yaxes(title_text="数量/成交额", row=2, col=1)

    # Save the figure as an HTML file
    output_html_file = "item_trend_chart.html"
    fig.write_html(output_html_file)

    print(f"Interactive chart saved to {output_html_file}")

if __name__ == "__main__":
    # Specify the path to your JSON file
    json_data_file = "data\\23442.json"
    create_interactive_chart(json_data_file) 