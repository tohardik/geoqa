from typing import List


class Constants(object):
    CLASS = "CLASS"
    ENTITY = "ENTITY"
    RELATION = "RELATION"

    NODE_CLASS = "http://linkedgeodata.org/meta/Node"
    WAY_CLASS = "http://linkedgeodata.org/meta/Way"
    RELATION_CLASS = "http://linkedgeodata.org/meta/Relation"

    ENTITY_PLACEHOLDER = "__ENTITY__"
    CLASS_PLACEHOLDER = "__CLASS__"

    GEO_OPERATOR_BORDER = "Borders"
    GEO_OPERATOR_CONTAINMENT = "Containment"
    GEO_OPERATOR_CROSSING = "Crossing"
    GEO_OPERATOR_PROXIMITY = "Proximity"

    GEO_OPERATOR_PATTERN = {
        GEO_OPERATOR_BORDER: "__BORDERS__",
        GEO_OPERATOR_CONTAINMENT: "__CONTAINED_IN__",
        GEO_OPERATOR_CROSSING: "__CROSSING__",
        GEO_OPERATOR_PROXIMITY: "__DISTANCE__"
    }

    QUERY_PREFIXES = "__PREFIXES__"
    QUERY_FORM = "__FORM__"
    QUERY_VARIABLE = "__VARIABLES__"
    QUERY_COUNT_VARIABLE = "(COUNT(DISTINCT __VARIABLES__) as ?count)"
    QUERY_WHERE_CLAUSE = "__WHERE_CLAUSE__"
    QUERY_ORDERING = "__ORDER_BY__"
    QUERY_LIMIT = "__LIMIT__"
    QUERY_PROXIMITY_VALUE = "__DISTANCE__"
    QUERY_RELATION = "__RELATION__"
    QUERY_RELATION_FILTER = "__RELATION_FILTER__"
    QUERY_RELATION_VARIABLE = "?value"

    QUERY_FORM_SELECT = "SELECT"
    QUERY_FORM_ASK = "ASK"

    QUERY_ANATOMY = f"{QUERY_PREFIXES} {QUERY_FORM} {QUERY_VARIABLE} WHERE {QUERY_WHERE_CLAUSE} {QUERY_ORDERING} {QUERY_LIMIT}"
    QUERY_COMMON_PREFIXES = """PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/> 
    PREFIX geo: <http://www.opengis.net/ont/geosparql#> 
    PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
     
    """


class LinkedCandidate:
    def __init__(self, uri, label, searchTerm, originalTerm, esScore, multiplier, levensteinDistance, types, startIndex,
                 endIndex, category):
        self.uri = uri
        self.label = label
        self.searchTerm = searchTerm
        self.originalTerm = originalTerm
        self.esScore = esScore
        self.multiplier = multiplier
        self.levensteinDistance = levensteinDistance
        self.types = types
        self.startIndex = startIndex
        self.endIndex = endIndex
        self.category = category

    def __str__(self) -> str:
        return f"({self.category}: uri={self.uri} , label={self.label})"

    def __repr__(self) -> str:
        return f"({self.category}: uri={self.uri} , label={self.label})"

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "label": self.label,
            "searchTerm": self.searchTerm,
            "originalTerm": self.originalTerm,
            "esScore": self.esScore,
            "multiplier": self.multiplier,
            "levensteinDistance": self.levensteinDistance,
            "types": self.types,
            "startIndex": self.startIndex,
            "endIndex": self.endIndex,
            "category": self.category
        }

    def is_class(self):
        return self.category == Constants.CLASS

    def is_entity(self):
        return self.category == Constants.ENTITY

    def is_relation(self):
        return self.category == Constants.RELATION

    def is_entity_node(self):
        return self.is_entity() and Constants.NODE_CLASS in self.types

    def is_entity_way(self):
        return self.is_entity() and Constants.WAY_CLASS in self.types

    def is_entity_relation(self):
        return self.is_entity() and Constants.RELATION_CLASS in self.types

    @classmethod
    def from_dict(cls, d, category):
        return LinkedCandidate(d['uri'], d["label"], d["searchTerm"], d["originalTerm"], d["esScore"], d["multiplier"],
                               d["levensteinDistance"], d["types"], d["startIndex"], d["endIndex"], category)


class LinkingResponse:
    def __init__(self, inputText, linkedClasses, linkedRelations, linkedEntities):
        self.inputText = inputText
        self.linkedClasses = [LinkedCandidate.from_dict(classCandidate, Constants.CLASS) for classCandidate in
                              linkedClasses]
        self.linkedRelations = [LinkedCandidate.from_dict(relationCandidate, Constants.RELATION) for relationCandidate
                                in
                                linkedRelations]
        self.linkedEntities = [LinkedCandidate.from_dict(entityCandidate, Constants.ENTITY) for entityCandidate in
                               linkedEntities]

    def to_dict(self):
        return {
            "inputText": self.inputText,
            "linkedClasses": [x.to_dict() for x in self.linkedClasses],
            "linkedRelations": [x.to_dict() for x in self.linkedRelations],
            "linkedEntities": [x.to_dict() for x in self.linkedEntities]
        }

    def get_all_links(self) -> List[LinkedCandidate]:
        return self.linkedClasses + self.linkedRelations + self.linkedEntities


class FilledPattern:
    def __init__(self, query_template, variable, used_classes=None, used_relations=None, used_entities=None):
        if used_entities is None:
            used_entities = []
        if used_relations is None:
            used_relations = []
        if used_classes is None:
            used_classes = []
        self.query_template = query_template
        self.variable = variable
        self.used_classes = used_classes
        self.used_relations = used_relations
        self.used_entities = used_entities

    def __str__(self) -> str:
        return f"{self.query_template}"

    def __repr__(self) -> str:
        return f"{self.query_template}"


class FilledQuery:
    def __init__(self, query: str, query_form: str, question: str = None, geo_operator: str = None,
                 used_classes: List[LinkedCandidate] = None, used_relations: List[LinkedCandidate] = None,
                 used_entities: List[LinkedCandidate] = None):
        if used_entities is None:
            used_entities = []
        if used_relations is None:
            used_relations = []
        if used_classes is None:
            used_classes = []
        self.query: str = query
        self.query_form: str = query_form
        self.question: str = question
        self.geo_operator: str = geo_operator
        self.used_classes: List[LinkedCandidate] = used_classes
        self.used_relations: List[LinkedCandidate] = used_relations
        self.used_entities: List[LinkedCandidate] = used_entities

    def __str__(self) -> str:
        return f"{self.query}"

    def __repr__(self) -> str:
        return f"{self.query}"

    def is_ask_query(self) -> bool:
        return self.query_form == Constants.QUERY_FORM_ASK

    def is_select_query(self) -> bool:
        return self.query_form == Constants.QUERY_FORM_SELECT

    def get_all_links(self) -> List[LinkedCandidate]:
        return self.used_classes + self.used_relations + self.used_entities


class QueryAndResult(object):
    def __init__(self, query: FilledQuery, result: dict, ranking_score: float = 0.0):
        self.query = query
        self.result = result
        self.ranking_score = ranking_score
