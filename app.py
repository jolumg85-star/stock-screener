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

# CSS personalizado para mejor visualización
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
    .pass-filter {
        color: green;
        font-weight: bold;
    }
    .fail-filter {
        color: red;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LISTA AMPLIADA DE ACCIONES VALUE (100+ TICKERS)
# ============================================================================
VALUE_TICKERS = [
    # BANCOS Y FINANZAS
    'JPM', 'BAC', 'WFC', 'C', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT',
    'MTB', 'FITB', 'HBAN', 'RF', 'CFG', 'KEY', 'ZION', 'CMA', 'NTRS', 'SCHW',
    
    # ENERGÍA
    'CVX', 'XOM', 'COP', 'EOG', 'SLB', 'OXY', 'MRO', 'DVN', 'HAL', 'BKR',
    'PXD', 'FANG', 'APA', 'HES', 'VLO', 'PSX', 'MPC', 'OKE', 'WMB', 'KMI',
    
    # INDUSTRIALES
    'GE', 'CAT', 'BA', 'HON', 'MMM', 'DE', 'EMR', 'ETN', 'ITW', 'ROK',
    'PH', 'CMI', 'FDX', 'UPS', 'WM', 'RSG', 'NUE', 'STLD', 'X', 'CLF',
    
    # CONSUMO BÁSICO
    'KO', 'PEP', 'WMT', 'TGT', 'COST', 'KR', 'SYY', 'GIS', 'K', 'CPB',
    'CAG', 'SJM', 'HSY', 'MKC', 'CLX', 'CHD', 'EL', 'MDLZ', 'MNST', 'KHC',
    
    # SALUD/FARMA
    'PFE', 'JNJ', 'MRK', 'ABBV', 'BMY', 'GILD', 'CVS', 'UNH', 'CI', 'HUM',
    'MCK', 'CAH', 'ABC', 'ZBH', 'BSX', 'MDT', 'SYK', 'BDX', 'EW', 'HOLX',
    
    # TELECOM/UTILITIES
    'VZ', 'T', 'TMUS', 'D', 'SO', 'DUK', 'NEE', 'AEP', 'EXC', 'XEL',
    'ED', 'EIX', 'WEC', 'ES', 'AWK', 'ATO', 'CMS', 'DTE', 'NI', 'LNT',
    
    # AUTOMOTRIZ Y OTROS
    'F', 'GM', 'STLA', 'HMC', 'TM', 'RACE', 'APTV', 'BWA', 'LEA', 'VC',
    'IBM', 'INTC', 'HPQ', 'CSCO', 'QCOM', 'TXN', 'ADI', 'MCHP', 'KLAC', 'AMAT',
    
    # SEGUROS Y RE
    'BRK.B', 'AIG', 'MET', 'PRU', 'ALL', 'TRV', 'PGR', 'CB', 'AFL', 'HIG',
    'SPG', 'O', 'WELL', 'AVB', 'EQR', 'VTR', 'ARE', 'DLR', 'PSA', 'AMT',
    
    # RETAIL
    'HD', 'LOW', 'DG', 'DLTR', 'ROST', 'TJX', 'BBY', 'GPS', 'M', 'KSS'
]

# ============================================================================
# FUNCIONES DE CÁLCULO DE RATIOS
# ============================================================================

def calculate_financial_ratios(ticker):
    """
    Calcula todos los ratios financieros con múltiples fuentes y fallbacks.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # --- DATOS BÁSICOS ---
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not price or price <= 0:
            return None
            
        market_cap = info.get('marketCap') or 0
        enterprise_value = info.get('enterpriseValue') or market_cap
        
        # --- CÁLCULO DE RATIOS ---
        
        # 1. PER (Price to Earnings)
        pe_ratio = info.get('trailingPE')
        if not pe_ratio or pe_ratio <= 0:
            eps = info.get('trailingEps')
            if eps and eps > 0:
                pe_ratio = price / eps
        
        # 2. P/B (Price to Book)
        pb_ratio = info.get('priceToBook')
        if not pb_ratio or pb_ratio <= 0:
            book_value = info.get('bookValue')
            if book_value and book_value > 0:
                pb_ratio = price / book_value
        
        # 3. EV/EBITDA
        ev_ebitda = info.get('enterpriseToEbitda')
        if not ev_ebitda or ev_ebitda <= 0:
            ebitda = info.get('ebitda')
            if ebitda and ebitda > 0 and enterprise_value > 0:
                ev_ebitda = enterprise_value / ebitda
        
        # 4. ROE (Return on Equity)
        roe = info.get('returnOnEquity')
        if not roe:
            net_income = info.get('netIncomeToCommon')
            equity = info.get('totalStockholderEquity')
            if net_income and equity and equity > 0:
                roe = net_income / equity
        
        # 5. FCF Yield (Free Cash Flow Yield)
        fcf = info.get('freeCashflow')
        operating_cash_flow = info.get('operatingCashflow')
        capex = info.get('capitalExpenditures')
        
        if not fcf and operating_cash_flow and capex:
            fcf = operating_cash_flow + capex  # CapEx viene negativo en Yahoo
        
        fcf_yield = None
        if fcf and market_cap and market_cap > 0:
            fcf_yield = (fcf / market_cap) * 100
        
        # 6. Debt to Equity
        debt_to_equity = info.get('debtToEquity')
        if not debt_to_equity:
            total_debt = info.get('totalDebt')
            equity = info.get('totalStockholderEquity')
            if total_debt and equity and equity > 0:
                debt_to_equity = total_debt / equity
        
        # 7. Caída desde máximo de 52 semanas
        high_52 = info.get('fiftyTwoWeekHigh')
        low_52 = info.get('fiftyTwoWeekLow')
        drop_from_high = None
        if high_52 and high_52 > 0:
            drop_from_high = ((high_52 - price) / high_52) * 100
        
        # 8. Dividend Yield
        dividend_yield = info.get('dividendYield')
        if dividend_yield:
            dividend_yield = dividend_yield * 100
        
        # 9. Payout Ratio
        payout_ratio = info.get('payoutRatio')
        if payout_ratio:
            payout_ratio = payout_ratio * 100
        
        # 10. Current Ratio
        current_ratio = info.get('currentRatio')
        
        # 11. Profit Margin
        profit_margin = info.get('profitMargins')
        if profit_margin:
            profit_margin = profit_margin * 100
        
        # 12. Beta
        beta = info.get('beta')
        
        # Nombre de la empresa
        company_name = info.get('shortName') or info.get('longName') or ticker
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        
        # Contar datos completos
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
            'Payout Ratio (%)': round(payout_ratio, 2) if payout_ratio else None,
            'Current Ratio': round(current_ratio, 2) if current_ratio else None,
            'Profit Margin (%)': round(profit_margin, 2) if profit_margin else None,
            'Beta': round(beta, 2) if beta else None,
            '52 Week Range': f"{low_52:.2f} - {high_52:.2f}" if low_52 and high_52 else "N/A",
            'Datos Completos': complete_data / 6
        }
        
    except Exception as e:
        return None

# ============================================================================
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# ============================================================================

@st.cache_data(ttl=7200)
def analyze_stocks(tickers, show_progress=True):
    """
    Analiza todas las acciones y devuelve DataFrame con resultados.
    """
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
Esta aplicación escanea el mercado buscando **empresas infravaloradas** según los criterios de 
**Benjamin Graham, Warren Buffett y otros inversores value**.
""")

