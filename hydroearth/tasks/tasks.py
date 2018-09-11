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
    import time
    time.sleep(2)

    # TODO: copy data to storage
    # ...
    model['status'] = 'UPLOADING_DATA'
    model = datastore.update(model, model_id)
    print('Uploading data to Cloud Storage ...')

    # upload_model_data(model_id)

    time.sleep(2)

    model['status'] = 'COMPLETED'
    model = datastore.update(model, model_id)

# def upload_model_data(model_id):
#     public_url = storage.upload_file(
#         file.read(),
#         file.filename,
#         file.content_type
#     )
