import requests
import pandas as pd

API_KEY = rrHkxpTybc90PICXVIt474aeofUicVl9  # Substitua pela sua chave da API do FinancialModelingPrep


def coletar_fluxo_caixa_livre(ticker, anos=5):
    try:
        url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker.upper()}?limit={anos}&apikey={API_KEY}"
        response = requests.get(url)

        if response.status_code != 200:
            raise ValueError(f"Erro ao acessar API FMP: {response.status_code} - {response.text}")

        data = response.json()

        if not data:
            raise ValueError(f"Nenhum dado de fluxo de caixa retornado para o ticker {ticker}.")

        fcf_list = [item['freeCashFlow'] for item in data if 'freeCashFlow' in item and item['freeCashFlow'] is not None]

        if len(fcf_list) < anos:
            raise ValueError("Dados insuficientes de FCF para projeção.")

        fluxo_base = fcf_list[0]  # último ano mais recente
        taxa_crescimento = 0.05
        anos_proj = range(1, anos + 1)
        fluxo_proj = [fluxo_base * ((1 + taxa_crescimento) ** ano) for ano in anos_proj]

        df_fluxo = pd.DataFrame({
            'Ano': anos_proj,
            'FCF Projetado (US$)': fluxo_proj
        })

        return df_fluxo

    except Exception as e:
        raise ValueError(f"Erro ao coletar fluxo de caixa livre: {e}")


def calcular_vpl_dcf(ticker, wacc, crescimento_perpetuo, anos_projecao=5):
    try:
        df_fluxo = coletar_fluxo_caixa_livre(ticker, anos_projecao)

        df_fluxo['Valor Presente Fluxo'] = df_fluxo['FCF Projetado (US$)'] / ((1 + wacc) ** df_fluxo['Ano'])

        valor_terminal = df_fluxo['FCF Projetado (US$)'].iloc[-1] * (1 + crescimento_perpetuo) / (wacc - crescimento_perpetuo)
        valor_presente_terminal = valor_terminal / ((1 + wacc) ** anos_projecao)

        vpl_total = df_fluxo['Valor Presente Fluxo'].sum() + valor_presente_terminal

        # Buscar número de ações usando FMP
        info_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker.upper()}?apikey={API_KEY}"
        profile_resp = requests.get(info_url)
        if profile_resp.status_code != 200:
            raise ValueError("Erro ao buscar dados da empresa no FMP.")

        info = profile_resp.json()
        if not info or 'mktCap' not in info[0] or 'price' not in info[0]:
            raise ValueError("Informações incompletas no perfil da empresa.")

        shares_outstanding = info[0]['mktCap'] / info[0]['price']

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
