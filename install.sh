#!/bin/bash
pip install -U pip setuptools wheel
pip install -U spacy==3.2.0
python -m spacy download en_core_web_sm
