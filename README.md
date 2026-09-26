# srformat

Every spaced-repetition app writes its review history in its own dialect.
One export has dates as `2024-1-5`, another as `Jan 5, 2024`. One writes
intervals as `3d`, another as `P3D`, another as a bare `3` and expects you
to know it means days. Ease factors show up as `2.5`, `250`, or `250%`
depending on whether the tool thinks in multipliers or percentages.
Grades come as `again/hard/good/easy`, `0/1/2/3`, or `fail/pass`.

`srformat` takes that mess and turns it into one fixed shape:

```
due,interval_days,ease,rating
```

`due` is an ISO date, `interval_days` is a plain integer, `ease` is a
float like `2.50`, and `rating` is one of `again/hard/good/easy`.

## Usage

Raw input, one record per line, fields separated by comma, semicolon,
pipe, or tab (mix and match, it doesn't care):

```
2024-1-5, 3d, 250%, good
Jan 6 2024 | P7D | 2.3 | easy
2024/01/08;10;2.5;again
```

Run it:

```
python -m srformat.cli reviews.txt
```

Output:

```
due,interval_days,ease,rating
2024-01-05,3,2.50,good
2024-01-06,7,2.30,easy
2024-01-08,10,2.50,again
```

Reading from stdin works too:

```
cat reviews.txt | python -m srformat.cli
```

By default a line that fails to parse stops the run and prints the
reason to stderr. Pass `--skip-errors` to log and continue instead.

## As a library

```python
from srformat.normalize import normalize_record

record = normalize_record("2024-1-5, 3d, 250%, good")
record.due            # date(2024, 1, 5)
record.interval_days  # 3
record.ease            # 2.5
record.rating_label   # "good"
```

## Tests

```
python -m unittest discover -s tests
```

## What it does not do yet

It normalizes one record at a time - it doesn't dedupe cards, merge
histories across apps, or know anything about a specific app's export
schema. See the roadmap for what's next.
