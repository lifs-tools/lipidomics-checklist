import sys
import os
import time
import subprocess
import json
import pysodium
import base64
from datetime import datetime
from urllib import parse
from urllib.parse import unquote, unquote_plus
import hashlib
import CreateReport
import sqlite3
from random import randint
import requests
import db.ChecklistConfig as cfg
from FormsEnum import *

    
    
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


all_commands = {"get_main_forms", "get_class_forms", "get_sample_forms",
                "add_main_form", "add_class_form", "add_sample_form",
                "copy_main_form", "copy_class_form", "copy_sample_form",
                "delete_main_form", "delete_class_form", "delete_sample_form",
                "get_all_class_forms", "get_all_sample_forms",
                "import_class_forms", "import_sample_forms",
                "complete_partial_form",
                "get_pdf", "publish", "get_public_link",
                "get_form_content", "update_form_content",
                "export_samples", "import_samples",
                "export_lipid_class", "import_lipid_class"}
conn = None
table_prefix = "TCrpQ_"
version = "v2.0.0"

path_name = "lipidomics-checklist"

main_form_id = "checklist"
class_form_id = "lipid-class"
sample_form_id = "sample"

partial_label = "partial"
completed_label = "completed"
published_label = "published"


workflow_types = {"di", "sep", "img"}

form_types = {"main": main_form_id,
              "class": class_form_id,
              "sample": sample_form_id
             }



def dbconnect():
    try:
        conn = sqlite3.connect(cfg.db_file)
        conn.row_factory = dict_factory
        curr = conn.cursor()
    except Exception as e:
        print(str(ErrorCodes.NO_DATABASE_CONNECTION) + " in dbconnect", e)
        exit()
        
    return conn, curr




def check_entry_id(entry_id, uid, db_cursor, form_type):
    entry_id = int(entry_id)
    uid = int(uid)
    sql = "SELECT count(*) AS cnt FROM %sentries WHERE id = ? and form = ? and user_id = ?;" % table_prefix
    db_cursor.execute(sql, (entry_id, form_types[form_type], uid))
    request = db_cursor.fetchone()
    return request["cnt"] != 0
    



def check_status(entry_id, uid, db_cursor, not_in = None, is_in = None):
    global table_prefix
    
    # checking if main form is partial or completed
    sql = "SELECT * FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
    db_cursor.execute(sql, (uid, entry_id))
    request = db_cursor.fetchone()
    status = request["status"]
    if not_in != None:
        if status not in not_in:
            print(str(ErrorCodes.PUBLISHED_ERROR) + " in check_state")
            exit()
            
    elif is_in != None:
        if status in is_in:
            print(str(ErrorCodes.PUBLISHED_ERROR) + " in check_state")
            exit()

    return status, request



def get_encrypted_entry(entry_id):
    conn, db_cursor = dbconnect()
    try:
        #key = "zMpfgHoUsie9p8VwcT3v7yYGBTunMs/PcFivTvDqDCU="
        message = bytes(str(entry_id), 'utf-8')
        nonce = pysodium.randombytes(pysodium.crypto_stream_NONCEBYTES)
        key = base64.b64decode(cfg.encryption_key)
        
        
        cipher = nonce + pysodium.crypto_secretbox(message, nonce, key)
        return str(base64.b64encode(cipher), "utf-8")

    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in get_encrypted_entry", e)

    finally:
        if conn is not None: conn.close()





def get_decrypted_entry(entry_id):
    conn, db_cursor = dbconnect()
    try:
        #key = "zMpfgHoUsie9p8VwcT3v7yYGBTunMs/PcFivTvDqDCU="
        message = bytes(str(entry_id), 'utf-8')
        key = base64.b64decode(cfg.encryption_key)
        decoded_entry_id = base64.b64decode(entry_id)
        
        nonce = decoded_entry_id[:pysodium.crypto_stream_NONCEBYTES]
        return str(pysodium.crypto_secretbox_open(decoded_entry_id[pysodium.crypto_stream_NONCEBYTES:], nonce, key), "utf-8")

    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in get_decrypted_entry", e)

    finally:
        if conn is not None: conn.close()




def get_content(request):
    content = {}
    for entry in request.split("&"):
        tokens = entry.split("=")
        if len(tokens) == 2:
            content[tokens[0]] = unquote(tokens[1])
        elif len(tokens) == 1:
            content[tokens[0]] = ""
    return content


if len(sys.argv) > 1:
    content = get_content(sys.argv[1])
else:
    print("ErrorCodes.NO_REQUEST_CONTENT")
    exit()
    

if "request_file" in content:
    with open(content["request_file"], "rt") as request_file:
        request = request_file.read()
    os.remove(content["request_file"])
    content = get_content(request)


          

if len(content) == 0:
    print(str(ErrorCodes.NO_CONTENT) + " in main")
    exit()
      

    
# check if manager command is present and valid
if "command" not in content: 
    print(str(ErrorCodes.NO_COMMAND_ARGUMENT) + " in main")
    exit()
if content["command"] not in all_commands:
    print(str(ErrorCodes.INVALID_COMMAND_ARGUMENT) + " in main")
    exit()
    
    
    

    
    
def get_select_value(field, field_name, current_label):
    if "label" in field and field["label"] == field_name and "choice" in field and len(field["choice"]) > 0:
        for choice in field["choice"]:
            if "label" in choice and "value" in choice and choice["value"] == 1:
                return choice["label"]
    return current_label
    
    
    
