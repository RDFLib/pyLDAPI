Register template
=================

Example of a generic register template:

.. code-block:: HTML

    {% extends "layout.html" %}
    {% block content %}
        <h1>{{ label }}</h1>
        <h2>Register View</h2>
        {% for class in contained_item_classes %}
            <span><h3>Of <a href="{{ class }}">{{ class }}</a> class items</h3></span>
        {% endfor %}
        <table>
            <tr>
                <td style="vertical-align:top; width:500px;">
                    <h3>Items in this Register</h3>
                    <ul>
                    {%- for item in register_items -%}
                        {%- if item is not string %}
                        <li class="no-line-height"><a href="{{ item[0] }}">{{ item[1] }}</a></li>
                        {%- else %}
                        <li class="no-line-height"><a href="{{ item }}">{{ item.split('#')[-1].split('/')[-1] }}</a></li>
                        {%- endif %}
                    {%- endfor -%}
                    </ul>
                    {%  if pagination.links %}
                    <h5>Paging</h5>
                    {%  endif %}
                    {{ pagination.links }}
                </td>
                <td style="vertical-align:top;">
                    <h3>Alternate profiles</h3>
                    <p>Different profiles of this register are listed at its <a href="{{ request.base_url }}?_profile=alternates">Alternate profiles</a> page.</p>
                    <h3>Automated Pagination</h3>
                    <p>To page through these items, use the query string arguments 'page' for the page number and 'per_page' for the number of items per page. HTTP <code>Link</code> headers of <code>first</code>, <code>prev</code>, <code>next</code> &amp; <code>last</code> indicate URIs to the first, a previous, a next and the last page.</p>
                    <p>Example:</p>
                    <pre>
                        {{ request.base_url }}?page=7&amp;per_page=50
                    </pre>
                    <p>Assuming 500 items, this request would result in a response with the following Link header:</p>
                    <pre>
                        Link:   &lt;{{ request.base_url }}?per_page=50&gt; rel="first",
                            &lt;{{ request.base_url }}?per_page=50&page=6&gt; rel="prev",
                            &lt;{{ request.base_url }}?per_page=50&page=8&gt; rel="next",
                            &lt;{{ request.base_url }}?per_page=50&page=10&gt; rel="last"
                    </pre>
                    <p>If you want to page the whole collection, you should start at <code>first</code> and follow the link headers until you reach <code>last</code> or until there is no <code>last</code> link given. You shouldn't try to calculate each <code>page</code> query string argument yourself.</p>
                </td>
            </tr>
        </table>
    {% endblock %}

Variables used by the register template:

.. code-block:: python

    render_template(
        self.register_template or 'register.html',          # the register template to use
        uri=self.uri,                                       # the URI requested
        label=self.label,                                   # The label of the Register
        comment=self.comment,                               # A description of the Register
        contained_item_classes=self.contained_item_classes, # The list of URI strings of each distinct class of item contained in this Register
        register_items=self.register_items,                 # The class items in this Register
        page=self.page,                                     # The page number of this current Register's instance
        per_page=self.per_page,                             # The number of class items per page. Default is 20
        first_page=self.first_page,                         # deprecated, use pagination instead
        prev_page=self.prev_page,                           # deprecated, use pagination instead
        next_page=self.next_page,                           # deprecated, use pagination instead
        last_page=self.last_page,                           # deprecated, use pagination instead
        super_register=self.super_register,                 # A super-Register URI for this register. Can be within this API or external
        pagination=pagination                               # pagination object from module flask_paginate
    )

See :class:`.RegisterRenderer` for an example on how to render the register profile.
