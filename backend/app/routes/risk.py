import os
import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine
from fastapi import Query
import numpy as np
from backend.app.services.monte_carlo import run_monte_carlo
from backend.app.services.portfolio_optimization import (
    simulate_portfolios,
    get_optimized_portfolios,
)
from backend.app.services.risk_metrics import (
    calculate_daily_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_var,
    calculate_cvar,
    calculate_max_drawdown,
)
from backend.app.services.report_generator import generate_portfolio_report
from backend.app.services.llm_report import generate_ai_risk_report
from backend.app.services.chat_assistant import answer_portfolio_question

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

router = APIRouter(prefix="/risk", tags=["Risk"])
def get_asset_prices(symbol: str):
    query = """
        SELECT date, close
        FROM asset_prices
        WHERE symbol = %(symbol)s
        ORDER BY date;
    """
    return pd.read_sql(query, engine, params={"symbol": symbol.upper()})

def get_multiple_asset_prices(symbols):
    all_returns = []
    for symbol in symbols:
        query = """
            SELECT date, close
            FROM asset_prices
            WHERE symbol = %(symbol)s
            ORDER BY date;
        """
        df = pd.read_sql(query, engine, params={"symbol": symbol.upper()})
        if df.empty:
            continue

        returns = df["close"].pct_change()
        returns.name = symbol.upper()

        all_returns.append(returns)

    if not all_returns:
        return None

    returns_df = pd.concat(all_returns, axis=1)

    return returns_df.dropna()

@router.get("/portfolio")
def get_portfolio_risk(
    symbols: str = Query(...)
):
    symbol_list = [
        s.strip().upper()
        for s in symbols.split(",")
    ]

    returns_df = get_multiple_asset_prices(symbol_list)

    if returns_df is None:
        raise HTTPException(
            status_code=404,
            detail="No valid assets found"
        )

    # Equal weighting
    weights = np.ones(len(symbol_list)) / len(symbol_list)

    portfolio_returns = returns_df.dot(weights)

    cumulative_returns = (
        1 + portfolio_returns
    ).cumprod()

    return {
        "assets": symbol_list,
        "volatility": round(
            calculate_volatility(portfolio_returns),
            4
        ),
        "sharpe_ratio": round(
            calculate_sharpe_ratio(portfolio_returns),
            4
        ),
        "var_95": round(
            calculate_var(portfolio_returns),
            4
        ),
        "cvar_95": round(
            calculate_cvar(portfolio_returns),
            4
        ),
        "max_drawdown": round(
            calculate_max_drawdown(cumulative_returns),
            4
        )
    }

@router.get("/correlation")
def get_correlation_matrix(symbols: str = Query(...)):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    returns_df = get_multiple_asset_prices(symbol_list)

    if returns_df is None:
        raise HTTPException(status_code=404, detail="No valid assets found")

    correlation = returns_df.corr().round(4)

    return correlation.to_dict()

@router.get("/risk-report")
def get_generated_risk_report(
    symbols: str = Query(...),
    shocks: str = Query(...),
    initial_value: float = Query(100000),
    mode: str = Query("standard")
):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    returns_df = get_multiple_asset_prices(symbol_list)

    if returns_df is None:
        raise HTTPException(status_code=404, detail="No valid assets found")

    weights = np.ones(len(symbol_list)) / len(symbol_list)
    portfolio_returns = returns_df.dot(weights)
    cumulative_returns = (1 + portfolio_returns).cumprod()

    portfolio_risk = {
        "volatility": calculate_volatility(portfolio_returns),
        "sharpe_ratio": calculate_sharpe_ratio(portfolio_returns),
        "var_95": calculate_var(portfolio_returns),
        "cvar_95": calculate_cvar(portfolio_returns),
        "max_drawdown": calculate_max_drawdown(cumulative_returns),
    }

    shock_list = [float(s.strip()) for s in shocks.split(",")]

    if len(symbol_list) != len(shock_list):
        raise HTTPException(
            status_code=400,
            detail="Number of symbols must match number of shocks"
        )

    asset_impacts = {
        symbol_list[i]: float(weights[i] * shock_list[i])
        for i in range(len(symbol_list))
    }

    portfolio_loss = sum(asset_impacts.values())

    stress_result = {
        "portfolio_loss": portfolio_loss,
        "initial_value": initial_value,
        "estimated_loss_value": initial_value * abs(portfolio_loss),
        "stressed_portfolio_value": initial_value * (1 + portfolio_loss),
    }

    simulated_results = simulate_portfolios(
        returns_df,
        simulations=5000
    )

    optimization_result = {
        "optimized_portfolios": get_optimized_portfolios(simulated_results)
    }

    standard_report = generate_portfolio_report(
    portfolio_risk=portfolio_risk,
    stress_result=stress_result,
    optimization_result=optimization_result
)

    if mode == "ai":
        report = generate_ai_risk_report(standard_report)
    else:
        report = standard_report

    return {
        "assets": symbol_list,
        "report": report
    }

