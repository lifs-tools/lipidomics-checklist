
try:    
    import sys
    import os
    from json import loads as json_loads
    from json import dumps as json_dumps
    import pysodium
    from base64 import b64decode, b64encode
    from datetime import datetime
    from urllib.parse import unquote
    from random import randint
    import db.ChecklistConfig as cfg
    from FormsEnum import *
    from datetime import datetime
    import traceback
        
    def dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


    all_commands = {"get_main_forms", "get_class_forms", "get_sample_forms",
                    "add_main_form", "add_class_form", "add_sample_form",
                    "copy_main_form", "copy_class_form", "copy_sample_form",
                    "delete_main_form", "delete_class_form", "delete_sample_form",
                    "delete_selected_class_forms", "delete_selected_sample_forms",
                    "get_all_class_forms", "get_all_sample_forms",
                    "import_class_forms", "import_sample_forms",
                    "complete_partial_form",
                    "export_report", "import_report",
                    "get_pdf", "publish", "get_public_link",
                    "get_form_content", "update_form_content",
                    "export_samples", "export_selected_samples", "import_samples",
                    "export_lipid_class", "export_selected_lipid_classes", "import_lipid_class",
                    "get_fragment_suggestions", "get_published_forms", "get_current_version"}
    
    conn = None
    table_prefix = "TCrpQ_"
    version = cfg.version

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


    def copy_form(original_form, new_form):
        original_fields = {}
        
        def fill_fields(form, original_fields):
            if type(form) == list:
                for element in form: fill_fields(element, original_fields)
            elif type(form) == dict:
                if "name" in form: original_fields[form["name"]] = form
                for k, v in form.items():
                    fill_fields(v, original_fields)

        fill_fields(original_form, original_fields)
        
        def copy_fields(form, original_fields):
            if type(form) == list:
                for element in form: copy_fields(element, original_fields)
            elif type(form) == dict:
                if "name" in form:
                    form_name = form["name"]
                    if form_name in original_fields:
                        orig_field = original_fields[form_name]
                        if (("type" not in form and "type" not in orig_field) or form["type"] == orig_field["type"]) and "value" in form and "value" in orig_field:
                            form["value"] = orig_field["value"]
                        
                for k, v in form.items():
                    copy_fields(v, original_fields)
                    
        copy_fields(new_form, original_fields)
        


    def dbconnect():
        try:
            from sqlite3 import connect as sqlite3_connect
            conn = sqlite3_connect(cfg.db_file)
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
            message = bytes(str(entry_id), 'utf-8')
            nonce = pysodium.randombytes(pysodium.crypto_stream_NONCEBYTES)
            key = b64decode(cfg.encryption_key)
            
            
            cipher = nonce + pysodium.crypto_secretbox(message, nonce, key)
            return str(b64encode(cipher), "utf-8")

        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in get_encrypted_entry", e)

        finally:
            if conn is not None: conn.close()





    def get_decrypted_entry(entry_id):
        conn, db_cursor = dbconnect()
        try:
            message = bytes(str(entry_id), 'utf-8')
            key = b64decode(cfg.encryption_key)
            decoded_entry_id = b64decode(entry_id)
            
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
            sql = "SELECT status, id, date, fields, 1 owner  FROM %sentries WHERE form = ? AND user_id = ?;" % table_prefix
            db_cursor.execute(sql, (main_form_id, uid))
            request = db_cursor.fetchall()
            
            
            # check if forms are shared
            # sql = "SELECT e.status, e.id, e.date, e.fields, 0 owner FROM %sentries e INNER JOIN %sshares s ON e.id = s.report_entry_id WHERE e.form = ? AND s.shared_user_id = ?;" % (table_prefix, table_prefix)
            # db_cursor.execute(sql, (main_form_id, uid))
            # request += db_cursor.fetchall()
            
            type_to_name = {"di": "direct infusion", "sep": "separation", "img": "imaging"}
            for entry in request:
                entry["entry_id"] = get_encrypted_entry(entry["id"])
                title = ""
                entry["type"] = ""
                entry["version"] = ""
                if len(entry["fields"]) > 0:
                    field_data = json_loads(entry["fields"])
                    del entry["fields"]
                    
                    if "version" in field_data: entry["version"] = field_data["version"]
                    
                    if len(field_data) > 0:
                        for field in field_data["pages"][0]["content"]:
                            if "label" in field and field["label"] == "Title of the study" and len(field["value"]) > 0:
                                title = field["value"]
                                
                            elif "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                                entry["type"] = field["value"]
                                
                
                if len(title) == 0: entry["title"] = "Untitled %s report" % (type_to_name[entry["type"]] if entry["type"] in type_to_name else "")
                else: entry["title"] = title
                entry["type"] = (type_to_name[entry["type"]] if entry["type"] in type_to_name else "").capitalize()
            
                
            request.sort(key = lambda x: x["date"], reverse = True)
            for entry in request:
                try:
                    entry["date"] = datetime.fromisoformat(entry["date"]).strftime('%m/%d/%Y')
                    if len(entry["version"]) > 0: entry["date"] += " (%s)" % entry["version"]
                except Exception as e:
                    pass
            
            print(json_dumps(request))
            
        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_GETTING_MAIN_FORMS) + " in %s" % content["command"], e)

        finally:
            if conn is not None: conn.close()
            
            
            
            
            


    if content["command"] == "get_published_forms":
        
        if "user_uuid" not in content or "uid" not in content:
            print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
            exit()
        user_uuid = content["user_uuid"]
        uid = int(content["uid"])
        type_to_name = {"di": "direct infusion", "sep": "separation", "img": "imaging"}
        
        try:
            # connect with the database
            conn, db_cursor = dbconnect()
            
            # getting all main forms
            sql = "SELECT id, date, fields FROM %sentries WHERE status = 'published';" % table_prefix
            db_cursor.execute(sql)
            request = db_cursor.fetchall()
            for entry in request:
                entry["entry_id"] = get_encrypted_entry(entry["id"])
                del entry["id"]
                entry["type"] = ""
                entry["author"] = ""
                title = ""
                if len(entry["fields"]) > 0:
                    field_data = json_loads(entry["fields"])
                    del entry["fields"]
                    
                    if len(field_data) > 0:
                        for field in field_data["pages"][0]["content"]:
                            if "label" in field and field["label"] == "Title of the study" and len(field["value"]) > 0:
                                title = field["value"]
                                
                            elif "name" in field and field["name"] == "principle_investigator" and len(field["value"]) > 0:
                                entry["author"] = field["value"]
                                
                            elif "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                                entry["type"] = field["value"]
                                
                
                if len(title) == 0: entry["title"] = "Untitled %s report" % (type_to_name[entry["type"]] if entry["type"] in type_to_name else "")
                else: entry["title"] = title
                entry["type"] = (type_to_name[entry["type"]] if entry["type"] in type_to_name else "").capitalize()
                
            request.sort(key = lambda x: x["date"], reverse = True)
            print(json_dumps(request))
            
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
                    field_data = json_loads(entry["fields"])
                    del entry["fields"]
                    
                    lipid_class, other_lipid_class, ion_type, pos_ion, neg_ion = "", "", "", "", ""
                    other_pos_ion, other_neg_ion = "", ""
                    
                    if len(field_data) > 0:
                        for field in field_data["pages"][0]["content"]:
                            lipid_class = get_select_value(field, "Lipid class", lipid_class)
                            pos_ion = get_select_value(field, "Type of positive (precursor)ion", pos_ion)
                            neg_ion = get_select_value(field, "Type of negative (precursor)ion", neg_ion)
                            ion_type = get_select_value(field, "Polarity mode", ion_type)
                            
                            if "name" in field and field["name"] == "other_lipid_class" and "value" in field and len(field["value"]) > 0:
                                other_lipid_class = field["value"]
                                
                            if "name" in field and field["name"] == "other_pos_ion" and "value" in field and len(field["value"]) > 0:
                                other_pos_ion = field["value"]
                                
                            if "name" in field and field["name"] == "other_neg_ion" and "value" in field and len(field["value"]) > 0:
                                other_neg_ion = field["value"]
                                
                    if len(other_pos_ion) > 0: pos_ion = other_pos_ion
                    if len(other_neg_ion) > 0: neg_ion = other_neg_ion
                                    
                    if lipid_class[:5].lower() == "other": lipid_class = other_lipid_class
                    ion = pos_ion if ion_type.lower() == "positive" else neg_ion
                entry["title"] = "%s%s" % (lipid_class, ion)
            print(json_dumps(request))

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
                    field_data = json_loads(entry["fields"])
                    del entry["fields"]
                    
                    if len(field_data) > 0:
                        for field in field_data["pages"][0]["content"]:
                            if "label" in field and field["label"] == "Sample set name" and "value" in field and len(field["value"]) > 0:
                                sample_set = field["value"]
                                
                            sample_type = get_select_value(field, "Sample type", sample_type)
                if len(sample_type) > 0 and len(sample_set) > 0:
                    entry["title"] = "%s / %s" % (sample_set, sample_type)
            print(json_dumps(request))

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
                    field_data = json_loads(entry["main_fields"])
                    if len(field_data) > 0:
                        for field in field_data["pages"][0]["content"]:
                            if "label" in field and field["label"] == "Title of the study" and len(field["value"]) > 0:
                                entry["main_title"] = field["value"]
                    del entry["main_fields"]
                
                title = ["Unspecified class", "[M]", "No Instrument"]
                if len(entry["fields"]) > 0:
                    field_data = json_loads(entry["fields"])
                    
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
            
        print(json_dumps(request))





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
                    field_data = json_loads(entry["main_fields"])
                    
                    if len(field_data) > 0:
                        for field in field_data["pages"][0]["content"]:
                            if "label" in field and field["label"] == "Title of the study" and len(field["value"]) > 0:
                                entry["main_title"] = field["value"]
                    
                del entry["main_fields"]
                
                if len(entry["fields"]) > 0:
                    field_data = json_loads(entry["fields"])
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
            print(json_dumps(request))
            
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
            
            field_template = json_loads(open("workflow-templates/checklist.json").read())
            if "pages" in field_template and len(field_template["pages"]) > 0:
                for field in field_template["pages"][0]["content"]:
                    if field["type"] == "hidden":
                        field["value"] = workflow_type
                        break
                field_template["version"] = version
            field_template = json_dumps(field_template)
            
            
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
                
                
            field_data = json_loads(request["fields"])
            workflow_type = ""
            for field in field_data["pages"][0]["content"]:
                if "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                    workflow_type = field["value"]
            
            
            field_template = json_loads(open("workflow-templates/lipid-class.json").read())
            if "pages" in field_template and len(field_template["pages"]) > 0:
                for field in field_template["pages"][0]["content"]:
                    if field["type"] == "hidden":
                        field["value"] = workflow_type
                        break
                field_template["version"] = version
                field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            field_template = json_dumps(field_template)
            
            
            
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

            field_data = json_loads(request["fields"])
            workflow_type = ""
            for field in field_data["pages"][0]["content"]:
                if "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                    workflow_type = field["value"]
                
            field_template = json_loads(open("workflow-templates/sample.json").read())
            if "pages" in field_template and len(field_template["pages"]) > 0:
                for field in field_template["pages"][0]["content"]:
                    if field["type"] == "hidden":
                        field["value"] = workflow_type
                        break
            field_template["version"] = version
            field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            field_template = json_dumps(field_template)
            
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
            fields_orig = json_loads(request["fields"])
            
            workflow_type = "di"
            
            if "pages" in fields_orig and len(fields_orig["pages"]) > 0:
                for field in fields_orig["pages"][0]["content"]:
                    if field["type"] == "hidden":
                        workflow_type = field["value"]
                        break
            
            fields = json_loads(open("workflow-templates/checklist.json").read())
            if "pages" in fields and len(fields["pages"]) > 0:
                for field in fields["pages"][0]["content"]:
                    if field["type"] == "hidden":
                        field["value"] = workflow_type
                        break
                fields["version"] = version            
                
            copy_form(fields_orig, fields)
            
            fields["current_page"] = 0
            fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fields = json_dumps(fields)
            
            
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
                fields_orig = json_loads(request["fields"])
                fields = json_loads(open("workflow-templates/sample.json").read())
                copy_form(fields_orig, fields)
                fields["current_page"] = 0
                fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                fields = json_dumps(fields)
                    
                    
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
                fields_orig = json_loads(request["fields"])
                fields = json_loads(open("workflow-templates/lipid-class.json").read())
                copy_form(fields_orig, fields)
                fields["current_page"] = 0
                fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                fields = json_dumps(fields)
                    
                    
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
            fields_orig = json_loads(request["fields"])
            fields = json_loads(open("workflow-templates/lipid-class.json").read())
            copy_form(fields_orig, fields)
            fields["current_page"] = 0
            fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fields = json_dumps(fields)
                
            
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
            fields_orig = json_loads(request["fields"])
            fields = json_loads(open("workflow-templates/sample.json").read())
            copy_form(fields_orig, fields)
            fields["current_page"] = 0
            fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fields = json_dumps(fields)
                
                
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
            
        if class_entry_id < 0:
            print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
            exit()
        
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
        
        
        
        
        
        
        
        
          

    elif content["command"] == "delete_selected_class_forms":
        if "user_uuid" not in content or "uid" not in content:
            print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
            exit()
        user_uuid = content["user_uuid"]
        uid = int(content["uid"])
        
        # check if main form entry id is within the request and an integer
        if "entry_ids" not in content:
            print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
        try:
            class_entry_ids = [int(get_decrypted_entry(entry_id)) for entry_id in content["entry_ids"].split(";")]
        except:
            print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        if len(class_entry_ids) == 0:
            print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        for class_entry_id in class_entry_ids:
            if class_entry_id < 0:
                print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
                exit()
        
        try:
            # connect with the database
            conn, db_cursor = dbconnect()
            
            for class_entry_id in class_entry_ids:
                if not check_entry_id(class_entry_id, uid, db_cursor, "class"):
                    print(str(ErrorCodes.INVALID_CLASS_ENTRY_ID) + " in %s" % content["command"])
                    exit()
            
                # checking if class form is partial or completed
                status, request = check_status(class_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
                
            
            for class_entry_id in class_entry_ids:
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
            print(str(ErrorCodes.NO_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
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
        
        
        
        
        
        
        






    elif content["command"] == "delete_selected_sample_forms":
        if "user_uuid" not in content or "uid" not in content:
            print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
            exit()
        user_uuid = content["user_uuid"]
        uid = int(content["uid"])
        
        # check if main form entry id is within the request and an integer
        if "entry_ids" not in content:
            print(str(ErrorCodes.NO_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
            exit()
        try:
            sample_entry_ids = [int(get_decrypted_entry(entry_id)) for entry_id in content["entry_ids"].split(";")]
        except:
            print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        if len(sample_entry_ids) == 0:
            print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
            exit()
        
        for sample_entry_id in sample_entry_ids:
            if sample_entry_id < 0:
                print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
                exit()
        
        try:
            # connect with the database
            conn, db_cursor = dbconnect()
            
            for sample_entry_id in sample_entry_ids:
                if not check_entry_id(sample_entry_id, uid, db_cursor, "sample"):
                    print(str(ErrorCodes.INVALID_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
                    exit()
                    
                    
                # checking if sample form is partial or completed
                status, request = check_status(sample_entry_id, uid, db_cursor, not_in = {partial_label, completed_label})
                
            for sample_entry_id in sample_entry_ids:  
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
            
            
            sql = "SELECT * FROM %sentries WHERE id = ?;" % table_prefix
            db_cursor.execute(sql, (entry_id,))
            status = db_cursor.fetchone()["status"]
            
            if status != published_label and not check_entry_id(entry_id, uid, db_cursor, "main"):
                print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
                exit()
                
            if status != published_label:
                sql = "SELECT hash FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ? AND e.user_id = ?;" % (table_prefix, table_prefix)
                db_cursor.execute(sql, (entry_id, uid))
            else:
                sql = "SELECT hash FROM %sreports AS r JOIN %sentries AS e ON r.entry_id = e.id WHERE e.id = ?;" % (table_prefix, table_prefix)
                db_cursor.execute(sql, (entry_id,))
                
            try:
                hash_value = db_cursor.fetchone()["hash"]
            except:
                print("ErrorCodes.NO_DOCUMENT: It seems that this report is published but no document is created.")
                exit()
            
            
            pdf_file = "completed_documents/report-%s.pdf" % hash_value
            
            if not os.path.exists(pdf_file):
                
                if status == published_label:
                    print("ErrorCodes.NO_DOCUMENT: It seems that this report is published but no document is created.")
                    exit()
                
                import subprocess
                import CreateReport
                
                # creating the tex and pdf file
                report_file = "completed_documents/report-%s.tex" % hash_value
                
                CreateReport.create_report(db_cursor, table_prefix, uid, entry_id, report_file)
                p = subprocess.Popen("./latexmk -pdflatex=lualatex -pdf -output-directory=completed_documents %s" % report_file, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, close_fds = True)
                
                output = p.stdout.read() # execution
                
                
                if os.path.exists(pdf_file):
                    print("/%s/%s" % (path_name, pdf_file))
                
                else:
                    print(str(output))
                
            else:
                print("/%s/%s" % (path_name, pdf_file))

        except Exception as e:
            import traceback
            ee = (''.join(traceback.format_tb(e.__traceback__)))
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
                
            import warnings
            warnings.filterwarnings("ignore")
            import requests
                
                
            # checking if main form is partial or completed
            status, request = check_status(entry_id, uid, db_cursor, is_in = {partial_label, published_label})
            
            
            fields = json_loads(request["fields"])
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
                    print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], json_dumps(r.json())))
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
                r = requests.put('https://%s/api/deposit/depositions/%s' % (cfg.zenodo_link, record_id), params = params, data=json_dumps(data), headers=headers, timeout = 15)
                
                if r.status_code != 200:
                    print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], json_dumps(r.json())))
                    exit()
                
            except:
                print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], publishing_error_code))
                exit()


            try:
                publishing_error_code = "Error during Zenodo publication"
                r = requests.post('https://%s/api/deposit/depositions/%s/actions/publish' % (cfg.zenodo_link, record_id), params = params, timeout = 15)
                
                if r.status_code != 202:
                    print("%s %s" % (str(ErrorCodes.PUBLISHING_FAILED) + " in %s" % content["command"], json_dumps(r.json())))
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
            form_content = unquote(b64decode(content["content"]).decode("utf-8"))
            
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
            
            if form_type == FormType.SAMPLE:
                sql = "SELECT e.fields FROM %sentries AS e INNER JOIN %sconnect_sample AS s ON e.id = s.sample_form_entry_id WHERE s.main_form_entry_id = ? and e.user_id = ?;" % (table_prefix, table_prefix)
                template_file = "workflow-templates/sample.json"
                sheet_name = "Sample forms"
            
            else:
                sql = "SELECT e.fields FROM %sentries AS e INNER JOIN %sconnect_lipid_class AS s ON e.id = s.class_form_entry_id WHERE s.main_form_entry_id = ? and e.user_id = ?;" % (table_prefix, table_prefix)
                template_file = "workflow-templates/lipid-class.json"
                sheet_name = "Lipid class forms"
                
            db_cursor.execute(sql, (entry_id, uid))
            fields = [row["fields"] for row in db_cursor.fetchall()]
            from ImportExportForms import export_forms_to_worksheet
            worksheet_base64 = export_forms_to_worksheet(template_file, fields, sheet_name)
            print("data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,%s" % worksheet_base64)
            
        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_EXPORTING_FORMS) + " in %s" % content["command"], e)

        finally:
            if conn is not None: conn.close()
            



    




    elif content["command"] in {"export_selected_samples", "export_selected_lipid_classes"}:
        if "user_uuid" not in content or "uid" not in content:
            print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
            exit()
        user_uuid = content["user_uuid"]
        uid = int(content["uid"])
        # check if main form entry id is within the request and an integer

        if "report_entry_id" not in content:
            print(str(ErrorCodes.NO_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
        try:
            report_entry_id = int(get_decrypted_entry(content["report_entry_id"]))
        except:
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        if report_entry_id < 0:
            print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        form_type = FormType.LIPID_CLASS if content["command"] == "export_selected_lipid_classes" else FormType.SAMPLE
        
        dyn_field_name = "sample_entry_ids" if form_type == FormType.SAMPLE else "lipid_class_entry_ids"
        if dyn_field_name not in content:
            print(str(ErrorCodes.NO_SAMPLE_ENTRY_ID) + " in %s" % content["command"])
            exit()
            
        field_entry_ids = {int(get_decrypted_entry(entry_id)) for entry_id in content[dyn_field_name].split(";")}
        
        for field_entry_id in field_entry_ids:
            if field_entry_id < 0:
                print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
                exit()
        
        
        try:
            # connect with the database
            conn, db_cursor = dbconnect()
            
            if not check_entry_id(report_entry_id, uid, db_cursor, "main"):
                print(str(ErrorCodes.INVALID_MAIN_ENTRY_ID) + " in %s" % content["command"])
                exit()
                
            
            if form_type == FormType.SAMPLE:
                sql = "SELECT e.id, e.fields FROM %sentries AS e INNER JOIN %sconnect_sample AS s ON e.id = s.sample_form_entry_id WHERE s.main_form_entry_id = ? and e.user_id = ?;" % (table_prefix, table_prefix)
                template_file = "workflow-templates/sample.json"
                sheet_name = "Sample forms"
            
            else:
                sql = "SELECT e.id, e.fields FROM %sentries AS e INNER JOIN %sconnect_lipid_class AS s ON e.id = s.class_form_entry_id WHERE s.main_form_entry_id = ? and e.user_id = ?;" % (table_prefix, table_prefix)
                template_file = "workflow-templates/lipid-class.json"
                sheet_name = "Lipid class forms"
                
            db_cursor.execute(sql, (report_entry_id, uid))
            fields = [row["fields"] for row in db_cursor.fetchall() if row["id"] in field_entry_ids]
            from ImportExportForms import export_forms_to_worksheet
            worksheet_base64 = export_forms_to_worksheet(template_file, fields, sheet_name)
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

            workflow_type = ""
            field_data = json_loads(request["fields"])
            for field in field_data["pages"][0]["content"]:
                if "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                    workflow_type = field["value"]
                
            
            from ImportExportForms import import_forms_from_worksheet
            imported_forms = import_forms_from_worksheet("workflow-templates/sample.json", worksheet_base64)
            
            # all complete
            if sum(form[1] for form in imported_forms) == len(imported_forms) or force_upload:
                for field_template, is_complete in imported_forms:
                    if "pages" in field_template and len(field_template["pages"]) > 0:
                        for field in field_template["pages"][0]["content"]:
                            if field["type"] == "hidden":
                                field["value"] = workflow_type
                                break
                        field_template["version"] = version
                        field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    field_template = json_dumps(field_template)
                    
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
                print("Warning: the entries with following IDs are incomplete: %s" % ", ".join(str(i + 1) for i, form in enumerate(imported_forms) if not form[1]))
                    
            
            
        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_IMPORTING_FORMS) + " in %s" % content["command"], e)

        finally:
            if conn is not None: conn.close()
            
        
        
        
        
        
        
        
        
        
        
        
        
    elif content["command"] == "import_lipid_class":
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
            
            workflow_type = ""
            field_data = json_loads(request["fields"])
            for field in field_data["pages"][0]["content"]:
                if "name" in field and field["name"] == "workflowtype" and len(field["value"]) > 0:
                    workflow_type = field["value"]
                
            
            from ImportExportForms import import_forms_from_worksheet
            imported_forms = import_forms_from_worksheet("workflow-templates/lipid-class.json", worksheet_base64)
            
            # all complete
            if sum(form[1] for form in imported_forms) == len(imported_forms) or force_upload:
                for field_template, is_complete in imported_forms:
                    if "pages" in field_template and len(field_template["pages"]) > 0:
                        for field in field_template["pages"][0]["content"]:
                            if field["type"] == "hidden":
                                field["value"] = workflow_type
                                break
                        field_template["version"] = version
                        field_template["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    field_template = json_dumps(field_template)
                    
                    status_label = completed_label if is_complete else partial_label
                    
                    # add main form entry
                    sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, DATETIME('now'), ?);" % table_prefix
                    values = (class_form_id, uid, status_label, field_template, user_uuid)
                    db_cursor.execute(sql, values)
                    conn.commit()
                    
                    # get new class entry id
                    sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ? and status = ?;" % table_prefix
                    db_cursor.execute(sql, (uid, class_form_id, status_label))
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
                
                print(0)
                
            else:
                print("Warning: the entries with following IDs are incomplete: %s" % ", ".join(str(i + 1) for i, form in enumerate(imported_forms) if not form[1]))
                    
            
            
        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_IMPORTING_FORMS) + " in %s" % content["command"], e)

        finally:
            if conn is not None: conn.close()
            
            
            
            
            
            
            
    elif content["command"] == "get_fragment_suggestions":
        
        if "lipid_class_name" not in content or "polarity" not in content:
            print(str(ErrorCodes.NO_CONTENT) + " in %s" % content["command"])
            exit()
            
    
        lipid_class_name = content["lipid_class_name"]
        polarity_positive = content["polarity"] == "Positive"
        adduct = None if "adduct" not in content else content["adduct"]
        
        from pandas import read_csv
        df = read_csv("db/ms2fragments.csv")
        
        
        def clean_fragment(fragment, adduct):
            fragment = fragment.replace("[adduct]", adduct)
            fragment = fragment.replace(" [xx:x]", "1")
            fragment = fragment.replace(" [yy:y]", "2")
            fragment = fragment.replace(" [zz:z]", "3")
            fragment = fragment.replace(" [aa:a]", "4")
            return fragment.replace(" [xx:x;x]", "")
    
        
        if polarity_positive:
            fragments = list(df[(df["class"] == lipid_class_name) & (df["charge"] > 0)]["nameafter"])
        else: 
            fragments = list(df[(df["class"] == lipid_class_name) & (df["charge"] < 0)]["nameafter"])
            
        if adduct and adduct[:2] == "[M" and (adduct[-2] == "]" or adduct[-3] == "]"):
            adduct = adduct[2:]
            if adduct[-2] == "]": adduct = adduct[:-2]
            elif adduct[-3] == "]": adduct = adduct[:-3]
            fragments = [clean_fragment(fragment, adduct) for fragment in fragments]
            
        print(json_dumps(fragments))
            
            
            
            
            
            
            
            
            

    
    elif content["command"] == "export_report":
        
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
                
                
            sql = "SELECT fields FROM %sentries WHERE id = ?;" % table_prefix
            db_cursor.execute(sql, (entry_id,))
            checklist = json_loads(db_cursor.fetchone()["fields"])
            samples, lipid_classes = [], []
            
            
            # get all IDs of the assiciated sample entries
            sql = "SELECT sample_form_entry_id FROM %sconnect_sample WHERE main_form_entry_id = ?;" % table_prefix
            db_cursor.execute(sql, (entry_id,))
            sample_form_entry_ids = [row["sample_form_entry_id"] for row in db_cursor.fetchall()]
            
            for sample_form_entry_id in sample_form_entry_ids:
                sql = "SELECT fields FROM %sentries WHERE id = ?;" % table_prefix
                db_cursor.execute(sql, (sample_form_entry_id,))
                samples.append(json_loads(db_cursor.fetchone()["fields"]))
                
                
            # get all IDs of the assiciated lipid class entries
            sql = "SELECT class_form_entry_id FROM %sconnect_lipid_class WHERE main_form_entry_id = ?;" % table_prefix
            db_cursor.execute(sql, (entry_id,))
            class_form_entry_ids = [row["class_form_entry_id"] for row in db_cursor.fetchall()]
            
            for class_form_entry_id in class_form_entry_ids:
                sql = "SELECT fields FROM %sentries WHERE id = ?;" % table_prefix
                db_cursor.execute(sql, (class_form_entry_id,))
                lipid_classes.append(json_loads(db_cursor.fetchone()["fields"]))
            
            
            report = {"checklist": checklist, "samples": samples, "lipid_classes": lipid_classes}
            
            b = b64encode(bytes(json_dumps(report).replace(" {", "\n{"), 'utf-8'))
            print("data:application/json;base64,%s" % b.decode('utf-8'))
            
            
        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_EXPORTING_REPORT) + " in %s" % content["command"], e)
            
            
            
            
            
            
            
            

    
    elif content["command"] == "import_report":
        
        if "user_uuid" not in content or "uid" not in content:
            print(str(ErrorCodes.NO_USER_UUID) + " in %s" % content["command"])
            exit()
        user_uuid = content["user_uuid"]
        uid = int(content["uid"])
        
        try:
            form_content = unquote(b64decode(content["content"]).decode("utf-8"))
            form_content = json_loads(form_content)
            f = form_content["checklist"]
            
        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_DECODING_FORM) + " in %s" % content["command"], e)
            exit()
            
        
        from ImportExportForms import import_form_from_file
        
        checklist, completed = import_form_from_file(form_content["checklist"], FormType.CHECKLIST, version)
        samples, lipid_classes = [], []
        if "samples" in form_content:        
            for form_sample in form_content["samples"]:
                sample, compl = import_form_from_file(form_sample, FormType.SAMPLE, version)
                samples.append([sample, compl])
                completed &= compl
                if not compl: checklist["max_page"] = min(checklist["max_page"], 1)
                
        if "lipid_classes" in form_content:
            for form_lipid_class in form_content["lipid_classes"]:
                lipid_class, compl = import_form_from_file(form_lipid_class, FormType.LIPID_CLASS, version)
                lipid_classes.append([lipid_class, compl])
                completed &= compl
                if not compl: checklist["max_page"] = min(checklist["max_page"], 4)
        
        
        try:
            # connect with the database
            conn, db_cursor = dbconnect()
            
            # importing checklist and all associated sample and lipid class forms
            # get form to copy and update some entries
            checklist["current_page"] = 0
            checklist["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            checklist = json_dumps(checklist)
            
            
            # insert content into the db
            sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, DATETIME('now'), ?);" % table_prefix
            values = (main_form_id, uid, completed_label if completed else partial_label, checklist, user_uuid)
            db_cursor.execute(sql, values)
            conn.commit()
            
            # retrieve new main entry id
            sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
            db_cursor.execute(sql, (uid, main_form_id))
            request = db_cursor.fetchone()
            new_main_entry_id = request["eid"]
            
            
            # add hash value, when report is completed
            if completed:
                while True:
                    hash_value = chr(randint(97, 122)) + chr(randint(97, 122)) + "".join(str(randint(0, 9)) for i in range(8))
                    
                    sql = "SELECT COUNT(*) AS cnt FROM %sreports WHERE hash = ?;" % table_prefix
                    db_cursor.execute(sql, (hash_value,))
                    if db_cursor.fetchone()["cnt"] == 0: break
                
                sql = "INSERT INTO %sreports (entry_id, hash, DOI) VALUES (?, ?, '');" % table_prefix
                db_cursor.execute(sql, (new_main_entry_id, hash_value))
                conn.commit()
            
            
            
            
            for sample_fields, compl in samples:
                sample_fields["current_page"] = 0
                sample_fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sample_fields = json_dumps(sample_fields)
                
                # insert sample entries into the db
                sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, DATETIME('now'), ?);" % table_prefix
                values = (sample_form_id, uid, completed_label if compl else partial_label, sample_fields, user_uuid)
                db_cursor.execute(sql, values)
                conn.commit()
                
                # retrieve new sample entry id
                sql = "SELECT max(id) as eid FROM %sentries WHERE user_id = ? and form = ?;" % table_prefix
                db_cursor.execute(sql, (uid, sample_form_id))
                request = db_cursor.fetchone()
                new_sample_entry_id = request["eid"]
                
                
                # add copy of lipid sample form into connetion table
                sql = "INSERT INTO %sconnect_sample (main_form_entry_id, sample_form_entry_id) VALUES (?, ?);" % table_prefix
                db_cursor.execute(sql, (new_main_entry_id, new_sample_entry_id))
                conn.commit()
            
            
            
            
            for class_fields, compl in lipid_classes:
                class_fields["current_page"] = 0
                class_fields["creation_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                class_fields = json_dumps(class_fields)
                
                # insert sample entries into the db
                sql = "INSERT INTO %sentries (form, user_id, status, fields, date, user_uuid) VALUES (?, ?, ?, ?, DATETIME('now'), ?);" % table_prefix
                values = (class_form_id, uid, completed_label if compl else partial_label, class_fields, user_uuid)
                db_cursor.execute(sql, values)
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
                
            print(0)
            
            
        except Exception as e:
            print(str(ErrorCodes.ERROR_ON_EXPORTING_REPORT) + " in %s" % content["command"], e)
        
        
        
    
    elif content["command"] == "get_current_version":
        print(cfg.version)
            
except Exception as e:
    print("ErrorCodes.GENERIC", traceback.format_exc().replace("\n", "  "))
