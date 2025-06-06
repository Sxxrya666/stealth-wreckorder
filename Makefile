python index.py: 
	python index.py

setup:
	python -m venv venv && ^
	.\venv\Scripts\activate && ^
	pip install -r requirements.txt


build: 
	pyinstaller --onefile --windowed --name "WinUtittyManager" index.py

rem:
	rm -rf venv dist build