import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def obter_beta_statusinvest(ticker):
    try:
        url = f"https://statusinvest.com.br/acoes/{ticker.lower()}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        span = soup.find("strong", string="Beta")
        if span:
            beta_valor = span.find_next("span").text.strip().replace(",", ".")
            beta = float(beta_valor)
            logging.info(f"Beta encontrado para {ticker.upper()}: {beta}")
            return beta

        logging.warning(f"Beta não encontrado para {ticker.upper()} na página do Status Invest.")
        return None

    except Exception as e:
        logging.exception(f"Erro ao buscar o beta para {ticker.upper()}")
        return None

def calcular_custo_capital_proprio(beta, rf=0.04, rm=0.10):
    try:
        ke = rf + beta * (rm - rf)
        return round(ke, 4)
    except Exception as e:
        logging.exception("Erro ao calcular o custo do capital próprio")
        return 0.1

def calcular_wacc(ticker, rf=0.04, rm=0.10):
    try:
        beta = obter_beta_statusinvest(ticker)
        if beta is None:
            raise ValueError("Beta não encontrado.")

        ke = calcular_custo_capital_proprio(beta, rf, rm)
        kd = 0.08  # estimativa conservadora
        taxa_imposto = 0.34  # imposto médio

        peso_acao = 0.7
        peso_divida = 0.3

        wacc = peso_acao * ke + peso_divida * kd * (1 - taxa_imposto)
        logging.info(f"WACC estimado para {ticker.upper()}: {round(wacc, 4)}")
        return round(wacc, 4)

    except Exception as e:
        logging.exception("Erro ao calcular o WACC")
        return 0.1
