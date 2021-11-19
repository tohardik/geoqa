from typing import List

from SPARQLWrapper import SPARQLWrapper, JSON

from geoqa import app as flask_app
from geoqa.model.beans import FilledQuery, Constants, QueryAndResult


class QueryExecutor(object):
    LOG = flask_app.logger

    @classmethod
    def execute(cls, query, sparql_endpoint=None):
        if sparql_endpoint is None:
            sparql_endpoint = flask_app.config['SPARQL_ENDPOINT']

        try:
            sparql = SPARQLWrapper(sparql_endpoint, returnFormat=JSON)
            sparql.setQuery(query)
            results = sparql.query().convert()
            return results
        except Exception as e:
            cls.LOG.error(f"Query execution failed: {query}")
            cls.LOG.error(f"Error: {str(e)}")

    def execute_and_rank(self, queries: List[FilledQuery]):
        results = []
        if len(queries) > 0:
            # print(queries[0].question)
            # print("before: ", len(queries))
            queries = self.pre_execution_filter(queries)
            # print("after: ", len(queries))

            # Execution
            for query in queries:
                query_and_result = self.execute(query.query)
                empty_result = False
                if query.is_select_query() and len(query_and_result['results']['bindings']) == 0:
                    empty_result = True
                if not empty_result:
                    results.append(QueryAndResult(query, query_and_result))

            # Ranking
            for query_and_result in results:
                all_links = query_and_result.query.get_all_links()

                # add multiplier value of linked candidates, i.e., queries using exact matches rank higher
                score = query_and_result.ranking_score + sum([link.multiplier for link in all_links])

                # add length of search term of linked candidates, i.e., queries using longer matches phrases rank higher
                score = score + sum([len(link.originalTerm) for link in all_links])

                # add number of results returned, i.e., queries returning more number results rank higher
                if query_and_result.query.is_select_query():
                    query_and_result.ranking_score = score

            results = sorted(results, key=lambda q_and_r: -q_and_r.ranking_score)

        return results

    @classmethod
    def pre_execution_filter(cls, queries: List[FilledQuery]):
        filtered_out = []
        for query in queries:
            # For Border/Crossing question, all of used entities must be non point geometry
            if query.geo_operator == Constants.GEO_OPERATOR_BORDER or \
                    query.geo_operator == Constants.GEO_OPERATOR_CROSSING:
                delete = False
                for entity in query.used_entities:
                    if entity.is_entity_node():
                        delete = True
                        break
                if delete:
                    filtered_out.append(query)
                    continue

            # For Containment question, at least one used entities should be non point geometry
            if query.geo_operator == Constants.GEO_OPERATOR_CONTAINMENT:
                delete = True
                for entity in query.used_entities:
                    if entity.is_entity_way() or entity.is_entity_relation():
                        delete = False
                        break
                if delete:
                    filtered_out.append(query)
                    continue

        return [query for query in queries if query not in filtered_out]


if __name__ == '__main__':
    QueryExecutor.execute(
        "PREFIX geo: <http://www.opengis.net/ont/geosparql#> PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/> PREFIX geof: <http://www.opengis.net/def/function/geosparql/> SELECT DISTINCT (COUNT(?target) AS ?count) WHERE { <http://linkedgeodata.org/triplify/relation62718> geo:hasGeometry ?aGeom . ?aGeom geo:asWKT ?aWKT . ?target geo:hasGeometry ?tGeom ; a <http://linkedgeodata.org/ontology/Castle> . ?tGeom geo:asWKT ?tWKT BIND(geof:sfContains(?aWKT, ?tWKT) AS ?contains) FILTER ( ?contains && ( ! sameTerm(?aWKT, ?tWKT) ) ) }",
        sparql_endpoint="http://geo-qa.cs.upb.de:3030/bremen_geo/sparql")
