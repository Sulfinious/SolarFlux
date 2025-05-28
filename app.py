import base64
import io
import pandas as pd
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Solar Energy Dashboard", style={'textAlign': 'center'}),
    html.P("Загрузите CSV с данными для анализа:", style={'textAlign': 'center'}),
    dcc.Upload(
        id="upload-data",
        children=html.Button("📂 Загрузить CSV"),
        multiple=False,
        style={
            'width': '50%',
            'margin': 'auto',
            'padding': '10px',
            'border': '1px dashed #ccc',
            'textAlign': 'center'
        }
    ),
    html.Div(id="output-upload", style={'marginTop': '20px'})
])

@app.callback(
    Output("output-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename")
)
def parse_upload(contents, filename):
    if contents is None:
        return html.P("Файл не загружен.", style={'color': 'red'})
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return html.P(f"Ошибка чтения CSV: {e}", style={'color': 'red'})
    return build_dashboard(df)

@app.callback(
    Output("ts-graph", "figure"),
    [Input("period-dropdown", "value"),
     Input("upload-data", "contents")]
)
def update_ts(period, contents):
    if contents is None:
        return {}
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    df['date'] = pd.to_datetime(df['date'])
    df_resampled = df.set_index('date').resample(period).sum().reset_index()
    fig = px.line(df_resampled, x='date', y='energy_kWh',
                  title="Производство энергии (кВт·ч)")
    fig.update_layout(transition_duration=500)
    return fig

def build_dashboard(df):
    return html.Div([
        html.P(f"✅ Файл {df.shape[0]} строк успешно загружен", style={'color': 'green'}),
        dash_table.DataTable(
            id="data-table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.head(5).to_dict('records'),
            page_size=5,
            style_table={'overflowX': 'auto'}
        )
    ])

html.Div([
    html.Label("Агрегировать по:"),
    dcc.Dropdown(
        id="period-dropdown",
        options=[
            {"label": "День", "value": "D"},
            {"label": "Неделя", "value": "W"},
            {"label": "Месяц", "value": "M"},
        ],
        value="D",
        clearable=False,
        style={'width': '200px'}
    ),
    dcc.Graph(id="ts-graph")
], style={'marginTop': '30px'})


if __name__ == "__main__":
    app.run_server(debug=True)
