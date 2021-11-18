import json
import logging

import requests

from app.model.beans import LinkingResponse
from app.util.property_utils import PropertyUtils


class ServiceConnector(object):
    LOG = logging.getLogger("app.service.ServiceConnector")

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
        response = self.connect(PropertyUtils.get_linking_service_url(), {"input_text": question})
        if response is None:
            raise Exception("Failed to connect to geo classification service")
        else:
            response_body = json.loads(response)
            linking_response = LinkingResponse(response_body['inputText'], response_body['linkedClasses'],
                                               response_body['linkedRelations'], response_body['linkedEntities'])
            return linking_response

    def do_geo_classification(self, question) -> dict:
        response = self.connect(PropertyUtils.get_classifier_service_url(), {"input_text": question})
        if response is None:
            raise Exception("Failed to connect to geo classification service")
        else:
            return json.loads(response)
