var connector_path = "/lipidomics-checklist";
var lipidomics_forms_content = null;
var field_map = {};
var dom_field_map = {};
var field_conditions = {};
var field_visible = {};
var form_pages = [];
var dom_form_pages = [];
var current_page = 0;
var required_messages = {};
var dom_text_fields = {};
var form_enabled = true;
var entry_id = null;
var workflow_type = null;
var choice_to_field = {};

function load_data(content){
    lipidomics_forms_content = content;
    field_map = {};
    dom_field_map = {};
    field_conditions = {};
    field_visible = {};
    form_pages = [];
    dom_form_pages = [];
    current_page = lipidomics_forms_content["current_page"];
    required_messages = {};
    dom_text_fields = {};
    choice_to_field = {};
    
    form_enabled = true;
    
    if (workflow_type == "sample"){
        //document.getElementById("back_button").innerHTML = "Save & Back to Sample Overview";
        document.getElementById("back_button").innerHTML = "Back to Sample Overview";
    }
    else if (workflow_type == "lipid-class"){
        //document.getElementById("back_button").innerHTML = "Save & Back to Lipid Class Overview";
        document.getElementById("back_button").innerHTML = "Back to Lipid Class Overview";
    }
    else {
        //document.getElementById("back_button").innerHTML = "Save & Back to Report Overview";
        document.getElementById("back_button").innerHTML = "Back to Report Overview";
    }
    
    check_fields = {};
    label_set = new Set();
    
    for (page of lipidomics_forms_content["pages"]){
        for (field of page["content"]){
            // add field info into field map
            if (!("type" in field) || !("name" in field)) continue;
            var field_name = field["name"];
            
            if (field_name in field_map){
                alert("Field with name \"" + field_name + "\" appears to be twice.");
                form_enabled = false;
            }
            field_map[field_name] = field;
            if ((field["type"] == "select" || field["type"] == "multiple") && ("choice" in field)){
                for (choice of field["choice"]){
                    if ("name" in choice){
                        var choice_name = choice["name"];
                        if (choice_name in field_map){
                            alert("Choice with name \"" + choice_name + "\" appears to be twice.");
                            form_enabled = false;
                        }
                        field_map[choice["name"]] = choice;
                        choice_to_field[choice["name"]] = field_name;
                    }
                }
            }
            else {
                choice_to_field[field_name] = field_name;
            }
            
            if (field["type"] == "multiple"){
                for (choice of field["choice"]){
                    label = field["label"] + "---" + choice["label"];
                    if (!label_set.has(label)){
                        label_set.add(label);
                    }
                    else {
                        alert("Corrupted form, labels are not allowed to be used twice: \"" + choice["label"] + "\".");
                        form_enabled = false;
                        break;
                    }
                }
            }
            else if (field["type"] == "text" || field["type"] == "number" || field["type"] == "select"){
                if (!label_set.has(field["label"])){
                    label_set.add(field["label"]);
                }
                else {
                    alert("Corrupted form, labels are not allowed to be used twice: \"" + field["label"] + "\".");
                    form_enabled = false;
                    break;
                }
            }
            
            // check for any logical conditions
            if (!("condition" in field) || field["condition"].length == 0) continue;
            
            check_fields[field_name] = [];
            var condition = [];
            for (condition_and of field["condition"].split("|")){
                var conjunction = [];
                for (con of condition_and.split("&")){
                    var single_condition = null;
                    var operator = "=";
                    if (con.indexOf("~") != -1){
                        single_condition = con.split("~");
                        operator = "~";
                    }
                    else{
                        single_condition = con.split("=");
                    }
                    
                    if (single_condition.length != 2){
                        alert("Corrupted condition \"" + field["condition"] + "\" in field \"" + field_name + "\".");
                        form_enabled = false;
                        continue;
                    }
                        
                    var key = single_condition[0];
                    var value = single_condition[1];
                        
                    var l = value.length;
                    
                    if (value[0] === "'" && value[l - 1] === "'"){
                        value = value.substring(1, l - 1);
                    }
                    else {
                        // check if value is a number
                        value = parseFloat(value);
                        if (isNaN(value)){
                            alert("Corrupted condition \"" + field["condition"] + "\" in field \"" + field_name + "\".");
                            form_enabled = false;
                            continue;
                        }
                    }
                    check_fields[field_name].push(key);
                    conjunction.push([key, operator, value]);
                    
                    
                }
                condition.push(conjunction);
            }
            field_conditions[field["name"]] = condition;
        }
    }
    // check if all required fields are actually present
    for (field_name in check_fields){
        if (!form_enabled) break;
        for (required_field of check_fields[field_name]){
            if (!(required_field in field_map)){
                alert("Error: required field \"" + required_field + "\" by field \"" + field_name + "\" is not in form.");
                form_enabled = false;
                break;
            }
        }
    }
    
    

    for (field_name in field_map){
        field_visible[field_name] = true;
    }
    
    var form_viewer = document.getElementById("form-viewer");
    var page_cnt = 0;
    for (page of lipidomics_forms_content["pages"]){
        var obj_page = document.createElement("div");
        obj_page.className = "lipidomics-forms-page";
        dom_form_pages.push(obj_page);
        
        var forms_in_page = [];
        form_pages.push(forms_in_page);
        
        
        // Status decorator
        if (lipidomics_forms_content["pages"].length > 1){
            var obj_status = document.createElement("div");
            obj_status.className = "lipidomics-forms-status";
            obj_page.append(obj_status);
            
            var obj_status_text = document.createElement("div");
            obj_status_text.className = "lipidomics-forms-status-text";
            obj_status_text.innerHTML = "<font size='+1'>" + (("title" in page) ? page["title"] : "X") + " - Page " + (page_cnt + 1) + " of " + lipidomics_forms_content["pages"].length + "</font>";
            obj_status.append(obj_status_text);
            
            var obj_status_bar = document.createElement("div");
            obj_status_bar.className = "lipidomics-forms-status-bar";
            obj_status.append(obj_status_bar);
            
            var obj_status_bar_progress = document.createElement("div");
            obj_status_bar_progress.className = "lipidomics-forms-status-bar-progress";
            obj_status_bar_progress.style.width = ((page_cnt + 1) / lipidomics_forms_content["pages"].length * 100) + "%";
            obj_status_bar.append(obj_status_bar_progress);
        }
        
        
        for (field of page["content"]){
            if (!("type" in field) || !("name" in field)) continue;
            var field_name = field["name"];

            var obj = document.createElement("div");
            obj.className = "lipidomics-forms-field";
            dom_field_map[field_name] = obj;
            obj_page.append(obj);
            forms_in_page.push(field_name);
            
            if (field["type"] == "text"){
                if (!("label" in field)) continue;
                if (!("value" in field)) field["value"] = "";
                if (!("description" in field)) field["description"] = "";
                
                // Adding the title of the field
                var obj_title = document.createElement("div");
                obj_title.className = "lipidomics-forms-field-title";
                obj_title.innerHTML = "<b>" + field["label"] + "</b>";
                if (("required" in field) && field["required"] == 1){
                    obj_title.innerHTML += " <font color='red'>*</font>";
                }
                obj.append(obj_title);
                
                // Adding the text field of the field
                var obj_content = document.createElement("div");
                obj_content.className = "lipidomics-forms-field-content";
                var obj_input = document.createElement("input");
                obj_input.className = "lipidomics-forms-input";
                obj_input.type = "text";
                obj_input.value = field["value"];
                obj_input.content = field;
                obj_input.field_name = field_name;
                obj_input.setAttribute('onchange','update_text(this);');
                obj_content.append(obj_input);
                obj.append(obj_content);
                dom_text_fields[field_name] = obj_input;
                
                // Adding description of the field if present
                if (field["description"].length > 0){
                    var obj_description = document.createElement("div");
                    obj_description.className = "lipidomics-forms-field-description";
                    obj_description.innerHTML = field["description"];
                    obj.append(obj_description);
                }
                
                var obj_required = document.createElement("div");
                obj_required.className = "lipidomics-forms-required-message";
                obj_required.innerHTML = "This field is required.";
                obj_required.style.display = "none";
                obj.append(obj_required);
                required_messages[field_name] = obj_required;
            }
            
            
            if (field["type"] == "html"){
                if (!("code" in field)) continue;
                var obj_html = document.createElement("div");
                obj.append(obj_html);
                obj_html.innerHTML = field["code"];
            }
            
            
            if (field["type"] == "table"){
                if (!("label" in field)) continue;
                if (!("columns" in field)) continue;
                if (!("value" in field)) field["value"] = "";
                if (!("description" in field)) field["description"] = "";
                
                // Adding the title of the field
                var obj_title = document.createElement("div");
                obj_title.className = "lipidomics-forms-field-title";
                obj_title.innerHTML = "<b>" + field["label"] + "</b>";
                if (("required" in field) && field["required"] == 1){
                    obj_title.innerHTML += " <font color='red'>*</font>";
                }
                obj.append(obj_title);
                
                // Adding the text field of the field
                var obj_content = document.createElement("div");
                obj_content.className = "lipidomics-forms-field-content";
                var obj_input_table = document.createElement("input-table");
                obj_input_table.className = "lipidomics-forms-input-table";
                obj_input_table.content = field;
                obj_input_table.field_name = field_name;
                obj_input_table.setAttribute('value', field["value"]);
                obj_input_table.setAttribute('columns', field["columns"]);
                obj_input_table.setAttribute('onchange', "this.content['value'] = this.value; update_table(this);");
                obj_content.append(obj_input_table);
                obj.append(obj_content);
                dom_text_fields[field_name] = obj_input_table;
                
                // Adding description of the field if present
                if (field["description"].length > 0){
                    var obj_description = document.createElement("div");
                    obj_description.className = "lipidomics-forms-field-description";
                    obj_description.innerHTML = field["description"];
                    obj.append(obj_description);
                }
                
                var obj_required = document.createElement("div");
                obj_required.className = "lipidomics-forms-required-message";
                obj_required.innerHTML = "At least one row must be added.";
                obj_required.style.display = "none";
                obj.append(obj_required);
                required_messages[field_name] = obj_required;
            }
            
            
            if (field["type"] == "tableview"){
                if (!("view" in field) || !(field["view"] in registered_tables)) continue;
                
                var obj_html = document.createElement("div");
                obj.append(obj_html);
                obj_html.innerHTML = registered_tables[field["view"]];
                
                var obj_required = document.createElement("div");
                obj_required.className = "lipidomics-forms-required-message";
                obj_required.innerHTML = "No partial entries allowed.";
                obj_required.style.display = "none";
                obj.append(obj_required);
                required_messages[field_name] = obj_required;
                
                if (field["view"] == "sample"){
                    sample_field_object = field;
                    update_sample_forms();
                }
                else if (field["view"] == "lipid-class"){
                    lipid_class_field_object = field;
                    update_class_forms();
                }
            }
            
            if (field["type"] == "number"){
                if (!("label" in field)) continue;
                if (!("value" in field)) field["value"] = "";
                if (!("description" in field)) field["description"] = "";
                
                // Adding the title of the field
                var obj_title = document.createElement("div");
                obj_title.className = "lipidomics-forms-field-title";
                obj_title.innerHTML = "<b>" + field["label"] + "</b>";
                if (("required" in field) && field["required"] == 1){
                    obj_title.innerHTML += " <font color='red'>*</font>";
                }
                obj.append(obj_title);
                
                // Adding the text field of the field
                var obj_content = document.createElement("div");
                obj_content.className = "lipidomics-forms-field-content";
                var obj_input = document.createElement("input");
                obj_input.className = "lipidomics-forms-number";
                obj_input.type = "number";
                obj_input.value = field["value"];
                if ("min" in field) obj_input.min = field["min"];
                if ("max" in field) obj_input.min = field["max"];
                if ("step" in field) obj_input.min = field["step"];
                obj_input.content = field;
                obj_input.field_name = field_name;
                obj_input.setAttribute('onchange','update_number(this);');
                obj_content.append(obj_input);
                obj.append(obj_content);
                dom_text_fields[field_name] = obj_input;
                
                // Adding description of the field if present
                if (field["description"].length > 0){
                    var obj_description = document.createElement("div");
                    obj_description.className = "lipidomics-forms-field-description";
                    obj_description.innerHTML = field["description"];
                    obj.append(obj_description);
                }
                
                var obj_required = document.createElement("div");
                obj_required.className = "lipidomics-forms-required-message";
                obj_required.innerHTML = "This field is required.";
                obj_required.style.display = "none";
                obj.append(obj_required);
                required_messages[field_name] = obj_required;
            }
            
            else if (field["type"] == "multiple"){
                if (!("label" in field) || !("choice" in field)) continue;
                if (!("description" in field)) field["description"] = "";
                
                
                // Adding the title of the field
                var obj_title = document.createElement("div");
                obj_title.className = "lipidomics-forms-field-title";
                obj_title.innerHTML = "<b>" + field["label"] + "</b>";
                if (("required" in field) && field["required"] == 1){
                    obj_title.innerHTML += " <font color='red'>*</font>";
                }
                obj.append(obj_title);
                
                // Adding the checkbox fields of the field
                var obj_content = document.createElement("div");
                obj_content.className = "lipidomics-forms-field-content";
                var obj_ul = document.createElement("ul");
                obj_ul.className = "lipidomics-forms-multiple";
                for (choice of field["choice"]){
                    if (!("name" in choice)) continue;
                    if (!("label" in choice)) choice["label"] = "Null";
                    if (!("value" in choice)) choice["value"] = 0;
                    
                    var obj_li = document.createElement("ul");
                    obj_ul.append(obj_li);
                    obj_li.className = "lipidomics-forms-li";
                    
                    var obj_input = document.createElement("input");
                    obj_li.append(obj_input);
                    
                    obj_input.type = "checkbox";
                    obj_input.content = choice;
                    obj_input.field_name = field_name;
                    if (choice["value"] == 1) obj_input.checked = true;
                    obj_input.setAttribute('onchange','update_choice(this);');
                    
                    var obj_label = document.createElement("label");
                    obj_li.append(obj_label);
                    obj_label.innerHTML = choice["label"];
                    
                }
                obj_content.append(obj_ul);
                obj.append(obj_content);
                
                // Adding description of the field if present
                if (field["description"].length > 0){
                    var obj_description = document.createElement("div");
                    obj_description.className = "lipidomics-forms-field-description";
                    obj_description.innerHTML = field["description"];
                    obj.append(obj_description);
                }
                
                var obj_required = document.createElement("div");
                obj_required.className = "lipidomics-forms-required-message";
                obj_required.innerHTML = "This field is required.";
                obj_required.style.display = "none";
                obj.append(obj_required);
                required_messages[field_name] = obj_required;
            }
            
            else if (field["type"] == "select"){
                if (!("label" in field) || !("choice" in field)) continue;
                if (!("description" in field)) field["description"] = "";
                
                
                // Adding the title of the field
                var obj_title = document.createElement("div");
                obj_title.className = "lipidomics-forms-field-title";
                obj_title.innerHTML = "<b>" + field["label"] + "</b>";
                if (("required" in field) && field["required"] == 1){
                    obj_title.innerHTML += " <font color='red'>*</font>";
                }
                obj.append(obj_title);
                
                // Adding the checkbox fields of the field
                var obj_content = document.createElement("div");
                obj_content.className = "lipidomics-forms-field-content";
                var obj_select = document.createElement("select");
                obj_select.className = "lipidomics-forms-select";
                obj_select.content = field;
                obj_select.field_name = field_name;
                var selectedIndex = 0;
                var cnt = 0;
                for (choice of field["choice"]){
                    if (!("name" in choice)) continue;
                    if (!("label" in choice)) choice["label"] = "Null";
                    if (!("value" in choice)) choice["value"] = 0;
                    
                    var obj_option = document.createElement("option");
                    obj_select.append(obj_option);
                    if (choice["value"] == 1) selectedIndex = cnt;
                    
                    obj_option.innerHTML = choice["label"];
                    cnt++;
                }
                obj_select.selectedIndex = selectedIndex;
                obj_select.setAttribute('onchange','update_select(this);');
                obj_content.append(obj_select);
                obj.append(obj_content);
                
                
                // Adding description of the field if present
                if (field["description"].length > 0){
                    var obj_description = document.createElement("div");
                    obj_description.className = "lipidomics-forms-field-description";
                    obj_description.innerHTML = field["description"];
                    obj.append(obj_description);
                }
                
                var obj_required = document.createElement("div");
                obj_required.className = "lipidomics-forms-required-message";
                obj_required.innerHTML = "This field is required.";
                obj_required.style.display = "none";
                obj.append(obj_required);
                required_messages[field_name] = obj_required;
            }
        }
        obj_page.style.display = (page_cnt == 0) ? "block" : "none";
            
        if (page_cnt > 0){ 
            var obj_prev = document.createElement("button");
            obj_prev.className = "submit-button";
            obj_prev.disabled = !form_enabled;
            obj_prev.innerHTML = "Save & Previous";
            obj_prev.setAttribute('onclick','change_page(-1);');
            obj_page.append(obj_prev);
        }
            
        var obj_next = document.createElement("button");
        obj_next.className = "submit-button";
        obj_next.disabled = !form_enabled;
        if (page_cnt < lipidomics_forms_content["pages"].length - 1){
            obj_next.innerHTML = "Save & Next";
            obj_next.setAttribute('onclick','change_page(1);');
        }
        else {
            obj_next.innerHTML = "Submit";
            obj_next.setAttribute('onclick','submit_form();');
        }
        obj_page.append(obj_next);
        
        form_viewer.append(obj_page);
        
        page_cnt++;
    }
    check_conditions();
    change_page(0);
}


