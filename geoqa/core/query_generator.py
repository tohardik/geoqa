import itertools
from typing import List, Tuple

import spacy

from geoqa import app as flask_app
from geoqa.model.beans import LinkingResponse, FilledPattern, LinkedCandidate, Constants, FilledQuery
from geoqa.util.property_utils import PropertyUtils

nlp = spacy.load("en_core_web_sm")


class QueryGenerator:

    LOG = flask_app.logger

    def __init__(self, question: str, geo_operator: str, linking_info: LinkingResponse):
        self.question = question
        self.parsed_question = nlp(question)
        self.geo_operator = geo_operator
        self.linking_info = linking_info

    def generate_queries(self):
        links_by_position = {}

        all_links = self.linking_info.get_all_links()
        # if len(all_links) == 0:
        #     print(self.question)
        #     return

        for linked_candidate in all_links:
            for start_index in linked_candidate.startIndex:
                if start_index in links_by_position:
                    links_by_position[start_index].append(linked_candidate)
                else:
                    links_by_position[start_index] = [linked_candidate]

        # if len(links_by_position) > 2:
        #     print(question)
        #     print(len(links_by_position), links_by_position)
        if len(links_by_position) < 2:
            print("-- ", self.question)
            return []

        triple_patterns = self.generate_triple_patterns(links_by_position)
        filled_triple_patterns = self.fill_patterns(triple_patterns)

        query_form = self.determine_query_form()
        count_applicable = self.should_apply_count_aggregate()
        queries = self.populate_query_anatomy(query_form, count_applicable, filled_triple_patterns)

        # Add question and geo_operator to filled queries
        for filled_query in queries:
            filled_query.question = self.question
            filled_query.geo_operator = self.geo_operator

        return queries

    @classmethod
    def generate_triple_patterns(cls, links_by_position):
        flattened = {}
        for start_index in links_by_position:
            flattened[start_index] = set()
            for link in links_by_position[start_index]:
                flattened[start_index].add(link.category)

        start_indexes = sorted(flattened.keys())
        triple_patterns = set()
        for i in range(len(start_indexes)):
            for j in range(i + 1, len(start_indexes)):
                combinations = list(itertools.product(flattened[start_indexes[i]], flattened[start_indexes[j]]))
                triple_patterns = triple_patterns.union(combinations)

        return_value = list(triple_patterns)
        cls.LOG.info(f"Triple patterns: {return_value}")

        return return_value

    def fill_patterns(self, triple_patterns) -> List[FilledPattern]:
        basic_patterns = PropertyUtils.get_query_templates(self.geo_operator)

        filled_patterns: List[FilledPattern] = []
        for triple_pattern in triple_patterns:
            basic_pattern_key = Constants.GEO_OPERATOR_PATTERN.get(self.geo_operator)
            basic_pattern_key = triple_pattern[0] + basic_pattern_key + triple_pattern[1]
            query_pattern_info: dict = basic_patterns.get(basic_pattern_key)

            if query_pattern_info is not None:
                self.LOG.info(f"Basic pattern: {basic_pattern_key}")

                query_pattern = query_pattern_info.get("pattern")
                variable = query_pattern_info.get("variable")

                first_placeholder = triple_pattern[0]
                first_placeholder_set = None
                if first_placeholder == Constants.CLASS:
                    first_placeholder_set = self.linking_info.linkedClasses
                elif first_placeholder == Constants.ENTITY:
                    first_placeholder_set = self.linking_info.linkedEntities

                second_placeholder = triple_pattern[1]
                second_placeholder_set = None
                if second_placeholder == Constants.CLASS:
                    second_placeholder_set = self.linking_info.linkedClasses
                elif second_placeholder == Constants.ENTITY:
                    second_placeholder_set = self.linking_info.linkedEntities

                combinations = list(itertools.product(first_placeholder_set, second_placeholder_set))
                for combination in combinations:
                    # Remove pairs which are self products
                    if combination[0].startIndex == combination[1].startIndex:
                        continue

                    filled: FilledPattern = self.apply_combination(query_pattern, variable, combination)
                    filled_patterns.append(filled)

        return filled_patterns

    @classmethod
    def apply_combination(cls, query_template: str, variable: str,
                          combination: Tuple[LinkedCandidate]) -> FilledPattern:
        filled = str(query_template)
        used_classes = []
        used_entities = []
        for link in combination:
            if link.is_class():
                filled = filled.replace(Constants.CLASS_PLACEHOLDER, f"<{link.uri}>")
                used_classes.append(link)
            elif link.is_entity():
                filled = filled.replace(Constants.ENTITY_PLACEHOLDER, f"<{link.uri}>")
                used_entities.append(link)

        return FilledPattern(filled, variable, used_classes=used_classes, used_entities=used_entities)

    def determine_query_form(self) -> str:
        if self.parsed_question[0].lemma_ == "do" or self.parsed_question[0].lemma_ == "be":
            return Constants.QUERY_FORM_ASK
        else:
            return Constants.QUERY_FORM_SELECT

    def should_apply_count_aggregate(self):  # todo improve with classifier
        first_two_words = self.parsed_question[:2].lemma_
        return first_two_words == "how many"

    @classmethod
    def populate_query_anatomy(cls, query_form: str, count_applicable: bool,
                               filled_triple_patterns: List[FilledPattern]) -> List[FilledQuery]:
        queries = []
        for triple_pattern in filled_triple_patterns:
            # Set prefixes
            query = Constants.QUERY_ANATOMY.replace(Constants.QUERY_PREFIXES, Constants.QUERY_COMMON_PREFIXES)

            # Set query form SELECT/ASK
            query = query.replace(Constants.QUERY_FORM, query_form)

            # Set selected variable
            if query_form == Constants.QUERY_FORM_SELECT:
                # Prevent invalid patterns
                if triple_pattern.variable is None:
                    continue

                if count_applicable:
                    query = query.replace(Constants.QUERY_VARIABLE, Constants.QUERY_COUNT_VARIABLE)

                query = query.replace(Constants.QUERY_VARIABLE, triple_pattern.variable)
            else:
                query = query.replace(Constants.QUERY_VARIABLE, "")

            # Set where clause
            query = query.replace(Constants.QUERY_WHERE_CLAUSE, triple_pattern.query_template)

            # Set ordering and limit TODO skipped for now
            query = query.replace(Constants.QUERY_ORDERING, "")
            query = query.replace(Constants.QUERY_LIMIT, "")

            queries.append(FilledQuery(query.strip(), query_form, used_classes=triple_pattern.used_classes,
                                       used_relations=triple_pattern.used_relations,
                                       used_entities=triple_pattern.used_entities))

        return queries


if __name__ == '__main__':
    q = "Does the district Hemelingen border Obervieland?"

    nlp = spacy.load("en_core_web_lg")

    some = list(nlp(q))
    print(some)
