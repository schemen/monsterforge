# Monsterforge

## About the project
The website at https://monsterforge.org provides tools for tabletop gaming. 
The website is free and contains no ads. Everything is supported through Patreon (https://www.patreon.com/monsterforge).
Feel free to contribute anything from commenting to design or new options and tools. If you plan something bigger, please contact me beforehand.

## Structure
The website is developed using the python framework django. I use the IDE PyCharm.
Refer to https://www.djangoproject.com/ for details about the directory structure and functions.
Using the provided venv is up to you. There is nothing special in it. Please always specify in your comments if you make changes to the venv!

## Collaboration
If you wish to collaborate with me on anything, please contact me here or on reddit /u/Newti.
I am open to any type of collaboration: Development, Graphics artist for website design or even for creature images, UI/UX, hosting (is currently fine), idea sharing, etc!

## Setup
If you want to run and develop the project locally, you can use PyCharm. Create your own settings_secret.py file according to the template and generate the folder 'paperminis/generate_minis/users/' manually. Finally create an sqlite3 DB in the root of the project called 'db.sqlite3' and run all the migrations (manage.py or ctrl + alt + R in PyCharm and run 'makemigrations' and 'migrate').
If you are having issues, let me know.
