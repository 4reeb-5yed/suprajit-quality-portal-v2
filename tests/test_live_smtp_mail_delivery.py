"""
REAL LOCAL SMTP INTEGRATION TEST SUITE
Tests authentic SMTP network socket delivery and dynamic email templating in app/mail.py:
1. Local SMTP socket server with AUTH extension support
2. send_password_reset_email (verifies recipient, tokenized reset_url in body, subject)
3. send_welcome_email (verifies username, raw temporary password, portal_url)
4. send_bulk_invite_email (verifies company-branded invitation copy, credentials)
5. send_heartbeat_email (verifies developer telemetry metrics and critical error log body)

ZERO MOCKS: All dispatches traverse the genuine smtplib.SMTP socket client.
"""

import threading
import time
import socket
from email import message_from_bytes
import pytest
from app.database import get_connection, ensure_schema
from app.helpers import encrypt_password
from app.mail import (
    send_password_reset_email,
    send_welcome_email,
    send_bulk_invite_email,
    send_heartbeat_email,
)


class LocalSMTPServer:
    """Lightweight in-process SMTP server supporting EHLO, AUTH, and DATA on a local TCP port."""
    def __init__(self):
        self.received_messages = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', 0))
        self.sock.listen(5)
        self.host, self.port = self.sock.getsockname()
        self.running = True
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        self.sock.settimeout(0.5)
        while self.running:
            try:
                conn, _ = self.sock.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn):
        conn.sendall(b"220 127.0.0.1 Simple SMTP Service Ready\r\n")
        data_buffer = b""
        in_data_mode = False

        while self.running:
            try:
                line = b""
                while not line.endswith(b"\r\n"):
                    chunk = conn.recv(1024)
                    if not chunk:
                        return
                    line += chunk
            except Exception:
                return

            if in_data_mode:
                data_buffer += line
                if data_buffer.endswith(b"\r\n.\r\n"):
                    raw_email = data_buffer[:-5]
                    msg = message_from_bytes(raw_email)
                    self.received_messages.append(msg)
                    conn.sendall(b"250 2.0.0 OK: message queued\r\n")
                    in_data_mode = False
                    data_buffer = b""
            else:
                cmd = line.decode('utf-8', errors='ignore').strip()
                cmd_upper = cmd.upper()
                if cmd_upper.startswith("EHLO") or cmd_upper.startswith("HELO"):
                    conn.sendall(b"250-127.0.0.1 Hello\r\n250-AUTH PLAIN LOGIN\r\n250 HELP\r\n")
                elif cmd_upper.startswith("AUTH"):
                    conn.sendall(b"235 2.7.0 Authentication successful\r\n")
                elif cmd_upper.startswith("MAIL FROM:"):
                    conn.sendall(b"250 2.1.0 Sender OK\r\n")
                elif cmd_upper.startswith("RCPT TO:"):
                    conn.sendall(b"250 2.1.5 Recipient OK\r\n")
                elif cmd_upper.startswith("DATA"):
                    in_data_mode = True
                    conn.sendall(b"354 Start mail input; end with <CRLF>.<CRLF>\r\n")
                elif cmd_upper.startswith("QUIT"):
                    conn.sendall(b"221 2.0.0 Bye\r\n")
                    conn.close()
                    return
                elif cmd_upper.startswith("RSET"):
                    conn.sendall(b"250 2.0.0 OK\r\n")
                elif cmd_upper.startswith("NOOP"):
                    conn.sendall(b"250 2.0.0 OK\r\n")
                else:
                    conn.sendall(b"250 2.0.0 OK\r\n")

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass


@pytest.fixture
def smtp_server():
    server = LocalSMTPServer()
    yield server
    server.close()


def setup_smtp_settings(app, port):
    with app.app_context():
        conn = get_connection(app.config["DATABASE_PATH"])
        ensure_schema(conn)
        
        settings = [
            ("mail_server", "127.0.0.1"),
            ("mail_port", str(port)),
            ("mail_username", "alerts@suprajit.local"),
            ("mail_password", encrypt_password("dummy_password")),
            ("mail_use_tls", "0"),
            ("public_portal_url", "https://quality.suprajit.com"),
            ("developer_email", "devops@canspirit.com"),
        ]
        for k, v in settings:
            conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (k, v))
        conn.commit()
        conn.close()


