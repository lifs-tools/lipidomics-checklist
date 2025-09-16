import json
import sqlite3
from datetime import datetime
import time
from urllib.parse import unquote
from fontTools.ttLib import TTFont
import re

DEFAULT_FONT = "LMSans"
MISSING_CHAR = '▯'
MISSING_CHAR_FONT = "Symbola"

workflow_types = {"gen": "General Lipidomics", "di": "Direct Infusion", "sep": "Separation", "img": "Imaging"}

font_sets = {
    "LMSans": [
        ["LMSansR", "lmsans10-regular.otf"],
        ["LMSansB", "lmsans10-bold.otf"],
        ["LMSansI", "lmsans10-oblique.otf"],
        ["LMSansBI", "lmsans10-boldoblique.otf"],
    ],
    "HaranoAjiMincho": [
        ["HaranoAjiMinchoR", "HaranoAjiMincho-regular.otf"],
        ["HaranoAjiMinchoB", "HaranoAjiMincho-bold.otf"],
        ["HaranoAjiMinchoI", "HaranoAjiMincho-regular.otf"],
        ["HaranoAjiMinchoBI", "HaranoAjiMincho-bold.otf"],
    ],
    "NotoSansDevanagari": [
        ["NotoSansDevanagariR", "NotoSansDevanagari-Regular.ttf"],
        ["NotoSansDevanagariB", "NotoSansDevanagari-Bold.ttf"],
        ["NotoSansDevanagariI", "NotoSansDevanagari-Regular.ttf"],
        ["NotoSansDevanagariBI", "NotoSansDevanagari-Bold.ttf"],
    ],
    "DejaVuSans": [
        ["DejaVuSansR", "DejaVuSans.ttf"],
        ["DejaVuSansB", "DejaVuSans-Bold.ttf"],
        ["DejaVuSansI", "DejaVuSans-Oblique.ttf"],
        ["DejaVuSansBI", "DejaVuSans-BoldOblique.ttf"],
    ],
    "Symbola": [
        ["SymbolaR", "Symbola.ttf"],
        ["SymbolaB", "Symbola.ttf"],
        ["SymbolaI", "Symbola.ttf"],
        ["SymbolaBI", "Symbola.ttf"],
    ],
}

fallback_fonts = ["LMSans", "HaranoAjiMincho", "NotoSansDevanagari", "DejaVuSans", "Symbola"]
font_types = {"R", "B", "I", "BI"}

font_preamble = []
FONT_COVERAGE = {}
for font_set_name, font_set in font_sets.items():
    font_preamble.append(f"""
\\newfontfamily\\{font_set_name}[
  Path = ./fonts/,
  UprightFont = {font_set[0][1]},
  BoldFont    = {font_set[1][1]},
  ItalicFont  = {font_set[2][1]},
  BoldItalicFont = {font_set[3][1]}
]{{{font_set_name}}}\n\n
""")

    for name, path in font_set:
        ttf = TTFont("./fonts/" + path)
        cmap = ttf["cmap"].getBestCmap()
        FONT_COVERAGE[name] = set(cmap.keys())
        ttf.close()
#font_preamble += [f"\\setmainfont{{{DEFAULT_FONT}}}"]
font_preamble = "".join(font_preamble)


def split_verison_number(text_version):
    version_array = [1, 0, 0];

    text_version = text_version.split(".")
    if len(text_version) != 3 or len(text_version[0]) < 2:
        return version_array

    text_version[0] = text_version[0][1:]

    if not text_version[0].isdigit() or not text_version[1].isdigit() or not text_version[2].isdigit():
        return version_array

        version_array[0] = int(text_version[0])
        version_array[1] = int(text_version[1])
        version_array[2] = int(text_version[2])


    return version_array


