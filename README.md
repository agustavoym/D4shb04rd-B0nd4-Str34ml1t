# Dashboard BONDA en Streamlit

Aplicación pública para explorar el catálogo de beneficios de BONDA desde el Excel incluido en este repositorio.

## Contenido
- `app.py`: aplicación principal.
- `BONDA- DATOS.xlsx`: fuente de datos.
- `requirements.txt`: dependencias para Streamlit Community Cloud.
- `.streamlit/config.toml`: tema visual.

## Ejecutar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar
1. Cree un repositorio nuevo en GitHub.
2. Suba todos los archivos y conserve la carpeta `.streamlit`.
3. En Streamlit Community Cloud, seleccione el repositorio, la rama principal y `app.py`.
4. Pulse **Deploy**.

## Nota de métricas
El archivo incluye beneficios, marcas, categorías, descuentos y ubicaciones. No incluye clientes inscritos ni transacciones de uso. Por eso el dashboard mide oferta del catálogo y no comportamiento de clientes.
