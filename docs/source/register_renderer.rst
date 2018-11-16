Register Renderer
=================

.. autoclass:: pyldapi.RegisterRenderer
    :members: __init__, render


Example Usage
-------------
This example contains a Flask route :code:`/sample/` which maps to the *Register of Samples*.
We use the :class:`.RegisterRenderer` to create the Register and return a response back to the client.
The code of interest is highlighted on lines 20-30.

.. code-block:: python
    :linenos:
    :emphasize-lines: 20-30

    @classes.route('/sample/')
    def samples():
        """
        The Register of Samples
        :return: HTTP Response
        """

        # get the total register count from the XML API
        try:
            r = requests.get(conf.XML_API_URL_TOTAL_COUNT)
            no_of_items = int(r.content.decode('utf-8').split('<RECORD_COUNT>')[1].split('</RECORD_COUNT>')[0])

            page = request.values.get('page') if request.values.get('page') is not None else 1
            per_page = request.values.get('per_page') if request.values.get('per_page') is not None else 20
            items = _get_items(page, per_page, "IGSN")
        except Exception as e:
            print(e)
            return Response('The Samples Register is offline', mimetype='text/plain', status=500)

        r = pyldapi.RegisterRenderer(
            request,
            request.url,
            'Sample Register',
            'A register of Samples',
            items,
            [conf.URI_SAMPLE_CLASS],
            no_of_items
        )

    return r.render()