################################################################################
## get forms
################################################################################


if content["command"] == "get_main_forms":
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # getting all main forms
        sql = "SELECT status, id, date, fields FROM %sentries WHERE form = ? AND user_id = ?;" % table_prefix
        db_cursor.execute(sql, (main_form_id, uid))
        request = db_cursor.fetchall()
        type_to_name = {"di": "direct infusion", "sep": "separation", "img": "imaging"}
        for entry in request:
            entry["entry_id"] = get_encrypted_entry(entry["id"])
            title = ""
            entry["type"] = ""
            if len(entry["fields"]) > 0:
                field_data = json.loads(entry["fields"])
                del entry["fields"]
                
                if len(field_data) > 0:
                    for field in field_data["pages"][0]["content"]:
                        if "label" in field and field["label"] == "Title of the study" and len(field["value"]) > 0:
                            title = field["value"]
                            
                        elif "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                            entry["type"] = field["value"]
                            
            
            if len(title) == 0: entry["title"] = "Untitled %s report" % (type_to_name[entry["type"]] if entry["type"] in type_to_name else "")
            else: entry["title"] = title
            entry["type"] = (type_to_name[entry["type"]] if entry["type"] in type_to_name else "").capitalize()
        print(json.dumps(request))
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
    
        
        
        

    

elif content["command"] == "get_class_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    if "main_entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
        
        # getting all main forms
        sql = "SELECT wpe.status, wpe.id, wpe.date, wpe.date, wpe.fields FROM %sconnect_lipid_class AS c INNER JOIN %sentries AS wpe ON c.class_form_entry_id = wpe.id WHERE c.main_form_entry_id = ? and wpe.form = ? AND wpe.user_id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (main_entry_id, class_form_id, uid))
        request = db_cursor.fetchall()
        for entry in request:
            entry["entry_id"] = get_encrypted_entry(entry["id"])
            
            if len(entry["fields"]) > 0:
                field_data = json.loads(entry["fields"].replace("'", '"'))
                del entry["fields"]
                
                lipid_class = ""
                other_lipid_class = ""
                ion_type = ""
                pos_ion = ""
                neg_ion = ""
                
                if len(field_data) > 0:
                    for field in field_data["pages"][0]["content"]:
                        lipid_class = get_select_value(field, "Lipid class", lipid_class)
                        pos_ion = get_select_value(field, "Type of positive (precursor)ion", pos_ion)
                        neg_ion = get_select_value(field, "Type of negative (precursor)ion", neg_ion)
                        ion_type = get_select_value(field, "Polarity mode", ion_type)
                        
                        if "label" in field and field["label"] == "Other Lipid class" and "value" in field and len(field["value"]) > 0:
                            other_lipid_class = field["value"]
                                
                if lipid_class[:5] == "other": lipid_class = other_lipid_class
                ion = pos_ion if ion_type.lower() == "positive" else neg_ion
            entry["title"] = "%s%s" % (lipid_class, ion)
        print(json.dumps(request))

    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_CLASS_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    
    

elif content["command"] == "get_sample_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    if "main_entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
        
        # getting all main forms
        sql = "SELECT wpe.status, wpe.id, wpe.date, wpe.fields FROM %sconnect_sample AS c INNER JOIN %sentries AS wpe ON c.sample_form_entry_id = wpe.id WHERE c.main_form_entry_id = ? and wpe.form = ? AND wpe.user_id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (main_entry_id, sample_form_id, uid))
        request = db_cursor.fetchall()
        for entry in request:
            entry["entry_id"] = get_encrypted_entry(entry["id"])
                
            entry["title"] = "Unspecified sample"
            sample_type, sample_set = "", ""
            if len(entry["fields"]) > 0:
                field_data = json.loads(entry["fields"])
                del entry["fields"]
                
                if len(field_data) > 0:
                    for field in field_data["pages"][0]["content"]:
                        if "label" in field and field["label"] == "Sample set name" and "value" in field and len(field["value"]) > 0:
                            sample_set = field["value"]
                            
                        sample_type = get_select_value(field, "Sample type", sample_type)
            if len(sample_type) > 0 and len(sample_set) > 0:
                entry["title"] = "%s / %s" % (sample_set, sample_type)
        print(json.dumps(request))

    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_SAMPLE_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
        
        
        
        
        
        
        
        
    
    
    
    
    
    
    
    
    
################################################################################
## get all secondary forms
################################################################################


