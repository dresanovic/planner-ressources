# Räume aus CAMPUSonline importieren

Die ausführliche Betriebsanleitung mit Einleitung, Backup, Serverbefehlen und
ausfüllbarem Laufprotokoll liegt unter [docs/Datenimport.md](../../docs/Datenimport.md).

Lehrenden- und LV-Dateien sowie deren Import sind in
[Abschnitt 9 der Anleitung](../../docs/Datenimport.md#9-lehrende-und-lv-grundlage-für-2027-s)
beschrieben. Die [LV-Gesamtliste](courses-overview.md) umfasst nach Ausschluss von Bachelorprüfungen, Masterarbeit und Masterprüfung 95 LVs aus 2026 S
als Grundlage für 2027 S. `lecturers.json` enthält 73 Personen. Der neue Import
verwendet `backend/scripts/import_academic_data.py` zusammen mit `import_rooms.py`.

Das wiederverwendbare Skript liegt unter `backend/scripts/import_rooms.py`.
Es benötigt Python 3.10 oder neuer und ausschließlich die Python-Standardbibliothek.
Es schreibt über die vorhandene Planer-API, niemals direkt in die Datenbank.

## Verhalten

- Eingabe ist der unveränderte CAMPUSonline-JSON-Export mit `resource[].content.MEINE_RAUM_V`.
- `RAUMCODE` wird zum `referenceCode`; der Name lautet `RAUMCODE – GEBAEUDE`.
- Nur eine positive ganzzahlige `SITZPLAETZE` wird als Kapazität übernommen.
- Räume ohne gültige Kapazität werden mit Begründung im Bericht ausgelassen.
- Identische Quelldubletten werden zusammengeführt. Widersprüchliche Dubletten stoppen den Lauf vor dem Import.
- Vor einem Online-Lauf werden sämtliche vorhandenen Räume gelesen, auch inaktive.
- Referenzcodes werden ohne äußere Leerzeichen und ohne Beachtung der Groß-/Kleinschreibung verglichen.
- Identische aktive Räume werden wiederverwendet. Abweichende Namen/Kapazitäten oder inaktive Einträge werden als Konflikt gemeldet und nicht geändert. Andere neue Räume können trotzdem angelegt werden.
- Das Skript aktualisiert, löscht oder reaktiviert keine vorhandenen Räume.
- Jeder Lauf erhält einen eigenen JSON-Bericht in `import-reports` neben der Eingabedatei; mit `--report-dir` ist ein anderes Ziel möglich.
- Nach jeder erfolgreichen Anlage werden Status und Planer-ID protokolliert. Zum Schluss werden die angelegten/wiederverwendeten Räume erneut über die API geprüft.
- Bei Fehlern stoppt der Lauf. Bereits angelegte Räume bleiben erhalten. Nach Klärung kann derselbe Befehl erneut ausgeführt werden: vorhandene Räume werden neu abgeglichen, sodass auch eine verlorene POST-Antwort nicht zu blindem Wiederholen führt.
- Die Originaldatei bleibt unverändert. Gebäude, Fläche und Stockwerk werden nicht als eigene Datenfelder importiert.

## Dateien auf den Server übertragen

In PowerShell auf dem Entwicklungs-PC, im Projektverzeichnis:

```powershell
scp -P 17655 backend/scripts/import_rooms.py artifacts/export-import/rooms.json admin_b50578@10.155.11.130:~/
```

Anschließend auf `si-resp-01`:

```bash
python3 --version
python3 ~/import_rooms.py ~/rooms.json
```

Dieser erste Aufruf prüft ausschließlich die Datei. Es erfolgt kein Zugriff auf den Planer.
Beim geprüften Export vom 03.11.2026 werden 121 gültige unterschiedliche Räume erwartet,
103 ohne gültige Kapazität ausgelassen und 2 identische Zusatzzeilen entfernt.

## Online-Vorschau und Import

Ersetze `https://PLANER-ADRESSE` durch die HTTPS-Basisadresse deiner Planer-Anwendung
(ohne `/api`, ohne Login-Seite). `DEIN_PLANER_LOGIN` ist das Konto der Anwendung,
nicht automatisch der Linux-/sudo-Benutzer. Eine Administratorrolle ist für die
Raumverwaltung nicht erforderlich; ein aktives Planer-Konto genügt.

```bash
python3 ~/import_rooms.py ~/rooms.json --base-url https://PLANER-ADRESSE --username DEIN_PLANER_LOGIN
```

Das Passwort wird verdeckt abgefragt, nicht als Befehlsargument übergeben und nicht
gespeichert. Die Online-Vorschau meldet `would_create`, `existing` und `conflict`.
Prüfe den ausgegebenen Bericht vor dem Import.

Zum tatsächlichen Anlegen:

```bash
python3 ~/import_rooms.py ~/rooms.json --base-url https://PLANER-ADRESSE --username DEIN_PLANER_LOGIN --apply
```

Die Anmeldung erzeugt eine neue Sitzung und beendet nach den Regeln des Planers
eine bisherige Sitzung desselben Kontos. Das Skript meldet seine Sitzung am Ende
wieder ab. Cookies bleiben nur im Arbeitsspeicher. Während des Imports keine
zweite Anmeldung mit demselben Konto durchführen.

HTTPS-Zertifikate werden regulär geprüft. Für lokale Entwicklungsinstanzen ist
HTTP ausschließlich mit `localhost`, `127.0.0.1` oder `::1` zulässig. Produktions-
Sitzungscookies benötigen HTTPS; ein Aufruf über `http://localhost` ist daher kein
Ersatz für die HTTPS-Adresse einer Produktionsinstanz.

Optional kann ein Automatisierungsprozess das Passwort über eine Umgebungsvariable
bereitstellen und deren Namen mit `--password-env VARIABLE` angeben. Keine
Passwörter in Skripten, Berichten oder Kommandozeilen speichern.

Exitcodes: `0` erfolgreich/konfliktfrei, `1` Fehler oder Abbruch, `2` Lauf beendet,
aber vorhandene Räume haben Konflikte. Bei `2` können andere Räume bereits angelegt
worden sein. Ein Bericht mit `status=completed` und `verified=true` bestätigt die
erfolgreiche Rückprüfung aller angelegten und identisch vorhandenen Räume;
Konflikte bleiben davon ausgenommen.

## Alternative ohne Python-Installation auf dem Host

Wenn `python3` auf dem Server nicht verfügbar ist, können die zwei Dateien in den
bestehenden Container kopiert und dort ausgeführt werden (kein neues Image nötig):

```bash
sudo docker cp ~/import_rooms.py planner-ressources-poc:/tmp/import_rooms.py
sudo docker cp ~/rooms.json planner-ressources-poc:/tmp/rooms.json
sudo docker exec -it planner-ressources-poc python /tmp/import_rooms.py /tmp/rooms.json --base-url http://127.0.0.1:8080 --username daniel --report-dir /data/import-reports
```

Nach Prüfung denselben Befehl mit zusätzlichem `--apply` ausführen. Der Container
muss die HTTPS-Adresse erreichen und ihrem Zertifikat vertrauen können. Die
Berichte liegen im persistenten `/data`-Volume.

## Tests

```powershell
backend/.venv/Scripts/python.exe -m unittest discover -s backend/tests/scripts -p test_import_rooms.py -v
```
