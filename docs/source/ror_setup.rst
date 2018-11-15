.. _setup-reference:

RoR Setup
=========

.. autofunction:: pyldapi.setup

Example Usage
-------------

.. code-block:: python
    :linenos:
    :emphasize-lines: 8

    from flask import Flask
    from pyldapi import setup as pyldapi_setup

    API_BASE = 'http://127.0.0.1:8081'
    app = Flask(__name__)

    if __name__ == "__main__":
        pyldapi_setup(app, '.', API_BASE)
        app.run("127.0.0.1", 8081, debug=True, threaded=True, use_reloader=False)