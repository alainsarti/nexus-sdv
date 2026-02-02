#!/bin/bash

# Wir versuchen, einen Token zu finden (entweder aus der Umgebung oder dem gh-Speicher)
CURRENT_TOKEN=$(gh auth token 2>/dev/null)

if [ -z "$CURRENT_TOKEN" ]; then
    echo "-------------------------------------------------------"
    echo "FEHLER: Kein Token gefunden!"
    echo "Bitte logge dich mit 'gh auth login' ein."
    echo "-------------------------------------------------------"
    exit 1
fi

# Validierung: Funktioniert der Token auch?
# Wir nutzen deine manuelle Abfrage als Test:
USER_LOGIN=$(gh api user -q .login 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "FEHLER: Token vorhanden, aber API-Abfrage fehlgeschlagen (evtl. abgelaufen)."
    exit 1
else
    echo "Check: Erfolgreich eingeloggt als $USER_LOGIN"
fi