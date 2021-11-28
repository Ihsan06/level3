from kedro.pipeline import Pipeline, node
from .nodes import releasegetter

def create_pipeline(**kwargs):
    return Pipeline(
        [
        node(func=releasegetter, inputs = ["params:rawtoken", "params:repository"], outputs = "seo_frame", name = "releasegetter"),        
        ]
    )