# ============================================================================
# PANEL LATERAL - CONFIGURACIÓN DE FILTROS (CORREGIDO)
# ============================================================================

st.sidebar.header("⚙️ Criterios de Value Investing")
st.sidebar.markdown("---")

st.sidebar.subheader("📊 Ratios Fundamentales")

# ✅ TODOS LOS VALORES SON FLOATS PARA EVITAR ERRORES
filter_per = st.sidebar.slider(
    "PER (P/E) máximo",
    min_value=1.0, max_value=50.0, value=15.0, step=1.0,
    help="Price to Earnings. Menor = más barato. Value: < 15"
)

filter_pb = st.sidebar.slider(
    "P/B (Price to Book) máximo",
    min_value=0.1, max_value=5.0, value=1.5, step=0.1,
    help="Precio sobre Valor en Libros. Value: < 1.5"
)

filter_ev_ebitda = st.sidebar.slider(
    "EV/EBITDA máximo",
    min_value=1.0, max_value=50.0, value=10.0, step=1.0,
    help="Enterprise Value sobre EBITDA. Value: < 10"
)

filter_roe = st.sidebar.slider(
    "ROE mínimo (%)",
    min_value=0.0, max_value=50.0, value=10.0, step=1.0,
    help="Return on Equity. Rentabilidad sobre patrimonio. Value: > 10%"
)

filter_fcf = st.sidebar.slider(
    "FCF Yield mínimo (%)",
    min_value=0.0, max_value=20.0, value=5.0, step=0.5,
    help="Free Cash Flow Yield. Flujo de caja libre sobre precio. Value: > 5%"
)

