import csv
import json
import os

def parse_json_file_checklist(file_path: str):
    with open(file_path, 'r', encoding="UTF8") as json_file:
        data = json.load(json_file)
        return data

    # checklist_page = Page(**checklist_data)
    # return checklist_page

if __name__ == "__main__":
    WORKFLOW_TEMPLATES_DIR = 'workflow-templates'
    CHECKLIST_FILE = 'checklist.json'
    checklist_file_path = os.path.join(WORKFLOW_TEMPLATES_DIR, CHECKLIST_FILE)
    print("Checklist file path: ", checklist_file_path)
    checklist_data = parse_json_file_checklist(checklist_file_path)
    print(checklist_data)
    # Extract all terms into a table format with headers:
    fields = ['location_id', 'term_name', 'term_label', 'term_description', 'term_value', 'term_accession']
    # location_id, term_name, term_label, term_value
    terms_dict = []
    
    # loop with index
    for index, page in enumerate(checklist_data.get('pages')):
        print(f"Processing page {index+1}: {page.get('title')}")
        for content in page.get('content'):
            # print(f"Processing content: {index+1}_{content.get('name')}_type={content.get('type')}")
            if content.get('type') == 'select':
                # print(f"{index+1}_{content.get('name')}_type={content.get('type')}, label={content.get('label')}")
                for item in content.get('choice'):
                    # print(f"{index+1}_{item.get('name')}_type={content.get('type')}, label={item.get('label')}, value={item.get('value')}")
                    choice_entry = {
                        'location_id': f"{index+1}_{item.get('name')}_type={content.get('type')}",
                        'term_name': item.get('name'),
                        'term_label': item.get('label'), 
                        'term_description': (None if item.get('description') is None else item.get('description')),
                        'term_value': item.get('value'),
                        'term_accession': None
                    }
                    terms_dict.append(choice_entry)
            else:
                other_entry = {
                    'location_id': f"{index+1}_{content.get('name')}_type={content.get('type')}",
                    'term_name': content.get('name'),
                    'term_label': content.get('label'),
                    'term_description': (None if content.get('description') is None else content.get('description')),
                    'term_value': content.get('value'),
                    'term_accession': None
                }
                # print(f"{index+1}_{content.get('name')}_type={content.get('type')}, label={content.get('label')}, value={content.get('value')}")
                terms_dict.append(other_entry)
            # terms.append(item.get('term'))
    #     terms.append(item.term)
    # print(terms)
    # Write terms into a csv file
    TERMS_FILE = 'checklist_terms_extracted.csv'
    with open(TERMS_FILE, 'w', newline='', encoding="UTF8") as file:
        writer = csv.DictWriter(file, fieldnames = fields, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(terms_dict)

    # create a new dictionary with the terms extracted from workflow-templates/lipid-class.json
    # and write the terms into a csv file 'checklist_lipid_class_terms_extracted.csv'
    LIPID_CLASS_FILE = 'lipid-class.json'
    lipid_class_file_path = os.path.join(WORKFLOW_TEMPLATES_DIR, LIPID_CLASS_FILE)
    print("Lipid class file path: ", lipid_class_file_path)
    lipid_class_data = parse_json_file_checklist(lipid_class_file_path)
    print(lipid_class_data)

    lipid_class_fields = ['location_id', 'term_name', 'term_label', 'term_description', 'term_value', 'term_accession']
    lipid_class_terms_dict = []
    for index, page in enumerate(lipid_class_data.get('pages')):
        print(f"Processing page {index+1}: {page.get('title')}")
        for content in page.get('content'):
            # print(f"Processing content: {index+1}_{content.get('name')}_type={content.get('type')}")
            if content.get('type') == 'select':
                # print(f"{index+1}_{content.get('name')}_type={content.get('type')}, label={content.get('label')}")
                for item in content.get('choice'):
                    # print(f"{index+1}_{item.get('name')}_type={content.get('type')}, label={item.get('label')}, value={item.get('value')}")
                    choice_entry = {
                        'location_id': f"{index+1}_{item.get('name')}_type={content.get('type')}",
                        'term_name': item.get('name'),
                        'term_label': item.get('label'), 
                        'term_description': (None if item.get('description') is None else item.get('description')),
                        'term_value': item.get('value'),
                        'term_accession': None
                    }
                    lipid_class_terms_dict.append(choice_entry)
            else:
                other_entry = {
                    'location_id': f"{index+1}_{content.get('name')}_type={content.get('type')}",
                    'term_name': content.get('name'),
                    'term_label': content.get('label'),
                    'term_description': (None if content.get('description') is None else content.get('description')),
                    'term_value': content.get('value'),
                    'term_accession': None
                }
                # print(f"{index+1}_{content.get('name')}_type={content.get('type')}, label={content.get('label')}, value={content.get('value')}")
                lipid_class_terms_dict.append(other_entry)
            # terms.append(item.get('term'))

    LIPID_CLASS_TERMS_FILE = 'checklist_lipid_class_terms_extracted.csv'
    with open(LIPID_CLASS_TERMS_FILE, 'w', newline='', encoding="UTF8") as file:
        writer = csv.DictWriter(file, fieldnames = lipid_class_fields, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(lipid_class_terms_dict)

    # create a new dictionary with the terms extracted from workflow-templates/samples.json
    # and write the terms into a csv file 'checklist_samples_terms_extracted.csv'
    SAMPLES_FILE = 'sample.json'
    samples_file_path = os.path.join(WORKFLOW_TEMPLATES_DIR, SAMPLES_FILE)
    print("Samples file path: ", samples_file_path)
    samples_data = parse_json_file_checklist(samples_file_path)
    print(samples_data)

    samples_fields = ['location_id', 'term_name', 'term_label', 'term_description', 'term_value', 'term_accession']
    samples_terms_dict = []

    for index, page in enumerate(samples_data.get('pages')):
        print(f"Processing page {index+1}: {page.get('title')}")
        for content in page.get('content'):
            # print(f"Processing content: {index+1}_{content.get('name')}_type={content.get('type')}")
            if content.get('type') == 'select':
                # print(f"{index+1}_{content.get('name')}_type={content.get('type')}, label={content.get('label')}")
                for item in content.get('choice'):
                    # print(f"{index+1}_{item.get('name')}_type={content.get('type')}, label={item.get('label')}, value={item.get('value')}")
                    choice_entry = {
                        'location_id': f"{index+1}_{item.get('name')}_type={content.get('type')}",
                        'term_name': item.get('name'),
                        'term_label': item.get('label'), 
                        'term_description': (None if item.get('description') is None else item.get('description')),
                        'term_value': item.get('value'),
                        'term_accession': None
                    }
                    samples_terms_dict.append(choice_entry)
            else:
                other_entry = {
                    'location_id': f"{index+1}_{content.get('name')}_type={content.get('type')}",
                    'term_name': content.get('name'),
                    'term_label': content.get('label'),
                    'term_description': (None if content.get('description') is None else content.get('description')),
                    'term_value': content.get('value'),
                    'term_accession': None
                }
                # print(f"{index+1}_{content.get('name')}_type={content.get('type')}, label={content.get('label')}, value={content.get('value')}")
                samples_terms_dict.append(other_entry)
            # terms.append(item.get('term'))

    SAMPLES_TERMS_FILE = 'checklist_samples_terms_extracted.csv'
    with open(SAMPLES_TERMS_FILE, 'w', newline='', encoding="UTF8") as file:
        writer = csv.DictWriter(file, fieldnames = samples_fields, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(samples_terms_dict)
