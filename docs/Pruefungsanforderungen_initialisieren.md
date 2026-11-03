# Prüfungsanforderungen automatisch initialisieren

Das Skript `backend/scripts/initialize_exam_requirements.py` benötigt Python 3.10
oder neuer, keine zusätzlichen Python-Pakete und Zugriff auf die laufende
Planner-API. Alle folgenden Aufrufe erfolgen im Projektverzeichnis.

Es legt fehlende Prüfungsanforderungen für ein ausgewähltes Semester an:

- Dauer: **90 Minuten = 2 UE à 45 Minuten, ohne Pause**.
- Prüfungsart: **Schriftlich**, Bezeichnung: **Prüfung**.
- Verantwortliche Lehrperson: die bei der LV angezeigte Lehrperson. Sind mehrere
  zugeordnet, ist das gemäß bestehender LV-Anzeige die erste Zuordnung.
- Benötigte Raumkapazität: **Gruppengröße der LV**. Es wird kein Raum gebucht;
  die Kapazität eines bestehenden Lehrraums wird nicht als Teilnehmerzahl benutzt.
- Kein fester Prüfungszeitraum, keine Termine, keine Planungsversion.

Vorhandene Anforderungen bleiben unverändert, einschließlich deaktivierter
Anforderungen. Fehlende/inaktive Lehrpersonen und ungültige Gruppengrößen werden
mit Grund übersprungen. Der Bericht führt auch LVs auf, die wegen inaktiver
Stammdaten nicht initialisiert werden können. Fehlende Lehrtermine verhindern das
Anlegen der Anforderungen nicht.

## Aufrufe unter Windows

Die folgenden Beispiele nutzen die vorhandene Projekt-Python-Umgebung.
Alternativ kann `python` oder unter Windows `py -3` verwendet werden.
`https://planner.example.org` durch die eigene Planner-Basis-URL ersetzen, ohne
`/api`. Lokal ist beispielsweise `http://localhost:8000` möglich. `mein.login`
durch den Planner-Anmeldenamen ersetzen.

Semester-IDs anzeigen:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/initialize_exam_requirements.py --base-url https://planner.example.org --username mein.login
```

Vorschau für Semester-ID 7, ohne Anforderungen zu speichern:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/initialize_exam_requirements.py --base-url https://planner.example.org --username mein.login --semester-id 7 --report tmp/pruefungen-vorschau.json
```

Anforderungen tatsächlich anlegen:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/initialize_exam_requirements.py --base-url https://planner.example.org --username mein.login --semester-id 7 --apply --report tmp/pruefungen-ergebnis.json
```

Das Passwort wird verdeckt abgefragt. Anmeldung und Abmeldung erfolgen auch bei
der Vorschau. Eine Skriptanmeldung ersetzt eine bestehende Browser-Sitzung
desselben Kontos; anschließend gegebenenfalls im Browser neu anmelden.
Für `--report` muss der Zielordner bereits existieren.

Die Schreibausführung erstellt eine neue Vorschau aus den aktuellen Daten; sie
liest keine zuvor gespeicherte Vorschaudatei ein. Vor jedem Speichern werden die
Quellwerte erneut geprüft. Zwischenzeitlich geänderte Datensätze werden
übersprungen. Ein Abbruch kann bereits angelegte Anforderungen hinterlassen;
erneute Ausführung überspringt diese automatisch. Bei einer gleichzeitig neu
angelegten Anforderung schützt die API vor dem Überschreiben.

Statuswerte: `would_create` = würde angelegt, `created` = angelegt,
`existing` = bereits vorhanden, `skipped` = übersprungen,
`failed_or_unknown` = Fehler oder unklarer Ausgang; vor Wiederholung Bestand
erneut lesen. Ohne JSON-Bericht wird das Ergebnis im Terminal angezeigt.

Exitcodes: `0` = erfolgreich, `1` = Abbruch/Fehler, `2` = einzelne LVs übersprungen.

## Prüfung der Implementierung

```powershell
.\backend\.venv\Scripts\python.exe -m unittest discover -s backend/tests/scripts -p test_initialize_exam_requirements.py
```
