import yfinance as yf
import pandas as pd

def coletar_fluxo_caixa_livre(ticker, anos=5):
    try:
        empresa = yf.Ticker(ticker)
        cf = empresa.cashflow

        if cf.empty or cf.shape[0] == 0:
            raise ValueError(f"O cashflow retornado está vazio para o ticker {ticker}.")

        fcf_series = None

        if 'Free Cash Flow' in cf.index:
            fcf_series = cf.loc['Free Cash Flow']
        elif ('Total Cash From Operating Activities' in cf.index and 'Capital Expenditures' in cf.index):
            fcf_series = cf.loc['Total Cash From Operating Activities'] + cf.loc['Capital Expenditures']

        if fcf_series is None or fcf_series.empty:
            raise ValueError(f"Não foi possível estimar o fluxo de caixa livre para o ticker {ticker}.")

        fluxo_base = fcf_series.rolling(window=4, axis=1).sum().iloc[:, -1]

        taxa_crescimento = 0.05
        anos_proj = range(1, anos + 1)
        fluxo_proj = [fluxo_base * ((1 + taxa_crescimento) ** ano) for ano in anos_proj]

        df_fluxo = pd.DataFrame({
            'Ano': anos_proj,
            'Fluxo de Caixa Livre Projetado': fluxo_proj
        })

        return df_fluxo

    except Exception as e:
        raise ValueError(f"Erro ao coletar fluxo de caixa livre: {e}")
