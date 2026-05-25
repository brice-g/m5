import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from email.message import Message
from resources.src.sources.legacy_collect import extract_body, collect

# =====================================================================
# TEST BUG 1 : Non-régression sur l'encodage non-UTF-8 (ex: ISO-8859-1)
# =====================================================================
def test_extract_body_non_utf8_encoding():
    msg = Message()
    msg.set_payload(b"H\xe9llo Support")  # "Héllo Support" encodé en ISO-8859-1
    msg.set_param("charset", "iso-8859-1")
    
    # Sans la correction, cela lèverait une exception UnicodeDecodeError
    body = extract_body(msg)
    assert body == "Héllo Support"


# =====================================================================
# TEST BUG 3 : Non-régression sur la conservation de la Timezone
# =====================================================================
@patch("resources.src.sources.legacy_collect.psycopg2.connect")
@patch("resources.src.sources.legacy_collect.mailbox.mbox")
def test_collect_preserves_timezone(mock_mbox, mock_connect):
    # Simuler un email avec un offset +0200
    msg = Message()
    msg["Message-ID"] = "<test-tz@fastia.ai>"
    msg["Date"] = "Fri, 15 May 2026 14:30:00 +0200"
    msg.set_payload("Corps du message")
    
    mock_box = MagicMock()
    mock_box.__iter__.return_value = [msg]
    mock_mbox.return_value = mock_box
    
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.rowcount = 1
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    collect("dummy_path.mbox")
    
    # Récupérer les arguments passés à cur.execute
    args, _ = mock_cur.execute.call_args
    sql_args = args[1]
    
    captured_date = sql_args[2]  # Le 3ème paramètre est received_at
    
    assert captured_date.tzinfo is not None
    assert captured_date.utcoffset() == timedelta(hours=2)


# =====================================================================
# TEST BUG 2 : Non-régression sur l'idempotence (Double exécution)
# =====================================================================
@patch("resources.src.sources.legacy_collect.psycopg2.connect")
@patch("resources.src.sources.legacy_collect.mailbox.mbox")
def test_collect_idempotency_handling(mock_mbox, mock_connect):
    msg = Message()
    msg["Message-ID"] = "<duplicate-id@fastia.ai>"
    msg["Date"] = "Fri, 15 May 2026 14:30:00 +0000"
    msg.set_payload("Corps du message")
    
    mock_box = MagicMock()
    mock_box.__iter__.return_value = [msg]
    mock_mbox.return_value = mock_box
    
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    # Simuler que la ligne est ignorée (rowcount = 0) à cause du ON CONFLICT
    mock_cur.rowcount = 0 
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    
    # On capture la sortie standard pour vérifier le décompte (print)
    with patch("builtins.print") as mock_print:
        collect("dummy_path.mbox")
        # Doit afficher 0 inséré et 1 skipped car le rowcount simulé était 0
        mock_print.assert_called_with("Inserted: 0, skipped: 1")
    
    # Vérifier que le SQL généré intègre bien la clause d'évitement de conflit
    args, _ = mock_cur.execute.call_args
    assert "ON CONFLICT (canal, external_id) DO NOTHING" in args[0]