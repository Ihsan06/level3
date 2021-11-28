import requests
import json
import pandas as pd
import logging


def poster(df: pd.core.frame.DataFrame, server_link: str) -> [str, str]:
    """Deleting the old predictions via HTTP-DELETE and uploading the new predictions
    to the database on the server via HTTP-POST.

    :param df: Dataframe containing all the necessary data for upload.
    :type df: pd.core.frame.DataFrame
    :param server_link: server address for HTTP-POST Upload of data.
    :return: answer [str, str] indicating success of failure of deletion and upload."""

    URL = server_link + '/prediction'
    sucess = "<Response [200]>"
    log = logging.getLogger(__name__)
    r = requests.delete(URL)
    if str(r) == sucess:
        answer_delete = "old predictions deleted"
    else:
        answer_delete = "error on deletion"
    log.info("%s, answer from server %s", answer_delete, str(r))
    response = requests.post(URL, json = json.loads(df.to_json(orient = 'records')))
    if str(response) == sucess:
        answer_post = "predictions successfully updated"
    else:
        answer_post = "error on upload"
    log.info("%s, answer from server %s", answer_post, str(response))
    return [answer_delete, answer_post]  # necessary to show answer when poster is called via API-call
