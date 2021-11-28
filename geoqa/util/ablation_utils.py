from typing import List

from geoqa.model.beans import QueryAndResult
from geoqa.util.property_utils import PropertyUtils


class AblationProvider(object):
    _golden_answers = None

    @classmethod
    def get_golden_answers(cls):
        if cls._golden_answers is None:
            print("triggered")
            questions_json = PropertyUtils.read_benchmark()["questions"]
            cls._golden_answers = {}
            for q in questions_json:
                question_text = q["question"][0]["string"].strip()
                golden = {}
                cls._golden_answers[question_text] = golden
                golden['type'] = q['answertype']
                golden['answer'] = q['answers'][0]
                if 'boolean' in q['answers'][0]:
                    golden['value'] = cls.get_boolean_value(q['answers'][0])
                elif len(q['answers'][0]["results"]['bindings']):
                    golden['value'] = cls.get_answer_strings(q['answers'][0])

        return cls._golden_answers

    @classmethod
    def get_best_answer(cls, cleaned_question, results: List[QueryAndResult]):
        if cleaned_question in cls._golden_answers:
            golden = cls._golden_answers[cleaned_question]
            if golden['type'] == 'boolean':
                for r in results:
                    if golden['value'] == cls.get_boolean_value(r.result):
                        return [r]
            elif golden['type'] == 'number':
                for r in results:
                    if golden['value'][0] in cls.get_answer_strings(r.result):
                        return [r]
            elif golden['type'] == 'resource':
                max_r = None
                max_common = 0
                golden_strings = cls.get_answer_strings(golden['answer'])
                for r in results:
                    answer_strings = cls.get_answer_strings(r.result)
                    common = len(set(golden_strings).intersection(set(answer_strings)))
                    if common > max_common:
                        max_common = common
                        max_r = r
                return [max_r] if max_r is not None else results
        else:
            print("ABLATION FLAG TRUE BUT QUESTION NOT FOUND: ", cleaned_question)

        print("ABLATION FLAG TRUE BUT BEST ANSWER NOT FOUND: ", cleaned_question)
        return results

    @classmethod
    def get_selected_variable(cls, rs_binding):
        return rs_binding['head']['vars'][0]

    @classmethod
    def get_answer_strings(cls, rs_binding):
        selected_var = cls.get_selected_variable(rs_binding)
        bindings = rs_binding["results"]['bindings']
        values = []
        for b in bindings:
            values.append(b[selected_var]['value'])
        return values

    @classmethod
    def get_boolean_value(cls, rs_binding):
        return rs_binding.get('boolean')
