import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RiskLens AI",
    layout="wide"
)

st.title("RiskLens AI")
st.write("Financial risk intelligence dashboard")

@st.cache_data
def get_assets():
    response = requests.get(f"{API_BASE_URL}/assets/")
    response.raise_for_status()
    return response.json()

assets_data = get_assets()
assets_df = pd.DataFrame(assets_data)
asset_symbols = assets_df["symbol"].tolist()

def create_pdf_report(report_text, selected_assets, initial_value, risk_score, risk_label, report_mode):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RiskLens AI Executive Risk Report", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "", 11)

    summary = f"""
Assets: {", ".join(selected_assets)}
Initial Portfolio Value: EUR {initial_value:,.2f}
Risk Score: {risk_score}/100
Risk Level: {risk_label}
Report Mode: {report_mode}
"""

    pdf.multi_cell(0, 8, summary)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Executive Summary", ln=True)

    pdf.set_font("Arial", "", 11)

    clean_report = (
        report_text
        .replace("€", "EUR ")
        .replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    pdf.multi_cell(0, 8, clean_report)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)

    with open(temp_file.name, "rb") as file:
        return file.read()
    

st.sidebar.header("Portfolio Selection")
selected_assets = st.sidebar.multiselect(
    "Choose assets",
    asset_symbols,
    default=asset_symbols
)

if not selected_assets:
    st.warning("Select at least one asset.")
    st.stop()

symbols_query = ",".join(selected_assets)

portfolio_response = requests.get(
    f"{API_BASE_URL}/risk/portfolio",
    params={"symbols": symbols_query}
)
portfolio_response.raise_for_status()
portfolio = portfolio_response.json()
def calculate_risk_score(portfolio):
    volatility = portfolio["volatility"]
    sharpe = portfolio["sharpe_ratio"]
    drawdown = abs(portfolio["max_drawdown"])

    score = 100

    score -= volatility * 80
    score -= drawdown * 50

    if sharpe < 0.5:
        score -= 20
    elif sharpe < 1:
        score -= 10

    return max(0, min(100, round(score)))


risk_score = calculate_risk_score(portfolio)

if risk_score >= 75:
    risk_label = "Strong"
elif risk_score >= 50:
    risk_label = "Moderate"
else:
    risk_label = "High Risk"
correlation_response = requests.get(
    f"{API_BASE_URL}/risk/correlation",
    params={"symbols": symbols_query}
)
correlation_response.raise_for_status()
correlation = correlation_response.json()
correlation_df = pd.DataFrame(correlation)

st.sidebar.header("Portfolio Settings")

initial_value = st.sidebar.number_input(
    "Initial Portfolio Value (€)",
    min_value=1000,
    value=100000,
    step=1000
)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📈 Optimization",
    "⚠️ Risk Simulation",
    "🤖 AI Insights"
])
with tab1:
    st.subheader("Portfolio Risk Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Volatility", f"{portfolio['volatility']:.2%}")
    col2.metric("Sharpe Ratio", portfolio["sharpe_ratio"])
    col3.metric("VaR 95%", f"{portfolio['var_95']:.2%}")
    col4.metric("CVaR 95%", f"{portfolio['cvar_95']:.2%}")
    col5.metric("Max Drawdown", f"{portfolio['max_drawdown']:.2%}")

    st.subheader("Portfolio Health")

    col1, col2 = st.columns(2)

    col1.metric("Risk Score", f"{risk_score}/100")
    col2.metric("Risk Level", risk_label)

    st.subheader("Individual Asset Risk")

    asset_reports = []

    for symbol in selected_assets:
        response = requests.get(f"{API_BASE_URL}/risk/{symbol}")
        response.raise_for_status()
        asset_reports.append(response.json())

    asset_risk_df = pd.DataFrame(asset_reports)
    st.dataframe(asset_risk_df, use_container_width=True)

    with st.expander("Dataset Information"):
        st.subheader("Available Asset Data")
        st.dataframe(assets_df, use_container_width=True)
