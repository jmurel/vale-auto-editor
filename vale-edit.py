import json
import re
import yaml
from collections import defaultdict


"""
Python script to automate Markdown edits using Vale's JSON output
Overwrites original Markdown file with edited file

Users must change these variables to accomodate local projects:
    - all "variables for rules" inside apply_edits()
    - json_file_path and vale_dir at end of script
"""


def edit_contractions(line: str, start: int, end: int, replacement: str) -> str:
    """
    Replace expanded word/phrase with contraction

    Parameters:
        line (str) -- line from input Markdown
        start (int) -- edit start index
        end (int) -- edit end index
        replacement (str) -- contraction
    Returns:
        str -- input line with contraction
    """
    start -= 1
    orig_word = line[start:end]
    print(f"\t\t\tOriginal word: '{orig_word}'\n\t\t\tReplacement:'{replacement}'")
    revised_line = line[:start] + replacement + line[end:]
    return revised_line


def edit_special_words(line: str, start: int, end: int, replacement: str) -> str:
    """
    Replace OOV word/phrase with in-style word/phrase

    Parameters:
        line (str) -- line from input Markdown
        start (int) -- edit start index
        end (int) -- edit end index
        replacement (str) -- correct term
    Returns:
        str -- input line with replaced word
    """
    start -= 1
    orig_word = line[start:end]
    print(f"\t\t\tOriginal word: '{orig_word}'\n\t\t\tReplacement:'{replacement}'")
    revised_line = line[:start] + replacement + line[end:]
    return revised_line


def edit_header_punct(line: str, start: int, end: int) -> str:
    """
    Remove punctuation from headers

    Parameters:
        line (str) -- line from input Markdown
        start (int) -- edit start index
        end (int) -- edit end index
    Returns:
        str -- input line sans punctuation
    """
    start -= 1
    header_seg = line[start:end]
    revised_seg = header_seg.rstrip('.,;:!?')
    revised_line = line[:start] + revised_seg + line[end:]
    return revised_line


def _load_exceptions(yml_file):
    """
    Load .yml file with 'exceptions' list

    Only used in edit_headcase()
    """
    try:
        with open(yml_file, 'r', encoding='utf-8') as file:
            rule = yaml.safe_load(file)
        return rule.get('exceptions', [])
    except FileNotFoundError:
        print(f"\t\t\tUnable to find YML at {yml_file}.")
        return []
    except Exception as err:
        print(f"\t\t\tUnable to load YML at {yml_file}: {err}")
        return []


def edit_headcase(line: str, start: int, end: int, yml_file: str) -> str:
    """
    Convert header to sentence casing (exclude exceptions)

    Parameters:
        line (str) -- line from input Markdown
        start (int) -- edit start index
        end (int) -- edit end index
        yml_file (str) -- path to .yml file with 'exceptions' list
    Returns:
        str -- input line with sentence casing
    """
    exceptions = _load_exceptions(yml_file)

    start -= 1
    orig_head = line[start:end]
    words = orig_head.split()
    revised_words = []

    for i, word in enumerate(words):
        if word in exceptions:
            revised_words.append(word)
        # capitalize first word of header
        elif i == 0:
            revised_words.append(word.capitalize())
        # lowercase following non-exceptions
        else:
            revised_words.append(word.lower())

    revised_head = ' '.join(revised_words)
    print(f"\t\t\tOriginal header: '{orig_head}'\n\t\t\tRevised header: '{revised_head}'")
    revised_line = line[:start] + revised_head + line[end:]
    return revised_line


def edit_spacing(line: str, start: int, end: int) -> str:
    """
    Standardize spacing around punctuation
    Gobal line edit

    Parameters:
        line (str) -- line from input Markdown
        start (int) -- edit start index
        end (int) -- edit end index
    Returns:
        str -- input line sans punctuation
    """
    line = re.sub(r' +([.,:;?!])', r'\1', line)
    line = re.sub(r'([.,:;?!])(?![ \n\t.,:;?!*]|\Z)', r'\1 ', line)
    line = re.sub(r'([.,:;?!]) +', r'\1 ', line)
    return line.strip()


def edit_eol_whitespace(line: str, start: int, end: int) -> str:
    """
    Remove EOL whitespace

    Parameters:
        line (str) -- line from input Markdown
        start (int) -- edit start index
        end (int) -- edit end index

    Returns:
        str -- input line stripped of EOL whitespace
    """  
    return line.rstrip()



