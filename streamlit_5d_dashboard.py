from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="5D Bubble Dashboard", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "cm_data.xlsx"

REQUIRED_COLUMNS = ["Category", "Strategic", "Risk", "Sustainability", "Value", "GS"]

@st.cache_data

def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")
    df = pd.read_excel(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    df = df.copy()
    df = df.dropna(subset=["Strategic", "Risk", "Sustainability", "Value", "GS"])
    df["GS"] = df["GS"].astype(str)
    return df


def normalize_sizes(values: pd.Series, min_size: float, max_size: float) -> np.ndarray:
    vals = values.astype(float).to_numpy()
    vmin, vmax = np.nanmin(vals), np.nanmax(vals)
    if np.isclose(vmin, vmax):
        return np.full_like(vals, (min_size + max_size) / 2, dtype=float)
    return min_size + (vals - vmin) * (max_size - min_size) / (vmax - vmin)


def add_center_axes(fig: go.Figure, center: float, axis_min: float, axis_max: float) -> None:
    fig.add_trace(go.Scatter3d(
        x=[axis_min, axis_max], y=[center, center], z=[center, center],
        mode="lines", line=dict(color="black", width=6), showlegend=False, hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter3d(
        x=[center, center], y=[axis_min, axis_max], z=[center, center],
        mode="lines", line=dict(color="black", width=6), showlegend=False, hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter3d(
        x=[center, center], y=[center, center], z=[axis_min, axis_max],
        mode="lines", line=dict(color="black", width=6), showlegend=False, hoverinfo="skip"
    ))


def add_center_planes(fig: go.Figure, center: float, axis_min: float, axis_max: float) -> None:
    grid = np.linspace(axis_min, axis_max, 12)
    X, Y = np.meshgrid(grid, grid)
    common = dict(opacity=0.08, showscale=False, hoverinfo="skip")
    fig.add_trace(go.Surface(x=np.full_like(X, center), y=Y, z=X, **common))
    fig.add_trace(go.Surface(x=X, y=np.full_like(X, center), z=Y, **common))
    fig.add_trace(go.Surface(x=X, y=Y, z=np.full_like(X, center), **common))


def make_figure(
    df: pd.DataFrame,
    bubble_min: float,
    bubble_max: float,
    show_labels: bool,
    center_axes: bool,
    show_planes: bool,
    category_mode: str,
) -> go.Figure:
    plot_df = df.copy()
    plot_df["BubbleSize"] = normalize_sizes(plot_df["Value"], bubble_min, bubble_max)

    hovertemplate = (
        "<b>%{text}</b><br>"
        "SI: %{x}<br>"
        "SR: %{y}<br>"
        "SP: %{z}<br>"
        "Value: %{customdata[0]:,.0f}<br>"
        "GS: %{customdata[1]}<extra></extra>"
    )

    if category_mode == "GS":
        fig = go.Figure()
        for gs_value in sorted(plot_df["GS"].unique()):
            subset = plot_df[plot_df["GS"] == gs_value]
            fig.add_trace(go.Scatter3d(
                x=subset["Strategic"],
                y=subset["Risk"],
                z=subset["Sustainability"],
                mode="markers+text" if show_labels else "markers",
                text=subset["Category"],
                textposition="top center",
                name=gs_value,
                marker=dict(
                    size=subset["BubbleSize"],
                    sizemode="diameter",
                    opacity=0.85,
                    line=dict(width=1),
                ),
                customdata=np.column_stack([subset["Value"], subset["GS"]]),
                hovertemplate=hovertemplate,
            ))
    else:
        fig = go.Figure(go.Scatter3d(
            x=plot_df["Strategic"],
            y=plot_df["Risk"],
            z=plot_df["Sustainability"],
            mode="markers+text" if show_labels else "markers",
            text=plot_df["Category"],
            textposition="top center",
            marker=dict(
                size=plot_df["BubbleSize"],
                sizemode="diameter",
                color=plot_df["Value"],
                colorscale="Viridis",
                colorbar=dict(title="Value"),
                opacity=0.85,
                line=dict(width=1),
            ),
            customdata=np.column_stack([plot_df["Value"], plot_df["GS"]]),
            hovertemplate=hovertemplate,
            showlegend=False,
        ))

    axis_min, axis_max, center = 0, 4, 2
    if center_axes:
        add_center_axes(fig, center, axis_min, axis_max)
    if show_planes:
        add_center_planes(fig, center, axis_min, axis_max)

    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        scene=dict(
            xaxis=dict(title="Strategic Importance", range=[axis_min, axis_max], nticks=5, backgroundcolor="rgba(240,240,240,0.35)"),
            yaxis=dict(title="Supplier Risk", range=[axis_min, axis_max], nticks=5, backgroundcolor="rgba(240,240,240,0.35)"),
            zaxis=dict(title="Potential for Sustainability", range=[axis_min, axis_max], nticks=5, backgroundcolor="rgba(240,240,240,0.35)"),
            aspectmode="cube",
        ),
        title="5D Bubble Chart",
        legend_title_text="GS" if category_mode == "GS" else None,
    )
    return fig


def main() -> None:
    st.title("5D Bubble Dashboard")
#    st.caption("SI = Strategic, SR = Risk, SP = Sustainability, bubble size = Value, color/grouping = GS")
    st.caption("5d bubble chart")

    try:
        df = load_data(DATA_FILE)
    except Exception as e:
        st.error(str(e))
        st.stop()

    st.sidebar.header("Controls")

    categories = sorted(df["Category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

    gs_values = sorted(df["GS"].dropna().unique().tolist())
    selected_gs = st.sidebar.multiselect("GS", gs_values, default=gs_values)

    val_min = float(df["Value"].min())
    val_max = float(df["Value"].max())
    selected_value_range = st.sidebar.slider(
        "Value range",
        min_value=float(val_min),
        max_value=float(val_max),
        value=(float(val_min), float(val_max)),
    )

    bubble_min, bubble_max = st.sidebar.slider("Bubble size scale", 6, 40, (10, 28))
    category_mode = st.sidebar.radio("Color mode", ["GS", "Value"], horizontal=True)
    show_labels = st.sidebar.checkbox("Show labels", value=False)
    center_axes = st.sidebar.checkbox("Show centered axes at 2", value=True)
    show_planes = st.sidebar.checkbox("Show center planes", value=False)

    filtered = df[
        df["Category"].isin(selected_categories)
        & df["GS"].isin(selected_gs)
        & df["Value"].between(selected_value_range[0], selected_value_range[1])
    ].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Visible bubbles", f"{len(filtered)}")
    c2.metric("Total value", f"{filtered['Value'].sum():,.0f}" if len(filtered) else "0")
    c3.metric("Average value", f"{filtered['Value'].mean():,.0f}" if len(filtered) else "0")

    if filtered.empty:
        st.warning("No rows match the selected filters.")
        st.stop()

    fig = make_figure(
        filtered,
        bubble_min=bubble_min,
        bubble_max=bubble_max,
        show_labels=show_labels,
        center_axes=center_axes,
        show_planes=show_planes,
        category_mode=category_mode,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Filtered data"):
        st.dataframe(
            filtered[["Category", "Strategic", "Risk", "Sustainability", "Value", "GS"]]
            .sort_values("Value", ascending=False),
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
