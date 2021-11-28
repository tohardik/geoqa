import logging

from flask import Flask

app = Flask(__name__)
app.config.from_object("config.Config")

logging.basicConfig(filename='geoqa.log', level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

print(f"Ablation classification: {app.config['ABLATION_CLASSIFICATION']}")
print(f"Ablation linking: {app.config['ABLATION_LINKING']}")
print(f"Ablation ranking: {app.config['ABLATION_RANKING']}")

from geoqa import views
