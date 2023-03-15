import sys
import os
import time
import subprocess
import json
import pysodium
import base64
from datetime import datetime
from enum import Enum
from urllib import parse
from urllib.parse import unquote, unquote_plus
import hashlib
import create_report
import sqlite3



class ErrorCodes(Enum):
    NO_DB_CONNECTION = -1
    NO_COMMAND_ARGUMENT = -2
    INVALID_COMMAND_ARGUMENT = -3
    NO_USER_UUID = -4
    INVALID_USER_UUID = -5
    ERROR_ON_GETTING_MAIN_FORMS = -6
    NO_MAIN_ENTRY_ID = -7
    INVALID_MAIN_ENTRY_ID = -8
    ERROR_ON_GETTING_CLASS_FORMS = -9
    ERROR_ON_ADDING_MAIN_FORMS = -10
    ERROR_ON_ADDING_CLASS_FORMS = -11
    NO_CONTENT = -12
    ERROR_ON_DELETING_MAIN_FORM = -13
    ERROR_ON_COPYING_MAIN_FORM = -14
    NO_FORM_TYPE = -15
    NO_CLASS_ENTRY_ID = -16
    INVALID_CLASS_ENTRY_ID = -17
    ERROR_ON_CREATING_PDF = -18
    ERROR_ON_ADDING_SAMPLE_FORMS = -19
    MAIN_FORM_COMPLETED = -20
    ERROR_ON_GETTING_SAMPLE_FORMS = -21
    INVALID_SAMPLE_ENTRY_ID = -22
    ERROR_ON_DELETING_CLASS_FORM = -23
    ERROR_ON_DELETING_SAMPLE_FORM = -24
    INVALID_CLASS_SAMPLE_ID = -25
    NO_SAMPLE_ENTRY_ID = -26
    WPFORMS_CONFIG_FILE_UNREADABLE = -27
    NO_WORKFLOW_TYPE = -28
    INCORRECT_WORKFLOW_TYPE = -29
    NO_DATABASE_CONNECTION = -30
    ERROR_ON_DECODING_FORM = -31
    
    
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
                "get_pdf",
                "publish",
                "get_form_content",
                "update_form_content"}
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



main_workflow_type_field_id = 156
class_workflow_type_field_id = 84

workflow_types = {"di", "sep", "img"}

form_types = {"main": main_form_id,
              "class": class_form_id,
              "sample": sample_form_id
             }



def dbconnect():
    try:
        conn = sqlite3.connect("db/checklist.sqlite")
        conn.row_factory = dict_factory
        curr = conn.cursor()
    except Exception as e:
        print(ErrorCodes.NO_DATABASE_CONNECTION, e)
        exit()
        
    return conn, curr




def check_entry_id(entry_id, uid, mycursor, form_type):
    entry_id = int(entry_id)
    uid = int(uid)
    sql = "SELECT count(*) AS cnt FROM %sentries WHERE id = ? and form = ? and user_id = ?;" % table_prefix
    mycursor.execute(sql, (entry_id, form_types[form_type], uid))
    request = mycursor.fetchone()
    return request["cnt"] != 0
    




def get_encrypted_entry(entry_id):
    conn, mycursor = dbconnect()
    try:
        key = "zMpfgHoUsie9p8VwcT3v7yYGBTunMs/PcFivTvDqDCU="
        message = bytes(str(entry_id), 'utf-8')
        nonce = pysodium.randombytes(pysodium.crypto_stream_NONCEBYTES)
        key = base64.b64decode(key)
        
        
        cipher = nonce + pysodium.crypto_secretbox(message, nonce, key)
        return str(base64.b64encode(cipher), "utf-8")

    except Error as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS)

    finally:
        if conn is not None: conn.close()





def get_decrypted_entry(entry_id):
    conn, mycursor = dbconnect()
    try:
        key = "zMpfgHoUsie9p8VwcT3v7yYGBTunMs/PcFivTvDqDCU="
        message = bytes(str(entry_id), 'utf-8')
        key = base64.b64decode(key)
        decoded_entry_id = base64.b64decode(entry_id)
        
        nonce = decoded_entry_id[:pysodium.crypto_stream_NONCEBYTES]
        return str(pysodium.crypto_secretbox_open(decoded_entry_id[pysodium.crypto_stream_NONCEBYTES:], nonce, key), "utf-8")


    except Error as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS)

    finally:
        if conn is not None: conn.close()