def is_first_version_higher(first_version, version_to_test):
    if first_version == None or version_to_test == None: return False

    first_version_array = split_verison_number(first_version)
    version_to_test_array = split_verison_number(version_to_test)

    return (
        (version_to_test_array[0] < first_version_array[0]) or
        (version_to_test_array[0] == first_version_array[0]) and (
            (version_to_test_array[1] < first_version_array[1]) or
            (version_to_test_array[1] == first_version_array[1]) and (
                (version_to_test_array[2] < first_version_array[2])
            )
        )
    )



def get_workflow_type(mycursor, table_prefix, uid, entry_id):

    sql = "SELECT form, fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
    mycursor.execute(sql, (uid, entry_id))
    result = json.loads(mycursor.fetchone()["fields"])
    for field in result["pages"][0]["content"]:
        if field["name"] == "workflowtype":
            workflow_type = field["value"] if field["value"] in workflow_types else "gen"
    return workflow_type



logging = open("log.txt", "wt")
def fill_report_fields(mycursor, table_prefix, uid, entry_id, titles, report_fields, version):

    sql = "SELECT form, fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
    mycursor.execute(sql, (uid, entry_id))
    result = json.loads(mycursor.fetchone()["fields"])
    workflow_type = "gen"

    visible = {}
    conditions = {}
    choice_to_field = {}
    field_map = {}
    form_version = result["version"] if "version" in result else "v0.9.9"

    version.append(form_version)

    for field in result["pages"][0]["content"]:
        if field["name"] == "workflowtype":
            workflow_type = field["value"] if field["value"] in workflow_types else "gen"


    for page in result["pages"]:
        for field in page["content"]:
            field_name = field["name"]
            visible[field_name] = True

            field_map[field_name] = field
            if field["type"] in {"select", "multiple"} and "choice" in field:
                for choice in field["choice"]:
                    if "name" in choice:
                        field_map[choice["name"]] = choice
                        choice_to_field[choice["name"]] = field_name
            else:
                choice_to_field[field_name] = field_name


            # check for any logical conditions
            if "condition" not in field or len(field["condition"]) == 0: continue

            condition = []
            for condition_and in field["condition"].split("|"):
                conjunction = []
                for con in condition_and.split("&"):
                    single_condition = None
                    operator = "="
                    if con.find("~") != -1:
                        single_condition = con.split("~")
                        operator = "~"

                    else:
                        single_condition = con.split("=")

                    if len(single_condition) != 2: continue;

                    key, value = single_condition
                    l = len(value)

                    if value[0] == "'" and value[-1] == "'":
                        value = value[1 : -1]

                    else:
                        try:
                            value = float(value)
                        except:
                            continue
                    conjunction.append([key, operator, value])

                condition.append(conjunction)
            conditions[field_name] = condition


    for page in result["pages"]:
        for field in page["content"]:
            field_name = field["name"]
            if "type" in field and field["type"] in {"number", "select"} \
                and (("required" not in field) or (field["required"] == 0)) \
                and (("activated" not in field) or (field["activated"] == 0)):
                #and (is_first_version_higher(form_version, "v.2.4.0") and (("activated" not in field) or (field["activated"] == 0))):
                    visible[field_name] = False
                    continue

            if "condition" not in field or len(field["condition"]) == 0: continue
            visible[field_name] = False
            for condition_and in conditions[field_name]:
                condition_met = True
                for single_condition in condition_and:
                    key, operator, value = single_condition
                    conditional_field_key = choice_to_field[key]
                    conditional_field = field_map[conditional_field_key]

                    if conditional_field["type"] in {"number", "select"}:
                    #if is_first_version_higher(form_version, "v.2.4.0") and conditional_field["type"] in {"number", "select"}:
                        condition_met &= ("required" not in conditional_field) or (conditional_field["required"] == 1) or (("activated" in conditional_field) and (conditional_field["activated"] == 1))

                    field_value = field_map[key]["value"] if ("type" not in field_map[key] or field_map[key]["type"] != "number") else float(field_map[key]["value"])
                    condition_met &= (conditional_field_key in visible and visible[conditional_field_key]) and ((operator == "=" and field_value == value) or (operator == "~" and field_value != value))
                    if field_name == "type_of_blanks": logging.write(f"{field_name} {field_value} {key} {operator} {value} {field_value == value} {conditional_field_key} {conditional_field_key in visible} {visible[conditional_field_key]}\n")
                visible[field_name] |= condition_met
            logging.write(f"{field_name} {visible[field_name]}\n")


    for page in result["pages"]:
        titles.append(page["title"])
        report_fields.append([])
        values = {}
        for field in page["content"]:
            if "type" not in field or "name" not in field or "label" not in field: continue
            if field["name"] in visible and not visible[field["name"]]: continue

            if field["type"] == "text":
                if field["label"][:5].lower() == "other":
                    if field["label"][6:].lower() in values:
                        values[field["label"][6:].lower()][-1] = field["value"]
                else:
                    if len(field["value"]) > 0:
                        values[field["label"].lower()] = [field["value"]]
                        report_fields[-1].append([field["label"], ""])

            elif field["type"] == "number":
                values[field["label"].lower()] = [str(field["value"])]
                report_fields[-1].append([field["label"], ""])

            elif field["type"] in {"select", "multiple"}:
                choice_values = []
                for choice in field["choice"]:
                    if choice["value"] == 1:
                        choice_values.append(choice["label"])
                values[field["label"].lower()] = choice_values
                if len(choice_values) > 0:
                    report_fields[-1].append([field["label"], ""])

            elif field["type"] == "table":
                values[field["label"].lower()] = ["!!!TABLE!!!%s!!!CONTENT!!!%s" % (field["columns"], field["value"])]
                #values[field["label"].lower()] = [field["value"]]
                report_fields[-1].append([field["label"], ""])

        for i in range(len(report_fields[-1])):
            key = report_fields[-1][i][0].lower()
            if key in values:
                report_fields[-1][i][1] = ", ".join(values[key])


