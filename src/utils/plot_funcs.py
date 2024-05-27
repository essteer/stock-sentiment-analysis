# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ===============================================================
# Plot palette and template
# ===============================================================


def get_palette() -> dict:
    """
    Called by utils.handler_funcs.handle_plots()
    Called by utils.plot_funcs: format_plot(), plot_candlestick() plot_sentiment()

    Returns
    -------
    pal : dict
        Dictionary with custom plot colour scheme
    """
    pal = {
        "dark": "#252b33",
        "grey": "#45464d",
        "light": "#fefeff",
        "stone": "#8f8f94",
        "blue": "#336681",
        "green": "#089389",
        "red": "#d34748",
        "pink": "#cf82d3",
        "yellow": "#e6daaa",
        "sky": "#8ebdff",
    }

    return pal


def format_plot(fig) -> None:
    """
    Applies custom theme to Plotly figure in-place
    Called by plot_funcs.plot_candlestick()

    Parameters
    ----------
    fig : Plotly figure

    Returns
    -------
    None : formats fig in-place
    """
    # Get custom palette
    palette = get_palette()

    fig.update_layout(
        plot_bgcolor=palette["dark"],
        paper_bgcolor=palette["dark"],
        title_font_color=palette["light"],
        xaxis_title_font_color=palette["light"],
        yaxis_title_font_color=palette["light"],
        xaxis_tickfont_color=palette["stone"],
        yaxis_tickfont_color=palette["stone"],
        xaxis_gridcolor=palette["grey"],
        yaxis_gridcolor=palette["grey"],
        xaxis_linecolor=palette["stone"],
        yaxis_linecolor=palette["stone"],
        title={"x": 0.5},  # Center title
        xaxis={
            "categoryorder": "category ascending"
        },  # Set y-axis labels from low to high
        yaxis={
            "categoryorder": "category ascending",  # Set y-axis labels from low to high
            # Add invisible y-ticks to add space between y-axis and y-labels
            "ticks": "outside",
            "tickcolor": palette["dark"],
            "ticklen": 5,
        },
        legend_font_color=palette["stone"],
        legend=dict(x=0.99),
        margin=dict(l=80, r=20, t=60, b=20),
    )
    fig.update_yaxes(title_standoff=5)


# ===============================================================
# Candlestick plot for selected ticker, period and interval
# ===============================================================


