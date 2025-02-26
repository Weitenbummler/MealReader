#!/usr/bin/env python3
from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import configparser
from datetime import datetime

app = Flask(__name__)
CORS(app)  # CORS aktivieren

# Konfiguration laden
config = configparser.ConfigParser()
config.read("config.ini")

USERNAME = config.get("credentials", "username")
PASSWORD = config.get("credentials", "password")

# Aliasse als Dictionary: Schlüssel in Kleinbuchstaben
aliases = {}
if config.has_section("aliases"):
    for key in config["aliases"]:
        aliases[key.strip().lower()] = config["aliases"][key].strip()

# Display-Konfiguration
ORDER_YES_COLOR = config.get("display", "order_yes_color", fallback="#00ff00")
ORDER_NO_COLOR = config.get("display", "order_no_color", fallback="#ff0000")
HEADER_BG_COLOR = config.get("display", "header_bg_color", fallback="#f0f0f0")
ROW_BG_COLOR = config.get("display", "row_bg_color", fallback="#ffffff")
TITLE_BG_COLOR = config.get("display", "title_bg_color", fallback="#333333")
CHILDREN_BG_COLOR = config.get("display", "children_bg_color", fallback="#444444")
CELL_PADDING = config.get("display", "cell_padding", fallback="12px")
TABLE_BORDER_SPACING = config.get("display", "table_border_spacing", fallback="10px")
PAGE_BG_COLOR = config.get("display", "page_bg_color", fallback="#000000")
TITLE_TEXT_COLOR = config.get("display", "title_text_color", fallback="#ffffff")
CHILDREN_TEXT_COLOR = config.get("display", "children_text_color", fallback="#ffffff")
CELL_TEXT_COLOR = config.get("display", "cell_text_color", fallback="#cccccc")
ORDER_YES_TEXT_COLOR = config.get("display", "order_yes_text_color", fallback="#000000")
ORDER_NO_TEXT_COLOR = config.get("display", "order_no_text_color", fallback="#000000")

# URLs – bitte ggf. anpassen
LOGIN_URL = 'https://www.milchbart-bestellung.de/login/'
MEALS_URL = 'https://www.milchbart-bestellung.de/kunden/essen/'

def login_and_fetch_html():
    """
    Loggt sich ein und liefert den HTML-Code der Seite mit dem Wochenmenüplan.
    """
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
    }
    # GET der Login-Seite (zum Erhalt des CSRF-Tokens)
    get_resp = session.get(LOGIN_URL, headers=headers)
    if get_resp.status_code != 200:
        raise Exception(f"GET Login-Seite fehlgeschlagen: {get_resp.status_code}")
    soup = BeautifulSoup(get_resp.text, 'html.parser')
    csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if not csrf_input or not csrf_input.get("value"):
        raise Exception("Kein CSRF-Token gefunden.")
    csrf_token = csrf_input["value"]

    # POST-Login
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf_token,
        "next": "/kunden/essen/"
    }
    headers["Referer"] = LOGIN_URL
    post_resp = session.post(LOGIN_URL, data=payload, headers=headers)
    if "id=\"login_form\"" in post_resp.text:
        raise Exception("Login fehlgeschlagen – Login-Formular wird erneut angezeigt.")

    # GET der Zielseite (Wochenmenüplan)
    meals_resp = session.get(MEALS_URL, headers=headers)
    if meals_resp.status_code != 200:
        raise Exception(f"Abfrage der Essen-Seite fehlgeschlagen: {meals_resp.status_code}")
    return meals_resp.text