with tab2:
    st.subheader("Portfolio Optimization")

    optimization_response = requests.get(
        f"{API_BASE_URL}/risk/optimize",
        params={
            "symbols": symbols_query,
            "simulations": 5000
        }
    )
    optimization_response.raise_for_status()
    optimization = optimization_response.json()

    max_sharpe = optimization["optimized_portfolios"]["max_sharpe_portfolio"]
    min_vol = optimization["optimized_portfolios"]["minimum_volatility_portfolio"]

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Max Sharpe Portfolio")
        st.metric("Return", f"{max_sharpe['return']:.2%}")
        st.metric("Volatility", f"{max_sharpe['volatility']:.2%}")
        st.metric("Sharpe Ratio", max_sharpe["sharpe_ratio"])
        st.dataframe(pd.DataFrame([max_sharpe["weights"]]))

    with col2:
        st.write("### Minimum Volatility Portfolio")
        st.metric("Return", f"{min_vol['return']:.2%}")
        st.metric("Volatility", f"{min_vol['volatility']:.2%}")
        st.metric("Sharpe Ratio", min_vol["sharpe_ratio"])
        st.dataframe(pd.DataFrame([min_vol["weights"]]))

    frontier_df = pd.DataFrame(optimization["efficient_frontier_sample"])

    with st.expander("Efficient Frontier Plot", expanded=True):
        fig, ax = plt.subplots(figsize=(8, 4))

        ax.scatter(
            frontier_df["volatility"],
            frontier_df["return"],
            s=8,
            alpha=0.35
        )

        ax.scatter(
            max_sharpe["volatility"],
            max_sharpe["return"],
            s=180,
            marker="*",
            color="green",
            edgecolor="black",
            label="Max Sharpe Portfolio"
        )

        ax.scatter(
            min_vol["volatility"],
            min_vol["return"],
            s=140,
            marker="X",
            color="red",
            edgecolor="black",
            label="Minimum Volatility Portfolio"
        )

        ax.set_title("Efficient Frontier")
        ax.set_xlabel("Volatility / Risk")
        ax.set_ylabel("Expected Return")
        ax.grid(alpha=0.3)
        ax.legend()

        st.pyplot(fig)

    st.write("### Portfolio Allocation")

    bar_col1, bar_col2 = st.columns(2)

    with bar_col1:

        weights_df = pd.DataFrame(
            max_sharpe["weights"].items(),
            columns=["Asset", "Weight"]
        )

        weights_df = weights_df.sort_values(
            by="Weight",
            ascending=True
        )

        fig, ax = plt.subplots(figsize=(5, 3))

        bars = ax.barh(
            weights_df["Asset"],
            weights_df["Weight"]
        )

        ax.set_title("Max Sharpe Allocation")
        ax.set_xlabel("Portfolio Weight")

        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.01,
                bar.get_y() + bar.get_height()/2,
                f"{width:.1%}",
                va="center"
            )

        ax.set_xlim(0, 1)

        st.pyplot(fig)

    with bar_col2:

        weights_df = pd.DataFrame(
            min_vol["weights"].items(),
            columns=["Asset", "Weight"]
        )

        weights_df = weights_df.sort_values(
            by="Weight",
            ascending=True
        )

        fig, ax = plt.subplots(figsize=(5, 3))

        bars = ax.barh(
            weights_df["Asset"],
            weights_df["Weight"]
        )

        ax.set_title("Minimum Volatility Allocation")
        ax.set_xlabel("Portfolio Weight")

        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.01,
                bar.get_y() + bar.get_height()/2,
                f"{width:.1%}",
                va="center"
            )

        ax.set_xlim(0, 1)

        st.pyplot(fig)

    st.subheader("Correlation Matrix")

    fig, ax = plt.subplots(figsize=(4, 4))

    heatmap = ax.imshow(
        correlation_df,
        cmap="RdYlGn",
        vmin=0,
        vmax=1
    )

    ax.set_xticks(range(len(correlation_df.columns)))
    ax.set_yticks(range(len(correlation_df.index)))

    ax.set_xticklabels(
        correlation_df.columns,
        rotation=45,
        ha="right"
    )

    ax.set_yticklabels(correlation_df.index)

    for i in range(len(correlation_df.index)):
        for j in range(len(correlation_df.columns)):
            ax.text(
                j,
                i,
                f"{correlation_df.iloc[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=8
            )

    cbar = plt.colorbar(
        heatmap,
        fraction=0.04,
        pad=0.04
    )

    cbar.set_label("Correlation")

    plt.tight_layout()

    with st.expander("View Correlation Matrix"):
        st.pyplot(fig)


