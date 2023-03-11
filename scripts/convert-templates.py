import json


def convert_condition(conditionals, field_types, trans):
    converted = []
    if type(conditionals) == dict:
        conditionals = [conditionals[i] for i in sorted(conditionals.keys())]
    
    for conditional_and in conditionals:
        converted_and = []
        for conditional in conditional_and:
            key, value = "", ""
            if field_types[conditional["field"]] in {"select", "checkbox"}:
                key = trans["%s-%s" % (conditional["field"], conditional["value"])]
                value = "1"
            else:
                key = trans[conditional["field"]]
                value = "'%s'" % conditional["value"]
                
            operator = "=" if conditional["operator"] == "==" else "~"
            converted_and.append("%s%s%s" % (key, operator, value))
        converted.append("&".join(converted_and))
        
    return "|".join(converted)

form_type = "checklist" 

if form_type == "checklist":
    from checklist_field_names import checklist_field_names as trans
    input_file = "wpforms245.json"
    output_file = "../workflow-templates/checklist.json"
    output_name_file = "../workflow-templates/checklist-field-names.csv"
    
elif form_type == "sample":
    from sample_field_names import sample_field_names as trans
    input_file = "wpforms240.json"
    output_file = "../workflow-templates/sample.json"
    output_name_file = "../workflow-templates/sample-field-names.csv"

elif form_type == "lipid-class":
    from lipid_class_field_names import lipid_class_field_names as trans
    input_file = "wpforms199.json"
    output_file = "../workflow-templates/lipid-class.json"
    output_name_file = "../workflow-templates/lipid-class-field-names.csv"

else:
    exit()



input_string = open(input_file, "rt").read()
input_data = json.loads(input_string)
output_data = []
current_page = None
field_types = {field_name: field["type"] for field_name, field in input_data["fields"].items()}

field_names = []

for field_name, field in input_data["fields"].items():
    
    field_type = field["type"]
    
    #field_label = field["label"] if "label" in field else "-"
    #field_names.append("%s,%s,%s,%s" % ("_".join(field_label.lower().split(" ")), field["id"], field_label, field["type"]))
    
    if field_type == "pagebreak" and "title" in field:
        page_name = field["title"]
        current_page = []
        output_data.append({"title": page_name, "content": current_page})
        
        
        
    elif field_type in {"text", "email"}:
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        
        new_field = {"label": field["label"],
                     "name": trans[field["id"]],
                     "type": "text",
                     "required": 1 if "required" in field and field["required"] == "1" else 0,
                     "value": field["default_value"] if field["default_value"] != False else "",
                     "description": field["description"]}
        
        if "conditionals" in field: new_field["condition"] = convert_condition(field["conditionals"], field_types, trans)
        current_page.append(new_field)
        
    
    elif field_type == "html":
        current_page.append({"name": trans[field["id"]], "type": "table", "value": 0, "required": 1, "view": "sample" if field["id"] == "148" else "lipid-class"})
        
    
    
    elif field_type in {"select", "checkbox"}:
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        choice = []
        new_field = {"label": field["label"],
                     "name": trans[field["id"]],
                     "type": "select" if field_type == "select" else "multiple",
                     "required": 1 if field_type == "checkbox" and "required" in field and field["required"] == "1" else 0,
                     "choice": choice,
                     "description": field["description"]}
        
        something_selected = False
        for choice_key, single_choice in field["choices"].items():
            #key = "%s-%s" % (field["id"], choice_key)
            #common_name = "%s|%s" % ("_".join(field["label"].lower().split(" ")), "_".join(single_choice["label"].lower().split(" ")))
            #field_names.append("%s,%s,%s,%s" % (common_name, key, single_choice["label"], field["type"]))
            
            choice_map = {"name": trans["%s-%s" % (field["id"], choice_key)],
                          "label": single_choice["label"],
                          "value": 1 if ("default" in single_choice and single_choice["default"] == "1") or ("value" in single_choice and single_choice["value"] == "1") else 0
                          }
            something_selected |= choice_map["value"]
            choice.append(choice_map)
            
        if field_type == "select" and len(choice) > 0 and not something_selected:
            choice[0]["value"] = 1
    
        if "conditionals" in field: new_field["condition"] = convert_condition(field["conditionals"], field_types, trans)
        current_page.append(new_field)
        
        
    
    elif field_type == "number":
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        new_field = {"label": field["label"],
                     "name": trans[field["id"]],
                     "type": "number",
                     "required": 1 if field["required"] == "1" else 0,
                     "value": 0,
                     "description": field["description"]}
        
        if "bfwpf_minnumber" in field and field["bfwpf_minnumber"] != "": new_field["min"] = float(field["bfwpf_minnumber"])
        if "bfwpf_maxnumber" in field and field["bfwpf_maxnumber"] != "": new_field["max"] = float(field["bfwpf_maxnumber"])
        
        if "conditionals" in field: new_field["condition"] = convert_condition(field["conditionals"], field_types, trans)
        current_page.append(new_field)
        
    
    
    
    elif field_type == "hidden":
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        new_field = {"name": trans[field["id"]],
                     "type": "hidden",
                     "value": field["default_value"] if field["default_value"] != False else ""}
        current_page.append(new_field)
        
    
output_data = {"pages": output_data, "current_page": 0, "creation_date": "", "version": ""}
    
with open(output_file, "wt") as out:
    out.write(json.dumps(output_data))

exit()

with open(output_name_file, "wt") as out:
    for field_name in field_names:
        out.write("%s\n" % field_name)
