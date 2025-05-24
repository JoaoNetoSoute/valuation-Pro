import yfinance as yf
import pandas as pd
import numpy as np

def coletar_fluxo_caixa_livre(ticker, anos=5):
    """
    Coleta dados financeiros da empresa para construir o fluxo de caixa livre projetado.
    Usa yfinance para extrair dados históricos.
    
    Parâmetros:
    - ticker: código da ação (ex: 'AAPL')
    - anos: número de anos para projetar o fluxo
    
    Retorna:
    - DataFrame com fluxo de caixa livre projetado por ano
    """
    try:
        empresa = yf.Ticker(ticker)
        # Extrai demonstração de fluxo de caixa (cashflow) trimestral
        cf = empresa.cashflow
        
        # Para simplificar, somamos os últimos 4 trimestres para estimar o fluxo anual
        fluxo_caixa_livre_ultimos_4t = cf.loc['Free Cash Flow'].rolling(window=4, axis=1).sum().iloc[:, -1]
        
        # Usamos o último valor anual como base para projetar crescimento
        fluxo_base = fluxo_caixa_livre_ultimos_4t.values[0]
        
        # Suponha crescimento constante de fluxo - pode ser parametrizado depois
        taxa_crescimento = 0.05  # 5% anual - default, pode ajustar
        
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
    """
    Calcula o valor presente líquido (VPL) pelo método do fluxo de caixa descontado (DCF).
    
    Parâmetros:
    - ticker: código da ação
    - wacc: custo médio ponderado de capital (decimal, ex: 0.1 para 10%)
    - crescimento_perpetuo: taxa de crescimento perpétuo após projeção (decimal)
    - anos_projecao: número de anos para projetar fluxo
    
    Retorna:
    - dict com:
        - 'valor_justo': valor justo por ação estimado
        - 'fluxo': DataFrame com fluxo de caixa projetado e VPL anual
    """
    try:
        df_fluxo = coletar_fluxo_caixa_livre(ticker, anos_projecao)
        
        # Desconta os fluxos projetados
        df_fluxo['Valor Presente Fluxo'] = df_fluxo['Fluxo de Caixa Livre Projetado'] / ((1 + wacc) ** df_fluxo['Ano'])
        
        # Calcula valor terminal usando fórmula de Gordon Growth Model
        valor_terminal = df_fluxo['Fluxo de Caixa Livre Projetado'].iloc[-1] * (1 + crescimento_perpetuo) / (wacc - crescimento_perpetuo)
        valor_presente_terminal = valor_terminal / ((1 + wacc) ** anos_projecao)
        
        # VPL total é soma dos valores presentes + valor presente terminal
        vpl_total = df_fluxo['Valor Presente Fluxo'].sum() + valor_presente_terminal
        
        # Obter número de ações em circulação para calcular valor justo por ação
        empresa = yf.Ticker(ticker)
        info = empresa.info
        shares_outstanding = info.get('sharesOutstanding')
        if not shares_outstanding or shares_outstanding == 0:
            raise ValueError("Número de ações em circulação não disponível ou inválido.")
        
        valor_justo_por_acao = vpl_total / shares_outstanding
        
        # Adiciona valores ao DataFrame para exibição detalhada
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