def has_matching_xml_tags(s):
    # Regex to find all tags (both opening and closing)
    tag_pattern = re.finditer(r"</?([a-zA-Z0-9]+)[^>]*>", s)
    stack = []

    for tag in tag_pattern:
        full_tag = tag.group(0)  # Full matched tag (e.g., "<sup>" or "</sup>")
        tag_name = tag.group(1)  # Extracted tag name (e.g., "sup")

        if full_tag.startswith("</"):  # Closing tag
            if not stack or stack[-1] != tag_name:
                return False  # Mismatched closing tag
            stack.pop()  # Match found → Pop from stack
        elif not full_tag.endswith("/>"):  # Opening tag (excluding self-closing)
            stack.append(tag_name)  # Push opening tag to stack

    return len(stack) == 0  # True if all tags are matched



def contains_xml_tags(s):
    return bool(re.search(r"<[^<>]+>", s))



def unicoding(t):
    def encode(text):
        return "".join(["{\\ }" if ord(c) == 32 else "\\char\"%s" % hex(ord(c))[2:].upper() for c in text])

    encoded = ""
    if contains_xml_tags(t):
        if not has_matching_xml_tags(t):
            encoded = "".join(t)

        else:
            tokens = [t]
            for pattern in ["<sup>", "</sup>", "<sub>", "</sub>"]:
                test_tokens = tokens
                tokens = []
                for token in test_tokens:
                    split_tokens = token.split(pattern)
                    for i, token in enumerate(split_tokens):
                        if i > 0: tokens.append(pattern)
                        if len(token) > 0: tokens.append(token)
            for i in range(len(tokens)):
                if tokens[i] == "<sup>": tokens[i] = "\\textsuperscript{"
                elif tokens[i] == "<sub>": tokens[i] = "\\textsubscript{"
                elif tokens[i] in {"</sub>", "</sup>"}: tokens[i] = "}"
                else: tokens[i] = encode(tokens[i])
                encoded = "".join(tokens)

    else:
        encoded = encode(t)

    return encoded




