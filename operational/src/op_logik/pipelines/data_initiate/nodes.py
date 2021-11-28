import requests
import os
from github import Github
from io import StringIO
import pandas as pd
import logging
from pathlib import Path

def releasegetter(rawtoken: str, repository: str) -> pd.core.frame.DataFrame:
    """
    Updates regressordict (first asset in release) directly and seo_frame (2nd asset
    in the release) through function output from latest Github release in the
    repository defined in conf/base/catalog.yml.

    :param rawtoken: OAuth Github Token
    :param repository: Github repository name
    :return: updated seo_frame from Github release
    """
    token = os.getenv('GITHUB_TOKEN', rawtoken)
    g = Github(token)
    headers = {'Authorization': 'token ' + rawtoken,
              'Accept': 'application/octet-stream'}
    session = requests.Session()
    
    r_regress = g.get_repo(repository).get_latest_release().get_assets()[0]
    response = session.get(r_regress.url, stream = True, headers=headers)
    dest = Path() / "data" / "01_raw" / r_regress.name
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(1024*1024): 
            f.write(chunk)
    log = logging.getLogger(__name__)
    log.info("regressordict updated")

    r_seo = g.get_repo(repository).get_latest_release().get_assets()[1]
    df_response = session.get(r_seo.url, headers=headers)
    data = StringIO(df_response.text)
    df = pd.read_csv(data)
    return df
