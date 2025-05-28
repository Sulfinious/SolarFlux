import base64
import io
import pandas as pd
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State

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

if __name__ == "__main__":
    app.run_server(debug=True)