# retrieve variables in request
#content = dict(parse.parse_qsl(parse.urlsplit(sys.argv[1]).query))

content = {}
if len(sys.argv) > 1:
    for entry in sys.argv[1].split("&"):
        tokens = entry.split("=")
        if len(tokens) == 2:
            content[tokens[0]] = unquote(tokens[1])
        elif len(tokens) == 1:
            content[tokens[0]] = ""

          

            
if len(content) == 0:
    print(ErrorCodes.NO_CONTENT)
    exit()
      

    
# check if manager command is present and valid
if "command" not in content: 
    print(ErrorCodes.NO_COMMAND_ARGUMENT)
    exit()
if content["command"] not in all_commands:
    print(ErrorCodes.INVALID_COMMAND_ARGUMENT)
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
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        # getting all main forms
        sql = "SELECT status, id, date, fields FROM %sentries WHERE form = ? AND user_id = ?;" % table_prefix
        mycursor.execute(sql, (main_form_id, uid))
        request = mycursor.fetchall()
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
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS, e)

    finally:
        if conn is not None: conn.close()
        
        
        
        

    

elif content["command"] == "get_class_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    if "main_entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()
        
        # getting all main forms
        sql = "SELECT wpe.status, wpe.id, wpe.date, wpe.date, wpe.fields FROM %sconnect_lipid_class AS c INNER JOIN %sentries AS wpe ON c.class_form_entry_id = wpe.id WHERE c.main_form_entry_id = ? and wpe.form = ? AND wpe.user_id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (main_entry_id, class_form_id, uid))
        request = mycursor.fetchall()
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
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_GETTING_CLASS_FORMS, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_GETTING_CLASS_FORMS, e)

    finally:
        if conn is not None: conn.close()
        
    
    

elif content["command"] == "get_sample_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    if "main_entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()
        
        # getting all main forms
        sql = "SELECT wpe.status, wpe.id, wpe.date, wpe.fields FROM %sconnect_sample AS c INNER JOIN %sentries AS wpe ON c.sample_form_entry_id = wpe.id WHERE c.main_form_entry_id = ? and wpe.form = ? AND wpe.user_id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (main_entry_id, sample_form_id, uid))
        request = mycursor.fetchall()
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
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_GETTING_SAMPLE_FORMS, e)
        

    except Exception as e:
        print(ErrorCodes.ERROR_ON_GETTING_SAMPLE_FORMS, e)

    finally:
        if conn is not None: conn.close()
        
        
        
        
        
        
        
        
        
    
    
    
    
    
    
    
    
    
################################################################################
## get all secondary forms
################################################################################


elif content["command"] == "get_all_class_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    

    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        # getting all main forms
        sql = "SELECT wpe2.fields as main_fields, wpe.status, wpe.id, wpe.date, wpe.fields FROM %sconnect_lipid_class AS c INNER JOIN %sentries AS wpe ON c.class_form_entry_id = wpe.id INNER JOIN %sentries as wpe2 ON c.main_form_entry_id = wpe2.id WHERE wpe.form = ? AND wpe.user_id = ? AND wpe.status <> 'partial' AND wpe2.status <> 'partial';" % (table_prefix, table_prefix, table_prefix)
        mycursor.execute(sql, (class_form_id, uid))
        request = mycursor.fetchall()
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
                ion = pos_ion if ion_type == "positive" else neg_ion
                del entry["fields"]
            entry["title"] = "%s%s" % (lipid_class, ion)
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS, e)

    finally:
        if conn is not None: conn.close()
        
    print(json.dumps(request))





