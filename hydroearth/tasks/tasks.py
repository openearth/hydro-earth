import os
import logging

from flask import current_app
from hydroearth import config
from hydroearth.data import storage
from hydroearth.data import datastore

from google.cloud import pubsub
import psq
import requests

publisher_client = pubsub.PublisherClient()
subscriber_client = pubsub.SubscriberClient()


def get_models_queue():
    project = current_app.config['PROJECT_ID']

    # Create a queue specifically for processing models and pass in the
    # Flask application context. This ensures that tasks will have access
    # to any extensions / configuration specified to the app, such as
    # models.
    return psq.BroadcastQueue(publisher_client, subscriber_client, project,
                              name='model-builders',
                              extra_context=current_app.app_context)


def kill_model(model_id):
    pass


def build_model(model_id):
    """
    Handles an individual messages by looking it up in the
    datastore, running corresponding generator, and uploading results to the
    storage.
    """

    logging.info('Building new model {0} ...'.format(model_id))

    model = datastore.read(model_id)

    model['status'] = 'RUNNING'
    model = datastore.update(model, model_id)

    print('Building model ...')

    # TODO: build model
    model = build_model(model)

    # TODO: copy data to storage
    # ...
    model['status'] = 'UPLOADING_DATA'
    model = datastore.update(model, model_id)

    print('Uploading data to Cloud Storage ...')
    model['url'] = upload_model_to_storage(model)

    model['status'] = 'COMPLETED'
    datastore.update(model, model_id)

    # Delete model generator
    model = delete_model_output_locally(model)


def build_model(model):
    """
    Build model for hydro-model-generator
    :param model:
    :type model:
    :return:
    :rtype:
    """
    generator_type = os.environ['MODELTYPE']

    if model['type'] == generator_type:
        cmd = "python model_generator_runner.py"
        subprocess.call(cmd)
    return model


def upload_model_to_storage(model):
    """
    Upload generated model files to Google Cloud Storage and retrieve its
    publicly-accessible URL.
    """

    filename = 'wflow_sbm_case.zip'

    content_type = 'application/zip'

    # TODO: replace this by the actual model output file path
    filename = 'app-worker-run.cmd'

    file = open(filename)

    prefix_path = "output/"
    path = "{0}-{1}.zip".format(model['type'], model['id'])

    public_url = storage.upload_file(
        file.read(),
        prefix_path,
        path,
        content_type
    )

    current_app.logger.info("Uploaded file %s as %s.", filename, public_url)

    return public_url

def delete_model_output_locally(model):
    """
    Delete model output from generator image once upload was successful
    """
    filename = 'wflow_sbm_case.zip'
    shutil.rmtree(filename)
    return model
