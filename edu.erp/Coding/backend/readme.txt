1 Setup

//create virtual env
python -m venv env

python -m venv .venv

//Activate 
source ./env/bin/activate

//ensure latest version
python -m pip install --upgrade pip

//dependency installation
pip install -r requirements.txt


2 Command to runserver 
//Activate created venv and run app
source ./env/bin/activate
uvicorn app.main:app --reload

uvicorn app.main:app --reload --host 10.91.0.213 --port 8001