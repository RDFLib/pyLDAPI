# -*- coding: utf-8 -*-
from pathlib import Path

from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from pyldapi.renderer import Renderer
from pyldapi.profile import Profile
from pyldapi.exceptions import ProfilesMediatypesException, CofCTtlError
from .data import RDF_MEDIATYPES, MEDIATYPE_NAMES

templates_dir = Path(__file__).parent.parent / "pyldapi" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


class ContainerRenderer(Renderer):
    """
    Specific implementation of the abstract Renderer for displaying Register information
    """
    DEFAULT_ITEMS_PER_PAGE = 100

    def __init__(self,
                 request,
                 instance_uri,
                 label,
                 comment,
                 parent_container_uri,
                 parent_container_label,
                 members,
                 members_total_count,
                 *args,
                 profiles=None,
                 default_profile_token=None,
                 super_register=None,
                 page_size_max=1000):
        """
        Constructor

        :param request: The Flask request object triggering this class object's creation.
        :type request: :class:`.flask.request`
        :param instance_uri: The URI requested.
        :type instance_uri: str
        :param label: The label of the Register.
        :type label: str
        :param comment: A description of the Register.
        :type comment: str
        :param members: The items within this register as a list of URI strings or tuples with string elements
        like (URI, label). They can also be tuples like (URI, URI, label) if you want to manually specify an item's
        class.
        :type members: list
        :param contained_item_classes: The list of URI strings of each distinct class of item contained in this
        Register.
        :type contained_item_classes: list
        :param members_total_count: The total number of items in this Register (not of a page but the register as a
        whole).
        :type members_total_count: int
        :param profiles: A dictionary of named :class:`.View` objects available for this Register, apart from 'reg'
        which is auto-created.
        :type profiles: dict
        :param default_profile_token: The ID of the default :class:`.View` (key of a profile in the list of Views).
        :type default_profile_token: str
        :param super_register: A super-Register URI for this register. Can be within this API or external.
        :type super_register: str
        :param members_template: The Jinja2 template to use for rendering the HTML profile of the register. If None,
        then it will default to try and use a template called :code:`alt.html`.
        :type members_template: str or None
        :param per_page: Number of items to show per page if not specified in request. If None, then it will default to
        RegisterRenderer.DEFAULT_ITEMS_PER_PAGE.
        :type per_page: int or None
        """
        self.instance_uri = instance_uri

        if profiles is None:
            profiles = {}
        for k, v in profiles.items():
            if k == 'mem':
                raise ProfilesMediatypesException(
                    'You must not manually add a profile with token \'mem\' as this is auto-created'
                )
        profiles.update({
            'mem': Profile(
                'https://w3id.org/profile/mem',
                'Members Profile',
                'A very basic RDF data model-only profile that lists the sub-items (members) of collections (rdf:Bag)',
                ['text/html'] + RDF_MEDIATYPES,
                'text/html'
            )
        })
        if default_profile_token is None:
            default_profile_token = 'mem'

        super(ContainerRenderer, self).__init__(
            request,
            instance_uri,
            profiles,
            default_profile_token
         )
        if self.vf_error is None:
            self.label = label
            self.comment = comment
            self.parent_container_uri = parent_container_uri
            self.parent_container_label = parent_container_label
            if members is not None:
                self.members = members
            else:
                self.members = []
            self.members_total_count = members_total_count

            if request.query_params.get("per_page"):
                self.per_page = int(request.query_params.get("per_page"))
            else:
                self.per_page = ContainerRenderer.DEFAULT_ITEMS_PER_PAGE
            if request.query_params.get("page"):
                self.page = int(request.query_params.get("page"))
            else:
                self.page = 1

            self.super_register = super_register
            self.page_size_max = page_size_max
            self.paging_error = self._paging()

    def _paging(self):
        # calculate last page
        self.last_page = int(round(self.members_total_count / self.per_page, 0)) + 1  # same as math.ceil()

        # if we've gotten the last page value successfully, we can choke if someone enters a larger value
        if self.page > self.last_page:
            return 'You must enter either no value for page or an integer <= {} which is the last page number.'\
                .format(self.last_page)

        if self.per_page > self.page_size_max:
            return 'You must choose a page size <= {}'.format(self.page_size_max)

        # set up Link headers
        links = list()
        # signalling this is an LDP Resource
        links.append('<http://www.w3.org/ns/ldp#Resource>; rel="type"')
        # signalling that this is, in fact, a Resource described in pages
        links.append('<http://www.w3.org/ns/ldp#Page>; rel="type"')

        # other Query String Arguments
        other_qsas = [x + "=" + self.request.query_params[x] for x in self.request.query_params if x not in ["page", "per_page"]]
        if len(other_qsas) > 0:
            other_qsas_str = "&".join(other_qsas) + "&"
        else:
            other_qsas_str = ''

        # always add a link to first
        self.first_page = 1
        links.append(
            '<{}?{}per_page={}&page=1>; rel="first"'.format(
                self.instance_uri,
                other_qsas_str,
                self.per_page
            )
        )

        # if this isn't the first page, add a link to "prev"
        if self.page > 1:
            self.prev_page = self.page - 1
            links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                self.instance_uri,
                self.per_page,
                self.prev_page
            ))
        else:
            self.prev_page = None

        # if this isn't the last page, add a link to next
        if self.page < self.last_page:
            self.next_page = self.page + 1
            links.append(
                '<{}?{}per_page={}&page={}>; rel="next"'.format(
                    self.instance_uri,
                    other_qsas_str,
                    self.per_page,
                    self.next_page
                )
            )
        else:
            self.next_page = None

        # always add a link to last
        links.append(
            '<{}?{}per_page={}&page={}>; rel="last"'.format(
                self.instance_uri,
                other_qsas_str,
                self.per_page, self.last_page
            )
        )

        self.headers['Link'] += ', ' + ', '.join(links)

        return None

    def render(self):
        """
        Renders the register profile.

        :return: A Flask Response object.
        :rtype: :py:class:`flask.Response`
        """
        response = super(ContainerRenderer, self).render()
        if response is None and self.profile == 'mem':
            if self.paging_error is None:
                if self.mediatype == 'text/html':
                    return self._render_mem_profile_html()
                elif self.mediatype in Renderer.RDF_MEDIA_TYPES:
                    return self._render_mem_profile_rdf()
                else:
                    return self._render_mem_profile_json()
            else:  # there is a paging error (e.g. page > last_page)
                return Response(self.paging_error, status_code=400, media_type='text/plain')
        return response

    def _render_mem_profile_html(
            self,
            mem_template: str = "mem.html",
            additional_mem_template_context=None,
            mem_template_context_replace=False
    ):
        _template_context = {
            'uri': self.instance_uri,
            'label': self.label,
            'comment': self.comment,
            'parent_container_uri': self.parent_container_uri,
            'parent_container_label': self.parent_container_label,
            'members': self.members,
            'page': self.page,
            'per_page': self.per_page,
            'first_page': self.first_page,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'last_page': self.last_page,
            'mediatype_names': MEDIATYPE_NAMES,
            'request': self.request
        }
        if additional_mem_template_context is not None and isinstance(additional_mem_template_context, dict):
            if mem_template_context_replace:
                _template_context = additional_mem_template_context
            else:
                _template_context.update(additional_mem_template_context)

        return templates.TemplateResponse(mem_template,
                                          context=_template_context,
                                          headers=self.headers)

    def _generate_mem_profile_rdf(self):
        g = Graph()

        LDP = Namespace('http://www.w3.org/ns/ldp#')
        g.bind('ldp', LDP)

        XHV = Namespace('https://www.w3.org/1999/xhtml/vocab#')
        g.bind('xhv', XHV)

        u = URIRef(self.instance_uri)
        g.add((u, RDF.type, RDF.Bag))
        g.add((u, RDFS.label, Literal(self.label)))
        g.add((u, RDFS.comment, Literal(self.comment, lang='en')))
        for member in self.members:
            if "uri" in member:
                member_uri = URIRef(member["uri"])
                g.add((u, RDFS.member, member_uri))
                g.add((member_uri, RDFS.label, Literal(member["title"])))
            elif isinstance(member, tuple):
                member_uri = URIRef(member[0])
                g.add((u, RDFS.member, member_uri))
                g.add((member_uri, RDFS.label, Literal(member[1])))
            else:
                g.add((u, RDFS.member, URIRef(member)))

        # other Query String Arguments
        other_qsas = [x + "=" + self.request.query_params[x] for x in self.request.query_params if x not in ["page", "per_page"]]
        if len(other_qsas) > 0:
            other_qsas_str = "&".join(other_qsas) + "&"
        else:
            other_qsas_str = ''

        page_uri_str = "{}?{}per_page={}&page={}".format(self.instance_uri, other_qsas_str, self.per_page, self.page)
        page_uri_str_nonum = "{}?{}per_page={}&page=".format(self.instance_uri, other_qsas_str, self.per_page)
        page_uri = URIRef(page_uri_str)

        # pagination
        # this page
        g.add((page_uri, RDF.type, LDP.Page))
        g.add((page_uri, LDP.pageOf, u))

        # links to other pages
        g.add((page_uri, XHV.first, URIRef(page_uri_str_nonum + '1')))
        g.add((page_uri, XHV.last, URIRef(page_uri_str_nonum + str(self.last_page))))

        if self.page != 1:
            g.add((page_uri, XHV.prev, URIRef(page_uri_str_nonum + str(self.page - 1))))

        if self.page != self.last_page:
            g.add((page_uri, XHV.next, URIRef(page_uri_str_nonum + str(self.page + 1))))

        if self.parent_container_uri is not None:
            g.add((URIRef(self.parent_container_uri), RDF.Bag, u))
            g.add((URIRef(self.parent_container_uri), RDFS.member, u))
            if self.parent_container_label is not None:
                g.add((URIRef(self.parent_container_uri), RDFS.label, Literal(self.parent_container_label)))
        return g

    def _render_mem_profile_rdf(self):
        g = self._generate_mem_profile_rdf()
        return self._make_rdf_response(g)

    def _render_mem_profile_json(self):
        return JSONResponse(
            content={
                'uri': self.instance_uri,
                'label': self.label,
                'comment': self.comment,
                'profiles': list(self.profiles.keys()),
                'default_profile': self.default_profile_token,
                'register_items': self.members
            },
            media_type='application/json',
            headers=self.headers
        )


