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


def calcular_vpl_dcf(ticker, wacc, crescimento_perpetuo, anos_projecao=5):
    try:
        df_fluxo = coletar_fluxo_caixa_livre(ticker, anos_projecao)

        df_fluxo['Valor Presente Fluxo'] = df_fluxo['Fluxo de Caixa Livre Projetado'] / ((1 + wacc) ** df_fluxo['Ano'])

        valor_terminal = df_fluxo['Fluxo de Caixa Livre Projetado'].iloc[-1] * (1 + crescimento_perpetuo) / (wacc - crescimento_perpetuo)
        valor_presente_terminal = valor_terminal / ((1 + wacc) ** anos_projecao)

        vpl_total = df_fluxo['Valor Presente Fluxo'].sum() + valor_presente_terminal

        empresa = yf.Ticker(ticker)
        info = empresa.info
        shares_outstanding = info.get('sharesOutstanding')
        if not shares_outstanding or shares_outstanding == 0:
            raise ValueError("Número de ações em circulação não disponível ou inválido.")

        valor_justo_por_acao = vpl_total / shares_outstanding

        df_fluxo['Valor Presente Fluxo'] = df_fluxo['Valor Presente Fluxo'].round(2)
        df_fluxo = df_fluxo.rename(columns={'Fluxo de Caixa Livre Projetado': 'FCF Projetado (US$)'})

        return {
            'valor_justo': valor_justo_por_acao,
            'fluxo': df_fluxo,
            'valor_terminal': valor_terminal,
            'valor_presente_terminal': valor_presente_terminal,
            'vpl_total': vpl_total
        }

    except Exception as e:
        raise ValueError(f"Erro ao calcular VPL DCF: {e}")
