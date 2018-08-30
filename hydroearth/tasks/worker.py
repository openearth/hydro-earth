from hydroearth import config
import hydroearth.frontend.app
from hydroearth.tasks import tasks

app = hydroearth.frontend.app.create_app(config)


def read_model_info():
    # check if modelinfo.json exists
    # read model type and model executable path
    # use that in tasks.generate_model

    pass


read_model_info()

# [START books_queue]
# Make the queue available at the top-level, this allows you to run
# `psqworker main.books_queue`. We have to use the app's context because
# it contains all the configuration for plugins.
# If you were using another task queue, such as celery or rq, you can use this
# section to configure your queues to work with Flask.
with app.app_context():
    models_queue = tasks.get_models_queue()
# [END books_queue]

# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
    raise Exception('Run me using psqworker')
