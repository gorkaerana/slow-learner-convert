import ast
from pathlib import Path
import sys


from src.slow_learner_convert.constructor import make_class


if __name__ == "__main__":
    from pprint import pprint

    input_path = Path(sys.argv[1]).resolve()
    for node in ast.walk(ast.parse(input_path.read_text())):
        if isinstance(node, ast.ClassDef):
            pprint(make_class("pydantic", node))
            print()
