from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from src.dcf import calcular_valuation_dcf
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.get("/")
def read_root():
    return {"mensagem": "API de Valuation Ativa!"}


@app.get("/valuation")
def valuation(
    ticker: str = Query(..., description="Código do ativo. Ex: PETR4"),
    rf: float = Query(0.04, description="Taxa livre de risco (ex: 0.04 para 4%)"),
    rm: float = Query(0.10, description="Retorno esperado do mercado (ex: 0.10 para 10%)"),
    crescimento_inicial: float = Query(0.10, description="Taxa de crescimento inicial do FCF"),
    anos_crescimento: int = Query(5, description="Anos de crescimento inicial"),
    crescimento_terminal: float = Query(0.02, description="Taxa de crescimento perpetuo")
):
    try:
        resultado = calcular_valuation_dcf(
            ticker=ticker,
            rf=rf,
            rm=rm,
            crescimento_inicial=crescimento_inicial,
            anos_crescimento=anos_crescimento,
            crescimento_terminal=crescimento_terminal
        )
        return resultado
    except Exception as e:
        logging.exception("Erro na rota /valuation")
        return {"erro": str(e)}
