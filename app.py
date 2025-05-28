# ┌──────────────────────────────────────────────────────────
# │ 1. Импортируем всё необходимое
import base64
import io

import pandas as pd
import plotly.express as px

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
# └──────────────────────────────────────────────────────────


# ┌──────────────────────────────────────────────────────────
# │ 2. Инициализация Dash‑приложения
app = Dash(__name__)
# └──────────────────────────────────────────────────────────


# ┌──────────────────────────────────────────────────────────
# │ 3. Описание макета (layout) — здесь обёртка и все виджеты
app.layout = html.Div(
    style={
        'maxWidth': '1200px',
        'margin': 'auto',
        'padding': '20px',
        'backgroundColor': '#f9f9f9'
    },
    children=[

        # Заголовок и подзаголовок
        html.H1("Solar Energy Dashboard", style={'textAlign': 'center'}),
        html.P("Загрузите CSV с данными для анализа:", style={'textAlign': 'center'}),

        # Кнопка загрузки
        dcc.Upload(
            id="upload-data",
            children=html.Button(
                "📂 Загрузить CSV",
                style={
                    'fontSize': '16px',
                    'padding': '10px 20px',
                    'borderRadius': '5px',
                    'backgroundColor': '#007BFF',
                    'color': 'white',
                    'border': 'none',
                    'cursor': 'pointer'
                }
            ),
            multiple=False,
            style={
                'width': '50%',
                'margin': 'auto',
                'padding': '10px',
                'border': '1px dashed #ccc',
                'textAlign': 'center'
            }
        ),

        # Контейнер для всего, что появится после загрузки
        html.Div(id="output-upload", style={'marginTop': '20px'})

    ]
)
# └──────────────────────────────────────────────────────────


# ┌──────────────────────────────────────────────────────────
# │ 4. Callback для обработки загрузки и рендеринга дашборда
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

    # После успешной загрузки покажем весь дашборд:
    return build_dashboard(df)
# └──────────────────────────────────────────────────────────


# ┌──────────────────────────────────────────────────────────
# │ 5. Callback для обновления именно Time Series графика
@app.callback(
    Output("ts-graph", "figure"),
    [
        Input("period-dropdown", "value"),
        Input("upload-data", "contents")
    ]
)
def update_ts(period, contents):
    if contents is None:
        return {}

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    df['date'] = pd.to_datetime(df['date'])
    df_resampled = df.set_index('date').resample(period).sum().reset_index()

    fig = px.line(
        df_resampled,
        x='date',
        y='energy_kWh',
        title="Производство энергии (кВт·ч)"
    )
    fig.update_layout(transition_duration=500)
    return fig
# └──────────────────────────────────────────────────────────


# ┌──────────────────────────────────────────────────────────
# │ 6. Функция build_dashboard — собирает все графики + таблицы
def build_dashboard(df):
    return html.Div([

        # — 1) Превью таблицы
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

        # — 2) Dropdown + Time Series график
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

        # — 3) Гистограмма
        dcc.Graph(
            id="histogram",
            figure=px.histogram(
                df,
                x="energy_kWh",
                nbins=30,
                title="Распределение выработки энергии (кВт·ч)"
            )
        ),

        # — 4) Scatter: температура vs энергия
        dcc.Graph(
            id="scatter",
            figure=px.scatter(
                df,
                x="temperature",
                y="energy_kWh",
                trendline="ols",
                title="Температура vs Энергия"
            )
        ),

        # — 5) Pie: по погодным условиям
        dcc.Graph(
            id="pie",
            figure=px.pie(
                df,
                names="weather_type",
                values="energy_kWh",
                title="Энергия по погодным условиям"
            )
        ),

        # — 6) Индикаторы среднего и максимума
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
# └──────────────────────────────────────────────────────────


# ┌──────────────────────────────────────────────────────────
# │ 7. Точка входа — запуск сервера
if __name__ == "__main__":
    app.run_server(debug=True)
# └──────────────────────────────────────────────────────────
