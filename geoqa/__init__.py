import logging

from flask import Flask

app = Flask(__name__)
app.config.from_object("config.Config")

logging.basicConfig(filename='geoqa.log', level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

from geoqa import views
