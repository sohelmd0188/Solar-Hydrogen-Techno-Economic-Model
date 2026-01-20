# ============================================================
# Solar Hydrogen Techno-Economic Model
# Designed by Mohammad Sohel
# ============================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Solar Hydrogen Techno-Economic Model",
    layout="wide"
)

st.title("Solar Hydrogen Techno-Economic Model")

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

menu = st.sidebar.radio(
    "Navigation",
    [
        "Model Overview",
        "Economic Summary",
        "Sensitivity Analysis",
        "Monthly EMS & Cost–Profit",
        "Documentation / Important Documents"
    ]
)

# ============================================================
# KEY CONSTANTS & INPUTS
# ============================================================

st.sidebar.header("Key Constants & Presets")

project_lifetime = 20
annual_h2_production = 208_800  # kg/year

wacc_baseline = 0.08
wacc_concessional = 0.04

grid_emission_factor = 0.67  # kg CO2/kWh

grid_tariff = st.sidebar.number_input("Grid Import Tariff (USD/kWh)", value=0.12)
export_tariff = st.sidebar.number_input("Grid Export Price (USD/kWh)", value=0.08)

solar_capex = st.sidebar.number_input("Solar PV CAPEX (USD)", value=4_500_000.0)
electrolyzer_capex = st.sidebar.number_input("Electrolyzer CAPEX (USD)", value=6_000_000.0)
fuel_cell_capex = st.sidebar.number_input("Fuel Cell CAPEX (USD)", value=1_700_000.0)
storage_capex = st.sidebar.number_input("Hydrogen Storage CAPEX (USD)", value=900_000.0)

annual_om_cost = st.sidebar.number_input("Annual O&M Cost (USD/year)", value=60_000.0)
annual_revenue = st.sidebar.number_input("Annual Revenue (USD/year)", value=679_549.0)

total_capex = solar_capex + electrolyzer_capex + fuel_cell_capex + storage_capex
annual_cashflow = annual_revenue - annual_om_cost

# ============================================================
# CORE FINANCIAL FUNCTIONS
# ============================================================

def crf(rate, n):
    return rate * (1 + rate) ** n / ((1 + rate) ** n - 1)

def lcoh(capex, om, rev, h2, rate):
    return (capex * crf(rate, project_lifetime) + om - rev) / h2

def npv(cashflow, capex, rate):
    pv = (1 - (1 + rate) ** (-project_lifetime)) / rate
    return cashflow * pv - capex

# ============================================================
# MODEL OVERVIEW
# ============================================================

if menu == "Model Overview":
    st.subheader("Key System Outputs")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total CAPEX (USD)", f"${total_capex:,.0f}")
    c2.metric("Annual H₂ Production", f"{annual_h2_production:,} kg")
    c3.metric("Project Lifetime", f"{project_lifetime} years")

# ============================================================
# ECONOMIC SUMMARY
# ============================================================

elif menu == "Economic Summary":
    st.subheader("Economic Performance")

    lcoh_8 = lcoh(total_capex, annual_om_cost, annual_revenue, annual_h2_production, wacc_baseline)
    lcoh_4 = lcoh(total_capex, annual_om_cost, annual_revenue, annual_h2_production, wacc_concessional)

    npv_8 = npv(annual_cashflow, total_capex, wacc_baseline)
    npv_4 = npv(annual_cashflow, total_capex, wacc_concessional)

    payback = total_capex / annual_cashflow if annual_cashflow > 0 else np.nan

    c1, c2, c3 = st.columns(3)
    c1.metric("LCOH (8% WACC)", f"${lcoh_8:.2f}/kg")
    c2.metric("NPV (8% WACC)", f"${npv_8/1e6:.2f} Million")
    c3.metric("Payback Period", f"{payback:.1f} years")

    st.metric("LCOH (4% WACC)", f"${lcoh_4:.2f}/kg")
    st.metric("NPV (4% WACC)", f"${npv_4/1e6:.2f} Million")

# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================

