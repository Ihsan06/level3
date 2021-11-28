from kedro.pipeline import Pipeline, node
from .nodes import framer, weathergetter, dictator, freidictor, featureadder, laggetter


def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=framer,
                inputs="parameters",
                outputs=["salesdata", 'pred_dates', 'api_length'],
                name="framer",
            ),
            node(
                func=dictator,
                inputs="salesdata",
                outputs="basedict",
                name="dictator",
            ),
            node(
                func=freidictor,
                inputs=["pred_dates", "filialdata", "fdict"],
                outputs='fdict!',
                name="freidictor",
            ),
            node(
                func=featureadder,
                inputs=["basedict", "filialdata",'fdict', "weatherdict", "parameters", "sales_lag"],
                outputs='filfeaturedict',
                name="featureadder",
            ),
            node(
                func=weathergetter,
                inputs=["filialdata", "pred_dates",'params:weatherkey'],
                outputs='weatherdict',
                name="weathergetter",
            ),
            node(
                func=laggetter,
                inputs=["params:lags_used", "pred_dates", "api_length", "params:server_link"],
                outputs='sales_lag',
                name="laggetter",
            ),
        ] 
    )