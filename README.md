# slow_learner_convert
A library to convert [`slow_learner`](https://github.com/nj-vs-vh/slow-learner) output to different data model frameworks.

## Usage
Following the example provided in the `slow_learner` [announcing post](https://nj-vs-vh.name/project/slow-learner) and assuming `Release.py` is in the current directory, one would generate `msgspec` structs equivalent to the `typing.TypedDict` objects in `Release.py` by executing:

```bash
slow_learner_convert --input-file Release.py --output-file Release_msgspec.py --framework msgspec
```

Currentlly four frameworks are supported:
- [`dataclasses`](https://docs.python.org/3/library/dataclasses.html)
- [`attrs`](https://www.attrs.org/en/stable/index.html)
- [`msgspec`](https://jcristharif.com/msgspec/)
- [`pydantic`](https://docs.pydantic.dev/latest/)

## Installation
I'm hoping to publish this to PyPI. On the meantime:
```bash
git clone git@github.com:gorkaerana/slow_learner_convert.git
cd slow_learner_convert
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install .
```

## Development
I used [`rye`](https://rye-up.com/) (with [`uv`](https://github.com/astral-sh/uv)) while developing this:
```bash
git clone git@github.com:gorkaerana/slow_learner_convert.git
cd slow_learner_convert
rye sync
```
