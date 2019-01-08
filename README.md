## Project Description
* This is a backend website built with Flask to display sports item, public users can just view the available items, while registered users can also make changes on their own items.
* database_setup.py is the configuration of the database, it uses sqlite.
* seeder.py populated the database with dummy items.

## Project Purpose
* The purpose of building this project is to practice my skills in making RESTful web apps that provide third party authentication and authorization functionalities. That's why the items are dummy, and the front end is not styled.

## System Requirments 
- Python3
- Flask module and the the ones that are at the beginning of server.py file
- Vagrant 2.20
- virtual box
- cloning this repo https://github.com/udacity/fullstack-nanodegree-vm
- adding the folder to the vagrant directory  
- run the application within the VM (python /vagrant/catalog/application.py)
- access the application by visiting http://localhost:8000 locally

## Running the server
Run the tool by typing the following in the command line of vagrant virtual 'python server.py',
then open your browser and navigate to http://localhost:8000/
