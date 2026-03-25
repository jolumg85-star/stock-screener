import streamlit as st
import yfinance as yf
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Value Stock Screener", layout="wide")

st.title("📊 Buscador de Acciones Value (Yahoo Finance)")
st.markdown("""
Esta aplicación escanea acciones basándose en criterios de inversión de valor:
- **PER** < 15
- **P/B** < 1.5
- **EV/EBITDA** < 10
- **ROE** > 10%
- **FCF Yield** > 5%
- **Deuda/Patrimonio** < 1
""")

# Lista de acciones a analizar (Ejemplo: S&P 500 o Dow Jones)
# NOTA: Para un escaneo real del mercado entero se necesita una API de pago.
# Aquí usamos una lista representativa de acciones industriales y financieras.
tickers_list = [
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW',
    'CVX', 'XOM', 'COP', 'SLB', 'OXY', 'MRO', 'DVN',
    'PFE', 'JNJ', 'MRK', 'ABBV', 'BMY', 'GILD', 'LLY',
    'KO', 'PEP', 'WMT', 'TGT', 'COST', 'HD', 'LOW',
    'F', 'GM', 'STLA', 'TM', 'HMC', 'VWAGY',
    'INTC', 'IBM', 'HPQ', 'CSCO', 'QCOM', 'TXN',
    'VZ', 'T', 'TMUS', 'CMCSA', 'DIS'
]

@st.cache_data
def get_stock_data(tickers):
    data = []
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extracción de datos básicos
            price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            market_cap = info.get('marketCap', 0)
            
            # 1. PER (Price to Earnings)
            pe_ratio = info.get('trailingPE', 999)
            
            # 2. P/B (Price to Book)
            pb_ratio = info.get('priceToBook', 999)
            
            # 3. EV/EBITDA
            ev_ebitda = info.get('enterpriseToEbitda', 999)
            
            # 4. ROE (Return on Equity) - Viene en decimal (ej: 0.15 es 15%)
            roe = info.get('returnOnEquity', 0) * 100 
            
            # 5. FCF Yield (Free Cash Flow Yield)
            # Cálculo: Free Cash Flow / Market Cap
            fcf = info.get('freeCashflow', 0)
            fcf_yield = (fcf / market_cap) * 100 if market_cap > 0 else 0
            
            # 6. Deuda / Patrimonio (Debt to Equity)
            debt_to_equity = info.get('debtToEquity', 999)
            
            # Cálculo de caída (Comparativa con Máximo de 52 semanas)
            high_52 = info.get('fiftyTwoWeekHigh', price)
            drop_percent = ((high_52 - price) / high_52) * 100 if high_52 > 0 else 0
            
            # Nombre de la empresa
            company_name = info.get('shortName', ticker)
            
            data.append({
                'Ticker': ticker,
                'Nombre': company_name,
                'Precio': price,
                'PER': pe_ratio,
                'P/B': pb_ratio,
                'EV/EBITDA': ev_ebitda,
                'ROE (%)': roe,
                'FCF Yield (%)': fcf_yield,
                'Deuda/Patrimonio': debt_to_equity,
                'Caída desde Max 52s (%)': drop_percent
            })
            
        except Exception as e:
            pass
            
        progress_bar.progress((i + 1) / len(tickers))
        
    return pd.DataFrame(data)

# Botón para ejecutar el análisis
if st.button("🔍 Analizar Acciones"):
    with st.spinner('Obteniendo datos en tiempo real...'):
        df = get_stock_data(tickers_list)
        
        # --- FILTROS ---
        
        # Filtros estrictos
        mask = (
            (df['PER'] < 15) & 
            (df['P/B'] < 1.5) & 
            (df['EV/EBITDA'] < 10) & 
            (df['ROE (%)'] > 10) & 
            (df['FCF Yield (%)'] > 5) & 
            (df['Deuda/Patrimonio'] < 1)
        )
        
        df_filtered = df[mask].copy()
        
        # Ordenar por mejor combinación (ej: menor PER y mayor ROE)
        # Creamos un score simple para ordenar: (ROE / PER)
        df_filtered['Score'] = df_filtered['ROE (%)'] / df_filtered['PER'].replace(0, 1)
        df_filtered = df_filtered.sort_values(by='Score', ascending=False)
        
        # --- TOP 1: MEJORES ACCIONES (VALUE) ---
        st.subheader("🏆 Top 5: Las Mejores Acciones Value")
        if not df_filtered.empty:
            top5_general = df_filtered.head(5)
            st.dataframe(top5_general[['Ticker', 'Nombre', 'Precio', 'PER', 'P/B', 'ROE (%)', 'FCF Yield (%)']], hide_index=True)
        else:
            st.warning("No se encontraron acciones que cumplan todos los criterios en la lista actual.")

        st.divider()

        # --- TOP 2: ACCIONES CAÍDAS (DEEP VALUE) ---
        st.subheader("📉 Top 5: Oportunidades en Caída (30% - 50%)")
        
        # Filtramos las que ya cumplieron los ratios Y además cayeron entre 30 y 50%
        mask_drop = (df_filtered['Caída desde Max 52s (%)'] >= 30) & (df_filtered['Caída desde Max 52s (%)'] <= 50)
        df_drop = df_filtered[mask_drop]
        
        # Ordenamos por la caída más profunda dentro del rango
        df_drop = df_drop.sort_values(by='Caída desde Max 52s (%)', ascending=False)
        
        if not df_drop.empty:
            top5_drop = df_drop.head(5)
            st.dataframe(top5_drop[['Ticker', 'Nombre', 'Precio', 'Caída desde Max 52s (%)', 'PER', 'ROE (%)']], hide_index=True)
        else:
            st.info("No se encontraron acciones con ratios sólidos que hayan caído entre un 30% y 50% en esta lista.")

        # Mostrar todos los datos filtrados
        with st.expander("Ver todas las acciones que pasaron el filtro"):
            st.dataframe(df_filtered)

else:
    st.info("Presiona el botón 'Analizar Acciones' para comenzar.")

# Footer
st.markdown("---")
st.caption("Nota: Los datos provienen de Yahoo Finance y pueden tener un retraso de 15 minutos. Los ratios financieros dependen de los reportes trimestrales.")