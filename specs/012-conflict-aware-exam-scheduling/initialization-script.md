# Initialisierung fehlender Prüfungsanforderungen

Ein eigenständiges Python-Skript nutzt die authentifizierte Planner-API, ohne
Planung oder Version anzulegen. Ein Semester wird explizit ausgewählt. Ohne
`--apply` erfolgen ausschließlich lesende Fachoperationen (An-/Abmeldung sind
auch für die Vorschau notwendig).

Für jede LV des Semesters ohne gespeicherte Konfiguration werden vorgeschlagen:
Prüfungsbezeichnung „Prüfung“, Prüfungsart „Schriftlich“, 90 Minuten (2 UE ohne
Pause), erforderliche Raumkapazität gleich der LV-Gruppengröße und die in der LV
angezeigte Lehrperson. Es wird kein Raum fest zugeteilt. Mehrere zulässige
Lehrpersonen folgen der bestehenden LV-Anzeige (erste zugeordnete Lehrperson).
Vorhandene, auch deaktivierte Konfigurationen bleiben erhalten.

Inaktive oder nicht über die Planungsoptionen verfügbare LVs, fehlende/inaktive
Lehrpersonen und ungültige Gruppengrößen werden mit Grund übersprungen. Fehlende
Lehrtermine oder Planungszeitfenster allein verhindern keine Initialisierung.
Ein Bericht führt jede LV aus der Semester-Prüfungsübersicht auf.

Beim Schreiben werden die LV-Daten und Anforderungen erneut gelesen. Änderungen
gegenüber der Vorschau werden übersprungen. `expectedRevision: null` verhindert
das Überschreiben einer gleichzeitig neu angelegten Konfiguration. Bei API- oder
Transportfehlern wird abgebrochen; bereits gespeicherte Anforderungen bleiben
erhalten. Erneute Ausführung legt nur weiterhin fehlende Anforderungen an.
Passwörter werden verdeckt abgefragt; entfernte Zugriffe benötigen HTTPS.

Validierung: Tests für Vorschau ohne Schreibzugriffe, Werteübernahme,
Bestandsschutz, fehlende Zuordnung, veränderte Daten, gleichzeitige Anlage und
Abbruch bei unklarem Schreibresultat. Keine Live-Änderungen bei der Entwicklung.
