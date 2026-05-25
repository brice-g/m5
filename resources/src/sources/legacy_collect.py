"""
Collecte rapide des emails support FastIA depuis un fichier mbox.

CORRIGÉ (M3) : Gestion des encodages, de l'idempotence et des timezones.
"""

import mailbox
import os
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime  # Correction Bug 3
import psycopg2

DB_DSN = os.environ.get(
    "FASTIA_DB_DSN",
    "postgresql://fastia:fastia@localhost:5432/fastia",
)


def extract_body(msg):
    """Recupere le corps texte d'un message (best effort)."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    # Correction Bug 1 : Récupération dynamique du charset
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        # Correction Bug 1 : Récupération dynamique du charset
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    return ""


def collect(mbox_path):
    box = mailbox.mbox(mbox_path)
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()

    inserted = 0
    skipped = 0
    for msg in box:
        message_id = (msg.get("Message-ID") or "").strip()
        sender = msg.get("From", "")
        subject = msg.get("Subject", "")
        date_raw = msg.get("Date", "")

        # Correction Bug 3 : Utilisation de parsedate_to_datetime pour garder la TZ
        try:
            received_at = parsedate_to_datetime(date_raw)
        except Exception:
            skipped += 1
            continue

        body = extract_body(msg)
        if not body.strip():
            skipped += 1
            continue

        # Correction Bug 2 : Ajout de l'idempotence via ON CONFLICT
        # Note : On s'assure d'inclure les colonnes requises par le schéma M2 (dataset_version, categorie, priorite, source)
        cur.execute(
            """
            INSERT INTO demandes
                (canal, external_id, received_at, sender, subject, body, dataset_version, categorie, priorite, source)
            VALUES (%s, %s, %s, %s, %s, %s, 'v2', 'inconnu', 'moyenne', 'legacy_script')
            ON CONFLICT (canal, external_id) DO NOTHING;
            """,
            ("email", message_id, received_at, sender, subject, body),
        )
        
        # cur.rowcount renvoie 1 si inséré, 0 si ignoré par le ON CONFLICT
        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Inserted: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python legacy_collect.py <path/to/file.mbox>")
        sys.exit(1)
    collect(sys.argv[1])