import streamlit as st
import numpy as np
import pandas as pd
import time
import datetime
from datetime import date
import json
import urllib.request
import streamlit.components.v1 as components
import os

# Variables for api server
api_server = os.environ.get("API_SERVER")

# Set the whole page layout to wide screen
st.set_page_config(layout="wide")

# Load an image for the header
st.image('title_cropped.jpg', use_column_width=True)

# Set title of the page
st.title(' ')
# Components.html to use html and css for editing the title
components.html("<h1 style='text-align: center; color: black; font-family: 'IBM Plex Sans', sans-serif;'>Dashboard "
                "Planungstool</h1>", height=80)

# Create variable map_data and load the data of store locations
map_data = pd.read_csv('Filialdaten.csv')

# Create a dataframe with example data for store kpis
filial_kpi = {'Filiale': ['Filiale 1: Würzburg', 'Filiale 2: Würzburg', 'Filiale 3: Würzburg'],
              'Bestellungen eingegangen': [100, 110, 120],
              'Bestellungen fehlend': [10, 20, 30],
              'Gesamtvolumen heute in €': [10000, 12000, 14000],
              'Gesamtvolumen letzte Woche in €': [9800, 10000, 10200],
              'Bestellung zur Prüfung': [10, 12, 15],
              'lat': [49.792539, 49.788573, 49.783948],
              'lon': [9.928544, 9.936500, 9.934917]}

filial_kpi_f = pd.DataFrame(data=filial_kpi)

# Use lat and lon of the map_data
map_lat_lon = map_data[['name_store', 'lat', 'lon']]

# Create a selectbox in the sidebar with every store in it
filial_select = st.sidebar.selectbox(
    'Filiale auswählen:',
    map_data[['name_store']]
)

# Create three columns for the whole page with beta_columns
map_layout_weather, map_layout_map, map_layout_kpis = st.beta_columns([1, 3, 1])
with map_layout_map:
    # Create checkbox: if its clicked all of the stores are selected, else only the selected store
    if not st.checkbox('Alle Filialen auf der Karte zeigen'):
        for index, row in map_lat_lon.iterrows():
            if filial_select == row['name_store']:
                map_lat_lon = pd.DataFrame({'lat': [row['lat']], 'lon': [row['lon']]})

    # Create the map
    st.map(data=map_lat_lon, zoom=12)

# Create a calender in sidebar with a limited period (only the period with available data)
start_cal = date(2016, 4, 1)
end_cal = date(2019, 4, 30)
calender = st.sidebar.date_input('Datum auswählen: ', value=[end_cal, end_cal],
                                 min_value=start_cal, max_value=end_cal)

# Convert datetime.date to string for api call
first_date_input = calender[0].strftime("%Y-%m-%d")
second_date_input = calender[1].strftime("%Y-%m-%d")

# Checkbox with a dataframe, different kpis
dummy_layout_col1, dummy_layout_col2, dummy_layout_col3 = st.beta_columns([1, 2, 1])
with dummy_layout_col2:
    st.header('Filialübersicht')
    if st.checkbox('Kennzahlen aller Filialen anzeigen'):
        defaultcols = ['Bestellungen eingegangen',
                       'Bestellungen fehlend',
                       'Gesamtvolumen heute in €',
                       'Gesamtvolumen letzte Woche in €',
                       'Bestellung zur Prüfung']
        cols = st.multiselect("Columns", filial_kpi_f.columns.tolist(), default=defaultcols)
        st.dataframe(filial_kpi_f[cols])

# Create variables for each column
best_ein = 100
best_fehl = 201
vol_heute = 1205
vol_woche = 9516
best_pruef = 30

# Show store-specific kpis
for index, row in filial_kpi_f.iterrows():
    if filial_select == row['Filiale']:
        best_ein = row['Bestellungen eingegangen']
        best_fehl = row['Bestellungen fehlend']
        vol_heute = row['Gesamtvolumen heute in €']
        vol_woche = row['Gesamtvolumen letzte Woche in €']
        best_pruef = row['Bestellung zur Prüfung']

# Create containers with html and css code
with map_layout_kpis:
    components.html(f"""
    <style>
    .flex-container {{
        width: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.5em;
        font-family: 'IBM Plex Sans', sans-serif;
        flex-wrap: wrap;
        margin: 0 auto;
        margin-top: 50px;
        }}
    .box {{
        padding: 1em;
        border: 2px solid grey;
        background-color: #F63A67;
        color: white;
        text-align: center;
        border-radius: 15px;
    }}
    </style>
    <div class="flex-container">
        <div class="box"><b>
                Bestellungen eingegangen:<br/>
            </b>
            {best_ein}
        </div>
        <div class="box">
            <b>
                Bestellungen fehlend:<br/>
            </b>
            {best_fehl}
        </div>
        <div class="box">
            <b>
                Gesamtvolumen heute in €:<br/>
            </b>
            {vol_heute}
        </div>
        <div class="box">
            <b>
                Gesamtvolumen letzte Woche in €:<br/>
            </b>
            {vol_woche}
        </div>
        <div class="box">
            <b>
                Bestellung zur Prüfung:<br/>
            </b>
            {best_pruef}
        </div>    
    </div>
    """, height=600, scrolling=True)

