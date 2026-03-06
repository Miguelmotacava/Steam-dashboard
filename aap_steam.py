##############################################
###     DASHBOARD DE STEAM EN STREAMLIT     ##
##############################################


## IMPORTACIONES

import streamlit as st
import pandas as pd
import numpy as np

# librerias gráficos
import plotly as px



st.title("Hello Streamlit-er 👋")
st.markdown(
    """ 
    This is a playground for you to try Streamlit and have fun. 

    **There's :rainbow[so much] you can build!**
    
    We prepared a few examples for you to get started. Just 
    click on the buttons above and discover what you can do 
    with Streamlit. 
    """
)

if st.button("Send balloons!"):
    st.balloons()
