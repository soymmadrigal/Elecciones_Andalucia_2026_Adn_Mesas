from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).parent / "data" / "mesas_adn_electoral.parquet"

TYPE_INFO = {
    "Mesa isla": ("#ff4e6d", "Muy distinta al entorno municipal. Señala un microclima electoral propio."),
    "Mesa inversora": ("#b47cff", "Se inclina hacia el bloque contrario al patrón general de su municipio."),
    "Mesa frontera": ("#ffd166", "Mesa competida: pequeños cambios podrían alterar el bloque dominante."),
    "Mesa amplificador": ("#28a7ff", "Exagera la tendencia dominante del municipio."),
    "Mesa liquida": ("#45d39e", "Alta fragmentación y competencia abierta."),
    "Mesa ancla": ("#8f9aa3", "Se parece mucho al promedio de su municipio."),
    "Mesa mixta": ("#d7d2c8", "Combina señales moderadas de varios tipos."),
}

PARTIDOS = [
    "PP", "PSOE-A", "VOX", "PorA", "ADELANTE ANDALUCÍA", "SALF", "PACMA",
    "MUNDO+JUSTO", "ESCAÑOS EN BLANCO", "FE de las JONS", "ALM", "NA",
    "PCPA", "PARTIDO AUTÓNOMOS", "ANDALUCISTAS - PA", "IZAR",
    "ANDALUCISTAS-PA", "100x100", "ANDALUSÍ", "PCTE", "JUFUDI", "HE>",
    "JM+", "CONECTA", "SOCIEDAD UNIDA", "29", "PODER ANDALUZ", "IPAL",
]


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError("No se encuentra el Parquet de datos.")
    return pd.read_parquet(DATA_PATH)


@st.cache_data(show_spinner=False)
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def fmt_int(value: float) -> str:
    return f"{int(value):,}".replace(",", ".")


def pct(value: float) -> str:
    return f"{value * 100:.1f}%".replace(".", ",")