elif menu == "Sensitivity Analysis":
    st.subheader("Sensitivity Analysis (LCOH vs CAPEX & O&M)")

    capex_range = np.linspace(0.7, 1.3, 20)
    lcoh_sens = [
        lcoh(total_capex * x, annual_om_cost, annual_revenue,
             annual_h2_production, wacc_baseline)
        for x in capex_range
    ]

    fig, ax = plt.subplots()
    ax.plot(capex_range * 100, lcoh_sens)
    ax.set_xlabel("CAPEX Variation (%)")
    ax.set_ylabel("LCOH ($/kg)")
    ax.set_title("LCOH Sensitivity to CAPEX")
    ax.grid(True)

    st.pyplot(fig)

# ============================================================
# MONTHLY EMS + COST–PROFIT + CO2
# ============================================================

elif menu == "Monthly EMS & Cost–Profit":
    st.subheader("Monthly Energy Management & Cost–Profit Analysis")

    uploaded = st.file_uploader(
        "Upload Monthly Excel / CSV",
        type=["xlsx", "csv"]
    )

    if uploaded:
        df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)

        required = ["Month", "Electricity_Demand_kWh", "Solar_Generation_kWh"]
        if not all(c in df.columns for c in required):
            st.error("Required columns: Month, Electricity_Demand_kWh, Solar_Generation_kWh")
        else:
            df["Grid_Import_kWh"] = np.maximum(df["Electricity_Demand_kWh"] - df["Solar_Generation_kWh"], 0)
            df["Grid_Export_kWh"] = np.maximum(df["Solar_Generation_kWh"] - df["Electricity_Demand_kWh"], 0)

            df["Import_Cost_USD"] = df["Grid_Import_kWh"] * grid_tariff
            df["Export_Revenue_USD"] = df["Grid_Export_kWh"] * export_tariff
            df["Net_Profit_USD"] = df["Export_Revenue_USD"] - df["Import_Cost_USD"]

            df["CO2_Emitted_kg"] = df["Grid_Import_kWh"] * grid_emission_factor
            df["CO2_Avoided_kg"] = df["Grid_Export_kWh"] * grid_emission_factor

            st.dataframe(df)

            st.download_button(
                "Download Results (CSV)",
                df.to_csv(index=False),
                "Monthly_EMS_Results.csv"
            )

            fig, ax = plt.subplots()
            ax.bar(df["Month"], df["Net_Profit_USD"])
            ax.set_ylabel("USD")
            ax.set_title("Monthly Net Cost–Profit")
            ax.grid(True)
            st.pyplot(fig)

            fig2, ax2 = plt.subplots()
            ax2.plot(df["Month"], df["CO2_Avoided_kg"], label="CO₂ Avoided")
            ax2.plot(df["Month"], df["CO2_Emitted_kg"], label="CO₂ Emitted")
            ax2.legend()
            ax2.set_title("Monthly CO₂ Mitigation")
            ax2.grid(True)
            st.pyplot(fig2)

            positive_months = (df["Net_Profit_USD"] > 0).sum()
            st.markdown(
                f"""
                **Interpretation:**  
                The system achieves net positive cash flow in **{positive_months} months**,
                driven primarily by surplus solar electricity export and reduced grid dependence.
                """
            )

# ============================================================
# DOCUMENTATION PAGE
# ============================================================

elif menu == "Documentation / Important Documents":
    st.subheader("Model Documentation (Editable)")

    st.markdown("""
    ### Methodology
    *(Add detailed methodology here later)*

    ### Key Equations
    - LCOH formulation  
    - NPV calculation  
    - Capital Recovery Factor  

    ### Assumptions
    - Grid emission factor  
    - Constant annual hydrogen production  
    - Monthly aggregated energy data  

    ### References
    *(Add journal references, datasets, standards here)*
    """)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    "<p style='text-align:center; font-size:12px;'>"
    "This model is designed by Mohammad Sohel"
    "</p>",
    unsafe_allow_html=True
)
