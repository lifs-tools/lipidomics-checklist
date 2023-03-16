import json
import mysql.connector
from mysql.connector import Error
import sqlite3
from checklist_field_names import checklist_field_names as cfn
from sample_field_names import sample_field_names as sfn
from lipid_class_field_names import lipid_class_field_names as lcfn
import hashlib
from datetime import datetime



def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


conn_sqlite = sqlite3.connect("../db/checklist.sqlite")
conn_sqlite.row_factory = dict_factory
cursor_sqlite = conn_sqlite.cursor()
database = 'd03847d2'
user = 'd03847d2'
password = 'VD92x6sGzS3tHmdnAhCR'
host = 'lipidomics-regensburg.de'
table_prefix = "TCrpQ_"

main_form_id = "checklist"
class_form_id = "lipid-class"
sample_form_id = "sample"


conn_mysql = mysql.connector.connect(host = host, database = database, user = user, password = password)
if not conn_mysql.is_connected():
    print(ErrorCodes.NO_DB_CONNECTION)
    exit()
cursor_mysql = conn_mysql.cursor(dictionary = True)


checklist_template_file = "../workflow-templates/checklist.json"
sample_template_file = "../workflow-templates/sample.json"
lipid_class_template_file = "../workflow-templates/lipid-class.json"



entry_id_map = {}


sql_prep = "select entry_id from TCrpQ_wpforms_entries where form_id IN (199, 240, 245) and status = 'partial' and status <> 'abandoned'"
cursor_mysql.execute("%s;" % sql_prep)
len_entry_ids = len([row["entry_id"] for row in cursor_mysql.fetchall()])

