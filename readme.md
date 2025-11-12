A simple script that depends on pdftotext to parse OCBC bank statements specifically.

pdftotext has some requirements that are hard to infer. Follow the steps at the [PyPI website](https://pypi.org/project/pdftotext/) to install requirements such as poppler.

Create virtual environment:

`python3 -m venv my-venv`

Install requirements:

`my-venv/bin/pip3 install -r requirements.txt`

Run code:

`my-venv/bin/python3 parser.py`