def main() -> None:
    st.set_page_config(
        page_title="Dashboard ADN Electoral",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    df = load_data()
    party_cols = [p for p in PARTIDOS if p in df.columns]

    st.title("Dashboard ADN Electoral")
    st.caption(
        "Cada mesa se compara con el patrón de su propio municipio. "
        "El objetivo es detectar microclimas electorales, no solo ganadores."
    )
    st.info(
        "Bloque derecha: PP, VOX, SALF, FE de las JONS, NA y Partido Autónomos. "
        "Bloque izquierda: PSOE-A, PorA, ADELANTE ANDALUCÍA y PCPA."
    )

    with st.sidebar:
        st.header("Filtros")
        provincias = ["Todas"] + sorted(df["Provincia"].dropna().unique().tolist())
        provincia = st.selectbox("Provincia", provincias)
        municipios_df = df if provincia == "Todas" else df[df["Provincia"].eq(provincia)]
        municipio_text = st.text_input("Municipio contiene", "")
        tipos = ["Todos"] + [t for t in TYPE_INFO if t in df["Tipo_ADN"].unique()]
        tipo = st.selectbox("Tipo ADN", tipos)
        partido = st.selectbox("Partido", ["Todos"] + party_cols)
        min_votos_partido = st.number_input("Votos mínimos del partido", min_value=1, value=1, step=1)
        ordenar = st.selectbox(
            "Ordenar mesas destacadas",
            ["Rareza_ADN", "Votos Totales", "Margen_ganador", "Fragmentacion_ENP"],
            format_func={
                "Rareza_ADN": "Rareza ADN",
                "Votos Totales": "Votos",
                "Margen_ganador": "Margen ganador",
                "Fragmentacion_ENP": "Fragmentación",
            }.get,
        )

        st.header("Tipos")
        for name, (color, desc) in TYPE_INFO.items():
            st.markdown(
                f"<div style='border-left: 10px solid {color}; padding: 0 0 10px 10px;'>"
                f"<b>{name}</b><br><span style='color:#aaa'>{desc}</span></div>",
                unsafe_allow_html=True,
            )

    filtered = municipios_df.copy()
    if municipio_text.strip():
        filtered = filtered[
            filtered["Municipio"].str.contains(municipio_text.strip(), case=False, na=False, regex=False)
        ]
    if tipo != "Todos":
        filtered = filtered[filtered["Tipo_ADN"].eq(tipo)]
    if partido != "Todos":
        filtered = filtered[filtered[partido].ge(min_votos_partido)]

    votos = filtered["Votos Totales"].sum()
    censo = filtered["Censo Total"].sum()
    participacion = votos / censo if censo else 0
    derecha = filtered["Bloque_derecha"].sum()
    izquierda = filtered["Bloque_izquierda"].sum()
    total_bloques = max(derecha + izquierda, 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Mesas", fmt_int(len(filtered)))
    c2.metric("Votos contemplados", fmt_int(votos))
    c3.metric("Municipios", fmt_int(filtered[["Provincia", "Municipio"]].drop_duplicates().shape[0]))
    c4.metric("Participación", pct(participacion))
    c5.metric("Rareza media", f"{filtered['Rareza_ADN'].mean():.1f}".replace(".", ",") if len(filtered) else "0")

    if partido != "Todos":
        st.success(
            f"Filtro por partido activo: {partido}. "
            f"Mesas con al menos {fmt_int(min_votos_partido)} votos para ese partido. "
            f"Votos de {partido} en la selección: {fmt_int(filtered[partido].sum())}."
        )

    with st.expander("Cómo leer rareza, margen y fragmentación", expanded=False):
        st.markdown(
            "- **Rareza ADN:** cuánto se aparta una mesa del patrón de su propio municipio. Alto significa microclima electoral distinto.\n"
            "- **Margen del ganador:** diferencia entre el primer y segundo partido. Bajo significa mesa más competida.\n"
            "- **Fragmentación:** número efectivo de partidos con voto relevante. Alto significa voto más repartido.\n"
            "- **Brecha derecha-izquierda:** derecha menos izquierda. Negativo pesa más hacia izquierda; positivo pesa más hacia derecha."
        )

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Votos por tipo de mesa")
        by_type = (
            filtered.groupby("Tipo_ADN", as_index=False)
            .agg(mesas=("Mesa", "count"), votos=("Votos Totales", "sum"), rareza=("Rareza_ADN", "mean"))
            .sort_values("votos", ascending=False)
        )
        st.bar_chart(by_type.set_index("Tipo_ADN")["votos"], color="#ffd166")
        st.dataframe(by_type, hide_index=True, use_container_width=True)
        st.download_button(
            "Descargar resumen por tipo CSV",
            to_csv_bytes(by_type),
            "resumen_tipos_adn.csv",
            "text/csv",
        )

    with right:
        st.subheader("Bloques en la selección")
        st.write(f"Derecha: **{fmt_int(derecha)}** votos ({pct(derecha / total_bloques)})")
        st.write(f"Izquierda: **{fmt_int(izquierda)}** votos ({pct(izquierda / total_bloques)})")
        block_df = pd.DataFrame({"bloque": ["Derecha", "Izquierda"], "votos": [derecha, izquierda]}).set_index("bloque")
        st.bar_chart(block_df, color=["#28a7ff"])

        if partido != "Todos":
            st.info(
                f"Filtro activo: mesas con al menos {fmt_int(min_votos_partido)} votos para {partido}. "
                f"Votos de {partido} en la selección: {fmt_int(filtered[partido].sum())}."
            )

    st.subheader("Mapa conceptual ADN")
    st.caption(
        "No es un mapa geográfico. Cada punto es una mesa: a la izquierda predomina el bloque de izquierdas, "
        "a la derecha el bloque de derechas, y cuanto más alto aparece más distinta es frente a su propio municipio."
    )
    chart_df = filtered[["Brecha_bloques", "Rareza_ADN", "Tipo_ADN", "Votos Totales"]].rename(
        columns={
            "Brecha_bloques": "Brecha derecha-izquierda",
            "Rareza_ADN": "Rareza ADN",
            "Tipo_ADN": "Tipo",
            "Votos Totales": "Votos",
        }
    )
    st.scatter_chart(
        chart_df,
        x="Brecha derecha-izquierda",
        y="Rareza ADN",
        color="Tipo",
        size="Votos",
        use_container_width=True,
    )

    st.subheader("Mesas destacadas")
    table_cols = [
        "Provincia", "Municipio", "Mesa", "Tipo_ADN", "Votos Totales", "Ganador",
        "Bloque_ganador", "Participacion", "Rareza_ADN", "Fragmentacion_ENP",
        "Margen_ganador", "Brecha_bloques",
    ]
    if partido != "Todos":
        table_cols.insert(5, partido)
    table = filtered.sort_values(ordenar, ascending=False)[table_cols].head(100).copy()
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button(
        "Descargar mesas filtradas CSV",
        to_csv_bytes(filtered.sort_values(ordenar, ascending=False)[table_cols]),
        "mesas_filtradas_adn.csv",
        "text/csv",
    )

    with st.expander("Notas metodológicas y seguridad"):
        st.markdown(
            "- La app no acepta subida de archivos ni ejecuta código introducido por usuarios.\n"
            "- Los filtros se aplican sobre un Parquet local incluido en el repositorio.\n"
            "- Las búsquedas de municipio usan coincidencia literal sin expresiones regulares.\n"
            "- La clasificación ADN compara cada mesa con su propio municipio."
        )


if __name__ == "__main__":
    main()