min_limit, num = 1, 1
total = 0
while min_limit < len_entry_ids:
    sql = "select entry_id, user_id, form_id, fields, date, status, user_uuid from TCrpQ_wpforms_entries where entry_id in (%s) limit %i, 100;" % (sql_prep, min_limit)
    cursor_mysql.execute(sql)
    results = cursor_mysql.fetchall()
    
    for result in results:

        form_type = {245: "checklist", 240: "sample", 199: "lipid-class"}[result["form_id"]]
        uid = result["user_id"]
        entry_id = result["entry_id"]
        print("entry: %i, %s, %i of %i / %i" % (entry_id, form_type, num, len_entry_ids, min_limit))
        num += 1
        
        if result["fields"] == None or len(result["fields"]) == 0: continue
        
        if form_type == "checklist":
            trans, template_data, form_id = cfn, json.loads(open(checklist_template_file, "rt").read()), main_form_id
            
        elif form_type == "sample":
            trans, template_data, form_id = sfn, json.loads(open(sample_template_file, "rt").read()), sample_form_id
            
        elif form_type == "lipid-class":
            trans, template_data, form_id = lcfn, json.loads(open(lipid_class_template_file, "rt").read()), class_form_id

        instance_data = json.loads(result["fields"])

        field_data = {}
        for page in template_data["pages"]:
            for field in page["content"]:
                field_data[field["name"]] = field
                
        template_data["version"] = "v1.0.0"
        template_data["current_page"] = 0
        template_data["creation_date"] = str(result["date"])
        status = result["status"]
        
        if entry_id == 3190: print(entry_id, status, form_type)
        
        if status == "": status = "completed"
        elif status == "abandoned": status = "completed"
        elif status not in {"partial", "permanent"}:
            print("status error for entry_id %i" % entry_id)
            continue

        
        for name, field in instance_data.items():
            if "value" not in field: continue
            
            values = field["value"]
            if len(values) == 0: continue
            
            if name in trans and trans[name] in field_data:
                template_field = field_data[trans[name]]
                if template_field["type"] in {"select", "multiple"}:
                    values = set(values.split("\n"))
                    for choice in template_field["choice"]:
                        choice["value"] = 1 if choice["label"] in values else 0
                            

                else:
                    template_field["value"] = values
                    

        sql = "insert into %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, ?, ?);" % table_prefix
        cursor_sqlite.execute(sql, (form_id, uid, status, json.dumps(template_data), result["date"], result["user_uuid"]))
        conn_sqlite.commit()
        if entry_id == 3190: print(sql)
        
        sql = "select max(id) as new_id from %sentries where user_id = ? and form = ?" % table_prefix
        cursor_sqlite.execute(sql, (uid, form_id))
        new_entry_id = cursor_sqlite.fetchone()["new_id"]

        if form_type == "checklist":
            hash_value = "%i-%i-%s" % (new_entry_id, uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            hash_value = hashlib.md5(hash_value.encode()).hexdigest()
            
            sql = "INSERT INTO %sreports (entry_id, hash) VALUES (?, ?);" % table_prefix
            cursor_sqlite.execute(sql, (new_entry_id, hash_value))
            conn_sqlite.commit()
            
        entry_id_map[entry_id] = new_entry_id
    min_limit += 100






sql_prep = "select DISTINCT f.entry_id from TCrpQ_wpforms_entry_fields AS f INNER JOIN TCrpQ_wpforms_entries AS e ON f.entry_id = e.entry_id where f.form_id IN (199, 240, 245) and e.status <> 'abandoned'"
cursor_mysql.execute("%s;" % sql_prep)
len_entry_ids = len([row["entry_id"] for row in cursor_mysql.fetchall()])

min_limit, num = 1, 1
while min_limit < len_entry_ids:
    sql = "select entry_id, user_id, form_id, fields, date, status, user_uuid from TCrpQ_wpforms_entries where entry_id in (%s) limit %i, 100;" % (sql_prep, min_limit)
    cursor_mysql.execute(sql)
    results = cursor_mysql.fetchall()
    
    for result in results:

        form_type = {245: "checklist", 240: "sample", 199: "lipid-class"}[result["form_id"]]
        uid = result["user_id"]
        entry_id = result["entry_id"]
        print("entry: %i, %s, %i of %i / %i" % (entry_id, form_type, num, len_entry_ids, min_limit))
        num += 1
        
        if result["fields"] == None or len(result["fields"]) == 0: continue
        
        if form_type == "checklist":
            trans, template_data, form_id = cfn, json.loads(open(checklist_template_file, "rt").read()), main_form_id
            
        elif form_type == "sample":
            trans, template_data, form_id = sfn, json.loads(open(sample_template_file, "rt").read()), sample_form_id
            
        elif form_type == "lipid-class":
            trans, template_data, form_id = lcfn, json.loads(open(lipid_class_template_file, "rt").read()), class_form_id

        instance_data = json.loads(result["fields"])

        field_data = {}
        for page in template_data["pages"]:
            for field in page["content"]:
                field_data[field["name"]] = field
                
        template_data["version"] = "v1.0.0"
        template_data["current_page"] = 0
        template_data["creation_date"] = str(result["date"])
        status = result["status"]
        
        if entry_id == 3190: print(entry_id, status, form_type)
        
        if status == "": status = "completed"
        elif status == "abandoned": status = "completed"
        elif status not in {"partial", "permanent"}:
            print("status error for entry_id %i" % entry_id)
            continue

        
        for name, field in instance_data.items():
            if "value" not in field: continue
            
            values = field["value"]
            if len(values) == 0: continue
            
            if name in trans and trans[name] in field_data:
                template_field = field_data[trans[name]]
                if template_field["type"] in {"select", "multiple"}:
                    values = set(values.split("\n"))
                    for choice in template_field["choice"]:
                        choice["value"] = 1 if choice["label"] in values else 0
                            

                else:
                    template_field["value"] = values
                    

        sql = "insert into %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, ?, ?);" % table_prefix
        cursor_sqlite.execute(sql, (form_id, uid, status, json.dumps(template_data), result["date"], result["user_uuid"]))
        conn_sqlite.commit()
        if entry_id == 3190: print(sql)
        
        sql = "select max(id) as new_id from %sentries where user_id = ? and form = ?" % table_prefix
        cursor_sqlite.execute(sql, (uid, form_id))
        new_entry_id = cursor_sqlite.fetchone()["new_id"]

        if form_type == "checklist":
            hash_value = "%i-%i-%s" % (new_entry_id, uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            hash_value = hashlib.md5(hash_value.encode()).hexdigest()
            
            sql = "INSERT INTO %sreports (entry_id, hash) VALUES (?, ?);" % table_prefix
            cursor_sqlite.execute(sql, (new_entry_id, hash_value))
            conn_sqlite.commit()
            
        entry_id_map[entry_id] = new_entry_id
    min_limit += 100








sql = "select * from TCrpQ_wpforms_connect;"
cursor_mysql.execute(sql)
results = cursor_mysql.fetchall()

for result in results:
    main_id, class_id = result["main_form_entry_id"], result["class_form_entry_id"]
    if main_id not in entry_id_map or class_id not in entry_id_map:
        #print("error class: %i %i" % (main_id, class_id))
        continue
        
    sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
    cursor_sqlite.execute(sql, (entry_id_map[main_id], entry_id_map[class_id]))
    #print("class: %i %i" % (main_id, class_id))
    conn_sqlite.commit()
    
    
    
    

sql = "select * from TCrpQ_wpforms_connect_sample;"
cursor_mysql.execute(sql)
results = cursor_mysql.fetchall()

for result in results:
    main_id, sample_id = result["main_form_entry_id"], result["sample_form_entry_id"]
    if main_id not in entry_id_map or sample_id not in entry_id_map:
        #print("error sample: %i %i" % (main_id, sample_id))
        continue
        
    sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
    cursor_sqlite.execute(sql, (entry_id_map[main_id], entry_id_map[sample_id]))
    #print("class: %i %i" % (main_id, sample_id))
    conn_sqlite.commit()
    
    
    
    
#TODO: lösche Karteileichen
# SELECT * FROM TCrpQ_entries WHERE form = 'lipid-class' and id NOT IN (SELECT class_form_entry_id from TCrpQ_connect_lipid_class);