elif content["command"] == "get_all_class_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    

    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # getting all main forms
        sql = "SELECT wpe2.fields as main_fields, wpe.status, wpe.id, wpe.date, wpe.fields FROM %sconnect_lipid_class AS c INNER JOIN %sentries AS wpe ON c.class_form_entry_id = wpe.id INNER JOIN %sentries as wpe2 ON c.main_form_entry_id = wpe2.id WHERE wpe.form = ? AND wpe.user_id = ? AND wpe.status <> ? AND wpe2.status <> ?;" % (table_prefix, table_prefix, table_prefix)
        db_cursor.execute(sql, (class_form_id, uid, partial_label, partial_label))
        request = db_cursor.fetchall()
        for entry in request:
            entry["entry_id"] = get_encrypted_entry(entry["id"])
            
            entry["main_title"] = "Untitled report"
            if "main_fields" in entry and len(entry["main_fields"]) > 0:
                field_data = json.loads(entry["main_fields"])
                if len(field_data) > 0:
                    for field in field_data["pages"][0]["content"]:
                        if "label" in field and field["label"] == "Title of the study" and len(field["value"]) > 0:
                            entry["main_title"] = field["value"]
                del entry["main_fields"]
            
            title = ["Unspecified class", "[M]", "No Instrument"]
            if len(entry["fields"]) > 0:
                field_data = json.loads(entry["fields"])
                
                lipid_class = ""
                other_lipid_class = ""
                ion_type = ""
                pos_ion = ""
                neg_ion = ""
                
                if len(field_data) > 0:
                    for field in field_data["pages"][0]["content"]:
                        lipid_class = get_select_value(field, "Lipid class", lipid_class)
                        pos_ion = get_select_value(field, "Type of positive (precursor)ion", pos_ion)
                        neg_ion = get_select_value(field, "Type of negative (precursor)ion", neg_ion)
                        ion_type = get_select_value(field, "Polarity mode", ion_type)
                        
                        if "label" in field and field["label"] == "Other Lipid class" and "value" in field and len(field["value"]) > 0:
                            other_lipid_class = field["value"]
                                
                if lipid_class[:5] == "other": lipid_class = other_lipid_class
                ion = pos_ion if ion_type.lower() == "positive" else neg_ion
                del entry["fields"]
            entry["title"] = "%s%s" % (lipid_class, ion)
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(json.dumps(request))





elif content["command"] == "get_all_sample_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # getting all main forms
        sql = "SELECT wpe2.fields as main_fields, wpe.status, wpe.id, wpe.date, wpe.fields FROM %sconnect_sample AS c INNER JOIN %sentries AS wpe ON c.sample_form_entry_id = wpe.id INNER JOIN %sentries as wpe2 ON c.main_form_entry_id = wpe2.id WHERE wpe.form = ? AND wpe.user_id = ? AND wpe.status <> ? AND wpe2.status <> ?;" % (table_prefix, table_prefix, table_prefix)
        db_cursor.execute(sql, (sample_form_id, uid, partial_label, partial_label))
        request = db_cursor.fetchall()
        for entry in request:
            entry["entry_id"] = get_encrypted_entry(entry["id"])
            
            entry["main_title"], entry["title"] = "Untitled report", "Unspecified sample"
            if "main_fields" in entry and len(entry["main_fields"]) > 0:
                field_data = json.loads(entry["main_fields"])
                
                if len(field_data) > 0:
                    for field in field_data["pages"][0]["content"]:
                        if "label" in field and field["label"] == "Title of the study" and len(field["value"]) > 0:
                            entry["main_title"] = field["value"]
                
            del entry["main_fields"]
            
            if len(entry["fields"]) > 0:
                field_data = json.loads(entry["fields"])
                del entry["fields"]
                
                sample_set_name = ""
                sample_origin = ""
                sample_type = ""
                
                if len(field_data) > 0:
                    for field in field_data["pages"][0]["content"]:
                        if "label" in field and field["label"] == "Sample set name" and "value" in field and len(field["value"]) > 0:
                            sample_set_name = field["value"]
                            
                        sample_type = get_select_value(field, "Sample type", sample_type)
                        sample_origin = get_select_value(field, "Sample origin", sample_origin)
                
                if len(sample_set_name) > 0 and len(sample_origin) > 0 and len(sample_type) > 0:
                    entry["title"] = "%s / %s / %s" % (sample_set_name, sample_origin, sample_type)
        print(json.dumps(request))
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()   
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
 
    
################################################################################
## add forms
################################################################################   

        
elif content["command"] == "add_main_form":
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    
    if "workflow_type" not in content:
        print(str(ErrorCodes.NO_WORKFLOW_TYPE) + " in %s" % content["command"])
        exit()
    if content["workflow_type"] not in workflow_types:
        print(str(ErrorCodes.INCORRECT_WORKFLOW_TYPE) + " in %s" % content["command"])
        exit()
    workflow_type = content["workflow_type"]
    
    
    # connect with the database
    try:
        conn, db_cursor = dbconnect()
        
        field_template = json.loads(open("workflow-templates/checklist.json").read())
        if "pages" in field_template and len(field_template["pages"]) > 0:
            for field in field_template["pages"][0]["content"]:
                if field["type"] == "hidden":
                    field["value"] = workflow_type
                    break
            field_template["version"] = version
        field_template = json.dumps(field_template)
        
        
        # add main form entry
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, 'partial', ?, DATETIME('now'), ?);" % table_prefix
        values = (main_form_id, uid, field_template, user_uuid)
        db_cursor.execute(sql, values)
        conn.commit()
        
        sql = "SELECT max(id) AS max_id FROM %sentries WHERE user_id = ? AND form = ?;" % table_prefix
        db_cursor.execute(sql, (uid, main_form_id))
        
        print(get_encrypted_entry(db_cursor.fetchone()["max_id"]))
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_ADDING_MAIN_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
        
    
        
