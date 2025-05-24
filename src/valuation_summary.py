import pandas as pd
import yfinance as yf

def gerar_resumo_valuation(ticker, valor_justo_dcf, df_multiplos=None):
    """
    Gera um DataFrame resumo com valor justo por DCF, por múltiplos (se disponível) e preço atual.
    """
    preco_atual = yf.Ticker(ticker).info.get('currentPrice', None)

    data = {
        "Critério": ["DCF", "Múltiplos", "Preço Atual"],
        "Valor por Ação (USD)": [valor_justo_dcf, None, preco_atual]
    }

    if df_multiplos is not None and "Valor Justo (Multiplo)" in df_multiplos.columns:
        valor_justo_multiplo = df_multiplos["Valor Justo (Multiplo)"].mean()
        data["Valor por Ação (USD)"][1] = valor_justo_multiplo

    df_resumo = pd.DataFrame(data)
    return df_resumo

def gerar_comparativo_valores(ticker, valor_justo_dcf, valor_justo_multiplo=None):
    """
    Gera DataFrame com valores de comparação visual: DCF, múltiplos (se houver) e preço atual.
    """
    preco_atual = yf.Ticker(ticker).info.get('currentPrice', None)

    dados = {
        'Método': ['DCF'],
        'Valor Estimado': [valor_justo_dcf]
    }

    if valor_justo_multiplo is not None:
        dados['Método'].append('Múltiplos')
        dados['Valor Estimado'].append(valor_justo_multiplo)

    if preco_atual:
        dados['Método'].append('Preço Atual')
        dados['Valor Estimado'].append(preco_atual)

    df = pd.DataFrame(dados)
    return df
