import itertools
import re
from typing import List, Tuple

import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

from geoqa import app as flask_app
from geoqa.model.beans import LinkingResponse, FilledPattern, LinkedCandidate, Constants, FilledQuery
from geoqa.util.property_utils import PropertyUtils

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe('spacytextblob')


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

    def generate_triple_patterns(self, links_by_position):
        flattened = {}
        for start_index in links_by_position:
            categories = set()
            for link in links_by_position[start_index]:
                if not link.is_relation():
                    categories.add(link.category)

            if len(categories) > 0:
                flattened[start_index] = categories

        start_indexes = sorted(flattened.keys())

        # If only a class is linked in the question in addition to (optionally) the relation
        if len(start_indexes) == 1 and Constants.CLASS in flattened[start_indexes[0]]:
            return [(Constants.CLASS,)]

        triple_patterns = set()
        for i in range(len(start_indexes)):
            for j in range(i + 1, len(start_indexes)):
                combinations = list(itertools.product(flattened[start_indexes[i]], flattened[start_indexes[j]]))
                triple_patterns = triple_patterns.union(combinations)

        # If linking has not linked any entities and only classes then add a single class pattern
        if len(self.linking_info.linkedEntities) == 0 and len(self.linking_info.linkedClasses) > 0:
            triple_patterns = triple_patterns.union([(Constants.CLASS,)])

        return_value = list(triple_patterns)
        self.LOG.info(f"Triple patterns: {return_value}")
        return return_value

    def fill_patterns(self, triple_patterns) -> List[FilledPattern]:
        basic_patterns = PropertyUtils.get_query_templates(self.geo_operator)

        filled_patterns: List[FilledPattern] = []
        for triple_pattern in triple_patterns:
            basic_pattern_key = triple_pattern[0]
            for i in range(1, len(triple_pattern)):
                basic_pattern_key = basic_pattern_key + "__" + triple_pattern[i]
            query_pattern_info: dict = basic_patterns.get(basic_pattern_key)

            if query_pattern_info is not None:
                self.LOG.info(f"Basic pattern: {basic_pattern_key}")

                query_pattern = query_pattern_info.get("pattern")
                variable = query_pattern_info.get("variable")

                # Make combinations
                combinations = []

                # There is always at least one placeholder, i.e., class
                first_placeholder = triple_pattern[0]
                first_placeholder_set = None
                if first_placeholder == Constants.CLASS:
                    first_placeholder_set = self.linking_info.linkedClasses
                elif first_placeholder == Constants.ENTITY:
                    first_placeholder_set = self.linking_info.linkedEntities
                for element in first_placeholder_set:
                    combinations.append((element,))

                if len(triple_pattern) > 1:
                    second_placeholder = triple_pattern[1]
                    second_placeholder_set = None
                    if second_placeholder == Constants.CLASS:
                        second_placeholder_set = self.linking_info.linkedClasses
                    elif second_placeholder == Constants.ENTITY:
                        second_placeholder_set = self.linking_info.linkedEntities

                    combinations = list(itertools.product(first_placeholder_set, second_placeholder_set))
                    # Remove pairs which are self products
                    combinations = [c for c in combinations if c[0].startIndex != c[1].startIndex]

                for combination in combinations:
                    filled: List[FilledPattern] = self.apply_combination(query_pattern, variable, combination)
                    filled_patterns.extend(filled)

        return filled_patterns

    def apply_combination(self, query_template: str, variable: str,
                          combination: Tuple[LinkedCandidate]) -> List[FilledPattern]:

        filled_patterns = []

        filled = query_template
        used_classes = []
        used_entities = []
        used_relations = []

        # Handle class and entities as part of the combination
        for link in combination:
            if link.is_class():
                filled = filled.replace(Constants.CLASS_PLACEHOLDER, f"<{link.uri}>")
                used_classes.append(link)
            elif link.is_entity():
                filled = filled.replace(Constants.ENTITY_PLACEHOLDER, f"<{link.uri}>")
                used_entities.append(link)

        # Handle relations as an additional constrains that targets the selected variable
        if len(self.linking_info.linkedRelations) > 0:
            for relation in self.linking_info.linkedRelations:
                filled_with_relation = str(filled)
                relation_triple_pattern = \
                    f'{variable} <{relation.uri}> {Constants.QUERY_RELATION_VARIABLE_RAW} . ' \
                    f'BIND(xsd:float(REPLACE(xsd:string({Constants.QUERY_RELATION_VARIABLE_RAW}), "[^\\\\d\\\\.,]", ""))' \
                    f' AS {Constants.QUERY_RELATION_VARIABLE})'

                filled_with_relation = filled_with_relation.replace(Constants.QUERY_RELATION, relation_triple_pattern)
                if self.get_comparative_token() is not None:
                    relation_filter = self.get_relation_filter(Constants.QUERY_RELATION_VARIABLE)
                    if relation_filter is None:
                        continue

                    filled_with_relation = filled_with_relation.replace(Constants.QUERY_RELATION_FILTER, relation_filter)
                    used_relations.append(relation)
                else:
                    filled_with_relation = filled_with_relation.replace(Constants.QUERY_RELATION_FILTER, "")
                    used_relations.append(relation)

                filled_patterns.append(FilledPattern(filled_with_relation, variable, used_classes=used_classes,
                                                     used_relations=used_relations, used_entities=used_entities))

        else:
            filled = filled.replace(Constants.QUERY_RELATION, "")
            filled = filled.replace(Constants.QUERY_RELATION_FILTER, "")
            filled_patterns.append(
                FilledPattern(filled, variable, used_classes=used_classes, used_entities=used_entities))

        return filled_patterns

    def is_superlative_present(self):
        return self.get_superlative_token() is not None

    def get_superlative_token(self):
        for token in self.parsed_question:
            if token.tag_ == "JJS":
                return token

        return None

    def get_comparative_token(self):
        for token in self.parsed_question:
            if token.tag_ == "JJR":
                return token

        return None

    def get_relation_filter(self, filter_variable: str):
        filter_value = None
        for token in self.parsed_question:
            if token.pos_ == "NUM" and re.search("\\d", token.text) is not None:
                filter_value = float(token.text)

        if filter_value is None:
            return None

        comparative = self.get_comparative_token()
        comparison_operator = ">" if comparative._.polarity > 0 else "<"
        return f"FILTER ({filter_variable} {comparison_operator} {str(filter_value)})"

    def determine_query_form(self) -> str:
        if self.parsed_question[0].lemma_ == "do" or self.parsed_question[0].lemma_ == "be":
            return Constants.QUERY_FORM_ASK
        else:
            return Constants.QUERY_FORM_SELECT

    def should_apply_count_aggregate(self):  # todo improve with classifier
        first_two_words = self.parsed_question[:2].lemma_
        return first_two_words == "how many"

    def populate_query_anatomy(self, query_form: str, count_applicable: bool,
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

            # Set ordering and limit
            if self.is_superlative_present():
                if self.get_superlative_token()._.polarity > 0:
                    ordering = f"ORDER BY DESC({Constants.QUERY_RELATION_VARIABLE})"
                else:
                    ordering = f"ORDER BY ASC({Constants.QUERY_RELATION_VARIABLE})"

                query = query.replace(Constants.QUERY_ORDERING, ordering)
                query = query.replace(Constants.QUERY_LIMIT, "LIMIT 1")
            else:
                query = query.replace(Constants.QUERY_ORDERING, "")
                query = query.replace(Constants.QUERY_LIMIT, "")

            # For proximity query, distance must be extracted
            if self.geo_operator == Constants.GEO_OPERATOR_PROXIMITY:
                distance = None
                for token in self.parsed_question:
                    if token.pos_ == "NUM":
                        next_token = self.parsed_question[token.i + 1]
                        unit_search = re.search(r'm|km|(kilo)?\s?(meter|metre)s?', next_token.text)
                        if unit_search is not None:
                            if unit_search.group().lower().startswith("m"):
                                distance = float(token.text)
                            elif unit_search.group().lower().startswith("k"):
                                distance = float(token.text) * 1000

                if distance is not None:
                    query = query.replace(Constants.QUERY_PROXIMITY_VALUE, str(distance))
                else:
                    query = query.replace(Constants.QUERY_PROXIMITY_VALUE, "250")

            queries.append(FilledQuery(query.strip(), query_form, used_classes=triple_pattern.used_classes,
                                       used_relations=triple_pattern.used_relations,
                                       used_entities=triple_pattern.used_entities))

        return queries