elif content["command"] == "add_class_form":
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "main_entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
            
        # checking if main form is partial or completed
        status, request = check_status(main_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
            
            
        field_data = json.loads(request["fields"])
        workflow_type = ""
        for field in field_data["pages"][0]["content"]:
            if "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                workflow_type = field["value"]
        
        
        field_template = json.loads(open("workflow-templates/lipid-class.json").read())
        if "pages" in field_template and len(field_template["pages"]) > 0:
            for field in field_template["pages"][0]["content"]:
                if field["type"] == "hidden":
                    field["value"] = workflow_type
                    break
            field_template["version"] = version
            field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        field_template = json.dumps(field_template)
        
        
        
        # add main form entry
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, 'partial', ?, DATETIME('now'), ?);" % table_prefix
        values = (class_form_id, uid, field_template, user_uuid)
        db_cursor.execute(sql, values)
        conn.commit()
        
        # get new class entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ? and status = 'partial';" % table_prefix
        db_cursor.execute(sql, (uid, class_form_id))
        request = db_cursor.fetchone()
        new_class_entry_id = request["eid"]
        
        # add main entry id and class entry id pair into DB
        sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
        db_cursor.execute(sql, (main_entry_id, new_class_entry_id))
        conn.commit()
        
        if status == completed_label:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (partial_label, main_entry_id, uid))
            conn.commit()
        
        print(get_encrypted_entry(new_class_entry_id))
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_ADDING_CLASS_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
        
    
    
    
    
    
    
    
    
    
        
elif content["command"] == "add_sample_form":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "main_entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
        
        # checking if main form is partial or completed
        status, request = check_status(main_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
            
        field_template = json.loads(open("workflow-templates/sample.json").read())
        field_template["version"] = version
        field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        field_template = json.dumps(field_template)
        
        # add main form entry
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, DATETIME('now'), ?);" % table_prefix
        values = (sample_form_id, uid, partial_label, field_template, user_uuid)
        db_cursor.execute(sql, values)
        conn.commit()
        
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ? and status = ?;" % table_prefix
        db_cursor.execute(sql, (uid, sample_form_id, partial_label))
        request = db_cursor.fetchone()
        new_sample_entry_id = request["eid"]
        
        # add main entry id and sample entry id pair into DB
        sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
        db_cursor.execute(sql, (main_entry_id, new_sample_entry_id))
        conn.commit()
        
        if status == completed_label:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (partial_label, main_entry_id, uid))
            conn.commit()
            
        print(get_encrypted_entry(new_sample_entry_id))
            
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_ADDING_SAMPLE_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
 
    
################################################################################
## complete partial form
################################################################################  
        
        
        
        
elif content["command"] == "complete_partial_form":
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # checking if main form is partial or completed
        status, request = check_status(entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
        
        
        # delete old partial entry
        sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
        db_cursor.execute(sql, (completed_label, entry_id, uid))
        conn.commit()
        
        
        sql = "SELECT form FROM %sentries WHERE id = ? AND user_id = ?;" % table_prefix
        db_cursor.execute(sql, (entry_id, uid))
        request = db_cursor.fetchone()
        
        
        # add report hash number if necessary
        if request["form"] == main_form_id:
            sql = "SELECT COUNT(*) as cnt FROM %sreports WHERE entry_id = ?;" % table_prefix
            db_cursor.execute(sql, (entry_id,))
            request = db_cursor.fetchone()["cnt"]
            
            if request == 0:
                while True:
                    #hash_value = "%i-%i-%s" % (entry_id, uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    #hash_value = hashlib.md5(hash_value.encode()).hexdigest()
                    hash_value = chr(randint(97, 122)) + chr(randint(97, 122)) + "".join(str(randint(0, 9)) for i in range(8))
                    
                    sql = "SELECT COUNT(*) AS cnt FROM %sreports WHERE hash = ?;" % table_prefix
                    db_cursor.execute(sql, (hash_value,))
                    if db_cursor.fetchone()["cnt"] == 0: break
                
                sql = "INSERT INTO %sreports (entry_id, hash, DOI) VALUES (?, ?, '');" % table_prefix
                db_cursor.execute(sql, (entry_id, hash_value))
                conn.commit()
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_DELETING_MAIN_FORM) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
    
    print(0)
    
    
    
    
        
        
   
   
   
   
   
   
        
 
    
################################################################################
## copy forms
################################################################################  


