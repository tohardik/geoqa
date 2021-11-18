from importlib.resources import open_text

import yaml

import geoqa
from geoqa import app as flask_app


class PropertyUtils(object):

    __QUERY_TEMPLATES = None

    @classmethod
    def get_classifier_service_url(cls) -> str:
        scheme = flask_app.config['GEO_CLASSIFIER_SERVICE_SCHEME']
        host = flask_app.config['GEO_CLASSIFIER_SERVICE_HOST']
        port = flask_app.config['GEO_CLASSIFIER_SERVICE_PORT']
        endpoint = flask_app.config['GEO_CLASSIFIER_SERVICE_ENDPOINT']

        return f"{scheme}://{host}:{port}/{endpoint}"

    @classmethod
    def get_linking_service_url(cls) -> str:
        scheme = flask_app.config['LINKING_SERVICE_SCHEME']
        host = flask_app.config['LINKING_SERVICE_HOST']
        port = flask_app.config['LINKING_SERVICE_PORT']
        endpoint = flask_app.config['LINKING_SERVICE_ENDPOINT']

        return f"{scheme}://{host}:{port}/{endpoint}"

    @classmethod
    def read_benchmark_questions(cls):
        with open("/home/hardik/Projects/geoqa/geo-qa-benchmark.json", "r") as benchmark_file:
            import json
            benchmark_json = json.load(benchmark_file)
            questions_json = benchmark_json["questions"]
            questions_list = []
            for question in questions_json:
                questions_list.append(question["question"][0]["string"])
            return questions_list

    @classmethod
    def get_query_templates(cls, geo_operator: str) -> dict:
        if cls.__QUERY_TEMPLATES is None:
            with open_text(geoqa, "query_templates.yml") as o:
                cls.__QUERY_TEMPLATES = yaml.load(o, Loader=yaml.FullLoader)

        return cls.__QUERY_TEMPLATES[geo_operator]


