import json

template_file = "../workflow-templates/checklist.json"
instance_file = "torta.json"

template_data = json.loads(open(template_file, "rt").read())
instance_data = json.loads(open(instance_file, "rt").read())

field_data = {}
for page in template_data:
    for field in page["content"]:
        field_data[field["name"]] = field
        
        

for name, field in instance_data.items():
    values = field["value"]
    if len(values) == 0: continue
    
    if name in field_data:
        template_field = field_data[name]
        if template_field["type"] in {"select", "multiple"}:
            values = set(values.split("\n"))
            for choice in template_field["choice"]:
                choice["value"] = 1 if choice["label"] in values else 0
                    

        else:
            template_field["value"] = values
            
print(template_data)
