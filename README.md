# MealReader

MealReader ist eine Python/Flask-Anwendung, die sich automatisch in eine Meal-Ordering-Website (https://www.schulmenueplaner.de) einloggt, den Wochenmenüplan für Kinder abruft und die Daten sowohl als JSON-API als auch in einer modernen HTML-Tabelle darstellt.

## Features

- **Automatischer Login & Datenextraktion**  
  MealReader loggt sich mit den in der Konfigurationsdatei hinterlegten Zugangsdaten in die Ziel-Website ein und ruft den aktuellen Wochenmenüplan ab. Mithilfe von BeautifulSoup werden die HTML-Daten geparst und pro Kind werden der Meal-Typ sowie für jeden Tag das Gericht und der Bestellstatus (0 oder 1) extrahiert.

- **Alias-Unterstützung für Kindernamen**  
  Über die `config.ini` kannst du Aliasse (Kosenamen oder Vornamen) für die Kinder definieren. Wird ein Alias definiert, so wird dieser anstelle des vollen Namens in der Darstellung verwendet.

- **Moderne HTML-Tabelle**  
  Die Startseite (`/`) zeigt eine Tabelle mit drei Headerzeilen:
  - **Header 1:** Zeigt das Datum (nur dd.mm.yy)
  - **Header 2:** Zeigt den Wochentag
  - **Header 3:** Zeigt das Gericht (repräsentativ aus dem ersten Panel)
  
  Jede Zeile repräsentiert ein Kind, und die Zellen enthalten den Bestellstatus, der farblich hervorgehoben wird. Zusätzlich kannst du über `config.ini` folgende Layout-Parameter konfigurieren:
  - Hintergrundfarbe der gesamten Seite
  - Hintergrund- und Textfarben für die Titelzellen (Header)
  - Hintergrund- und Textfarben für die Kinderspalte
  - Hintergrund- und Textfarben für Bestellstatuszellen (unterschiedlich für "Bestellt" und "Nicht bestellt")
  - Zellabstände (Padding und Border-Spacings)

- **JSON API Endpoint**  
  Über den Endpoint `/menu` werden die Rohdaten als JSON zur Verfügung gestellt – ideal für die Integration in Home Assistant, Node‑RED oder andere Systeme.

- **CORS aktiviert**  
  Cross-Origin Resource Sharing ist aktiviert, sodass externe Systeme problemlos auf den JSON-Endpoint zugreifen können.

## Erforderliche Konfiguration

Erstelle im Projektverzeichnis eine Datei namens `config.ini` und passe die folgenden Einstellungen an:

```ini
[credentials]
username = dein_benutzername
password = dein_passwort

[aliases]
Nachname, Vorname Kind 1 = Kind 1
Nachname, Vorname Kind 2 = Kind 2
Nachname, Vorname Kind 3 = Kind 3

[display]
page_bg_color = #000000
header_bg_color = #1a1a1a
title_bg_color = #333333
children_bg_color = #444444
title_text_color = #ffffff
children_text_color = #ffffff
cell_text_color = #cccccc
order_yes_color = #00ff00
order_no_color = #ff0000
order_yes_text_color = #000000
order_no_text_color = #000000
cell_padding = 12px
table_border_spacing = 10px
```


- **[credentials]:**
Gib hier deinen Benutzernamen und dein Passwort für die Ziel-Website ein.
-	**[aliases]:**
Definiere Aliasse für die vollständigen Kindernamen. Die Schlüssel werden in Kleinbuchstaben verglichen, daher sollten sie exakt (ohne zusätzliche Anführungszeichen) angegeben werden.
-	**[display]:**
  
Konfiguriere alle Anzeigeparameter:

	•	page_bg_color: Hintergrundfarbe der gesamten Seite.
	•	header_bg_color: Hintergrundfarbe für den Seitenheader.
	•	title_bg_color: Hintergrundfarbe für die Headerzellen.
	•	children_bg_color: Hintergrundfarbe für die Kinderspalte.
	•	title_text_color, children_text_color, cell_text_color: Textfarben für Header, Kinderspalte und übrige Zellen.
	•	order_yes_color und order_no_color: Hintergrundfarben für Zellen, die den Bestellstatus anzeigen.
	•	order_yes_text_color und order_no_text_color: Textfarben in den Bestellstatuszellen.
	•	cell_padding und table_border_spacing: Abstände für die Tabelle.

## Wie man das Script ausführt

Lokale Ausführung

1.	Repository klonen:

```
git clone https://github.com/yourusername/mealreader.git
cd mealreader
```

2.	Abhängigkeiten installieren:

Stelle sicher, dass Python 3 installiert ist, und führe im Projektverzeichnis aus:

```
pip install flask flask-cors requests beautifulsoup4
```

3.	Konfiguration anpassen:
   
Bearbeite die config.ini mit deinen Zugangsdaten, Aliassen und Display-Einstellungen.

4.	Anwendung starten:

```
python app.py
```

Standardmäßig läuft die Anwendung auf Port 5002.

	•	HTML-Anzeige: Öffne in deinem Browser http://192.168.10.25:5002/, um die modern formatierte Tabelle zu sehen.
	•	JSON API: Greife auf http://192.168.10.25:5002/menu zu, um die Rohdaten als JSON zu erhalten.

## Als Systemdienst auf Debian

Um MealReader als systemd-Dienst einzurichten, erstelle eine Service-Datei:

1.	Service-Datei erstellen:

Erstelle (als root oder mit sudo) die Datei /etc/systemd/system/mealreader.service mit folgendem Inhalt (passe die Pfade, den Benutzer und die Gruppe an):

```mealreader.service
[Unit]
Description=MealReader Python Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/mealreader
ExecStart=/usr/bin/python3 /path/to/mealreader/app.py
Restart=always
User=youruser
Group=yourgroup
Environment=PATH=/usr/bin:/usr/local/bin
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mealreader

[Install]
WantedBy=multi-user.target
```


2.	Service neu laden und starten:

```
sudo systemctl daemon-reload
sudo systemctl start mealreader.service
sudo systemctl enable mealreader.service
```

3.	Logs überprüfen:

```
sudo journalctl -u mealreader.service -f
```


Jetzt läuft MealReader als Systemdienst dauerhaft und ist über die konfigurierte IP und Port (z. B. http://192.168.nnn.nnn:5002) jederzeit abrufbar.

## Integration in externe Systeme

Home Assistant, Node‑RED oder andere Systeme können den JSON-Endpoint abrufen, indem sie eine HTTP-GET-Anfrage an http://192.168.nnn.nnn:5002/menu senden.

### Zusammenfassung

MealReader automatisiert den Abruf und die Aufbereitung des Wochenmenüplans von einer Meal-Ordering-Website. Es bietet:

	•	Automatischen Login und Datenextraktion
	•	Konfigurierbare Aliasse für Kindernamen
	•	Eine moderne HTML-Tabelle mit drei Headerzeilen (Datum, Wochentag, Gericht) und einer separaten Kinderspalte
	•	Konfigurierbare Farben für Hintergrund und Text (sowohl für Header, Kinderspalte als auch für Bestellstatuszellen)
	•	Einen JSON API Endpoint zur Integration in externe Systeme
	•	Vollständige Konfiguration aller Anzeigeparameter über config.ini
	•	Eine einfache Einrichtung als systemd-Dienst auf Debian

Diese Anwendung ist ideal, um die Essensbestellungen in dein Smart-Home- oder Automationssystem zu integrieren und bietet gleichzeitig eine ansprechende, voll konfigurierbare Web-Oberfläche.

