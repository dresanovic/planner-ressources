# Kontrolle der importierten Daten für 2027 S

Prüfdatum: 03.11.2026. Anwendung: `http://10.155.11.130:8081/`.

## Ergebnis

Die eingetragenen Daten stimmen mit den zuletzt bestätigten Importdateien und
Benutzervorgaben überein. Es wurden keine fehlenden LVs, Dubletten, abweichenden
Unterrichtseinheiten, falschen Kohortenzuordnungen oder abweichenden
Ressourcenberechtigungen gefunden.

Die Prüfung erfolgte ausschließlich lesend über die angemeldete Weboberfläche.
Bearbeitungsansichten wurden zum Ablesen geöffnet und ohne Speichern geschlossen.
Es wurden keine Eingaben verändert, keine Importe gestartet und kein Plan erzeugt.
Nach der Prüfung zeigt die Anwendung weiterhin „Keine Revision verfügbar“ und
„Es gibt noch keine Planungsrevision“.

## Vollständig geprüfter Umfang

| Bereich | Ergebnis |
|---|---|
| Semester | 2027 S, aktiv, 19.02.2027–17.08.2027 |
| Kohorten | Alle zehn vorhanden und aktiv; Größen siehe unten |
| Lehrveranstaltungen | 94 vorhanden und aktiv; exakt dieselben 94 Namen wie in den zehn ausgewählten Teilimporten |
| LV-Einheiten | Alle 94 Gesamt-UE entsprechen den gerundeten Importwerten; Minimum 2 UE und Maximum 4 UE bei allen LVs |
| Semester / Kohorte / Studienform je LV | Alle 94 Zuordnungen stimmen mit den Teilimportdateien überein |
| Lehrende | 73 aktive Personen, Namen und Referenzcodes vollständig mit `lecturers.json` abgeglichen |
| Räume | 121 aktive Räume, Referenzcodes und Kapazitäten vollständig gegen die importierbaren Quellräume abgeglichen |
| Berechtigte Ressourcen | Alle 94 Ressourcenansichten geprüft; vollständige ausgewählte Personen- und Raummengen stimmen mit den jeweiligen Teilimportdateien überein |
| Raumkapazitäten | Sämtliche ausgewählten LV-Räume haben mindestens so viele Plätze wie die zugeordnete Kohorte Studierende |
| Studienformen | Vollzeit und Berufsbegleitend vorhanden und aktiv |
| Kalender | Genau 15 Einträge; Datumswerte und Namen vollständig gegen `nonteaching-AT-2027-S.json` abgeglichen |

Der Vergleich berücksichtigt die letzten Korrekturen in den Teilimporten und nicht
die ursprüngliche, noch unvollständige Hauptzuordnungsdatei.

## Kohorten und Umfang

| Kohorte | Studierende | LVs |
|---|---:|---:|
| Business Analytics & AI – 2. Semester | 30 | 10 |
| Business Analytics & AI – 4. Semester | 30 | 6 |
| Business Analytics & AI – 6. Semester | 30 | 4 |
| Business Software Development – 2. Semester | 25 | 8 |
| Business Software Development – 4. Semester | 25 | 10 |
| Business Software Development – 6. Semester | 25 | 10 |
| MA IT & Wirtschaftsinformatik – 2. Semester | 65 | 11 |
| Wirtschaftsinformatik – 2. Semester | 40 | 12 |
| Wirtschaftsinformatik – 4. Semester | 40 | 11 |
| Wirtschaftsinformatik – 6. Semester | 40 | 12 |
| Gesamt | | **94** |

## Besondere Vorgaben

- Mathematik 2 bei BAAI 2: ausschließlich Hatzl, Johannes berechtigt.
- Betriebswirtschaftslehre bei BAAI 2: Koch, Volker und Meglitsch, Mario berechtigt.
- Business IT-Applications bei BAAI 2: Gerzic, Harris und Wipfler, Yevheniia berechtigt.
- Alle elf Master-LVs: ausschließlich RC409 als Raum, Kapazität 78 für 65 Studierende.
- Alle 35 Wirtschaftsinformatik-LVs: ausschließlich CZ107, CZ108, CZ109 und CZ110;
  keine RC-Räume, kein zu kleiner CZ106. Die kleinste ausgewählte Kapazität ist 45
  für jeweils 40 Studierende.
- Die vorher bestätigten unterschiedlichen Raumumfänge der ersten BAAI-Teilimporte
  bleiben erhalten: BAAI 2 und 4 haben CZ108/RC409; BAAI 6 und die BSD-Teilimporte
  verwenden die später erweiterte Auswahl. Diese Unterschiede entsprechen den
  jeweiligen bestätigten Teilimportdateien.
- Bachelorprüfungen, eigenständige Masterarbeit und Masterprüfung sind ausgeschlossen.
  Die ausdrücklich beibehaltene Bachelorarbeit und das Seminar zur Masterarbeit 1
  sind vorhanden. „Accompanying Project“ mit 0 UE ist nicht importiert.
- Alle sechs gesetzlichen Feiertage sind vorhanden. Osterferien sind lückenlos
  vom 20.03. bis einschließlich 29.03.2027 gesperrt; der 29.03. heißt Ostermontag.

## Zeitfenster und verbleibende fachliche Festlegungen

Alle fünf Zeitfenster sind aktiv:

| Studienform | Tage | Zeit |
|---|---|---|
| Vollzeit | Montag, Dienstag, Mittwoch | jeweils 08:15–17:00 |
| Berufsbegleitend | Freitag | 16:00–22:00 |
| Berufsbegleitend | Samstag | 08:15–15:00 |

Der Mittwoch beginnt inzwischen korrekt um 08:15. **Für Vollzeit sind Donnerstag
und Freitag derzeit nicht freigegeben.** Das ist kein Widerspruch zum zuletzt
gezeigten Zeitfensterstand, aber für die spätere Planung relevant: Falls an diesen
Tagen ebenfalls Vollzeitunterricht stattfinden soll, fehlen entsprechende Fenster.
Diese Kontrolle nimmt keine solche Änderung vor.

Der Wunschwert 3 UE ist im vorhandenen Optimierer die Mitte zwischen den gespeicherten
Grenzen 2 und 4; er ist kein separat gespeichertes Pflichtfeld und erzwingt nicht
die Länge jedes Termins. Die Terminverteilung geteilter LVs auf beide Lehrenden
bleibt später manuell vorzunehmen. Raumausstattung und fachliche Raumgeeignetheit
sind aus dem Raumexport nicht vollständig nachweisbar. Eine Machbarkeitsprüfung
oder Stundenplangenerierung wurde ausdrücklich nicht durchgeführt.

## Nachweise

Die abgelesenen Oberflächenwerte und das Vergleichsergebnis liegen unter
`artifacts/export-import/validation/`:

- `live-courses-2026-11-03.json`: vollständige akademische Werte aller 94 LVs.
- `live-eligibility-2026-11-03.json`: alle ausgewählten Lehrenden und Räume je LV.
- `live-lecturers-2026-11-03.json`, `live-rooms-2026-11-03.json` und
  `live-cohorts-2026-11-03.json`: abgeglichene Stammdaten.
- Textnachweise für Semester, Studienformen, Zeitfenster, Feiertage und unveränderten Kalenderzustand.
- `comparison-2026-11-03.json`: zusammengefasstes Ergebnis ohne festgestellte Datenabweichungen.

Die Kontrolle belegt den sichtbaren Anwendungsstand zum Prüfzeitpunkt. Sie bestätigt
keine spätere unveränderte Datenlage und ersetzt nicht das Datenbankbackup.
