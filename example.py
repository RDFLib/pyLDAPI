import json

from flask import Flask, Response, request, render_template
from pyldapi import setup as pyldapi_setup
from pyldapi import RegisterOfRegistersRenderer, RegisterRenderer, Renderer, View

API_BASE = 'http://127.0.0.1:8081'

cats = [
    {
        "name": "Jonny",
        "breed": "DomesticShorthair",
        "age": 10,
        "color": "tortoiseshell",
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

dogs = [
    {
        "name": "Rex",
        "breed": "Dachshund",
        "age": 7,
        "color": "brown",
    }, {
        "name": "Micky",
        "breed": "Alsatian",
        "age": 3,
        "color": "black",
    }
]

MyPetView = View("PetView", "A profile of my pet.", ['text/html', 'application/json'],
                 'text/html', namespace="http://example.org/def/mypetview")

app = Flask(__name__)


class PetRenderer(Renderer):
    def __init__(self, request, uri, instance, pet_html_template, **kwargs):
        self.views = {'mypetview': MyPetView}
        self.default_view_token = 'mypetview'
        super(PetRenderer, self).__init__(
            request, uri, self.views, self.default_view_token, **kwargs)
        self.instance = instance
        self.pet_html_template = pet_html_template

    def _render_mypetview(self):
        self.headers['Profile'] = 'http://example.org/def/mypetview'
        if self.format == "application/json":
            return Response(json.dumps(self.instance),
                            mimetype="application/json", status=200)
        elif self.format == "text/html":
            return Response(render_template(self.pet_html_template, **self.instance))

    # All `Renderer` subclasses _must_ implement render
    def render(self):
        response = super(PetRenderer, self).render()
        if not response and self.view == 'mypetview':
            response = self._render_mypetview()
        else:
            raise NotImplementedError(self.view)
        return response


@app.route('/id/dog/<string:dog_id>')
def dog_instance(dog_id):
    instance = None
    for d in dogs:
        if d['name'] == dog_id:
            instance = d
            break
    if instance is None:
        return Response("Not Found", status=404)
    renderer = PetRenderer(request, request.base_url, instance, 'dog.html')
    return renderer.render()


@app.route('/id/cat/<string:cat_id>')
def cat_instance(cat_id):
    instance = None
    for c in cats:
        if c['name'] == cat_id:
            instance = c
            break
    if instance is None:
        return Response("Not Found", status=404)
    renderer = PetRenderer(request, request.base_url, instance, 'cat.html')
    return renderer.render()


@app.route('/cats')
def cats_reg():
    cat_items = [("http://example.com/id/cat/{}".format(i['name']), i['name']) for i in cats]
    r = RegisterRenderer(request,
                         API_BASE + '/cats',
                         "Cats Register",
                         "A complete register of my cats.",
                         cat_items,
                         ["http://example.com/Cat"],
                         len(cat_items),
                         super_register=API_BASE + '/'
                         )
    return r.render()

@app.route('/dogs')
def dogs_reg():
    dog_items = [("http://example.com/id/dog/{}".format(i['name']), i['name']) for i in dogs]
    r = RegisterRenderer(request,
                         API_BASE + '/dogs',
                         "Dogs Register",
                         "A complete register of my dogs.",
                         dog_items,
                         ["http://example.com/Dog"],
                         len(dog_items),
                         super_register=API_BASE + '/',
                         register_template='register.html',
                         alternates_template='alternates.html'
                         )
    return r.render()


@app.route('/')
def index():
    rofr = RegisterOfRegistersRenderer(request,
                                       API_BASE,
                                       "Register of Registers",
                                       "A register of all of my registers.",
                                       "./rofr.ttl"
                                       )
    return rofr.render()


if __name__ == "__main__":
    pyldapi_setup(app, '.', API_BASE)
    app.run("127.0.0.1", 8081, debug=True, threaded=True, use_reloader=False)
