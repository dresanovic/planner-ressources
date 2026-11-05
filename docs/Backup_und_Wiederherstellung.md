# Datenbank sichern und aus einem Backup wiederherstellen

Die folgenden Befehle sind für deinen lokalen Rechner und den Testserver
`10.155.11.130` vorbereitet. Passwörter bei SSH oder sudo nur auf Nachfrage
eingeben. Für Backup und Restore wird kein Bootstrap-Credential benötigt.

Ein Restore ersetzt den aktuellen Datenbestand vollständig durch den Stand des
Backups. Auch Benutzerkonten und Anmeldezustände werden zurückgesetzt. Das
Restore-Skript prüft das Backup und sichert eine vorhandene Zieldatenbank vor
dem Ersetzen zusätzlich in einem eigenen `before-restore-*`-Ordner.

**Backup ist bei laufender Anwendung möglich. Vor Restore müssen alle Prozesse,
die dieselbe Zieldatenbank verwenden, gestoppt sein.** Die Beispiele stellen in
die bestehende Installation wieder her; Container, Datenvolume und Konfiguration
müssen noch vorhanden sein. Zum Backup passende Anwendungsversion und stabilen
`LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` beibehalten. Ein älteres Image kann eine
neuere Datenbank möglicherweise nicht öffnen.

## 1. Lokal: Python-Backend ohne Docker

Diese Befehle in **Windows PowerShell** ausführen. Der angenommene Datenbankpfad
ist `C:\Codex\planner-resource\backend\planner.db`. Falls du das Backend mit
einem anderen Arbeitsverzeichnis oder `DATABASE_URL` startest, `$Database`
entsprechend ändern. Im Projekt existiert auch eine Datenbank im Hauptordner;
deshalb den tatsächlich verwendeten Pfad vorab prüfen.

### Backup erstellen

```powershell
Set-Location C:\Codex\planner-resource
$Database = 'C:\Codex\planner-resource\backend\planner.db'

.\backend\.venv\Scripts\python.exe backend/scripts/backup_sqlite_db.py --database $Database --output-dir backend/backups
if ($LASTEXITCODE -ne 0) { throw 'Backup fehlgeschlagen.' }

Get-ChildItem backend/backups -Filter '*.db' | Sort-Object LastWriteTime -Descending
```

Den Dateinamen aus `Backup created: ...` für den Restore verwenden. Eine weitere
Kopie außerhalb dieses Rechners aufbewahren.

### Altes Stammdaten-Backup auf das aktuelle Schema aktualisieren

Wenn die laufende Datenbank Testdaten enthält, aber ein älteres Backup den
gewünschten Datenstand hat, kann eine separate Kopie dieses Backups auf das
Schema des aktuellen Projektstands aktualisiert werden. Dabei werden keine
Daten aus der laufenden Datenbank übernommen. Das ursprüngliche Backup bleibt
erhalten. Die Schemaaktualisierung entfernt keine Pläne: Ein Backup mit Plänen
enthält sie auch nach der Aktualisierung. Deshalb zuerst den Inhalt des
Ausgangsbackups prüfen.

Das folgende Beispiel verwendet das lokale Stammdaten-Backup vom 3. November
2026. Es enthielt bei der Prüfung 94 Kurse und keine generierten Entwürfe oder
Termine. Für ein anderes Backup den Pfad `source` anpassen. Die Migration
verwendet den aktuellen Projektcode und benötigt die Backend-Umgebung; ein
Backup mit neuerem Schema ist nicht unbedingt mit einem älteren App-Image
kompatibel.

