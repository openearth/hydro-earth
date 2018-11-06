import json
import datetime

from hydroearth.frontend.app import get_datastore
from hydroearth.tasks import tasks
from hydroearth.data import storage

from flask import Blueprint, current_app, redirect, render_template, request, \
    jsonify, session, url_for, Response, send_from_directory

import google.oauth2.id_token
import google.auth.transport.requests

api_tasks = Blueprint('api_tasks', __name__)

HTTP_REQUEST = google.auth.transport.requests.Request()


@api_tasks.route("/count", methods=['GET'])
def count():
    task_count = get_datastore().count()

    return jsonify({'count': task_count})


@api_tasks.route("/", methods=['GET'])
def list():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    # Verify Firebase auth.
    # [START gae_python_verify_token]
    print(request.headers)
    print('Authorization: ' + request.headers['Authorization'])

    if request.headers['Authorization'] != 'undefined' and request.headers['Authorization']:
        id_token = request.headers['Authorization'].split(' ').pop()
        # claims = google.oauth2.id_token.verify_oauth2_token(id_token,
        #                                                     HTTP_REQUEST)
        id_info = google.oauth2.id_token.verify_firebase_token(id_token,
                                                               HTTP_REQUEST)
        # if not id_info:
        #     return 'Unauthorized', 401
        print(id_info)
    # [END gae_python_verify_token]

    tasks, next_page_token = get_datastore().list(cursor=token)

    # replace user id by name
    # for task in tasks:

    return jsonify({'tasks': tasks, 'next_page_token': next_page_token})


# @api_tasks.route("/")
# def list():
#     token = request.args.get('page_token', None)
#     if token:
#         token = token.encode('utf-8')
#
#     tasks, next_page_token = get_datastore().list(cursor=token)
#
#     return render_template(
#         "list.html",
#         tasks=tasks,
#         next_page_token=next_page_token)


# [START list_mine]
@api_tasks.route("/mine")
# @oauth2.required
def list_mine():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    tasks, next_page_token = get_datastore().list_by_user(
        user_id=session['profile']['id'],
        cursor=token)

    return render_template(
        "list.html",
        tasks=tasks,
        next_page_token=next_page_token)


# [END list_mine]

@api_tasks.route("/templates/<type>", methods=['GET'])
def get_template(type):
    """
    Gets options text file for model type.
    :return:
    """

    # read model options file from Cloud Storage
    content = storage.read_file('templates/' + type + '.yaml')

    return Response(content, status=200, mimetype='application/text')


# [START add]
@api_tasks.route('/add', methods=['POST'])
def add():
    task = request.json

    task['status'] = 'CREATED'

    task['createdTime'] = datetime.datetime.now() \
        .strftime('%Y-%m-%d %H:%M:%S')

    # If the user is logged in, associate their profile with the new model.
    if request.headers['Authorization'] != 'undefined':
        id_token = request.headers['Authorization'].split(' ').pop()
        # claims = google.oauth2.id_token.verify_oauth2_token(id_token,
        #                                                     HTTP_REQUEST)
        id_info = google.oauth2.id_token.verify_firebase_token(id_token,
                                                               HTTP_REQUEST)

        task['userInfo'] = json.dumps(id_info)

        task['createdBy'] = id_info['name']
        # task['createdById'] = session['profile']['id']

        task = get_datastore().create(task)

        # [START enqueue]
        q = tasks.get_models_queue()
        q.enqueue(tasks.build_model, task['id'])
        # [END enqueue]

    return jsonify(task)

    modelTypes = [
        {'name': 'wflow'},
        {'name': 'iMOD'}
    ]

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        data['status'] = 'CREATED'

        data['createdTime'] = datetime.datetime.now() \
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


@api_tasks.route('/<id>/edit', methods=['GET', 'POST'])
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


@api_tasks.route('/<id>/delete', methods=['POST'])
def delete(id):
    if request.headers['Authorization'] != 'undefined':
        id_token = request.headers['Authorization'].split(' ').pop()

        id_info = google.oauth2.id_token.verify_firebase_token(id_token,
                                                               HTTP_REQUEST)

        get_datastore().delete(id)

        return jsonify({'deleted': True})

    return jsonify({'deleted': False, 'message': 'Access denied.'})


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


@api_tasks.route('/<id>')
def view(id):
    model = get_datastore().read(id)
    return render_template("view.html", model=model)
