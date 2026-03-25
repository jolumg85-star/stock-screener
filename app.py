import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Value Stock Screener", layout="wide")

st.title("📊 Buscador de Acciones Value (Yahoo Finance)")
st.markdown("""
### Criterios de filtrado:
| Ratio | Condición | Tu requisito |
|-------|-----------|--------------|
| **PER** | `<= 15` | 15 o menor ✅ |
| **P/B** | `<= 1.5` | 1.5 o menor ✅ |
| **EV/EBITDA** | `<= 10` | 10 o menor ✅ |
| **ROE** | `> 10%` | Mayor al 10% ✅ |
| **FCF Yield** | `> 5%` | Mayor al 5% ✅ |
| **Deuda/Patrimonio** | `< 1` | Menor a 1 ✅ |
""")

# Lista AMPLIADA de acciones value-típicas (bancos, energía, industrias, telecom)
tickers_list = [
    # Bancos y Finanzas
    'JPM', 'BAC', 'WFC', 'C', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT',
    # Energía
    'CVX', 'XOM', 'COP', 'EOG', 'SLB', 'OXY', 'MRO', 'DVN', 'HAL', 'BKR',
    # Industriales
    'GE', 'CAT', 'BA', 'HON', 'MMM', 'DE', 'EMR', 'ETN', 'ITW', 'ROK',
    # Consumo Básico
    'KO', 'PEP', 'WMT', 'TGT', 'COST', 'KR', 'SYY', 'GIS', 'K', 'CPB',
    # Salud/Farma
    'PFE', 'JNJ', 'MRK', 'ABBV', 'BMY', 'GILD', 'CVS', 'UNH', 'CI', 'HUM',
    # Telecom/Utilities
    'VZ', 'T', 'TMUS', 'D', 'SO', 'DUK', 'NEE', 'AEP', 'EXC', 'XEL',
    # Automotriz/Otros Value
    'F', 'GM', 'STLA', 'HMC', 'TM', 'VWAGY', 'IBM', 'INTC', 'HPQ', 'CSCO'
]

@st.cache_data(ttl=3600)  # Cache por 1 hora para no saturar Yahoo
def get_stock_data(tickers):
    data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # --- Datos básicos ---
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            if not price or price <= 0:
                continue  # Saltar si no hay precio válido
                
            market_cap = info.get('marketCap') or 0
            if market_cap < 1e9:  # Filtrar micro-caps (<1B) para evitar datos ruidosos
                continue
            
            # --- Extracción de ratios con manejo de None ---
            pe_ratio = info.get('trailingPE')
            pb_ratio = info.get('priceToBook')
            ev_ebitda = info.get('enterpriseToEbitda')
            roe = info.get('returnOnEquity')  # Viene en decimal (0.15 = 15%)
            fcf = info.get('freeCashflow')  # Puede ser negativo
            debt_to_equity = info.get('debtToEquity')
            high_52 = info.get('fiftyTwoWeekHigh')
            
            # --- Cálculos ---
            # ROE a porcentaje
            roe_pct = (roe * 100) if roe is not None else None
            
            # FCF Yield: (Free Cash Flow / Market Cap) * 100
            fcf_yield = None
            if fcf is not None and market_cap > 0:
                fcf_yield = (fcf / market_cap) * 100
            
            # Caída desde máximo de 52 semanas
            drop_pct = None
            if high_52 and high_52 > 0:
                drop_pct = ((high_52 - price) / high_52) * 100
            
            # Nombre de la empresa
            company_name = info.get('shortName') or info.get('longName') or ticker
            
            data.append({
                'Ticker': ticker,
                'Nombre': company_name,
                'Precio': round(price, 2),
                'PER': pe_ratio,
                'P/B': pb_ratio,
                'EV/EBITDA': ev_ebitda,
                'ROE (%)': round(roe_pct, 2) if roe_pct else None,
                'FCF Yield (%)': round(fcf_yield, 2) if fcf_yield else None,
                'Deuda/Patrimonio': debt_to_equity,
                'Caída desde Max 52s (%)': round(drop_pct, 2) if drop_pct else None,
                'Market Cap (B)': round(market_cap / 1e9, 2)
            })
            
        except Exception as e:
            continue  # Saltar errores silenciosamente
            
        progress_bar.progress((i + 1) / len(tickers))
        status_text.text(f"Procesando: {ticker} ({i+1}/{len(tickers)})")
    
    status_text.empty()
    return pd.DataFrame(data)

# --- PANEL LATERAL: Controles ---
st.sidebar.header("⚙️ Ajustes de Filtro")

