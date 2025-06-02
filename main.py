import logging
import math
import requests
from bs4 import BeautifulSoup
from src.wacc import calcular_wacc

def estimar_fcf_real(ticker):
    try:
        logging.info(f"Coletando FCF real histórico de {ticker} via StatusInvest")
        url = f"https://statusinvest.com.br/acoes/{ticker.lower()}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        script_tags = soup.find_all('script')
        fcf_data = []
        for script in script_tags:
            if 'freeCashFlow' in script.text:
                start = script.text.find('freeCashFlow')
                trecho = script.text[start:start + 1000]
                valores = [int(v.replace('.', '').replace('"', '').replace('R$', '').strip())
                           for v in trecho.split('value":')[1:6]]
                fcf_data = valores
                break

        if fcf_data:
            media_fcf = sum(fcf_data) / len(fcf_data)
            logging.info(f"FCF médio estimado: {media_fcf}")
            return media_fcf, "Média dos últimos 5 anos via StatusInvest"
        else:
            raise ValueError("Não foi possível extrair o FCF do site.")
    except Exception as e:
        logging.warning(f"Erro ao coletar FCF: {e}")
        return None, "Estimativa genérica baseada em MarketCap (5%)"

def calcular_valuation_dcf(ticker, rf, rm, crescimento_inicial, anos_crescimento, crescimento_terminal):
    try:
        wacc = calcular_wacc(ticker, rf, rm)
        logging.info(f"WACC para {ticker}: {wacc}")
    except Exception as e:
        logging.error("Erro ao calcular o WACC", exc_info=True)
        return {"erro": f"Erro ao calcular WACC: {e}"}

    try:
        logging.info(f"Coletando dados para o ticker: {ticker}")
        url = f"https://brapi.dev/api/quote/{ticker}?range=1d&fundamental=true"
        response = requests.get(url)
        data = response.json()["results"][0]

        market_cap = data.get("marketCap", 0)
        numero_acoes = data.get("numberOfShares", 1)
        logging.info(f"MarketCap: {market_cap} | Número de ações: {numero_acoes}")

        fcf, metodo_fcf = estimar_fcf_real(ticker)
        if not fcf:
            fcf = market_cap * 0.05  # fallback
        logging.info(f"FCF estimado: {fcf} — Método: {metodo_fcf}")

        fluxo = []
        vpl_fluxo = 0

        for ano in range(1, anos_crescimento + 1):
            fcf_ano = fcf * ((1 + crescimento_inicial) ** ano)
            valor_presente = fcf_ano / ((1 + wacc) ** ano)
            fluxo.append({
                "Ano": ano,
                "FCF Projetado (R$)": fcf_ano,
                "Valor Presente Fluxo": valor_presente
            })
            vpl_fluxo += valor_presente

        fcf_terminal = fcf * ((1 + crescimento_inicial) ** anos_crescimento)
        valor_terminal = (fcf_terminal * (1 + crescimento_terminal)) / (wacc - crescimento_terminal)
        valor_presente_terminal = valor_terminal / ((1 + wacc) ** anos_crescimento)

        vpl_total = vpl_fluxo + valor_presente_terminal
        valor_justo = vpl_total / numero_acoes if numero_acoes else 0

        logging.info(f"Valuation finalizado — Valor justo por ação: {valor_justo}")

        return {
            "valor_justo": round(valor_justo, 2),
            "valor_terminal": round(valor_terminal, 2),
            "valor_presente_terminal": round(valor_presente_terminal, 2),
            "vpl_total": round(vpl_total, 2),
            "fluxo": fluxo,
            "metodo_fcf": metodo_fcf
        }

    except Exception as e:
        logging.error("Erro ao calcular Valuation DCF", exc_info=True)
        return {"erro": str(e)}
