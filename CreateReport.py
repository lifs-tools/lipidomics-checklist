import json
import sqlite3
from datetime import datetime
import time
from urllib.parse import unquote


workflow_types = {"gen": "General Lipidomics", "di": "Direct Infusion", "sep": "Separation", "img": "Imaging"}



def get_workflow_type(mycursor, table_prefix, uid, entry_id):
    
    sql = "SELECT form, fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
    mycursor.execute(sql, (uid, entry_id))
    result = json.loads(mycursor.fetchone()["fields"])
    for field in result["pages"][0]["content"]:
        if field["name"] == "workflowtype":
            workflow_type = field["value"] if field["value"] in workflow_types else "gen"
    return workflow_type




def fill_report_fields(mycursor, table_prefix, uid, entry_id, titles, report_fields, version):
    
    sql = "SELECT form, fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
    mycursor.execute(sql, (uid, entry_id))
    result = json.loads(mycursor.fetchone()["fields"])
    workflow_type = "gen"
    
    visible = {}
    conditions = {}
    choice_to_field = {}
    field_map = {}
    
    version.append(result["version"] if "version" in result else "v0.9.9")
    
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
                            continue;
                    conjunction.append([key, operator, value])
                    
                condition.append(conjunction)
            conditions[field_name] = condition
    
    
    
    for page in result["pages"]:
        for field in page["content"]:
            if "condition" not in field or len(field["condition"]) == 0: continue
            field_name = field["name"]
            visible[field_name] = False
            for condition_and in conditions[field_name]:
                condition_met = True
                for single_condition in condition_and:
                    key, operator, value = single_condition
                    conditional_field = choice_to_field[key]
                    condition_met &= (conditional_field in visible and visible[conditional_field]) and ((operator == "=" and field_map[key]["value"] == value) or (operator == "~" and field_map[key]["value"] != value))
                visible[field_name] |= condition_met
    
    
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
                report_fields[-1].append([field["label"], ""])
                
            elif field["type"] == "table":
                values[field["label"].lower()] = ["!!!TABLE!!!%s!!!CONTENT!!!%s" % (field["columns"], field["value"])]
                #values[field["label"].lower()] = [field["value"]]
                report_fields[-1].append([field["label"], ""])
    
    
        
        for i in range(len(report_fields[-1])):
            key = report_fields[-1][i][0].lower()
            if key in values:
                report_fields[-1][i][1] = ", ".join(values[key])
    

                
def unicoding(t):
    #t = t.replace("\\", "\\backslash").replace("&", "\&").replace("%", "").replace("$", "")
    encoded = "".join(["{\ }" if ord(c) == 32 else "\\char\"%s" % hex(ord(c))[2:].upper() for c in t])
    #encoded = "".join([c for c in t if ord(c) < 256])
    #return encoded.replace("\\", "\\backslash").replace("&", "\&").replace("%", "\%")
    return encoded
    
    
    
def make_table(title, text):
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
            
        result_text.append(unicoding(unquote(cell)))
        
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
        if type(titles[i] == dict):
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
            lipid_class, polarity, adduct_pos, adduct_neg = "", "negative", "", ""
            for tmp_rep_field in tmp_report_field:
                if tmp_rep_field[0] == "Lipid class": lipid_class = tmp_rep_field[1]
                elif tmp_rep_field[0] == "Polarity mode": polarity = tmp_rep_field[1].lower()
                elif tmp_rep_field[0] == "Type of positive (precursor)ion": adduct_pos = tmp_rep_field[1]
                elif tmp_rep_field[0] == "Type of negative (precursor)ion": adduct_neg = tmp_rep_field[1]
            
            if len(lipid_class) > 0 and (len(adduct_pos) > 0 or len(adduct_neg) > 0):
                lipid_class_prefix = "%s%s" % (lipid_class, adduct_pos if polarity == "positive" else adduct_neg)
            
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
\\usepackage{textcomp}
\\usepackage[hidelinks]{hyperref}
%%\\usepackage{tgheros}