elif content["command"] == "copy_main_form":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
            
        # get form to copy and update some entries
        sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        db_cursor.execute(sql, (uid, main_entry_id))
        request = db_cursor.fetchone()
        fields = json.loads(request["fields"])
        fields["current_page"] = 0
        fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fields = json.dumps(fields)
        
        
        # copy content assigned to entry id
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (partial_label, fields, uid, main_entry_id))
        conn.commit()
        
        
        # retrieve new main entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
        db_cursor.execute(sql, (uid, main_form_id))
        request = db_cursor.fetchone()
        new_main_entry_id = request["eid"]
        
        
        # copy all lipid sample forms assigned to old entry
        sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (main_entry_id,))
        sample_form_entry_ids = [row["sample_form_entry_id"] for row in db_cursor.fetchall()]
        
        for sample_entry_id in sample_form_entry_ids:
            
            # get form to copy and update some entries
            sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
            db_cursor.execute(sql, (uid, sample_entry_id))
            request = db_cursor.fetchone()
            fields = json.loads(request["fields"])
            fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fields = json.dumps(fields)
                
                
            # copy content assigned to entry id
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            db_cursor.execute(sql, (partial_label, fields, uid, sample_entry_id))
            conn.commit()
                
            
            # retrieve new main entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            db_cursor.execute(sql, (uid, sample_form_id))
            request = db_cursor.fetchone()
            new_sample_entry_id = request["eid"]
            
            
            # add copy of lipid sample form into connetion table
            sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
            db_cursor.execute(sql, (new_main_entry_id, new_sample_entry_id))
            conn.commit()
    
    
        
        # copy all lipid class forms assigned to old entry
        sql = "SELECT class_form_entry_id FROM %sconnect_lipid_class WHERE main_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (main_entry_id,))
        class_form_entry_ids = [row["class_form_entry_id"] for row in db_cursor.fetchall()]
        
        for class_entry_id in class_form_entry_ids:
            
            # get form to copy and update some entries
            sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
            db_cursor.execute(sql, (uid, class_entry_id))
            request = db_cursor.fetchone()
            fields = json.loads(request["fields"])
            fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fields = json.dumps(fields)
                
                
            # copy content assigned to entry id
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            db_cursor.execute(sql, (partial_label, fields, uid, class_entry_id))
            conn.commit()
                
            
            # retrieve new main entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            db_cursor.execute(sql, (uid, class_form_id))
            request = db_cursor.fetchone()
            new_class_entry_id = request["eid"]
            
            
            # add copy of lipid class form into connetion table
            sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
            db_cursor.execute(sql, (new_main_entry_id, new_class_entry_id))
            conn.commit()
            
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXECUTING_FUNCTION) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        
        
        
        
        
        
        
        


elif content["command"] == "copy_class_form":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_CLASS_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        class_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_CLASS_SAMPLE_ID) + " in %s" % content["command"])
        exit()
    if class_entry_id < 0:
        print(str(ErrorCodes.INVALID_CLASS_SAMPLE_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(class_entry_id, uid, db_cursor, "class"):
            print(str(ErrorCodes.INVALID_CLASS_SAMPLE_ID) + " in %s" % content["command"])
            exit()
            
            
        # get main entry id
        sql = "SELECT main_form_entry_id FROM %sconnect_lipid_class WHERE class_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (class_entry_id,))
        request = db_cursor.fetchone()
        main_entry_id = request["main_form_entry_id"]
        
        
        # checking if main form is partial or completed
        status, request = check_status(main_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
        
            
        # get form to copy and update some entries
        sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        db_cursor.execute(sql, (uid, class_entry_id))
        request = db_cursor.fetchone()
        fields = json.loads(request["fields"])
        fields["current_page"] = 0
        fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fields = json.dumps(fields)
            
        
        # copy content assigned to entry id
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (partial_label, fields, uid, class_entry_id))
        conn.commit()
            
        
        # retrieve new main entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
        db_cursor.execute(sql, (uid, class_form_id))
        request = db_cursor.fetchone()
        new_class_entry_id = request["eid"]
        
        
        # add copy of lipid class form into connetion table
        sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
        db_cursor.execute(sql, (main_entry_id, new_class_entry_id))
        conn.commit()
        
        
        if status == completed_label:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (partial_label, main_entry_id, uid))
            conn.commit()
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXECUTING_FUNCTION) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
    
    
    
    
    
    
        


elif content["command"] == "copy_sample_form":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        sample_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if sample_entry_id < 0:
        print(str(ErrorCodes.INVALID_SAMPLE_SAMPLE_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(sample_entry_id, uid, db_cursor, "sample"):
            print(str(ErrorCodes.INVALID_SAMPLE_SAMPLE_ID) + " in %s" % content["command"])
            exit()
        
        
        # get main entry id
        sql = "SELECT main_form_entry_id FROM %sconnect_sample WHERE sample_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (sample_entry_id, ))
        request = db_cursor.fetchone()
        main_entry_id = request["main_form_entry_id"]
        
        
        # checking if main form is partial or completed
        status, request = check_status(main_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
        
            
        # get form to copy and update some entries
        sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        db_cursor.execute(sql, (uid, sample_entry_id))
        request = db_cursor.fetchone()
        fields = json.loads(request["fields"])
        fields["current_page"] = 0
        fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fields = json.dumps(fields)
            
            
        # copy content assigned to entry id
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (partial_label, fields, uid, sample_entry_id))
        conn.commit()
            
        
        # retrieve new main entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
        db_cursor.execute(sql, (uid, sample_form_id))
        request = db_cursor.fetchone()
        new_sample_entry_id = request["eid"]
        
        
        # add copy of lipid sample form into connetion table
        sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
        db_cursor.execute(sql, (main_entry_id, new_sample_entry_id))
        conn.commit()
        
        
        if status == completed_label:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (partial_label, main_entry_id, uid))
            conn.commit()
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXECUTING_FUNCTION) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        









        
 
    
################################################################################
## delete forms
################################################################################  

elif content["command"] == "delete_class_form":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        class_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if class_entry_id < 0: print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(class_entry_id, uid, db_cursor, "class"):
            print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
            exit()
        
        # checking if class form is partial or completed
        status, request = check_status(class_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
            
        
        # delete class entry from connection table
        sql = "DELETE FROM %sconnect_lipid_class WHERE class_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (class_entry_id,))
        conn.commit()
        
        # delete class entry
        sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
        db_cursor.execute(sql, (class_entry_id, class_form_id, uid))
        conn.commit()
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_DELETING_CLASS_FORM) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)