class ContainerOfContainersRenderer(ContainerRenderer):
    """
    Specialised implementation of the :class:`.RegisterRenderer` for displaying Register of Registers information.

    This sub-class auto-fills many of the :class:`.RegisterRenderer` options.
    """

    def __init__(self, request, instance_uri, label, comment, profiles, cofc_file_path, default_profile_token='mem'):
        """
        Constructor

        :param request: The Flask request object triggering this class object's creation.
        :type request: :class:`flask.request`
        :param instance_uri: The URI requested.
        :type instance_uri: str
        :param label: The label of the Register.
        :type label: str
        :param comment: A description of the Register.
        :type comment: str
        :param cofc_file_path: The path to the Register of Registers RDF file (used in API setup).
        :type cofc_file_path: str
        """
        super(ContainerOfContainersRenderer, self).__init__(
            request,
            instance_uri,
            label,
            comment,
            None,
            None,
            [],  # will be replaced further down
            0,    # will be replaced further down
            profiles=profiles,
            default_profile_token=default_profile_token,
        )
        self.members = []

        # find things (Containers) within the C of C from cofc.ttl
        try:
            with open(cofc_file_path, 'rb') as file:
                g = Graph().parse(file=file, format='turtle')
            assert g, "Could not parse the CofC RDF file."
        except FileNotFoundError:
            raise CofCTtlError()
        except AssertionError:
            raise CofCTtlError()

        q = '''
            SELECT ?uri ?label
            WHERE {{
                # the URIs and labels of all the things of type rdf:Bag that are within (rdfs:member) the CofC
                ?uri a rdf:Bag ;
                     rdfs:label ?label .
                <{register_uri}> rdfs:member ?uri .
            }}
            '''.format(**{'register_uri': instance_uri})
        for r in g.query(q):
            self.members.append((r['uri'], r['label']))

        self.register_total_count = len(self.members)
