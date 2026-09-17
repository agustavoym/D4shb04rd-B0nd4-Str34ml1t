from pathlib import Path
import re
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard de de Bonda", page_icon="📊", layout="wide")
RED,DARK,LIGHT,BLUE="#EB0A1E","#4A4A4A","#E9EAE8","#82CEE6"
COLORS=[BLUE,DARK,"#A7DDEA","#6D6D6D","#CBEAF2","#878787","#B8E1EC","#5A5A5A","#D9F0F6","#9B9B9B",RED]
st.markdown(f"""<style>
.block-container{{padding-top:1.4rem;max-width:1500px}} [data-testid='stAppViewContainer']{{background:#F5F6F6}}
.hero{{padding:18px 24px;border-radius:20px;background:linear-gradient(120deg,#fff,#EAF7FB);border:1px solid #D9E1E4;margin-bottom:14px}}
.hero h1{{color:{DARK};margin:0;font-size:2.1rem}} .hero p{{color:{DARK};margin:.35rem 0 0}}
.kpi{{background:#fff;border:1px solid #D9E1E4;border-radius:20px;padding:18px 20px;min-height:130px;box-shadow:0 5px 18px #0000000d}}
.kpi-label{{font-size:.95rem;color:#667085;font-weight:700;margin-bottom:8px}} .kpi-value{{font-size:2.35rem;color:{DARK};font-weight:800;line-height:1}}
.kpi-note{{font-size:.78rem;color:#8A8F98;margin-top:9px}} .section-title{{font-size:1.15rem;font-weight:800;color:{DARK};margin:.25rem 0 .6rem}}
div[data-testid='stPlotlyChart']{{background:#fff;border:1px solid #D9E1E4;border-radius:20px;padding:8px 10px;box-shadow:0 5px 18px #0000000a}}
</style>""",unsafe_allow_html=True)

def fix(x):
    if not isinstance(x,str): return x
    for _ in range(2):
        try: x=x.encode('latin1').decode('utf8')
        except: break
    return x.strip()
@st.cache_data(show_spinner=False)
def load():
    d=pd.read_excel(Path(__file__).parent/'BONDA- DATOS.xlsx',engine='openpyxl')
    d.columns=[fix(str(c)).replace('Categoría','Categoria').replace('Subcategoría','Subcategoria') for c in d.columns]
    for c in ['Marca','Categoria','Subcategoria','Disponible en','Descuento']: d[c]=d[c].map(fix)
    d['ID']=pd.to_numeric(d['ID'],errors='coerce').astype('Int64')
    d['Canal']=d['Disponible en'].fillna('Sin información').map(lambda x:'Online' if str(x).lower()=='online' else 'Presencial')
    d['Zona']=d['Disponible en'].fillna('Sin información').map(lambda x:'Online' if str(x).lower()=='online' else ([p.strip() for p in str(x).split('-')]+[''])[1] or str(x))
    def pct(x):
        if pd.isna(x): return None
        if isinstance(x,(int,float)): return float(x) if float(x)<=1 else float(x)/100
        m=re.search(r'(\d+(?:[.,]\d+)?)\s*%',str(x));
        if m:return float(m.group(1).replace(',','.'))/100
        try:
            v=float(x);return v if v<=1 else v/100
        except:return None
    d['Descuento_num']=d['Descuento'].map(pct)
    return d
