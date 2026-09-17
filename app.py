from pathlib import Path
import re
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Análisis de BONDA", page_icon="🎁", layout="wide")

ORANGE = "#A65300"
NAVY = "#17324D"
TEAL = "#2A9D8F"
PALETTE = ["#A65300", "#E76F51", "#F4A261", "#E9C46A", "#2A9D8F", "#457B9D", "#6D597A", "#355070", "#84A59D", "#BC6C25", "#7F5539"]

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px;}
[data-testid="stAppViewContainer"] {background: #F7F5F2;}
.hero {padding: 18px 24px; border-radius: 20px; background: linear-gradient(120deg,#fff 0%,#fff8ef 100%); border:1px solid #eadfce; margin-bottom: 14px;}
.hero h1 {color:#8C4500; margin:0; font-size:2.1rem;}
.hero p {color:#5C6470; margin:.35rem 0 0 0;}
.kpi {background:white;border:1px solid #E7DED3;border-radius:20px;padding:18px 20px;min-height:130px;box-shadow:0 5px 18px rgba(36,28,20,.05);}
.kpi-label {font-size:.95rem;color:#667085;font-weight:700;margin-bottom:8px;}
.kpi-value {font-size:2.35rem;color:#151515;font-weight:800;line-height:1;}
.kpi-note {font-size:.78rem;color:#8A8F98;margin-top:9px;}
.section-title {font-size:1.15rem;font-weight:800;color:#202124;margin:.25rem 0 .6rem 0;}
div[data-testid="stPlotlyChart"] {background:white;border:1px solid #E7DED3;border-radius:20px;padding:8px 10px;box-shadow:0 5px 18px rgba(36,28,20,.04);}
</style>
""", unsafe_allow_html=True)


def fix_text(value):
    if not isinstance(value, str):
        return value
    for _ in range(2):
        try:
            repaired = value.encode("latin1").decode("utf8")
            if repaired == value:
                break
            value = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
    return value.strip()


def normalize_columns(df):
    mapping = {}
    for col in df.columns:
        clean = fix_text(str(col))
        clean = clean.replace("Categoría", "Categoria").replace("Subcategoría", "Subcategoria")
        mapping[col] = clean
    return df.rename(columns=mapping)

@st.cache_data(show_spinner=False)
def load_data():
    path = Path(__file__).parent / "BONDA- DATOS.xlsx"
    data = pd.read_excel(path, engine="openpyxl")
    data = normalize_columns(data)
    for col in ["Marca", "Categoria", "Subcategoria", "Disponible en", "Descuento"]:
        if col in data.columns:
            data[col] = data[col].map(fix_text)
    data["ID"] = pd.to_numeric(data["ID"], errors="coerce").astype("Int64")
    data["Canal"] = data["Disponible en"].fillna("Sin información").apply(
        lambda x: "Online" if str(x).strip().lower() == "online" else "Presencial"
    )
    def geo(x):
        x = str(x)
        if x.strip().lower() == "online": return "Online"
        parts = [p.strip() for p in x.split("-")]
        return parts[1] if len(parts) > 1 else parts[0]
    data["Zona"] = data["Disponible en"].fillna("Sin información").map(geo)
    def discount_num(x):
        if pd.isna(x): return None
        if isinstance(x, (int, float)): return float(x) if float(x) <= 1 else float(x)/100
        s = str(x).strip().lower().replace(",", ".")
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
        if match: return float(match.group(1))/100
        try:
            n = float(s)
            return n if n <= 1 else n/100
        except ValueError: return None
    data["Descuento_num"] = data["Descuento"].map(discount_num)
    return data

df = load_data()

st.markdown('<div class="hero"><h1>Análisis de BONDA</h1><p>Catálogo interactivo de beneficios, marcas, categorías, descuentos y cobertura.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Filtros")
    categories = sorted(df["Categoria"].dropna().unique())
    selected_categories = st.multiselect("Categorías", categories, default=categories)
    channels = sorted(df["Canal"].dropna().unique())
    selected_channels = st.multiselect("Canal", channels, default=channels)
    zones = sorted(df["Zona"].dropna().unique())
    selected_zones = st.multiselect("Zona / departamento", zones, default=zones)
    brands = sorted(df["Marca"].dropna().unique())
    selected_brands = st.multiselect("Marcas", brands)
    search = st.text_input("Buscar marca", placeholder="Ejemplo: KFC")
    st.caption("Los indicadores y gráficos cambian con los filtros.")

filtered = df[
    df["Categoria"].isin(selected_categories)
    & df["Canal"].isin(selected_channels)
    & df["Zona"].isin(selected_zones)
].copy()
if selected_brands:
    filtered = filtered[filtered["Marca"].isin(selected_brands)]
if search:
    filtered = filtered[filtered["Marca"].str.contains(search, case=False, na=False)]

unique_offers = filtered.drop_duplicates(subset=["ID"])
unique_brand_cat = filtered.drop_duplicates(subset=["Marca", "Categoria"])
with_discount = unique_offers["Descuento_num"].notna().sum()

k1, k2, k3, k4 = st.columns(4)
def kpi(col, label, value, note):
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)
kpi(k1, "Beneficios únicos", f"{unique_offers['ID'].nunique():,}", "Identificados por ID")
kpi(k2, "Categorías", f"{filtered['Categoria'].nunique():,}", "Segmentos disponibles")
kpi(k3, "Marcas", f"{filtered['Marca'].nunique():,}", "Empresas o aliados")
kpi(k4, "Beneficios con %", f"{with_discount:,}", "Excluye PROMO y 2x1 sin porcentaje")

if filtered.empty:
    st.warning("No hay registros para la combinación de filtros seleccionada.")
    st.stop()

cat = unique_brand_cat.groupby("Categoria", as_index=False).agg(Marcas=("Marca", "nunique")).sort_values("Marcas", ascending=True)
zone = filtered.drop_duplicates(["ID","Zona"]).groupby("Zona", as_index=False).agg(Beneficios=("ID","nunique")).sort_values("Beneficios", ascending=False).head(12)

a, b = st.columns([1, 1.15])
with a:
    st.markdown('<div class="section-title">Tipo de categorías</div>', unsafe_allow_html=True)
    fig = px.bar(cat, x="Marcas", y="Categoria", orientation="h", color="Categoria", color_discrete_sequence=PALETTE, text="Marcas")
    fig.update_layout(showlegend=False, height=430, margin=dict(l=10,r=20,t=10,b=10), xaxis_title="Cantidad de marcas", yaxis_title="")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)
with b:
    st.markdown('<div class="section-title">Zona geográfica de beneficios</div>', unsafe_allow_html=True)
    fig = px.bar(zone.sort_values("Beneficios"), x="Beneficios", y="Zona", orientation="h", color="Beneficios", color_continuous_scale=["#F6D6B8", ORANGE], text="Beneficios")
    fig.update_layout(coloraxis_showscale=False, height=430, margin=dict(l=10,r=20,t=10,b=10), xaxis_title="Beneficios únicos", yaxis_title="")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

numeric = filtered[filtered["Descuento_num"].notna()].copy()
pred = numeric.groupby("Categoria", as_index=False).agg(Descuento_promedio=("Descuento_num","mean"), Descuento_maximo=("Descuento_num","max"), Beneficios=("ID","nunique")).sort_values("Descuento_promedio")
brand = filtered.groupby("Marca", as_index=False).agg(Beneficios=("ID","nunique"), Ubicaciones=("Disponible en","nunique")).sort_values(["Beneficios","Ubicaciones"], ascending=False).head(10)

c, d = st.columns(2)
with c:
    st.markdown('<div class="section-title">Descuento predominante por categorías</div>', unsafe_allow_html=True)
    fig = px.bar(pred, x="Descuento_promedio", y="Categoria", orientation="h", text=pred["Descuento_promedio"].map(lambda x:f"{x:.0%}"), color="Descuento_promedio", color_continuous_scale=["#F6D6B8", ORANGE])
    fig.update_layout(coloraxis_showscale=False, height=430, margin=dict(l=10,r=20,t=10,b=10), xaxis_tickformat=".0%", xaxis_title="Descuento promedio", yaxis_title="")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)
with d:
    st.markdown('<div class="section-title">Top 10 de marcas con más beneficios</div>', unsafe_allow_html=True)
    fig = px.bar(brand.sort_values("Beneficios"), x="Beneficios", y="Marca", orientation="h", text="Beneficios", color_discrete_sequence=[TEAL])
    fig.update_layout(height=430, margin=dict(l=10,r=20,t=10,b=10), xaxis_title="Beneficios únicos", yaxis_title="")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

channel = filtered.drop_duplicates(["ID","Canal"]).groupby("Canal", as_index=False).agg(Beneficios=("ID","nunique"))
subcat = filtered.drop_duplicates(["ID","Subcategoria"]).groupby("Subcategoria", as_index=False).agg(Beneficios=("ID","nunique")).sort_values("Beneficios", ascending=False).head(12)

e, f = st.columns([.8, 1.2])
with e:
    st.markdown('<div class="section-title">Disponibilidad por canal</div>', unsafe_allow_html=True)
    fig = px.pie(channel, values="Beneficios", names="Canal", hole=.58, color_discrete_sequence=[ORANGE, TEAL])
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with f:
    st.markdown('<div class="section-title">Subcategorías con mayor oferta</div>', unsafe_allow_html=True)
    fig = px.bar(subcat.sort_values("Beneficios"), x="Beneficios", y="Subcategoria", orientation="h", text="Beneficios", color="Beneficios", color_continuous_scale=["#F3C7A2", NAVY])
    fig.update_layout(coloraxis_showscale=False, height=400, margin=dict(l=10,r=20,t=10,b=10), xaxis_title="Beneficios únicos", yaxis_title="")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">Detalle del catálogo</div>', unsafe_allow_html=True)
detail = filtered[["ID","Marca","Descuento","Categoria","Subcategoria","Disponible en"]].drop_duplicates().sort_values(["Categoria","Marca"])
st.dataframe(detail, use_container_width=True, hide_index=True, height=420)
st.download_button("Descargar vista filtrada", detail.to_csv(index=False).encode("utf-8-sig"), "bonda_filtrado.csv", "text/csv")
st.caption("Fuente: archivo BONDA- DATOS.xlsx incluido en el repositorio. La base contiene catálogo de beneficios, no datos de uso por clientes.")
