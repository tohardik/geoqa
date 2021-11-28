import json

import requests

from geoqa import app as flask_app
from geoqa.model.beans import LinkingResponse
from geoqa.util.property_utils import PropertyUtils


class ServiceConnector(object):
    LOG = flask_app.logger

    def connect(self, service_url: str, params: dict):
        try:
            response = requests.post(service_url, data=params)

            if response.status_code == 200:
                return response.text
            else:
                self.LOG.error(f"Problem in connecting to {service_url}")
                self.LOG.error(f"Response status code: {response.status_code}")
                return None
        except Exception as ex:
            self.LOG.error(f"Failed to connect to {service_url}")
            self.LOG.error(str(ex))
            return None

    def do_linking(self, question) -> LinkingResponse:
        params = {"input_text": question}
        if flask_app.config['ABLATION_LINKING']:
            params["ablation"] = True

        response = self.connect(PropertyUtils.get_linking_service_url(), params)
        if response is None:
            raise Exception("Failed to connect to geo classification service")
        else:
            response_body = json.loads(response)
            linking_response = LinkingResponse(response_body['inputText'], response_body['linkedClasses'],
                                               response_body['linkedRelations'], response_body['linkedEntities'])
            return linking_response

    def do_geo_classification(self, question) -> dict:
        params = {"input_text": question}
        if flask_app.config['ABLATION_CLASSIFICATION']:
            params["ablation"] = True

        response = self.connect(PropertyUtils.get_classifier_service_url(), params)
        if response is None:
            raise Exception("Failed to connect to geo classification service")
        else:
            return json.loads(response)