# Include weather api from wetter.com via components.html
with map_layout_weather:

    components.html("""
    <div style="margin-top: 3em">
        <div id="wcom-f2cdecaadabcd878abd9695920a63168" class="wcom-default w300x250" 
            style="border: 1px solid #CCC; background-color: #FCFCFC; border-radius: 5px; width: 8em; margin: 0 auto;">
            <link rel="stylesheet" href="//cs3.wettercomassets.com/woys/5/css/w.css" media="all">
            <div class="wcom-city">
                <a style="color: #000" href="https://www.wetter.com/deutschland/wuerzburg/DE0010967.html" 
                    target="_blank" rel="nofollow" aria-label="Wetter Berlin"
                    title="Wetter Würzburg">Wetter Würzburg
                </a>
            </div> 
            <div id="wcom-f2cdecaadabcd878abd9695920a63168-weather"></div>
            <script type="text/javascript" src="//cs3.wettercomassets.com/woys/5/js/w.js"></script>
            <script type="text/javascript"> _wcomWidget({id: 'wcom-f2cdecaadabcd878abd9695920a63168',location: 'DE0010967',
                format: '300x250',type: 'summary'}); 
            </script> 
        </div>
    </div>
""", height=500)

# Create a dummy layout column to center the rest of the application
with dummy_layout_col2:
    # Create header for orders
    st.header('Bestellübersicht')

    produktKat = {'Artikelnummer': [],
                  'Anzahl': [],
                  }

    all_articles = {211}

    # API request to display each unique artnr
    with urllib.request.urlopen(f"{api_server}/api/sales/unique/artnr") as url:
        all_articles = json.loads(url.read().decode())
        all_articles = [x["artnr"] for x in all_articles]

    # Get request for products
    produktKatf = pd.DataFrame(data=produktKat)

    # Create multiselect to choose specific articles
    kategorieselect = st.multiselect('Wählen Sie die gewünschte Artikelnummer: ',
                                     list(all_articles))

    # Create variables for each column
    prediction = 0
    article_amounts = []
    base_value = 0
    day_specific = 0
    last_month = 0
    weather = 0
    safety_stock = 0
    system_reco = 0

    # Request data for selected article, store, and date from the /sales endpoint of the api
    for i, value in enumerate(kategorieselect):
        filial_id = map_data[map_data.name_store.eq(filial_select)]["number_store"].to_numpy()[0]
        with urllib.request.urlopen(
                f"{api_server}/api/sales/amount?artnr={value}&filnr={filial_id}&dateFrom={first_date_input}&dateTo={second_date_input}") as url:
            article_amounts.append([])
            sales_for_article = json.loads(url.read().decode())

            for sale in sales_for_article:
                article_amounts[i].append({
                    "amount": sale["amount"],
                    "date": sale["date"]
                })
        # Request prediction data from the /prediction endpoint of the api
        with urllib.request.urlopen(
                f"{api_server}/api/prediction?artnr={value}&filnr={filial_id}&date={first_date_input}") as url:
            prediction_for_article = json.loads(url.read().decode())
            for predict in prediction_for_article:
                prediction = predict["prediction"]
                safety_stock = predict["safetystock"]
            system_reco = prediction + safety_stock
            st.markdown("Artikel ""**" + str(value) + "**:  Empfohlene Bestellmenge des Systems: " + str(system_reco))
            predict_data = st.checkbox('Einflussfaktoren der empfohlenen Bestellmenge anzeigen: ', key=value)
            if predict_data:
                for predict in prediction_for_article:
                    base_value = predict["base_value"]
                    day_specific = predict["dayspecific"]
                    last_month = predict["lastmonth"]
                    weather = predict["weather"]
                    safety_stock = predict["safetystock"]
                # Create boxes via html and css to display specific prediciton data from the api
                components.html(f"""
                    <style>
                    .flex-container {{
                        width: 100%;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        gap: 0.5em;
                        font-family: 'IBM Plex Sans', sans-serif;
                        margin: 0 auto;
                        margin-top: 40px;
                         }}
                    .box {{
                        padding: 1em;
                        border: 2px solid grey;
                        background-color: #F63A67;
                        color: white;
                        text-align: center;
                        border-radius: 15px;
                        }}
                    </style>
                    <div class="flex-container">
                        <div class="box"><b>
                        Durchschnittliche Verkaufszahl:<br/>
                        </b>
                        {base_value}
                        </div>
                        <div class="box"><b>
                        Tagesspezifische Faktoren:<br/>
                        </b>
                        {day_specific}
                        </div>
                        <div class="box"><b>
                        Verkaufszahlen des Vormonats:<br/>
                        </b>
                        {last_month}
                        </div>
                        <div class="box"><b>
                        Wettervorhersage:<br/>
                        </b>
                        {weather}
                        </div>
                        <div class="box"><b>
                        Sicherheitsbestand:<br/>
                        </b>
                        {safety_stock}
                        </div>
                    </div>
                """, height=500)
            # Create variable for historic data of the selected period
            historic_data = st.checkbox('Verkaufszahl im gewählten Zeitraum anzeigen', key=value)
            if historic_data:
                chart_data = pd.DataFrame(article_amounts[i])
                st.line_chart(chart_data.rename(columns={'date': 'index'}).set_index('index'))

            # Take order quantity of input field and calculate the deviation of the prediction and the value
            order_quantity = st.number_input(" Aktuelle Bestellmenge von Artikel " + str(value) + ":",
                                             min_value=0, value=system_reco,
                                             key=value)
            deviation_order_predict = order_quantity - system_reco
            st.write("Abweichung zwischen Vorhersage und Bestellmenge: " + str(deviation_order_predict))
            st.checkbox("Freigeben", key=value)
    # Create a button to send the order
    if st.button('Bestellungen abschicken'):
        st.error('404')
