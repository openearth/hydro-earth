import json
import datetime

from hydroearth.frontend.app import get_datastore
from hydroearth.tasks import tasks

from flask import Blueprint, request, \
    jsonify, session

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

    if request.headers['Authorization'] != 'undefined' and request.headers[
        'Authorization']:
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

    return jsonify({'tasks': tasks, 'next_page_token': next_page_token})


# [END list_mine]

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


# [END add]


@api_tasks.route('/<id>/update', methods=['GET', 'POST'])
def update(id):
    model = get_datastore().read(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        # image_url = upload_image_file(request.files.get('image'))

        # if image_url:
        #     data['imageUrl'] = image_url

        model = get_datastore().update(data, id)

        # return redirect(url_for('.view', id=model['id']))

    # return render_template("form.html", action="Edit", model=model)

    return jsonify({'updated': True})


@api_tasks.route('/<id>/delete', methods=['POST'])
def delete(id):
    if request.headers['Authorization'] != 'undefined':
        id_token = request.headers['Authorization'].split(' ').pop()

        id_info = google.oauth2.id_token.verify_firebase_token(id_token,
                                                               HTTP_REQUEST)

        get_datastore().delete(id)

        return jsonify({'deleted': True})

    return jsonify({'deleted': False, 'message': 'Access denied.'})
