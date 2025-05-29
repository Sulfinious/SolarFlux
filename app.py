import pandas as pd
import numpy as np
import plotly.express as px

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output

# Цветовая тема
THEME = {
    'background': '#f0f2f5',
    'primary': '#2c3e50',
    'secondary': '#27ae60',
    'text': '#34495e'
}

CSV_URL = (
    "https://raw.githubusercontent.com/"
    "Sulfinious/SolarFlux/main/weathergis.csv"
)

app = Dash(__name__)

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
                    'fontSize': '23px',
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

    # Загружаем CSV и сразу парсим datetime
    try:
        df = pd.read_csv(CSV_URL, parse_dates=['datetime'])
    except Exception as e:
        return html.P(f"Ошибка загрузки CSV: {e}", style={'color': 'red'})

    # Удаляем лишний столбец, если он есть
    if 'unique_id' in df.columns:
        df = df.drop(columns=['unique_id'])

    # Добавляем колонку date (без времени) для агрегации по дням
    df['date'] = df['datetime'].dt.normalize()

    # Расчёт ежедневного среднего солнечной радиации
    df_daily = (
        df
        .groupby('date', as_index=False)['solar_radiation']
        .mean()
    )

    # Категории для круговой диаграммы
    df_daily['category'] = np.where(
        df_daily['solar_radiation'] < 100,
        '< 100 Вт/м²',
        '≥ 100 Вт/м²'
    )
    # Подсчёт количества дней в каждой категории
    pie_data = (
        df_daily['category']
        .value_counts()
        .reset_index()
        .rename(columns={'index': 'category'})
    )

    # Графики
    ts_fig = px.line(
        df,
        x='datetime', y='solar_radiation',
        title='Солнечная радиация (Вт/м²)',
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
    pie_fig = px.pie(
        pie_data,
        names='category',
        values='count',
        title='Дней с солнечной радиацией <100 и ≥100 Вт/м²',
        color_discrete_sequence=[THEME['primary'], THEME['secondary']]
    )

    # Статистики
    avg_rad = df['solar_radiation'].dropna().mean()
    max_rad = df['solar_radiation'].dropna().max()

    return html.Div([
        html.P(
            f"✅ Загружено {df.shape[0]} строк с данными; дней в выборке: {df_daily.shape[0]}.",
            style={'color': THEME['secondary'], 'fontWeight': 'bold'}
        ),

        dash_table.DataTable(
            columns=[{'name': col, 'id': col} for col in df.columns if col != 'date'],
            data=df.drop(columns=['date']).to_dict('records'),
            page_action='none',
            virtualization=True,
            fixed_rows={'headers': True},
            style_table={
                'maxHeight': '600px',
                'overflowY': 'auto',
                'overflowX': 'auto'
            },
            style_header={'backgroundColor': THEME['primary'], 'color': 'white'},
            style_cell={'textAlign': 'left', 'color': THEME['text']}
        ),

        # Линейный график
        dcc.Graph(id='ts-graph', figure=ts_fig),

        # Гистограмма
        dcc.Graph(id='histogram', figure=hist_fig),

        # Точечный график
        dcc.Graph(id='scatter', figure=scatter_fig),

        # Круговая диаграмма
        dcc.Graph(id='pie-chart', figure=pie_fig),

        # Индикаторы: среднее и максимум
        html.Div([
            html.Div([
                html.H4('Средняя радиация (Вт/м²)', style={'textAlign': 'center', 'color': THEME['primary']}),
                html.P(f"{avg_rad:.2f}", style={'textAlign': 'center', 'color': THEME['text']})
            ], style={'display': 'inline-block', 'width': '45%'}),
            html.Div([
                html.H4('Максимальная радиация (Вт/м²)', style={'textAlign': 'center', 'color': THEME['primary']}),
                html.P(f"{max_rad:.2f}", style={'textAlign': 'center', 'color': THEME['text']})
            ], style={'display': 'inline-block', 'width': '45%'}),
        ], style={'marginTop': '20px'})
    ], style={'maxWidth': '1200px', 'margin': 'auto', 'padding': '20px'})


if __name__ == '__main__':
    app.run(debug=True)