function go_back(){
    if (workflow_type == "sample"){
        hide_samplelist();
    }
    else if (workflow_type == "lipid-class"){
        hide_lipid_classlist();
    }
    else {
        hide_checklist();
    }
}


function update_text(form){
    if (!form_enabled) return;
    
    var field_name = form.content["name"];
    form.content["value"] = form.value;
    required_messages[field_name].style.display = "none";
    required_messages[field_name].innerHTML = "This field is required.";
    form.style.border = "1px solid #ccc";
    check_conditions();
}


function update_table(form){
    if (!form_enabled) return;
    
    var field_name = form.content["name"];
    form.content["value"] = form.value;
    required_messages[field_name].style.display = "none";
    check_conditions();
}


function update_number(form){
    if (!form_enabled) return;
    
    var field_name = form.content["name"];
    form.content["value"] = form.value;
    required_messages[field_name].style.display = "none";
    required_messages[field_name].innerHTML = "This field is required.";
    form.style.border = "1px solid #ccc";
    check_conditions();
}



                
function update_choice(form){
    if (!form_enabled) return;
    
    var field_name = form.field_name;
    form.content["value"] = form.checked ? 1 : 0;
    required_messages[field_name].style.display = "none";
    check_conditions();
}



function update_select(form){
    if (!form_enabled) return;
    
    var field_name = form.content["name"];
    var l = form.content["choice"].length;
    for (var i = 0; i < l; ++i){
        form.content["choice"][i]["value"] = (i == form.selectedIndex) ? 1 : 0;
    }
    required_messages[field_name].style.display = "none";
    check_conditions();
}


