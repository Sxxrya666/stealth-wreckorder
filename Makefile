setup: 
	python -m venv venv
	source venv/bin/activate
	.\venv\Scripts\activate
	pip install -r requirements.txt

build: 
	pyinstaller --onefile --windowed --name "WinUtittyManager" index.py