def plot_candlestick(
    fig: go.Figure,
    ticker_code: str,
    history: pd.DataFrame,
    horizon: str,
    earnings_dates: list = [],
    name: str = "",
    currency: str = "Currency Undefined",
    period: str = "3mo",
    interval: str = "1d",
) -> None:
    """
    Applies candlestick price data and trade volume data to a Plotly figure.
    Called by utils.handler_funcs.handle_plots()

    Parameters
    ----------
    See main.run_once() and utils.handler_funcs.handle_data() functions for parameter descriptions

    Complete example : plot_candlestick("MSFT", <pd.DataFrame>, "YYYY-MM-DD", ["YYYY-DD-MM", "YYYY-DD-MM"],
    "Microsoft Corporation", "USD", "1d")
    """
    # Get custom palette
    palette = get_palette()
    # Add OHLC data to first subplot (Prices)
    fig.update_traces(
        x=history.index,
        open=history["Open"],
        high=history["High"],
        low=history["Low"],
        close=history["Close"],
        hoverinfo="x+y",
        selector={"name": "Prices"},
    )
    # Add trade volume data to second subplot (Volume)
    fig.update_traces(
        x=history.index,
        y=history["Volume"],
        mode="lines",
        line_color=palette["sky"],
        hovertemplate="%{x|%b %d, %Y}<br>%{y:,.0f}<extra></extra>",  # <extra> code removes trace name default
        selector={"name": "Volume"},
    )

    start_date = history.index.min()
    end_date = history.index.max()
    # Get date range information for plot title
    start_date_string = start_date.strftime("%d %b. %Y")
    end_date_string = end_date.strftime(
        "%d %b. %Y"
    )  # here b/c end_date reassigned to horizon below
    date_range_label = f"{start_date_string} - {end_date_string}"

    # Extend x-axis to horizon
    if horizon != "":
        fig.update_layout(xaxis_range=[history.index.min(), horizon])
        end_date = horizon

    # Calculate mean close price and mean trade volume
    mean_price = history["Close"].mean()
    mean_volume = history["Volume"].mean()
    # Add horizontal dashed lines for mean values - declare only one on legend
    fig.add_shape(
        type="line",
        x0=start_date,
        x1=end_date,
        y0=mean_price,
        y1=mean_price,
        line=dict(color=palette["stone"], width=2, dash="dash"),
        name="Mean",
        showlegend=True,
        row=1,
        col=1,
    )
    fig.add_shape(
        type="line",
        x0=start_date,
        x1=end_date,
        y0=mean_volume,
        y1=mean_volume,
        line=dict(color=palette["stone"], width=2, dash="dash"),
        name="Mean",
        row=2,
        col=1,
    )

    # Get period to determine x-axis date display
    periods_dict = {"1mo": 7, "3mo": 7, "6mo": 7, "1y": 14}
    period_label = periods_dict[period.lower()]

    # Hide dates on Prices (top) subplot x-axis
    fig.update_xaxes(dtick=86400000 * period_label, showticklabels=False, row=1, col=1)
    fig.update_yaxes(title_text=f"Price ({currency})", row=1, col=1)
    # Show dates on Volume (bottom) subplot x-axis
    fig.update_xaxes(
        range=[history.index.min(), horizon],
        tickfont=dict(color=palette["stone"]),
        gridcolor=palette["grey"],
        linecolor=palette["stone"],
        tickangle=45,
        dtick=86400000 * period_label,
        tickformat="%Y-%m-%d",
        row=2,
        col=1,
    )
    fig.update_yaxes(
        title_text="Volume",
        title=dict(font=dict(color=palette["light"])),
        tickfont=dict(color=palette["stone"]),
        gridcolor=palette["grey"],
        linecolor=palette["stone"],
        row=2,
        col=1,
    )

    # Get interval label for figure title
    intervals_dict = {"1d": "Daily", "1wk": "Weekly"}
    interval_label = intervals_dict[interval.lower()]

    # Combine name, ticker, and interval for figure title
    ticker_label = f"{name} ({ticker_code.upper()}) {interval_label}"
    # Update layout
    fig.update_layout(
        title_text=f"{ticker_label} Market Data <br>{date_range_label}",
        xaxis_rangeslider_visible=False,
        width=1080,
        height=720,
    )

    # Add earnings dates as vertical lines
    if earnings_dates != []:
        reverse_earnings_dates = earnings_dates[
            ::-1
        ]  # Reverse list so legend is chronological
        for date in reverse_earnings_dates:
            fig.add_shape(
                type="line",
                x0=date,
                x1=date,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                line=dict(color=palette["pink"], width=1, dash="dash"),
                name=f"ED '{date[2:]}",
                showlegend=True,
            )


# ===============================================================
# Sentiment data plot trace
# ===============================================================


def plot_sentiment(sent_df: pd.DataFrame, fig: go.Figure) -> None:
    """
    Applies market sentiment data to a Plotly figure.
    Called by utils.handler_funcs.handle_plots()

    Parameters
    ----------
    See main.run_once() and utils.handler_funcs.handle_data() functions for parameter descriptions

    Complete example : plot_candlestick("MSFT", <pd.DataFrame>, "YYYY-MM-DD", ["YYYY-DD-MM", "YYYY-DD-MM"],
    "Microsoft Corporation", "USD", "1d")
    """
    # Get custom palette
    palette = get_palette()

    if not sent_df["rolling_avg"].isna().all():
        max_value = np.nanmax(sent_df["rolling_avg"])
        min_value = np.nanmin(sent_df["rolling_avg"])
        # Calculate upper and lower bounds
        upper_bound = min([1.0, max_value + 0.2])
        lower_bound = max([-1.0, min_value - 0.2])

    else:
        upper_bound = 1.0
        lower_bound = -1.0

    fig.update_traces(
        x=sent_df.index,
        y=sent_df["rolling_avg"],
        mode="lines+markers",
        line_color=palette["yellow"],
        marker=dict(symbol="arrow", size=10, angleref="previous"),
        hovertemplate="%{x|%b %d, %Y}<br>sentiment (1wk avg): %{y:,.2f}<extra></extra>",  # <extra> code removes trace name default
        showlegend=True,
        selector={"name": "Sentiment"},
    )
    fig.update_yaxes(
        title_text="",
        tickfont=dict(color=palette["stone"]),
        tickmode="array",
        range=[lower_bound, upper_bound],
        zeroline=False,
        showgrid=False,
        row=1,
        col=1,
        secondary_y=True,
    )
