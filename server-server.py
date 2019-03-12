from flask import Flask, request, make_response, abort
from graph import simulate


app = Flask(__name__)


@app.errorhandler(406)
def error406(e):
    return "Wrong content-type. \"Application\JSON must be sent\""


@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.headers['content-type'] != 'application/json':
        return abort(406)

    json = request.get_json()
    answer = simulate(json)
    resp = (answer, 200)
    return resp


@app.route('/hello')
def hello():
    return "<h1>ЫЫЫЫ</h1>"


app.run(port=88005)