import re
from pprint import pprint
from typing import List

from geoqa import app as flask_app
from geoqa.core.query_executor import QueryExecutor
from geoqa.core.query_generator import QueryGenerator
from geoqa.model.beans import FilledQuery
from geoqa.service.rest import ServiceConnector
from geoqa.util.ablation_utils import AblationProvider
from geoqa.util.property_utils import PropertyUtils

ablation_provider = AblationProvider()
ablation_provider.get_golden_answers()

class Orchestrator(object):
    LOG = flask_app.logger
    service_connector = ServiceConnector()

    def answer_question(self, question: str, lang="en"):
        cleaned_question = re.sub(r"\s+", " ", question.strip())
        self.LOG.info(f"Question: {cleaned_question}")

        classification = self.service_connector.do_geo_classification(cleaned_question)["result"]
        geo_operator = max(classification, key=classification.get)
        self.LOG.info(f"Classification: {classification}")

        linking_info = self.service_connector.do_linking(cleaned_question)
        self.LOG.info(f"Linked classes: {linking_info.linkedClasses}")
        self.LOG.info(f"Linked entities: {linking_info.linkedEntities}")

        query_generator = QueryGenerator(cleaned_question, geo_operator, linking_info)
        queries: List[FilledQuery] = query_generator.generate_queries()
        self.LOG.info(f"Generated queries: {len(queries)}")

        query_executor = QueryExecutor()
        results = query_executor.execute_and_rank(queries)

        if len(results) > 0:
            if flask_app.config["ABLATION_RANKING"]:
                results = ablation_provider.get_best_answer(cleaned_question, results)

            self.LOG.info(results[0].query.query)
            return results[0].result
        else:
            return {
                "head": {
                    "vars": ["x"]
                },
                "results": {
                    "bindings": []
                }
            }



if __name__ == '__main__':
    o = Orchestrator()
    p = PropertyUtils()

    for q in p.read_benchmark_questions():
        o.answer_question(q)