with tab3:
    st.subheader("Scenario Stress Testing")

    st.write("Set individual shock values for each selected asset:")

    shock_values = []
    with st.expander("Configure Stress Scenario"):
    
        for asset in selected_assets:
            shock_percent = st.slider(
                f"{asset} Shock (%)",
                min_value=-60,
                max_value=20,
                value=-20,
                step=1
            )
            shock_values.append(shock_percent / 100)

    shocks_query = ",".join([str(s) for s in shock_values])

    scenario_response = requests.get(
        f"{API_BASE_URL}/risk/scenario-stress-test",
        params={
            "symbols": symbols_query,
            "shocks": shocks_query,
            "initial_value": initial_value
        }
    )

    scenario_response.raise_for_status()
    scenario = scenario_response.json()

    col1, col2, col3 = st.columns(3)

    col1.metric("Estimated Loss", f"€{scenario['estimated_loss_value']:,.2f}")
    col2.metric("Stressed Portfolio Value", f"€{scenario['stressed_portfolio_value']:,.2f}")
    col3.metric("Portfolio Loss", f"{scenario['portfolio_loss']:.2%}")

    scenario_df = pd.DataFrame({
        "Asset": list(scenario["shocks"].keys()),
        "Shock": [f"{v:.2%}" for v in scenario["shocks"].values()],
        "Portfolio Impact": [f"{v:.2%}" for v in scenario["asset_impacts"].values()]
    })

    st.dataframe(scenario_df, use_container_width=True)

    st.subheader("Monte Carlo Simulation")

    mc_response = requests.get(
        f"{API_BASE_URL}/risk/monte-carlo",
        params={
            "symbols": symbols_query,
            "initial_value": initial_value,
            "days": 252,
            "simulations": 5000
        }
    )

    mc_response.raise_for_status()
    mc = mc_response.json()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Expected Value", f"€{mc['expected_final_value']:,.2f}")
    col2.metric("Median Value", f"€{mc['median_final_value']:,.2f}")
    col3.metric("Worst 5%", f"€{mc['worst_5_percent_value']:,.2f}")
    col4.metric("Probability of Loss", f"{mc['probability_of_loss']:.2%}")

    mc_values = pd.Series(mc["final_values_sample"])

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.hist(
        mc_values,
        bins=40,
        edgecolor="black",   # borders around bins
        linewidth=0.5,
        alpha=0.75
    )

    ax.axvline(
        mc["expected_final_value"],
        color="green",
        linestyle="--",
        linewidth=2,
        label=f"Expected (€{mc['expected_final_value']:,.0f})"
    )

    ax.axvline(
        mc["median_final_value"],
        color="blue",
        linestyle="--",
        linewidth=2,
        label=f"Median (€{mc['median_final_value']:,.0f})"
    )

    ax.axvline(
        mc["worst_5_percent_value"],
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"5th Percentile (€{mc['worst_5_percent_value']:,.0f})"
    )

    ax.set_title("Monte Carlo Portfolio Value Distribution")
    ax.set_xlabel("Portfolio Value (€)")
    ax.set_ylabel("Frequency")

    ax.grid(alpha=0.3)
    ax.legend()

    st.pyplot(fig)

with tab4:
    st.subheader("Executive Risk Report")

    report_mode = st.radio(
        "Report Mode",
        ["Standard Report", "AI Report"],
        horizontal=True
    )

    if st.button("Generate Report"):
        mode = "ai" if report_mode == "AI Report" else "standard"

        report_response = requests.get(
            f"{API_BASE_URL}/risk/risk-report",
            params={
                "symbols": symbols_query,
                "shocks": shocks_query,
                "initial_value": initial_value,
                "mode": mode
            }
        )

        report_response.raise_for_status()
        report_data = report_response.json()

        report_text = report_data["report"]

        st.write(report_text)
        pdf_bytes = create_pdf_report(
            report_text=report_text,
            selected_assets=selected_assets,
            initial_value=initial_value,
            risk_score=risk_score,
            risk_label=risk_label,
            report_mode=report_mode
        )

        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name="risklens_ai_report.pdf",
            mime="application/pdf"
        )
        download_content = f"""
    RiskLens AI Executive Risk Report

    Assets: {", ".join(selected_assets)}
    Initial Portfolio Value: €{initial_value:,.2f}
    Risk Score: {risk_score}/100
    Risk Level: {risk_label}
    Report Mode: {report_mode}

    {report_text}
    """

    st.subheader("RiskLens Copilot")

    user_question = st.text_input(
        "Ask a question about this portfolio",
        placeholder="Example: Why is my portfolio risky?"
    )

    if st.button("Ask RiskLens"):
        if user_question.strip() == "":
            st.warning("Please enter a question.")
        else:
            chat_response = requests.get(
                f"{API_BASE_URL}/risk/ask",
                params={
                    "symbols": symbols_query,
                    "question": user_question,
                    "initial_value": initial_value
                }
            )

            chat_response.raise_for_status()
            chat_data = chat_response.json()

            st.write(chat_data["answer"])



   