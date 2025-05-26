import requests
import pandas as pd

API_KEY_BRAPI = "sC6eE4drp7whvmu6qeg1vM"  # Substitua pela sua chave da API da Brapi.dev


def coletar_dados_brapi(ticker):
    url = f"https://brapi.dev/api/quote/{ticker}?token={API_KEY_BRAPI}"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Erro ao acessar a API Brapi: {response.status_code} - {response.text}")

    data = response.json()
    if not data or 'results' not in data or not data['results']:
        raise ValueError(f"Dados não encontrados para o ticker {ticker} na Brapi.")

    return data['results'][0]


def estimar_fcf_adaptativo(dados):
    try:
        market_cap = dados.get("marketCap") or 0
        pe_ratio = dados.get("priceToEarnings") or 0
        book_value = dados.get("bookValue") or 0
        roe = dados.get("roe") or 0

        if market_cap > 0 and pe_ratio > 0:
            fcf = market_cap / pe_ratio
            base = "P/L inverso × MarketCap"
        elif roe > 0 and book_value > 0:
            fcf = roe * book_value
            base = "ROE × Patrimônio"
        elif market_cap > 0:
            fcf = market_cap * 0.05
            base = "Estimativa genérica (5% do MarketCap)"
        else:
            raise ValueError(
                f"Não foi possível estimar o FCF com os dados disponíveis.\nCampos recebidos: marketCap={market_cap}, P/L={pe_ratio}, ROE={roe}, bookValue={book_value}"
            )

        return fcf, base
    except Exception as e:
        raise ValueError(f"Erro na estimativa de FCF: {e}")


def calcular_vpl_dcf(ticker, wacc, crescimento_perpetuo, anos_projecao=5):
    try:
        ticker = ticker.upper()
        dados = coletar_dados_brapi(ticker)
        fcf_base, metodo = estimar_fcf_adaptativo(dados)

        taxa_crescimento = crescimento_perpetuo
        anos_proj = range(1, anos_projecao + 1)
        fluxo_proj = [fcf_base * ((1 + taxa_crescimento) ** ano) for ano in anos_proj]

        df_fluxo = pd.DataFrame({
            'Ano': anos_proj,
            'FCF Projetado (R$)': fluxo_proj
        })

        df_fluxo['Valor Presente Fluxo'] = df_fluxo['FCF Projetado (R$)'] / ((1 + wacc) ** df_fluxo['Ano'])

        valor_terminal = df_fluxo['FCF Projetado (R$)'].iloc[-1] * (1 + crescimento_perpetuo) / (wacc - crescimento_perpetuo)
        valor_presente_terminal = valor_terminal / ((1 + wacc) ** anos_projecao)

        vpl_total = df_fluxo['Valor Presente Fluxo'].sum() + valor_presente_terminal

        if 'marketCap' in dados and 'regularMarketPrice' in dados and dados['regularMarketPrice']:
            shares_outstanding = dados['marketCap'] / dados['regularMarketPrice']
        else:
            raise ValueError("Não foi possível estimar o número de ações em circulação.")

        valor_justo_por_acao = vpl_total / shares_outstanding

        df_fluxo['Valor Presente Fluxo'] = df_fluxo['Valor Presente Fluxo'].round(2)

        return {
            'valor_justo': round(valor_justo_por_acao, 2),
            'metodo_fcf': metodo,
            'fluxo': df_fluxo,
            'valor_terminal': round(valor_terminal, 2),
            'valor_presente_terminal': round(valor_presente_terminal, 2),
            'vpl_total': round(vpl_total, 2)
        }

    except Exception as e:
        raise ValueError(f"Erro ao calcular VPL DCF: {e}")
