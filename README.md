<h2>Overview</h2>

Activities Catalog is a RESTful web application built using the Python framework Flask that provides a list of activities within six categories, JSON endpoints, as well as integrates user registration and authentication system using third-party OAuth2 providers (Facebook and Google). Registered users have the ability to post, edit and delete their own items. The database for the project was set up and configured using ORM for Python SQLAlchemy.

<h2>How to run</h2>

Please ensure you have Python, Vagrant and VirtualBox installed. This project uses a pre-congfigured Vagrant virtual machine which has the Flask server installed. 
https://www.udacity.com/wiki/ud088/vagrant

Save this Flask application locally in the vagrant/catalog directory (which will automatically be synced to /vagrant/catalog within the VM).

To create the database run python /vagrant/catalog/catalog_database.py to create activitiescatalogwithuser.db and catalogpopulator.py to populate your database with information. 

Run your application within the VM (python /vagrant/catalog/catalog_project.py)

Access and test your application by visiting http://localhost:8080 locally