elif content["command"] == "get_all_sample_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    # check if main form entry id is within the request and an integer

    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        # getting all main forms
        sql = "SELECT wpe2.fields as main_fields, wpe.status, wpe.id, wpe.date, wpe.fields FROM %sconnect_sample AS c INNER JOIN %sentries AS wpe ON c.sample_form_entry_id = wpe.id INNER JOIN %sentries as wpe2 ON c.main_form_entry_id = wpe2.id WHERE wpe.form = ? AND wpe.user_id = ? AND wpe.status <> 'partial' AND wpe2.status <> 'partial';" % (table_prefix, table_prefix, table_prefix)
        mycursor.execute(sql, (sample_form_id, uid))
        request = mycursor.fetchall()
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
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS, e)
        
    except Exception as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS, e)

    finally:
        if conn is not None: conn.close()   
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
 
    
################################################################################
## add forms
################################################################################   
        
        
elif content["command"] == "add_main_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    
    if "workflow_type" not in content:
        print(ErrorCodes.NO_WORKFLOW_TYPE)
        exit()
    if content["workflow_type"] not in workflow_types:
        print(ErrorCodes.INCORRECT_WORKFLOW_TYPE)
        exit()
    workflow_type = content["workflow_type"]
    
    
    # connect with the database
    try:
        conn, mycursor = dbconnect()
        
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
        mycursor.execute(sql, values)
        conn.commit()
        
        print(0)
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_ADDING_MAIN_FORMS, e)
        
    except Exception as e:
        print(ErrorCodes.ERROR_ON_ADDING_MAIN_FORMS, e)
        
    except:
        print(ErrorCodes.ERROR_ON_ADDING_MAIN_FORMS)

    finally:
        if conn is not None: conn.close()
        
        
    
        