elif content["command"] == "delete_sample_form":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        sample_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if sample_entry_id < 0: print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(sample_entry_id, uid, db_cursor, "sample"):
            print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
            
        # checking if sample form is partial or completed
        status, request = check_status(sample_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
            
            
        # delete sample entry from connection table
        sql = "DELETE FROM %sconnect_sample WHERE sample_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (sample_entry_id,))
        conn.commit()
        
        
        # delete sample entry
        sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
        db_cursor.execute(sql, (sample_entry_id, sample_form_id, uid))
        conn.commit()
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_DELETING_SAMPLE_FORM) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
     
     
     
     
     
        
        
        


elif content["command"] == "delete_main_form":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()

        # check status of entry
        sql = "SELECT e.status, r.hash FROM %sentries AS e LEFT JOIN %sreports AS r ON e.id = r.entry_id WHERE e.id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (main_entry_id,))
        results = db_cursor.fetchone()
        main_status = results["status"]
        hash_value = results["hash"]
        if main_status not in {partial_label, completed_label}:
            print(0)
            exit()
            
        
        # delete all lipid sample forms assigned to current entry
        sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (main_entry_id,))
        sample_form_entry_ids = [row["sample_form_entry_id"] for row in db_cursor.fetchall()]
        
        for sample_form_entry_id in sample_form_entry_ids:
            # delete sample entry from connection table
            sql = "DELETE FROM %sconnect_sample WHERE sample_form_entry_id = ?;" % table_prefix
            db_cursor.execute(sql, (sample_form_entry_id,))
            conn.commit()
            
            # delete sample entry
            sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (sample_form_entry_id, sample_form_id, uid))
            conn.commit()
            
            
        
        # delete all lipid class forms assigned to current entry
        sql = "SELECT class_form_entry_id FROM %sconnect_lipid_class WHERE main_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (main_entry_id,))
        class_form_entry_ids = [row["class_form_entry_id"] for row in db_cursor.fetchall()]
        
        for class_form_entry_id in class_form_entry_ids:
            # delete class entry from connection table
            sql = "DELETE FROM %sconnect_lipid_class WHERE class_form_entry_id = ?;" % table_prefix
            db_cursor.execute(sql, (class_form_entry_id,))
            conn.commit()
            
            # delete class entry
            sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (class_form_entry_id, class_form_id, uid))
            conn.commit()
            
            
        # delete main entry
        sql = "DELETE FROM %sreports WHERE entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (main_entry_id, ))
        conn.commit()
            
            
        # delete main entry
        sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
        db_cursor.execute(sql, (main_entry_id, main_form_id, uid))
        conn.commit()
        
        
        # check if entry in reports exist and delete entry and pdf file
        if hash_value != None:
            for extension in {"aux", "log", "out", "tex", "pdf"}:
                file_to_del = "completed_documents/report-%s.%s" % (hash_value, extension)
                if os.path.exists(file_to_del): os.remove(file_to_del)
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        
        
        
        
        
        
        
        
        
 
    
################################################################################
## remaining commands
################################################################################  


