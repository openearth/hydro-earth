import datetime

from hydroearth.frontend.app import get_datastore, oauth2
from hydroearth.tasks import tasks
from hydroearth.data import storage
from flask import Blueprint, current_app, redirect, render_template, request, \
    session, url_for

crud = Blueprint('crud', __name__)


def upload_image_file(file):
    """
    Upload the user-uploaded file to Google Cloud Storage and retrieve its
    publicly-accessible URL.
    """
    if not file:
        return None

    public_url = storage.upload_file(
        file.read(),
        file.filename,
        file.content_type
    )

    current_app.logger.info(
        "Uploaded file %s as %s.", file.filename, public_url)

    return public_url


@crud.route("/")
def list():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    models, next_page_token = get_datastore().list(cursor=token)

    return render_template(
        "list.html",
        models=models,
        next_page_token=next_page_token)


# [START list_mine]
@crud.route("/mine")
@oauth2.required
def list_mine():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    models, next_page_token = get_datastore().list_by_user(
        user_id=session['profile']['id'],
        cursor=token)

    return render_template(
        "list.html",
        models=models,
        next_page_token=next_page_token)


# [END list_mine]


@crud.route('/<id>')
def view(id):
    model = get_datastore().read(id)
    return render_template("view.html", model=model)


# [START add]
@crud.route('/add', methods=['GET', 'POST'])
def add():
    modelTypes = [
        {'name': 'wflow'},
        {'name': 'iMOD'}
    ]

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        data['status'] = 'CREATED'

        data['createdTime'] = datetime.datetime.now()\
            .strftime('%Y-%m-%d %H:%M:%S')

        # If an image was uploaded, update the data to point to the new image.
        image_url = upload_image_file(request.files.get('image'))

        if image_url:
            data['imageUrl'] = image_url

        # If the user is logged in, associate their profile with the new model.
        if 'profile' in session:
            data['createdBy'] = session['profile']['displayName']
            data['createdById'] = session['profile']['id']

        model = get_datastore().create(data)

        # [START enqueue]
        q = tasks.get_models_queue()
        q.enqueue(tasks.build_model, model['id'])
        # [END enqueue]

        return redirect(url_for('.view', id=model['id']))

    return render_template("form.html", action="Add", model={},
                           modelTypes=modelTypes)


# [END add]


@crud.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    model = get_datastore().read(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        image_url = upload_image_file(request.files.get('image'))

        if image_url:
            data['imageUrl'] = image_url

        model = get_datastore().update(data, id)

        return redirect(url_for('.view', id=model['id']))

    return render_template("form.html", action="Edit", model=model)


@crud.route('/<id>/delete')
def delete(id):
    get_datastore().delete(id)
    return redirect(url_for('.list'))
