from flask import Flask, Response, request
from pyldapi import setup as pyldapi_setup
from pyldapi import RegisterOfRegistersRenderer, RegisterRenderer

cats = [
    {
        "name": "Jonny",
        "breed": "Tortoiseshell",
        "age": 10,
        "color": "orange",
    }, {
        "name": "Sally",
        "breed": "Manx",
        "age": 3,
        "color": "brown",
    }, {
        "name": "Spud",
        "breed": "Persian",
        "age": 7,
        "color": "grey",
    }
]


app = Flask(__name__)


@app.route('/cats')
def reg1():
    cat_items = [("http://example.com/id/cat/{}".format(i['name']), i['name']) for i in cats]
    r = RegisterRenderer(request,
                         request.url_root + 'cats',
                         "Cats Register",
                         "A complete register of my cats.",
                         cat_items,
                         ["http://example.com/Cat"],
                         len(cat_items)
                         )
    return r.render()


@app.route('/')
def index():
    rofr = RegisterOfRegistersRenderer(request,
                                       request.url,
                                       "Register of Registers",
                                       "A register of all of my registers.",
                                       "./rofr.ttl"
                                       )
    return rofr.render()

thread = pyldapi_setup(app, '.', 'http://127.0.0.1:8081')

if __name__ == "__main__":
    app.run("127.0.0.1", 8081, debug=True, threaded=True)
    thread.join()