elif content["command"] == "add_class_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "main_entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()
        
        
        # checking if main form is partial or completed
        sql = "SELECT fields, status FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        mycursor.execute(sql, (uid, main_entry_id))
        request = mycursor.fetchone()
        if request["status"] != {partial_label, completed_label}:
            print(ErrorCodes.MAIN_FORM_COMPLETED)
            exit()
            
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
        mycursor.execute(sql, values)
        conn.commit()
        
        # get new class entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ? and status = 'partial';" % table_prefix
        mycursor.execute(sql, (uid, class_form_id))
        request = mycursor.fetchone()
        new_class_entry_id = request["eid"]
        
        # add main entry id and class entry id pair into DB
        sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
        mycursor.execute(sql, (main_entry_id, new_class_entry_id))
        conn.commit()
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_ADDING_CLASS_FORMS, e)
        
    except Exception as e:
        print(ErrorCodes.ERROR_ON_ADDING_CLASS_FORMS, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
    
    
    
        
elif content["command"] == "add_sample_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "main_entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["main_entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()
        
        # checking if main form is partial or completed
        sql = "SELECT status FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        mycursor.execute(sql, (uid, main_entry_id))
        request = mycursor.fetchone()
        if request["status"] not in {partial_label, completed_label}:
            print(ErrorCodes.MAIN_FORM_COMPLETED)
            exit()
            
            
            
        field_template = json.loads(open("workflow-templates/sample.json").read())
        field_template["version"] = version
        field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        field_template = json.dumps(field_template)
        
        # add main form entry
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, DATETIME('now'), ?);" % table_prefix
        values = (sample_form_id, uid, partial_label, field_template, user_uuid)
        mycursor.execute(sql, values)
        conn.commit()
        
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ? and status = ?;" % table_prefix
        mycursor.execute(sql, (uid, sample_form_id, partial_label))
        request = mycursor.fetchone()
        new_sample_entry_id = request["eid"]
        
        # add main entry id and sample entry id pair into DB
        sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
        mycursor.execute(sql, (main_entry_id, new_sample_entry_id))
        conn.commit()
            
            
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_ADDING_SAMPLE_FORMS, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_ADDING_SAMPLE_FORMS, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
 
    
################################################################################
## complete partial form
################################################################################  
        
        
        
        
elif content["command"] == "complete_partial_form":
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        # delete old partial entry
        sql = "UPDATE %sentries SET status = ? WHERE id = ? AND user_id = ?;" % table_prefix
        mycursor.execute(sql, (completed_label, entry_id, uid))
        conn.commit()
        
        
        sql = "SELECT form FROM %sentries WHERE id = ? AND user_id = ?;" % table_prefix
        mycursor.execute(sql, (entry_id, uid))
        request = mycursor.fetchone()
        
        
        # add report hash number if necessary
        if request["form"] == main_form_id:
            sql = "SELECT COUNT(*) as cnt FROM %sreports WHERE entry_id = ?;" % table_prefix
            mycursor.execute(sql, (entry_id,))
            request = mycursor.fetchone()["cnt"]
            
            if request == 0:
                hash_value = "%i-%i-%s" % (entry_id, uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                hash_value = hashlib.md5(hash_value.encode()).hexdigest()
                
                sql = "INSERT INTO %sreports (entry_id, hash) VALUES (?, ?);" % table_prefix
                mycursor.execute(sql, (entry_id, hash_value))
                conn.commit()
        
    
    except Error as e:
        print(ErrorCodes.ERROR_ON_DELETING_MAIN_FORM, e)
        
    except Exception as e:
        print(ErrorCodes.ERROR_ON_DELETING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close()
    
    print(0)
    
    
    
    
        
        
   
   
   
   
   
   
        
 
    
################################################################################
## copy forms
################################################################################  


elif content["command"] == "copy_main_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()
            
            
        # get form to copy and update some entries
        sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        mycursor.execute(sql, (uid, main_entry_id))
        request = mycursor.fetchone()
        fields = json.loads(request["fields"])
        fields["current_page"] = 0
        fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fields = json.dumps(fields)
        
        # copy content assigned to entry id
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (partial_label, fields, uid, main_entry_id))
        conn.commit()
        
        
        # retrieve new main entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
        mycursor.execute(sql, (uid, main_form_id))
        request = mycursor.fetchone()
        new_main_entry_id = request["eid"]
        
        
        
        
        # copy all lipid sample forms assigned to old entry
        sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (main_entry_id,))
        sample_form_entry_ids = [row["sample_form_entry_id"] for row in mycursor.fetchall()]
        
        for sample_entry_id in sample_form_entry_ids:
            
            # get form to copy and update some entries
            sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
            mycursor.execute(sql, (uid, sample_entry_id))
            request = mycursor.fetchone()
            fields = json.loads(request["fields"])
            fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fields = json.dumps(fields)
                
                
            # copy content assigned to entry id
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, status, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            mycursor.execute(sql, (fields, uid, sample_entry_id))
            conn.commit()
                
            
            # retrieve new main entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            mycursor.execute(sql, (uid, sample_form_id))
            request = mycursor.fetchone()
            new_sample_entry_id = request["eid"]
            
            
            # add copy of lipid sample form into connetion table
            sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
            mycursor.execute(sql, (new_main_entry_id, new_sample_entry_id))
            conn.commit()
    
    
        
        # copy all lipid class forms assigned to old entry
        sql = "SELECT class_form_entry_id FROM %sconnect_lipid_class WHERE main_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (main_entry_id,))
        class_form_entry_ids = [row["class_form_entry_id"] for row in mycursor.fetchall()]
        
        for class_entry_id in class_form_entry_ids:
            
            # get form to copy and update some entries
            sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
            mycursor.execute(sql, (uid, class_entry_id))
            request = mycursor.fetchone()
            fields = json.loads(request["fields"])
            fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fields = json.dumps(fields)
                
                
            # copy content assigned to entry id
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, status, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            mycursor.execute(sql, (fields, uid, class_entry_id))
            conn.commit()
                
            
            # retrieve new main entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            mycursor.execute(sql, (uid, class_form_id))
            request = mycursor.fetchone()
            new_class_entry_id = request["eid"]
            
            
            # add copy of lipid class form into connetion table
            sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
            mycursor.execute(sql, (new_main_entry_id, new_class_entry_id))
            conn.commit()
            
            
            
            

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        


elif content["command"] == "copy_class_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_CLASS_ENTRY_ID)
        exit()
    try:
        class_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_CLASS_SAMPLE_ID)
        exit()
    if class_entry_id < 0:
        print(ErrorCodes.INVALID_CLASS_SAMPLE_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(class_entry_id, uid, mycursor, "class"):
            print(ErrorCodes.INVALID_CLASS_SAMPLE_ID)
            exit()
            
            
        
            
        # get form to copy and update some entries
        sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        mycursor.execute(sql, (uid, class_entry_id))
        request = mycursor.fetchone()
        fields = json.loads(request["fields"])
        fields["current_page"] = 0
        fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fields = json.dumps(fields)
            
        
        # copy content assigned to entry id
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (partial_label, fields, uid, class_entry_id))
        conn.commit()
            
        
        # retrieve new main entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
        mycursor.execute(sql, (uid, class_form_id))
        request = mycursor.fetchone()
        new_class_entry_id = request["eid"]
        
        
        # get main entry id
        sql = "SELECT main_form_entry_id FROM %sconnect_lipid_class WHERE class_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (class_entry_id,))
        request = mycursor.fetchone()
        main_entry_id = request["main_form_entry_id"]
        
        
        # add copy of lipid class form into connetion table
        sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
        mycursor.execute(sql, (main_entry_id, new_class_entry_id))
        conn.commit()
        
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        


