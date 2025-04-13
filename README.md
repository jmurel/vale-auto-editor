# Automated Vale editor

A Python script to automate rudimentary edits flagged by the [Vale linter](https://github.com/errata-ai/vale) and saved in Vale's JSON output.


## Getting started

Clone this repo using Git:

```
git clone https://github.com/jmurel/vale-auto-editor
```

When your Vale style rules are ready, create a JSON record of all flagged edits using the Vale CLI:

```
vale path/to/md/dir --output=JSON > vale_output.json
```

This creates a JSON file in the working directory.

Adjust the contents of the `vale-edit.py` script to reference your project's .yml rules. See the script's topmost docstring for directions on which variables need to be adjusted for your project. Then run the script from the command line. The terminal prints all successful revisions and potential errors it encounters.

Feel free to provide additions to the script to accomodate other common .yml rules.