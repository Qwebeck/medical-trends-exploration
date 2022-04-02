import requests
import pandas as pd
from enum import Enum
from pathlib import Path
import logging

DATA_PATH = Path(__file__).parent / 'data'

GUS_BDL_KEY = 'e3adef99-ed5f-4674-84a5-08d6664cdff3'


GUS_API_URL = 'https://bdl.stat.gov.pl/api/v1'
PAGE_SIZE = '100'


class GUSException(Exception):
    """ Wyjątki związane z API GUS
    """

    def __init__(self, status_code, json):
        # weź pierwszy błąd:
        if 'errors' in json:
            errors_json = json['errors'][0]
            self.message = f"{errors_json['errorResult']} \n{errors_json['errorReason']}." + \
                f" {errors_json['errorSolution']}"
            self.help = f"Zobacz: {errors_json['errorHelp']}"
        else:
            self.message = json['errorResult']
            self.help = ''
        self.status_code = str(status_code)

    def __str__(self):
        return f'ERROR {self.status_code}: {self.message}\n{self.help}'


def _perform_simple_query(url, relative=True, params={
                          'format': 'json', 'page-size': PAGE_SIZE}, headers={}):
    if relative:
        url = GUS_API_URL + url
    return requests.get(url=url, params=params, headers=headers)


def _perform_one_full_query(url, params={}):
    headers = {'X-ClientId': GUS_BDL_KEY}
    add_to_params = {'format': 'json',
                     'page-size': PAGE_SIZE}
    params = {**add_to_params, **params}
    response = _perform_simple_query(
        url=url,
        relative=True,
        params=params,
        headers=headers)
    response_json = response.json()

    if response.status_code != 200:
        logging.info(f'Bad {url}')
        raise GUSException(
            status_code=response.status_code,
            json=response_json)

    if len(response.json()['results']) == 0:
        logging.info("No results")
        return None
    column_names = list(response.json()['results'][0])
    result = pd.DataFrame(columns=column_names)

    while True:
        result = pd.concat([result, pd.DataFrame(
            response_json['results'])], ignore_index=True, sort=False)

        if ('links' not in response_json) or (
                'next' not in response_json['links']):
            break

        response = _perform_simple_query(
            url=response_json['links']['next'],
            relative=False,
            params={},
            headers=headers)
        response_json = response.json()

        if response.status_code != 200:
            raise GUSException(
                status_code=response.status_code,
                json=response_json)

    return result


class Level(Enum):
    COUNTRY = 0
    MAKROREGION = 1
    VOIVODESHIP = 2
    REGION = 3
    SUBREGION = 4
    POWIAT = 5
    GMINA = 6
    STATISTICAL_AREA = 7


def get_complete_gus_data(
        level, variables, year, var_names):
    if level == Level.VOIVODESHIP:
        results = pd.read_pickle(DATA_PATH / 'jednostki-wojewodztwa.pkl')
    elif level == Level.POWIAT:
        results = pd.read_pickle(DATA_PATH / 'jednostki-powiaty.pkl')
    elif level == Level.GMINA:
        results = pd.read_pickle(DATA_PATH / 'jednostki-gminy.pkl')
    elif not isinstance(level, Level):
        raise TypeError(f"{type(level)} passed as level instead of Level")
    else:
        results = _perform_one_full_query(
            url='/units', params={'level': level.value})

    for var in variables:
        var_name = None
        for name, number in var_names.items():
            if number == var:
                var_name = name
        if var_name is None:
            var_name = var

        var_url = '/data/by-variable/' + str(var)
        try:
            var_data = _perform_one_full_query(
                url=var_url, params={
                    'unit-level': level, 'year': year})
            if var_data is None:
                logging.error(
                    f"No results returned for variable {var_name} for year: {year} and level: {level}")
                continue
        except GUSException as err:
            if err.status_code == 429:
                logging.error("Quota exceeded! Partially results returned")
                break
            raise

        var_data[var_name] = var_data['values'].apply(lambda x: x[0]['val'])
        var_data = var_data.drop(columns=['name', 'values'])

        results = pd.merge(results, var_data, on='id', sort=False, how="left")

    return results