elif content["command"] == "copy_sample_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_SAMPLE_ENTRY_ID)
        exit()
    try:
        sample_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_SAMPLE_ENTRY_ID)
        exit()
    if sample_entry_id < 0:
        print(ErrorCodes.INVALID_SAMPLE_SAMPLE_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(sample_entry_id, uid, mycursor, "sample"):
            print(ErrorCodes.INVALID_SAMPLE_SAMPLE_ID)
            exit()
            
        # get form to copy and update some entries
        sql = "SELECT fields FROM %sentries WHERE user_id = ? AND id = ?;" % table_prefix
        mycursor.execute(sql, (uid, sample_entry_id))
        request = mycursor.fetchone()
        fields = json.loads(request["fields"])
        fields["current_page"] = 0
        fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fields = json.dumps(fields)
            
            
        # copy content assigned to entry id
        sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, ?, ?, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (partial_label, fields, uid, sample_entry_id))
        conn.commit()
            
        
        # retrieve new main entry id
        sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
        mycursor.execute(sql, (uid, sample_form_id))
        request = mycursor.fetchone()
        new_sample_entry_id = request["eid"]
        
        
        # get main entry id
        sql = "SELECT main_form_entry_id FROM %sconnect_sample WHERE sample_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (sample_entry_id, ))
        request = mycursor.fetchone()
        main_entry_id = request["main_form_entry_id"]
        
        
        # add copy of lipid sample form into connetion table
        sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
        mycursor.execute(sql, (main_entry_id, new_sample_entry_id))
        conn.commit()
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        









        
 
    
################################################################################
## delete forms
################################################################################  

elif content["command"] == "delete_class_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        class_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_CLASS_ENTRY_ID)
        exit()
    if class_entry_id < 0: print(ErrorCodes.INVALID_CLASS_ENTRY_ID)
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(class_entry_id, uid, mycursor, "class"):
            print(ErrorCodes.INVALID_CLASS_ENTRY_ID)
            exit()
            
        
        # delete class entry from connection table
        sql = "DELETE FROM %sconnect_lipid_class WHERE class_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (class_entry_id,))
        conn.commit()
        
        # delete class entry
        sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
        mycursor.execute(sql, (class_entry_id, class_form_id, uid))
        conn.commit()
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_DELETING_CLASS_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_DELETING_CLASS_FORM, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)




elif content["command"] == "delete_sample_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        sample_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_SAMPLE_ENTRY_ID)
        exit()
    if sample_entry_id < 0: print(ErrorCodes.INVALID_SAMPLE_ENTRY_ID)
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(sample_entry_id, uid, mycursor, "sample"):
            print(ErrorCodes.INVALID_SAMPLE_ENTRY_ID)
            exit()
            
            
        
        # delete sample entry from connection table
        sql = "DELETE FROM %sconnect_sample WHERE sample_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (sample_entry_id,))
        conn.commit()
        
        # delete sample entry
        sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
        mycursor.execute(sql, (sample_entry_id, sample_form_id, uid))
        conn.commit()
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_DELETING_SAMPLE_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_DELETING_CLASS_FORM, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        
        


