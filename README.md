# Watson Knowledge Catalog (WKC) Bulk Guru

This repo demonstrates how the WKC API can be used to perform quick updates in bulk for some laborous tasks when done through the UI.

## Installation

1. Make sure the prerequisites are installed.
2. clone this github repository.
3. Install necessary dependencies:

```sh
pip install -r requirements.txt
```

4. Create `.env` file with Secrets:

```sh
cp .envExample .env
```


### Swagger UIs and other API docs

- <https://{hostname}/v3/search/api/explorer>


### Programming resources

- Beginners Guide to Python: <https://wiki.python.org/moin/BeginnersGuide/NonProgrammers>
- Programmers Guide to Python: <https://wiki.python.org/moin/BeginnersGuide/Programmers>
- Getting Stared with Pandas: <https://pandas.pydata.org/docs/getting_started/index.html>

## Use Cases

Following are the key use cases that are covered in this repo

### How do I authenticate?

- Session class
- Hostname, User, Pwd
- Headers, Token

### How do I search for artefacts?

- Using Global Search to demonstrate how to find artefacts in WKC

### How do I perfom mass (batch) updates?

- How to export a list of all data assets along with their columns and descriptions in a specific catalog and write these into a CSV
- Now the CSV can be manipulated by a business user in that for instance a description can be added or modified
- Then the CSV can be imported and all descriptions contained therein will updated updated in the catalog
