# main.py

from fastapi import FastAPI, Query
from src.dcf import calcular_vpl_dcf
from src.wacc import calcular_wacc
from src.comparables import obter_multiplicadores
from src.valuation_summary import gerar_resumo_valuation
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Valuation Pro API", version="1.0")

# Permitir acesso do app móvel (React Native ou navegador)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API de Valuation Pro está ativa!"}

@app.get("/valuation")
def valuation_endpoint(
    ticker: str = Query(..., example="AAPL"),
    rf: float = Query(0.04, description="Taxa livre de risco"),
    rm: float = Query(0.10, description="Retorno do mercado"),
    crescimento: float = Query(0.02, description="Crescimento perpétuo"),
    anos: int = Query(5, description="Anos de projeção")
):
    wacc = calcular_wacc(ticker, rf, rm)
    dcf = calcular_vpl_dcf(ticker, wacc, crescimento, anos)
    multiplos = obter_multiplicadores(ticker)
    resumo = gerar_resumo_valuation(ticker, dcf['valor_justo'], multiplos)

    return {
        "ticker": ticker.upper(),
        "valor_justo": round(dcf['valor_justo'], 2),
        "wacc": round(wacc, 4),
        "resumo": resumo.to_dict(orient="records"),
        "fluxo": dcf["fluxo"].to_dict(orient="records"),
        "multiplos": multiplos.to_dict(orient="records")
    }
