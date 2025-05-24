import yfinance as yf
import pandas as pd

def obter_multiplicadores(ticker):
    acao = yf.Ticker(ticker)
    info = acao.info

    multiplos = {
        "P/L (Preço/Lucro)": info.get("trailingPE"),
        "P/VPA (Preço/Valor Patrimonial)": info.get("priceToBook"),
        "EV/EBITDA": info.get("enterpriseToEbitda"),
        "P/FCF (Preço/Fluxo de Caixa Livre)": info.get("priceToFreeCashFlows"),
        "PEG Ratio": info.get("pegRatio"),
        "Setor": info.get("sector"),
        "Indústria": info.get("industry")
    }

    return pd.DataFrame(multiplos.items(), columns=["Múltiplo", "Valor"])

def interpretar_multiplicadores(df_multiplos):
    if df_multiplos.empty:
        return "❗️ Não foi possível obter os múltiplos para esta ação."

    try:
        pl = df_multiplos[df_multiplos["Múltiplo"] == "P/L (Preço/Lucro)"]["Valor"].values[0]
        if pl is None:
            return "ℹ️ Múltiplos indisponíveis para análise detalhada."
        if pl < 10:
            return "🔎 A ação parece subvalorizada com base no P/L."
        elif 10 <= pl <= 20:
            return "📈 A ação parece estar dentro de um intervalo justo de valuation (P/L entre 10 e 20)."
        else:
            return "⚠️ A ação pode estar supervalorizada com base no P/L alto."
    except Exception:
        return "⚠️ Erro ao interpretar múltiplos."
