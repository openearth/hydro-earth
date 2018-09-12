from hydroearth import config_private

# NoSQL Google Cloud Datastore used to keep track of tasks, users and other data
DATA_BACKEND = 'datastore'

# Google Cloud Project ID.
PROJECT_ID = 'hydro-earth'

# Google Cloud Storage and upload settings.
# Typically, you'll name your bucket the same as your project. To create a
# bucket:
#
#   $ gsutil mb gs://<your-bucket-name>
#
# You also need to make sure that the default ACL is set to public-read,
# otherwise users will not be able to see their upload images:
#
#   $ gsutil defacl set public-read gs://<your-bucket-name>
#
# You can adjust the max content length and allow extensions settings to allow
# larger or more varied file types if desired.
CLOUD_STORAGE_BUCKET = 'hydro-earth-models'
MAX_CONTENT_LENGTH = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = {'zip'}

SECRET_KEY = config_private.SECRET_KEY

GOOGLE_OAUTH2_CLIENT_ID = config_private.GOOGLE_OAUTH2_CLIENT_ID

GOOGLE_OAUTH2_CLIENT_SECRET = config_private.GOOGLE_OAUTH2_CLIENT_SECRET
