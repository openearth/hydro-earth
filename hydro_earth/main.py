from flask import Flask, jsonify, redirect, request
import flask_cors

app = Flask(__name__)

@app.route('/')
@flask_cors.cross_origin()
def root():
    """
    Main page.
    """

    return 'Hello World!'

