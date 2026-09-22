"""
utils/ui.py
-----------
Reusable Streamlit presentation components: page setup, the global location
selector, metric cards, hospital crowd cards and the standard notices.

Keeping these here means every page looks the same and the page files stay
short and readable.
"""

import streamlit as st

from config import (
    APP_NAME,
    APP_TAGLINE,
    CROWD_STATUS_STYLE,
    DEMO_DATA_NOTICE,
    MEDICAL_DISCLAIMER,
    PREDICTION_DISCLAIMER,
)
import data_service
from utils.analysis_utils import describe_time_ago

CUSTOM_CSS = """
<style>
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1200px; }

    .ch-hero {
        background: linear-gradient(120deg, #0f766e 0%, #0e7490 55%, #1d4ed8 100%);
        color: #ffffff; padding: 1.6rem 1.8rem; border-radius: 16px;
        margin-bottom: 1.2rem;
    }
    .ch-hero h1 { margin: 0; font-size: 2.0rem; letter-spacing: .5px; color: #fff; }
    .ch-hero p  { margin: .35rem 0 0; opacity: .92; font-size: 1.0rem; }

    .ch-metric {
        background: #ffffff; border: 1px solid #e5e7eb; border-left: 5px solid #0f766e;
        border-radius: 12px; padding: 1rem 1.1rem; height: 100%;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .06);
    }
    .ch-metric .label { font-size: .78rem; text-transform: uppercase;
        letter-spacing: .6px; color: #64748b; font-weight: 600; }
    .ch-metric .value { font-size: 1.7rem; font-weight: 700; color: #0f172a;
        margin-top: .25rem; line-height: 1.2; }
    .ch-metric .hint  { font-size: .8rem; color: #64748b; margin-top: .2rem; }

    .ch-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 14px;
        padding: 1.1rem 1.25rem; margin-bottom: .9rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .06);
    }
    .ch-card h4 { margin: 0 0 .15rem; font-size: 1.12rem; color: #0f172a; }
    .ch-card .sub { color: #64748b; font-size: .85rem; margin-bottom: .7rem; }
    .ch-stat { display: inline-block; margin-right: 1.8rem; }
    .ch-stat .k { font-size: .75rem; color: #64748b; text-transform: uppercase;
        letter-spacing: .5px; }
    .ch-stat .v { font-size: 1.25rem; font-weight: 700; color: #0f172a; }
    .ch-updated { color: #94a3b8; font-size: .78rem; margin-top: .6rem; }

    .ch-pill { display: inline-block; padding: .2rem .7rem; border-radius: 999px;
        font-size: .8rem; font-weight: 600; }

    .ch-trend {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: .9rem 1rem; height: 100%;
    }
    .ch-trend .name { font-weight: 700; color: #0f172a; font-size: 1.02rem; }
    .ch-trend .delta { font-size: 1.3rem; font-weight: 700; margin-top: .2rem; }
    .ch-trend .note { font-size: .78rem; color: #64748b; margin-top: .25rem; }

    .ch-demo-badge {
        background: #fff7ed; border: 1px solid #fed7aa; color: #9a3412;
        border-radius: 10px; padding: .55rem .85rem; font-size: .82rem;
        margin-bottom: 1rem;
    }
    section[data-testid="stSidebar"] .ch-side {
        font-size: .8rem; color: #64748b; line-height: 1.45;
    }

    .ch-condition-row {
        display: flex; justify-content: space-between; align-items: center;
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: .8rem 1.1rem; margin-bottom: .6rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .05);
    }
    .ch-condition-row .name { font-weight: 700; color: #0f172a; font-size: 1.02rem; }
    .ch-condition-row .count { color: #64748b; font-size: .88rem; text-align: right; }

    .ch-summary {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 14px;
        padding: 1.1rem 1.25rem; margin-bottom: 1rem; font-size: 1.0rem;
        color: #0f172a; line-height: 1.6;
    }
    .ch-summary b { color: #0f766e; }

    .ch-chart-note {
        color: #64748b; font-size: .85rem; margin: -.3rem 0 .8rem;
    }
</style>
"""


# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------
def setup_page(title, icon="🏥"):
    """Standard page configuration + CSS + database bootstrap."""
    st.set_page_config(
        page_title=f"{title} | {APP_NAME}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    data_service.bootstrap()


def hero(subtitle=None):
    """The gradient page header."""
    st.markdown(
        f"""
        <div class="ch-hero">
            <h1>{APP_NAME}</h1>
            <p>{subtitle or APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def demo_badge():
    st.markdown(
        f'<div class="ch-demo-badge">🧪 <b>{DEMO_DATA_NOTICE}</b></div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Global location selector
# --------------------------------------------------------------------------
def location_selector(label="📍 Select Your Location", sidebar=False):
    """
    Location picker shared by every public page.

    The choice is stored in st.session_state so switching page keeps the
    selected city, and changing it re-filters every query on every page.
    """
    version = data_service.data_version()
    available = data_service.locations(version)

    if not available:
        st.error("No hospitals are registered yet. Please seed the database from the Admin page.")
        st.stop()

    current = st.session_state.get("location", available[0])
    if current not in available:
        current = available[0]

    container = st.sidebar if sidebar else st
    selected = container.selectbox(
        label, available, index=available.index(current), key="location_picker",
    )
    st.session_state["location"] = selected
    return selected


def sidebar_footer():
    """Short context block shown in the sidebar on every page."""
    with st.sidebar:
        st.markdown("---")
        if st.button("🔄 Refresh data", use_container_width=True):
            data_service.refresh()
            st.rerun()
        st.markdown(
            '<div class="ch-side">'
            "All information shown is demo data for this project.<br>"
            "This platform does not diagnose medical conditions."
            "</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------
# Cards
# --------------------------------------------------------------------------
def metric_card(label, value, hint=""):
    st.markdown(
        f"""
        <div class="ch-metric">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="hint">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(status):
    style = CROWD_STATUS_STYLE.get(status, CROWD_STATUS_STYLE["Unknown"])
    return (
        f'<span class="ch-pill" style="background:{style["color"]}1A;'
        f'color:{style["color"]};">{style["emoji"]} {status}</span>'
    )


def hospital_crowd_card(row, show_status=True):
    """
    One hospital's latest reported crowd, rendered as a self-contained card.

    `row` is a record from get_latest_queue() annotated with a `status` column.
    Missing data is displayed honestly rather than replaced with a guess.
    """
    patients = row.get("patients_waiting")
    minutes = row.get("estimated_waiting_minutes")
    has_data = patients == patients and patients is not None  # NaN-safe

    if has_data:
        stats = f"""
            <div class="ch-stat">
                <div class="k">Current reported crowd</div>
                <div class="v">{int(patients)} patients waiting</div>
            </div>
            <div class="ch-stat">
                <div class="k">Estimated waiting time</div>
                <div class="v">{int(minutes)} minutes</div>
            </div>
        """
        pill = status_pill(row.get("status", "Unknown")) if show_status else ""
        updated = f"Last updated: {row['recorded_at'].strftime('%d %b %Y, %I:%M %p')} " \
                  f"({describe_time_ago(row['recorded_at'])})"
    else:
        stats = (
            '<div class="ch-stat"><div class="k">Current reported crowd</div>'
            '<div class="v">Not reported yet</div></div>'
        )
        pill = status_pill("Unknown")
        updated = "No crowd record has been submitted for this hospital yet."

    st.markdown(
        f"""
        <div class="ch-card">
            <h4>{row['hospital_name']}</h4>
            <div class="sub">{row['location']}</div>
            {stats}
            <div style="margin-top:.7rem;">{pill}</div>
            <div class="ch-updated">{updated}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def summary_card(html):
    """A single plain-language sentence/paragraph in a soft card (Health Overview)."""
    st.markdown(f'<div class="ch-summary">{html}</div>', unsafe_allow_html=True)


def condition_row(name, count_label, key=None, button_label=None):
    """
    One compact row for a health condition: name + reported-cases label.

    If button_label is given, an actual Streamlit button is rendered next to
    the row (used to jump straight into that condition's detail page) and its
    clicked state is returned; otherwise returns None.
    """
    row_col, btn_col = st.columns([4, 1]) if button_label else (st.container(), None)
    with row_col:
        st.markdown(
            f"""
            <div class="ch-condition-row">
                <span class="name">{name}</span>
                <span class="count">{count_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if button_label:
        with btn_col:
            return st.button(button_label, key=key, use_container_width=True)
    return None


def bullet_list(text):
    """
    Render a semicolon-separated sentence as a clean bullet list.

    Health-information text is written as clauses separated by '; ' — this
    splits on that separator so normal users see short bullet points instead
    of one dense paragraph. Falls back to a single paragraph if there is
    nothing to split on.
    """
    if not text:
        return
    parts = [p.strip().rstrip(".") for p in text.split(";") if p.strip()]
    if len(parts) <= 1:
        st.write(text)
        return
    st.markdown("\n".join(f"- {p.capitalize()}." for p in parts))


def chart_note(text):
    """Small grey explanation line placed above/below a chart."""
    st.markdown(f'<div class="ch-chart-note">{text}</div>', unsafe_allow_html=True)


def trend_card(row, format_label):
    """A single 'Recent Health Trends' card."""
    if row["enough_data"] and row["change_pct"] is not None:
        change = row["change_pct"]
        color = "#dc2626" if change > 0 else ("#16a34a" if change < 0 else "#64748b")
        arrow = "▲" if change > 0 else ("▼" if change < 0 else "▬")
        delta = f'<div class="delta" style="color:{color};">{arrow} {format_label}</div>'
        note = (f'<div class="note">{row["recent_cases"]} recent vs '
                f'{row["previous_cases"]} previous reported cases</div>')
    else:
        delta = '<div class="delta" style="color:#64748b;font-size:.95rem;">Insufficient historical data to determine a trend.</div>'
        note = f'<div class="note">{row["recent_cases"]} recent reported cases</div>'

    st.markdown(
        f"""
        <div class="ch-trend">
            <div class="name">{row['condition']}</div>
            {delta}
            {note}
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Notices
# --------------------------------------------------------------------------
def medical_disclaimer(expanded=False):
    st.markdown("### ⚠️ Health Awareness Notice")
    st.info(MEDICAL_DISCLAIMER)


def prediction_disclaimer():
    st.caption(f"ℹ️ {PREDICTION_DISCLAIMER}")


def empty_state(message, hint=None):
    """Consistent, friendly empty-data message."""
    st.info(message + (f"\n\n{hint}" if hint else ""))