df=load()
st.markdown('<div class="hero"><h1>Dashboard de de Bonda</h1><p>Catálogo interactivo de beneficios, marcas, categorías, descuentos y cobertura.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.header('Filtros')
    cats=sorted(df.Categoria.dropna().unique()); selc=st.multiselect('Categorías',cats,default=cats)
    chans=sorted(df.Canal.unique()); selch=st.multiselect('Canal',chans,default=chans)
    zones=sorted(df.Zona.unique()); selz=st.multiselect('Zona / departamento',zones,default=zones)
    brands=sorted(df.Marca.dropna().unique()); selb=st.multiselect('Marcas',brands)
    q=st.text_input('Buscar marca',placeholder='Ejemplo: KFC')
f=df[df.Categoria.isin(selc)&df.Canal.isin(selch)&df.Zona.isin(selz)].copy()
if selb:f=f[f.Marca.isin(selb)]
if q:f=f[f.Marca.str.contains(q,case=False,na=False)]
u=f.drop_duplicates('ID'); ubc=f.drop_duplicates(['Marca','Categoria'])
def card(col,label,val,note):col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{val:,}</div><div class="kpi-note">{note}</div></div>',unsafe_allow_html=True)
a,b,c,d=st.columns(4);card(a,'Beneficios únicos',u.ID.nunique(),'Identificados por ID');card(b,'Categorías',f.Categoria.nunique(),'Segmentos disponibles');card(c,'Marcas',f.Marca.nunique(),'Empresas o aliados');card(d,'Beneficios con %',u.Descuento_num.notna().sum(),'Excluye promociones sin porcentaje')
if f.empty:st.warning('No hay registros para los filtros seleccionados.');st.stop()
def hbar(data,x,y,color=BLUE,height=420,percent=False):
    fig=px.bar(data,x=x,y=y,orientation='h',text=data[x].map(lambda v:f'{v:.0%}') if percent else x,color_discrete_sequence=[color])
    fig.update_yaxes(categoryorder='total ascending');fig.update_traces(textposition='outside');fig.update_layout(height=height,margin=dict(l=10,r=25,t=10,b=10),showlegend=False,xaxis_title=x.replace('_',' '),yaxis_title='')
    if percent:fig.update_xaxes(tickformat='.0%')
    return fig
cat=ubc.groupby('Categoria',as_index=False).Marca.nunique().rename(columns={'Marca':'Marcas'})
zone=f.drop_duplicates(['ID','Zona']).groupby('Zona',as_index=False).ID.nunique().rename(columns={'ID':'Beneficios'}).nlargest(12,'Beneficios')
x,y=st.columns([1,1.15])
with x:st.markdown('<div class="section-title">Tipo de categorías</div>',unsafe_allow_html=True);st.plotly_chart(hbar(cat,'Marcas','Categoria',BLUE),use_container_width=True)
with y:st.markdown('<div class="section-title">Zona geográfica de beneficios</div>',unsafe_allow_html=True);st.plotly_chart(hbar(zone,'Beneficios','Zona',DARK),use_container_width=True)
num=f[f.Descuento_num.notna()];pred=num.groupby('Categoria',as_index=False).Descuento_num.mean().rename(columns={'Descuento_num':'Descuento promedio'})
brand=f.groupby('Marca',as_index=False).ID.nunique().rename(columns={'ID':'Beneficios'}).nlargest(10,'Beneficios')
x,y=st.columns(2)
with x:st.markdown('<div class="section-title">Descuento predominante por categorías</div>',unsafe_allow_html=True);st.plotly_chart(hbar(pred,'Descuento promedio','Categoria',BLUE,percent=True),use_container_width=True)
with y:st.markdown('<div class="section-title">Top 10 de marcas con más beneficios</div>',unsafe_allow_html=True);st.plotly_chart(hbar(brand,'Beneficios','Marca',DARK),use_container_width=True)
channel=f.drop_duplicates(['ID','Canal']).groupby('Canal',as_index=False).ID.nunique().rename(columns={'ID':'Beneficios'})
sub=f.drop_duplicates(['ID','Subcategoria']).groupby('Subcategoria',as_index=False).ID.nunique().rename(columns={'ID':'Beneficios'}).nlargest(12,'Beneficios')
x,y=st.columns([.65,1.35])
with x:
    st.markdown('<div class="section-title">Disponibilidad por canal</div>',unsafe_allow_html=True)
    fig=px.pie(channel,values='Beneficios',names='Canal',hole=.58,color_discrete_sequence=[BLUE,DARK]);fig.update_traces(textposition='inside',textinfo='percent+label');fig.update_layout(height=300,margin=dict(l=30,r=30,t=5,b=35),legend=dict(orientation='h',y=-.08,x=.5,xanchor='center'))
    st.plotly_chart(fig,use_container_width=True)
with y:st.markdown('<div class="section-title">Subcategorías con mayor oferta</div>',unsafe_allow_html=True);st.plotly_chart(hbar(sub,'Beneficios','Subcategoria',BLUE,360),use_container_width=True)
st.markdown('<div class="section-title">Detalle del catálogo</div>',unsafe_allow_html=True)
detail=f[['ID','Marca','Descuento','Categoria','Subcategoria','Disponible en']].drop_duplicates().sort_values(['Categoria','Marca']);st.dataframe(detail,use_container_width=True,hide_index=True,height=420)
st.download_button('Descargar vista filtrada',detail.to_csv(index=False).encode('utf-8-sig'),'bonda_filtrado.csv','text/csv')
