import streamlit as st

def header_dashboard():
    """
    Muestra el encabezado institucional del Dashboard de Custodia de Vehículos
    con logo, título y diseño tipo banner corporativo.
    """
    st.markdown(
        """
        <div style='background-color: #003366; padding: 15px; border-radius: 8px; display: flex; align-items: center;'>
            <img src="https://images.seeklogo.com/logo-png/17/1/fiscalia-general-de-la-nacion-logo-png_seeklogo-179934.png" 
                 alt="Logo Fiscalía" style="width:100px; margin-right: 20px;">
            <div>
                <h1 style='color: white; margin: 0;'>🚗 Dashboard de Custodia de Vehículos</h1>
                <h3 style='color: #FFD700; margin: 0;'>Fiscalía General de la Nación</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Línea divisoria elegante
    st.markdown("<hr style='border:1px solid #ccc; margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)
