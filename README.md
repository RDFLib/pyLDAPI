# Python Linked Data API
A Linked Data API too to be used to present non-Linked Data in HTML and RDF.

NOTE: this repo currently contains an implementation of the generic *pyldapi* tool. Shortly this repo will be reconfigured so that the tool is a stand-alone [Python Flask](http://flask.pocoo.org/) plugin.

## Code Structure
Folders:  
* **model**
    * contains files to custom interface with data structures (databases/files etc.)
    * the files here are likely class files that get called by @register in route.py
* **view**
    * contains template files, static files like CSS and other content used to formulate ouput formats
* **controller**
    * contains the declarations of Flask API endpoints - routes
    * these are the HTTP endpoints that, when accessed via a browser or some external agent trigger handling by this application
    * in this MVC formulation, the routes file(s) should be minimal and just respond to HTTP requests and hand off data access to model and use resources via views for responses
* **pyldp**
    * contains the model of register decorator, which will be released as a python package later.
* **_config**
    * a basic config file to store things like pointers to static folders

Files:  
* **app.py**
    * the Flask application declaration
    * this can be run through a WSGI-capable web server, like Apache, by refering to it via the app.wsgi file
* **app.wsgi**
    * a file needed to be referred to by a web server, such as Apache, for some location, such as /app, so the web server can forward requests at that point to this Flask App
* **requirements.txt**
    * a listing of the Python modules required for this app

## Installation on ubuntu
To run this app using Apache2 web server on Debina/Ubuntu Linux:
* install Apache
	* sudo apt install -y apache2
	* sudo apt install apache2-utils
* enable Apache <--> Python3 interactions via mod_wsgi
	* sudo apt install libapache2-mod-wsgi-py3
	* sudo apt install python3-flask
* install Git in order to clone this repo
	* sudo apt install git
* clone the app somewhere
	* mkdir /var/www/minimal
	* sudo chown -R ubuntu /var/www/minimal
	* cd /var/www/minimal
	* git clone https://github.com/nicholascar/minimal-flask-mvc.git .
	* cd minimal-flask-mvc
	* pip3 install -r requirement.txt
* adjust this app's app.wsgi file to point to the dir you cloned it to
	* nano app.wsgi
	* replace '/var/www/app' to '/var/www/minimal/minimal-flask-mvc'
* configure Apache to point to this app at /minimal
	* sudo mv /var/www/minimal/minimal-flask-mvc/apache.config /etc/apache2/sites-available/
	* sudo a2ensite apache
	* note: the user and group of WSGIDaemonProcess configuration specified in apache.conf should be an Unix/Linux user, who should have execute privileges on the WSGIscript.
* access service
    * navigate http://localhost/minimal to access services

## Installation and running on develop machine
* installation on windows
    * install python3
    * install pip using python3
    * install requirement.txt by pip install -r requirement.txt

* start on windows
    * SET  FLASK_APP=app.py
    * python3 -m flask run
* start on Linux
    * export FLASK_APP=app.py
    * python3 -m flask run


## License
This repository is licensed under Creative Commons 4.0 International. See the [LICENSE deed](LICENSE) in this repository for details.


## Contacts
You can write anything you like in the Contacts section, as long as you also include one or more GA contact people using the layout below as a guide. You do not need to include more than a name and email address: the title, ORCID etc. are all optional.

Point of Contact:
**Nicholas Car**  
*Senior Experimental Scientist*  
CSIRO Land & Water  
<nicholas.car@csiro.au>  
<http://orcid.org/0000-0002-8742-7730>
