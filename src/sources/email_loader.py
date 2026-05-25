import mailbox
import re
import logging
from datetime import datetime
from email.header import decode_header
from mailbox import mboxMessage
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterator, Literal
from bs4 import BeautifulSoup
from pydantic import BaseModel

# Configuration du logger
logger = logging.getLogger(__name__)

class RawDemande(BaseModel):
    canal: Literal["email", "web", "chat"]
    external_id: str
    received_at: datetime
    sender: str | None
    subject: str | None
    body: str
    canal_metadata: dict


def decode_mime_header(header_value: str | None) -> str | None:
    """Décode les en-têtes encodés comme =?utf-8?B?...?="""
    if not header_value:
        return None
    
    # Si c'est un objet Header (et non un str), on le convertit proprement
    if not isinstance(header_value, str):
        try:
            return str(header_value).strip()
        except Exception as e:
            logger.warning(f"Échec de la conversion de l'objet Header: {e}")
            return repr(header_value) # Fallback sécurisé en str pour Pydantic

    try:
        decoded_fragments = decode_header(header_value)
        header_text = ""
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                header_text += fragment.decode(encoding or "utf-8", errors="replace")
            else:
                header_text += fragment
        return header_text.strip()
    except Exception as e:
        logger.warning(f"Échec du décodage de l'en-tête: {e}")
        return header_value


def strip_quoted_text(text: str) -> str:
    """
    Nettoie le texte en coupant les signatures (-- \n) 
    et en retirant les lignes de citation (>).
    """
    lines = text.splitlines()
    clean_lines = []

    for line in lines:
        if line.strip() in ("--", "---"):
            break
        
        if line.strip().startswith(">"):
            continue
            
        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


def extract_email_body(message: mailbox.Message) -> str | None:
    """
    Parcourt l'email pour extraire le texte brut.
    Préfère le text/plain, fallback sur le text/html traduit en texte brut.
    """
    plain_text = None
    html_text = None

    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
                continue
                
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            
            # Sécurité pour le linter: get_payload(decode=True) renvoie des bytes ou None
            if not payload or not isinstance(payload, bytes):
                continue

            charset = part.get_content_charset() or "utf-8"
            try:
                decoded_payload = payload.decode(charset, errors="replace")
            except Exception:
                decoded_payload = payload.decode("utf-8", errors="replace")

            if content_type == "text/plain":
                plain_text = decoded_payload
                break 
            elif content_type == "text/html":
                html_text = decoded_payload
    else:
        payload = message.get_payload(decode=True)
        if payload and isinstance(payload, bytes):
            charset = message.get_content_charset() or "utf-8"
            content_type = message.get_content_type()
            
            try:
                decoded_payload = payload.decode(charset, errors="replace")
            except Exception:
                decoded_payload = payload.decode("utf-8", errors="replace")
            
            if content_type == "text/html":
                html_text = decoded_payload
            else:
                plain_text = decoded_payload

    if plain_text and plain_text.strip():
        return plain_text
    elif html_text and html_text.strip():
        soup = BeautifulSoup(html_text, "html.parser")
        return soup.get_text(separator="\n")
    
    return None


def load_mbox(path: Path) -> Iterator[RawDemande]:
    """Itère sur les messages d'un fichier mbox et yield un RawDemande par mail."""
    if not path.exists():
        logger.error(f"Le fichier mbox {path} n'existe pas.")
        return

    try:
        mbox = mailbox.mbox(path, factory=mboxMessage) 
    except Exception as e:
        logger.error(f"Impossible d'ouvrir le fichier mbox : {e}")
        return

    for key, message in mbox.items():
        raw_body = extract_email_body(message)
        if not raw_body:
            logger.warning(f"Message ignoré (clé mbox {key}) : aucun corps de texte utilisable.")
            continue
            
        clean_body = strip_quoted_text(raw_body)
        if not clean_body:
            logger.warning(f"Message ignoré (clé mbox {key}) : corps vide après nettoyage des citations/signatures.")
            continue

        external_id = message.get("Message-ID") or f"mbox_key_{key}"
        
        date_header = message.get("Date")
        if date_header:
            try:
                received_at = parsedate_to_datetime(str(date_header))
            except Exception:
                received_at = datetime.now()
        else:
            received_at = datetime.now()

        sender = decode_mime_header(message.get("From"))
        subject = decode_mime_header(message.get("Subject"))
        to_field = decode_mime_header(message.get("To"))

        canal_metadata = {
            "mbox_key": key,
            "to": to_field,
            "headers": {k: str(v) for k, v in message.items() if k.lower() in ["x-mailer", "thread-topic", "references"]}
        }

        yield RawDemande(
            canal="email",
            external_id=str(external_id).strip("<>"),
            received_at=received_at,
            sender=sender,
            subject=subject,
            body=clean_body,
            canal_metadata=canal_metadata
        )