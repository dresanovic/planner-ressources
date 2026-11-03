# Datenimport aus CAMPUSonline in den Ressourcenplaner

Die abgeschlossene lesende Prüfung des Live-Anwendungsstands ist unter
[Importpruefung_2027_S.md](Importpruefung_2027_S.md) dokumentiert: 94 LVs,
73 Lehrende, 121 Räume, zehn Kohorten und 15 freie Tage wurden vollständig abgeglichen.

Stand: 03.11.2026. Diese Anleitung beschreibt den wiederholbaren Raumimport und
den aktuellen Stand der Vorbereitung für das Semester **2027 S**.

## 1. Einleitung und Ausgangslage

Der Ressourcenplaner wird für **2027 S, 19.02.2027 bis 17.08.2027**, vorbereitet.
Das Semester, die zehn Kohorten sowie die Studienformen **Vollzeit** und
**Berufsbegleitend** wurden bereits manuell angelegt. Diese Einträge sollen bei
weiteren Importen wiederverwendet werden.

Die zehn Kohorten sind:

| Studiengang | Fachsemester / jeweils getrennte Gruppen |
|---|---|
| Business Analytics & AI | 2., 4., 6. |
| Business Software Development | 2., 4., 6. |
| MA IT & Wirtschaftsinformatik | 2. |
| Wirtschaftsinformatik | 2., 4., 6. |

Eine Kohorte bezeichnet eine konkrete Studierendengruppe. Das Fachsemester der
Gruppe ist vom Planungszeitraum „2027 S“ zu unterscheiden. Die Verbindung zwischen
Kohorte und Planungszeitraum entsteht über die Lehrveranstaltungen.

Die Stammdaten stammen aus dem loginpflichtigen CAMPUSonline-System. Entgegen der
anfänglichen Annahme konnte für Räume ein JSON-Export gefunden und heruntergeladen
werden. Der ursprüngliche Export liegt in
`artifacts/export-import/rooms.json`.

Die vollständige Prüfung dieses Exports ergab:

| Merkmal | Ergebnis |
|---|---:|
| Quellzeilen | 226 |
| Unterschiedliche Raumcodes | 224 |
| Unterschiedliche Räume mit gültiger Kapazität | 121 |
| Unterschiedliche Räume ohne Kapazitätsangabe | 103 |
| Identische zusätzliche Zeilen | 2: CE404 und CE405 |

Für den Import wurde `backend/scripts/import_rooms.py` erstellt. Das Skript
verwendet die vorhandene Planer-API und schreibt nicht direkt in die Datenbank.
Der Benutzer hat die erfolgreiche Ausführung auf dem Server einschließlich des
tatsächlichen Befehls und der Ausgabe nachgereicht: 121 Räume wurden neu angelegt.
Der funktionierende Weg führt über SSH auf Port 17655 und den Import im laufenden
Docker-Container. Die bestätigten Werte sind unten dokumentiert; noch unbekannte
Details des ursprünglichen Exports bleiben im Protokoll zum Nachtragen markiert.

## 2. Bekannte Umgebung und Dateien

