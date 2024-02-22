# slow-learner-convert
A library to convert [`slow-learner`](https://github.com/nj-vs-vh/slow-learner) output to different data model frameworks.

## Usage
Following the example provided in the `slow-learner` [announcing post](https://nj-vs-vh.name/project/slow-learner) and assuming `Release.py` is in the current directory, one would generate `msgspec` structs equivalent to the `typing.TypedDict` objects in `Release.py` by executing:

```bash
slow-learner-convert --input-file Release.py --output-file Release_msgspec.py --framework msgspec
```

More specifically, if `example.py` contains

```python
from typing import TypedDict


class Foo(TypedDict):
    bar: str
	

Baz = TypedDict("Baz", {"qux": int})
```

then the command line program

```bash
slow-learner-convert --input-file example.py --framework attrs
```

will generate `example_attrs.py`, containing the following code.

```python
import attrs
from typing import TypedDict


@attrs.define
class Foo:
    bar: str


@attrs.define
class Baz:
    qux: int
```

Currently four frameworks are supported:
- [`dataclasses`](https://docs.python.org/3/library/dataclasses.html)
- [`attrs`](https://www.attrs.org/en/stable/index.html)
- [`msgspec`](https://jcristharif.com/msgspec/)
- [`pydantic`](https://docs.pydantic.dev/latest/)

## Installation
```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install slow-learner-convert
```

## Development
I used [`rye`](https://rye-up.com/) (with [`uv`](https://github.com/astral-sh/uv) backend) while developing this:
```bash
git clone git@github.com:gorkaerana/slow-learner-convert.git
cd slow-learner-convert
rye sync
```
