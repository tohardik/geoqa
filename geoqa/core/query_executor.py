from SPARQLWrapper import SPARQLWrapper, JSON

from geoqa import app as flask_app


class QueryExecutor(object):
    LOG = flask_app.logger

    @classmethod
    def execute(cls, query, sparql_endpoint=None):
        if sparql_endpoint is None:
            sparql_endpoint = flask_app.config['SPARQL_ENDPOINT']

        sparql = SPARQLWrapper(sparql_endpoint, returnFormat=JSON)
        sparql.setQuery(query)

        try:
            results = sparql.query().convert()
            return results
        except Exception as e:
            cls.LOG.error(f"Query execution failed: {query}")
            cls.LOG.error(f"Error: {str(e)}")


if __name__ == '__main__':
    QueryExecutor.execute(
        "PREFIX geo: <http://www.opengis.net/ont/geosparql#> PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/> PREFIX geof: <http://www.opengis.net/def/function/geosparql/> SELECT DISTINCT (COUNT(?target) AS ?count) WHERE { <http://linkedgeodata.org/triplify/relation62718> geo:hasGeometry ?aGeom . ?aGeom geo:asWKT ?aWKT . ?target geo:hasGeometry ?tGeom ; a <http://linkedgeodata.org/ontology/Castle> . ?tGeom geo:asWKT ?tWKT BIND(geof:sfContains(?aWKT, ?tWKT) AS ?contains) FILTER ( ?contains && ( ! sameTerm(?aWKT, ?tWKT) ) ) }",
        sparql_endpoint="http://geo-qa.cs.upb.de:3030/bremen_geo/sparql")
