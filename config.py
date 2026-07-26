import os

# A planilha deve ficar na mesma pasta deste projeto (funciona em qualquer
# computador sem precisar editar o caminho abaixo).
EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Placas.xlsx")

PLACA_COL = 1
HEADER_ROW = 2
DATA_START_ROW = 3

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 20
DELAY_BETWEEN_REQUESTS = (10, 20)  # segundos, intervalo aleatorio

SITES = [
    {"name": "TabelaFipeBrasil", "base_url": "https://www.tabelafipebrasil.com", "modelo_col": 2, "valor_col": 3},
    {"name": "FipePelaPlaca", "base_url": "https://fipepelaplaca.com.br", "modelo_col": 4, "valor_col": 5},
    {"name": "KePlaca", "base_url": "https://www.keplaca.com", "modelo_col": 6, "valor_col": 7},
]

NAO_ENCONTRADO = "não encontrado"
