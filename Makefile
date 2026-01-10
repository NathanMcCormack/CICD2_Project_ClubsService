
ClubServiceAPP = app.main:app 
install: 
	pip install -r requirements.txt 

runClubs: 
	python -m uvicorn $(ClubServiceAPP) --host 0.0.0.0 --port 8002 --reload 

test: 
	python -m pytest -q
