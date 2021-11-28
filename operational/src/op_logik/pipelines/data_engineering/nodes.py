import logging
import pandas as pd
import numpy as np
import requests
from typing import Dict
import datetime
import asyncio
import aiohttp


def framer(parameters: Dict) -> [pd.core.frame.DataFrame, pd.core.series.Series, int]:
    """
    Function generating df with 'raw' data for prediction period according to the
    parameters defined in /conf/base/parameters.yml . Api_length is the product of the number of unique
    articles * unique stores and defines the number of entries per page of the REST API.

    :param parameters: Parameters defined in /conf/base/parameters.yml.
    :return: [df: basic information for prediction, pd.Series: unique dates for prediction, api_length].
    """

    pred_duration = parameters['pred_duration']
    server_link = parameters['server_link']
    start_date = parameters['start_date']
    n_arts = len(requests.get(url=server_link + '/sales/unique/artnr').json())
    n_fils = len(requests.get(url=server_link + '/sales/unique/filnr').json())
    api_length = n_arts * n_fils
    date_raw = requests.get(url=server_link + "/sales/unique/date").json()
    dates = pd.Series(date_raw).apply(lambda x: x['date'])
    start = dates[dates == start_date].index[0] + 1
    end = start + pred_duration
    pages = range(start, end)
    URL = server_link + '/sales?&pageSize=' + str(api_length) + '&page='
    list_df = func(URL, pages)
    df = pd.concat(list(pd.Series(list_df).apply(lambda x: pd.json_normalize(x))))
    df['amount'] = np.nan  # adaption for 'forecasts' on historical data
    df.drop(columns=['prediction'])
    pred_dates = pd.to_datetime(pd.Series(df['date'].unique()))
    min_max_dates = str(min(pred_dates))[:10] + ' until ' + str(max(pred_dates))[:10]
    log = logging.getLogger(__name__)
    log.info('Amound of predictions: {}, range: {}, api_length: {}'.format(len(df), min_max_dates, api_length))
    return [df, pred_dates, api_length]


async def fetch(session, url: str):
    """
    Asynchronous function sending the API requests (GET) to url.

    :param session: aiohttp.ClientSession.
    :param url: single url for (asynchronous) API request (GET).
    :return: json response from url.
    """
    async with session.get(url) as response:
        json_response = await response.json()
        return json_response


