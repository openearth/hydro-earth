set DATASTORE_PROJECT_ID=hydro-earth

set GOOGLE_APPLICATION_CREDENTIALS=hydroearth/config_privatekey.json
psqworker hydroearth.tasks.worker.models_queue

