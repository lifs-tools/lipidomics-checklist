
var lipid_class_field_object = null;
var has_partial_lipid_class = false;
var checkbox_list_lipid_class = [];

function show_class_selector(){
    update_load_class_forms();
    
    window.addEventListener('resize', function(event) {
        document.getElementById("viewtable-import-lipid-class").style.height = String(document.getElementById("control-buttons").clientHeight * 0.75) + "px";
    }, true);
    
    document.getElementById("grey_background_class").style.display = "block";
    document.getElementById("class_selector_wrapper").style.display = "block";
    document.getElementById("viewtable-import-lipid-class").style.height = String(document.getElementById("control-buttons").clientHeight * 0.75) + "px";
}


function update_load_class_forms(){
    refresh_lipid_class_view();
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    checkbox_list_lipid_class = [];
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                document.getElementById("viewtable-import-lipid-class").resetTable();
                if (response_text.startsWith("ErrorCodes")){
                    console.log("Error response all");
                }
                else {
                    var response = JSON.parse(response_text);
                    
                    response.sort(function(a, b){
                        if (a["main_title"] == b["main_title"]) return a["title"] > b["title"];
                         return a["main_title"] > b["main_title"];
                    });
                    
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("main_title") || !("entry_id" in row) || !("title" in row) || !("status" in row)){
                            echo("Error entry all");
                            return;
                        }
                        
                        var table_row = [];
                        table_row.push([row["main_title"]]);
                        table_row.push([row["title"]]);
                        table_row.push([row["date"]]);
                        
                        var checkbox_obj = document.createElement("input");
                        checkbox_obj.type = "checkbox";
                        checkbox_obj.setAttribute("class", "check_class");
                        checkbox_obj.setAttribute("id", row["entry_id"]);
                        table_row.push([checkbox_obj]);
                        checkbox_list_lipid_class.push(checkbox_obj);
                        
                        document.getElementById("viewtable-import-lipid-class").addRow(table_row);
                    }
                }
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_all_class_forms";
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function refresh_lipid_class_view(){
    if (lipid_class_field_object != null) update_tableview(lipid_class_field_object);
}


function select_class_selector(){
    close_class_selector();
    refresh_lipid_class_view();
    
    if (entry_id == undefined || entry_id.length == 0) return;
    
    var class_entry_ids = [];
    for (var checkbox_obj of checkbox_list_lipid_class){
        if (checkbox_obj.checked) class_entry_ids.push(checkbox_obj.id);
    }
    checkbox_list_lipid_class = [];
    if (class_entry_ids.length == 0) return;
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            update_class_forms();
        }
    }
    var request_url = connector_path + "/connector.php";
    xmlhttp_request.open("POST", request_url, false);
    xmlhttp_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlhttp_request.send("command=import_class_forms&entry_id=" + encodeURIComponent(entry_id) + "&class_entry_ids=" + encodeURIComponent(class_entry_ids.join("|")));
    
}


function close_class_selector(){
    document.getElementById("grey_background_class").style.display = "none";
    document.getElementById("class_selector_wrapper").style.display = "none";
}


function update_class_forms() {
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            
            if (document.getElementById("viewtable-lipid-class") == undefined) return;
            
            if (response_text.length > 0){
                document.getElementById("viewtable-lipid-class").resetTable();
                
                if (!response_text.startsWith("ErrorCodes")){
                    has_partial_lipid_class = false;
                    var response = JSON.parse(response_text);
                    
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("entry_id" in row) || !("title" in row) || !("status" in row)){
                            echo("Error entry");
                            return;
                        }
                        
                        var table_row = [];
                        table_row.push([row["title"] + " "]);
                        if (row["status"] == "partial"){
                            var font_obj = document.createElement("font");
                            font_obj.style.color = "red";
                            font_obj.style.font_weight = "bold";
                            font_obj.innerHTML = "*";
                            table_row[table_row.length - 1].push(font_obj);
                        }
                        table_row.push([row["status"]]);
                        
                        var trb = [];
                        table_row.push(trb);
                        if (row["status"] == "partial"){
                            has_partial_samples = true;
                            
                            var img_continue = document.createElement("img");
                            trb.push(img_continue);
                            img_continue.setAttribute("onclick", "refresh_sample_view(); show_lipid_classlist('" + row["entry_id"] + "');");
                            img_continue.src = connector_path + "/pencil.png";
                            img_continue.title = "Continue lipid class";
                            img_continue.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                        }
                        else {
                            
                            var img_update = document.createElement("img");
                            trb.push(img_update);
                            img_update.setAttribute("onclick", "refresh_sample_view(); show_lipid_classlist('" + row["entry_id"] + "');");
                            img_update.src = connector_path + "/pencil.png";
                            img_update.title = "Update lipid class";
                            img_update.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                            
                            var img_copy = document.createElement("img");
                            trb.push(img_copy);
                            img_copy.setAttribute("onclick", "copy_class_form('" + row["entry_id"] + "');");
                            img_copy.src = connector_path + "/recycle.png";
                            img_copy.title = "Copy lipid class";
                            img_copy.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                        }
                        var img_delete = document.createElement("img");
                        trb.push(img_delete);
                        img_delete.setAttribute("onclick", "refresh_sample_view(); delete_class_form('" + row["title"] + "', '" + row["entry_id"] + "');");
                        img_delete.src = connector_path + "/trashbin.png";
                        img_delete.title = "Delete lipid class";
                        img_delete.style = "cursor: pointer; height: 20px;";
                        
                        document.getElementById("viewtable-lipid-class").addRow(table_row);
                    }
                    
                    if (lipid_class_field_object != null){
                        if (!("value" in lipid_class_field_object)) lipid_class_field_object["value"] = 0;
                        lipid_class_field_object["value"] = !has_partial_lipid_class;
                    }
                }
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_class_forms&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function delete_class_form(lipid_class, entry_id){
    refresh_lipid_class_view();
    if (!confirm("Do you really want to delete '" + lipid_class + "' class?")) return;
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_class_forms();
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=delete_class_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function copy_class_form(entry_id){
    refresh_lipid_class_view();
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0 && !response_text.startsWith("ErrorCodes")){
                update_class_forms();
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=copy_class_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function register_new_class_form(){
    refresh_lipid_class_view();
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_class_forms();
                    show_lipid_classlist(response_text);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=add_class_form&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}
