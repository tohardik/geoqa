import re
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


if __name__ == '__main__':
    import spacy
    nlp = spacy.load("en_core_web_sm")
    questions = PropertyUtils.read_benchmark_questions()
    questions = ["within 200m", "500 m", "200 kilometers", "within 500kilometre", "within 200meter", "500 metres","within 200meters", "500 metre", "200km"]
    for q in questions:
        print(q)
        parsed = nlp(q)
        for token in parsed:
            if token.pos_ == "NUM":
                next_token = parsed[token.i + 1]
                unit_search = re.search(r'(m)|(km)|(kilo)?\s?(meter|metre)s?', next_token.text)
                if unit_search is not None:
                    print(token.text, unit_search.group())

        print("------------")