async def main(URL: str, pages):
    """
    Asynchronous function coordinating the API requests.

    :param URL: base URL without page-number.
    :param pages: range of pages for requests (defined through api-length).
    :return: json responses from set of urls.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, (URL + str(i))) for i in pages]
        responses = await asyncio.gather(*tasks)
        return responses


def func(URL: str, pages):
    responses = asyncio.run(main(URL, pages))
    return responses


def dictator(df: pd.core.frame.DataFrame) -> Dict:
    """
    Transforms the input data into nested dict. Format fits better for training individual models per store + article.

    :return: nested dict['storenr']['artnr']
    :param df: salesdata with columns ['amount', 'artnr', 'date', 'discount', 'filnr', 'id']
    :rtype: pd.core.frame.DataFrame"""

    df['wochentag'] = pd.to_datetime(df['date']).dt.dayofweek
    df['monat'] = pd.to_datetime(df['date']).dt.month
    filialen = df["filnr"].unique()  # [0]
    artikels = df["artnr"].unique()  # [0]
    grouped = df.groupby("filnr")
    fildict = {}
    for filiale in filialen:
        fildict[str(filiale)] = {}
        df = grouped.get_group(filiale)
        subgrouped = df.groupby("artnr")
        for artikel in artikels:
            fildict[str(filiale)][str(artikel)] = subgrouped.get_group(artikel)
            fildict[str(filiale)][str(artikel)] = fildict[str(filiale)][str(artikel)].drop(columns=['filnr', 'artnr'])
            fildict[str(filiale)][str(artikel)]["date"] = pd.to_datetime(fildict[str(filiale)][str(artikel)]["date"])
    fildict.pop('10', None)  # no data for store 10 in filialdata available
    return fildict


def laggetter(lags_used, pred_dates: pd.core.series.Series, api_length, server_link) -> pd.core.frame.DataFrame:
    """
    Gets lags (defined in /conf/base/parameters.yml) from server via HTTP-GET.
    Lags form one important Input for the model.

    :param lags_used: lags used for prediction defined in /conf/base/parameters.yml (parameters).
    :param pred_dates: unique dates for predictions, which define the retrieved lags (amount of sales on pred_date-lag).
    :param api_length: enables easier retrieval of date-based values.
    :param server_link: address to database with REST-API storing historical data ("ground truth").
    :return: df with all the relevant lags for prediction.
    :rtype: pd.core.frame.DataFrame"""

    start = str(min(pred_dates) - datetime.timedelta(max(lags_used)))[:-9]
    end = str(max(pred_dates) - datetime.timedelta(min(lags_used)))[:-9]  # adapted end
    size = api_length * ((pd.to_datetime(end) - pd.to_datetime(start)).days + 1)
    URL = server_link + '/sales/amount?dateFrom=' + start + '&dateTo=' + end + '&pageSize=' + str(size)
    raw = requests.get(url=URL)
    # for more articles asychronous API Calls might be better (faster)
    # because the server cannot handle requests with many thousands of entries
    df = pd.DataFrame(raw.json())
    # list_df = func(URL, pages)
    # df = pd.concat(list(pd.Series(list_df).apply(lambda x: pd.json_normalize(x))))
    # df = df.iloc[pd.to_datetime(df.date).values.argsort()] # return df sorted by date after asynchronous calls
    return df


def freidictor(pred_dates: pd.core.series.Series, filialdata: pd.core.frame.DataFrame, fdict: Dict) -> Dict:
    """
    Generates nested Dict[state][year] with lists per state containing the dates of all vacations and bank holidays.
    Based on the states stored in filialdata and the data stored in the database (ground truth) for all the required
    years.

    :param pred_dates: Pandas Series of unique dates for prediction.
    :param filialdata: df with information about location of all the stores mentioned in the data.
    :param fdict: Dict with vacations and bank holidays not checked for timeliness.
    :return: Dict with vacations and bank holidays checked for timeliness.
    :rtype: Dict
    """
    needed = pd.Series(pred_dates.apply(lambda x: x.year).unique())
    #  generates Dict for bank holidays of the according years
    for state in filialdata['state'].unique():
        # generates Dict for the holidays of the respective years
        existing = pd.Series(fdict['feiertage'][state]).apply(lambda x: x.year).unique()
        requests = needed[~needed.isin(existing)]
        if len(requests) > 0:
            for year in requests:
                log = logging.getLogger(__name__)
                log.info('updating vacations and bank holidays for {} in {}'.format(state, year))
                fdict['feiertage'][state] += feiertagegenerator(state, str(year))
                fdict['ferientage'][state] += list(pd.to_datetime(feriengenerator(state, str(year))))
    return fdict


def feriengenerator(state: str, year: str) -> list:
    """
    Retrieves school vacations from public API: http://ferien-api.de.

    :param state: "BY"/ "BW" --> all codes available on https://de.wikipedia.org/wiki/ISO_3166-2:DE.
    :param year: necessary year for request.
    :return: array containing all the days with school vacations in the corresponding year.
    :rtype: list
    """

    URL = 'https://ferien-api.de/api/v1/holidays/' + state + '/' + year
    r = requests.get(url=URL)
    data = r.json()
    ferientage = []
    for i in range(0, len(data)):
        ferientage += list(pd.date_range(data[i]['start'], data[i]['end']).tz_convert(None))
    return ferientage


def feiertagegenerator(state: str, year: str) -> list:
    """
    function retrieving school bank holidays from public API: https://feiertage-api.de.
    Equivalent to feriengenerator for generating bank holidays.

    :param state: "BY"/ "BW" --> all codes available on https://de.wikipedia.org/wiki/ISO_3166-2:DE.
    :param year: necessary year for request.
    :return: array containing all the days with bank holidays in the corresponding year.
    :rtype: list
    """
    URL = 'https://feiertage-api.de/api/?jahr=' + year + '&nur_land=' + state
    r = requests.get(url=URL)
    data = r.json()
    feiertage = []
    skips = {'BW': ['Gründonnerstag', 'Reformationstag'],
             'BY': ['Augsburger Friedensfest',
                    'Buß und Bettag']}  # dict containing non-official/regional public holidays
    for feiertag in data.keys():
        if feiertag not in skips[state] or data[feiertag]['hinweis'] == '':
            # necessary, bacause Reformationstag was only in 2017 a bank holiday in BW
            feiertage.append(pd.to_datetime(data[feiertag]['datum']))
    return feiertage


def weathergetter(filialdata: pd.core.frame.DataFrame, pred_dates: pd.core.series.Series, weatherkey: str) -> Dict:  # params:weatherkey
    """function orchestrating all the requests to the weatherAPI. The function summarizes stores with the same lat + lon
    values (for 2 numbers after the decimals), because the API just offers this level of accuracy for predictions.

    :param filialdata: containing lat + long values for the position of every store.
    :param pred_dates: Pandas Series of unique dates for prediction.
    :param weatherkey: key for API access of worldweatheronline.com.
    :return: dict with historical weather data/predictions (for past/ future dates) for every lat-lon combination.
    :rtype: Dict"""

    filialdata.loc[:, 'latlon'] = filialdata.apply(lambda row: str(round(row['lat'], 2)) + ',' +
                                                               str(round(row['lon'], 2)), axis=1)
    weatherdict = {}
    queries = daynator(pred_dates)
    for location in filialdata['latlon'].unique():
        #  specification of lat + lon from weather api only accurate 2 digits after the . (x.xx).
        #  results in some stores having the same latlon
        latlonweather = weatherrequester(queries, location, weatherkey)
        weatherdict[location] = pd.DataFrame.from_dict(latlonweather)
    log = logging.getLogger(__name__)
    log.info("weather data retrieved from %d different locations", len(weatherdict.keys()))
    return weatherdict


def daynator(ps: pd.core.series.Series) -> pd.core.frame.DataFrame:
    """converts Series of dates to the format necessary for the API requests.

    :param ps: Pandas Series of unique dates for prediction.
    :type ps: pd.core.series.Series
    :return: df with first+last day of every month in the date-range."""

    first_day = []
    last_day = []
    querydict = {}
    for year in ps.apply(lambda x: x.year).unique():
        for month in ps[ps.apply(lambda x: x.year) == year].apply(lambda x: x.month).unique():
            first_day_int = min(ps[(ps.apply(lambda x: x.year) == year) & (ps.apply(lambda x: x.month) == month)].apply(
                lambda x: x.day))
            first_day.append(str(year) + '-' + str(month).zfill(2) + '-' + str(first_day_int))
            last_day_int = max(ps[(ps.apply(lambda x: x.year) == year) & (ps.apply(lambda x: x.month) == month)].apply(
                lambda x: x.day))
            last_day.append(str(year) + '-' + str(month).zfill(2) + '-' + str(last_day_int))
    querydict['first_day'] = pd.to_datetime(first_day)
    querydict['last_day'] = pd.to_datetime(last_day)
    return pd.DataFrame.from_dict(querydict)


def weatherrequester(queries: pd.core.frame.DataFrame, location: str, weatherkey: str) -> Dict:
    """
    Function coordinating the API-calls to the worldweatheronline.com weather-API. Depending on the dates, the function
    retrieves the data for historical and future (predicted) weather.

    :param queries: df with [first_day, last_day] of each month queried.
    :type queries: pd.core.frame.DataFrame
    :param location: location of store(s) in format "lat.xx,lon.xx" e.g. "48.83,2.39".
    :param weatherkey: key for API access of worldweatheronline.com.
    :return: latlonweather Dict with ['date', 'sunhour', 'weathercodes', 'feels_like', 'heat_index'].
    """
    latlonweather = {}
    datadict = {'date': np.empty(0, dtype='datetime64[ns]'), 'sunhour': np.empty(0),
                'feels_like': np.empty(0), 'heat_index': np.empty(0), 'weathercodes': np.empty(0)}
    for i in range(0, len(queries)):
        if datetime.date.today() >= queries['last_day'][i]:
            # only historical (only relevant case based on our data)
            start_date = str(queries['first_day'][i])[:-9]
            end_date = str(queries['last_day'][i])[:-9]
            datadict = wheaterhist(datadict, weatherkey, location, start_date, end_date)
            # for production environment: include warnings
            # log = logging.getLogger(__name__)
            # log.warning("historical weather data retrieved - check whether the dates are correct")
        elif datetime.date.today() < queries['first_day'][i]:
            # only predictions: duration = time difference in days from today on
            duration = str((queries['last_day'][i] - pd.Timestamp(datetime.date.today())).days)
            datadict = wheatherpred(datadict, weatherkey, location, duration)
        else:
            # historical + future -> first hist, then pred
            start_date = str(queries['first_day'][i])[:-9]
            end_date = str(datetime.date.today())
            datadict, = wheaterhist(datadict, weatherkey, location, start_date, end_date)
            duration = str((queries['last_day'][i] - pd.Timestamp(datetime.date.today())).days)
            datadict = wheatherpred(datadict, weatherkey, location, duration)
    latlonweather['date'] = datadict['date']
    latlonweather['sunhour'] = datadict['sunhour']
    latlonweather['weathercodes'] = datadict['weathercodes']
    latlonweather['feels_like'] = datadict['feels_like']
    latlonweather['heat_index'] = datadict['heat_index']
    return latlonweather


def wheaterhist(datadict: Dict, weatherkey: str, location: str, start_date: str, end_date: str) -> Dict:
    """
    Function generating the URL and performing a single API request for historical weather data using the apicrawler
    function.

    :param datadict: Empty Dict with columns to fill ['date', 'sunhour', 'feels_like', 'heat_index', 'weathercodes'].
    :param weatherkey: key for API access of worldweatheronline.com.
    :param location: location of store(s) in format "lat.xx,lon.xx" e.g. "48.83,2.39".
    :param start_date: first_day of the according month (necessary for API-requests).
    :param end_date: last_day of the according month (necessary for API-requests).
    :return: datadict filled with values from weather-API call.
    """
    URL = ('http://api.worldweatheronline.com/premium/v1/past-weather.ashx?key=' + weatherkey +
           '&q=' + location + '&date=' + start_date + '&enddate=' + end_date + '&format=json&tp=24')
    datadict = apicrawler(URL, datadict)
    return datadict


def wheatherpred(datadict: Dict, weatherkey: str, location: str, duration: str) -> Dict:
    """
    Function generating the URL and performing a single API request for weather prediction data via the apicrawler
    function.

    :param datadict: Empty Dict with columns to fill ['date', 'sunhour', 'feels_like', 'heat_index', 'weathercodes'].
    :param weatherkey: key for API access of worldweatheronline.com.
    :param location: location of store(s) in format "lat.xx,lon.xx" e.g. "48.83,2.39".
    :param duration: String with numbers of days relevant for prediction (and hence API-call).
    :return: datadict filled with values from weather-API call
    """
    URL = ('https://api.worldweatheronline.com/premium/v1/weather.ashx?key=' +
           weatherkey + '&q=' + location + '&num_of_days=' + duration + '&cc=no' + '&format=json&tp=24')
    datadict = apicrawler(URL, datadict)
    return datadict


def apicrawler(URL: str, datadict: Dict):
    """
    Function that performs the API-request to worldweatheronline and safes the weather to the datadict.

    :param URL: string for API-call (more information on https://www.worldweatheronline.com/developer/api/docs/).
    :param datadict: Empty Dict with columns to fill ['date', 'sunhour', 'feels_like', 'heat_index', 'weathercodes'].
    :return: datadict filled with values from weather-API call.
    """
    r = requests.get(url=URL)
    while True:  # if request fails the first time
        try:
            data = r.json()['data']['weather']
            break
        except:
            log = logging.getLogger(__name__)
            log.warning("error on first asynchronous API-request for" + URL)
            r = requests.get(url=URL)
            data = r.json()['data']['weather']
            break
    jsonframe = pd.DataFrame.from_dict(data)
    datadict['date'] = np.append(datadict['date'], pd.to_datetime(jsonframe['date']).values)
    datadict['sunhour'] = np.append(datadict['sunhour'], np.float64(jsonframe['sunHour'].values))
    datadict['weathercodes'] = np.append(datadict['weathercodes'], np.float64(
        jsonframe.apply(lambda row: row['hourly'][0]['weatherCode'], axis=1).values))
    datadict['feels_like'] = np.append(datadict['feels_like'], np.float64(
        jsonframe.apply(lambda row: row['hourly'][0]['FeelsLikeC'], axis=1).values))
    datadict['heat_index'] = np.append(datadict['heat_index'], np.float64(
        jsonframe.apply(lambda row: row['hourly'][0]['HeatIndexC'], axis=1).values))
    return datadict


def featureadder(fildict: Dict, filialdata: pd.core.frame.DataFrame, fdict: Dict, weatherdict: Dict, parameters: Dict,
                 sales_lag: pd.core.frame.DataFrame):
    """
    Function adding all generated features to one dataframe stored in a nested dict['storenr']['artnr'] ready for the
    prediction through the machine learning model (regressor).

    :param fildict: nested Dict["storenr"]["artnr"] with information about histrorical sales.
    :param filialdata: df with information about location of all the stores mentioned in the data.
    :param fdict: Information about holiday-situation of stores (depending on state in Germany).
    :param weatherdict: Infos about the weather-conditions at stores locations (some stores have the same conditions,
    as the accuracy of the weather-API is on .2digits on lat+lon values.
    :param parameters: Dict of projects parameters defined in /conf/base/parameters.yml.
    :param sales_lag: df with sales-data necessary for the generation of the lag-features.
    :return:
    """
    pred_duration = parameters['pred_duration']
    # filialdata['number_store'] = pd.to_numeric(filialdata['number_store'])
    filialdata.loc[:, 'latlon'] = filialdata.apply(
        lambda row: str(round(row['lat'], 2)) + ',' + str(round(row['lon'], 2)), axis=1)
    feiertage = fdict['feiertage']
    ferientage = fdict['ferientage']
    for filiale in fildict.keys():
        state = filialdata[filialdata['number_store'] == np.float64(filiale)]['state'].values[0]
        vor_feiertag = list(np.array(feiertage[state]) - datetime.timedelta(days=1))
        zweivor_feiertag = list(np.array(feiertage[state]) - datetime.timedelta(days=2))
        fillatlon = filialdata[filialdata['number_store'] == int(filiale)]['latlon'].values[0]
        firstart = list(fildict[filiale].keys())[0]  # Assumption: Time series of the stores are equal
        filialweather = weatherdict[fillatlon][weatherdict[fillatlon]['date'].isin(fildict[filiale][firstart]['date'])]
        # state for the according stores
        for article in fildict[filiale].keys():
            df = fildict[filiale][article]
            df['datecode'] = 0
            df.loc[:, 'date'] = pd.to_datetime(df['date'])  # change date to timestamp format
            # bank holidays = 1; vacations(school) = 2; day before bank holidays = 3; two days before bank holidays = 4
            df.loc[df['date'].isin(zweivor_feiertag), 'datecode'] = 4
            df.loc[df['date'].isin(vor_feiertag), 'datecode'] = 3
            df.loc[df['date'].isin(ferientage[state]), 'datecode'] = 2
            df.loc[df['date'].isin(feiertage[state]), 'datecode'] = 1
            # lag features (defiened in parameters)
            # df["ma_" + str(parameters['MA_used'])] = df['x'].rolling(window=parameters['MA_used']).mean()
            lagbase = None  # used to slice dataframe with lags
            for lag in parameters['lags_used']:
                start = lag - (parameters['lags_used'][0] - pred_duration)
                # faster: apply call on df to return "lagdf" for merging?
                df["lag_" + str(lag)] = \
                    sales_lag[(sales_lag['filnr'] == int(filiale)) & (sales_lag['artnr'] == int(article))].iloc[
                    -start:lagbase]['amount'].values
                lagbase = -lag
                # for datecodes feature engineering needed -> df["datelag_" + str(lag)] = df.shift(lag)['datecode']
            df = pd.merge(df, filialweather, how='inner', on=['date', 'date'])
            fildict[filiale][article] = df
    return fildict