#!/bin/bash
source ./venv/bin/activate
FILES=`find . -type f -name "*.py" -not -path "./venv/*"`
flake8 --ignore=E501,E266,W503 $FILES
mypy --strict $FILES