def font_encoding(text, font_type = "R", size = 8, to_string = True):
    if font_type not in font_types:
        raise Exception(f"Font type '{font_type}' not in {font_types}.")

    latex = []
    last_font = None
    last_position = 0

    def add_encoding(txt, st, en, font, lst, s, ft):
        if en - st > 0:
            if ft in {"B", "BI"}: lst.append(r"{\textbf{")
            if ft in {"I", "BI"}: lst.append(r"{\textit{")

            if font != None:
                lst.append(f"{{\\fontsize{{{s}}}{{{int(s + 2)}}}\\selectfont {{\\{font} {unicoding(txt[st : en])}}}}}")
            else:
                lst.append(f"{{\\fontsize{{{s}}}{{{int(s * 1.2)}}}\\selectfont {{\\{MISSING_CHAR_FONT} {MISSING_CHAR * (en - st)}}} }}")

            if ft in {"I", "BI"}: lst.append(r"}}")
            if ft in {"B", "BI"}: lst.append(r"}}")

    for i, c in enumerate(text):
        # pick font
        current_font = None
        for font in fallback_fonts:
            if ord(c) in FONT_COVERAGE[font + font_type]:
                current_font = font
                break

        if last_font != current_font:
            add_encoding(text, last_position, i, last_font, latex, size, font_type)
            last_position = i
            last_font = current_font

    add_encoding(text, last_position, len(text), last_font, latex, size, font_type)
    return "".join(latex) if to_string else latex





def make_table(title, text):


    column_labels, content = text[11:].split("!!!CONTENT!!!")
    column_labels = column_labels.split("|")
    content = content.split("|")
    num_cols = len(column_labels)

    result_text = ["%s \\\\ \\multicolumn{7}{P{0.99\\textwidth}}{" % title]
    result_text.append("\\centering \\begin{tabular}{%s}\\rowcolor{ILSgreen!60}" % (("P{%0.3f\\hsize}" % (0.93 / num_cols)) * num_cols))
    result_text.append(" & ".join("\\textbf{\\color{white}%s}" % column_label for column_label in column_labels) + "\\\\ \\hline \\end{tabular} \n")
    result_text.append("}\\\\ \n")


    row_cnt, col_cnt = 0, 0
    for cell in content:
        if col_cnt == 0:
            if row_cnt > 0: result_text.append(" \\end{tabular} }\\\\ \n")

            result_text.append("\\multicolumn{7}{P{0.99\\textwidth}}{")
            result_text.append("\\centering \\begin{tabular}{%s}\\rowcolor{%s}" % ((("P{%0.3f\\hsize}" % (0.93 / num_cols)) * num_cols), ("ILSgreen!20" if row_cnt % 2 == 1 else "white")))
        else:
            result_text.append(" & ")

        result_text.append(font_encoding(unquote(cell)))

        col_cnt += 1
        if col_cnt == num_cols:
            result_text.append("\\\\")
            col_cnt = 0
            row_cnt += 1

    result_text.append(" \\hline \\end{tabular} \\\\[1pt] }\\\\ \n")

    return "".join(result_text)


    result_text = ["\\multicolumn{3}{P{0.49\\textwidth}}{%s\\newline \\vskip-7px \n" % title]

    column_labels, content = text[11:].split("!!!CONTENT!!!")
    column_labels = column_labels.split("|")
    content = content.split("|")
    num_cols = len(column_labels)

    result_text.append("\\centering \\begin{tabular}{%s}\\rowcolor{ILSgreen!60}" % (("P{%0.3f\\hsize}" % (0.93 / num_cols)) * num_cols))

    result_text.append(" & ".join("\\textbf{\\color{white}%s}" % column_label for column_label in column_labels) + "\\\\ \\hline \n")


    row_cnt = 0
    for i, cell in enumerate(content):
        if i % num_cols == 0:
            result_text.append("\\rowcolor{%s}" % ("ILSgreen!20" if row_cnt % 2 == 1 else "white"))
        else:
            result_text.append(" & ")

        result_text.append(font_encoding(unquote(cell)))

        if i % num_cols == num_cols - 1:
            result_text.append("\\\\")
            row_cnt += 1

    if i % num_cols < num_cols - 1: result_text.append("\\\\")
    result_text.append("\\hline  \\end{tabular} \\vskip-7px}")

    return "".join(result_text)




