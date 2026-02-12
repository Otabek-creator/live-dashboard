import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random
import json

st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide"
)


@st.cache_data(ttl=300)
def load_data():
    """Google Sheets yoki Demo ma'lumot yuklash"""

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        # Secrets dan JSON o‘qish
        creds_dict = json.loads(st.secrets["GOOGLE_CREDS_JSON"])

        # Credentials yaratish
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )

        # gspread client
        client = gspread.authorize(credentials)

        # Sheet ochish (NOMI bilan)
        sheet = client.open("Streamlid").sheet1

        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        st.sidebar.success("✅ Google Sheets dan yuklandi!")
        return df

    except Exception as e:
        st.sidebar.warning("⚠️ Google Sheets ishlamadi")
        st.sidebar.error(str(e))
        st.sidebar.info("📊 Demo ma'lumot bilan ishlayapman")
        return create_demo_data()


def create_demo_data():
    """Demo ma'lumot yaratish"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')

    df = pd.DataFrame({
        'date': dates,
        'sales': [50000 + (i * 100) + random.randint(-5000, 10000) for i in range(len(dates))],
        'customers': [100 + random.randint(-20, 50) for _ in range(len(dates))],
        'product': [random.choice(['Product A', 'Product B', 'Product C', 'Product D']) for _ in range(len(dates))],
        'region': [random.choice(['Tashkent', 'Samarkand', 'Bukhara', 'Fergana']) for _ in range(len(dates))]
    })

    return df


# ============================================
# MAIN DASHBOARD
# ============================================
def main():
    st.title("📊 SALES ANALYTICS DASHBOARD")
    st.markdown("---")

    # Load data
    with st.spinner("Ma'lumotlar yuklanmoqda..."):
        df = load_data()

        df['sales'] = pd.to_numeric(df['sales'], errors='coerce')
        df['customers'] = pd.to_numeric(df['customers'], errors='coerce')

    # Convert date
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)

    # ============================================
    # SIDEBAR
    # ============================================
    st.sidebar.header("🔍 Filtrlar")

    # Date filter
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    date_range = st.sidebar.date_input(
        "Sana oralig'i",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        df = df[(df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])]

    # Region filter
    regions = ['Barchasi'] + sorted(df['region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Mintaqa", regions)

    if selected_region != 'Barchasi':
        df = df[df['region'] == selected_region]

    # ============================================
    # KPI METRICS
    # ============================================
    st.subheader("📈 Asosiy ko'rsatkichlar")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_sales = df['sales'].sum()
        st.metric("Jami sotuv", f"${total_sales:,.0f}", delta="+12.5%")

    with col2:
        avg_sales = df['sales'].mean()
        st.metric("O'rtacha sotuv", f"${avg_sales:,.0f}", delta="+5.2%")

    with col3:
        total_customers = df['customers'].sum()
        st.metric("Mijozlar", f"{total_customers:,}", delta="+8.1%")

    with col4:
        avg_order = total_sales / total_customers if total_customers > 0 else 0
        st.metric("O'rtacha chek", f"${avg_order:,.0f}", delta="+3.7%")

    st.markdown("---")

    # ============================================
    # CHARTS
    # ============================================
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Sotuv dinamikasi")
        daily_sales = df.groupby('date')['sales'].sum().reset_index()

        fig = px.line(
            daily_sales,
            x='date',
            y='sales',
            title='Kunlik sotuv',
            labels={'sales': 'Sotuv ($)', 'date': 'Sana'}
        )
        fig.update_traces(line_color='#667eea', line_width=3)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏪 Mahsulot bo'yicha")
        product_sales = df.groupby('product')['sales'].sum().reset_index()

        fig = px.pie(
            product_sales,
            values='sales',
            names='product',
            title='Mahsulot ulushi',
            hole=0.4
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Row 2
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌍 Mintaqa bo'yicha")
        region_sales = df.groupby('region')['sales'].sum().sort_values(ascending=True).reset_index()

        fig = px.bar(
            region_sales,
            x='sales',
            y='region',
            orientation='h',
            title='Mintaqalar bo\'yicha sotuv',
            color='sales',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Oylik trend")
        monthly_sales = df.groupby('month')['sales'].sum().reset_index()

        fig = px.area(
            monthly_sales,
            x='month',
            y='sales',
            title='Oylik sotuv trendi'
        )
        fig.update_traces(fill='tonexty', fillcolor='rgba(102, 126, 234, 0.3)')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # ============================================
    # DATA TABLE
    # ============================================
    st.markdown("---")
    st.subheader("📋 Ma'lumotlar jadvali")

    top_n = st.slider("Ko'rsatiladigan qatorlar", 5, 50, 10)
    st.dataframe(df.head(top_n), use_container_width=True)

    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 CSV yuklash",
        csv,
        f"sales_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )

    # ============================================
    # INSTRUCTIONS
    # ============================================
    with st.expander("📖 Google Sheets bilan bog'lash"):
        st.markdown("""
        ### Google Sheets sozlash:

        1. **Credentials olish:**
           - Google Cloud Console ga kiring
           - Service Account yarating
           - JSON key yuklab oling
           - `credentials.json` ga saqlang

        2. **Sheet ulash:**
           - Google Sheets yarating
           - Service Account emailini Share qiling
           - URL ni kodga qo'ying

        3. **Kod o'zgartirish:**
           ```python
           SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
           ```

        Batafsil: `GOOGLE_SHEETS_SETUP.md` faylini o'qing
        """)


if __name__ == "__main__":
    main()