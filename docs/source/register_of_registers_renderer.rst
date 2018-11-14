Register of Registers Renderer (RoR)
====================================

.. note:: To use this, ensure :func:`pyldapi.setup` is called before calling Flask's :code:`app.run()`. See :ref:`setup-reference` for more information.

.. autoclass:: pyldapi.RegisterOfRegistersRenderer
    :members: __init__

Example Usage
-------------

A Flask route at the root of the application serving the *Register of Registers* page to the client.

.. code-block:: python

    @app.route('/')
    def index():
        rofr = RegisterOfRegistersRenderer(request,
                                           API_BASE,
                                           "Register of Registers",
                                           "A register of all of my registers.",
                                           "./rofr.ttl"
                                           )
        return rofr.render()
