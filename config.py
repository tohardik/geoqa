class Config(object):
    GEO_CLASSIFIER_SERVICE_SCHEME = "http"
    # GEO_CLASSIFIER_SERVICE_HOST = "localhost"
    GEO_CLASSIFIER_SERVICE_HOST = "geo-qa.cs.upb.de"
    GEO_CLASSIFIER_SERVICE_PORT = "9091"
    GEO_CLASSIFIER_SERVICE_ENDPOINT = "classify"

    LINKING_SERVICE_SCHEME = "http"
    # LINKING_SERVICE_HOST = "localhost"
    LINKING_SERVICE_HOST = "geo-qa.cs.upb.de"
    LINKING_SERVICE_PORT = "9092"
    LINKING_SERVICE_ENDPOINT = "link"

    SPARQL_ENDPOINT = "http://geo-qa.cs.upb.de:3030/bremen_geo/sparql"

    ABLATION_CLASSIFICATION = True
    ABLATION_LINKING = False
    ABLATION_RANKING = True
