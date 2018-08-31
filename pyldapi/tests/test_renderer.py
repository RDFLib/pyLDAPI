from pyldapi import Renderer, View


class MockRequest:
    pass


class MockRenderer(Renderer):
    def render(self):
        # use the now gotten view & format to create a response
        pass


def accept_profile_testing_setup():
    # this tests Accept-Profile selection of 'test' view
    mr = MockRequest()
    mr.url = 'http://whocares.com'
    mr.values = {}
    mr.headers = {
        'Accept-Profile': 'http://nothing.com ,'
                          'http://nothing-else.com,'
                          '<http://notavailable.com>; q=0.9, '  # ignored - not available
                          '<http://test.linked.data.gov.au/def/auorg#>; q=0.1, '  # available but lower weight
                          '<http://test.com>; q=0.2',
        'Accept': 'text/turtle'
    }

    views = {
        'auorg': View(
            'AU Org View',
            'A view of basic properties of main classes in the AU Org Ontology',
            ['text/html'] + Renderer.RDF_MIMETYPES,
            'text/turtle',
            namespace='http://test.linked.data.gov.au/def/auorg#'
        ),
        'test': View(
            'Test View',
            'A view for testing',
            ['text/xml'],
            'text/xml',
            namespace='http://test.com'
        )
    }

    global r
    r = MockRenderer(
        mr,
        'http://whocares.com',
        views,
        'auorg'
    )

    # this tests QSA selection of 'alternates' view
    mr2 = MockRequest()
    mr2.url = 'http://whocares.com'
    mr2.values = {'_view': 'alternates'}
    mr2.headers = {}

    views2 = {
        'auorg': View(
            'AU Org View',
            'A view of basic properties of main classes in the AU Org Ontology',
            ['text/html'] + Renderer.RDF_MIMETYPES,
            'text/turtle',
            namespace='http://test.linked.data.gov.au/def/auorg#'
        ),
        'test': View(
            'Test View',
            'A view for testing',
            ['text/xml'],
            'text/xml',
            namespace='http://test.com'
        )
    }

    global r2
    r2 = MockRenderer(
        mr2,
        'http://whocares.com',
        views2,
        'auorg'
    )

    # this tests QSA selection of 'alternates' view
    mr3 = MockRequest()
    mr3.url = 'http://whocares.com'
    mr3.values = {}
    mr3.headers = {}

    views3 = {
        'auorg': View(
            'AU Org View',
            'A view of basic properties of main classes in the AU Org Ontology',
            ['text/html'] + Renderer.RDF_MIMETYPES,
            'text/turtle',
            namespace='http://test.linked.data.gov.au/def/auorg#'
        ),
        'test': View(
            'Test View',
            'A view for testing',
            ['text/xml'],
            'text/xml',
            namespace='http://test.com'
        )
    }

    global r3
    r3 = MockRenderer(
        mr3,
        'http://whocares.com',
        views3,
        'auorg'
    )


def test_get_accept_profiles_in_order():
    global r

    aexpected_result = [
        'http://nothing.com',
        'http://nothing-else.com',
        'http://notavailable.com',
        'http://test.com',
        'http://test.linked.data.gov.au/def/auorg#'
    ]
    assert r._get_accept_profiles_in_order() == aexpected_result, \
        'Failed test_get_accept_profiles_in_order() test 4'


def test_get_available_profile_uris():
    global r

    assert r._get_available_profile_uris() == {
        'http://test.linked.data.gov.au/def/auorg#': 'auorg',
        'http://test.com': 'test',
        'https://promsns.org/def/alt': 'alternates'
    }, 'Failed test_get_available_profile_uris()'


def test_get_best_accept_profile():
    global r

    assert r._get_best_accept_profile() == 'test', 'Failed test_get_best_accept_profile()'


def test_get_requested_view():
    global r
    global r2

    assert r._get_requested_view() == 'test', 'Failed test_get_requested_view() test 1'
    assert r2._get_requested_view() == 'alternates', 'Failed test_get_requested_view() test 2'


def test_render_alternates_view_rdf():
    views3 = {
        'auorg': View(
            'AU Org View',
            'A view of basic properties of main classes in the AU Org Ontology',
            ['text/html'] + Renderer.RDF_MIMETYPES,
            'text/turtle',
            namespace='http://test.linked.data.gov.au/def/auorg#'
        ),
        'test': View(
            'Test View',
            'A view for testing',
            ['text/xml'],
            'text/xml',
            namespace='http://test.com'
        ),
        'test2': View(
            'Test2 View',
            'A second view for testing',
            Renderer.RDF_MIMETYPES,
            'application/rdf+xml',
            namespace='http://test2.com'
        )
    }

    mr3 = MockRequest()
    mr3.url = 'http://whocares.com'
    mr3.values = {'_format': 'text/turtle'}
    mr3.headers = {}

    global r3
    r3 = MockRenderer(
        mr3,
        'http://whocares.com',
        views3,
        'test2'  # default view
    )
    print(r3._render_alternates_view_rdf().decode('utf-8'))


if __name__ == '__main__':
    global r
    global r2
    global r3

    accept_profile_testing_setup()
    test_get_accept_profiles_in_order()
    test_get_available_profile_uris()
    test_get_best_accept_profile()
    test_get_requested_view()

    # test_render_alternates_view_rdf()

    print('Passed all tests')