def create_report(mycursor, table_prefix, uid, entry_id, report_file):
    ## fill general data
    version, titles, report_fields = [], [], []
    workflow_type = get_workflow_type(mycursor, table_prefix, uid, entry_id)
    fill_report_fields(mycursor, table_prefix, uid, entry_id, titles, report_fields, version)
    version = version[0]

    for i in range(len(titles)):
        if type(titles[i]) == dict:
            if workflow_type in titles[i]: titles[i] = titles[i][workflow_type]
            elif "default" in titles[i]: titles[i] = titles[i]["default"]
            else: titles[i] = "NA"

    ## fill sample specific data
    sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = %i;" % (table_prefix, entry_id)
    mycursor.execute(sql)
    sample_entry_ids = [row["sample_form_entry_id"] for row in mycursor.fetchall()]

    sample_report_fields = []
    sample_titles = ["Sample %i" % (i + 1) for i in range(len(sample_entry_ids))]
    for i, sample_entry_id in enumerate(sample_entry_ids):
        tmp_titles = []
        tmp_report_fields = []
        fill_report_fields(mycursor, table_prefix, uid, sample_entry_id, tmp_titles, tmp_report_fields, [])

        sample_ids = {k: v for k, v in tmp_report_fields[0][:3]}
        if "Sample set name" in sample_ids and "Sample origin" in sample_ids and "Sample type" in sample_ids:
            sample_titles[i] = "%s / %s / %s" % (sample_ids["Sample set name"], sample_ids["Sample origin"], sample_ids["Sample type"])
            tmp_report_fields[0] = tmp_report_fields[0][3:]

        sample_report_fields.append(tmp_report_fields[0])




    ## fill lipid class specific data
    sql = "SELECT class_form_entry_id FROM %sconnect_lipid_class WHERE main_form_entry_id = %i;" % (table_prefix, entry_id)
    mycursor.execute(sql)
    class_entry_ids = [row["class_form_entry_id"] for row in mycursor.fetchall()]

    lipid_classes_report_fields = []
    lipid_classes_titles = []
    for i, class_entry_id in enumerate(class_entry_ids):
        tmp_titles = []
        tmp_report_fields = []

        fill_report_fields(mycursor, table_prefix, uid, class_entry_id, tmp_titles, tmp_report_fields, [])
        lipid_classes_report_fields += tmp_report_fields

        lipid_class_prefix = "Lipid class %i" % (i + 1)

        for tmp_report_field, tmp_title in zip(tmp_report_fields, tmp_titles):
            lipid_class, adduct_ms1, adduct_ms2, other_adduct_ms1, other_adduct_ms2 = "", "", "", "", ""
            for tmp_rep_field in tmp_report_field:
                if tmp_rep_field[0] == "Lipid class": lipid_class = tmp_rep_field[1]
                elif tmp_rep_field[0] == "MS<sup>1</sup> adduct": adduct_ms1 = tmp_rep_field[1]
                elif tmp_rep_field[0] == "MS<sup>2</sup> adduct": adduct_ms2 = tmp_rep_field[1]
                elif tmp_rep_field[0] == "Other MS<sup>1</sup> adduct": other_adduct_ms1 = tmp_rep_field[1]
                elif tmp_rep_field[0] == "Other MS<sup>2</sup> adduct": other_adduct_ms2 = tmp_rep_field[1]

            if len(lipid_class) > 0:
                lipid_class_prefix = lipid_class
                if len(adduct_ms1) > 0: lipid_class_prefix += adduct_ms1
                elif len(other_adduct_ms1) > 0: lipid_class_prefix += other_adduct_ms1
                elif len(adduct_ms2) > 0: lipid_class_prefix += adduct_ms2
                elif len(other_adduct_ms2) > 0: lipid_class_prefix += other_adduct_ms2

            lipid_class_title = "%i) %s / %s" % (i + 1, lipid_class_prefix, tmp_title)
            lipid_classes_titles.append(lipid_class_title)

    tex_preamble = """\\documentclass{article}

% add packages
\\usepackage[utf8x]{inputenc}
\\usepackage{graphicx}
\\usepackage{xcolor}
\\usepackage{adjustbox}
\\usepackage{amsmath}
\\usepackage[a4paper, portrait, margin=2cm]{geometry}
\\usepackage{tocloft}
\\usepackage{array}
\\usepackage{colortbl}
\\usepackage{longtable}
\\setlength{\\LTpre}{1pt}
\\setlength{\\LTpost}{2pt}
\\usepackage{textcomp}
\\usepackage[hidelinks]{hyperref}
\\usepackage{titlesec}
\\usepackage{needspace}
\\usepackage{fontspec}
"""
    tex_preamble += font_preamble + "\n"
    tex_preamble += """

\\makeatletter
\\renewcommand{\\section}{\\@startsection{section}{1}{0pt}%
  {0ex} % negative space before
  {0pt}    % space after
  {\\normalfont\\Large\\bfseries}}
\\renewcommand{\\subsection}{\\@startsection{subsection}{2}{0pt}%
  {0ex} % negative space before
  {1ex}    % space after
  {\\normalfont\\large\\bfseries}}
\\makeatother

\\setlength{\\parskip}{0pt}  % remove paragraph skips if any
\\setlength{\\parindent}{0pt} % optional, keep indentation
\\newcommand{\\Sec}[1]{\\Needspace{5\\baselineskip}\\section{#1}}

% define variables
\\renewcommand{\\arraystretch}{1.3}
\\renewcommand{\\contentsname}{Contents of Report}
\\renewcommand*{\\cftsecindent}{2.5em}
\\renewcommand*{\\cftsubsecindent}{4.5em}
\\definecolor{ILSgreen}{HTML}{7EBA28}
\\definecolor{TitleGray}{HTML}{999999}
\\newcolumntype{P}[1]{>{\\raggedright\\arraybackslash}p{#1}}
\\newcolumntype{C}[1]{>{\\raggedleft\\arraybackslash}p{#1}}
\\newcommand{\\mainbox}[1]{\\Sec{#1}}
\\newcommand*{\\tabindent}{0px}
\\setcounter{secnumdepth}{0}
\\newcommand{\\grayline}{\\arrayrulecolor{TitleGray}\\hline\\arrayrulecolor{black}}
% \\newenvironment{pageblock}{\\par\\nobreak\\vfil\\penalty0\\vfilneg\\vtop\\bgroup}{\\par\\xdef\\tpd{\\the\\prevdepth}\\egroup\\prevdepth=\\tpd}
%\\newenvironment{pageblock}{\\par\\nobreak\\vfil\\penalty0\\vfilneg\\bgroup}{\\par\\xdef\\tpd{\\the\\prevdepth}\\egroup\\prevdepth=\\tpd}


\\begin{document}
\\begingroup\\fontsize{8pt}{10pt}\\selectfont

\\hfill\\includegraphics[width=50pt]{images/ILS_standalone_logo.pdf}\\\\
\\begin{flushright}\\vskip-15pt{\\tiny Created by \\href{https://lipidomicstandards.org}{https://lipidomicstandards.org}, version """
    tex_preamble += version
    tex_preamble += """}\\end{flushright}
\\vskip-45pt
\\tableofcontents
~\\\\~\\\\

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% General Workflow
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
"""

    tex_suffix = """\\endgroup
\\end{document}
    """


    with open(report_file, "wt", encoding = "utf-8") as tex:
        tex.write("%s\n\n" % tex_preamble)


        def write_data(mainbox, titles, report_fields, main_section = False, lipid_classes = False):

            for i in range(len(titles)): titles[i] = font_encoding(titles[i])
            for section in report_fields:
                for row in section:
                    row[0] = font_encoding(row[0])
                    if row[1][:11] != "!!!TABLE!!!": row[1] = font_encoding(row[1]) if len(row[1]) > 0 else font_encoding("-")

            ii = 0
            for i, mc in enumerate(titles):
                if len(report_fields[i]) == 0: continue

                #tex.write("\\begin{pageblock}\n")
                if i == 0: tex.write("\\mainbox{%s}~\\\\\n" % mainbox)
                tex.write("\\subsection{\\textcolor{TitleGray}{%s}}\n" % mc)
                #tex.write("\\textbf{\\large \\textcolor{TitleGray}{%s}}\n" % mc)
                tex.write("\\vskip-1.2em\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\n")
                tex.write("\\newline{\\vskip-10px\\noindent\\textcolor{gray!20}{\\rule{\\textwidth}{10pt}}}\n")
                tex.write("\\setlength\\tabcolsep{0pt}\\begin{longtable}{@{}P{0.26\\textwidth}P{0.005\\textwidth}P{0.23\\textwidth}P{0.01\\textwidth}@{}P{0.26\\textwidth}P{0.005\\textwidth}P{0.23\\textwidth}}\n")

                if i == 0 and main_section:
                    tex.write("%s & \\multicolumn{6}{@{}P{0.70\\textwidth}}{%s} \\\\\n" % (report_fields[0][0][0], report_fields[0][0][1]))
                    tex.write("\\hline\n")

                    # create time stamp of now
                    date_time = datetime.fromtimestamp(time.time())
                    str_date_time = date_time.strftime("%m/%d/%Y")
                    report_fields[i][0] = ["Document creation date", str_date_time]


                left = True
                n = len(report_fields[i])
                for ci in range(n):
                    # prevent that a table will be put on the right column
                    if left and ci + 1 < n and report_fields[i][ci + 1][1][:11] == "!!!TABLE!!!":
                        report_fields[i][ci], report_fields[i][ci + 1] = report_fields[i][ci + 1], report_fields[i][ci]

                    if report_fields[i][ci][1][:11] == "!!!TABLE!!!":
                        tex.write(make_table(report_fields[i][ci][0], report_fields[i][ci][1]))

                    else:
                        if left:
                            tex.write("%s & & %s" % (report_fields[i][ci][0], report_fields[i][ci][1]))
                            left = False
                            if ci + 1 == n: tex.write(" & & & & \\\\\n")
                        else:
                            tex.write(" & & %s & & %s\\\\\n" % (report_fields[i][ci][0], report_fields[i][ci][1]))
                            if ci + 1 < n: tex.write("\\cline{1-3}\\cline{5-7}\n")
                            left = True

                tex.write("\\end{longtable}\n")
                tex.write("\\vskip-1.3em\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\n")
                #tex.write("\\end{pageblock}\\par~\\\\[20pt]\n\n\n")
                tex.write("\\par~\\\\\n\n\n")

                if lipid_classes and ii % 2 == 1: tex.write("~\\\\[20pt] \n\n\n")
                ii += 1

        write_data("%s Workflow" % workflow_types[workflow_type], titles, report_fields, main_section = True)
        tex.write("~\\\\~\\\\\n")
        write_data("Sample Descriptions", sample_titles, sample_report_fields)
        tex.write("~\\\\~\\\\\n")
        write_data("Lipid Class Descriptions", lipid_classes_titles, lipid_classes_report_fields, lipid_classes = True)

        tex.write("%s\n\n" % tex_suffix)
