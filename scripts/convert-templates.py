import json


def convert_condition(conditionals, field_types):
    converted = []
    if type(conditionals) == dict:
        conditionals = [conditionals[i] for i in sorted(conditionals.keys())]
        
    for conditional_and in conditionals:
        converted_and = []
        for conditional in conditional_and:
            key, value = "", ""
            if field_types[conditional["field"]] in {"select", "checkbox"}:
                key = "%s-%s" % (conditional["field"], conditional["value"])
                value = "1"
            else:
                key = conditional["field"]
                value = "'%s'" % conditional["value"]
                
            operator = "=" if conditional["operator"] == "==" else "!="
            converted_and.append("%s%s%s" % (key, operator, value))
        converted.append("&".join(converted_and))
        
    return "|".join(converted)


input_file, output_file = "wpforms245.json", "../workflow-templates/checklist.json"
#input_file, output_file = "wpforms240.json", "../workflow-templates/sample.json"
#input_file, output_file = "wpforms199.json", "../workflow-templates/lipid-class.json"


input_string = open(input_file, "rt").read()
input_data = json.loads(input_string)
output_data = []
current_page = None
field_types = {field_name: field["type"] for field_name, field in input_data["fields"].items()}
for field_name, field in input_data["fields"].items():
    
    field_type = field["type"]
    
    if field_type == "pagebreak" and "title" in field:
        page_name = field["title"]
        current_page = []
        output_data.append({"title": page_name, "content": current_page})
        
        
        
    elif field_type in {"text", "email"}:
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        
        new_field = {"label": field["label"],
                     "name": field["id"],
                     "type": "text",
                     "required": 1 if "required" in field and field["required"] == "1" else 0,
                     "value": field["default_value"] if field["default_value"] != False else "",
                     "description": field["description"]}
        
        if "conditionals" in field: new_field["condition"] = convert_condition(field["conditionals"], field_types)
        current_page.append(new_field)
        
    
    
    
    elif field_type in {"select", "checkbox"}:
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        choice = []
        new_field = {"label": field["label"],
                     "name": field["id"],
                     "type": "select" if field_type == "select" else "multiple",
                     "required": 1 if field_type == "checkbox" and "required" in field and field["required"] == "1" else 0,
                     "choice": choice,
                     "description": field["description"]}
        
        for choice_key, single_choice in field["choices"].items():
            choice_map = {"name": "%s-%s" % (field["id"], choice_key),
                          "label": single_choice["label"],
                          "value": 1 if ("default" in single_choice and single_choice["default"] == "1") or ("value" in single_choice and single_choice["value"] == "1") else 0
                          }
            choice.append(choice_map)
    
        if "conditionals" in field: new_field["condition"] = convert_condition(field["conditionals"], field_types)
        current_page.append(new_field)
        
        
    
    elif field_type == "number":
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        new_field = {"label": field["label"],
                     "name": field["id"],
                     "type": "number",
                     "required": 1 if field["required"] == "1" else 0,
                     "value": 0,
                     "description": field["description"]}
        
        if "bfwpf_minnumber" in field and field["bfwpf_minnumber"] != "": new_field["min"] = float(field["bfwpf_minnumber"])
        if "bfwpf_maxnumber" in field and field["bfwpf_maxnumber"] != "": new_field["max"] = float(field["bfwpf_maxnumber"])
        
        if "conditionals" in field: new_field["condition"] = convert_condition(field["conditionals"], field_types)
        current_page.append(new_field)
        
    
    
    
    elif field_type == "hidden":
        if current_page == None:
            current_page = []
            output_data.append({"title": "-", "content": current_page})
            
        new_field = {"name": field["id"],
                     "type": "hidden",
                     "value": field["default_value"] if field["default_value"] != False else ""}
        current_page.append(new_field)
        
    
with open(output_file, "wt") as out:
    out.write(json.dumps(output_data))


