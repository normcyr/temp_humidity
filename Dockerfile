FROM python:3
ADD temp_humidity.py requirements.txt /
RUN pip install -r requirements.txt
CMD [ "python", "./temp_humidity.py --db" ]
