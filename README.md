# Snippet-Oracle

Save, categorize, and search code with ease!

## Setting Up

It's a good idea to start by making a virtual python environment.
```
py -3.12 -m venv .venv
.venv\Scripts\activate
```

Then, install the project's dependencies.
```
pip install -r requirements.txt
```

Finally, run `flask run --debug` to host a local server!

## Extra Commands

- `flask reset-db`: Remove all user and snippet data.
- `flask populate-db`: Remove all existing data, then fill the database with fake snippets and users.