```powershell
Set-Location C:\Codex\planner-resource

@'
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

project = Path.cwd()
source = project / "backend" / "backups" / "planner-20261103-125742.db"
backup_dir = project / "backend" / "backups"
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
target = backup_dir / f"planner-upgraded-{timestamp}.db"

if not source.is_file():
    raise SystemExit(f"Source backup not found: {source}")

sys.path.insert(0, str(project / "backend"))
from app.db.schema import initialize_database

with target.open("xb"):
    pass

try:
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as old:
        with sqlite3.connect(target) as new:
            old.backup(new)

    engine = create_engine(URL.create("sqlite", database=str(target)))
    try:
        initialize_database(engine)
    finally:
        engine.dispose()

    with sqlite3.connect(target.resolve().as_uri() + "?mode=ro", uri=True) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_errors = db.execute("PRAGMA foreign_key_check").fetchall()
        columns = {
            row[1] for row in db.execute("PRAGMA table_info(optimization_operations)")
        }
        courses = db.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        drafts = db.execute("SELECT COUNT(*) FROM draft_schedules").fetchone()[0]
        sessions = db.execute("SELECT COUNT(*) FROM draft_sessions").fetchone()[0]

    if integrity != "ok" or foreign_key_errors or "budget_exhausted" not in columns:
        raise RuntimeError(
            f"Validation failed: integrity={integrity}, "
            f"foreign key errors={len(foreign_key_errors)}"
        )

    print(f"New upgraded backup: {target}")
    print("Integrity: ok; foreign key errors: 0; optimization schema: present")
    print(f"Courses: {courses}; draft schedules: {drafts}; draft sessions: {sessions}")
except Exception:
    target.unlink(missing_ok=True)
    raise
'@ | .\backend\.venv\Scripts\python.exe -

if ($LASTEXITCODE -ne 0) { throw 'Backup-Aktualisierung fehlgeschlagen.' }
```

Den ausgegebenen Dateinamen und die Zahlen prüfen und die neue Datei auf
separatem Speicher sichern. Die Prüfungen bestätigen Datenbankintegrität und
zeigen diese drei Tabellen; sie ersetzen nicht die inhaltliche Kontrolle eines
isolierten Restores. Das am 5. November 2026 erstellte Ergebnis heißt
`planner-upgraded-20261105-092241.db`.

**Eine Backup-Datei wird beim Start der App nicht automatisch geladen.** Soll
die App den Stand des neuen Backups anzeigen, muss es wie im nächsten Abschnitt
in die tatsächlich verwendete Datenbank wiederhergestellt werden.

### Backup wiederherstellen

Zuerst den gewünschten Dateinamen eintragen. Du kannst hier auch eine vom
Testserver heruntergeladene Datei angeben.

```powershell
Set-Location C:\Codex\planner-resource
$Database = 'C:\Codex\planner-resource\backend\planner.db'
$Backup = 'C:\Codex\planner-resource\backend\backups\planner-upgraded-20261105-092241.db' # Gewuenschtes vorhandenes Backup einsetzen.

# Nur prüfen; die Zieldatenbank bleibt unverändert.
.\backend\.venv\Scripts\python.exe backend/scripts/restore_sqlite_db.py --backup $Backup --database $Database
if ($LASTEXITCODE -ne 0) { throw 'Backup-Pruefung fehlgeschlagen.' }
```

Jetzt das Backend im zugehörigen Terminal mit **Strg+C** sauber beenden und
warten, bis es beendet ist. Auch andere Zugriffe auf diese Datenbank schließen.
Anschließend in derselben PowerShell:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/restore_sqlite_db.py --backup $Backup --database $Database --backup-dir backend/backups --apply --backend-stopped
if ($LASTEXITCODE -ne 0) { throw 'Restore fehlgeschlagen; Fehlermeldung pruefen.' }
```

Danach das Backend mit deinem bisherigen Startbefehl starten und Anmeldung,
Semester, Kurse und Stundenplan prüfen.

## 2. Testserver: Backup erstellen

### Von Windows PowerShell verbinden

Zugriff aus dem internen Netz oder über das Campus-VPN:

```powershell
ssh -p 17655 admin_b50578@10.155.11.130
```

### In der SSH-Sitzung: Container prüfen und Backup erstellen

Die folgenden Befehle gehören in die **Linux-Shell auf dem Testserver**.
`CONTAINER` ändern, falls die Liste einen anderen Namen zeigt.

```bash
sudo docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
CONTAINER=planner-ressources-poc

