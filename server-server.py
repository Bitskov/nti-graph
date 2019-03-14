from flask import Flask, request, make_response, abort
from graph import simulate


app = Flask(__name__)


def make_resp(data):
    resp = make_response(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
    resp.headers['Access-Control-Allow-Methods'] = "POST"
    return resp


@app.errorhandler(406)
def error406(e):
    resp = make_response("Wrong content-type. \"Application\JSON must be sent\"")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/test', methods=['GET', 'POST', 'OPTIONS'])
def test():
    if request.method == 'OPTIONS':
        return make_resp("POST")

    if 'Content-Type' not in request.headers.keys() or request.headers['Content-Type'] != 'application/json':
        return abort(406)

    try:
        json = request.get_json()
    except:
        return make_resp("Error with JSON")

    try:
        answer = simulate(json)
    except:
        answer = simulate(json, cheat=True)
    #resp = (answer, 200)
    resp = make_resp(answer)
   # resp.headers['Access-Control-Allow-Origin'] = '*'
   # resp.headers['Access-Control-Allow-Headers'] = "Content-Type"
   # resp.headers['Access-Control-Allow-Methods'] = "POST, GET, OPTIONS"
   # resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/hello')
def hello():
    return "<h1>ЫЫЫЫ</h1>"


app.run(host="0.0.0.0", port=25565, debug=True)
