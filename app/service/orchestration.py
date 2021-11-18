import logging
import re

from app.core.query import QueryGenerator
from app.service.rest import ServiceConnector
from app.util.property_utils import PropertyUtils


class Orchestrator(object):
    LOG = logging.getLogger("orchestration.py")
    service_connector = ServiceConnector()

    def answer_question(self, question:str, lang="en"):
        cleaned_question = re.sub(r"\s+", " ", question.strip())
        classification = self.service_connector.do_geo_classification(cleaned_question)["result"]
        geo_operator = max(classification, key=classification.get)
        linking_info = self.service_connector.do_linking(cleaned_question)

        query_generator = QueryGenerator(cleaned_question, geo_operator, linking_info)
        query_generator.generate_queries()


if __name__ == '__main__':
    o = Orchestrator()
    o.answer_question("Are there any driving schools in Blumenthal?")
    # o.answer_question("Does Delmestraße cross Pappelstraße?")

    # question = Utils.read_benchmark_questions()
    # for q in question:
    #     o.answer_question(q)