elif content["command"] == "import_class_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    
    if "class_entry_ids" not in content:
        print(str(ErrorCodes.NO_CLASS_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        import_class_forms = [int(get_decrypted_entry(c_id)) for c_id in content["class_entry_ids"].split("|")]
    except:
        print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # checking if main form is partial or completed
        status, request = check_status(main_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
        
        
        for class_entry_id in import_class_forms:
            if not check_entry_id(class_entry_id, uid, db_cursor, "class"):
                print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
                exit()
                
            # import new entry based on old entry
            
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, fields, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            db_cursor.execute(sql, (partial_label, uid, class_entry_id))
            conn.commit()
            
            # get new class entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            db_cursor.execute(sql, (uid, class_form_id))
            request = db_cursor.fetchone()
            new_class_entry_id = request["eid"]
            
            # add main entry id and class entry id pair into DB
            sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
            db_cursor.execute(sql, (main_entry_id, new_class_entry_id))
            conn.commit()
            
        if len(import_class_forms) > 0 and status == completed_label:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (partial_label, main_entry_id, uid))
            conn.commit()
            
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXECUTING_FUNCTION) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close() 
        
    print(0)










elif content["command"] == "import_sample_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    if "sample_entry_ids" not in content:
        print(str(ErrorCodes.NO_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        import_sample_forms = [int(get_decrypted_entry(c_id)) for c_id in content["sample_entry_ids"].split("|")]
    except:
        print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    
    
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # checking if sample form is partial or completed
        status, request = check_status(main_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
            
        
        for sample_entry_id in import_sample_forms:
            if not check_entry_id(sample_entry_id, uid, db_cursor, "sample"):
                print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
                exit()
            
            # import new entry based on old entry    
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, fields, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            db_cursor.execute(sql, (partial_label, uid, sample_entry_id))
            conn.commit()
            
            # get new sample entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            db_cursor.execute(sql, (uid, sample_form_id))
            request = db_cursor.fetchone()
            new_sample_entry_id = request["eid"]
            
            # add main entry id and sample entry id pair into DB
            sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
            db_cursor.execute(sql, (main_entry_id, new_sample_entry_id))
            conn.commit()
            
        if len(import_sample_forms) > 0 and status == completed_label:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (partial_label, main_entry_id, uid))
            conn.commit()
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXECUTING_FUNCTION) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        
        
        
        
        
        


elif content["command"] == "get_pdf":
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        sql = "SELECT hash FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (entry_id, uid))
        hash_value = db_cursor.fetchone()["hash"]
        
        pdf_file = "completed_documents/report-%s.pdf" % hash_value
        
        if not os.path.exists(pdf_file):
            
            # creating the tex and pdf file
            report_file = "completed_documents/report-%s.tex" % hash_value
            
            CreateReport.create_report(db_cursor, table_prefix, uid, entry_id, report_file, version)
            p = subprocess.Popen("/usr/bin/lualatex -output-directory=completed_documents %s" % report_file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
            
            output = p.stdout.read() # execution
            
            if os.path.exists(pdf_file):
                print("/%s/%s" % (path_name, pdf_file))
            
            else:
                print(str(output))
            
        else:
            print("/%s/%s" % (path_name, pdf_file))

    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_CREATING_PDF) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
        

        
        
        
    
    
        

        
        


elif content["command"] == "publish":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
            
            
        # checking if main form is partial or completed
        status, request = check_status(entry_id, uid, db_cursor, is_in = {partial_label, published_label})
        
        
        fields = json.loads(request["fields"])
        report_title, report_author,report_affiliation = "-", "-", "-"
        
        for field in fields["pages"][0]["content"]:
            if "name" in field and field["name"] == "title_study": report_title = field["value"]
            elif "name" in field and field["name"] == "principle_investigator": report_author = field["value"]
            elif "name" in field and field["name"] == "institution": report_affiliation = field["value"]
        
        
            
        # checking if pdf was created
        sql = "SELECT r.hash FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (entry_id, uid))
        hash_value = db_cursor.fetchone()["hash"]
        
        pdf_file = "report-%s.pdf" % hash_value
        pdf_path = "completed_documents/%s" % pdf_file
        if not os.path.exists(pdf_path):
            print(str(ErrorCodes.REPORT_NOT_CREATED) + " in %s" % content["command"])
            exit()

        headers = {"Content-Type": "application/json"}
        params = {'access_token': cfg.ACCESS_TOKEN}
        
        
        publishing_error_code = ""
        try:
            publishing_error_code = "Error during Zenodo reservation"
            r = requests.post('https://%s/api/deposit/depositions' % cfg.zenodo_link, params = params, json = {}, headers = headers, timeout = 15)

            if r.status_code != 201:
                print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], json.dumps(r.json())))
                exit()
        except:
            print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], publishing_error_code))
            exit()
                
                
        try:
            publishing_error_code = "Error during Zenodo upload"
            bucket_url = r.json()["links"]["bucket"]
            record_id = r.json()["record_id"]


            with open(pdf_path, "rb") as fp:
                r = requests.put("%s/%s" % (bucket_url, pdf_file), data = fp, params = params, timeout = 15)

            if r.status_code != 200:
                print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], json.dumps(r.json())))
                exit()
        except:
            print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], publishing_error_code))
            exit()



        try:
            publishing_error_code = "Error during Zenodo meta data upload"
            data = {
                'metadata': {
                    'title': report_title,
                    'upload_type': 'publication',
                    'publication_type': 'report',
                    'publication_date': datetime.now().strftime("%Y-%m-%d"),
                    'description': report_title,
                    'creators': [{'name': report_author, 'affiliation': report_affiliation}],
                    'communities': [{'identifier': 'ils'}]
                }
            }
            r = requests.put('https://%s/api/deposit/depositions/%s' % (cfg.zenodo_link, record_id), params = params, data=json.dumps(data), headers=headers, timeout = 15)
            
            if r.status_code != 200:
                print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], json.dumps(r.json())))
                exit()
            
        except:
            print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], publishing_error_code))
            exit()


        try:
            publishing_error_code = "Error during Zenodo publication"
            r = requests.post('https://%s/api/deposit/depositions/%s/actions/publish' % (cfg.zenodo_link, record_id), params = params, timeout = 15)
            
            if r.status_code != 202:
                print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], json.dumps(r.json())))
                exit()
                
            doi = r.json()["doi"]
        except:
            print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], publishing_error_code))
            exit()        

        
        

        # set status of entry to published
        sql = "UPDATE %sentries SET status = ? WHERE id = ? AND status = ?;" % table_prefix
        db_cursor.execute(sql, (published_label, entry_id, completed_label))
        conn.commit()
        
        
        sql = "UPDATE %sreports SET DOI = ? WHERE entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (doi, entry_id))
        conn.commit()
        
        
        # give all sample forms assigned to current entry a published status
        sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (entry_id,))
        sample_form_entry_ids = [row["sample_form_entry_id"] for row in db_cursor.fetchall()]
        for sample_form_entry_id in sample_form_entry_ids:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND status = ?;" % table_prefix
            db_cursor.execute(sql, (published_label, sample_form_entry_id, completed_label))
            conn.commit()

        
        # give all sample forms assigned to current entry a published status
        sql = "SELECT class_form_entry_id FROM %sconnect_lipid_class WHERE main_form_entry_id = ?;" % table_prefix
        db_cursor.execute(sql, (entry_id,))
        class_form_entry_ids = [row["class_form_entry_id"] for row in db_cursor.fetchall()]
        
        for class_entry_id in class_form_entry_ids:
            sql = "UPDATE %sentries SET status = ? WHERE id = ? AND status = ?;" % table_prefix
            db_cursor.execute(sql, (published_label, class_entry_id, completed_label))
            conn.commit()

    except Exception as e:
        print(str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
            
    print(0)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
elif content["command"] == "get_form_content":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except Exception as e:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"], e)
        exit()
        
    if entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # checking if main form is partial or completed
        status, request = check_status(entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
        
        sql = "SELECT fields FROM %sentries WHERE id = ?;" % table_prefix
        db_cursor.execute(sql, (entry_id,))
        print(db_cursor.fetchone()["fields"])

    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXECUTING_FUNCTION) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
        
        
        
        
        
        
        
        
        
        
        
        
elif content["command"] == "update_form_content":
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
        
    if "content" not in content:
        print(str(ErrorCodes.NO_CONTENT) + " in %s" % content["command"])
        exit()
        
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    try:
        form_content = unquote(base64.b64decode(content["content"]).decode("utf-8"))
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_DECODING_FORM) + " in %s" % content["command"], e)
        exit()
    
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    if entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
        
        
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        # checking if main form is partial or completed
        status, request = check_status(entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
        

        sql = "UPDATE %sentries SET fields = ? WHERE id = ? AND user_id = ?;" % table_prefix
        db_cursor.execute(sql, (form_content, entry_id, uid))
        conn.commit()
        
        
        # if updating completed main form, pdf must be deleted if present
        sql = "SELECT COUNT(*) as count_entries FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (entry_id, uid))
        
        
        
        if db_cursor.fetchone()["count_entries"] > 0:
            sql = "SELECT hash FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
            db_cursor.execute(sql, (entry_id, uid))
            pdf_file = "completed_documents/report-%s.pdf" % db_cursor.fetchone()["hash"]
            if os.path.isfile(pdf_file): os.remove(pdf_file)
                
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXECUTING_FUNCTION) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
elif content["command"] == "get_public_link":
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
        
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    if entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
        
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        
        # checking if main form is not partial or completed
        status, request = check_status(entry_id, uid, db_cursor, is_in = {partial_label, completed_label})

        
        sql = "SELECT r.DOI FROM %sreports AS r INNER JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? and e.user_id = ?;" % (table_prefix, table_prefix)
        db_cursor.execute(sql, (entry_id, uid))
        print("https://doi.org/%s" % db_cursor.fetchone()["DOI"])
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_GETTING_REPORT_LINK) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        








