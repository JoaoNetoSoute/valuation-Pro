import yfinance as yf

def calcular_wacc(ticker: str, rf: float = 0.04, rm: float = 0.10) -> float:
    """
    Calcula o WACC (Custo Médio Ponderado de Capital) com base em dados do Yahoo Finance.
    
    Parâmetros:
    - ticker: código da ação (ex: AAPL)
    - rf: taxa livre de risco
    - rm: retorno esperado do mercado

    Retorna:
    - WACC arredondado (float)
    """
    try:
        empresa = yf.Ticker(ticker)
        info = empresa.info

        beta = info.get('beta')
        if beta is None:
            beta = 1.0  # fallback conservador

        # Custo do capital próprio via CAPM
        ke = rf + beta * (rm - rf)

        # Custo da dívida (estimado) e efeito do imposto
        kd = 0.08
        taxa_imposto = 0.34

        # Estrutura de capital
        valor_mercado_acao = info.get('marketCap') or 1e9
        valor_divida = info.get('totalDebt') or 1e8
        total = valor_mercado_acao + valor_divida

        if total == 0:
            return 0.10  # fallback caso dados ausentes

        peso_acao = valor_mercado_acao / total
        peso_divida = valor_divida / total

        wacc = peso_acao * ke + peso_divida * kd * (1 - taxa_imposto)
        return round(wacc, 4)

    except Exception as e:
        print(f"[Erro WACC] Não foi possível calcular para {ticker}: {e}")
        return 0.10


def calcular_custo_capital_proprio(beta: float, rf: float = 0.04, rm: float = 0.10) -> float:
    """
    Calcula o custo do capital próprio com o modelo CAPM.
    
    Fórmula: ke = rf + beta * (rm - rf)
    """
    return round(rf + beta * (rm - rf), 4)
