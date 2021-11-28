from flask import Flask, render_template
import os

app = Flask(__name__)

server_link = os.environ.get('API_SERVER') + '/api'

@app.route('/')
def home():
    """
    Shows the screen defined in templates/index.html
    """
    return render_template('index.html')

@app.route('/run/initiate/upload/<int:duration>')
def run_n_upload(duration):
    """
    Runs (1) the pipeline for the initiation of the data from a new release,
    (2) the data engineering and data science pipeline for the defined duration
    and (3) the data upload pipeline to delete the old data and post the updated 
    data to the predictions table of the database defined in server_link.
    """
    from kedro.framework.context import load_context

    context = load_context('./', extra_params={
        'pred_duration': duration,
        'server_link': server_link 
        })
    output = context.run()
    return output

@app.route('/initiate')
def initiate():
    """
    Runs (1) the pipeline for the initiation of the data from a new release.
    """
    from kedro.framework.context import load_context

    context = load_context('./')
    output = context.run(pipeline_name = ('di'))
    return output
    
@app.route('/run/<int:duration>')
def run_days(duration):
    """
    Runs (1) the data engineering and data science pipeline for the defined duration.
    """
    from kedro.framework.context import load_context

    context = load_context('./', extra_params={
        'pred_duration': duration,
        'server_link': server_link
        })
    output = context.run(pipeline_name = ('de_ds'))
    return output

@app.route('/run/upload/<int:duration>')
def run_upload_days(duration):
    """
    Runs (1) the data engineering and data science pipeline for the defined duration
    and (2) the data upload pipeline to delete the old data and post the updated 
    data to the predictions table of the database defined in server_link.
    """
    from kedro.framework.context import load_context

    context = load_context('./', extra_params={
        'pred_duration': duration,
        'server_link': server_link
        })
    output = context.run(pipeline_name = ('de_ds_du'))
    return output

@app.route('/run/initiate/<int:duration>')
def run_init_days(duration):
    """
    Runs (1) the pipeline for the initiation of the data from a new release
    and (2) the data engineering and data science pipeline for the defined duration.
    """
    from kedro.framework.context import load_context

    context = load_context('./', extra_params={
        'pred_duration': duration,
        'server_link': server_link
        })
    output = context.run(pipeline_name = ('di_de_ds'))
    return output

@app.route('/upload')
def upload():
    """
    Runs the data upload pipeline to delete the old data and post the updated 
    data to the predictions table of the database defined in server_link.
    """
    from kedro.framework.context import load_context

    context = load_context('./', extra_params={
        'server_link': server_link
        }
    )
    output = context.run(pipeline_name = ('du'))
    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)