function update_tableview(field){
    var field_name = field["name"];
    required_messages[field_name].style.display = "none";
    store_form();
}


function check_conditions(){
    if (!form_enabled) return;

    for (field_name in field_conditions){
        field_visible[field_name] = false;
        for (condition_and of field_conditions[field_name]){
            var condition_met = true;
            for (single_condition of condition_and){
                var key = single_condition[0];
                var operator = single_condition[1];
                var value = single_condition[2];
                var conditional_field = choice_to_field[key];
                condition_met &= (conditional_field in field_visible && field_visible[conditional_field]) && (operator == "=" && field_map[key]["value"] == value) || (operator == "~" && field_map[key]["value"] != value);
            }
            field_visible[field_name] |= condition_met;
        }
        dom_field_map[field_name].style.display = field_visible[field_name] ? "block" : "none";
    }
}


function check_requirements(){
    if (!form_enabled) return false;
    
    
    var first_required = null;
    for (form_name of form_pages[current_page]){
        var field = field_map[form_name];
        
        if (!("required" in field) || field["required"] == 0) continue;
        if (!field_visible[form_name]) continue;
        
        if (field["type"] == "text"){
            if (field["value"].length > 0){
                if (!("validate" in field)) continue;
                var re = new RegExp(field["validate"]);
                if (re.test(field["value"])) continue;
                required_messages[form_name].innerHTML = "Incorrect format";
            }
            
            dom_text_fields[form_name].style.border = "1px solid #cc0000";
        }
        else if (field["type"] == "tableview"){
            if (field["value"] == 1) continue;
        }
        else if (field["type"] == "table"){
            if (field["value"].length > 0) continue;
        }
        
        else if (field["type"] == "multiple"){
            var something_selected = false;
            for (choice of field["choice"]){
                something_selected |= choice["value"] != 0;
            }
            if (something_selected) continue;
        }
        
        else if (field["type"] == "number"){
            var value = field["value"];
            if (typeof(value) != 'number'){
                if (value.length > 0){
                    value = parseFloat(value);
                    if (isNaN(value)){
                        required_messages[form_name].innerHTML = "Please check the correct format and use a point . as decimal sign.";
                        value = null;
                    }
                }
                else {
                    value = null;
                }
            }
            
            if (value != null){
                if ("min" in field && field["value"] < field["min"]){
                    required_messages[form_name].innerHTML = "Value must be at least '" + field["min"] + "'";
                }
                else if ("max" in field && field["max"] < field["value"]){
                    required_messages[form_name].innerHTML = "Value must be at most '" + field["max"] + "'";
                }
                else {
                    continue;
                }
            }
        }
        
        if (first_required == null) first_required = form_name;
        required_messages[form_name].style.display = "block";
    }
    
    // move to first required
    if (first_required != null){
        dom_field_map[first_required].scrollIntoView({behavior: "smooth"});
    }

    return first_required == null;
}


