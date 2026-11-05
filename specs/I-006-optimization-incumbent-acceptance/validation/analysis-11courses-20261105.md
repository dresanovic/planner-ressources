# Analyse des gespeicherten 11-LV-Laufs

Datum:2026-11-05. Nur lesende Datenbankanalyse und reine Validierung; kein Termin, keine Stammdaten und keine Solverregel geändert. Quelle: Benutzer-Abschlussmeldung und aktuelle lokale Datenbank backend/planner.db, neuester gespeicherter Optimierungslauf für Semester1/Revision1, LV49–59.

## Ergebnis

48 gespeicherte Termine,10LV mit Terminen,1LV ohne Termine,0vollständigeLV.192von358LE geplant(53,6%),166offen. Lauf24,3s bei300sBudget; kein Timeout. Alle48Termine haben4LE. Kein gespeicherter ausgewählter Termin liegt auf einem Hochschulfeiertag.

| LV | Termine | Soll LE | Geplant | Offen |
|---|---:|---:|---:|---:|
| Angewandte Forschung und Entwicklung in der Wirtschaftsinformatik |4|26|16|10|
| Unternehmensgründung in der IT |6|34|24|10|
| Communication & Presentation |0|34|0|34|
| Operation Research |7|34|28|6|
| Informationssicherheitsmanagement |8|34|32|2|
| Seminar zur Masterarbeit1 |3|34|12|22|
| Systems Engineering & Analytisches Denken |3|34|12|22|
| Begleitendes FuE Projekt |6|34|24|10|
| Gesellschafts- und Vertragsrecht |4|34|16|18|
| Consulting Methoden |3|26|12|14|
| Integration elekt. Geschäftsprozesse |4|34|16|18|
| Gesamt |48|358|192|166|

## Konkreter Engpass und Fehler im Suchraum

Alle11LV gehören zur selben Kohorte MA IT & Wirtschaftsinformatik -2.Semester und zum berufsbegleitenden Studientyp. Aktive Fenster: Freitag16:00–22:00, Samstag08:15–15:00. Terminlängen2–4LE. Zeitraum19.02.–17.08.2027 enthält26Freitage+26Samstage.20.03.,26.03.,27.03.und01.05. sind unterrichtsfrei:25Freitage+23Samstage=48nutzbare Tage.

Der aktuelle Kandidatengenerator erzeugt jede Alternative ausschließlich mit window.start_time (backend/app/services/semester_optimization.py,generate_candidates,ca.Zeile302/329). Alle ausgewählten LV starten damit am selben Freitag16:00 bzw.Samstag08:15. Wegen gemeinsamer Kohorte darf nur eine dieser überlappenden Alternativen gewählt werden. Maximal4LE pro Termin ergeben48x4=192LE. Alle48Tage sind so belegt, aber die späteren Teile der langen Fenster bleiben ungenutzt. Das ist eine Einschränkung des erzeugten Suchraums, kein belegter physischer Kapazitätsmangel der gesamten Zeitfenster.

Konkretes Gegenbeispiel: Am19.02.2027 liegt ein vorhandener4LE-Termin16:00–19:30. Für die bislang leere LV Communication & Presentation ist ein zusätzlicher2LE-Termin19:40–21:20 innerhalb des zugelassenen Freitagfensters möglich. Zwei zulässige Lehrpersonen/Ressourcenkombinationen wurden überprüft. Die gesamte11LV-Zuordnung mit diesem Zusatz besteht validate_exact_candidate gegen aktuelle Kurs-/Fenster-/Ressourcen-/Feiertags-/Prüfungs-/Kohortenregeln und feste Belegung:194statt192LE. Kein Schreiben oder Speichern dieses Gegenbeispiels. Es zeigt nicht das tatsächliche Maximum; weitere Platzierungen wurden nicht optimiert.

Die angezeigte Obergrenze192/Optimalitätsaussage ist daher nur für den eingeschränkten enumerierten Kandidatenraum belegt und darf nicht als vollständiger Maximalnachweis aller nach harten Regeln zulässigen Pläne verstanden werden. Mehr Suchzeit allein erweitert diesen Raum nicht.

Communication & Presentation hat zwei zulässige Lehrpersonen und einen zulässigen Raum. Ihre0LE beweisen keine Unplanbarkeit: das Gegenbeispiel liefert2LE zusätzlich. Der bestehende Optimierer maximiert Gesamt-LE und nachrangige Ziele; eine Mindestabdeckung/Fairness pro LV ist nicht Bestandteil der genehmigten Ziele.

## Weitere irreführende Anzeige

- INSTITUTION_HOLIDAY bezeichnet ausgeschlossene mögliche Termine, nicht gespeicherte Regelverstöße; die aktuelle allgemeine Meldung suggeriert fälschlich einen gespeicherten Feiertagstermin.
- SELECTED_COURSE_COMPETITION wird als generischer Aktionsfehler statt als Konkurrenz um gemeinsame Kapazität erklärt.
- improved_partial erscheint selbst für0LE als teilweise verbessert; das Ergebnis sollte neutral als unvollständig beschrieben werden.

Diese Analyse widerlegt die frühere pauschale Annahme, es seien ausschließlich manuelle Nachweise offen. Neuer konkreter Suchraum-/Nachweisfehler plus Anzeigegaps sind dokumentiert. Keine Produktionskorrektur in diesem Analyseauftrag, keine neue Korrekturrunde verbraucht:3/5abgeschlossen,aktuellkeine. Vor Implementierung sind Fehlerumfang/Tests und unabhängige Konvergenz wieder aufzunehmen; genehmigte Hardrules/Zielprioritäten nicht stillschweigend um Fairness erweitern. Goal4bleibt nicht bereit.
