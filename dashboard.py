import streamlit as st
import pandas as pd
import pydeck as pdk
import math

def main():
    st.set_page_config(
        page_title=" Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <h4>Created by <b>Selcuk Oner</b></h4>
            <p style="font-size: small;">
                <a href="https://linkedin.com/in/selcukoner" target="_blank">LinkedIn</a> • 
                <a href="https://github.com/selcukoner" target="_blank">GitHub</a> • 
                <a href="https://www.selcukoner.com" target="_blank">Website</a>
            </p>
            <p style="font-size: small; color: gray;">
            This dashboard utilizes maritime traffic data provided by <b>Kystverket</b>. 
            The dataset displayed is based on records from January 2022.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # custom CSS
    st.markdown(
        """
        <style>

        html, body, [class*="css"]  {
            font-family: 'Roboto', sans-serif;
            color: #333;
        }

        .sidebar .sidebar-content {
            background-color: #f7f7f7;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #3f51b5;
        }

        .dataframe thead tr {
            background-color: #3f51b5 !important;
            color: white !important;
        }

        .stDataFrame {
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Kystverket Maritime Tracker")

    # Load the csv files and rename data columns

    df = pd.read_csv("ship_routes_with_coords.csv", sep=",")
    df = df.dropna(subset=["dep_lat", "dep_lon", "arr_lat", "arr_lon"])

    df = df.rename(columns={
        "avgangshavn_navn": "Departure Port",
        "ankomsthavn_navn": "Arrival Port",
        "etd_estimert_avgangstidspunkt": "ETD",
        "ankomsttidspunkt": "ETA",
        "fartoynavn": "Ship Name",
        "dep_lat": "Dep Lat",
        "dep_lon": "Dep Lon",
        "arr_lat": "Arr Lat",
        "arr_lon": "Arr Lon"
    })


    # Convert datetime columns and create formatted versions

    df["ETD"] = pd.to_datetime(df["ETD"], utc=True)
    df["ETA"] = pd.to_datetime(df["ETA"], utc=True)

    df["ETD (Formatted)"] = df["ETD"].dt.strftime("%d.%m.%Y - %I:%M %p")
    df["ETA (Formatted)"] = df["ETA"].dt.strftime("%d.%m.%Y - %I:%M %p")

    # Sidebar Filters & Parameters

    st.sidebar.header("Filters")
    with st.sidebar.expander("Search Filters", expanded=True):
        selected_port = st.text_input("Search for a Port", "").strip()
        selected_ship = st.text_input("Search for a Ship (fartoynavn)", "").strip()

    if selected_port:
        df = df[
            (df["Departure Port"].str.contains(selected_port, case=False, na=False)) |
            (df["Arrival Port"].str.contains(selected_port, case=False, na=False))
        ]
    if selected_ship:
        df = df[df["Ship Name"].str.contains(selected_ship, case=False, na=False)]

    with st.sidebar.expander("Visualization Settings", expanded=True):
        radius = st.slider("Scatter Plot Radius (meters)", 100, 10000, 3000, 100)
        arc_width_scale = st.slider("Arc Width Scale", 0.01, 0.2, 0.03, 0.01)


    # PyDeck
    #    (a) Arc data (routes) (lines)
    #    (b) Scatter data (ports) (dots)

    route_counts = (
        df.groupby(["Departure Port", "Arrival Port"])
          .size()
          .reset_index(name="count")
    )

    # departure coords
    route_counts = pd.merge(
        route_counts,
        df[["Departure Port", "Dep Lat", "Dep Lon"]].drop_duplicates("Departure Port"),
        how="left",
        on="Departure Port"
    ).rename(columns={"Dep Lat": "source_lat", "Dep Lon": "source_lon"})

    # arrival coords
    route_counts = pd.merge(
        route_counts,
        df[["Arrival Port", "Arr Lat", "Arr Lon"]].drop_duplicates("Arrival Port"),
        how="left",
        on="Arrival Port"
    ).rename(columns={"Arr Lat": "target_lat", "Arr Lon": "target_lon"})

    route_counts["Port"] = ""
    route_counts["dep_count"] = 0
    route_counts["arr_count"] = 0

    # (b) scatter data: combine departure + arrival ports
    dep_stats = df.groupby("Departure Port").size().reset_index(name="dep_count")
    arr_stats = df.groupby("Arrival Port").size().reset_index(name="arr_count")

    departure_ports = (
        df[["Departure Port", "Dep Lat", "Dep Lon"]]
        .drop_duplicates("Departure Port")
        .rename(columns={"Departure Port": "Port", "Dep Lat": "Lat", "Dep Lon": "Lon"})
    )
    arrival_ports = (
        df[["Arrival Port", "Arr Lat", "Arr Lon"]]
        .drop_duplicates("Arrival Port")
        .rename(columns={"Arrival Port": "Port", "Arr Lat": "Lat", "Arr Lon": "Lon"})
    )

    all_ports = pd.concat([departure_ports, arrival_ports], ignore_index=True)
    all_ports.drop_duplicates(["Port", "Lat", "Lon"], inplace=True)

    # merge departure + arrival counts
    all_ports = pd.merge(all_ports, dep_stats, how="left", left_on="Port", right_on="Departure Port")
    all_ports = pd.merge(all_ports, arr_stats, how="left", left_on="Port", right_on="Arrival Port")
    all_ports["dep_count"] = all_ports["dep_count"].fillna(0).astype(int)
    all_ports["arr_count"] = all_ports["arr_count"].fillna(0).astype(int)

    # drop merge helper columns
    all_ports.drop(columns=["Departure Port", "Arrival Port"], inplace=True, errors="ignore")

    # placeholder columns for routes
    all_ports["Departure Port"] = ""
    all_ports["Arrival Port"] = ""
    all_ports["count"] = 0

    # PyDeck layers

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=route_counts,
        get_source_position=["source_lon", "source_lat"],
        get_target_position=["target_lon", "target_lat"],
        get_width="count",
        width_scale=arc_width_scale,
        get_source_color=[255, 0, 0],
        get_target_color=[0, 0, 255],
        pickable=True
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=all_ports,
        get_position=["Lon", "Lat"],
        get_radius=radius,
        radius_scale=1,
        radius_min_pixels=2,
        get_fill_color=[255, 140, 0],
        pickable=True
    )


    # Center the map

    if not df.empty:
        avg_lat = df["Dep Lat"].mean()
        avg_lon = df["Dep Lon"].mean()
    else:
        avg_lat, avg_lon = 0, 0

    view_state = pdk.ViewState(
        latitude=avg_lat,
        longitude=avg_lon,
        zoom=3,
        pitch=0
    )

    # tooltip for arcs & ports

    tooltip = {
        "html": """
        <b>Port:</b> {Port} <br />
        <b>Departures:</b> {dep_count} <br />
        <b>Arrivals:</b> {arr_count} <br />
        <hr />
        <b>Route:</b> {Departure Port} → {Arrival Port} <br />
        <b>Route Count:</b> {count}
        """,
        "style": {
            "backgroundColor": "#3f51b5",
            "color": "white",
            "padding": "10px",
            "borderRadius": "4px"
        }
    }


    # Display Map & Stats in Tabs

    tabs = st.tabs(["Map View", "Data & Summary"])

    with tabs[0]:
        st.subheader("Maritime Map")
        deck_chart = pdk.Deck(
            layers=[arc_layer, scatter_layer],
            initial_view_state=view_state,
            tooltip=tooltip
        )
        st.pydeck_chart(deck_chart)

    with tabs[1]:
        st.subheader("Summary Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Rows (Filtered)", value=len(df))
            st.metric(label="Unique Ships", value=df["Ship Name"].nunique() if not df.empty else 0)
        with col2:
            if not df.empty:
                most_dep = df["Departure Port"].mode()[0]
                most_arr = df["Arrival Port"].mode()[0]
                st.metric(label="Most Frequent Departure", value=most_dep)
                st.metric(label="Most Frequent Arrival", value=most_arr)
            else:
                st.write("No data for stats.")

        st.markdown("---")
        #  coords
        st.subheader("Selected Data")
        # Sorting + Pagination
        df_for_display = df[[
            "Ship Name",
            "Departure Port",
            "Arrival Port",
            "ETD (Formatted)",
            "ETA (Formatted)"
        ]].reset_index(drop=True)

        # Sort controls
        sort_column = st.selectbox("Sort Whole Table By Column", df_for_display.columns.tolist())
        sort_direction = st.radio("Sort Direction", ("Ascending", "Descending"), index=0)
        ascending_bool = (sort_direction == "Ascending")
        df_for_display = df_for_display.sort_values(by=sort_column, ascending=ascending_bool, ignore_index=True)

        # Pagination
        page_size = st.slider("Rows per page", 5, 50, 20)
        if "page_number" not in st.session_state:
            st.session_state.page_number = 0

        total_rows = len(df_for_display)
        total_pages = math.ceil(total_rows / page_size)

        if total_rows > 0:
            colA, colB, colC = st.columns([1, 2, 1])
            with colA:
                if st.button("Previous"):
                    if st.session_state.page_number > 0:
                        st.session_state.page_number -= 1
            with colB:
                st.markdown(
                    f"<div style='text-align:center;'>Page {st.session_state.page_number + 1} of {total_pages}</div>",
                    unsafe_allow_html=True
                )
            with colC:
                if st.button("Next"):
                    if st.session_state.page_number < total_pages - 1:
                        st.session_state.page_number += 1

            start_idx = st.session_state.page_number * page_size
            end_idx = start_idx + page_size
            st.dataframe(df_for_display.iloc[start_idx:end_idx])
        else:
            st.write("No data to display based on current filters.")

        st.markdown("---")
        if not route_counts.empty:
            st.subheader("Route Stats")
            route_counts_display = (
                route_counts[["Departure Port", "Arrival Port", "count"]]
                .sort_values("count", ascending=False)
            )
            st.dataframe(route_counts_display)

if __name__ == "__main__":
    main()
