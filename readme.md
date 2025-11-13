A simple script to parse OCBC bank statements specifically. If you can download the csv extract from OCBC that'd be the best case scenario. This is for when you don't have access to that csv option. It works on the current format of PDF extracts.

Create virtual environment:

`python3 -m venv my-venv`

Install requirements:

`my-venv/bin/pip3 install -r requirements.txt`

Run code:

`my-venv/bin/python3 parser.py`

Check `parser.py` to see how to change the variables, but you can just set the file paths. It's currently set to 'test.pdf'.