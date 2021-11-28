from kedro.pipeline import Pipeline, node
from .nodes import predictor, finalizer



def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=predictor,
                inputs=["filfeaturedict", "parameters", "regressordict"],
                outputs="preddict",
                name="predictor",
            ),
            node(
                func=finalizer,
                inputs=["seo_frame", "preddict", "regressordict", "parameters"],
                outputs=["postframe","jsummary"],
                name="finalize",
            ),
        ] 
    )