def test_send_password_reset_email_live_smtp(app, smtp_server):
    """
    Exercises send_password_reset_email against a real local SMTP socket.
    Asserts headers, recipient, and dynamically generated reset token URL.
    """
    setup_smtp_settings(app, smtp_server.port)

    with app.app_context():
        success = send_password_reset_email("operator@tvs.com", 101)
        assert success is True

    time.sleep(0.2)
    assert len(smtp_server.received_messages) == 1
    msg = smtp_server.received_messages[-1]
    assert msg["To"] == "operator@tvs.com"
    assert msg["From"] == "alerts@suprajit.local"
    assert "Password Reset" in msg["Subject"]
    
    body = str(msg.get_payload()).replace("\r\n", "\n")
    assert "https://quality.suprajit.com/reset-password/" in body
    assert "This link is valid for 1 hour." in body


def test_send_welcome_email_live_smtp(app, smtp_server):
    """
    Exercises send_welcome_email against a real local SMTP socket.
    Asserts credentials and login link placement.
    """
    setup_smtp_settings(app, smtp_server.port)

    with app.app_context():
        success = send_welcome_email("john.doe@mahindra.com", "johndoe", "SecretTempPass987!")
        assert success is True

    time.sleep(0.2)
    assert len(smtp_server.received_messages) == 1
    msg = smtp_server.received_messages[-1]
    assert msg["To"] == "john.doe@mahindra.com"
    assert "Your Login Info" in msg["Subject"]
    
    body = str(msg.get_payload()).replace("\r\n", "\n")
    assert "Your Username: johndoe" in body
    assert "Your Temporary Password: SecretTempPass987!" in body
    assert "https://quality.suprajit.com/login" in body


def test_send_bulk_invite_email_live_smtp(app, smtp_server):
    """
    Exercises send_bulk_invite_email against a real local SMTP socket.
    Asserts company branding and invitation instructions.
    """
    setup_smtp_settings(app, smtp_server.port)

    with app.app_context():
        success = send_bulk_invite_email(
            user_email="qa_lead@tata.com",
            username="tata_qa_lead",
            raw_password="TemporaryTataPass456!",
            company_name="Tata Motors Quality Division"
        )
        assert success is True

    time.sleep(0.2)
    assert len(smtp_server.received_messages) == 1
    msg = smtp_server.received_messages[-1]
    assert msg["To"] == "qa_lead@tata.com"
    assert "Invitation to Suprajit Quality Inspection Portal" in msg["Subject"]
    
    body = str(msg.get_payload()).replace("\r\n", "\n")
    assert "on behalf of Tata Motors Quality Division" in body
    assert "Username  : tata_qa_lead" in body
    assert "Temporary Password: TemporaryTataPass456!" in body
    assert "https://quality.suprajit.com/login" in body


def test_send_heartbeat_email_live_smtp(app, smtp_server):
    """
    Exercises send_heartbeat_email against a real local SMTP socket.
    Asserts developer telemetry fields, sync status, and error payload.
    """
    setup_smtp_settings(app, smtp_server.port)

    with app.app_context():
        success = send_heartbeat_email(
            files_processed=1420,
            files_failed=3,
            status="PARTIAL_SUCCESS",
            error_msg="Zero-byte quarantine on 3 corrupt files"
        )
        assert success is True

    time.sleep(0.2)
    assert len(smtp_server.received_messages) == 1
    msg = smtp_server.received_messages[-1]
    assert msg["To"] == "devops@canspirit.com"
    assert "[PARTIAL_SUCCESS] Suprajit Portal Telemetry" in msg["Subject"]
    
    body = str(msg.get_payload()).replace("\r\n", "\n")
    assert "Sync Status: PARTIAL_SUCCESS" in body
    assert "Files Processed: 1420" in body
    assert "Files Failed: 3" in body
    assert "CRITICAL ERROR LOG:\nZero-byte quarantine on 3 corrupt files" in body