# Permitir ajustar criterios desde la UI (útil para testing)
filter_per = st.sidebar.number_input("PER (máximo)", value=15, min_value=1, max_value=100)
filter_pb = st.sidebar.number_input("P/B (máximo)", value=1.5, min_value=0.1, max_value=20.0, step=0.1)
filter_ev_ebitda = st.sidebar.number_input("EV/EBITDA (máximo)", value=10, min_value=1, max_value=100)
filter_roe = st.sidebar.number_input("ROE mínimo (%)", value=10, min_value=0, max_value=100)
filter_fcf = st.sidebar.number_input("FCF Yield mínimo (%)", value=5, min_value=0, max_value=50)
filter_de = st.sidebar.number_input("Deuda/Patrimonio (máximo)", value=1.0, min_value=0.1, max_value=10.0, step=0.1)

# Checkbox para relajar filtros temporalmente
relax_mode = st.sidebar.checkbox("🔓 Modo relajado (ignorar FCF Yield)", value=False)

if st.button("🔍 Analizar Acciones", type="primary"):
    with st.spinner('Consultando Yahoo Finance... Esto puede tardar 1-2 minutos.'):
        df = get_stock_data(tickers_list)
        
        if df.empty:
            st.error("❌ No se pudieron obtener datos de ninguna acción. Revisa tu conexión o intenta más tarde.")
            st.stop()
        
        st.success(f"✅ Datos obtenidos de {len(df)} acciones. Aplicando filtros...")
        
        # --- APLICAR FILTROS CON TUS CRITERIOS EXACTOS ---
        # Usamos <= para PER, P/B, EV/EBITDA como pediste
        mask = (
            (df['PER'].notna()) & (df['PER'] <= filter_per) &
            (df['P/B'].notna()) & (df['P/B'] <= filter_pb) &
            (df['EV/EBITDA'].notna()) & (df['EV/EBITDA'] <= filter_ev_ebitda) &
            (df['ROE (%)'].notna()) & (df['ROE (%)'] > filter_roe) &
            (df['Deuda/Patrimonio'].notna()) & (df['Deuda/Patrimonio'] < filter_de)
        )
        
        if not relax_mode:
            mask = mask & (df['FCF Yield (%)'].notna()) & (df['FCF Yield (%)'] > filter_fcf)
        else:
            st.warning("🔓 Modo relajado: Ignorando filtro de FCF Yield")
        
        df_filtered = df[mask].copy()
        
        # Calcular score para ranking: (ROE / PER) - prioriza alto retorno, bajo precio
        df_filtered = df_filtered.copy()
        df_filtered['Score'] = df_filtered['ROE (%)'] / df_filtered['PER'].replace(0, 1)
        df_filtered = df_filtered.sort_values(by='Score', ascending=False)
        
        # --- 🏆 TOP 1: MEJORES ACCIONES VALUE ---
        st.subheader("🏆 Top 5: Mejores Acciones Value")
        if not df_filtered.empty:
            display_cols = ['Ticker', 'Nombre', 'Precio', 'PER', 'P/B', 'EV/EBITDA', 'ROE (%)', 'FCF Yield (%)', 'Deuda/Patrimonio']
            st.dataframe(df_filtered.head(5)[display_cols].style.format({
                'Precio': '${:.2f}', 'PER': '{:.2f}', 'P/B': '{:.2f}', 
                'EV/EBITDA': '{:.2f}', 'ROE (%)': '{:.1f}%', 'FCF Yield (%)': '{:.1f}%',
                'Deuda/Patrimonio': '{:.2f}'
            }), hide_index=True, use_container_width=True)
        else:
            st.warning("⚠️ Ninguna acción cumple TODOS los criterios. Prueba:")
            st.markdown("""
            - ✅ Activar **"Modo relajado"** en el panel lateral
            - ✅ Aumentar ligeramente los límites (ej: PER <= 18)
            - ✅ Revisar la tabla de "Análisis de Filtros" más abajo
            """)
        
        st.divider()
        
        # --- 📉 TOP 2: ACCIONES CAÍDAS (30%-50%) ---
        st.subheader("📉 Top 5: Oportunidades en Caída (30% - 50%)")
        
        if not df_filtered.empty:
            mask_drop = (
                (df_filtered['Caída desde Max 52s (%)'].notna()) &
                (df_filtered['Caída desde Max 52s (%)'] >= 30) &
                (df_filtered['Caída desde Max 52s (%)'] <= 50)
            )
            df_drop = df_filtered[mask_drop].copy()
            df_drop = df_drop.sort_values(by='Caída desde Max 52s (%)', ascending=False)
            
            if not df_drop.empty:
                display_cols_drop = ['Ticker', 'Nombre', 'Precio', 'Caída desde Max 52s (%)', 'PER', 'ROE (%)', 'FCF Yield (%)']
                st.dataframe(df_drop.head(5)[display_cols_drop].style.format({
                    'Precio': '${:.2f}', 'Caída desde Max 52s (%)': '{:.1f}%',
                    'PER': '{:.2f}', 'ROE (%)': '{:.1f}%', 'FCF Yield (%)': '{:.1f}%'
                }), hide_index=True, use_container_width=True)
            else:
                st.info("ℹ️ No hay acciones con ratios sólidos que hayan caído entre 30%-50% en esta lista.")
                st.caption("💡 Tip: Las acciones muy 'value' a veces no caen tanto porque ya están baratas. Prueba ampliar la lista de tickers.")
        else:
            st.caption("Primero deben aparecer acciones en el Top 1 para poder filtrar por caída.")
        
        # --- 🔍 ANÁLISIS DE FILTROS (DEBUG) ---
        with st.expander("🔍 Ver análisis: ¿Por qué se filtran las acciones?"):
            st.markdown("### 📊 Resumen de filtrado")
            
            # Contar cuántas acciones pasan cada filtro individualmente
            filters_info = [
                (f"PER <= {filter_per}", len(df[df['PER'].notna() & (df['PER'] <= filter_per)])),
                (f"P/B <= {filter_pb}", len(df[df['P/B'].notna() & (df['P/B'] <= filter_pb)])),
                (f"EV/EBITDA <= {filter_ev_ebitda}", len(df[df['EV/EBITDA'].notna() & (df['EV/EBITDA'] <= filter_ev_ebitda)])),
                (f"ROE > {filter_roe}%", len(df[df['ROE (%)'].notna() & (df['ROE (%)'] > filter_roe)])),
                (f"FCF Yield > {filter_fcf}%", len(df[df['FCF Yield (%)'].notna() & (df['FCF Yield (%)'] > filter_fcf)])),
                (f"Deuda/Patrimonio < {filter_de}", len(df[df['Deuda/Patrimonio'].notna() & (df['Deuda/Patrimonio'] < filter_de)])),
                ("**TODOS LOS FILTROS**", len(df_filtered))
            ]
            
            for name, count in filters_info:
                st.metric(name, f"{count} / {len(df)}")
            
            st.markdown("### 📋 Acciones que casi pasan (fallan en solo 1 criterio)")
            # Mostrar acciones que fallan en solo 1 filtro para diagnóstico
            almost_there = []
            for _, row in df.iterrows():
                fails = 0
                if pd.isna(row['PER']) or row['PER'] > filter_per: fails += 1
                if pd.isna(row['P/B']) or row['P/B'] > filter_pb: fails += 1
                if pd.isna(row['EV/EBITDA']) or row['EV/EBITDA'] > filter_ev_ebitda: fails += 1
                if pd.isna(row['ROE (%)']) or row['ROE (%)'] <= filter_roe: fails += 1
                if not relax_mode and (pd.isna(row['FCF Yield (%)']) or row['FCF Yield (%)'] <= filter_fcf): fails += 1
                if pd.isna(row['Deuda/Patrimonio']) or row['Deuda/Patrimonio'] >= filter_de: fails += 1
                
                if fails == 1:  # Casi lo logra
                    almost_there.append(row)
            
            if almost_there:
                df_almost = pd.DataFrame(almost_there).head(10)
                st.dataframe(df_almost[['Ticker', 'Nombre', 'PER', 'P/B', 'EV/EBITDA', 'ROE (%)', 'FCF Yield (%)', 'Deuda/Patrimonio']], hide_index=True)
            else:
                st.caption("Ninguna acción está cerca de cumplir todos los criterios.")
        
        # --- 📥 Descargar resultados ---
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar resultados filtrados (CSV)",
                data=csv,
                file_name="value_stocks_filter.csv",
                mime="text/csv"
            )

else:
    st.info("👈 Presiona **'Analizar Acciones'** para comenzar el escaneo.")
    st.markdown("""
    ### 💡 Consejos para obtener resultados:
    1. **Estos criterios son MUY estrictos** (típicos de value investing profundo).
    2. Es normal que pocas o ninguna acción pase todos los filtros simultáneamente.
    3. Usa el **panel lateral** para relajar temporalmente algún criterio y ver qué acciones se acercan.
    4. La lista de tickers incluye ~60 acciones value-típicas. Puedes editar `app.py` para añadir más.
    """)

# Footer
st.markdown("---")
st.caption("⚠️ Datos de Yahoo Finance pueden tener retraso. Los ratios financieros se actualizan trimestralmente. Esto no es asesoramiento financiero.")