elif content["command"] == "delete_main_form":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(main_entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()

        # check status of entry
        sql = "SELECT e.status, r.hash FROM %sentries AS e LEFT JOIN %sreports AS r ON e.id = r.entry_id WHERE e.id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (main_entry_id,))
        results = mycursor.fetchone()
        main_status = results["status"]
        hash_value = results["hash"]
        if main_status not in {partial_label, completed_label}:
            print(0)
            exit()
            
        
        # delete all lipid sample forms assigned to current entry
        sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (main_entry_id,))
        sample_form_entry_ids = [row["sample_form_entry_id"] for row in mycursor.fetchall()]
        
        for sample_form_entry_id in sample_form_entry_ids:
            # delete sample entry from connection table
            sql = "DELETE FROM %sconnect_sample WHERE sample_form_entry_id = ?;" % table_prefix
            mycursor.execute(sql, (sample_form_entry_id,))
            conn.commit()
            
            # delete sample entry
            sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
            mycursor.execute(sql, (sample_form_entry_id, sample_form_id, uid))
            conn.commit()
            
            
        
        # delete all lipid class forms assigned to current entry
        sql = "SELECT class_form_entry_id FROM %sconnect_lipid_class WHERE main_form_entry_id = ?;" % table_prefix
        mycursor.execute(sql, (main_entry_id,))
        class_form_entry_ids = [row["class_form_entry_id"] for row in mycursor.fetchall()]
        
        for class_form_entry_id in class_form_entry_ids:
            # delete class entry from connection table
            sql = "DELETE FROM %sconnect_lipid_class WHERE class_form_entry_id = ?;" % table_prefix
            mycursor.execute(sql, (class_form_entry_id,))
            conn.commit()
            
            # delete class entry
            sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
            mycursor.execute(sql, (class_form_entry_id, class_form_id, uid))
            conn.commit()
            
            
        # delete main entry
        sql = "DELETE FROM %sreports WHERE entry_id = ?;" % table_prefix
        mycursor.execute(sql, (main_entry_id, ))
        conn.commit()
            
            
        # delete main entry
        sql = "DELETE FROM %sentries WHERE id = ? AND form = ? AND user_id = ?;" % table_prefix
        mycursor.execute(sql, (main_entry_id, main_form_id, uid))
        conn.commit()
        
        
        # check if entry in reports exist and delete entry and pdf file
        if hash_value != None:
            for extension in {"aux", "log", "out", "pdf", "tex"}:
                file_to_del = "completed_documents/%s.%s" % (hash_value, extension)
                if os.path.exists(file_to_del):
                    os.remove(file_to_del)
        
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        
        
        
 
    
################################################################################
## remaining commands
################################################################################  


elif content["command"] == "import_class_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    
    if "class_entry_ids" not in content:
        print(ErrorCodes.NO_CLASS_ENTRY_ID)
        exit()
    try:
        import_class_forms = [int(get_decrypted_entry(c_id)) for c_id in content["class_entry_ids"].split("|")]
    except:
        print(ErrorCodes.INVALID_CLASS_ENTRY_ID)
        exit()
    
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        for class_entry_id in import_class_forms:
            if not check_entry_id(class_entry_id, uid, mycursor, "class"):
                print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
                exit()
                
            # import new entry based on old entry
            
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, status, fields, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            mycursor.execute(sql, (uid, class_entry_id))
            conn.commit()
            
            # get new class entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            mycursor.execute(sql, (uid, class_form_id))
            request = mycursor.fetchone()
            new_class_entry_id = request["eid"]
            
            # add main entry id and class entry id pair into DB
            sql = "INSERT INTO %sconnect_lipid_class (main_form_entry_id, class_form_entry_id) VALUES (?, ?);" % table_prefix
            mycursor.execute(sql, (main_entry_id, new_class_entry_id))
            conn.commit()
            

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close() 
        
    print(0)




elif content["command"] == "import_sample_forms":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        main_entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if main_entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    if "sample_entry_ids" not in content:
        print(ErrorCodes.NO_SAMPLE_ENTRY_ID)
        exit()
    try:
        import_sample_forms = [int(get_decrypted_entry(c_id)) for c_id in content["sample_entry_ids"].split("|")]
    except:
        print(ErrorCodes.INVALID_SAMPLE_ENTRY_ID)
        exit()
    
    
    
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        for sample_entry_id in import_sample_forms:
            if not check_entry_id(sample_entry_id, uid, mycursor, "sample"):
                print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
                exit()
            
            # import new entry based on old entry    
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) SELECT form, user_id, status, fields, DATETIME('now'), user_uuid FROM %sentries WHERE user_id = ? and id = ?;" % (table_prefix, table_prefix)
            mycursor.execute(sql, (uid, sample_entry_id))
            conn.commit()
            
            # get new sample entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            mycursor.execute(sql, (uid, sample_form_id))
            request = mycursor.fetchone()
            new_sample_entry_id = request["eid"]
            
            # add main entry id and sample entry id pair into DB
            sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
            mycursor.execute(sql, (main_entry_id, new_sample_entry_id))
            conn.commit()
            
        
        

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
        
        
        
        


