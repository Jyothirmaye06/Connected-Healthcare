"""
data_service.py
---------------
The single place where Streamlit caching is applied.

Why this module exists: database_utils / analysis_utils / crowd_model are kept
free of Streamlit so they stay testable. This thin layer wraps them with
`st.cache_data` / `st.cache_resource` for the UI.

Cache invalidation strategy
---------------------------
Every cached function takes a `version` argument produced by `data_version()`,
which is a cheap count of the rows in the database. As soon as an admin inserts
a new record the version changes, the cache key changes, and the public
dashboard shows the new data. Caches also expire on a short TTL, so nothing is
cached indefinitely.
"""

import streamlit as st

from database import DatabaseError, ensure_database
from models.crowd_model import train_crowd_model
from utils import database_utils as db

CACHE_TTL = 60  # seconds


# --------------------------------------------------------------------------
# Start-up & versioning
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def bootstrap():
    """Create the schema and seed demo data exactly once per server process."""
    ensure_database()
    return True


def data_version():
    """
    Cheap fingerprint of the database contents.

    Used as a cache key so that any insert made on the Admin page immediately
    invalidates the cached dashboard queries.
    """
    try:
        summary = db.get_database_summary()
        return sum(summary.values())
    except DatabaseError:
        return 0


def refresh():
    """Force every cache to be rebuilt (used by the Refresh buttons)."""
    st.cache_data.clear()
    st.cache_resource.clear()


# --------------------------------------------------------------------------
# Cached readers
# --------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def locations(version):
    return db.get_locations()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def hospitals(location, version):
    return db.get_hospitals(location)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def cases(location, version, condition=None, days=None):
    return db.get_cases(location, condition=condition, days=days)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def conditions(location, version):
    return db.get_conditions(location)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def all_known_conditions(version):
    return db.get_all_known_conditions()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def health_information(condition, version):
    return db.get_health_information(condition)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def latest_queue(location, version):
    return db.get_latest_queue(location)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def queue_history(version, hospital_id=None, location=None, days=None):
    return db.get_queue_history(hospital_id=hospital_id, location=location, days=days)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def saved_predictions(version, hospital_id=None, location=None):
    return db.get_saved_predictions(hospital_id=hospital_id, location=location)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def database_summary(version):
    return db.get_database_summary()


# --------------------------------------------------------------------------
# Cached ML model (expensive — trained once per location per data version)
# --------------------------------------------------------------------------
@st.cache_resource(ttl=900, show_spinner="Training the crowd prediction model…")
def crowd_model(location, version):
    """
    Train (or reuse) the crowd model for a location.

    Returns (model, error_message); the caller displays the message instead of
    crashing when there is not enough history.
    """
    history = db.get_queue_history(location=location)
    return train_crowd_model(history)