elif content["command"] in {"export_samples", "export_lipid_class"}:
    
    
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        form_type = FormType.LIPID_CLASS if content["command"] == "export_lipid_class" else FormType.SAMPLE
        template_file = "workflow-templates/sample.json" if form_type == FormType.SAMPLE else "workflow-templates/lipid-class.json"
        
        from ImportExportForms import export_forms_to_worksheet
        worksheet_base64 = export_forms_to_worksheet(table_prefix, template_file, form_type, db_cursor, uid, entry_id)
        print("data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,%s" % worksheet_base64)
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_EXPORTING_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
        
     
     
     
     
     
     
     
     
     
     
     
     
elif content["command"] == "import_samples":
    if "user_uuid" not in content or "uid" not in content:
        print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    if "entry_id" not in content:
        print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
    if main_entry_id < 0:
        print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
        exit()
        
    if "content" not in content:
        print(str(ErrorCodes.NO_CONTENT) + " in %s" % content["command"])
        exit()
    
    worksheet_base64 = content["content"]
    force_upload = "force_upload" in content
    
    
    try:
        # connect with the database
        conn, db_cursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, db_cursor, "main"):
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
        
        # checking if main form is partial or completed
        status, request = check_status(main_entry_id, uid, db_cursor, is_in = {published_label})
            
        
        from import_export_forms import import_forms_from_worksheet
        forms = import_forms_from_worksheet(table_prefix, "workflow-templates/sample.json", worksheet_base64, "sample", db_cursor, uid, main_entry_id)
        
        # all complete
        if sum(form[1] for form in forms) == len(forms) or force_upload:
            for field_template, is_complete in forms:
                field_template["version"] = version
                field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                field_template = json.dumps(field_template)
                
                status_label = completed_label if is_complete else partial_label
                
                # add sample form entry
                sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, DATETIME('now'), ?);" % table_prefix
                values = (sample_form_id, uid, status_label, field_template, user_uuid)
                db_cursor.execute(sql, values)
                conn.commit()
                
                sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ? and status = ?;" % table_prefix
                db_cursor.execute(sql, (uid, sample_form_id, status_label))
                request = db_cursor.fetchone()
                new_sample_entry_id = request["eid"]
                
                # add main entry id and sample entry id pair into DB
                sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
                db_cursor.execute(sql, (main_entry_id, new_sample_entry_id))
                conn.commit()
                
                if status == completed_label:
                    sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
                    db_cursor.execute(sql, (partial_label, main_entry_id, uid))
                    conn.commit()
            
            print(0)
            
        else:
            print("Warning: the following rows are incomplete: %s" % [(i + 3) for i, form in enumerate(forms) if not form[1]])
                
        
        
    except Exception as e:
        print(str(ErrorCodes.ERROR_ON_IMPORTING_FORMS) + " in %s" % content["command"], e)

    finally:
        if conn is not None: conn.close()
