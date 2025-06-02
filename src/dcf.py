from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from src.dcf import calcular_valuation_dcf
from src.wacc import calcular_wacc
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

@app.get("/")
def read_root():
    return {"mensagem": "API de Valuation Ativa!"}


@app.get("/valuation")
def valuation(
    ticker: str = Query(..., description="Código do ativo. Ex: PETR4"),
    rf: float = Query(0.04, description="Taxa livre de risco (ex: 0.04 para 4%)"),
    rm: float = Query(0.10, description="Retorno esperado do mercado (ex: 0.10 para 10%)"),
    crescimento: float = Query(None, description="Taxa de crescimento perpétuo (formato antigo, usado se os parâmetros modernos não forem fornecidos)"),
    anos: int = Query(None, description="Anos de projeção (formato antigo, usado se os parâmetros modernos não forem fornecidos)"),
    crescimento_inicial: float = Query(
        None,
        description="Taxa de crescimento no primeiro estágio (ex: 0.10 para 10% ao ano). Recomenda-se usar a média dos últimos 5 anos de crescimento do lucro ou receita."
    ),
    anos_crescimento: int = Query(
        None,
        description="Número de anos em que o crescimento inicial será mantido. Normalmente entre 3 e 10 anos para empresas maduras."
    ),
    crescimento_terminal: float = Query(
        None,
        description="Crescimento perpétuo após o primeiro estágio. Deve refletir o crescimento esperado da economia de longo prazo (ex: 2 a 3%)."
    )
):
    try:
        wacc = calcular_wacc(ticker, rf, rm)

        if crescimento_inicial is not None and anos_crescimento is not None and crescimento_terminal is not None:
            resultado = calcular_valuation_dcf(
                ticker=ticker,
                wacc=wacc,
                crescimento_inicial=crescimento_inicial,
                anos_crescimento=anos_crescimento,
                crescimento_terminal=crescimento_terminal
            )
        elif crescimento is not None and anos is not None:
            resultado = calcular_valuation_dcf(
                ticker=ticker,
                wacc=wacc,
                crescimento_inicial=crescimento,
                anos_crescimento=anos,
                crescimento_terminal=crescimento
            )
        else:
            raise ValueError("Parâmetros insuficientes: forneça o conjunto de múltiplos estágios ou o antigo crescimento + anos.")

        return resultado

    except Exception as e:
        logging.exception("Erro na rota /valuation")
        return {"erro": str(e)}