% define variables
\\renewcommand{\\arraystretch}{1.3}
\\renewcommand{\\contentsname}{Contents of Report}
\\renewcommand*{\\cftsecindent}{2.5em}
\\renewcommand*{\\cftsubsecindent}{4.5em}
\\definecolor{ILSgreen}{HTML}{7EBA28}
\\definecolor{TitleGray}{HTML}{999999}
\\newcolumntype{P}[1]{>{\\raggedright\\arraybackslash}p{#1}}
\\newcolumntype{C}[1]{>{\\raggedleft\\arraybackslash}p{#1}}
\\newcommand{\\mainbox}[1]{\\section{#1}}
%%\\colorbox{ILSgreen}{\\section{#1}}}
%%\\textsf{\\textbf{\\color{white}\\LARGE \\adjustbox{margin=3px}{#1}}}}
%%\\vskip-2.6pt
%%\\par\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\\vskip+1em}
\\setlength{\\parindent}{0px}
\\renewcommand{\\familydefault}{\\sfdefault}
\\newcommand*{\\tabindent}{0px}
\\setcounter{secnumdepth}{0}
\\newcommand{\\grayline}{\\arrayrulecolor{TitleGray}\\hline\\arrayrulecolor{black}}
\\newenvironment{pageblock}{\\par\\nobreak\\vfil\\penalty0\\vfilneg\\vtop\\bgroup}{\\par\\xdef\\tpd{\\the\\prevdepth}\\egroup\\prevdepth=\\tpd}


\\begin{document}
\\begingroup\\fontsize{8pt}{10pt}\\selectfont

\\hfill\\includegraphics[width=50pt]{images/ILS_standalone_logo.pdf}\\\\
\\begin{flushright}\\vskip-15pt{\\tiny Created by \\href{https://lipidomicstandards.org}{https://lipidomicstandards.org}, version """ 
    tex_preamble += version
    tex_preamble += """}\\end{flushright}
\\vskip-45pt
\\tableofcontents

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
            
            for i in range(len(titles)): titles[i] = unicoding(titles[i])
            for section in report_fields:
                for row in section:
                    row[0] = unicoding(row[0])
                    if row[1][:11] != "!!!TABLE!!!": row[1] = unicoding(row[1]) if len(row[1]) > 0 else unicoding("-")
            
            ii = 0
            for i, mc in enumerate(titles):
                if len(report_fields[i]) == 0: continue
            
                
                tex.write("\\begin{pageblock}\n")
                if i == 0: tex.write("\\mainbox{%s}~\\\\\n" % mainbox)
                tex.write("\\subsection{\\textcolor{TitleGray}{%s}}\n" % mc)
                #tex.write("\\textbf{\\large \\textcolor{TitleGray}{%s}}\n" % mc)
                tex.write("\\vskip-1.2em\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\n")
                tex.write("\\newline{\\vskip-10px\\noindent\\textcolor{gray!20}{\\rule{\\textwidth}{10pt}}}\n")
                tex.write("\\setlength\\tabcolsep{0pt}\\begin{tabular}{@{}P{0.26\\textwidth}P{0.005\\textwidth}P{0.23\\textwidth}P{0.01\\textwidth}@{}P{0.26\\textwidth}P{0.005\\textwidth}P{0.23\\textwidth}}\n")
                
                
                if i == 0 and main_section:
                    tex.write("%s & \\multicolumn{6}{@{}P{0.70\\textwidth}}{%s} \\\\\n" % (report_fields[0][0][0], report_fields[0][0][1]))
                    tex.write("\\hline\n")
                    
                    # create time stamp of now
                    date_time = datetime.fromtimestamp(time.time())
                    str_date_time = date_time.strftime("%m/%d/%Y")
                    report_fields[i][0] = ["Document creation date", str_date_time]
                    
                n = len(report_fields[i])
                h = (n + 1) // 2
                for ci in range(h):
                    
                    if ci + h < n:
                        
                        if report_fields[i][ci][1][:11] == "!!!TABLE!!!":
                            first_col = make_table(report_fields[i][ci][0], report_fields[i][ci][1])
                        else:
                            first_col = "%s & & %s" % (report_fields[i][ci][0], report_fields[i][ci][1])
                            
                        if report_fields[i][ci + h][1][:11] == "!!!TABLE!!!":
                            second_col = make_table(report_fields[i][ci + h][0], report_fields[i][ci + h][1])
                        else:
                            second_col = "%s & & %s" % (report_fields[i][ci + h][0], report_fields[i][ci + h][1])
                        
                        tex.write("%s & & %s \\\\\n" % (first_col, second_col))
                    else:
                        if report_fields[i][ci][1][:11] == "!!!TABLE!!!":
                            first_col = make_table(report_fields[i][ci][0], report_fields[i][ci][1])
                        else:
                            first_col = "%s & & %s" % (report_fields[i][ci][0], report_fields[i][ci][1])
                            
                        tex.write("%s \\\\\n" % (first_col))
                        
                    if ci < h - 1:
                        tex.write("\\cline{1-3}\\cline{5-7}\n")
                        
                    
                
                tex.write("\\end{tabular}\n")
                tex.write("\\newline\\vskip-1.3em\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\n")
                tex.write("\\end{pageblock}\\par~\\\\\n\n\n")
                
                if lipid_classes and ii % 2 == 1: tex.write("~\\\\\n\n\n")
                ii += 1
                
        write_data("%s Workflow" % workflow_types[workflow_type], titles, report_fields, main_section = True)
        tex.write("~\\\\~\\\\\n")
        write_data("Sample Descriptions", sample_titles, sample_report_fields)
        tex.write("~\\\\~\\\\\n")
        write_data("Lipid Class Descriptions", lipid_classes_titles, lipid_classes_report_fields, lipid_classes = True)
        
        tex.write("%s\n\n" % tex_suffix)
