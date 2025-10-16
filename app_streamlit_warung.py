
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Dashboard Warung", layout="wide")
st.title("Dashboard Warung - Digitalisasi Sederhana")
st.markdown("Aplikasi sederhana untuk memonitor penjualan, stok, dan laporan keuangan warung. Upload CSV atau gunakan data contoh.")

uploaded = st.file_uploader("Upload CSV - columns: date, product, qty_sold, price, cost", type=["csv"])
use_sample = st.button("Gunakan Data Contoh")

if uploaded is not None:
    df = pd.read_csv(uploaded)
else:
    sample_path = "warung_sample_data.csv"
    df = pd.read_csv(sample_path)

required_cols = {"date","product","qty_sold","price","cost"}
if not required_cols.issubset(set(df.columns)):
    st.error(f"File tidak sesuai. Pastikan kolom: {required_cols}")
    st.stop()

df['date'] = pd.to_datetime(df['date'])

st.sidebar.header("Filter")
min_date = df['date'].min().date()
max_date = df['date'].max().date()
date_range = st.sidebar.date_input("Pilih rentang tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
selected_products = st.sidebar.multiselect("Pilih produk", options=df['product'].unique(), default=list(df['product'].unique()))

start_date, end_date = date_range
mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date) & (df['product'].isin(selected_products))
df_filtered = df.loc[mask].copy()

total_revenue = (df_filtered['qty_sold'] * df_filtered['price']).sum()
total_cost = (df_filtered['qty_sold'] * df_filtered['cost']).sum()
total_profit = total_revenue - total_cost
total_items_sold = df_filtered['qty_sold'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"Rp {int(total_revenue):,}".replace(',', '.'))
col2.metric("Total Profit", f"Rp {int(total_profit):,}".replace(',', '.'))
col3.metric("Total Items Sold", int(total_items_sold))
col4.metric("Unique Products", df_filtered['product'].nunique())

st.markdown("---")
st.subheader("Ringkasan Penjualan per Produk")
summary = df_filtered.groupby('product').apply(lambda g: pd.Series({
    'qty_sold': g['qty_sold'].sum(),
    'revenue': (g['qty_sold'] * g['price']).sum(),
    'cost': (g['qty_sold'] * g['cost']).sum(),
    'profit': (g['qty_sold'] * (g['price'] - g['cost'])).sum()
})).reset_index()
st.dataframe(summary.sort_values(by='qty_sold', ascending=False))

st.subheader("Trend Penjualan Harian (Total Revenue)")
daily = df_filtered.groupby(df_filtered['date'].dt.date).apply(lambda g: (g['qty_sold'] * g['price']).sum()).reset_index(name='revenue')
fig, ax = plt.subplots()
ax.plot(daily['date'], daily['revenue'])
ax.set_xlabel("Date")
ax.set_ylabel("Revenue")
ax.set_title("Revenue per Hari")
plt.xticks(rotation=45)
st.pyplot(fig)

st.subheader("Top Produk - Berdasarkan Quantity Terjual")
top = df_filtered.groupby('product')['qty_sold'].sum().sort_values(ascending=False).reset_index()
fig2, ax2 = plt.subplots()
ax2.bar(top['product'], top['qty_sold'])
ax2.set_xticklabels(top['product'], rotation=45, ha='right')
ax2.set_ylabel("Qty Sold")
st.pyplot(fig2)

st.markdown("---")
st.subheader("Manajemen Stok (Estimasi)")
st.markdown("Masukkan stok awal per produk di tabel berikut, lalu lihat sisa stok setelah periode terfilter.")
products = df['product'].unique().tolist()
stock_init = {}
cols = st.columns(3)
for i, p in enumerate(products):
    stock_init[p] = cols[i%3].number_input(f"Stok awal - {p}", min_value=0, value=20, key=f"stock_{i}")

sold_per_product = df_filtered.groupby('product')['qty_sold'].sum().to_dict()
stock_rows = []
for p in products:
    sold = sold_per_product.get(p, 0)
    initial = stock_init.get(p, 0)
    remaining = initial - sold
    stock_rows.append({"product": p, "stok_awal": initial, "terjual": int(sold), "sisa_stok": int(remaining)})

st.table(pd.DataFrame(stock_rows))

st.markdown("---")
st.subheader("Export Laporan")
from io import BytesIO
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_filtered.to_excel(writer, sheet_name="raw_data", index=False)
    summary.to_excel(writer, sheet_name="summary", index=False)
    pd.DataFrame(stock_rows).to_excel(writer, sheet_name="stock", index=False)
    writer.close()
buffer.seek(0)
st.download_button("Download Laporan Excel", data=buffer, file_name=f"laporan_warung.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.info("Aplikasi ini untuk pencatatan sederhana. Untuk kebutuhan lebih besar pertimbangkan sistem POS.")