function change_page(offset){
    if (offset != 0 && !check_requirements()) return;
    
    current_page = Math.min(Math.max(current_page + offset, 0), lipidomics_forms_content["pages"].length - 1);
    if (offset != 0){
        lipidomics_forms_content["current_page"] = current_page;
        store_form();
    }

    var i = 0;
    for (page of dom_form_pages){
        page.style.display = (current_page == i++) ? "block" : "none";
    }
}


function submit_form(){
    if (!form_enabled) return;
    if (!check_requirements()) return;
    store_form();
    
    var xmlhttp_request = new XMLHttpRequest();
    var request_url = connector_path + "/connector.php";
    xmlhttp_request.open("POST", request_url, false);
    xmlhttp_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlhttp_request.send("command=complete_partial_form&entry_id=" + encodeURIComponent(entry_id));
    if (workflow_type == "sample"){
        alert("Sample form successfully completed.");
        hide_samplelist();
    }
    else if (workflow_type == "lipid-class"){
        alert("Lipid class form successfully completed.");
        hide_lipid_classlist();
    }
    else {
        alert("Lipidomics report successfully completed.");
        hide_checklist();
        var xmlhttp_m = new XMLHttpRequest();
        xmlhttp_m.open("GET", "https://lifs-tools.org/matomo/matomo.php?idsite=15&rec=1&e_c=v2.0&e_a=report_completed", true);
        xmlhttp_m.send();
    }
}


