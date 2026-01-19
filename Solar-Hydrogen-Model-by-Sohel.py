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
# SIDEBAR — KEY CONSTANTS & PRESETS
# ============================================================

st.sidebar.header("Key Constants & Presets")

project_lifetime = 20
annual_h2_production = 208_800  # kg/year

wacc_baseline = 0.08
wacc_concessional = 0.04

grid_emission_factor = 0.67  # kg CO2 per kWh

solar_capex = st.sidebar.number_input("Solar PV CAPEX (USD)", 1_000_000.0, value=4_500_000.0)
electrolyzer_capex = st.sidebar.number_input("Electrolyzer CAPEX (USD)", 1_000_000.0, value=6_000_000.0)
fuel_cell_capex = st.sidebar.number_input("Fuel Cell CAPEX (USD)", 0.0, value=1_700_000.0)
storage_capex = st.sidebar.number_input("Hydrogen Storage CAPEX (USD)", 0.0, value=900_000.0)

annual_om_cost = st.sidebar.number_input("Annual O&M Cost (USD/year)", 10_000.0, value=60_000.0)
annual_revenue = st.sidebar.number_input("Annual Revenue (USD/year)", 100_000.0, value=679_549.0)

# ============================================================
# TOTAL CAPEX
# ============================================================

total_capex = solar_capex + electrolyzer_capex + fuel_cell_capex + storage_capex

# ============================================================
# FINANCIAL CORE
# ============================================================

def capital_recovery_factor(rate, lifetime):
    return rate * (1 + rate) ** lifetime / ((1 + rate) ** lifetime - 1)


def calculate_lcoh(total_capex, annual_om, annual_rev, h2, rate, lifetime):
    crf = capital_recovery_factor(rate, lifetime)
    return (total_capex * crf + annual_om - annual_rev) / h2


def calculate_npv(annual_cashflow, total_capex, rate, lifetime):
    pv_factor = (1 - (1 + rate) ** (-lifetime)) / rate
    return annual_cashflow * pv_factor - total_capex


annual_cashflow = annual_revenue - annual_om_cost

lcoh_8 = calculate_lcoh(total_capex, annual_om_cost, annual_revenue,
                        annual_h2_production, wacc_baseline, project_lifetime)

lcoh_4 = calculate_lcoh(total_capex, annual_om_cost, annual_revenue,
                        annual_h2_production, wacc_concessional, project_lifetime)

npv_8 = calculate_npv(annual_cashflow, total_capex, wacc_baseline, project_lifetime)
npv_4 = calculate_npv(annual_cashflow, total_capex, wacc_concessional, project_lifetime)

payback = total_capex / annual_cashflow if annual_cashflow > 0 else np.nan

# ============================================================
# ECONOMIC SUMMARY
# ============================================================

st.subheader("Economic Summary")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total CAPEX (USD)", f"${total_capex:,.0f}")
    st.metric("Payback Period (years)", f"{payback:.1f}")

with c2:
    st.metric("LCOH (8% WACC)", f"${lcoh_8:.2f}/kg")
    st.metric("NPV (8% WACC)", f"${npv_8/1e6:.2f} Million")

with c3:
    st.metric("LCOH (4% WACC)", f"${lcoh_4:.2f}/kg")
    st.metric("NPV (4% WACC)", f"${npv_4/1e6:.2f} Million")

# ============================================================
# MONTHLY ENERGY MANAGEMENT SIMULATION (EMS)
# ============================================================

st.subheader("Energy Management Simulation (Monthly)")

uploaded_file = st.file_uploader(
    "Upload Monthly Energy Data (Excel or CSV)",
    type=["xlsx", "csv"]
)

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    required_cols = ["Month", "Electricity_Demand_kWh", "Solar_Generation_kWh"]
    if not all(col in df.columns for col in required_cols):
        st.error("File must contain columns: Month, Electricity_Demand_kWh, Solar_Generation_kWh")
    else:
        df["Grid_Import_kWh"] = np.maximum(
            df["Electricity_Demand_kWh"] - df["Solar_Generation_kWh"], 0
        )
        df["Grid_Export_kWh"] = np.maximum(
            df["Solar_Generation_kWh"] - df["Electricity_Demand_kWh"], 0
        )

        df["CO2_Emitted_kg"] = df["Grid_Import_kWh"] * grid_emission_factor
        df["CO2_Avoided_kg"] = df["Grid_Export_kWh"] * grid_emission_factor

        st.write("Monthly Energy Balance & CO₂ Mitigation")
        st.dataframe(df)

        # ====================================================
        # CO2 MITIGATION PLOT
        # ====================================================

        fig, ax = plt.subplots()
        ax.plot(df["Month"], df["CO2_Emitted_kg"], label="CO₂ Emitted")
        ax.plot(df["Month"], df["CO2_Avoided_kg"], label="CO₂ Avoided")
        ax.set_ylabel("kg CO₂")
        ax.set_title("Monthly CO₂ Emission & Mitigation")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    "<p style='text-align:center; font-size:12px;'>"
    "this model is designed by Mohammad Sohel"
    "</p>",
    unsafe_allow_html=True
)