# ✅ CORREGIDO: min_value=0.0 (float) en lugar de 0 (int)
filter_de = st.sidebar.slider(
    "Deuda/Patrimonio máximo",
    min_value=0.0, max_value=5.0, value=1.0, step=0.1,
    help="Debt to Equity. Apalancamiento. Value: < 1"
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtros Adicionales")

min_market_cap = st.sidebar.number_input(
    "Market Cap mínimo (miles de millones $)",
    min_value=0.0, max_value=1000.0, value=1.0, step=0.5,
    help="Evitar empresas demasiado pequeñas"
)

min_dividend_yield = st.sidebar.number_input(
    "Dividend Yield mínimo (%)",
    min_value=0.0, max_value=15.0, value=0.0, step=0.5,
    help="Solo empresas que paguen dividendos"
)

max_beta = st.sidebar.number_input(
    "Beta máximo (volatilidad)",
    min_value=0.0, max_value=3.0, value=2.0, step=0.1,
    help="Medida de volatilidad vs mercado"
)

st.sidebar.markdown("---")
st.sidebar.subheader("📉 Filtro de Caída")

enable_drop_filter = st.sidebar.checkbox(
    "Filtrar por caída de precio",
    value=False,
    help="Buscar acciones que hayan caído significativamente"
)

if enable_drop_filter:
    min_drop = st.sidebar.slider("Caída mínima desde máximos (%)", 10.0, 80.0, 30.0, step=5.0)
    max_drop = st.sidebar.slider("Caída máxima desde máximos (%)", 10.0, 80.0, 50.0, step=5.0)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Opciones")

relax_mode = st.sidebar.checkbox(
    "🔓 Modo Relajado",
    value=False,
    help="Ignorar FCF Yield si no hay datos suficientes"
)

min_data_completeness = st.sidebar.slider(
    "Datos completos mínimos (%)",
    min_value=30.0, max_value=100.0, value=50.0, step=10.0,
    help="Porcentaje mínimo de ratios disponibles"
)

# ============================================================================
# BOTÓN DE ANÁLISIS
# ============================================================================

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    analyze_button = st.button("🔍 ANALIZAR ACCIONES VALUE", type="primary", use_container_width=True)
with col2:
    clear_cache = st.button("🔄 Limpiar Cache")
with col3:
    export_data = st.button("📥 Exportar", use_container_width=True)

if clear_cache:
    st.cache_data.clear()
    st.success("✅ Cache limpiada. Vuelve a analizar para obtener datos frescos.")

# ============================================================================
# EJECUCIÓN DEL ANÁLISIS
# ============================================================================

if analyze_button:
    with st.spinner('📊 Analizando ' + str(len(VALUE_TICKERS)) + ' acciones... Esto puede tardar 2-3 minutos.'):
        
        df = analyze_stocks(VALUE_TICKERS)
        
        if df.empty:
            st.error("❌ No se pudieron obtener datos. Verifica tu conexión a internet.")
            st.stop()
        
        # ====================================================================
        # APLICACIÓN DE FILTROS
        # ====================================================================
        
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
        
        # Calcular Score Value
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
        # MOSTRAR RESULTADOS
        # ====================================================================
        
        st.markdown("---")
        st.subheader("📊 Resumen del Análisis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Acciones Analizadas", len(df))
        with col2:
            st.metric("Cumplen Criterios Value", len(df_filtered))
        with col3:
            st.metric("Tasa de Éxito", f"{(len(df_filtered)/len(df)*100):.1f}%")
        with col4:
            avg_score = df_filtered['Value Score'].mean() if not df_filtered.empty else 0
            st.metric("Score Value Promedio", f"{avg_score:.1f}")
        
        # ====================================================================
        # TOP 5 MEJORES ACCIONES VALUE
        # ====================================================================
        
        st.markdown("---")
        st.subheader("🏆 TOP 5: Mejores Oportunidades Value")
        
        if not df_filtered.empty:
            top5 = df_filtered.head(5)
            
            for idx, row in top5.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([2, 3, 2])
                    with col1:
                        st.markdown(f"### {row['Ticker']}")
                        st.caption(row['Nombre'])
                        st.markdown(f"**Sector:** {row['Sector']}")
                    with col2:
                        cols = st.columns(3)
                        cols[0].metric("PER", f"{row['PER']:.2f}" if row['PER'] else "N/A")
                        cols[1].metric("P/B", f"{row['P/B']:.2f}" if row['P/B'] else "N/A")
                        cols[2].metric("EV/EBITDA", f"{row['EV/EBITDA']:.2f}" if row['EV/EBITDA'] else "N/A")
                    with col3:
                        cols = st.columns(2)
                        cols[0].metric("ROE", f"{row['ROE (%)']:.1f}%" if row['ROE (%)'] else "N/A")
                        cols[1].metric("FCF Yield", f"{row['FCF Yield (%)']:.1f}%" if row['FCF Yield (%)'] else "N/A")
                    
                    drop_text = f"{row['Caída desde Max 52s (%)']:.1f}%" if row['Caída desde Max 52s (%)'] else "N/A"
                    st.markdown(f"**Value Score:** {row['Value Score']:.1f}/100 | **Precio:** ${row['Precio']:.2f} | **Caída 52s:** {drop_text}")
                    st.divider()
            
            display_cols = [
                'Ticker', 'Nombre', 'Precio', 'PER', 'P/B', 'EV/EBITDA',
                'ROE (%)', 'FCF Yield (%)', 'Deuda/Patrimonio', 'Dividend Yield (%)',
                'Caída desde Max 52s (%)', 'Value Score'
            ]
            st.dataframe(
                top5[display_cols].style.format({
                    'Precio': '${:.2f}', 'PER': '{:.2f}', 'P/B': '{:.2f}',
                    'EV/EBITDA': '{:.2f}', 'ROE (%)': '{:.1f}%', 'FCF Yield (%)': '{:.1f}%',
                    'Deuda/Patrimonio': '{:.2f}', 'Dividend Yield (%)': '{:.1f}%',
                    'Caída desde Max 52s (%)': '{:.1f}%', 'Value Score': '{:.1f}'
                }).background_gradient(subset=['Value Score'], cmap='Greens'),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("""
            ⚠️ **Ninguna acción cumple TODOS los criterios simultáneamente.**
            
            Esto es NORMAL con filtros tan estrictos. Prueba:
            - ✅ Activar **Modo Relajado** en el panel lateral
            - ✅ Aumentar ligeramente PER (18-20) o P/B (2.0)
            - ✅ Reducir FCF Yield mínimo (3-4%)
            """)
        
        # ====================================================================
        # TOP 5 ACCIONES CAÍDAS
        # ====================================================================
        
        st.markdown("---")
        st.subheader("📉 TOP 5: Oportunidades en Caída (30% - 50%)")
        st.caption("Empresas value que han caído significativamente pero mantienen fundamentales sólidos")
        
        if not df_filtered.empty:
            mask_drop = (
                (df_filtered['Caída desde Max 52s (%)'].notna()) &
                (df_filtered['Caída desde Max 52s (%)'] >= 30) &
                (df_filtered['Caída desde Max 52s (%)'] <= 50)
            )
            df_drop = df_filtered[mask_drop].copy()
            df_drop = df_drop.sort_values(by='Caída desde Max 52s (%)', ascending=False)
            
            if not df_drop.empty:
                st.success(f"✅ Se encontraron {len(df_drop)} acciones en caída significativa")
                
                display_cols_drop = [
                    'Ticker', 'Nombre', 'Precio', 'Caída desde Max 52s (%)',
                    'PER', 'P/B', 'ROE (%)', 'FCF Yield (%)', 'Dividend Yield (%)'
                ]
                st.dataframe(
                    df_drop.head(5)[display_cols_drop].style.format({
                        'Precio': '${:.2f}', 'Caída desde Max 52s (%)': '{:.1f}%',
                        'PER': '{:.2f}', 'P/B': '{:.2f}', 'ROE (%)': '{:.1f}%',
                        'FCF Yield (%)': '{:.1f}%', 'Dividend Yield (%)': '{:.1f}%'
                    }).background_gradient(subset=['Caída desde Max 52s (%)'], cmap='Reds'),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("ℹ️ **No hay acciones con caída 30-50% que cumplan los criterios value.**")
        else:
            st.caption("Primero deben aparecer acciones en el Top 1 para filtrar por caída.")
        
        # ====================================================================
        # ANÁLISIS DE FILTROS
        # ====================================================================
        
        st.markdown("---")
        with st.expander("🔍 Análisis de Filtros: ¿Por qué se eliminan acciones?"):
            st.markdown("### 📊 Efecto de cada filtro individualmente")
            
            filters_breakdown = [
                (f"PER ≤ {filter_per}", len(df[df['PER'].notna() & (df['PER'] <= filter_per)])),
                (f"P/B ≤ {filter_pb}", len(df[df['P/B'].notna() & (df['P/B'] <= filter_pb)])),
                (f"EV/EBITDA ≤ {filter_ev_ebitda}", len(df[df['EV/EBITDA'].notna() & (df['EV/EBITDA'] <= filter_ev_ebitda)])),
                (f"ROE ≥ {filter_roe}%", len(df[df['ROE (%)'].notna() & (df['ROE (%)'] >= filter_roe)])),
                (f"FCF Yield ≥ {filter_fcf}%", len(df[df['FCF Yield (%)'].notna() & (df['FCF Yield (%)'] >= filter_fcf)])),
                (f"Deuda/Patrimonio ≤ {filter_de}", len(df[df['Deuda/Patrimonio'].notna() & (df['Deuda/Patrimonio'] <= filter_de)])),
                (f"Market Cap ≥ ${min_market_cap}B", len(df[df['Market Cap (B)'] >= min_market_cap])),
                ("**TODOS LOS FILTROS**", len(df_filtered))
            ]
            
            df_filters = pd.DataFrame(filters_breakdown, columns=['Filtro', 'Acciones que pasan'])
            df_filters['% del Total'] = (df_filters['Acciones que pasan'] / len(df) * 100).round(1)
            
            st.dataframe(
                df_filters.style.background_gradient(subset=['Acciones que pasan'], cmap='YlGn'),
                hide_index=True,
                use_container_width=True
            )
            
            st.bar_chart(df_filters.set_index('Filtro')['Acciones que pasan'])
        
        # ====================================================================
        # EXPORTAR DATOS
        # ====================================================================
        
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar Resultados Completos (CSV)",
                data=csv,
                file_name=f"value_stocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # ====================================================================
        # RECOMENDACIONES
        # ====================================================================
        
        st.markdown("---")
        st.subheader("💡 Recomendaciones de Inversión")
        
        if not df_filtered.empty:
            st.markdown("""
            ### ✅ Acciones encontradas - Próximos pasos:
            1. **Investigación adicional:** Revisa los estados financieros completos.
            2. **Ventaja competitiva:** ¿Tiene la empresa un moat duradero?
            3. **Gestión:** ¿Es el equipo directivo competente?
            4. **Margen de seguridad:** ¿El precio ofrece descuento al valor intrínseco?
            
            ### ⚠️ Advertencias:
            - Los datos pueden tener retraso de 15 minutos
            - **Esto NO es asesoramiento financiero.** Haz tu propia investigación.
            """)
        else:
            st.markdown("""
            ### 🔍 No se encontraron oportunidades con estos criterios
            
            **Consejo Value:** La paciencia es clave. Mejor no invertir que invertir en empresas 
            que no cumplen tus criterios. Espera a mejores oportunidades del mercado.
            """)

else:
    st.markdown("---")
    st.info("👈 **Presiona el botón 'ANALIZAR ACCIONES VALUE'** para comenzar el escaneo.")
    
    st.markdown("""
    ### 📚 Sobre Value Investing
    
    | Principio | Descripción |
    |-----------|-------------|
    | 🎯 **Margen de Seguridad** | Comprar por debajo del valor intrínseco |
    | 📊 **Análisis Fundamental** | Enfocarse en el negocio, no en el precio |
    | 🧠 **Mentalidad de Propietario** | Pensar como dueño del negocio |
    | ⏰ **Paciencia** | El mercado vota a corto, pesa a largo |
    | 🛡️ **Protección de Capital** | Regla #1: No perder dinero |
    
    ### 📋 Tus Criterios Value
    
    | Ratio | Tu Criterio | Importancia |
    |-------|-------------|-------------|
    | **PER** | ≤ 15 | Pagas poco por ganancias |
    | **P/B** | ≤ 1.5 | Cotiza cerca de valor contable |
    | **EV/EBITDA** | ≤ 10 | Valoración empresarial atractiva |
    | **ROE** | ≥ 10% | Buena rentabilidad sobre patrimonio |
    | **FCF Yield** | ≥ 5% | Genera caja libre saludable |
    | **Deuda/Patrimonio** | ≤ 1 | Bajo apalancamiento |
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("""
⚠️ **Descargo:** Esta herramienta es solo para fines educativos. 
Los datos provienen de Yahoo Finance y pueden tener errores o retrasos. 
**Esto NO es asesoramiento financiero.**

📅 Última actualización: """ + datetime.now().strftime("%Y-%m-%d %H:%M"))