| Bestandteil | Wert |
|---|---|
| Quellsystem | [CAMPUSonline CAMPUS 02](https://online.campus02.at/C02online/ee/ui/ca2/app/desktop/#/home?$ctx=lang=DE) |
| Server | `si-resp-01` |
| Bestätigte SSH-Adresse | `10.155.11.130` |
| SSH-Port | `17655` |
| Linux-Benutzer | `admin_b50578` |
| Laufender Container beim ersten Import | `planner-ressources-poc` |
| Bestätigte API-Basisadresse im Container | `http://127.0.0.1:8080` |
| Anwendungskonto für den Import | `daniel` |
| Planer-Adresse im Browser / vom Server-Host aus | Noch nicht dokumentiert; nicht mit der Container-Loopback-Adresse gleichsetzen |
| Importskript im Repository | `backend/scripts/import_rooms.py` |
| Originalexport im Repository | `artifacts/export-import/rooms.json` |
| Technische Kurzbeschreibung | `artifacts/export-import/README.md` |
| Tests | `backend/tests/scripts/test_import_rooms.py` |

Die Dateipfade in der Tabelle beziehen sich auf das Repository. Auf dem
Entwicklungs-PC liegt es unter `C:\Codex\planner-resource`.
Anwendungslogin und Linux-/sudo-Benutzer sind unterschiedliche Konten.
Passwörter, Sitzungscookies und andere Zugangsdaten gehören nicht in dieses Dokument.

### 2.1 Welcher Befehl läuft wo?

| Aufgabe | Ausführungsort | Erkennbar am Prompt |
|---|---|---|
| Dateien mit `scp` übertragen | Lokale PowerShell auf dem Windows-PC | `(base) PS C:\Codex\planner-resource>` |
| Mit `ssh` am Server anmelden | Lokale PowerShell auf dem Windows-PC | `(base) PS ...>` |
| Backup, `docker cp`, `docker exec` | SSH-Sitzung auf dem Server | `admin_b50578@si-resp-01:~$` |
| Python-Import im Container | Vom Server aus mit `sudo docker exec -it ...` starten | Passwortabfrage des Skripts nach dem Docker-Aufruf |

**Lokaler Windows-PC:**

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 backend/scripts/import_academic_data.py backend/scripts/import_rooms.py artifacts/export-import/lecturers.json admin_b50578@10.155.11.130:~/
ssh -p 17655 admin_b50578@10.155.11.130
```

`scp` verwendet ein großes `-P`, `ssh` ein kleines `-p`. Port 22 hat bei der
Übertragung `Connection refused` geliefert. Der bestätigte Zugang ist Port 17655
an der genannten IP-Adresse. Der SSH-Port ist kein API-Port.

Für die aktuelle PoC-Installation die konkreten Container-Befehle in Abschnitt 5
(Räume) beziehungsweise 9.6 (Lehrende und LVs) verwenden. Die folgenden
Host-Python-Beispiele mit `https://PLANER-ADRESSE` sind eine alternative Ausführungsart
und benötigen eine tatsächlich erreichbare HTTPS-Adresse. Platzhalter nicht
unverändert ausführen.

`127.0.0.1` bezeichnet immer die Umgebung, in der Python läuft. Die bestätigte
Adresse `http://127.0.0.1:8080` gehört hier zum Planer-Container und ist keine
bestätigte Browseradresse auf dem Windows-PC oder API-Adresse vom Server-Host aus.

## 3. Was das Raumskript übernimmt

### Feldzuordnung

| CAMPUSonline | Planer-API | Beispiel |
|---|---|---|
| `RAUMCODE` | `referenceCode` | `CC202` |
| `RAUMCODE` + `GEBAEUDE` | `name` | `CC202 – Campus Classic` |
| `SITZPLAETZE` | `capacity` | `56` |

Erwartete JSON-Struktur: `resource[].content.MEINE_RAUM_V`.
Wenn das Gebäude fehlt, wird nur der Raumcode als Name verwendet.
Fläche und Stockwerk werden nicht als eigene Felder übernommen. Gebäude und
Stockwerk sind auch keine zusätzlichen Abhängigkeiten, die vorher angelegt werden müssen.

### Importregeln

- Nur positive ganzzahlige Sitzplatzzahlen werden übernommen. Fehlende Werte,
  Null, negative Zahlen oder Zahlen als Zeichenfolge werden ausgelassen.
- Ein Referenzcode muss vorhanden und höchstens 100 Zeichen lang sein; ein
  erzeugter Raumname darf höchstens 200 Zeichen haben.
- Identische Quelldubletten werden zusammengeführt. Widersprüchliche Daten für
  denselben Code stoppen den Lauf vor dem Import.
- Vor dem Online-Import werden alle vorhandenen Räume einschließlich inaktiver
  Einträge gelesen. Referenzcodes werden ohne äußere Leerzeichen und unabhängig
  von Groß-/Kleinschreibung verglichen.
- Ein vorhandener aktiver Raum mit gleichem Namen und gleicher Kapazität wird
  wiederverwendet. Abweichende oder inaktive Einträge werden als Konflikt gemeldet.
- Das Skript legt nur fehlende Räume an. Es ändert, reaktiviert oder löscht keine
  vorhandenen Räume. Konflikte verhindern nicht die Anlage anderer neuer Räume.
- Jede Raum-Anlage ist eine eigene API-Transaktion. Ein Fehler kann deshalb einen
  teilweise abgeschlossenen Import hinterlassen.
- Wiederholungen gleichen den aktuellen Serverbestand erneut ab. So lassen sich
  abgebrochene Läufe fortsetzen, ohne erfolgreiche Anlagen blind zu wiederholen.

Räume sind semesterübergreifende Stammdaten. Sie werden nicht für jedes Semester
neu angelegt. Der Import stellt noch keine Zuordnung zu Lehrveranstaltungen her.
Er enthält auch keine Raumbelegungen, Ausstattung oder Nichtverfügbarkeiten.

## 4. Schrittfolge für einen neuen Import

### Schritt 1: Quellstand sichern

1. Selbst in CAMPUSonline anmelden und die Raumexport-Funktion öffnen.
2. Den gewünschten Umfang prüfen und den Export als JSON herunterladen.
3. Den Originalexport unverändert aufbewahren und Exportzeitpunkt sowie Filter
   im Protokoll unter Abschnitt 8 dokumentieren.
4. Die neue Datei als `rooms.json` im lokalen Arbeitsverzeichnis bereitstellen.
   Einen früheren Originalexport vorher unter einem datierten Namen archivieren.

Der genaue Menüpfad der gefundenen Exportfunktion und die gewählten Filter sind
noch nachzutragen. Aus der Datei allein lässt sich nicht bestätigen, dass alle
benötigten beziehungsweise alle tatsächlich geeigneten Räume enthalten sind.

### Schritt 2: Datenbankbackup erstellen

Auf dem Server zuerst den aktuellen Containernamen prüfen:

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Für den bekannten Container:

```bash
sudo docker exec planner-ressources-poc python scripts/backup_sqlite_db.py --output-dir /data/backups
```

Die Erfolgsausgabe lautet `Backup created: /data/backups/DATEINAME.db`.
Das vorhandene Skript verwendet die SQLite-Backupfunktion und prüft anschließend
die Integrität der Sicherung. Den ausgegebenen Dateinamen im Protokoll festhalten.

Optional eine zusätzliche Kopie aus dem Container-Volume ins Server-Home kopieren.
`DATEINAME.db` durch den soeben ausgegebenen Namen ersetzen:

```bash
sudo docker cp planner-ressources-poc:/data/backups/DATEINAME.db "$HOME/DATEINAME.db"
```

Eine Kopie im Server-Home befindet sich weiterhin auf demselben Server. Für eine
Sicherung außerhalb dieses Servers muss sie zusätzlich auf ein anderes Ziel kopiert werden.

Das vor dem ersten Import bestätigte Backup lautet:
`/data/backups/planner-20261103-100307.db`.
Bei späteren Importen ein neues Backup erstellen; diesen alten Namen nicht übernehmen.

### Schritt 3: Skript und Export auf den Server übertragen

Auf dem Entwicklungs-PC in PowerShell:

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 backend/scripts/import_rooms.py artifacts/export-import/rooms.json admin_b50578@10.155.11.130:~/
```

Auf dem Server ein eigenes Verzeichnis je Lauf anlegen und beide Dateien archivieren:

```bash
IMPORT_RUN="$HOME/planner-imports/rooms-$(TZ=Europe/Vienna date +%Y%m%d-%H%M%S)"
mkdir -p "$IMPORT_RUN"
cp "$HOME/import_rooms.py" "$HOME/rooms.json" "$IMPORT_RUN/"
printf '%s\n' "$IMPORT_RUN"
sha256sum "$IMPORT_RUN/import_rooms.py" "$IMPORT_RUN/rooms.json"
```

Den Verzeichnispfad und die Prüfsummen im Protokoll festhalten. Die Variable
`IMPORT_RUN` gilt in dieser Shell; bei einer neuen SSH-Sitzung auf den tatsächlich
verwendeten Verzeichnispfad setzen. Das archivierte Skript ermöglicht auch nach
späteren Änderungen die Zuordnung von Ergebnis und Skriptversion.

### Schritt 4: Offline-Vorschau prüfen

Auf dem Server ist Python 3.10 oder neuer erforderlich. Zusätzliche Python-Pakete
werden nicht benötigt.

```bash
python3 --version
python3 "$IMPORT_RUN/import_rooms.py" "$IMPORT_RUN/rooms.json"
```

Ohne `--base-url` erfolgt kein Zugriff auf die Anwendung. Die Ausgabe zeigt die
gültigen Kandidaten, ausgelassenen Räume und entfernten Dubletten. Zusätzlich
entsteht ein Bericht unter `$IMPORT_RUN/import-reports/`.

Beim ursprünglichen Export wurden 121 Kandidaten, 103 ausgelassene Räume und
2 entfernte Zusatzzeilen festgestellt. Diese Zahlen gelten für diesen Export,
nicht als feste Vorgabe für spätere Exporte.

### Schritt 5: Online-Vorschau gegen den vorhandenen Planerbestand

Die Platzhalter durch die tatsächliche HTTPS-Basisadresse und den Planer-Login
ersetzen. Die Basisadresse enthält weder `/api` noch den Login-Seitenpfad.

```bash
python3 "$IMPORT_RUN/import_rooms.py" "$IMPORT_RUN/rooms.json" \
  --base-url https://PLANER-ADRESSE \
  --username DEIN_PLANER_LOGIN
```

Das Passwort wird verdeckt abgefragt. Die Vorschau schreibt keine Raumdaten,
meldet sich jedoch an der Anwendung an. Das beendet nach den Planer-Regeln eine
gegebenenfalls vorhandene Sitzung desselben Kontos. Das Skript meldet seine
Sitzung am Ende wieder ab. Während des Laufs nicht parallel mit demselben Konto anmelden.

Den Bericht prüfen:

| Ergebnis je Raum | Bedeutung / Entscheidung |
|---|---|
| `would_create` | Neuer Raum würde angelegt |
| `existing` | Identischer aktiver Raum ist vorhanden; wird wiederverwendet |
| `conflict` | Abweichender oder inaktiver Raum vorhanden; wird nicht verändert |
| `skipped` im Abschnitt `skipped` | Keine gültige Kapazität; wird nicht angelegt |

Vor dem Import den Umfang und etwaige Konflikte fachlich prüfen. Ob ein Raum für
die eigenen Lehrveranstaltungen geeignet ist, muss anhand der Planung geklärt werden.

### Schritt 6: Import ausführen

Mit denselben Dateien und derselben Zieladresse, nun mit `--apply`:

```bash
python3 "$IMPORT_RUN/import_rooms.py" "$IMPORT_RUN/rooms.json" \
  --base-url https://PLANER-ADRESSE \
  --username DEIN_PLANER_LOGIN \
  --apply
IMPORT_EXIT=$?
printf 'Import-Exitcode: %s\n' "$IMPORT_EXIT"
```

Der Exitcode wird unmittelbar nach dem Python-Aufruf erfasst. Für diesen Aufruf
ist kein `sudo` erforderlich, sofern der Benutzer die Dateien lesen und im
Laufverzeichnis schreiben kann.

### Schritt 7: Ergebnis prüfen und dokumentieren

Den zuletzt ausgegebenen Berichtspfad notieren. Jeder Aufruf erzeugt einen eigenen
Bericht; Offline-Vorschau, Online-Vorschau und tatsächlichen Import unterscheiden.

| Merkmal | Bedeutung |
|---|---|
| Exitcode `0` | Vorschau oder Import ohne gemeldete Konflikte erfolgreich beendet |
| Exitcode `1` | Fehler oder Abbruch; bereits angelegte Räume können vorhanden sein |
| Exitcode `2` | Lauf beendet, aber Konflikte vorhanden; andere Räume können bereits angelegt sein |
| `status: completed` | Import-Schleife wurde beendet |
| `verified: true` auf Berichtsebene | Angelegte und identisch vorhandene Räume wurden nochmals über die API geprüft; Konflikte sind ausgenommen |
| `created` | Neu angelegter Raum, einschließlich Planer-ID |
| `existing` | Wiederverwendeter Raum, einschließlich Planer-ID |
| `uncertain_or_failed` | Anlage fehlgeschlagen oder Ergebnis unklar; vor Wiederholung neu abgleichen |

`validUniqueRooms` ist die Zahl gültiger Quellräume, nicht automatisch die Zahl
neu angelegter Räume. Ein erneuter Lauf kann deshalb 121 gültige Räume melden,
obwohl alle bereits existieren und keine neuen Räume angelegt werden.

Zusätzlich in der Raumverwaltung einige importierte Codes, Namen und Kapazitäten
prüfen. Export, Skript, Berichte und Backup-Referenz zusammen archivieren und das
Protokoll ausfüllen. Berichtszeitstempel mit `Z` sind UTC; die Laufverzeichnisnamen
oben verwenden Europe/Vienna.

## 5. Bestätigter Ausführungsweg im Docker-Container

Diese Variante ist für die aktuelle PoC-Installation durch den Raumimport bestätigt.
Sie ersetzt die Python-Aufrufe auf dem Host; nicht beide Varianten zum Anlegen ausführen.
Die Dateien zuvor wie in Schritt 3 nach `~/` übertragen.

```bash
sudo docker cp ~/import_rooms.py planner-ressources-poc:/tmp/import_rooms.py
sudo docker cp ~/rooms.json planner-ressources-poc:/tmp/rooms.json
```

Offline-Vorschau:

```bash
sudo docker exec -it planner-ressources-poc python /tmp/import_rooms.py /tmp/rooms.json \
  --report-dir /data/import-reports
```

Online-Vorschau:

```bash
sudo docker exec -it planner-ressources-poc python /tmp/import_rooms.py /tmp/rooms.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports
```

Import nach Prüfung:

```bash
sudo docker exec -it planner-ressources-poc python /tmp/import_rooms.py /tmp/rooms.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
IMPORT_EXIT=$?
printf 'Import-Exitcode: %s\n' "$IMPORT_EXIT"
```

`-it` ermöglicht die verdeckte Passwortabfrage. Die Berichte liegen unter
`/data/import-reports` im persistenten Container-Volume. Die Eingaben in `/tmp`
sind dagegen keine dauerhafte Archivierung; Originaldateien auf dem Host behalten.
Bei Archivierung eines einzelnen Berichts dessen tatsächlich ausgegebenen Namen
für `BERICHT.json` einsetzen:

```bash
sudo docker cp planner-ressources-poc:/data/import-reports/BERICHT.json "$HOME/BERICHT.json"
```

## 6. Fehler behandeln und einen Lauf wiederholen

| Meldung / Situation | Vorgehen |
|---|---|
| `no configuration file provided` | `docker compose` wurde außerhalb des Compose-Verzeichnisses aufgerufen. Die hier dokumentierten `docker exec`-Befehle benötigen keine Compose-Datei. |
| Docker-Socket: `permission denied` | Auf diesem Server Docker-Befehle mit `sudo` ausführen. |
| `No such container` | Aktuellen Namen mit `sudo docker ps` prüfen und in den Befehlen ersetzen. |
| HTTP `401` | Planer-Zugang prüfen; bei Abbruch nach Anmeldung auch eine parallele Anmeldung oder abgelaufene Sitzung berücksichtigen. |
| HTTP `404` / unerwartete API-Antwort | Basisadresse und bereitgestellte Anwendungsversion prüfen. |
| Zertifikats-/Verbindungsfehler | Erreichbarkeit und Zertifikatsvertrauen auf dem ausführenden Host beziehungsweise im Container prüfen. |
| Fehlende Sitzplatzanzahl | Im Quellsystem oder fachlich klären und anschließend erneut exportieren; keine Kapazität erfinden. |
| `conflict` | Namen, Kapazität und Aktivstatus des vorhandenen Raums prüfen. Das Skript überschreibt den Eintrag nicht. |
| Verbindungsabbruch nach POST | Bericht behalten, Ursache klären und denselben Import erneut starten. Die neue Bestandsabfrage erkennt bereits erfolgte Anlagen. |

Für eine Produktionsinstanz die HTTPS-Adresse verwenden. Das Skript erlaubt HTTP
nur für lokale Adressen; Produktions-Sitzungscookies benötigen HTTPS. Eine
HTTP-Loopback-Adresse ist daher kein Ersatz für den Produktionszugang.

Ein Wiederholungslauf stellt den ursprünglichen Datenbankstand nicht wieder her.
Bereits erfolgreich angelegte Räume bleiben erhalten. Ein vollständiger Restore
ist ein separater Betriebsschritt und nicht Teil dieses Skripts. Die Datenbank
enthält auch Konten und Sitzungszustände; eine Wiederherstellung betrifft deshalb
mehr als nur die importierten Räume.

## 7. Weitere Stammdaten und Abhängigkeiten

| Datengruppe | Stand / nächster Schritt |
|---|---|
| Semester 2027 S | Manuell angelegt; wiederverwenden |
| Zehn Kohorten | Manuell angelegt; vorhandene IDs und Studierendenzahlen verwenden |
| Vollzeit / Berufsbegleitend | Manuell angelegt; wiederverwenden |
| Räume | Erfolgreicher Import durch Benutzer bestätigt; Details siehe Laufprotokoll |
| Lehrende | Erfolgreich importiert: `created=73`; Bericht `/data/import-reports/lecturers-20261103T112807Z-fc0cca88.json` |
| Zeitfenster der Studienformen | Vorhandenen Stand prüfen und fehlende Fenster ergänzen |
| Lehrveranstaltungen | 95 Einträge als Grundlage für 2027 S vorbereitet; erster Teilimport BAAI 2. Semester erfolgreich mit `created=10, skipped=85`; weitere Kohorten offen (Abschnitt 9) |

Eine Lehrveranstaltung benötigt in der vorhandenen Anlage-API Semester, Kohorte,
Studienform, einen geeigneten Lehrenden, einen ausreichend großen Raum und Angaben
zu Unterrichtseinheiten. Quellkennungen müssen den jeweiligen Planer-IDs zugeordnet
werden. Das Raumskript behandelt ausschließlich Räume; die übrigen Datengruppen
werden dadurch nicht automatisch angelegt oder verknüpft.

## 8. Importprotokoll

### Erster Raumimport am 03.11.2026

| Feld | Dokumentierter Stand |
|---|---|
| Zielserver / Container | `si-resp-01` / `planner-ressources-poc` |
| Zielsemester des Gesamtvorhabens | 2027 S; Räume selbst sind semesterunabhängig |
| Quelldatei | `artifacts/export-import/rooms.json` |
| Erwarteter Umfang nach Dateiprüfung | 121 gültige unterschiedliche Räume; 103 ohne Kapazität; 2 entfernte identische Zusatzzeilen |
| Vorheriges Backup | `/data/backups/planner-20261103-100307.db`; Erfolg und Integritätsprüfung bestätigt |
| Erfolgsmeldung | Benutzer bestätigt: erfolgreich importiert |
| Genaue Exportansicht / Filter / Exportzeitpunkt | Aus Nebenchat beziehungsweise Quellsystem nachtragen |
| Tatsächliche API-Adresse / Anwendungskonto | `http://127.0.0.1:8080` innerhalb des Containers / `daniel`; Anwendungsversion noch nachtragen |
| Ausführungsvariante und tatsächlicher Befehl | Container-Aufruf aus der SSH-Sitzung, siehe unten |
| Skriptversion / SHA-256 und Export-SHA-256 | Nachtragen; nicht aus später veränderten Dateien als damaligen Stand ableiten |
| Tatsächliches Ergebnis laut nachgereichter Ausgabe | `created=121`; gültige unterschiedliche Räume: 121; ausgelassen: 103; entfernte Zusatzzeilen: 2 |
| Berichtspfad | `/data/import-reports/rooms-20261103T102958Z-53f4ec92.json` |
| Exitcode / verified im Bericht | Noch aus dem Serverbericht nachtragen; in der Konsolenausgabe nicht enthalten |
| Manuelle Stichprobe / Abweichungen | Nachtragen |

Der Benutzer hat folgenden tatsächlichen Serverbefehl und dessen Erfolgsausgabe
nachgereicht. Damit sind 121 Neuanlagen durch die Konsolenausgabe bestätigt:

```bash
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_rooms.py /tmp/rooms.json \
  --base-url http://127.0.0.1:8080 \
  --username daniel \
  --report-dir /data/import-reports \
  --apply
```

```text
Valid unique rooms: 121; skipped: 103; duplicate rows removed: 2
Results: created=121
Report: /data/import-reports/rooms-20261103T102958Z-53f4ec92.json
```

### Vorlage für weitere Läufe

Diesen Abschnitt pro Lauf kopieren und ausfüllen. Keine Zugangsdaten eintragen.

| Feld | Eintrag |
|---|---|
| Laufdatum / Uhrzeit / Zeitzone | |
| Verantwortliche Person | |
| Anlass / Datengruppe / Bezug zum Semester | |
| Exportansicht, Menüpfad, Filter und Exportzeitpunkt | |
| Originaldatei / Archivpfad / SHA-256 | |
| Skriptpfad / Version oder Commit / SHA-256 | |
| Server / Container / Image-Version / Planer-Basisadresse | |
| Backup vor dem Lauf / zusätzliche Sicherungskopie | |
| Ausführungsvariante: Host oder Container | |
| Offline-Vorschau: Kandidaten / ausgelassen / Dubletten / Bericht | |
| Online-Vorschau: neu / vorhanden / Konflikte / Bericht | |
| Entscheidung zum Umfang / Umgang mit Konflikten | |
| Tatsächlich ausgeführter Importbefehl ohne Passwort | |
| Beginn / Ende / Exitcode | |
| Ergebnis: created / existing / conflict / skipped | |
| Berichtspfad / status / verified | |
| Stichprobe im Planer | |
| Fehler, Wiederholungen und vorgenommene Anpassungen | |
| Offene Punkte / nächster Schritt | |

### Abschlusscheck je Lauf

- [ ] Originalexport und verwendetes Skript archiviert.
- [ ] Backup vor dem Import erfolgreich erstellt und Pfad dokumentiert.
- [ ] Offline- und Online-Vorschau geprüft.
- [ ] Importbefehl, tatsächliches Ergebnis und Exitcode dokumentiert.
- [ ] Rückprüfung im Bericht und Stichprobe im Planer geprüft.
- [ ] Fehlende Kapazitäten und Konflikte als offene Punkte erfasst.
- [ ] Ergebnisberichte zusammen mit dem Laufprotokoll aufbewahrt.

## 9. Lehrende und LV-Grundlage für 2027 S

### 9.1 Quelle und bestätigte Entscheidungen

Am 03.11.2026 wurden die Vortragenden und Lehrveranstaltungen aus den vier vom
Benutzer genannten Studienplanversionen im angemeldeten Browser erfasst. Weil
die Lehrenden für 2027 S noch nicht eingetragen sind, wurde **2026 S** verwendet.
Im Browser entspricht das `objTermId=124`; `objTermId=125` bezeichnet 2026 W.

| Studienplan | Version-ID | Vollständig erfasste LV-Einträge |
|---|---:|---:|
| Business Analytics und Artificial Intelligence, Vollzeit, 2020W V3 | 349 | 22 |
| Business Software Development, Vollzeit, 2018W V5 | 362 | 29 |
| Informationstechnologien und Wirtschaftsinformatik, Master, Berufsbegleitend, 2021W V1 | 301 | 13 |
| Wirtschaftsinformatik, Bachelor, Berufsbegleitend, 2021W V1 | 297 | 36 |
| Gesamt | | **100** |

Für jede Liste wurden 100 Einträge pro Seite eingestellt und der vollständig
angezeigte Umfang geprüft. Alle 100 Quell-LVs haben eine Vortragendenrolle mit
auslesbaren Personenlinks. Die vier Listen enthalten **217 Person-LV-Zuordnungen**,
aus denen **73 unterschiedliche Personen** ermittelt wurden. Es wurden ausschließlich
Links unter „Vortragende*r“ übernommen; eine reine Koordinationsrolle reicht nicht aus.

Die letzte Komponente des Personenlinks wird als Quellkennung verwendet. Daraus
entsteht der Referenzcode `campus02:<Personenkennung>`. Die Kennung hat in dieser
Erfassung keine widersprüchlichen Namen. Ihre Stabilität bei späteren Exporten
ist erneut zu prüfen; sie ist keine bestätigte Personalnummer.

Der Benutzer hat bestätigt:

- Die LVs aus 2026 S sollen als Grundlage für **2027 S** übernommen werden.
- Notwendige Anpassungen werden anschließend manuell vorgenommen.
- Nicht ganzzahlige UE werden auf die nächstgelegene ganze Zahl gerundet;
  bei genau `.5` wird aufgerundet, beispielsweise `25.5 → 26`, `8.5 → 9`, `29.75 → 30`.

Auf zusätzlichen Benutzerwunsch wurden die drei Bachelorprüfungen, „Masterarbeit 1“
und die Masterprüfung aus dem aufbereiteten LV-Katalog, der lesbaren Liste und der
Import-Zuordnungsdatei entfernt. Die ursprünglichen 100 Quell-LVs bleiben in den
vier Quellnachweisen dokumentiert. Die Arbeitsliste enthält damit **95 LVs**.
Die Lehrenden-Stammliste bleibt mit ihren historischen Quellnachweisen erhalten;
hier wurden keine Personen gelöscht.

Die Rundung betrifft 40 LVs. Der ursprüngliche Gesamtumfang von 3013,25 UE wird
dadurch zu 3027 UE. Beide Werte bleiben über die gespeicherten Quelldaten und
den LV-Katalog nachvollziehbar. Die Quellzuordnungen aus 2026 S sind eine
Arbeitsgrundlage und keine bestätigte Lehrplanung für 2027 S.

### 9.2 Dateien und erneute Aufbereitung

| Datei | Zweck |
|---|---|
| `artifacts/export-import/lecturers-sources/curriculum-*-2026-S.json` | Vier Quellnachweise der sichtbaren LV-Listen, mit Namen, Personenkennungen, Rollenprüfung, Quell-UE, LV-Code und Quell-LV-ID |
| `artifacts/export-import/lecturers.json` | 73 eindeutige Lehrende mit Referenzcode und sämtlichen Quell-LVs |
| `artifacts/export-import/courses.json` | 95 LVs nach den vereinbarten Ausschlüssen, mit Quell- und gerundeten UE, Studienplan und Lehrendenreferenzen |
| [courses-overview.md](../artifacts/export-import/courses-overview.md) | Lesbare Liste aller LVs mit Vortragenden und beiden UE-Werten |
| `artifacts/export-import/courses-2027-S.mapping.json` | Editierbare Zielzuordnungen für 2027 S |
| `backend/scripts/prepare_campus_catalog.py` | Wiederholbare lokale Aufbereitung der vier gespeicherten Quelllisten |
| `backend/scripts/import_academic_data.py` | Wiederverwendbarer API-Import für Lehrende und LVs |
| `backend/scripts/import_rooms.py` | Muss neben dem neuen Importskript liegen; stellt dessen gemeinsamen HTTP-Client und Berichtsfunktionen bereit |

Die Browsererfassung ist ein Auslesen der sichtbaren Listen, kein offizieller
CAMPUSonline-JSON-Export. Für eine spätere Neuerfassung dieselben Studienplanversionen,
das richtige Quellsemester und den vollständigen Seitenumfang prüfen. Je LV werden
aus der angezeigten Karte Code, Titel, Typ, UE sowie ausschließlich die Personenlinks
der Vortragendenrolle gespeichert. Die vier Rohdateien bleiben als Nachweis erhalten.

Die vorhandenen Rohdateien lassen sich ohne Browserzugriff erneut aufbereiten.
Auf dem Entwicklungs-PC im Projektverzeichnis:

```powershell
backend/.venv/Scripts/python.exe backend/scripts/prepare_campus_catalog.py artifacts/export-import/lecturers-sources artifacts/export-import --target-semester "2027 S"
```

Das schreibt `lecturers.json`, `courses.json` und die Übersicht neu. Eine bereits
vorhandene Zuordnungsdatei behält ihre manuellen Korrekturen. Nur die ausdrücklich
ausgeschlossenen Bachelorprüfungs-, Masterarbeits- und Masterprüfungseinträge werden
auch aus einer vorhandenen Zuordnungsdatei entfernt. Wenn sich die übrigen Quell-LVs ändern, muss die alte Zuordnungsdatei
bewusst abgeglichen oder nach Archivierung neu erzeugt werden. Der Import verlangt,
dass die Zuordnungsdatei genau dieselben Quell-LV-IDs abdeckt wie `courses.json`.

### 9.3 Lehrende importieren

Zuerst wie in Abschnitt 4 ein neues Datenbankbackup erstellen. Danach die Dateien
vom Entwicklungs-PC auf den Server übertragen:

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 backend/scripts/import_academic_data.py backend/scripts/import_rooms.py artifacts/export-import/lecturers.json artifacts/export-import/courses.json artifacts/export-import/courses-2027-S.mapping.json admin_b50578@10.155.11.130:~/
```

Auf dem Server ein Laufverzeichnis anlegen:

```bash
ACADEMIC_RUN="$HOME/planner-imports/academic-$(TZ=Europe/Vienna date +%Y%m%d-%H%M%S)"
mkdir -p "$ACADEMIC_RUN"
cp ~/import_academic_data.py ~/import_rooms.py ~/lecturers.json ~/courses.json ~/courses-2027-S.mapping.json "$ACADEMIC_RUN/"
sha256sum "$ACADEMIC_RUN"/*.py "$ACADEMIC_RUN"/*.json
```

Offline-Vorschau für die Lehrenden:

```bash
python3 "$ACADEMIC_RUN/import_academic_data.py" lecturers "$ACADEMIC_RUN/lecturers.json"
```

Erwartet werden beim vorliegenden Datenstand 73 Kandidaten. Anschließend die
Online-Vorschau mit der echten HTTPS-Adresse und dem Anwendungslogin aufrufen:

```bash
python3 "$ACADEMIC_RUN/import_academic_data.py" lecturers "$ACADEMIC_RUN/lecturers.json" \
  --base-url https://PLANER-ADRESSE --username DEIN_PLANER_LOGIN
```

Nach Prüfung den Import starten:

```bash
python3 "$ACADEMIC_RUN/import_academic_data.py" lecturers "$ACADEMIC_RUN/lecturers.json" \
  --base-url https://PLANER-ADRESSE --username DEIN_PLANER_LOGIN --apply
IMPORT_EXIT=$?
printf 'Import-Exitcode: %s\n' "$IMPORT_EXIT"
```

Identische aktive Lehrende mit gleichem Referenzcode werden wiederverwendet.
Ein anderer Name, ein inaktiver Eintrag oder unklare Zuordnungen führen zu einem
Konflikt. Das neue Skript schreibt bei einer Vorprüfung mit Konflikten **gar keine
neuen Datensätze**. Anders als das Raumskript lässt es nicht parallel die anderen
Neuanlagen weiterlaufen. Vorhandene Einträge werden nicht geändert oder reaktiviert.

### 9.4 Zielzuordnungen der LVs ergänzen

Vor dem LV-Import die Datei `courses-2027-S.mapping.json` im verwendeten
Laufverzeichnis bearbeiten und archivieren. `semesterName` ist auf `2027 S` gesetzt.
Die API kennt keine externe LV-Referenz; deshalb enthält der vorbereitete Name
Titel, LV-Code und Zielsemester, beispielsweise `Algorithmen [0319BB2008] – 2027 S`.
Dieser Name dient bei Wiederholungen als Vergleichsschlüssel.

| Feld | Was zu tun ist |
|---|---|
| `sourceCourseId` / `code` | Quellidentität beibehalten; nicht die Planer-ID eintragen |
| `include` | `true` für Import, `false` für bewusst ausgelassene LV |
| `name` | Vorbereiteter eindeutiger Zielname; nach dem ersten Import für Wiederholung unverändert lassen |
| `cohortName` | Genauen Namen einer bereits angelegten Kohorte eintragen; die Zuordnung nicht allein aus der LV-Nummer erraten |
| `studyTypeName` | Aus dem Studienplan vorbelegt: Vollzeit oder Berufsbegleitend; prüfen |
| `lecturerReferenceCode` | Bei genau einem Vortragenden aus 2026 S vorbelegt; bei mehreren fehlt die Auswahl. Einen Wert aus `suggestedLecturerReferenceCodes` auswählen oder fachlich eine andere vorhandene Person zuordnen |
| `additionalLecturerReferenceCodes` | Optional: weitere ausdrücklich bestätigte Lehrende. Diese werden zusätzlich über die Ressourcenberechtigungs-API gespeichert und geprüft; keine Wiederholung der ersten Referenz |
| `suggestedLecturerReferenceCodes` | Historische Vorschläge aus 2026 S; diese Liste wird nicht automatisch als vollständige Ressourcenberechtigung importiert |
| `roomReferenceCode` | Vorhandenen geeigneten Raumcode, etwa `CC202`, eintragen |
| `additionalRoomReferenceCodes` | Optional: weitere ausdrücklich gewünschte geeignete Räume; werden gemeinsam mit den Lehrenden über die Ressourcenberechtigungs-API gespeichert und auf Kapazität geprüft |
| `totalUnits` | Nach Benutzervorgabe gerundeter UE-Wert; Originalwert bleibt in `courses.json` |
| `minSessionUnits` / `maxSessionUnits` | Gewünschte Grenzen der Unterrichtseinheiten je Termin festlegen; positive ganze Zahlen mit Minimum ≤ Maximum ≤ Gesamt-UE |
| `preferredSessionUnits` | Optionaler dokumentierter Wunschwert. Der vorhandene Optimierer bevorzugt die Mitte zwischen Minimum und Maximum; das Skript prüft die Übereinstimmung. Bei 2 und 4 ergibt sich der Wunschwert 3 |

Beispiel einer ergänzten Zuordnung; der Kohortenplatzhalter ist vor Verwendung
durch den tatsächlichen Namen zu ersetzen. Die Sitzungslängen sind Beispielwerte,
keine bestätigte Vorgabe für alle Lehrveranstaltungen:

```json
{
  "sourceCourseId": "117735",
  "code": "0319BB2008",
  "include": true,
  "name": "Algorithmen [0319BB2008] – 2027 S",
  "cohortName": "GENAUER KOHORTENNAME IM PLANER",
  "studyTypeName": "Berufsbegleitend",
  "lecturerReferenceCode": "campus02:3937638AF47C6DBE",
  "roomReferenceCode": "CC202",
  "totalUnits": 34,
  "minSessionUnits": 2,
  "maxSessionUnits": 4
}
```

Der Import löst Namen und Raum-/Lehrendenreferenzen zu den tatsächlichen Planer-IDs
auf. Die Stammdaten müssen eindeutig vorhanden und aktiv sein. Raumkapazität und
Studierendenzahl werden verglichen; die Studienform muss aktive Zeitfenster haben.

Pro LV wird zunächst ein ausgewählter Lehrender und ein ausgewählter Raum
angelegt. Ausdrücklich angegebene `additionalLecturerReferenceCodes` ergänzt das
Skript anschließend über `PUT /api/academic/courses/{id}/resource-eligibility`.
Ebenso ergänzt es angegebene `additionalRoomReferenceCodes`.
Es prüft danach die vollständige Menge der berechtigten Lehrenden und Räume.
Eine unterbrochene Ergänzung wird bei Wiederholung als `would_configure` erkannt
und ohne erneute LV-Anlage abgeschlossen; im Ergebnis erscheint `configured`.
Nicht vorgesehene vorhandene Ressourcen werden nicht entfernt, sondern als
Konflikt gemeldet. Weitere geeignete Ressourcen und geänderte Lehrzuordnungen können später
in der Verwaltung ergänzt werden. Die vollständige historische Personenliste geht
durch diese Auswahl nicht verloren, da sie in `courses.json` gespeichert bleibt.

Die folgenden fünf Einträge sind auf Benutzerwunsch vollständig aus der Arbeitsliste
und Zuordnungsdatei entfernt und bleiben nur in den ursprünglichen Quellnachweisen erhalten:

| Code | Titel |
|---|---|
| 0319BB6SO1 | Bachelorprüfung |
| 0320BB2023 | Masterarbeit 1 |
| 0320BB4SO1 | Masterprüfung |
| 0864VZ6SO1 | Bachelorprüfung |
| 0835VD6SO1 | Bachelorprüfung |

Der verbleibende 0-UE-Eintrag **0864VZ4003 – Accompanying Project** bleibt in der
95 Einträge umfassenden Liste enthalten und ist mit `include: false` markiert.
Die Lehrveranstaltungs-API verlangt positive Unterrichtseinheiten; diesen Eintrag
vor einer etwaigen Übernahme fachlich klären.

### 9.5 LVs für 2027 S importieren

#### Verbindliche Reihenfolge der Kohorten

Der Benutzer hat die Reihenfolge aus der Kohortenverwaltung vorgegeben:

1. Business Analytics & AI – 2. Semester
2. Business Analytics & AI – 4. Semester
3. Business Analytics & AI – 6. Semester
4. Business Software Development – 2. Semester
5. Business Software Development – 4. Semester
6. Business Software Development – 6. Semester
7. MA IT & Wirtschaftsinformatik – 2. Semester
8. Wirtschaftsinformatik – 2. Semester
9. Wirtschaftsinformatik – 4. Semester
10. Wirtschaftsinformatik – 6. Semester

Zunächst wird jede Kohorte einzeln vervollständigt, geprüft und importiert.
Der erste Teilimport ist lokal unter
`artifacts/export-import/courses-2027-S.batch-01-BAAI-2.mapping.json` vorbereitet.
Er enthält weiterhin alle 95 Quell-LV-IDs, aktiviert aber nur die zehn Codes
`0864VZ2001` bis `0864VZ2010`. Die Zuordnung zum 2. Fachsemester wird aus diesem
Codeschema abgeleitet und vor dem Import fachlich geprüft. Als Kohortenname ist
entsprechend dem Screenshot `Business Analytics & AI - 2.Semester` eingetragen;
die Online-Vorschau prüft, ob er im Planer eindeutig vorhanden ist.

Für diese erste Kohorte wurden inzwischen folgende Einstellungen bestätigt:

- Mindestens 2 UE, bevorzugt 3 UE, höchstens 4 UE je Termin, für alle zehn LVs.
- Mathematik 2: ausschließlich Hatzl, Johannes.
- Betriebswirtschaftslehre: Koch, Volker und Meglitsch, Mario.
- Business IT-Applications: Gerzic, Harris und Wipfler, Yevheniia.
- Die jeweils zwei Lehrenden teilen sich die Termine; die Verteilung erfolgt später
  manuell. Die Ressourcenberechtigung garantiert allein noch nicht, dass beide
  automatisch einen Anteil der Termine erhalten. Pro Termin ist genau eine Person vorgesehen.

Der Wunschwert 3 wird durch das vorhandene Optimierungsziel bei Grenzen 2 und 4
berücksichtigt; er ist keine zwingende Länge jedes Termins. Offen bleibt der
geeignete, ausreichend große Raum beziehungsweise dessen Referenzcode war zunächst offen.
Inzwischen hat der Benutzer 30 Studierende als Planungsannahme und eine Präferenz
für CZ- und RC-Räumlichkeiten angegeben. Für alle zehn LVs sind **CZ108 (45 Plätze)**
und **RC409 (78 Plätze)** aus `rooms.json` als zulässige Räume eingetragen.
Die Online-Vorschau verwendet die tatsächlich gespeicherte Studierendenzahl der
Kohorte; der Import ändert diese Zahl nicht automatisch auf 30.
Die beiden Räume sind eine erlaubte Auswahl, keine technisch gewichtete Rangfolge.
Eine Eignung aufgrund besonderer Ausstattung ist aus dem Export nicht nachgewiesen.
Vorhandene Einzelzuordnungen der übrigen Vortragenden aus 2026 S sind vorbelegt. Die
Hauptzuordnungsdatei wird durch das Erstellen dieses Teilimports nicht verändert.
Für die Befehle unten beim ersten Teilimport den Dateinamen hinter `--mapping`
durch `courses-2027-S.batch-01-BAAI-2.mapping.json` ersetzen und genau diese
Datei nach Bearbeitung auf den Server beziehungsweise in den Container übertragen.

Der vorbereitete erste Teilimport besteht die Offline-Prüfung mit
`candidate=10, skipped=85`. Vor dem Serverlauf muss das **aktualisierte**
`import_academic_data.py` übertragen werden, da es nun mehrere Lehrende und Räume unterstützt.

Lokale PowerShell:

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 backend/scripts/import_academic_data.py backend/scripts/import_rooms.py artifacts/export-import/courses.json artifacts/export-import/courses-2027-S.batch-01-BAAI-2.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/import_academic_data.py planner-ressources-poc:/tmp/import_academic_data.py
sudo docker cp ~/import_rooms.py planner-ressources-poc:/tmp/import_rooms.py
sudo docker cp ~/courses.json planner-ressources-poc:/tmp/courses.json
sudo docker cp ~/courses-2027-S.batch-01-BAAI-2.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-01-BAAI-2.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-01-BAAI-2.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports
```

Nach konfliktfreier Vorschau denselben letzten Befehl mit `--apply` ausführen.
Bei einem neuen Lauf das vorherige Backup und die verwendeten Dateien wie oben
beschrieben archivieren. Dieser Teilimport wurde inzwischen erfolgreich ausgeführt;
Ergebnis und Berichtspfad sind in Abschnitt 9.8 dokumentiert.

#### Prüfung und Ausführung

Zuerst offline die Vollständigkeit der bearbeiteten Zuordnung prüfen:

```bash
python3 "$ACADEMIC_RUN/import_academic_data.py" courses "$ACADEMIC_RUN/courses.json" \
  --mapping "$ACADEMIC_RUN/courses-2027-S.mapping.json"
```

Bei der unveränderten Vorlage ist **blocked=94, skipped=1** das erwartete Ergebnis:
Die Quellliste ist vollständig, aber die benötigten Zielzuordnungen sind noch offen.
Das bedeutet keine 94 fehlerhaften Quell-LVs. Die Vorlage enthält bewusst keine
erfundenen Kohorten, Räume oder Sitzungsgrößen.

Falls eine einheitliche Sitzungsgrenze fachlich gewünscht ist, kann sie alternativ
mit `--min-session-units N --max-session-units M` angegeben werden. Das gilt nur
für Zuordnungszeilen, in denen diese Werte noch `null` sind. Beide Optionen bei
Vorschau und Import identisch verwenden. Auch dann muss Maximum ≤ Gesamt-UE bleiben.

Online-Vorschau nach Ergänzung aller ausgewählten LVs:

```bash
python3 "$ACADEMIC_RUN/import_academic_data.py" courses "$ACADEMIC_RUN/courses.json" \
  --mapping "$ACADEMIC_RUN/courses-2027-S.mapping.json" \
  --base-url https://PLANER-ADRESSE --username DEIN_PLANER_LOGIN
```

Tatsächlicher Import nach Prüfung:

```bash
python3 "$ACADEMIC_RUN/import_academic_data.py" courses "$ACADEMIC_RUN/courses.json" \
  --mapping "$ACADEMIC_RUN/courses-2027-S.mapping.json" \
  --base-url https://PLANER-ADRESSE --username DEIN_PLANER_LOGIN --apply
IMPORT_EXIT=$?
printf 'Import-Exitcode: %s\n' "$IMPORT_EXIT"
```

Ein `blocked` oder `conflict` bei einem ausgewählten Eintrag stoppt sämtliche neuen
Schreibvorgänge vor dem Import. Für einen bewussten Teilimport die anderen Einträge
mit `include: false` markieren. Bei einem Laufzeitfehler nach Beginn können dagegen
bereits einzelne LVs angelegt sein. Wie beim Raumimport werden die Ergebnisse je
Datensatz protokolliert und beim nächsten Lauf erneut abgeglichen.

Die Prüfung vorhandener LVs berücksichtigt Name, UE, Sitzungslängen, Zielsemester,
Kohorte, Studienform, ausgewählten Lehrenden und Raum. Abweichungen werden als
Konflikte gemeldet. Eine vorhandene LV wird nicht in ein anderes Semester verschoben.
Nach manuellen Änderungen im Planer kann ein Wiederholungslauf daher bewusst
Konflikte melden; er setzt diese Änderungen nicht zurück.

Der Import erzeugt Stammdaten für die spätere Planung, keine Unterrichtstermine,
Stundenpläne oder Veröffentlichung. Anschließend die übernommenen Daten im Planer
fachlich prüfen und die von 2026 S abweichenden Angaben für 2027 S manuell ändern.

### 9.6 Container-Ausführung

Für die aktuelle PoC-Installation diesen Weg wie beim bestätigten Raumimport verwenden.
Die folgenden Befehle laufen in der SSH-Sitzung auf dem Server. Beide Skripte müssen
im selben Verzeichnis liegen. Die Dateien müssen vorher lokal per `scp` übertragen sein:

```bash
sudo docker cp ~/import_academic_data.py planner-ressources-poc:/tmp/import_academic_data.py
sudo docker cp ~/import_rooms.py planner-ressources-poc:/tmp/import_rooms.py
sudo docker cp ~/lecturers.json planner-ressources-poc:/tmp/lecturers.json
sudo docker cp ~/courses.json planner-ressources-poc:/tmp/courses.json
sudo docker cp ~/courses-2027-S.mapping.json planner-ressources-poc:/tmp/courses-2027-S.mapping.json
```

Beispiel: Online-Vorschau der Lehrenden im Container:

```bash
sudo docker exec -it planner-ressources-poc python /tmp/import_academic_data.py lecturers /tmp/lecturers.json \
  --base-url http://127.0.0.1:8080 --username daniel --report-dir /data/import-reports
```

Nach Prüfung die Lehrenden tatsächlich importieren:

```bash
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py lecturers /tmp/lecturers.json \
  --base-url http://127.0.0.1:8080 \
  --username daniel \
  --report-dir /data/import-reports \
  --apply
```

Für den späteren LV-Import zuerst die Zuordnungsdatei wie in Abschnitt 9.4 ergänzen.
Anschließend die Online-Vorschau aufrufen:

```bash
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.mapping.json \
  --base-url http://127.0.0.1:8080 \
  --username daniel \
  --report-dir /data/import-reports
```

Erst bei geklärten Zuordnungen und konfliktfreier Vorschau denselben LV-Befehl mit
`--apply` ergänzen.
Die bearbeitete Zuordnungsdatei vor dem LV-Lauf erneut in den Container kopieren.
Die Login- und Sitzungshinweise des Raumimports gelten auch hier. Der lokale
HTTP-Zugang wurde für die aktuelle PoC-Instanz bestätigt. Eine später mit
Secure-Sitzungscookies betriebene Produktionsinstanz benötigt HTTPS; dafür die
passende Basisadresse verwenden.

### 9.7 Prüfung und Übergabeprotokoll

Tests auf dem Entwicklungs-PC:

```powershell
backend/.venv/Scripts/python.exe -m unittest discover -s backend/tests/scripts -p "test_import*.py" -v
```

Nach Ergänzung mehrerer Räume bestanden 29 Tests. Geprüft wurden unter anderem
Rundung, vollständige Quelldatenabdeckung, Idempotenz, Fortsetzen nach verlorener
POST-Antwort, Kapazität, aktive Stammdaten, Zeitfenster und Konflikte mit vorhandenen LVs,
Mehrfachzuordnungen und deren Wiederaufnahme nach einem unterbrochenen Konfigurationsschritt.
Die Tests verwenden für Schreibabläufe simulierte API-Antworten; im Rahmen der
Skriptvorbereitung wurde kein Live-Import ausgeführt. Der Benutzer hat anschließend
den erfolgreichen Lehrendenimport und den ersten LV-Teilimport bestätigt (Abschnitt 9.8).

Für beide Serverimporte je eine Kopie der Protokollvorlage aus Abschnitt 8 ausfüllen.
Zusätzlich bei LVs den Stand der Zuordnungsdatei, ihre SHA-256, die verwendeten
Sitzungsgrenzen und ausgelassene Einträge dokumentieren. Der Bericht speichert
Datei- und Mapping-Prüfsummen, aufgelöste API-Payloads und nach erfolgreicher Anlage
die Planer-IDs. Exitcodes sind `0` für einen erfolgreichen konfliktfreien Lauf,
`1` für Fehler und `2` für offene Zuordnungen oder Konflikte.

### 9.8 Bestätigtes Laufprotokoll: BAAI, 2. Semester

| Feld | Bestätigter Stand |
|---|---|
| Datum | 03.11.2026; Zeitangaben in Berichtsdateinamen sind UTC |
| Zielsemester / Kohorte | 2027 S / Business Analytics & AI - 2.Semester |
| Zuordnungsdatei | `courses-2027-S.batch-01-BAAI-2.mapping.json` |
| Umfang | Zehn LVs, Codes 0864VZ2001 bis 0864VZ2010 |
| UE je Termin | Minimum 2, bevorzugt 3, Maximum 4 |
| Räume | CZ108 (45 Plätze), RC409 (78 Plätze); Planungsannahme 30 Studierende |
| Mathematik 2 | Nur Hatzl, Johannes |
| Betriebswirtschaftslehre | Koch, Volker und Meglitsch, Mario |
| Business IT-Applications | Gerzic, Harris und Wipfler, Yevheniia |
| Aufteilung mehrerer Lehrender | Termine werden geteilt; Verteilung später manuell |
| Vorprüfung zunächst blockiert | Fehlende aktive Zeitfenster für Vollzeit; anschließend vom Benutzer angelegt |
| Erfolgreiche Online-Vorschau | `skipped=85, would_create=10` |
| Vorschaubericht | `/data/import-reports/courses-20261103T120030Z-df00f057.json` |
| Importergebnis laut Benutzer-Konsolenausgabe | `created=10, skipped=85` |
| Importbericht | `/data/import-reports/courses-20261103T120103Z-30a11f6b.json` |
| Tatsächliche Ausführung | Container-Befehl aus Abschnitt 9.5, ergänzt um `--apply` |
| Noch zu archivieren | Verwendetes Backup, Datei-/Skriptprüfsummen, Berichtskopie und manuelle Stichprobe; `verified` direkt aus dem Bericht bestätigen |
| Nächste Kohorte laut Vorgabe | Business Analytics & AI – 4. Semester |

Die Konsolenausgabe bestätigt die zehn Neuanlagen. Auf dem Server wurden im
Rahmen dieses Chats keine zusätzlichen direkten Prüfungen durch den Assistenten
ausgeführt. Die nachträgliche Verteilung der Termine auf beide Lehrenden und die
eigentliche Stundenplangenerierung sind getrennte Folgeschritte.

### 9.9 Vorbereitung: BAAI, 4. Semester

Nach Sichtprüfung des ersten Teilimports hat der Benutzer die Fortsetzung in der
vorgegebenen Reihenfolge bestätigt. Der zweite Teilimport ist unter
`artifacts/export-import/courses-2027-S.batch-02-BAAI-4.mapping.json` vorbereitet.

| LV-Code | Titel | Gerundete UE | Berechtigte Lehrende als Grundlage aus 2026 S |
|---|---|---:|---|
| 0864VZ4001 | Electronic und Mobile Business | 60 | Glinik, Martin; Jesenko, Berndt |
| 0864VZ4004 | Databases | 68 | Softic, Safet |
| 0864VZ4005 | Internet Security | 51 | Leitner, Sascha |
| 0864VZ4006 | Business English 2 | 34 | Briscoe, Henry |
| 0864VZ4007 | Managerial Communication und Leadership | 51 | Kreuzer, Ernst |
| 0864VZ4009 | Data Cleaning und Data Analytics | 47 | Hollosi, Arno; Schirgi, Eva |

Die Einstellungen des bisherigen Teilimports werden fortgeführt: Minimum 2 UE,
Wunschwert 3, Maximum 4 und zulässige Räume CZ108/RC409. Die tatsächliche
Studierendenzahl dieser Kohorte wird aus dem Planer geprüft, nicht auf 30 gesetzt.
Bei mehreren Quell-Lehrenden bleiben alle als zulässige Lehrende erhalten;
die Verteilung der Termine erfolgt später manuell. „Accompanying Project“ mit
0 UE ist weiterhin ausgelassen. Die Zuordnung der Codes `0864VZ4*` zum
4. Fachsemester ist bei der Vorschau fachlich zu prüfen.

Lokale Offline-Prüfung: `candidate=6, skipped=89`. Ein Serverimport ist noch
nicht bestätigt. Der bestehende Katalog `courses.json` und die Importskripte im
Container bleiben für diesen Lauf verwendbar; nur die neue Zuordnungsdatei ist
zusätzlich zu übertragen.

Lokale PowerShell:

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 artifacts/export-import/courses-2027-S.batch-02-BAAI-4.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/courses-2027-S.batch-02-BAAI-4.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-02-BAAI-4.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-02-BAAI-4.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports
```

Bei unverändertem Bestand und passenden Zuordnungen wird `would_create=6,
skipped=89` erwartet. Nach Prüfung denselben Docker-exec-Befehl mit `--apply`
ausführen und Ergebnis sowie Berichtspfad hier nachtragen. Die 89 ausgelassenen
Einträge umfassen auch die zehn bereits importierten LVs des 2. Semesters;
sie werden durch diesen Teilimport nicht geändert.

Nachgereichte erfolgreiche Vorschau: `skipped=89, would_create=6`, Bericht
`/data/import-reports/courses-20261103T120349Z-7f8abed0.json`. Der Benutzer hat
anschließend die Fortsetzung bestätigt; die abschließende Importausgabe und der
Importbericht dieses zweiten Teilimports sind noch nachzutragen.

### 9.10 Vorbereitung: BAAI, 6. Semester und erweiterte Raumauswahl

Der dritte Teilimport ist unter
`artifacts/export-import/courses-2027-S.batch-03-BAAI-6.mapping.json` vorbereitet.
Er aktiviert vier LVs, die weiteren 91 Katalogeinträge bleiben ausgelassen:

| Code | Titel | UE | Lehrende aus 2026 S |
|---|---|---:|---|
| 0864VZ6001 | Cloud Computing | 34 | Softic, Selver |
| 0864VZ6003 | Bachelorarbeit | 17 | Softic, Selver |
| 0864VZ6007 | Data Mining | 34 | Schirgi, Eva |
| 0864VZ6009 | Wissensmanagement und Semantic Web | 34 | Softic, Selver |

Die Bachelorarbeit bleibt enthalten; der zuvor bestätigte Ausschluss betraf
Bachelorprüfungen, Masterarbeit und Masterprüfung. Die Einstellungen je Termin
bleiben Minimum 2 UE, Wunschwert 3 und Maximum 4. Die Kohorte ist als
`Business Analytics & AI - 6.Semester` zugeordnet, aus dem LV-Codeschema abgeleitet.
Die tatsächlichen Stammdaten werden vor dem Import online geprüft.

Der Benutzer hat die bisherige Raumauswahl um CZ106, CZ107, CZ109, CZ110,
RC403, RC404 und RC402 erweitert. Die Kapazitäten aus `rooms.json` lauten:

| Raum | Sitzplätze | Für die Arbeitsannahme von 30 Studierenden |
|---|---:|---|
| CZ106 | 36 | Verwendbar |
| CZ107 | 45 | Verwendbar |
| CZ108 | 45 | Verwendbar |
| CZ109 | 53 | Verwendbar |
| CZ110 | 63 | Verwendbar |
| RC403 | 72 | Verwendbar |
| RC404 | 60 | Verwendbar |
| RC409 | 78 | Verwendbar |
| RC402 | 28 | Zu klein; in diesem Teilimport nicht als zulässiger Raum eingetragen |

Alle acht ausreichend großen Räume sind für die vier LVs als berechtigte Auswahl
eingetragen. Die Anwendung entscheidet später bei der Planung über die konkrete
Raumbelegung; die Reihenfolge der Codes ist keine Gewichtung. Die tatsächliche
Kohortengröße kann die Auswahl weiter einschränken und wird aus dem Planer gelesen.
Raumausstattung ist in den Quelldaten nicht ausgewiesen. Frühere Teilimporte und
deren Raumberechtigungen werden durch diese neue Datei nicht verändert.

Offline-Prüfung: `candidate=4, skipped=91`. Servervorschau und Import sind noch offen.

Lokale PowerShell:

```powershell
scp -P 17655 C:/Codex/planner-resource/artifacts/export-import/courses-2027-S.batch-03-BAAI-6.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/courses-2027-S.batch-03-BAAI-6.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-03-BAAI-6.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-03-BAAI-6.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports
```

Bei passender Vorschau wird `would_create=4, skipped=91` erwartet. Danach denselben
Docker-exec-Befehl mit `--apply` ausführen und die tatsächliche Ausgabe samt
Berichtspfad dokumentieren. Die nächste Kohorte ist anschließend
Business Software Development – 2. Semester.

Der Benutzer hat danach mit „passt nächst“ die Fortsetzung bestätigt. Der konkrete
Importbericht und die abschließende Konsolenausgabe für BAAI 6 sind noch nachzutragen.

### 9.11 Vorbereitung: Business Software Development, 2. Semester

Datei: `artifacts/export-import/courses-2027-S.batch-04-BSD-2.mapping.json`.
Acht positive-UE-LVs mit Codes `0835VD2001` bis `0835VD2008` sind ausgewählt;
87 andere Einträge bleiben ausgelassen. Zielkohorte laut Screenshot:
`Business Software Development – 2. Semester`; die Online-Prüfung bestätigt die
Übereinstimmung mit den vorhandenen Stammdaten. Die Semesterzuordnung ist aus
dem Codeschema abgeleitet und vor der Übernahme fachlich zu prüfen.

| Code | Titel | Gerundete UE |
|---|---|---:|
| 0835VD2001 | Mathematik für Informatik 2 | 60 |
| 0835VD2002 | Professional English | 30 |
| 0835VD2003 | Personalmanagement und Arbeitsrecht | 30 |
| 0835VD2004 | Objektorientierte Programmierung | 60 |
| 0835VD2005 | Datenbankdesign | 47 |
| 0835VD2006 | Datenstrukturen und Algorithmen | 47 |
| 0835VD2007 | Konfigurationsmanagement | 30 |
| 0835VD2008 | Web Technologien & Usability | 47 |

Die bisherigen Einstellungen werden fortgeführt: Minimum 2 UE, Wunschwert 3,
Maximum 4; zulässige Räume CZ106, CZ107, CZ108, CZ109, CZ110, RC403, RC404 und
RC409. RC402 bleibt aufgrund von 28 Sitzplätzen für die Arbeitsannahme von
30 Studierenden ausgeschlossen. Alle Quell-Lehrenden der ausgewählten LVs bleiben
als Berechtigte hinterlegt. Die tatsächliche Kohortengröße wird online geprüft.

Offline-Prüfung: `candidate=8, skipped=87`. Servervorschau und Import stehen noch aus.

Lokale PowerShell:

```powershell
scp -P 17655 C:/Codex/planner-resource/artifacts/export-import/courses-2027-S.batch-04-BSD-2.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/courses-2027-S.batch-04-BSD-2.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-04-BSD-2.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-04-BSD-2.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports
```

Erwartete Vorschau bei passenden Zuordnungen: `would_create=8, skipped=87`.
Nach Prüfung denselben Docker-exec-Befehl mit `--apply` ausführen und Ergebnis
sowie Berichtspfad ergänzen. Danach folgt Business Software Development – 4. Semester.

### 9.12 Fortsetzung: Business Software Development, 4. und 6. Semester

Die Fortsetzung nach BSD 2 und BSD 4 wurde jeweils vom Benutzer bestätigt.
Konkrete Konsolenausgaben und Serverberichtspfade sind noch nachzutragen.

| Teilimport | Datei unter `artifacts/export-import/` | Ausgewählte LVs | Ausgelassen |
|---|---|---:|---:|
| BSD 4. Semester | `courses-2027-S.batch-05-BSD-4.mapping.json` | 10 | 85 |
| BSD 6. Semester | `courses-2027-S.batch-06-BSD-6.mapping.json` | 10 | 85 |

Die Zuordnung erfolgt anhand der positiven-UE-Codes `0835VD4*` beziehungsweise
`0835VD6*`. Die Kohortennamen sind `Business Software Development – 4. Semester`
und `Business Software Development – 6. Semester`. Beide Dateien verwenden
Minimum 2 UE, Wunschwert 3 und Maximum 4 sowie die acht bisher freigegebenen,
für die Arbeitsannahme von 30 Studierenden ausreichend großen CZ-/RC-Räume.
Die tatsächliche Kohortengröße wird online geprüft. Alle historischen Quell-Lehrenden
bleiben als Berechtigte hinterlegt, die Terminverteilung erfolgt später manuell.
Die Offline-Prüfung beider Dateien ergab jeweils `candidate=10, skipped=85`.

Der Benutzer wünscht inzwischen den direkten Befehl mit `--apply`. Die Vorprüfung
gegen die API bleibt dabei aktiv; bei Blockaden oder Konflikten erfolgen keine
Neuanlagen. Lokal die jeweilige Datei per `scp -P 17655` nach
`admin_b50578@10.155.11.130:~/` übertragen, dann in der SSH-Sitzung beispielsweise
für BSD 6 ausführen:

```bash
sudo docker cp ~/courses-2027-S.batch-06-BSD-6.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-06-BSD-6.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-06-BSD-6.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
```

Bei unverändertem Zielbestand wird jeweils `created=10, skipped=85` erwartet.
Für BSD 6 ist ein erfolgreicher Serverlauf noch offen. Danach folgt
MA IT & Wirtschaftsinformatik – 2. Semester.

Die Fortsetzung nach BSD 6 wurde vom Benutzer bestätigt; konkrete Abschlussausgabe
und Berichtspfad sind noch nachzutragen.

### 9.13 Vorbereitung: MA IT & Wirtschaftsinformatik, 2. Semester

Datei: `artifacts/export-import/courses-2027-S.batch-07-MA-IT-2.mapping.json`.
Elf LVs mit positiven UE und Codes `0320BB2*` sind ausgewählt, 84 andere Einträge
bleiben ausgelassen. Zielkohorte laut Screenshot ist
`MA IT & Wirtschaftsinformatik - 2.Semester`. Die Studienform ist
**Berufsbegleitend**; hierfür müssen passende aktive Zeitfenster vorhanden sein.

Es gelten weiterhin Minimum 2 UE, Wunschwert 3 und Maximum 4.
Die erste Servervorprüfung war mit `blocked=11, skipped=84` blockiert, weil
mindestens einer der ursprünglich acht Räume zu klein für die Kohorte war.
Bericht: `/data/import-reports/courses-20261103T121649Z-c9682585.json`.
Es wurden dabei keine neuen LVs angelegt. Anschließend bestätigte der Benutzer
**65 Studierende** und wählte ausdrücklich **RC409**. Die Zuordnungsdatei wurde
deshalb für alle elf LVs auf ausschließlich **RC409 (78 Plätze)** beschränkt.
RC403 wäre mit 72 Plätzen ebenfalls groß genug, ist aber nicht ausgewählt.
CZ106, CZ107, CZ108,
CZ109, CZ110, RC402 und RC404 sind für diese Kohorte zu klein und entfernt.
Alle anderen Zuordnungen bleiben unverändert. Die korrigierte Datei muss vor
dem nächsten Serverlauf erneut übertragen und in den Container kopiert werden.
Alle historischen Quell-Lehrenden bleiben als berechtigte Personen erhalten.
Die tatsächliche Kohortengröße wird weiterhin online geprüft und nicht geändert.
Das **Seminar zur Masterarbeit 1** mit 34 UE ist als reguläre Lehrveranstaltung
enthalten. Die eigenständige Masterarbeit und die Masterprüfung bleiben ausgeschlossen.

Offline-Prüfung: `candidate=11, skipped=84`. Serverimport noch offen.

Lokale PowerShell:

```powershell
scp -P 17655 C:/Codex/planner-resource/artifacts/export-import/courses-2027-S.batch-07-MA-IT-2.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/courses-2027-S.batch-07-MA-IT-2.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-07-MA-IT-2.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-07-MA-IT-2.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
```

Erwartet bei passenden Zuordnungen und unverändertem Zielbestand:
`created=11, skipped=84`. Danach folgt Wirtschaftsinformatik – 2. Semester.

Nach Korrektur auf RC409 hat der Benutzer den MA-Teilimport mit „passt“ bestätigt.
Der tatsächliche Abschlussbericht samt Konsolenausgabe ist noch nachzutragen.

### 9.14 Vorbereitung: Wirtschaftsinformatik, 2. Semester

Datei: `artifacts/export-import/courses-2027-S.batch-08-WI-2.mapping.json`.
Zwölf LVs mit positiven UE und Codes `0319BB2*` sind ausgewählt; 83 andere
Einträge bleiben ausgelassen. Zielkohorte ist `Wirtschaftsinformatik - 2.Semester`,
Studienform **Berufsbegleitend**. Die Zuordnung aus dem Codeschema ist fachlich
zu prüfen; die Online-Prüfung löst den Kohortennamen zu den vorhandenen Stammdaten auf.

Minimum 2 UE, Wunschwert 3, Maximum 4 werden fortgeführt. Alle Quell-Lehrenden
bleiben als berechtigte Personen erhalten, die Verteilung erfolgt später manuell.
Der Benutzer hat für diese Kohorte **40 Studierende und ausschließlich CZ-Räume**
vorgegeben. Die Zuordnungsdatei wurde deshalb auf **CZ107 (45 Plätze), CZ108
(45 Plätze), CZ109 (53 Plätze) und CZ110 (63 Plätze)** beschränkt. CZ106 ist mit
36 Plätzen zu klein; sämtliche RC-Räume sind für diese Kohorte auf Benutzerwunsch
ausgeschlossen. Die vorherige Datei darf nicht weiterverwendet werden; die
korrigierte Zuordnungsdatei erneut übertragen und in den Container kopieren.
Die tatsächliche WI-Kohortengröße wird weiterhin aus dem Planer geprüft und nicht
automatisch auf 40 gesetzt. Die ausschließliche Auswahl RC409 bleibt auf die
MA-Kohorte mit 65 Studierenden beschränkt.

Falls der WI-Teilimport bereits mit den früheren Raumberechtigungen angelegt wurde,
ist dies kein reiner Neuanlagenlauf mehr: das Skript entfernt vorhandene RC-Räume
nicht automatisch, sondern meldet einen Konflikt. In diesem Fall die bestehenden
Raumberechtigungen im Planer gezielt korrigieren und danach erneut prüfen.

Offline-Prüfung: `candidate=12, skipped=83`. Die erfolgreiche Fortsetzung wurde
inzwischen vom Benutzer bestätigt; genaue Konsolenausgabe und Berichtspfad sind
noch nachzutragen.

Lokale PowerShell:

```powershell
scp -P 17655 C:/Codex/planner-resource/artifacts/export-import/courses-2027-S.batch-08-WI-2.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/courses-2027-S.batch-08-WI-2.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-08-WI-2.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-08-WI-2.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
```

Bei passenden Zuordnungen wird `created=12, skipped=83` erwartet.
Danach folgt Wirtschaftsinformatik – 4. Semester.

Nach Korrektur auf die CZ-Auswahl bestätigte der Benutzer die Fortsetzung mit
„passt“. Die tatsächliche Abschlussausgabe und der Berichtspfad von WI 2 sind
noch nachzutragen.

### 9.15 Vorbereitung: Wirtschaftsinformatik, 4. Semester

Datei: `artifacts/export-import/courses-2027-S.batch-09-WI-4.mapping.json`.
Elf positive-UE-LVs der Codes `0319BB4*` sind ausgewählt, 84 andere Einträge
ausgelassen. Zielkohorte: `Wirtschaftsinformatik - 4.Semester`; Studienform:
Berufsbegleitend. Die Zuordnung anhand der Quellcodes ist fachlich zu prüfen.

Minimum 2 UE, Wunschwert 3, Maximum 4 und sämtliche historischen Quell-Lehrenden
bleiben Grundlage. Die CZ-Auswahl aus dem vorherigen WI-Teilimport wird zunächst
fortgeführt: CZ107, CZ108, CZ109 und CZ110. Die Gruppengröße von WI 4 ist nicht
separat bestätigt; die API prüft die tatsächlich gespeicherte Zahl und verändert
sie nicht. Die bestätigten 40 Studierenden beziehen sich auf WI 2.

Offline-Prüfung: `candidate=11, skipped=84`. Serverimport noch offen.

Lokale PowerShell:

```powershell
scp -P 17655 C:/Codex/planner-resource/artifacts/export-import/courses-2027-S.batch-09-WI-4.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/courses-2027-S.batch-09-WI-4.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-09-WI-4.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-09-WI-4.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
```

Bei passenden Zuordnungen wird `created=11, skipped=84` erwartet.
Danach folgt als letzte Kohorte Wirtschaftsinformatik – 6. Semester.

Der Benutzer hat anschließend die Fortsetzung bestätigt; tatsächliche
Abschlussausgabe und Serverbericht von WI 4 sind noch nachzutragen.

### 9.16 Letzter Teilimport: Wirtschaftsinformatik, 6. Semester

Datei: `artifacts/export-import/courses-2027-S.batch-10-WI-6.mapping.json`.
Zwölf LVs mit positiven UE und Codes `0319BB6*` sind ausgewählt; 83 andere
Einträge bleiben ausgelassen. Zielkohorte: `Wirtschaftsinformatik - 6.Semester`;
Studienform: Berufsbegleitend. Die Zuordnung aus dem Codeschema ist fachlich zu prüfen.

Die bisherigen Einstellungen werden fortgeführt: Minimum 2 UE, Wunschwert 3,
Maximum 4; zulässige Räume CZ107, CZ108, CZ109 und CZ110; alle historischen
Quell-Lehrenden als berechtigte Personen. Die tatsächliche WI-6-Kohortengröße wird
vor dem Import über die API geprüft. Sie wurde hier noch nicht separat bestätigt.

Offline-Prüfung: `candidate=12, skipped=83`. Der Benutzer hat den erfolgreichen
letzten Teilimport anschließend mit „passt“ bestätigt; genaue Konsolenausgabe
und Berichtspfad bleiben nachzutragen.

Lokale PowerShell:

```powershell
scp -P 17655 C:/Codex/planner-resource/artifacts/export-import/courses-2027-S.batch-10-WI-6.mapping.json admin_b50578@10.155.11.130:~/
```

SSH-Sitzung auf dem Server:

```bash
sudo docker cp ~/courses-2027-S.batch-10-WI-6.mapping.json planner-ressources-poc:/tmp/courses-2027-S.batch-10-WI-6.mapping.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py courses /tmp/courses.json \
  --mapping /tmp/courses-2027-S.batch-10-WI-6.mapping.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
```

Erwartetes Ergebnis bei unverändertem Zielbestand und passenden Zuordnungen:
`created=12, skipped=83`. Tatsächliche Abschlussausgabe und Berichtspfad nachtragen.

### 9.17 Abdeckung aller zehn Teilimporte

Die lokalen Zuordnungsdateien wurden gemeinsam geprüft: Alle 94 positiven-UE-LVs
des bereinigten Katalogs sind genau einmal ausgewählt; es gibt keine doppelte
Auswahl zwischen Teilimporten. Dies bestätigt die Dateiabdeckung, nicht den
vollständigen Serverbestand. „Accompanying Project“ mit 0 UE bleibt ausgelassen.

| Reihenfolge | Kohorte | Ausgewählte LVs |
|---|---|---:|
| 1 | Business Analytics & AI – 2. Semester | 10 |
| 2 | Business Analytics & AI – 4. Semester | 6 |
| 3 | Business Analytics & AI – 6. Semester | 4 |
| 4 | Business Software Development – 2. Semester | 8 |
| 5 | Business Software Development – 4. Semester | 10 |
| 6 | Business Software Development – 6. Semester | 10 |
| 7 | MA IT & Wirtschaftsinformatik – 2. Semester | 11 |
| 8 | Wirtschaftsinformatik – 2. Semester | 12 |
| 9 | Wirtschaftsinformatik – 4. Semester | 11 |
| 10 | Wirtschaftsinformatik – 6. Semester | 12 |
| Gesamt | | **94** |

Nach dem letzten erfolgreichen Serverlauf den Bestand für 2027 S im Planer je
Kohorte gegen diese Übersicht prüfen. Insbesondere Lehrendenberechtigungen und
die kohortenspezifischen Räume stichprobenartig kontrollieren, Serverberichte
archivieren und ein neues Backup des abgeschlossenen Importstands erstellen.
Die Stundenplangenerierung ist ein separater nächster Schritt; die geteilten
Lehrveranstaltungen müssen später manuell auf die beteiligten Personen verteilt werden.

### 9.18 Abschlussbestätigung

Am 03.11.2026 hat der Benutzer auch den letzten Teilimport mit „passt“ bestätigt.
Damit ist die Durchführung aller zehn Teilimporte nach den Rückmeldungen des
Benutzers abgeschlossen. Erwarteter Umfang: **94 LVs für 2027 S**. Die lokale
Abdeckungsprüfung bestätigt 94 eindeutige positive-UE-LVs in den zehn Dateien;
ein vollständiger direkter Serverabgleich durch den Assistenten wurde nicht ausgeführt.
Die nicht geposteten Einzelberichte und Abschlussausgaben bleiben nachzutragen.

Die Nachprüfung im Planer sowie ein Backup des nun abgeschlossenen Importstands
sind noch offen. Dafür in der Server-SSH-Sitzung ausführen:

```bash
sudo docker exec planner-ressources-poc python scripts/backup_sqlite_db.py --output-dir /data/backups
```

Den tatsächlich ausgegebenen Backup-Dateinamen hier beziehungsweise im
Betriebsprotokoll festhalten und die Sicherung wie in Abschnitt 4 zusätzlich
außerhalb des Container-Volumes archivieren. Dieses neue Backup ergänzt die
vorherige Sicherung; es ersetzt nicht den Nachweis des Zustands vor dem Import.

## 10. Österreichische Feiertage für 2027 S

Der Benutzer möchte die österreichischen Feiertage für den bestehenden
Semesterzeitraum **19.02.2027 bis einschließlich 17.08.2027** übernehmen.
Die vorbereitete Datei liegt unter `artifacts/export-import/holidays-AT-2027-S.json`.

| Datum | Wochentag | Name |
|---|---|---|
| 29.03.2027 | Montag | Ostermontag |
| 01.05.2027 | Samstag | Staatsfeiertag |
| 06.05.2027 | Donnerstag | Christi Himmelfahrt |
| 17.05.2027 | Montag | Pfingstmontag |
| 27.05.2027 | Donnerstag | Fronleichnam |
| 15.08.2027 | Sonntag | Mariä Himmelfahrt |

Quellen, am 03.11.2026 geprüft:

- [USP: gesetzliche Feiertage](https://www.usp.gv.at/themen/mitarbeiter-und-gesundheit/urlaub-und-arbeitszeit/ruhezeiten.html) für die bundesweit gesetzliche Feiertagsliste.
- [BMEIA: Feiertage 2025–2027](https://www.bmeia.gv.at/fileadmin/user_upload/Vertretungen/Kopenhagen/Aktuelles/Feiertage_2025-2027.pdf) für die konkreten Daten 2027. Die dort zusätzlich genannten Oster- und Pfingstsonntage werden nicht als zusätzliche gesetzliche Feiertage aus der USP-Liste übernommen.

Die Datei enthält nur die sechs bundesweiten gesetzlichen Feiertage im
Semesterzeitraum, einschließlich solcher am Wochenende. Schulferien, Fenstertage,
regionale schulfreie Tage und hochschuleigene Schließzeiten sind nicht automatisch
eingetragen und müssen bei Bedarf gesondert festgelegt werden.

Der Planer verwaltet Feiertage **institutionsweit nach Datum**, nicht als direkte
Semesterzuordnung. Die Datei ist auf den Semesterzeitraum begrenzt; beim Import
bleiben vorhandene Feiertage anderer Zeiträume unverändert. Der Generator verwendet
die Einträge für die jeweils betroffenen Termine. Der Import verschiebt keine
bereits gespeicherten Unterrichtstermine automatisch.

### 10.1 Skript und Vorprüfung

`backend/scripts/import_academic_data.py` unterstützt nun zusätzlich den Modus
`holidays`. Die Datei `import_rooms.py` muss weiterhin im selben Skriptverzeichnis
liegen. Die Feiertags-API liefert eine Liste ohne Paginierung:
`GET /api/holidays`; Anlage: `POST /api/holidays` mit `date` und `name`.

Gleiche Daten und Namen werden wiederverwendet. Ein bereits belegtes Datum mit
abweichendem Namen ist ein Konflikt und wird nicht überschrieben. Alle ausgewählten
Daten werden vorab geprüft, bei Konflikten erfolgen keine Neuanlagen. Wiederholungen
und unterbrochene Läufe verwenden denselben Bestandsabgleich wie die anderen Importe.
Nach Abschluss werden die angelegten oder vorhandenen Einträge nochmals gelesen.

Die Eingabeprüfung verlangt eindeutige Datumswerte im ISO-Format `YYYY-MM-DD`,
Namen mit 1–200 Zeichen und Daten innerhalb des angegebenen Zeitraums.
Offline-Prüfung des vorbereiteten Standes: `candidate=6`.
Die gemeinsame Testsuite umfasst nach der Ergänzung 33 bestandene Tests.
Ein Serverimport der Feiertage ist bisher nicht bestätigt.

### 10.2 Übertragen und importieren

Vor dem Lauf den abgeschlossenen LV-Importstand wie in Abschnitt 9.18 sichern.
Das aktualisierte Skript muss erneut übertragen werden; die bisherige Version
im Container kennt den neuen Modus möglicherweise noch nicht.

**Lokale PowerShell:**

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 backend/scripts/import_academic_data.py backend/scripts/import_rooms.py artifacts/export-import/holidays-AT-2027-S.json admin_b50578@10.155.11.130:~/
```

**Server-SSH-Sitzung:**

```bash
sudo docker cp ~/import_academic_data.py planner-ressources-poc:/tmp/import_academic_data.py
sudo docker cp ~/import_rooms.py planner-ressources-poc:/tmp/import_rooms.py
sudo docker cp ~/holidays-AT-2027-S.json planner-ressources-poc:/tmp/holidays-AT-2027-S.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py holidays /tmp/holidays-AT-2027-S.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
```

Die Online-Vorprüfung läuft auch bei `--apply`. Für eine separate Online-Vorschau
`--apply` weglassen. Wenn keiner der sechs Feiertage vorhanden ist, wird
`created=6` erwartet. Bei Wiederholung können `existing`-Einträge erscheinen.
Exitcodes und Berichtsauswertung entsprechen Abschnitt 9.7. Die tatsächlich
ausgeführte Ausgabe und den neuen Berichtspfad hier nachtragen und die sechs
Datumswerte in der Feiertagsverwaltung prüfen.

### 10.3 Ergänzung: Osterferien als unterrichtsfreie Zeit

Der Benutzer hat bestätigt, dass die steirischen Schulosterferien auch in der
Hochschulplanung vollständig unterrichtsfrei bleiben sollen:
**20.03.2027 bis einschließlich 29.03.2027**. Der Zeitraum wurde anhand der
[Ferientermine des Bildungsministeriums](https://www.bmb.gv.at/Themen/schule/schulpraxis/termine/ferientermine_26_27.html)
ermittelt. Seine Übernahme als Hochschulschließzeit ist die ausdrückliche
Planungsentscheidung des Benutzers, keine automatisch unterstellte Hochschulregel.

Die kombinierte Datei `artifacts/export-import/nonteaching-AT-2027-S.json` enthält
alle sechs gesetzlichen Feiertage plus neun zusätzliche Daten vom 20.03. bis
28.03.2027 unter dem Namen `Osterferien (unterrichtsfrei)`. Am 29.03.2027 bleibt
der bereits enthaltene Name **Ostermontag** unverändert. Es entstehen somit
**15 unterschiedliche gesperrte Kalendertage** im Semester; der vollständige
zehntägige Ferienzeitraum ist enthalten, ohne den Ostermontag zu duplizieren.
Die ursprüngliche Datei mit ausschließlich gesetzlichen Feiertagen bleibt als
separate Quelle erhalten. Für den vollständigen gewünschten Planungsstand nun
die kombinierte Datei verwenden.

Der vorhandene Modus `holidays` ist wiederverwendbar, eine weitere Änderung des
Imports ist nicht erforderlich. Die Kalenderdaten gelten institutionsweit für
alle Kohorten. Bereits gespeicherte Unterrichtstermine werden nicht verschoben;
sie sind gegebenenfalls separat auf Konflikte mit den freien Tagen zu prüfen.

Offline-Prüfung: `candidate=15`. 35 gemeinsame Tests bestanden, einschließlich
vollständiger inklusiver Ferienabdeckung, unverändertem Ostermontag und Wiederholung
bei sechs bereits vorhandenen Feiertagen. Serverimport noch nicht bestätigt.

**Lokale PowerShell:**

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 backend/scripts/import_academic_data.py backend/scripts/import_rooms.py artifacts/export-import/nonteaching-AT-2027-S.json admin_b50578@10.155.11.130:~/
```

**Server-SSH-Sitzung:**

```bash
sudo docker cp ~/import_academic_data.py planner-ressources-poc:/tmp/import_academic_data.py
sudo docker cp ~/import_rooms.py planner-ressources-poc:/tmp/import_rooms.py
sudo docker cp ~/nonteaching-AT-2027-S.json planner-ressources-poc:/tmp/nonteaching-AT-2027-S.json
sudo docker exec -it planner-ressources-poc \
  python /tmp/import_academic_data.py holidays /tmp/nonteaching-AT-2027-S.json \
  --base-url http://127.0.0.1:8080 --username daniel \
  --report-dir /data/import-reports --apply
```

Erwartetes Ergebnis, wenn die sechs gesetzlichen Feiertage bereits identisch
vorhanden sind: `created=9, existing=6`. Wenn noch keiner der Einträge angelegt
wurde: `created=15`. Bei vollständiger Wiederholung: `existing=15`. Ein bereits
mit einem anderen Namen belegtes Datum führt zum Konflikt und wird nicht geändert.
Tatsächliche Ausgabe und Berichtspfad nach erfolgreicher Ausführung ergänzen.
