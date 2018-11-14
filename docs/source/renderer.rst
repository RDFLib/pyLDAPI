Renderer
========

.. autoclass:: pyldapi.Renderer
    :members: __init__, render

Example Implementation of :func:`pyldapi.Renderer.render`
---------------------------------------------------------

.. code-block:: python

    def render(self):
        if self.site_no is None:
            return Response('Site {} not found.'.format(self.site_no), status=404, mimetype='text/plain')
        if self.view == 'alternates':
            # you need to define self._render_alternates_view()
            return self._render_alternates_view()
        elif self.view == 'pdm':
            # render the view with the token 'pdm' as text/html
            if self.format == 'text/html':
                # you need to define your own self.export_html()
                return self.export_html(model_view=self.view)
            else:
                # you need to define your own self.export_rdf()
                return Response(self.export_rdf(self.view, self.format), mimetype=self.format)
        elif self.view == 'nemsr':
            # you need to define your own self.export_nemsr_geojson()
            return self.export_nemsr_geojson()

The example code determines the response based on the set *view* and *format* of the object.

.. seealso:: See :ref:`example-renderer-reference` for implementation details for :class:`.Renderer`.