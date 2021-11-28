from kedro.pipeline import Pipeline, node
from .nodes import poster

def create_pipeline(**kwargs):
    return Pipeline(
        [
        node(func=poster, inputs = ["postframe", "params:server_link"], outputs = None, name = "poster"),        
        ] 
    )