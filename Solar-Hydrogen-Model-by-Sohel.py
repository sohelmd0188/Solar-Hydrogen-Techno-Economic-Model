
import streamlit as st

st.set_page_config(page_title="Solar Hydrogen Techno-Economic Model", layout="wide")

st.title("Solar Hydrogen Techno-Economic Model")

st.sidebar.header("System Inputs")

fuel_cell_capex = st.sidebar.number_input("Fuel Cell CAPEX (USD)", min_value=0.0, value=0.0)
include_fc = st.sidebar.checkbox("Include Fuel Cell in System", value=True)

st.markdown("### Overview")
st.write("This is the upgraded skeleton version of the Solar Hydrogen Techno-Economic Model.")

st.markdown("---")
st.markdown(
    "<p style='text-align:center; font-size:12px;'>this model is designed by Mohammad Sohel</p>",
    unsafe_allow_html=True
)
