import requests
import yfinance as yf
import pandas as pd

API_KEY = "rrHkxpTybc90PICXVIt474aeofUicVl9"  # Substitua pela sua chave da API do FinancialModelingPrep


def normalizar_ticker(ticker):
    ticker = ticker.upper()
    if not ticker.endswith(".SA") and len(ticker) <= 6 and ticker[-1].isdigit():
        return ticker + ".SA"
    return ticker


def coletar_fluxo_caixa_livre_yahoo(ticker, anos=5):
    try:
        empresa = yf.Ticker(ticker)
        cf = empresa.cashflow

        if cf.empty or cf.shape[0] == 0:
            raise ValueError(f"O cashflow retornado está vazio para o ticker {ticker}.")

        if 'Free Cash Flow' in cf.index:
            fcf_series = cf.loc['Free Cash Flow']
        elif ('Total Cash From Operating Activities' in cf.index and 'Capital Expenditures' in cf.index):
            fcf_series = cf.loc['Total Cash From Operating Activities'] + cf.loc['Capital Expenditures']
        else:
            raise ValueError(f"Não foi possível estimar o fluxo de caixa livre para o ticker {ticker}.")

        fluxo_base = fcf_series.rolling(window=4, axis=1).sum().iloc[:, -1]

        taxa_crescimento = 0.05
        anos_proj = range(1, anos + 1)
        fluxo_proj = [fluxo_base * ((1 + taxa_crescimento) ** ano) for ano in anos_proj]

        df_fluxo = pd.DataFrame({
            'Ano': anos_proj,
            'FCF Projetado (US$)': fluxo_proj
        })

        return df_fluxo
    except Exception as e:
        raise ValueError(f"Erro ao coletar fluxo de caixa livre (Yahoo): {e}")


def coletar_fluxo_caixa_livre_fmp(ticker, anos=5):
    try:
        url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit={anos}&apikey={API_KEY}"
        response = requests.get(url)

        if response.status_code != 200:
            raise ValueError(f"Erro ao acessar API FMP: {response.status_code} - {response.text}")

        if not response.text:
            raise ValueError("A resposta da API está vazia. Possível limite atingido ou erro de conexão.")

        data = response.json()

        if not data:
            raise ValueError(f"Nenhum dado de fluxo de caixa retornado para o ticker {ticker}.")

        fcf_list = [item['freeCashFlow'] for item in data if 'freeCashFlow' in item and item['freeCashFlow'] is not None]

        if len(fcf_list) < anos:
            raise ValueError("Dados insuficientes de FCF para projeção.")

        fluxo_base = fcf_list[0]
        taxa_crescimento = 0.05
        anos_proj = range(1, anos + 1)
        fluxo_proj = [fluxo_base * ((1 + taxa_crescimento) ** ano) for ano in anos_proj]

        df_fluxo = pd.DataFrame({
            'Ano': anos_proj,
            'FCF Projetado (US$)': fluxo_proj
        })

        return df_fluxo
    except Exception as e:
        raise ValueError(f"Erro ao coletar fluxo de caixa livre (FMP): {e}")


def calcular_vpl_dcf(ticker, wacc, crescimento_perpetuo, anos_projecao=5):
    try:
        ticker = ticker.upper()
        is_brasileira = len(ticker) <= 6 and ticker[-1].isdigit()
        ticker_usado = normalizar_ticker(ticker) if is_brasileira else ticker

        if ticker_usado.endswith(".SA"):
            df_fluxo = coletar_fluxo_caixa_livre_yahoo(ticker_usado, anos_projecao)
            info = yf.Ticker(ticker_usado).info
            shares_outstanding = info.get('sharesOutstanding')
            if not shares_outstanding or shares_outstanding == 0:
                raise ValueError("Número de ações em circulação não disponível ou inválido.")
        else:
            df_fluxo = coletar_fluxo_caixa_livre_fmp(ticker_usado, anos_projecao)
            # Buscar número de ações usando FMP
            info_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker_usado}?apikey={API_KEY}"
            profile_resp = requests.get(info_url)
            if profile_resp.status_code != 200 or not profile_resp.text:
                raise ValueError("Erro ao buscar dados da empresa no FMP.")
            info_data = profile_resp.json()
            if not info_data or 'mktCap' not in info_data[0] or 'price' not in info_data[0]:
                raise ValueError("Informações incompletas no perfil da empresa.")
            shares_outstanding = info_data[0]['mktCap'] / info_data[0]['price']

        df_fluxo['Valor Presente Fluxo'] = df_fluxo['FCF Projetado (US$)'] / ((1 + wacc) ** df_fluxo['Ano'])

        valor_terminal = df_fluxo['FCF Projetado (US$)'].iloc[-1] * (1 + crescimento_perpetuo) / (wacc - crescimento_perpetuo)
        valor_presente_terminal = valor_terminal / ((1 + wacc) ** anos_projecao)

        vpl_total = df_fluxo['Valor Presente Fluxo'].sum() + valor_presente_terminal
        valor_justo_por_acao = vpl_total / shares_outstanding

        df_fluxo['Valor Presente Fluxo'] = df_fluxo['Valor Presente Fluxo'].round(2)

        return {
            'valor_justo': valor_justo_por_acao,
            'fluxo': df_fluxo,
            'valor_terminal': valor_terminal,
            'valor_presente_terminal': valor_presente_terminal,
            'vpl_total': vpl_total
        }

    except Exception as e:
        raise ValueError(f"Erro ao calcular VPL DCF: {e}")
