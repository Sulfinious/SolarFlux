import pandas as pd
import plotly.express as px

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output

# Цветовая тема: мягкие синие, зеленые и серые
THEME = {
    'background': '#f0f2f5',  # светло-серый
    'primary': '#2c3e50',     # темно-синий
    'secondary': '#27ae60',   # зеленый
    'text': '#34495e'         # серо-синий для текста
}

# URL CSV с вашими данными (поля: date, city_id, datetime, temperature, humidity, solar_radiation)
CSV_URL = (
    "https://raw.githubusercontent.com/"
    "Sulfinious/SolarFlux/main/weathergis.csv"
)

# Инициализация приложения
app = Dash(__name__)

# Макет приложения
app.layout = html.Div(
    style={
        'backgroundColor': THEME['background'],
        'minHeight': '100vh',
        'padding': '20px'
    },
    children=[
        html.H1(
            "Solar Energy Dashboard",
            style={
                'textAlign': 'center',
                'color': THEME['primary'],
                'marginBottom': '10px'
            }
        ),
        html.P(
            "Файл weathergis.csv готов к использованию и загружается автоматически.",
            style={
                'textAlign': 'center',
                'color': THEME['text'],
                'fontStyle': 'italic'
            }
        ),
        html.Div(
            html.Button(
                "Показать анализ",
                id="show-analysis",
                n_clicks=0,
                style={
                    'fontSize': '16px',
                    'padding': '10px 20px',
                    'borderRadius': '6px',
                    'backgroundColor': THEME['secondary'],
                    'color': 'white',
                    'border': 'none',
                    'cursor': 'pointer',
                    'marginTop': '20px'
                }
            ),
            style={'textAlign': 'center'}
        ),
        html.Div(id="output-upload", style={'marginTop': '40px'})
    ]
)

# Callback для кнопки «Показать анализ»
@app.callback(
    Output("output-upload", "children"),
    Input("show-analysis", "n_clicks")
)
def on_click_show(n_clicks):
    if not n_clicks:
        return html.P(
            "Нажмите «Показать анализ», чтобы отобразить дашборд.",
            style={'textAlign': 'center', 'color': THEME['text']}
        )

    # Загружаем CSV
    try:
        df = pd.read_csv(CSV_URL)
    except Exception as e:
        return html.P(f"Ошибка загрузки CSV: {e}", style={'color': 'red'})

    # Конвертация даты
    first_col = df.columns[0]
    df = df.rename(columns={first_col: 'date'})
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Ежедневная агрегация solar_radiation (только этот столбец)
    df_resampled = (
        df.set_index('date')['solar_radiation']
        .resample('D')
        .mean()
        .reset_index()
    )

    # Графики по solar_radiation
    ts_fig = px.line(
        df_resampled,
        x='date', y='solar_radiation',
        title='Средняя солнечная радиация (Вт/м²) — ежедневная агрегация',
        color_discrete_sequence=[THEME['primary']]
    )
    hist_fig = px.histogram(
        df,
        x='solar_radiation',
        nbins=30,
        title='Распределение солнечной радиации',
        color_discrete_sequence=[THEME['secondary']]
    )
    scatter_fig = px.scatter(
        df,
        x='temperature',
        y='solar_radiation',
        title='Температура vs Солнечная радиация',
        color_discrete_sequence=[THEME['primary']]
    )

    # Таблица и индикаторы
    avg_rad = df['solar_radiation'].dropna().mean()
    max_rad = df['solar_radiation'].dropna().max()

    return html.Div([
        # Превью таблицы
        html.P(
            f"✅ Загружено {df.shape[0]} строк с данными.",
            style={'color': THEME['secondary'], 'fontWeight': 'bold'}
        ),
        dash_table.DataTable(
            columns=[{'name': i, 'id': i} for i in df.columns],
            data=df.head(5).to_dict('records'),
            page_size=5,
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': THEME['primary'], 'color': 'white'},
            style_cell={'textAlign': 'left', 'color': THEME['text']}
        ),
        # Графики
        dcc.Graph(id='ts-graph', figure=ts_fig),
        dcc.Graph(id='histogram', figure=hist_fig),
        dcc.Graph(id='scatter', figure=scatter_fig),
        # Индикаторы: среднее и максимум
        html.Div([
            html.Div([
                html.H4('Средняя радиация (Вт/м²)', style={'textAlign': 'center', 'color': THEME['primary']}),
                html.P(f"{avg_rad:.2f}", style={'textAlign': 'center', 'color': THEME['text']})
            ], style={'display': 'inline-block', 'width': '45%'}),
            html.Div([
                html.H4('Максимальная радиация (Вт/м²)', style={'textAlign': 'center', 'color': THEME['primary']}),
                html.P(f"{max_rad:.2f}", style={'textAlign': 'center', 'color': THEME['text']})
            ], style={'display': 'inline-block', 'width': '45%'})
        ], style={'marginTop': '20px'})

    ], style={'maxWidth': '1000px', 'margin': 'auto', 'padding': '20px'})

# Точка входа
if __name__ == '__main__':
    app.run(debug=True)