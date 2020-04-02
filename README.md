# Item-Catalog

Item Catalog Web App

This web app is a project for the Udacity FSND Course.

About

This project is a RESTful web application utilizing the Flask framework which accesses a SQL database that populates categories and their items. OAuth2 provides authentication for further CRUD functionality on the application. Currently OAuth2 is implemented for Google Accounts.

In This Repo

This project has one main Python module app.py which runs the Flask application. A SQL database is created using the database_setup.py module and you can populate the database with test data using database_init.py. The Flask application uses stored HTML templates in the tempaltes folder to build the front-end of the application. CSS/JS/Images are stored in the static directory.

Skills Honed

Python
HTML
CSS
OAuth
Flask Framework
Installation

There are some dependancies and a few instructions on how to run the application. Seperate instructions are provided to get GConnect working also.

Dependencies

Vagrant
Udacity Vagrantfile
VirtualBox
How to Install

Install Vagrant & VirtualBox
Clone the Udacity Vagrantfile
Go to Vagrant directory and either clone this repo or download and place zip here
Launch the Vagrant VM (vagrant up)
Log into Vagrant VM (vagrant ssh)
Navigate to cd/vagrant as instructed in terminal
The app imports requests which is not on this vm. Run sudo pip install requests
Setup application database python /item-catalog/database_setup.py
*Insert fake data python /item-catalog/database_init.py
Run application using python /item-catalog/app.py
Access the application locally using http://localhost:5000
*Optional step(s)

Using Google Login

To get the Google login working there are a few additional steps:

Go to Google Dev Console
Sign up or Login if prompted
Go to Credentials
Select Create Crendentials > OAuth Client ID
Select Web application
Enter name 'Item-Catalog'
Authorized JavaScript origins = 'http://localhost:5000'
Authorized redirect URIs = 'http://localhost:5000/login' && 'http://localhost:5000/gconnect'
Select Create
Copy the Client ID and paste it into the data-clientid in login.html
On the Dev Console Select Download JSON
Rename JSON file to client_secrets.json
Place JSON file in item-catalog directory that you cloned from here
Run application using python /item-catalog/app.py
JSON Endpoints

The following are open to the public:

Catalog JSON: /catalog/JSON - Displays the whole catalog. Categories and all items.

Categories JSON: /catalog/categories/JSON - Displays all categories

Category Items JSON: /catalog/<path:category_name>/items/JSON - Displays items for a specific category

Category Item JSON: /catalog/<path:category_name>/<path:item_name>/JSON - Displays a specific category item.
