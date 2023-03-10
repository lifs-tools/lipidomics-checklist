import json
import sqlite3
from datetime import datetime
import time


def fill_report_fields(mycursor, table_prefix, uid, entry_id, titles, report_fields):
    
    sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
    mycursor.execute(sql, (uid, entry_id))
    result = json.loads(mycursor.fetchone()["fields"])
    
    for page in result["pages"]:
        titles.append(page["title"])
        report_fields.append([])
        
        values = {}
        
        for field in page["content"]:
            if "type" not in field or "name" not in field or "label" not in field: continue
        
            if field["type"] == "text":
                if field["label"][:5].lower() == "other":
                    if field["label"][6:] in values:
                        values[field["label"][6:]] = field["value"]
                else:
                    values[field["label"]] = field["value"]
                    report_fields[-1].append([field["label"], ""])
                
            elif field["type"] == "number":
                values[field["label"]] = str(field["value"])
                report_fields[-1].append([field["label"], ""])
                
            elif field["type"] in {"select", "multiple"}:
                choice_values = []
                for choice in field["choice"]:
                    if choice["value"] == 1:
                        choice_values.append(choice["label"])
                
                values[field["label"]] = "\n".join(choice_values)
                report_fields[-1].append([field["label"], ""])
    
        for i in range(len(report_fields[-1])):
            key = report_fields[-1][i][0]
            if key in values: report_fields[-1][i][1] = values[key]
                    
    return
    
    sql = "SELECT p.post_content AS form FROM %sposts AS p INNER JOIN %swpforms_entries AS e ON p.id = e.form_id WHERE e.user_id = %i and e.entry_id = %i;" % (table_prefix, table_prefix, uid, entry_id)
    mycursor.execute(sql)
    form_content = json.loads(mycursor.fetchone()["form"])["fields"]
    
    
    sql = "SELECT fields FROM %swpforms_entries WHERE user_id = %i and entry_id = %i;" % (table_prefix, uid, entry_id)
    mycursor.execute(sql)
    db_fields = json.loads(mycursor.fetchone()["fields"])
    field_values = {k: set(row["value"].split("\n")) for k, row in db_fields.items()}
    
    
    field_ids = {}
    conditions = {}
    possible_values = {}

    
    for i, (k, v) in enumerate(form_content.items()):
        if "title" in v:
            titles.append(v["title"])
            report_fields.append([])

        elif "label" in v:
            if len(report_fields) == 0:
                report_fields.append([])
                
            if "type" in v and v["type"] != "hidden":
                report_fields[-1].append(v["label"])
            
            field_ids[v["label"]] = k
            
            if "conditional_logic" in v and v["conditional_logic"] == '1':
                conditions[k] = v["conditionals"]
                if type(conditions[k]) == dict:
                    conditions[k] = [vv for kk, vv in conditions[k].items()]
            
            if "type" in v and v["type"] in {"checkbox", "select"}:
                possible_values[k] = {}
                for ci, cv in v["choices"].items():
                    possible_values[k][ci] = cv["label"]
                    
    
    # 'other' substitution
    for field_name, field_id in field_ids.items():
        if field_name[:5].lower() == "other" and field_id in conditions and field_id in field_values:
            other_value = field_values[field_id]
            ref_id = conditions[field_id][0][0]["field"]
            if ref_id not in field_values: continue
        
            cnt = sum([f[:5].lower() == "other" for f in field_values[ref_id]])
            if len(other_value) == 1 and cnt == 1:
                other_value = "".join(other_value)
                field_values[ref_id] = {f if f[:5].lower() != "other" else other_value for f in field_values[ref_id]}
                
    # checking for conditionals
    for report_section in report_fields:
        new_section = []
        for report_field in report_section:
            if report_field[:5].lower() == "other" or report_field not in field_ids: continue
        
            field_id = field_ids[report_field]
            field_value = field_values[field_id] if field_id in field_values else {""}
            
            
            if field_id not in conditions:
                new_section.append([report_field, ", ".join(sorted(list(field_value)))])
                
            else:
                condition_satisfied = False
                for or_cond in conditions[field_id]:
                    if condition_satisfied: break
                
                    c = True
                    for and_cond in or_cond:
                        cfield_id = and_cond["field"]
                        if cfield_id not in field_values:
                            c = False
                            break
                        
                        value_id = and_cond["value"]
                        c_op = and_cond["operator"]
                        
                        if not str.isnumeric(value_id):
                            c_value = value_id
                        else:
                            if cfield_id not in possible_values:
                                c = False
                                break
                            elif value_id not in possible_values[cfield_id]:
                                c = False
                                break
                            else:
                                c_value = possible_values[cfield_id][value_id]
                        
                        cfield_value = field_values[cfield_id]
                        if c_op == "==" and c_value not in cfield_value:
                            c = False
                            break
                        elif c_op == "!=" and c_value in cfield_value:
                            c = False
                            break
                    condition_satisfied |= c
                    
                if condition_satisfied:
                    new_section.append([report_field, ", ".join(field_value)])
                
        new_section = [n for n in new_section if len(n[1]) > 0]
        report_section.clear()
        report_section += new_section



                
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
                    tex.write("%s & \\multicolumn{4}{l}{%s} \\\\\n" % (report_fields[0][0][0], report_fields[0][0][1]))
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
