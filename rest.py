from flask import Flask


_app = Flask(__name__)


@_app.route('/')
def hello_world():
    return 'Hello World!'


def make_rest_app():
    return _app