elif content["command"] == "get_pdf":
    
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
        
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()
            
        sql = "SELECT hash FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (entry_id, uid))
        hash_value = mycursor.fetchone()["hash"]
        
        pdf_file = "completed_documents/%s.pdf" % hash_value
        
        if not os.path.exists(pdf_file):
            
            # creating the tex and pdf file
            report_file = "completed_documents/%s.tex" % hash_value
            
            create_report.create_report(mycursor, table_prefix, uid, entry_id, report_file, version)
            p = subprocess.Popen("/usr/bin/lualatex -output-directory=completed_documents completed_documents/%s.tex" % hash_value, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
            
            output = p.stdout.read() # execution
            
            if os.path.exists(pdf_file):
                print("/%s/%s" % (path_name, pdf_file))
            
            else:
                print(str(output))
            
        else:
            print("/%s/%s" % (path_name, pdf_file))

    except Error as e:
        print(ErrorCodes.ERROR_ON_CREATING_PDF, e)
        
    except Exception as e:
        print(ErrorCodes.ERROR_ON_CREATING_PDF, e)

    finally:
        if conn is not None: conn.close()
        
        

        
        
        
    
    
        

        
        


elif content["command"] == "publish":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    
    try:
        # connect with the database
        conn, mycursor = dbconnect()
        
        if not check_entry_id(entry_id, uid, mycursor, "main"):
            print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
            exit()
        
        # set status of entry to published
        sql = "UPDATE %sentries SET status = ? WHERE id = ? AND status = ?;" % table_prefix
        mycursor.execute(sql, (published_label, entry_id, completed_label))
        conn.commit()
            
    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)
            
    except Exception as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close()
            
    print(0)
        
        
        
        
        
        
        
        
        
        
elif content["command"] == "get_form_content":
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
    if entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
        
    try:
        # connect with the database
        conn, mycursor = dbconnect()

        sql = "SELECT fields FROM %sentries WHERE id = ?;" % table_prefix
        mycursor.execute(sql, (entry_id,))
        print(mycursor.fetchone()["fields"])

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM)

    finally:
        if conn is not None: conn.close()
        
        
        
        
        
        
        
        
        
        
elif content["command"] == "update_form_content":
    
    if "user_uuid" not in content or "uid" not in content:
        print(ErrorCodes.NO_USER_UUID)
        exit()
        
    if "content" not in content:
        print(ErrorCodes.NO_CONTENT)
        exit()
        
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
        
    
    user_uuid = content["user_uuid"]
    uid = int(content["uid"])
    try:
        form_content = unquote(base64.b64decode(content["content"]).decode("utf-8"))
        
    except Exception as e:
        print(ErrorCodes.ERROR_ON_DECODING_FORM, e)
        exit()
    
    
    # check if main form entry id is within the request and an integer
    if "entry_id" not in content:
        print(ErrorCodes.NO_MAIN_ENTRY_ID)
        exit()
    try:
        entry_id = int(get_decrypted_entry(content["entry_id"]))
    except:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
        
    if entry_id < 0:
        print(ErrorCodes.INVALID_MAIN_ENTRY_ID)
        exit()
        
        
        
    try:
        # connect with the database
        conn, mycursor = dbconnect()

        sql = "UPDATE %sentries SET fields = ? WHERE id = ? AND user_id = ?;" % table_prefix
        mycursor.execute(sql, (form_content, entry_id, uid))
        conn.commit()
        
        
        # if updating completed main form, pdf must be deleted if present
        sql = "SELECT COUNT(*) as count_entries FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
        mycursor.execute(sql, (entry_id, uid))
        
        
        
        if mycursor.fetchone()["count_entries"] > 0:
            sql = "SELECT hash FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
            mycursor.execute(sql, (entry_id, uid))
            pdf_file = "completed_documents/%s.pdf" % mycursor.fetchone()["hash"]
            if os.path.isfile(pdf_file): os.remove(pdf_file)
                

    except Error as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    except Exception as e:
        print(ErrorCodes.ERROR_ON_REUSING_MAIN_FORM, e)

    finally:
        if conn is not None: conn.close()
        
    print(0)