function store_form(){
    var xmlhttp_request = new XMLHttpRequest();
    var request_url = connector_path + "/connector.php";
    xmlhttp_request.open("POST", request_url, false);
    xmlhttp_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlhttp_request.send("command=update_form_content&entry_id=" + encodeURIComponent(entry_id) + "&content=" + btoa(encodeURIComponent(JSON.stringify(lipidomics_forms_content))));
}


function parseURLParams(url) {
    var queryStart = url.indexOf("?") + 1,
        queryEnd   = url.indexOf("#") + 1 || url.length + 1,
        query = url.slice(queryStart, queryEnd - 1),
        pairs = query.replace(/\+/g, " ").split("&"),
        parms = {}, i, n, v, nv;

    if (query === url || query === "") return;

    for (i = 0; i < pairs.length; i++) {
        nv = pairs[i].split("=", 2);
        n = decodeURIComponent(nv[0]);
        v = decodeURIComponent(nv[1]);

        if (!parms.hasOwnProperty(n)) parms[n] = [];
        parms[n].push(nv.length === 2 ? v : null);
    }
    return parms;
}


function request_form_content(){
    if (entry_id == null) return;
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            load_data(JSON.parse(xmlhttp_request.responseText));
        }
    }
    var request_url = connector_path + "/connector.php?command=get_form_content&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}

var checklist_content = "<button class=\"submit-button\" id=\"back_button\" onclick=\"go_back();\">Back to Report Overview</button><p /> \
<div id=\"form-viewer\"></div>";
