## Install and setup venv
pip3 install virtualenv 
virtualenv venv 
source venv/bin/activate
pip3 install -r requirements.txt

## Run project dev
uvicorn main:app --reload

## Run project
uvicorn main:app

## Update package
pip3 freeze > requirements.txt
