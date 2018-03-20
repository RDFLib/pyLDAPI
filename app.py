import logging
import _config as conf
from flask import Flask
from controller import routes
# from pyldapi import pyldp_routes

app = Flask(__name__, template_folder=conf.TEMPLATES_DIR, static_folder=conf.STATIC_DIR)

app.register_blueprint(routes.routes)
# app.register_blueprint(pyldp_routes.path_routes)

# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=conf.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    app.run(debug=conf.DEBUG)
