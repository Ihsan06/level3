import logging
from typing import Dict
import pandas as pd
import numpy as np
import shap


def predictor(fildict: Dict, parameters: Dict, regressordict: Dict) -> Dict:
    """
    Generating the predictions for the data passed in fildict.

    :param fildict: Dict['store_no']['art_no'] with input data for ML.
    :param parameters: Parameters defined in /conf/base/parameters.yml.
    :param regressordict: Dictionary['store_no']['art_no'] containing regressors for corresponding store-art
        combination.
    :return: Dict['store_no']['art_no'] with appended column for predictions.
    """
    featurenames = np.array(parameters['features'])
    for filiale in fildict.keys():
        for article in fildict[filiale].keys():
            model = regressordict[filiale][article]
            fildict[filiale][article].loc[:, 'prediction'] = np.around(model.predict(fildict[filiale][article].loc[:,
                                                                                     featurenames].values))
            fildict[filiale][article].loc[fildict[filiale][article]['prediction'] < 0, 'prediction'] = 0
    log = logging.getLogger(__name__)
    log.info('predictions generated for %s stores', np.str(pd.Series(fildict.keys()).unique()))
    return fildict  # alias preddict


def finalizer(seo_frame: pd.core.frame.DataFrame, preddict: Dict, regressordict: Dict, parameters: Dict) -> [pd.core.frame.DataFrame, list]:
    """
    Function finalizing the predictions by adding safetystocks and values for explainability. Explainability values are
    calculated based on shapely values and grouped by categories. Categories are defined in parameters.

    :param seo_frame: df with SEO Factor for each store * article combination.
    :param preddict: nested dict['storenr']['artnr'] with features and prediction per day.
    :param regressordict: nested dict['storenr']['artnr'] with prediction model per store * article combination.
    :param parameters: Parameters defined in /conf/base/parameters.yml.
    :return: [df: generated from preddict with all the relevant information from predictions, summary_df: list with
        mean prediction for every article across all stores]
    """
    features = pd.Series(parameters['features'])
    catdict = parameters['explain_categories']
    appenddict = {'id': [], 'filnr': [], 'artnr': [], 'date': [], 'prediction': [],
                  'base_value': [], 'dayspecific': [], 'weather': [], 'lastmonth': []}
    for filiale in preddict.keys():
        for article in preddict[filiale].keys():
            df = preddict[filiale][article]
            appenddict['id'] += df['id'].to_list()
            appenddict['date'] += df['date'].to_list()
            appenddict['prediction'] += df['prediction'].to_list()
            appenddict['artnr'] += [int(article)] * len(df)
            appenddict['filnr'] += [int(filiale)] * len(df)
            explainer = shap.TreeExplainer(regressordict[filiale][article])
            appenddict['base_value'] += [int(explainer.expected_value)] * len(df)
            shap_df = pd.DataFrame(explainer.shap_values(df[features], df['prediction']))
            for category in parameters['explain_categories']:
                appenddict[category] += shap_df.apply(lambda x: categorizer(x, features, category, catdict),
                                                      axis=1).to_list()
    df = pd.DataFrame.from_dict(appenddict)
    df['safetystock'] = df.apply(lambda x: round(seo_frame[(seo_frame['filnr'] == x['filnr'])
                                                           & (seo_frame['artnr'] == x['artnr'])]['seo_factor'].values[
                                                     0] * x['prediction']),
                                 axis=1)
    jsummary = list(df.groupby('artnr')['prediction'].mean())
    log = logging.getLogger(__name__)
    log.info('Mean of predictions: %.2f, mean safetystocks: %.2f', df.prediction.mean(), df.safetystock.mean())
    # list(df.groupby('artnr')['prediction'].mean())
    return [df, jsummary]


def categorizer(x, features: pd.core.series.Series, category: str, catdict: Dict) -> int:
    """
    Helper function for apply call in the finalizer function.

    :param x: row of df.
    :param features: pandas.Series of features defined in /conf/base/parameters.yml.
    :param category: single category from catdict.
    :param catdict: Dict with (grouped) categories for explainability defined in /conf/base/parameters.yml.
    :return: Rounded sum of shapely values of every category.
    """
    return round(sum(x[features[features.isin(catdict[category])].index.values]))
