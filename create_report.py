import json
import sqlite3
from datetime import datetime
import time


def fill_report_fields(mycursor, table_prefix, uid, entry_id, titles, report_fields):
    
    sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
    mycursor.execute(sql, (uid, entry_id))
    result = json.loads(mycursor.fetchone()["fields"])
    
    visible = {}
    conditions = {}
    choice_to_field = {}
    field_map = {}
    
    
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
                    condition_met &= (conditional_field in visible and visible[conditional_field]) and (operator == "=" and field_map[key]["value"] == value) or (operator == "~" and field_map[key]["value"] != value)
                visible[field_name] |= condition_met
    
    
    for page in result["pages"]:
        titles.append(page["title"])
        report_fields.append([])
        
        values = {}
        
        for field in page["content"]:
            if "type" not in field or "name" not in field or "label" not in field: continue
            if field["name"] in visible and not visible[field["name"]]: continue
        
            if field["type"] == "text":
                #print(field["label"], field["value"])
            
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
    
    
        
        for i in range(len(report_fields[-1])):
            key = report_fields[-1][i][0].lower()
            if key in values:
                report_fields[-1][i][1] = ", ".join(values[key])
    

                
def unicoding(t):
    #return "".join([c if ord(c) < 128 else "\\unichar{%s}" % ord(c) for c in t])
    encoded = "".join([c for c in t if ord(c) < 256])
    return encoded.replace("\\", "\\backslash").replace("&", "\&")
    
    

def create_report(mycursor, table_prefix, uid, entry_id, report_file, version):

    ## fill general data
    titles = []
    report_fields = []
    fill_report_fields(mycursor, table_prefix, uid, entry_id, titles, report_fields)



    ## fill sample specific data
    sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = %i;" % (table_prefix, entry_id)
    mycursor.execute(sql)
    sample_entry_ids = [row["sample_form_entry_id"] for row in mycursor.fetchall()]

    sample_report_fields = []
    sample_titles = ["Sample %i" % (i + 1) for i in range(len(sample_entry_ids))]
    for i, sample_entry_id in enumerate(sample_entry_ids):
        tmp_titles = []
        tmp_report_fields = []
        fill_report_fields(mycursor, table_prefix, uid, sample_entry_id, tmp_titles, tmp_report_fields)
        
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
        
        
        fill_report_fields(mycursor, table_prefix, uid, class_entry_id, tmp_titles, tmp_report_fields)
        for t in tmp_titles: lipid_classes_titles.append("Lipid class %i - %s" % (i + 1, t))
        lipid_classes_report_fields += tmp_report_fields
    


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
\\newcolumntype{P}[1]{>{\\raggedright\\arraybackslash}p{#1}}
\\newcommand{\\mainbox}[1]{\\colorbox{ILSgreen}{\\textsf{\\textbf{\\color{white}\\LARGE \\adjustbox{margin=3px}{#1}}}}
\\vskip-2.6pt
\\par\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\\vskip+1em}
\\setlength{\\parindent}{0px}
\\renewcommand{\\familydefault}{\\sfdefault}
\\newcommand*{\\tabindent}{0px}
\\newcommand{\\grayline}{\\arrayrulecolor{gray}\\hline\\arrayrulecolor{black}}
\\newenvironment{pageblock}{\\par\\nobreak\\vfil\\penalty0\\vfilneg\\vtop\\bgroup}{\\par\\xdef\\tpd{\\the\\prevdepth}\\egroup\\prevdepth=\\tpd}


\\begin{document}
\\begingroup\\fontsize{8pt}{10pt}\\selectfont

\\hfill\\includegraphics[width=50pt]{ILS_standalone_logo.pdf}\\\\
\\begin{flushright}\\vskip-15pt{\\tiny Created by \\href{https://lipidomicstandards.org}{https://lipidomicstandards.org}, version """ 
    tex_preamble += version
    tex_preamble += """}\\end{flushright}
\\vskip-45pt

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
                    row[1] = unicoding(row[1])
            
            ii = 0
            for i, mc in enumerate(titles):
                if len(report_fields[i]) == 0: continue
            
                
                tex.write("\\begin{pageblock}\n")
                if i == 0: tex.write("\\mainbox{%s}~\\\\\n" % mainbox)
                tex.write("\\textbf{\\large %s}\n" % mc)
                tex.write("\\newline\\vskip-1.6em\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\n")
                tex.write("\\newline{\\vskip-1.2em\\noindent\\textcolor{gray!20}{\\rule{\\textwidth}{10pt}}}\n")
                tex.write("\\begin{tabular}{@{}P{0.31\\textwidth}P{0.15\\textwidth}P{0.002\\textwidth}@{}P{0.31\\textwidth}P{0.142\\textwidth}}\n")
                
                
                if i == 0 and main_section:
                    tex.write("%s & \\multicolumn{4}{@{}P{0.64\\textwidth}}{%s} \\\\\n" % (report_fields[0][0][0], report_fields[0][0][1]))
                    tex.write("\\hline\n")
                    
                    # create time stamp of now
                    date_time = datetime.fromtimestamp(time.time())
                    str_date_time = date_time.strftime("%m/%d/%Y")
                    report_fields[i][0] = ["Document creation date", str_date_time]
                    
                n = len(report_fields[i])
                h = (n + 1) // 2
                for ci in range(h):
                    if ci + h < n:
                        tex.write("%s & %s & & %s & %s \\\\\n" % (report_fields[i][ci][0], report_fields[i][ci][1], report_fields[i][ci + h][0], report_fields[i][ci + h][1]))
                    else:
                        tex.write("%s & %s \\\\\n" % (report_fields[i][ci][0], report_fields[i][ci][1]))
                        
                    if ci < h - 1:
                        tex.write("\\cline{1-2}\\cline{4-5}\n")
                        
                    
                
                tex.write("\\end{tabular}\n")
                tex.write("\\newline\\vskip-1.3em\\noindent\\textcolor{ILSgreen}{\\rule{\\textwidth}{1.5pt}}\n")
                tex.write("\\end{pageblock}\\par~\\\\\n\n\n")
                
                if lipid_classes and ii % 2 == 1: tex.write("~\\\\\n\n\n")
                ii += 1
                
        write_data("General Lipidomics Workflow", titles, report_fields, main_section = True)
        tex.write("~\\\\~\\\\\n")
        write_data("Sample Descriptions", sample_titles, sample_report_fields)
        tex.write("~\\\\~\\\\\n")
        write_data("Lipid Class Descriptions", lipid_classes_titles, lipid_classes_report_fields, lipid_classes = True)
        
        tex.write("%s\n\n" % tex_suffix)
