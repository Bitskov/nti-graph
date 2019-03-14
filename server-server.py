from flask import Flask, request, make_response, abort
from graph import simulate


app = Flask(__name__)


@app.errorhandler(406)
def error406(e):
    resp = make_response("Wrong content-type. \"Application\JSON must be sent\"")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'Content-Type' not in request.headers.keys() or request.headers['Content-Type'] != 'application/json':
        return abort(406)

    json = request.get_json()
    answer = simulate(json)
    #resp = (answer, 200)
    resp = make_response(answer)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/hello')
def hello():
    return "<h1>ЫЫЫЫ</h1>"


app.run(host="0.0.0.0", port=25565)
