# DASS Assignment 2

Git repository: `https://github.com/nanchan1912/DASS-A2.git`
GDrive link: `https://drive.google.com/drive/folders/1rn8rbDOnF1h1DeURgYkzaJcx8ZvJ5p5S?usp=sharing`

## Submission Structure

- `whitebox/`
- `integration/`
- `blackbox/`

## Dependencies

Install the required Python packages before running the tests:

```bash
pip install pytest requests
```

## How To Run Whitebox

Run the MoneyPoly code:

```bash
python whitebox/code/main.py
```

Run the white-box tests:

```bash
python -m pytest whitebox/tests -q
```

## How To Run Integration

Run the integration tests:

```bash
python -m pytest integration/tests -q
```

The StreetRace Manager code is inside `integration/code/`.

## How To Run Blackbox

Start the QuickCart API on port `8080` first, then run:

```bash
python -m pytest blackbox/tests -q
```

The black-box tests use:
- base URL: `http://127.0.0.1:8080/api/v1`
- headers: `X-Roll-Number` and `X-User-ID` as required by the API, placeholder throughout are 2024111034 and 1.

## Notes

- The hand-drawn CFG image is in `whitebox/diagrams/`. Might nto have attached it in report due to space issues.
- The hand-drawn call graph image is in `integration/diagrams/`.
- I was unable to attach the images to the report due tot he size of the folder. I apologize in advance.