def apply_edits(json_data, vale_dir=".vale"):
    """
    Apply edits to Markdown per Check key in Vale JSON file
        1. Opens Markdown file
        2. Apply local, index-based edits in reverse order (ascending, right-to-left)
        3. Apply global line edits (whitespace)
        4. Overwrite original file

    Parameters:
        json_data -- contents of Vale JSON output file (parsed dictionary)
        vale_dir (str) -- path to .vale dir (parent of "style" subdir)
    """

    # variables for rules
    # EX: "Google.Spacing"
    whitespace_rule = "style.rule"
    eol_rule = "style.rule"
    contraction_rule = "style.rule"
    special_words_rule = "style.rule" # EX: "Google.WordList"
    head_punct_rule = "style.rule"
    head_case_rule = "style.rule"
    # path to Headings.yml with exceptions list header sentence-style casing
    # EX: .vale/style/Google/Headers.yml
    exceptions_yml = '.vale/style/styleguide/rule.yml'

    # GLOBAL = edit modifies whole line
    GLOBAL_RULES = {
        whitespace_rule,
        eol_rule}
    # SPAN = edit modifies only content with index span
    SPAN_RULES = {
        contraction_rule,
        special_words_rule,
        head_punct_rule,
        head_case_rule
    }

    # dict to match .yml rule (key) with edit function (value)
    edit_functions = {
        whitespace_rule: edit_spacing,
        eol_rule: edit_eol_whitespace,
        contraction_rule: edit_contractions,
        special_words_rule: edit_special_words,
        head_punct_rule: edit_header_punct,
        head_case_rule: edit_headcase
    }

    for file_path, revisions in json_data.items():
        print(f"\nEditing file {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.readlines()
        except FileNotFoundError:
            print(f"\tUnable to find {file_path}. Skipping.")
            continue
        except Exception:
            print(f"\tUnable to read {file_path}. Skipping.")
            continue

        revisions_by_line = defaultdict(list)
        for revision in revisions:
            line_num = revision.get("Line")
            if line_num is None: continue
            revisions_by_line[line_num - 1].append(revision) # 0-based index

        lines_to_process = sorted(revisions_by_line.keys())

        for line_num in lines_to_process:
            if line_num < 0 or line_num >= len(content):
                print(f"\t\tUnable to find line {line_num + 1}. Skipping.")
                continue

            line_revisions = revisions_by_line[line_num]
            current_line = content[line_num]

            print(f"\tEditing line {line_num + 1}:")

            # separate revision rules span vs. global per JSON "Check" key
            span_checks = []
            global_checks = set()
            for revision in line_revisions:
                 check = revision.get("Check")
                 if check in SPAN_RULES:
                     span_checks.append(revision)
                 elif check in GLOBAL_RULES:
                     global_checks.add(check)
                 elif check:
                    print(f"\t\tUnable to apply revisions for {check}. Skipping.")

            # span revisions (the last shall be first)
            span_checks.sort(key=lambda e: e.get("Span", [0, 0])[0], reverse=True)

            for revision in span_checks:
                check = revision.get("Check")
                span = revision.get("Span")
                if not span: continue

                start, end = span
                func = edit_functions.get(check)
                if not func: continue

                print(f"\t\tApply local revision {check} at {start}-{end}")
                try:
                    if check in [contraction_rule, special_words_rule]:
                         action = revision.get("Action", {})
                         params = action.get("Params")
                         if params and len(params) > 0:
                             replacement = params[0]
                             current_line = func(current_line, start, end, replacement)
                         else:
                             print(f"\t\t\tMissing replacement Params for {check}. Skipping.")
                    elif check == head_case_rule:
                         current_line = func(current_line, start, end, exceptions_yml)
                    else:
                         current_line = func(current_line, start, end)
                except IndexError:
                     print(f"\t\t\tIndex out of bounds for {check} at {start}-{end}.")
                except Exception as err:
                    print(f"\t\t\tError for {check}: {err}")

            # now global line revision
            if whitespace_rule in global_checks:
                print(f"\t\tApply global line revision {whitespace_rule}")
                try:
                    # dummy spans (0,0)
                    current_line = edit_spacing(current_line, 0, 0)
                except Exception as err:
                    print(f"\t\t\tError for {whitespace_rule}: {err}")

            if eol_rule in global_checks:
                print(f"\t\tApply global line revision {eol_rule}")
                try:
                    # dummy spans (0,0)
                    current_line = edit_eol_whitespace(current_line, 0, 0)
                except Exception as err:
                    print(f"\t\t\tError for {eol_rule}: {err}")

            # line break check
            if not current_line.endswith('\n') and content[line_num].endswith('\n'):
                 content[line_num] = current_line + '\n'
            else:
                 content[line_num] = current_line

        # write over original file
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(content)
            print(f"\tCompleted revisions for {file_path}")
        except Exception as err:
            print(f"\tError writing revisions to {file_path}: {err}")

if __name__ == "__main__":


    # path to vale JSON output
    json_file_path = 'vale_output.json'

    # path to .vale dir (parent of "style" subdir)
    vale_dir = '.vale'

    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        apply_edits(json_data, vale_dir)
        print("\nRevisions complete.\n")

    except FileNotFoundError:
        print(f"Unable to find JSON at '{json_file_path}'")
    except json.JSONDecodeError:
        print(f"Unable to parse JSON at '{json_file_path}'")
    except Exception as err:
        print(f"Unexpected error: {err}")