# Nur Datenbankpfad und Daten-Mounts anzeigen.
sudo docker exec "$CONTAINER" printenv DATABASE_URL
sudo docker inspect --format '{{range .Mounts}}{{println .Destination .Type .Source}}{{end}}' "$CONTAINER"

sudo docker exec "$CONTAINER" python scripts/backup_sqlite_db.py --database /data/planner.db --output-dir /data/backups
```

Die folgenden Docker-Beispiele setzen voraus, dass die Anwendung tatsächlich
`/data/planner.db` verwendet und `/data` als Volume oder Verzeichnis eingebunden
ist. Bei abweichender Ausgabe die Pfade entsprechend ändern. Der Backup-Befehl
meldet zum Beispiel `Backup created: /data/backups/planner-20261103-100307.db`.
Immer den **neu ausgegebenen** Namen verwenden:

```bash
BACKUP=planner-20261103-100307.db
mkdir -p "$HOME/planner-backups"
chmod 700 "$HOME/planner-backups"
sudo docker cp "$CONTAINER:/data/backups/$BACKUP" "$HOME/planner-backups/$BACKUP" &&
sudo chown "$(id -u):$(id -g)" "$HOME/planner-backups/$BACKUP" &&
chmod 600 "$HOME/planner-backups/$BACKUP"
```

Die Kopie liegt weiterhin auf dem Testserver. Für eine Kopie auf deinen PC in
einer **zweiten Windows PowerShell** ausführen:

```powershell
Set-Location C:\Codex\planner-resource
New-Item -ItemType Directory -Force backend/backups | Out-Null
$BackupName = 'planner-20261103-100307.db' # Namen des gerade erstellten Backups einsetzen.
scp -P 17655 "admin_b50578@10.155.11.130:planner-backups/$BackupName" "backend/backups/$BackupName"
if ($LASTEXITCODE -ne 0) { throw 'Download fehlgeschlagen.' }
```

Bei `ssh` ist der Port-Schalter **`-p`**, bei `scp` **`-P`**.

## 3. Testserver: Backup wiederherstellen

### Einmalig die vorhandenen Restore-Werkzeuge hochladen

Das aktuelle Dockerfile liefert nur das Backup-Skript mit. Deshalb beide
zusammengehörigen Skripte aus diesem Projekt hochladen. Diese Befehle gehören
in **Windows PowerShell**, außerhalb der SSH-Sitzung:

```powershell
Set-Location C:\Codex\planner-resource
ssh -p 17655 admin_b50578@10.155.11.130 'mkdir -p ~/planner-db-tools && chmod 755 ~/planner-db-tools'
if ($LASTEXITCODE -ne 0) { throw 'Werkzeugordner konnte nicht erstellt werden.' }
scp -P 17655 backend/scripts/backup_sqlite_db.py backend/scripts/restore_sqlite_db.py admin_b50578@10.155.11.130:planner-db-tools/
if ($LASTEXITCODE -ne 0) { throw 'Upload der Werkzeuge fehlgeschlagen.' }
```

### Backup auswählen und prüfen

Wieder in der **SSH-Sitzung auf dem Testserver** ausführen. Der ausgewählte
Backup-Dateiname muss bereits unter `/data/backups` liegen.

```bash
CONTAINER=planner-ressources-poc
BACKUP=planner-20261103-100307.db
chmod 644 "$HOME/planner-db-tools/backup_sqlite_db.py" "$HOME/planner-db-tools/restore_sqlite_db.py"

# Exakte lokal vorhandene Image-ID des bestehenden Containers verwenden.
IMAGE=$(sudo docker inspect --format '{{.Image}}' "$CONTAINER")

