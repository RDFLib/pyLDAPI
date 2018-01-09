from flask import Blueprint, render_template, request, Response
import urllib.parse as uriparse
import requests
from _ldapi.__init__ import LDAPI, LdapiParameterError
from .functions import render_alternates_view, client_error_Response
from controller import classes_functions
import _config as conf

from decorator import register


routes = Blueprint('controller', __name__)


@routes.route('/')
@register.register
def index():
    return render_template('page_index.html')

@routes.route('/register')
def register():
    return Response ('["http://pid.geoscience.gov.au/def/ont/ga/pdm#Site"]',
                    status=200,
                    mimetype='text/plain')
@routes.route('/site/')
def sites():
    """
    The Register of Site

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = classes_functions.get_classes_views_formats() \
        .get('http://purl.org/linked-data/registry#Register')

    try:
        view, mime_format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )

        # if alternates model, return this info from file
        class_uri = conf.URI_SITE_CLASS

        if view == 'alternates':
            del views_formats['renderer']
            return render_alternates_view(
                class_uri,
                uriparse.quote_plus(class_uri),
                None,
                None,
                views_formats,
                request.args.get('_format')
            )
        else:
            from model import register

            # pagination
            page = int(request.args.get('page')) if request.args.get('page') is not None else 1
            per_page = int(request.args.get('per_page')) if request.args.get('per_page') is not None else 100

            if per_page > conf.PAGE_SIZE_DEFAULT:
                return Response(
                    'You must enter either no value for per_page or an integer <= {}.'.format(conf.PAGE_SIZE_DEFAULT),
                    status=400,
                    mimetype='text/plain'
                )

            links = list()
            links.append('<http://www.w3.org/ns/ldp#Resource>; rel="type"')
            # signalling that this is, in fact, a resource described in pages
            links.append('<http://www.w3.org/ns/ldp#Page>; rel="type"')
            links.append('<{}?per_page={}>; rel="first"'.format(conf.URI_SITE_INSTANCE_BASE, per_page))

            # if this isn't the first page, add a link to "prev"
            if page != 1:
                links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                    conf.URI_SITE_INSTANCE_BASE,
                    per_page,
                    (page - 1)
                ))

            # if this isn't the first page, add a link to "prev"
            if page != 1:
                prev_page = page - 1
                links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                    conf.URI_SITE_INSTANCE_BASE,
                    per_page,
                    prev_page
                ))
            else:
                prev_page = None

            # add a link to "next" and "last"
            try:
                r = requests.get(conf.XML_API_URL_SITES_TOTAL_COUNT)
                no_of_samples = int(r.content.decode('utf-8').split('<RECORD_COUNT>')[1].split('</RECORD_COUNT>')[0])
                last_page = int(round(no_of_samples / per_page, 0)) + 1  # same as math.ceil()

                # if we've gotten the last page value successfully, we can choke if someone enters a larger value
                if page > last_page:
                    return Response(
                        'You must enter either no value for page or an integer <= {} which is the last page number.'
                        .format(last_page),
                        status=400,
                        mimetype='text/plain'
                    )

                # add a link to "next"
                if page != last_page:
                    next_page = page + 1
                    links.append('<{}?per_page={}&page={}>; rel="next"'
                                 .format(conf.URI_SITE_INSTANCE_BASE, per_page, (page + 1)))
                else:
                    next_page = None

                # add a link to "last"
                links.append('<{}?per_page={}&page={}>; rel="last"'
                             .format(conf.URI_SITE_INSTANCE_BASE, per_page, last_page))
            except:
                # if there's some error in getting the no of samples, add the "next" link but not the "last" link
                next_page = page + 1
                links.append('<{}?per_page={}&page={}>; rel="next"'
                             .format(conf.URI_SITE_INSTANCE_BASE, per_page, (page + 1)))
                last_page = None

            headers = {
                'Link': ', '.join(links)
            }

            return register.RegisterRenderer(
                request,
                conf.URI_SITE_INSTANCE_BASE,
                conf.URI_SITE_CLASS,
                None,
                page,
                per_page,
                prev_page,
                next_page,
                last_page).render(view, mime_format, extra_headers=headers)

    except LdapiParameterError as e:
        return client_error_Response(e)


@routes.route('/site/<string:site_no>')
def site(site_no):
    """
    A single Site

    :return: HTTP Response
    """
    # lists the views and formats available for a Site
    c = conf.URI_SITE_CLASS
    views_formats = LDAPI.get_classes_views_formats().get(c)

    try:
        view, mimetype = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )

        # if alternates model, return this info from file
        if view == 'alternates':
            instance_uri = 'http://pid.geoscience.gov.au/site/' + site_no
            del views_formats['renderer']
            return render_alternates_view(
                c,
                uriparse.quote_plus(c),
                instance_uri,
                uriparse.quote_plus(instance_uri),
                views_formats,
                request.args.get('_format')
            )
        else:
            from model.site import Site
            try:
                s = Site(site_no)
                return s.render(view, mimetype)
            except ValueError:
                return render_template('class_site_no_record.html')

    except LdapiParameterError as e:
        return client_error_Response(e)
