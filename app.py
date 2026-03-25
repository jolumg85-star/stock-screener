import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Value Investing Screener Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stDataFrame {
        font-size: 14px;
    }
    .good-value {
        color: #00CC44;
        font-weight: bold;
    }
    .bad-value {
        color: #FF4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LISTA DE ACCIONES VALUE
# ============================================================================
VALUE_TICKERS = [
    'JPM', 'BAC', 'WFC', 'C', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT',
    'CVX', 'XOM', 'COP', 'EOG', 'SLB', 'OXY', 'MRO', 'DVN', 'HAL', 'BKR',
    'GE', 'CAT', 'BA', 'HON', 'MMM', 'DE', 'EMR', 'ETN', 'ITW', 'ROK',
    'KO', 'PEP', 'WMT', 'TGT', 'COST', 'KR', 'SYY', 'GIS', 'K', 'CPB',
    'PFE', 'JNJ', 'MRK', 'ABBV', 'BMY', 'GILD', 'CVS', 'UNH', 'CI', 'HUM',
    'VZ', 'T', 'TMUS', 'D', 'SO', 'DUK', 'NEE', 'AEP', 'EXC', 'XEL',
    'F', 'GM', 'STLA', 'HMC', 'TM', 'IBM', 'INTC', 'HPQ', 'CSCO', 'QCOM',
    'BRK.B', 'AIG', 'MET', 'PRU', 'ALL', 'TRV', 'PGR', 'CB', 'AFL', 'HIG',
    'HD', 'LOW', 'DG', 'DLTR', 'ROST', 'TJX', 'BBY', 'GPS', 'M', 'KSS'
]

# ============================================================================
# FUNCIÓN DE CÁLCULO DE RATIOS
# ============================================================================

def calculate_financial_ratios(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not price or price <= 0:
            return None
            
        market_cap = info.get('marketCap') or 0
        enterprise_value = info.get('enterpriseValue') or market_cap
        
        # PER
        pe_ratio = info.get('trailingPE')
        if not pe_ratio or pe_ratio <= 0:
            eps = info.get('trailingEps')
            if eps and eps > 0:
                pe_ratio = price / eps
        
        # P/B
        pb_ratio = info.get('priceToBook')
        if not pb_ratio or pb_ratio <= 0:
            book_value = info.get('bookValue')
            if book_value and book_value > 0:
                pb_ratio = price / book_value
        
        # EV/EBITDA
        ev_ebitda = info.get('enterpriseToEbitda')
        if not ev_ebitda or ev_ebitda <= 0:
            ebitda = info.get('ebitda')
            if ebitda and ebitda > 0 and enterprise_value > 0:
                ev_ebitda = enterprise_value / ebitda
        
        # ROE
        roe = info.get('returnOnEquity')
        if not roe:
            net_income = info.get('netIncomeToCommon')
            equity = info.get('totalStockholderEquity')
            if net_income and equity and equity > 0:
                roe = net_income / equity
        
        # FCF Yield
        fcf = info.get('freeCashflow')
        operating_cash_flow = info.get('operatingCashflow')
        capex = info.get('capitalExpenditures')
        
        if not fcf and operating_cash_flow and capex:
            fcf = operating_cash_flow + capex
        
        fcf_yield = None
        if fcf and market_cap and market_cap > 0:
            fcf_yield = (fcf / market_cap) * 100
        
        # Debt to Equity
        debt_to_equity = info.get('debtToEquity')
        if not debt_to_equity:
            total_debt = info.get('totalDebt')
            equity = info.get('totalStockholderEquity')
            if total_debt and equity and equity > 0:
                debt_to_equity = total_debt / equity
        
        # Caída 52 semanas
        high_52 = info.get('fiftyTwoWeekHigh')
        low_52 = info.get('fiftyTwoWeekLow')
        drop_from_high = None
        if high_52 and high_52 > 0:
            drop_from_high = ((high_52 - price) / high_52) * 100
        
        # Dividend Yield
        dividend_yield = info.get('dividendYield')
        if dividend_yield:
            dividend_yield = dividend_yield * 100
        
        # Beta
        beta = info.get('beta')
        
        company_name = info.get('shortName') or info.get('longName') or ticker
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        
        data_points = [pe_ratio, pb_ratio, ev_ebitda, roe, fcf_yield, debt_to_equity]
        complete_data = sum(1 for x in data_points if x is not None and x > 0)
        
        return {
            'Ticker': ticker,
            'Nombre': company_name,
            'Sector': sector,
            'Industria': industry,
            'Precio': round(price, 2) if price else None,
            'Market Cap (B)': round(market_cap / 1e9, 2) if market_cap else None,
            'PER': round(pe_ratio, 2) if pe_ratio and pe_ratio > 0 else None,
            'P/B': round(pb_ratio, 2) if pb_ratio and pb_ratio > 0 else None,
            'EV/EBITDA': round(ev_ebitda, 2) if ev_ebitda and ev_ebitda > 0 else None,
            'ROE (%)': round(roe * 100, 2) if roe else None,
            'FCF Yield (%)': round(fcf_yield, 2) if fcf_yield else None,
            'Deuda/Patrimonio': round(debt_to_equity, 2) if debt_to_equity else None,
            'Caída desde Max 52s (%)': round(drop_from_high, 2) if drop_from_high else None,
            'Dividend Yield (%)': round(dividend_yield, 2) if dividend_yield else None,
            'Beta': round(beta, 2) if beta else None,
            'Datos Completos': complete_data / 6
        }
        
    except Exception:
        return None

# ============================================================================
# FUNCIÓN DE ANÁLISIS
# ============================================================================

@st.cache_data(ttl=7200)
def analyze_stocks(tickers, show_progress=True):
    results = []
    
    if show_progress:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        try:
            data = calculate_financial_ratios(ticker)
            if data and data['Datos Completos'] >= 0.5:
                results.append(data)
        except Exception:
            continue
        
        if show_progress:
            progress = (i + 1) / len(tickers)
            progress_bar.progress(progress)
            status_text.text(f"Analizando: {ticker} ({i+1}/{len(tickers)}) - {len(results)} válidas")
    
    if show_progress:
        status_text.empty()
    
    return pd.DataFrame(results)

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

st.title("📈 Value Investing Screener Pro")
st.markdown("""
### 🔍 Analizador Profesional de Acciones Value
Busca **empresas infravaloradas** según criterios de **Benjamin Graham y Warren Buffett**.
""")

# ============================================================================
# PANEL LATERAL - FILTROS
# ============================================================================

st.sidebar.header("⚙️ Criterios de Value Investing")
st.sidebar.markdown("---")

st.sidebar.subheader("📊 Ratios Fundamentales")

filter_per = st.sidebar.slider(
    "PER (P/E) máximo",
    min_value=1.0, max_value=50.0, value=15.0, step=1.0,
    help="Value: < 15"
)

filter_pb = st.sidebar.slider(
    "P/B (Price to Book) máximo",
    min_value=0.1, max_value=5.0, value=1.5, step=0.1,
    help="Value: < 1.5"
)

filter_ev_ebitda = st.sidebar.slider(
    "EV/EBITDA máximo",
    min_value=1.0, max_value=50.0, value=10.0, step=1.0,
    help="Value: < 10"
)

filter_roe = st.sidebar.slider(
    "ROE mínimo (%)",
    min_value=0.0, max_value=50.0, value=10.0, step=1.0,
    help="Value: > 10%"
)

filter_fcf = st.sidebar.slider(
    "FCF Yield mínimo (%)",
    min_value=0.0, max_value=20.0, value=5.0, step=0.5,
    help="Value: > 5%"
)

filter_de = st.sidebar.slider(
    "Deuda/Patrimonio máximo",
    min_value=0.0, max_value=5.0, value=1.0, step=0.1,
    help="Value: < 1"
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtros Adicionales")

min_market_cap = st.sidebar.number_input(
    "Market Cap mínimo (miles de millones $)",
    min_value=0.0, max_value=1000.0, value=1.0, step=0.5
)

min_dividend_yield = st.sidebar.number_input(
    "Dividend Yield mínimo (%)",
    min_value=0.0, max_value=15.0, value=0.0, step=0.5
)

max_beta = st.sidebar.number_input(
    "Beta máximo (volatilidad)",
    min_value=0.0, max_value=3.0, value=2.0, step=0.1
)

st.sidebar.markdown("---")
st.sidebar.subheader("📉 Filtro de Caída")

enable_drop_filter = st.sidebar.checkbox(
    "Filtrar por caída de precio",
    value=False
)

if enable_drop_filter:
    min_drop = st.sidebar.slider("Caída mínima desde máximos (%)", 10.0, 80.0, 30.0, step=5.0)
    max_drop = st.sidebar.slider("Caída máxima desde máximos (%)", 10.0, 80.0, 50.0, step=5.0)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Opciones")

relax_mode = st.sidebar.checkbox(
    "🔓 Modo Relajado",
    value=False,
    help="Ignorar FCF Yield si no hay datos"
)

min_data_completeness = st.sidebar.slider(
    "Datos completos mínimos (%)",
    min_value=30.0, max_value=100.0, value=50.0, step=10.0
)

# ============================================================================
# BOTONES
# ============================================================================

col1, col2 = st.columns([4, 1])
with col1:
    analyze_button = st.button("🔍 ANALIZAR ACCIONES VALUE", type="primary", use_container_width=True)
with col2:
    clear_cache = st.button("🔄 Limpiar Cache")

if clear_cache:
    st.cache_data.clear()
    st.success("✅ Cache limpiada.")

# ============================================================================
# EJECUCIÓN
# ============================================================================

if analyze_button:
    with st.spinner('📊 Analizando ' + str(len(VALUE_TICKERS)) + ' acciones... (2-3 minutos)'):
        
        df = analyze_stocks(VALUE_TICKERS)
        
        if df.empty:
            st.error("❌ No se pudieron obtener datos. Verifica tu conexión.")
            st.stop()
        
        # Aplicar filtros
        df = df[df['Datos Completos'] >= (min_data_completeness / 100)].copy()
        df = df[df['Market Cap (B)'] >= min_market_cap].copy()
        
        mask_value = (
            (df['PER'].notna()) & (df['PER'] <= filter_per) &
            (df['P/B'].notna()) & (df['P/B'] <= filter_pb) &
            (df['EV/EBITDA'].notna()) & (df['EV/EBITDA'] <= filter_ev_ebitda) &
            (df['ROE (%)'].notna()) & (df['ROE (%)'] >= filter_roe) &
            (df['Deuda/Patrimonio'].notna()) & (df['Deuda/Patrimonio'] <= filter_de)
        )
        
        if not relax_mode:
            mask_value = mask_value & (df['FCF Yield (%)'].notna()) & (df['FCF Yield (%)'] >= filter_fcf)
        
        if min_dividend_yield > 0:
            mask_value = mask_value & (df['Dividend Yield (%)'].notna()) & (df['Dividend Yield (%)'] >= min_dividend_yield)
        
        mask_value = mask_value & (df['Beta'].notna()) & (df['Beta'] <= max_beta)
        
        if enable_drop_filter:
            mask_value = mask_value & (
                (df['Caída desde Max 52s (%)'].notna()) &
                (df['Caída desde Max 52s (%)'] >= min_drop) &
                (df['Caída desde Max 52s (%)'] <= max_drop)
            )
        
        df_filtered = df[mask_value].copy()
        
        # Value Score
        df_filtered = df_filtered.copy()
        
        def calculate_value_score(row):
            score = 0
            if row['PER'] and row['PER'] > 0:
                score += (15 / row['PER']) * 25
            if row['P/B'] and row['P/B'] > 0:
                score += (1.5 / row['P/B']) * 20
            if row['EV/EBITDA'] and row['EV/EBITDA'] > 0:
                score += (10 / row['EV/EBITDA']) * 20
            if row['ROE (%)']:
                score += (row['ROE (%)'] / 10) * 20
            if row['FCF Yield (%)']:
                score += (row['FCF Yield (%)'] / 5) * 15
            if row['Deuda/Patrimonio']:
                score += max(0, (1 - row['Deuda/Patrimonio'])) * 10
            return score
        
        df_filtered['Value Score'] = df_filtered.apply(calculate_value_score, axis=1)
        df_filtered = df_filtered.sort_values(by='Value Score', ascending=False)
        
        # ====================================================================
        # RESUMEN
        # ====================================================================
        
        st.markdown("---")
        st.subheader("📊 Resumen del Análisis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Acciones Analizadas", len(df))
        with col2:
            st.metric("Cumplen Criterios", len(df_filtered))
        with col3:
            st.metric("Tasa de Éxito", f"{(len(df_filtered)/len(df)*100):.1f}%")
        with col4:
            avg_score = df_filtered['Value Score'].mean() if not df_filtered.empty else 0
            st.metric("Score Promedio", f"{avg_score:.1f}")
        
        # ====================================================================
        # TOP 5 VALUE
        # ====================================================================
        
        st.markdown("---")
        st.subheader("🏆 TOP 5: Mejores Oportunidades Value")
        
        if not df_filtered.empty:
            top5 = df_filtered.head(5)
            
            for idx, row in top5.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([2, 3, 2])
                    with c1:
                        st.markdown(f"### {row['Ticker']}")
                        st.caption(row['Nombre'])
                        st.markdown(f"**Sector:** {row['Sector']}")
                    with c2:
                        cols = st.columns(3)
                        cols[0].metric("PER", f"{row['PER']:.2f}" if row['PER'] else "N/A")
                        cols[1].metric("P/B", f"{row['P/B']:.2f}" if row['P/B'] else "N/A")
                        cols[2].metric("EV/EBITDA", f"{row['EV/EBITDA']:.2f}" if row['EV/EBITDA'] else "N/A")
                    with c3:
                        cols = st.columns(2)
                        cols[0].metric("ROE", f"{row['ROE (%)']:.1f}%" if row['ROE (%)'] else "N/A")
                        cols[1].metric("FCF Yield", f"{row['FCF Yield (%)']:.1f}%" if row['FCF Yield (%)'] else "N/A")
                    
                    drop_text = f"{row['Caída desde Max 52s (%)']:.1f}%" if row['Caída desde Max 52s (%)'] else "N/A"
                    st.markdown(f"**Value Score:** {row['Value Score']:.1f} | **Precio:** ${row['Precio']:.2f} | **Caída:** {drop_text}")
                    st.divider()
            
            display_cols = [
                'Ticker', 'Nombre', 'Precio', 'PER', 'P/B', 'EV/EBITDA',
                'ROE (%)', 'FCF Yield (%)', 'Deuda/Patrimonio', 'Dividend Yield (%)',
                'Caída desde Max 52s (%)', 'Value Score'
            ]
            st.dataframe(
                top5[display_cols],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("""
            ⚠️ **Ninguna acción cumple TODOS los criterios.**
            
            Prueba:
            - ✅ Activar **Modo Relajado**
            - ✅ Aumentar PER (18-20) o P/B (2.0)
            - ✅ Reducir FCF Yield mínimo (3-4%)
            """)
        
        # ====================================================================
        # TOP 5 CAÍDAS
        # ====================================================================
        
        st.markdown("---")
        st.subheader("📉 TOP 5: Oportunidades en Caída (30% - 50%)")
        
        if not df_filtered.empty:
            mask_drop = (
                (df_filtered['Caída desde Max 52s (%)'].notna()) &
                (df_filtered['Caída desde Max 52s (%)'] >= 30) &
                (df_filtered['Caída desde Max 52s (%)'] <= 50)
            )
            df_drop = df_filtered[mask_drop].copy()
            df_drop = df_drop.sort_values(by='Caída desde Max 52s (%)', ascending=False)
            
            if not df_drop.empty:
                st.success(f"✅ {len(df_drop)} acciones en caída significativa")
                
                display_cols_drop = [
                    'Ticker', 'Nombre', 'Precio', 'Caída desde Max 52s (%)',
                    'PER', 'P/B', 'ROE (%)', 'FCF Yield (%)'
                ]
                st.dataframe(
                    df_drop.head(5)[display_cols_drop],
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("ℹ️ No hay acciones con caída 30-50% que cumplan los criterios.")
        
        # ====================================================================
        # ANÁLISIS DE FILTROS (SIN MATPLOTLIB)
        # ====================================================================
        
        st.markdown("---")
        with st.expander("🔍 Análisis de Filtros"):
            st.markdown("### 📊 Efecto de cada filtro")
            
            filters_breakdown = [
                (f"PER ≤ {filter_per}", len(df[df['PER'].notna() & (df['PER'] <= filter_per)])),
                (f"P/B ≤ {filter_pb}", len(df[df['P/B'].notna() & (df['P/B'] <= filter_pb)])),
                (f"EV/EBITDA ≤ {filter_ev_ebitda}", len(df[df['EV/EBITDA'].notna() & (df['EV/EBITDA'] <= filter_ev_ebitda)])),
                (f"ROE ≥ {filter_roe}%", len(df[df['ROE (%)'].notna() & (df['ROE (%)'] >= filter_roe)])),
                (f"FCF Yield ≥ {filter_fcf}%", len(df[df['FCF Yield (%)'].notna() & (df['FCF Yield (%)'] >= filter_fcf)])),
                (f"Deuda/Patrimonio ≤ {filter_de}", len(df[df['Deuda/Patrimonio'].notna() & (df['Deuda/Patrimonio'] <= filter_de)])),
                ("**TODOS LOS FILTROS**", len(df_filtered))
            ]
            
            df_filters = pd.DataFrame(filters_breakdown, columns=['Filtro', 'Acciones que pasan'])
            df_filters['% del Total'] = (df_filters['Acciones que pasan'] / len(df) * 100).round(1)
            
            # ✅ SIN background_gradient (no requiere matplotlib)
            st.dataframe(
                df_filters,
                hide_index=True,
                use_container_width=True
            )
        
        # ====================================================================
        # EXPORTAR
        # ====================================================================
        
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar Resultados (CSV)",
                data=csv,
                file_name=f"value_stocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # ====================================================================
        # RECOMENDACIONES
        # ====================================================================
        
        st.markdown("---")
        st.subheader("💡 Recomendaciones")
        
        if not df_filtered.empty:
            st.markdown("""
            ### ✅ Próximos pasos:
            1. **Investiga cada empresa** a fondo
            2. **Revisa estados financieros** completos
            3. **Evalúa ventaja competitiva** (moat)
            4. **Calcula margen de seguridad**
            
            ### ⚠️ Advertencia:
            - Datos pueden tener retraso
            - **NO es asesoramiento financiero**
            """)
        else:
            st.markdown("""
            ### 🔍 No se encontraron oportunidades
            
            **Consejo Value:** La paciencia es clave. Mejor no invertir que invertir 
            en empresas que no cumplen tus criterios.
            """)

else:
    st.markdown("---")
    st.info("👈 **Presiona 'ANALIZAR ACCIONES VALUE'** para comenzar.")
    
    st.markdown("""
    ### 📚 Criterios Value Investing
    
    | Ratio | Tu Criterio | Por qué |
    |-------|-------------|---------|
    | **PER** | ≤ 15 | Pagas poco por ganancias |
    | **P/B** | ≤ 1.5 | Cotiza cerca de valor contable |
    | **EV/EBITDA** | ≤ 10 | Valoración atractiva |
    | **ROE** | ≥ 10% | Buena rentabilidad |
    | **FCF Yield** | ≥ 5% | Genera caja libre |
    | **Deuda/Patrimonio** | ≤ 1 | Bajo apalancamiento |
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("""
⚠️ **Descargo:** Herramienta educativa. Datos de Yahoo Finance pueden tener errores. 
**NO es asesoramiento financiero.**

📅 Actualizado: """ + datetime.now().strftime("%Y-%m-%d %H:%M"))
