import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.sources.dedup import check_cross_channel_duplicate


# ----------------------------
# Cas 1 : doublon détecté
# ----------------------------
def test_cross_channel_duplicate_detected():
    conn = MagicMock()
    cur = MagicMock()

    conn.cursor.return_value = cur
    cur.fetchone.return_value = (1,)  # match trouvé en DB

    result = check_cross_channel_duplicate(
        conn=conn,
        current_hash="abc123",
        sender="user1",
        current_time=datetime.utcnow()
    )

    assert result == "cross_channel_duplicate"
    cur.execute.assert_called_once()
    cur.close.assert_called_once()


# ----------------------------
# Cas 2 : faux positif évité
# (deux clients différents)
# ----------------------------
def test_no_duplicate_different_senders():
    conn = MagicMock()
    cur = MagicMock()

    conn.cursor.return_value = cur
    cur.fetchone.return_value = None  # aucun match

    result = check_cross_channel_duplicate(
        conn=conn,
        current_hash="same_hash",
        sender="user1",
        current_time=datetime.utcnow()
    )

    assert result == "active"
    cur.close.assert_called_once()


# ----------------------------
# Cas 3 : hors fenêtre (5 jours)
# ----------------------------
def test_no_duplicate_outside_time_window():
    conn = MagicMock()
    cur = MagicMock()

    conn.cursor.return_value = cur
    cur.fetchone.return_value = None  # filtré par SQL

    result = check_cross_channel_duplicate(
        conn=conn,
        current_hash="abc123",
        sender="user1",
        current_time=datetime.utcnow()
    )

    assert result == "active"

    # vérifie que la requête est bien exécutée avec fenêtre
    args, _ = cur.execute.call_args
    assert "received_at >=" in args[0]
    assert "received_at <=" in args[0]


# ----------------------------
# Cas : même body "bonjour"
# mais utilisateurs différents
# ----------------------------
def test_identical_body_different_users_not_deduplicated():
    conn = MagicMock()
    cur = MagicMock()

    conn.cursor.return_value = cur
    cur.fetchone.return_value = None

    result1 = check_cross_channel_duplicate(
        conn=conn,
        current_hash="hash_bonjour",
        sender="user1",
        current_time=datetime.utcnow()
    )

    result2 = check_cross_channel_duplicate(
        conn=conn,
        current_hash="hash_bonjour",
        sender="user2",
        current_time=datetime.utcnow()
    )

    assert result1 == "active"
    assert result2 == "active"