# Nur pruefen; noch keine Wiederherstellung.
sudo docker run --rm --network none --volumes-from "$CONTAINER" \
  --mount "type=bind,source=$HOME/planner-db-tools,target=/restore-tools,readonly" \
  --entrypoint python "$IMAGE" /restore-tools/restore_sqlite_db.py \
  --backup "/data/backups/$BACKUP" --database /data/planner.db
```

Nur nach erfolgreicher Prüfung fortfahren. Ein temporärer Hilfscontainer führt
das Restore-Skript aus; sein normaler Anwendungsstart wird durch `--entrypoint`
ersetzt. Dadurch funktioniert der Restore auch bei gestopptem App-Container.

### Stoppen, wiederherstellen und starten

```bash
sudo docker stop --time 30 "$CONTAINER" &&
sudo docker run --rm --network none --volumes-from "$CONTAINER" \
  --mount "type=bind,source=$HOME/planner-db-tools,target=/restore-tools,readonly" \
  --entrypoint python "$IMAGE" /restore-tools/restore_sqlite_db.py \
  --backup "/data/backups/$BACKUP" --database /data/planner.db \
  --backup-dir /data/backups --apply --backend-stopped &&
sudo docker start "$CONTAINER"
```

Durch `&&` erfolgt der nächste Schritt nur bei Erfolg. Bei fehlgeschlagenem
Restore bleibt die Anwendung gestoppt; zuerst die Fehlermeldung prüfen.

```bash
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
sudo docker logs --tail 50 "$CONTAINER"
```

Den Healthstatus nach der Startphase prüfen. Danach im Browser anmelden und
Semester, Kurse und Stundenplan kontrollieren. Bootstrap ist bei einer aus dem
Backup wiederhergestellten bestehenden Installation nicht erforderlich.

### Optional: Backup vom PC zum Testserver übertragen

Falls das gewünschte Backup nur lokal liegt, zuerst in **Windows PowerShell**:

```powershell
Set-Location C:\Codex\planner-resource
scp -P 17655 backend/backups/planner-20261103-100307.db admin_b50578@10.155.11.130:planner-restore-upload.db
if ($LASTEXITCODE -ne 0) { throw 'Backup-Upload fehlgeschlagen.' }
```

Dann in der **SSH-Sitzung**, solange der App-Container noch läuft:

```bash
CONTAINER=planner-ressources-poc
sudo docker exec -i "$CONTAINER" sh -c 'mkdir -p /data/backups && umask 077 && cat > /data/backups/restore-input.db' < "$HOME/planner-restore-upload.db"
```

Nur nach erfolgreicher Übertragung mit Abschnitt 3 fortfahren und dort
`BACKUP=restore-input.db` setzen. Der feste Dateiname ist eine Eingangsdatei;
ein erneuter Upload ersetzt diese Eingangsdatei. Der eigentliche Restore
ersetzt die aktive Datenbank erst im Schritt mit `--apply`.

## 4. Lokal: Docker Desktop

Falls dein lokaler Server in Docker läuft, diesen Abschnitt anstelle von
Abschnitt 1 verwenden. Alles hier läuft in **Windows PowerShell**.

### Backup

```powershell
Set-Location C:\Codex\planner-resource
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
$Container = 'planner-ressources' # Tatsaechlichen lokalen Namen einsetzen.
docker exec $Container printenv DATABASE_URL
docker inspect --format '{{range .Mounts}}{{println .Destination .Type .Source}}{{end}}' $Container

docker exec $Container python scripts/backup_sqlite_db.py --database /data/planner.db --output-dir /data/backups
if ($LASTEXITCODE -ne 0) { throw 'Backup fehlgeschlagen.' }

