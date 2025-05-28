import base64
import io
import pandas as pd
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px

app = Dash(__name__)

app.layout = html.Div(
style={
        'maxWidth': '1200px',
        'margin': 'auto',
        'padding': '20px',
        'backgroundColor': '#f9f9f9'    # опционально — чуть светло-серого фона
    },
    children=[
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
    # df — DataFrame с колонками: date, energy_kWh, temperature, weather_type и т.д.

    # Интерфейс: таблица, дропдаун + график, гистограмма, scatter, pie, индикаторы
    return html.Div([

        # 1) Приветственное сообщение и таблица превью
        html.P(
            f"✅ Файл с {df.shape[0]} строками успешно загружен",
            style={'color': 'green', 'fontWeight': 'bold'}
        ),
        dash_table.DataTable(
            id="data-table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.head(5).to_dict('records'),
            page_size=5,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'}
        ),

        # 2) Dropdown + Time Series график
        html.Div([
            html.Label("Агрегировать по:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id="period-dropdown",
                options=[
                    {"label": "День",   "value": "D"},
                    {"label": "Неделя","value": "W"},
                    {"label": "Месяц", "value": "M"},
                ],
                value="D",
                clearable=False,
                style={'width': '200px', 'marginBottom': '10px'}
            ),
            dcc.Graph(id="ts-graph")
        ], style={'marginTop': '30px'}),

        # 3) Гистограмма распределения энергии
        dcc.Graph(
            id="histogram",
            figure=px.histogram(
                df,
                x="energy_kWh",
                nbins=30,
                title="Распределение выработки энергии (кВт·ч)"
            )
        ),

        # 4) Scatter-plot: температура vs энергия
        dcc.Graph(
            id="scatter",
            figure=px.scatter(
                df,
                x="temperature",
                y="energy_kWh",
                trendline="ols",
                title="Корреляция: Температура vs Энергия"
            )
        ),

        # 5) Pie-chart по типу погоды
        dcc.Graph(
            id="pie",
            figure=px.pie(
                df,
                names="weather_type",
                values="energy_kWh",
                title="Энергия по погодным условиям"
            )
        ),

        # 6) Индикаторы: среднее и максимум энергии
        html.Div([
            html.Div([
                html.H4("Среднее (кВт·ч)", style={'textAlign': 'center'}),
                html.P(f"{df['energy_kWh'].mean():.2f}", style={'textAlign': 'center'})
            ], style={'display': 'inline-block', 'width': '45%'}),
            html.Div([
                html.H4("Максимум (кВт·ч)", style={'textAlign': 'center'}),
                html.P(f"{df['energy_kWh'].max():.2f}", style={'textAlign': 'center'})
            ], style={'display': 'inline-block', 'width': '45%'})
        ], style={'marginTop': '30px'})

    ], style={'maxWidth': '1000px', 'margin': 'auto', 'padding': '20px'})



if __name__ == "__main__":
    app.run_server(debug=True)
