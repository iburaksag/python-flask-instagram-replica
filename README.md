# Python Flask Instagram Replica

> #python #flask #googlecloud #appengine #gcstoragebucket #datastore #firebase #html #css #bootstrap

In this assignment I built a simplified replica of Instagram. The system where users can create posts is built. There will be a system here where users can follow each other to see their posts. Eventually this will lead to a timeline where the posts of a user and the posts of users they follow will be merged together. <br><br>
Users will also be permitted to comment on other posts. Here the main task I added in is that I had to deal with and manage multiple data storage mechanisms. The Cloud Storage Bucket will solely be used for managing the images. Whereas the Datastore will be used to manage all other information. <br><br>
In this project, you need to use firebase for authentication purposes. This will keep track of user/password combinations. 
For setting up Firebase, check out the link:
https://console.firebase.google.com/u/0/

## Getting Started 🏁

First before we can start with anything we will need to create a python virtual environment as we will need to install things into it without messing with the local python environment. In the project directory, you can run:

### `python3 -m venv env`

After this we will need to run the following command:

### `source env/bin/activate`

Make sure you have created your environment and sourced it as shown above and run the following command:

### `pip install -r requirements.txt`

Before you go to run this project you will need the JSON file nearby to access the datastore. Before you run your application in your command line you will need to set the session variable GOOGLE_APPLICATION_CREDENTIALS with the location of this JSON file.

### `export GOOGLE_APPLICATION_CREDENTIALS=”../app-engine-3-testing.json”`

Run your application by executing the following command:
 
### `python main.py`

Change the local_constants.py and add the following code to it:
### `PROJECT_NAME='<your project name goes here>’` 
### `PROJECT_STORAGE_BUCKET='<your storage bucket goes here>'`