# Namen aus der Erfolgsausgabe einsetzen.
$BackupName = 'planner-20261103-100307.db'
New-Item -ItemType Directory -Force backend/backups | Out-Null
docker cp "${Container}:/data/backups/$BackupName" "backend/backups/$BackupName"
if ($LASTEXITCODE -ne 0) { throw 'Backup-Kopie fehlgeschlagen.' }
```

Auch hier müssen Datenbankpfad und `/data`-Mount zur Ausgabe passen.

### Restore eines Backups aus diesem lokalen Container

Der Dateiname muss im lokalen Container unter `/data/backups` vorhanden sein.

```powershell
Set-Location C:\Codex\planner-resource
$Container = 'planner-ressources'
$BackupName = 'planner-20261103-100307.db'
$Tools = (Resolve-Path backend/scripts).Path
$Image = docker inspect --format '{{.Image}}' $Container
if ($LASTEXITCODE -ne 0) { throw 'Container konnte nicht gelesen werden.' }

docker run --rm --network none --volumes-from $Container --mount "type=bind,source=$Tools,target=/restore-tools,readonly" --entrypoint python $Image /restore-tools/restore_sqlite_db.py --backup "/data/backups/$BackupName" --database /data/planner.db
if ($LASTEXITCODE -ne 0) { throw 'Backup-Pruefung fehlgeschlagen.' }

docker stop --time 30 $Container
if ($LASTEXITCODE -ne 0) { throw 'Container konnte nicht gestoppt werden.' }

docker run --rm --network none --volumes-from $Container --mount "type=bind,source=$Tools,target=/restore-tools,readonly" --entrypoint python $Image /restore-tools/restore_sqlite_db.py --backup "/data/backups/$BackupName" --database /data/planner.db --backup-dir /data/backups --apply --backend-stopped
if ($LASTEXITCODE -ne 0) { throw 'Restore fehlgeschlagen; Container bleibt gestoppt.' }

docker start $Container
if ($LASTEXITCODE -ne 0) { throw 'Containerstart fehlgeschlagen.' }
docker logs --tail 50 $Container
```

### Optional: heruntergeladenes Backup lokal in Docker verwenden

Solange der lokale App-Container noch läuft, die Datei mit einem eigenen
Eingangsnamen bereitstellen. Das zusätzliche Werkzeug-Mount erlaubt dem
Containerbenutzer, die Datei selbst ins Datenvolume zu kopieren:

```powershell
Set-Location C:\Codex\planner-resource
$Container = 'planner-ressources'
$BackupName = 'planner-20261103-100307.db'
$InputFile = (Resolve-Path "backend/backups/$BackupName").Path
$Image = docker inspect --format '{{.Image}}' $Container
if ($LASTEXITCODE -ne 0) { throw 'Container konnte nicht gelesen werden.' }

docker run --rm --network none --volumes-from $Container --mount "type=bind,source=$InputFile,target=/restore-input.db,readonly" --entrypoint sh $Image -c 'mkdir -p /data/backups && cp /restore-input.db /data/backups/restore-input.db'
if ($LASTEXITCODE -ne 0) { throw 'Bereitstellung des Backups fehlgeschlagen.' }
```

Danach den lokalen Docker-Restore oben ausführen und dort
`$BackupName = 'restore-input.db'` setzen.

## Wenn das Restore-Skript abbricht

- Bei `SQLite sidecar exists` sind noch WAL-, SHM- oder Journal-Dateien
  vorhanden. Diese nicht einfach löschen. Zuerst alle Datenbanknutzer sauber
  stoppen und den SQLite-Zustand klären; anschließend erneut versuchen.
- Bei `Backup file not found` den Dateinamen und den jeweiligen Rechner prüfen.
  Ein Windows-Pfad ist kein Containerpfad.
- Bei einer ungültigen Datei oder fehlenden Planner-Tabellen ein anderes,
  geprüftes Backup verwenden.
- Bei Zugriffsfehlern Mounts, Containerbenutzer und Berechtigungen prüfen.
  Die Hilfscontainer verwenden den Standardbenutzer des vorhandenen Images.
  Die Beispiele setzen voraus, dass der App-Container diesen ebenfalls verwendet.

Die Befehle löschen weder das Datenvolume noch Backups. Bei vollständigem
Verlust der Installation müssen zusätzlich Image und Deployment-Konfiguration
aus einer getrennten Sicherung wiederhergestellt werden.
