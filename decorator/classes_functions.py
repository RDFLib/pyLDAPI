import json
from os.path import join, dirname
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()


def get_classes_views_formats():
    """
    Caches the graph_classes JSON file in memory
    :return: a Python object parsed from the views_formats.json file
    """
    cvf = cache.get('classes_views_formats')
    if cvf is None:
        cvf = json.load(open(join(dirname(__file__), 'views_formats.json')))
        # times out never (i.e. on app startup/shutdown)
        cache.set('classes_views_formats', cvf)
    return cvf