def extract_menu_plans(html):
    """
    Parst den HTML-Code und extrahiert pro Panel (Klasse "panel-mealplan")
    den (aliasierten) Kindnamen, den Meal-Typ sowie für jeden Wochentag:
      - Gerichtstext (aus der ersten Zeile im <tbody>)
      - Bestellmenge (aus der Zeile mit div.order-quantity)
    """
    soup = BeautifulSoup(html, 'html.parser')
    panels = soup.find_all("div", class_="panel-mealplan")
    plans = []
    for panel in panels:
        child_elem = panel.find("span", class_="childname")
        extracted_name = " ".join(child_elem.get_text().split()) if child_elem else None
        child = aliases.get(extracted_name.lower(), extracted_name)

        table = panel.find("table", class_="food-order")
        if not table:
            continue

        # Extrahiere die Tage aus dem <thead> (ab der 2. Zelle)
        headers = []
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                ths = header_row.find_all("th")
                for th in ths[1:]:
                    headers.append(th.get_text(strip=True))
        
        tbody = table.find("tbody")
        if not tbody:
            continue
        rows = tbody.find_all("tr")
        if not rows:
            continue
        # Erste Zeile: Meal-Typ in erster Zelle und Gerichtstexte in den folgenden Zellen
        dish_row = rows[0]
        dish_cells = dish_row.find_all("td")
        if len(dish_cells) < 2:
            continue
        meal_type = dish_cells[0].get_text(strip=True)
        day_data = {}
        for i, cell in enumerate(dish_cells[1:]):
            dish_text = cell.get_text(separator=" ", strip=True)
            day_header = headers[i] if i < len(headers) else f"Tag {i+1}"
            day_data[day_header] = {"dish": dish_text, "ordered": 0}
        
        # Suche nach der Zeile mit Bestellmengen
        order_row = None
        for row in rows[1:]:
            if row.find("div", class_="order-quantity"):
                order_row = row
                break
        if order_row:
            order_cells = order_row.find_all("td")
            for i, cell in enumerate(order_cells):
                order_div = cell.find("div", class_="order-quantity")
                qty = 0
                if order_div:
                    text = order_div.get_text(strip=True)
                    parts = text.split(":")
                    if len(parts) > 1:
                        try:
                            qty = int(parts[1].strip())
                        except ValueError:
                            qty = 0
                if i < len(headers):
                    day_header = headers[i]
                    if day_header in day_data:
                        day_data[day_header]["ordered"] = qty
                    else:
                        day_data[day_header] = {"ordered": qty}
        plans.append({
            "child": child,
            "meal_type": meal_type,
            "days": day_data
        })
    return plans

def sort_day_keys(day_keys):
    """Sortiert Tages-Header (Format: 'Wochentag, dd.mm.yy') aufsteigend nach Datum."""
    def sort_key(day_str):
        parts = day_str.split(',')
        if len(parts) >= 2:
            date_str = parts[1].strip()
            try:
                return datetime.strptime(date_str, "%d.%m.%y")
            except Exception:
                return datetime.min
        return datetime.min
    return sorted(day_keys, key=sort_key)

@app.route('/')
def index():
    try:
        html = login_and_fetch_html()
        plans = extract_menu_plans(html)
        day_set = set()
        for plan in plans:
            day_set.update(plan.get("days", {}).keys())
        sorted_days = sort_day_keys(list(day_set))
        # Erzeuge drei Headerzeilen: 
        # Header 1: Datum (nur dd.mm.yy)
        # Header 2: Wochentag
        # Header 3: Gericht (repräsentativ aus erstem Panel)
        header_date = []
        header_weekday = []
        header_dish = []
        if plans and plans[0].get("days"):
            for day in sorted_days:
                parts = day.split(',')
                if len(parts) >= 2:
                    header_date.append(parts[1].strip())
                    header_weekday.append(parts[0].strip())
                else:
                    header_date.append(day)
                    header_weekday.append(day)
                dish = plans[0]["days"].get(day, {}).get("dish", "-")
                header_dish.append(dish)
        return render_template(
            'index.html',
            children=plans,
            sorted_days=sorted_days,
            header_date=header_date,
            header_weekday=header_weekday,
            header_dish=header_dish,
            title_bg_color=TITLE_BG_COLOR,
            children_bg_color=CHILDREN_BG_COLOR,
            order_yes_color=ORDER_YES_COLOR,
            order_no_color=ORDER_NO_COLOR,
            order_yes_text_color=ORDER_YES_TEXT_COLOR,
            order_no_text_color=ORDER_NO_TEXT_COLOR,
            cell_padding=CELL_PADDING,
            table_border_spacing=TABLE_BORDER_SPACING,
            page_bg_color=PAGE_BG_COLOR,
            title_text_color=TITLE_TEXT_COLOR,
            children_text_color=CHILDREN_TEXT_COLOR,
            cell_text_color=CELL_TEXT_COLOR
        )
    except Exception as e:
        return f"<p>Fehler: {str(e)}</p>", 500

@app.route('/menu', methods=['GET'])
def menu():
    try:
        html = login_and_fetch_html()
        plans = extract_menu_plans(html)
        return jsonify({"children": plans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/no_lunch_today', methods=['GET'])
def no_lunch_today():
    """
    Gibt als JSON eine Liste der Kindnamen zurück, die am heutigen Datum kein Mittagessen bestellt haben.
    Es wird angenommen, dass die Tagesangaben im Format "Wochentag, dd.mm.yy" vorliegen.
    """
    try:
        html = login_and_fetch_html()
        plans = extract_menu_plans(html)
        today_str = datetime.now().strftime("%d.%m.%y")
        result = []
        for plan in plans:
            for day, data in plan.get("days", {}).items():
                parts = day.split(',')
                if len(parts) >= 2 and parts[1].strip() == today_str:
                    if data.get("ordered", 0) == 0:
                        result.append(plan["child"])
                    break
        return jsonify({"no_lunch_today": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
