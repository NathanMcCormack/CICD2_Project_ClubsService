PaymentServiceAPP = PaymentService.app.main:app 
ClubServiceAPP = ClubService.app.main:app 
UserServiceAPP = UserService.app.main:app 
PID_FILE = .uvicorn.pid 

install: 
	pip install -r requirements.txt 

runClubs: 
	python -m uvicorn $(ClubServiceAPP) --host 0.0.0.0 --port 8002 --reload 

test: 
	cd UserService && python -m pytest -q