@router.get("/monte-carlo")
def monte_carlo_simulation(
    symbols: str = Query(...),
    initial_value: float = Query(100000),
    days: int = Query(252),
    simulations: int = Query(5000)
):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    returns_df = get_multiple_asset_prices(symbol_list)

    if returns_df is None:
        raise HTTPException(status_code=404, detail="No valid assets found")

    weights = np.ones(len(symbol_list)) / len(symbol_list)
    portfolio_returns = returns_df.dot(weights)

    return run_monte_carlo(
        portfolio_returns,
        initial_value=initial_value,
        days=days,
        simulations=simulations
    )

@router.get("/optimize")
def optimize_portfolio(
    symbols: str = Query(...),
    simulations: int = Query(10000)
):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    returns_df = get_multiple_asset_prices(symbol_list)

    if returns_df is None:
        raise HTTPException(status_code=404, detail="No valid assets found")

    simulated_results = simulate_portfolios(
        returns_df,
        simulations=simulations
    )

    optimized = get_optimized_portfolios(simulated_results)

    return {
        "assets": symbol_list,
        "simulations": simulations,
        "optimized_portfolios": optimized,
        "efficient_frontier_sample": simulated_results[:500],
    }

@router.get("/stress-test")
def stress_test_portfolio(
    symbols: str = Query(...),
    shock: float = Query(-0.20),
    initial_value: float = Query(100000)
):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    returns_df = get_multiple_asset_prices(symbol_list)

    if returns_df is None:
        raise HTTPException(status_code=404, detail="No valid assets found")

    weights = np.ones(len(symbol_list)) / len(symbol_list)

    shock_impact = shock * weights

    return {
        "assets": symbol_list,
        "shock": shock,
        "portfolio_loss": round(shock, 4),
        "asset_impacts": {
            symbol_list[i]: round(float(shock_impact[i]), 4)
            for i in range(len(symbol_list))
        },
        "initial_value": initial_value,
        "estimated_loss_value": round(initial_value * abs(shock), 2),
        "stressed_portfolio_value": round(initial_value * (1 + shock), 2),
    }

@router.get("/scenario-stress-test")
def scenario_stress_test(
    symbols: str = Query(...),
    shocks: str = Query(...),
    initial_value: float = Query(100000)
):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    shock_list = [float(s.strip()) for s in shocks.split(",")]

    if len(symbol_list) != len(shock_list):
        raise HTTPException(
            status_code=400,
            detail="Number of symbols must match number of shocks"
        )

    returns_df = get_multiple_asset_prices(symbol_list)

    if returns_df is None:
        raise HTTPException(status_code=404, detail="No valid assets found")

    weights = np.ones(len(symbol_list)) / len(symbol_list)

    asset_impacts = {
        symbol_list[i]: round(float(weights[i] * shock_list[i]), 4)
        for i in range(len(symbol_list))
    }

    portfolio_loss = sum(asset_impacts.values())

    return {
        "assets": symbol_list,
        "shocks": {
            symbol_list[i]: shock_list[i]
            for i in range(len(symbol_list))
        },
        "portfolio_loss": round(portfolio_loss, 4),
        "initial_value": initial_value,
        "estimated_loss_value": round(initial_value * abs(portfolio_loss), 2),
        "stressed_portfolio_value": round(initial_value * (1 + portfolio_loss), 2),
        "asset_impacts": asset_impacts
    }

@router.get("/ask")
def ask_risklens(
    symbols: str=Query(...),
    question: str=Query(...),
    initial_value: float=Query(100000)
):
    symbol_list = [s.strip() for s in symbols.upper().split(",")]

    returns_df = get_multiple_asset_prices(symbol_list)
    if returns_df is None:
        raise HTTPException(status_code=404, detail="No assets found")
    weights = np.ones(len(symbol_list)) / len(symbol_list)
    portfolio_returns = returns_df.dot(weights)
    cumulative_returns = (1 + portfolio_returns).cumprod()

    portfolio_context = {
        "assets": symbol_list,
        "initial_value": initial_value,
        "portfolio_risk": {
            "volatility": round(calculate_volatility(portfolio_returns), 4),
            "sharpe_ratio": round(calculate_sharpe_ratio(portfolio_returns), 4),
            "var_95": round(calculate_var(portfolio_returns), 4),
            "cvar_95": round(calculate_cvar(portfolio_returns), 4),
            "max_drawdown": round(calculate_max_drawdown(cumulative_returns), 4),
        },
        "correlation_matrix": returns_df.corr().round(4).to_dict(),
    }

    answer = answer_portfolio_question(
        question=question,
        context=portfolio_context
    )
    return {
        "question": question,
        "answer": answer}

@router.get("/{symbol}")
def get_risk_report(symbol:str):
    df = get_asset_prices(symbol)
    if df.empty:
        raise HTTPException(status_code=404, detail= "Asset not found")
    prices = df["close"]
    returns = calculate_daily_returns(prices)
    return {
        "asset": symbol.upper(),
        "volatility": round(calculate_volatility(returns), 4),
        "sharpe_ratio": round(calculate_sharpe_ratio(returns), 4),
        "var_95": round(calculate_var(returns), 4),
        "cvar_95": round(calculate_cvar(returns), 4),
        "max_drawdown": round(calculate_max_drawdown(prices), 4),
    }


    