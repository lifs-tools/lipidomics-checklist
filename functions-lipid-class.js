
var lipid_class_field_object = null;
var has_partial_lipid_class = false;


function show_class_selector(){
    update_load_class_forms();
    
    window.addEventListener('resize', function(event) {
        document.getElementById("class_forms_table").style.height = String(document.getElementById("control-buttons").clientHeight * 0.75) + "px";
    }, true);
    
    document.getElementById("grey_background_class").style.display = "block";
    document.getElementById("class_selector_wrapper").style.display = "block";
    document.getElementById("class_forms_table").style.height = String(document.getElementById("control-buttons").clientHeight * 0.75) + "px";
}


function update_load_class_forms(){
    refresh_lipid_class_view();
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("class_forms_table").innerHTML = "";
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            var innerHTML = "";
            var post = 1;
            if (response_text.length > 0){
                if (response_text.startsWith("ErrorCodes")){
                    console.log("Error response all");
                }
                else {
                    var response = JSON.parse(response_text);
                    innerHTML += "<table cellspacing='0' cellpadding='10' style='width: 100%'>";
                    innerHTML += "<tr><th style='border-bottom: 3px solid black;'>&nbsp;</th>";
                    innerHTML += "<th style='border-bottom: 3px solid black;'>Workflow title</th>";
                    innerHTML += "<th style='border-bottom: 3px solid black;'>Lipid class</th>";
                    innerHTML += "<th style='border-bottom: 3px solid black;'>Modification date</th>";
                    innerHTML += "<th style='border-bottom: 3px solid black;'>Selection</th></tr>";
                    
                    response.sort(function(a, b){
                        if (a["main_title"] == b["main_title"]) return a["title"] > b["title"];
                         return a["main_title"] > b["main_title"];
                    });
                    
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("entry_id" in row) || !("title" in row) || !("status" in row)){
                            echo("Error entry all");
                            return;
                        }
                        
                        innerHTML += "<tr><td>" + String(post++) + ") </td>";
                        innerHTML += "<td>" + row["main_title"] + "</td><td>" + row["title"] + "</td><td>" + row["date"] + "</td>";
                        innerHTML += "<td><input type='checkbox' id='" + row["entry_id"] + "' class='check_class'></input></td>";
                        innerHTML += "</tr>";
                    }
                    
                    
                    innerHTML += "</table>";
                }
            }
            document.getElementById("class_forms_table").innerHTML = innerHTML;
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
    
    var checked_entries = document.getElementsByClassName("check_class");
    var class_entry_ids = [];
    for (var i = 0; i < checked_entries.length; ++i){
        var dom = checked_entries[i];
        if (dom.checked){
            class_entry_ids.push(dom.id);
        }
    }
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
            var innerHTML = "";
            var post = 1;
            
            if (response_text.length > 0){
                
                if (!response_text.startsWith("ErrorCodes")){
                    has_partial_lipid_class = false;
                    var response = JSON.parse(response_text);
                    innerHTML += "<table cellspacing='0' cellpadding='10' style='width: 100%'>";
                    innerHTML += "<tr><th style='width: 5%;'>&nbsp;</th>";
                    innerHTML += "<th style='width: 20%;'>Lipid Class</th>";
                    innerHTML += "<th style='width: 10%;'>Status</th>";
                    innerHTML += "<th style='width: 10%;'>Action</th></tr>";
                    
                    response.sort(function(a, b){
                        return b["date"] - a["date"];
                    });
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("entry_id" in row) || !("title" in row) || !("status" in row)){
                            echo("Error entry");
                            return;
                        }
                        
                        innerHTML += "<tr><td>" + String(post++) + ") </td>";
                        if (row["status"] == "partial"){
                            has_partial_lipid_class = true;
                            innerHTML += "<td>" + row["title"] + "<font color='red'>*</font></td><td>" + row["status"] + "</td>";
                            innerHTML += "<td><img src='" + connector_path + "/pencil.png' style='cursor: pointer; height: 20px;' onclick=\"refresh_lipid_class_view(); show_lipid_classlist('" + row["entry_id"] + "');\" title='Continue' />&nbsp;";
                        }
                        else {
                            innerHTML += "<td>" + row["title"] + "</td><td>" + row["status"] + "</td>";
                            innerHTML += "<td><img src='" + connector_path + "/pencil.png' title='Update lipid class' style='cursor: pointer; height: 20px;' onclick=\"refresh_lipid_class_view(); show_lipid_classlist('" + row["entry_id"] + "&');\" />&nbsp;";
                            innerHTML += "<img src='" + connector_path + "/recycle.png' title='Copy lipid class' style='cursor: pointer; height: 20px;' onclick=\"copy_class_form('" + row["entry_id"] + "');\" />&nbsp;";
                            
                        }
                        innerHTML += "<img src='" + connector_path + "/trashbin.png' title='Delete lipid class' style='cursor: pointer; height: 20px;' onclick=\"delete_class_form('" + row["title"] + "', '" + row["entry_id"] + "');\" /></td>";
                        innerHTML += "</tr>";
                    }

                    innerHTML += "</table>";
                    
                    if (lipid_class_field_object != null){
                        if (!("value" in lipid_class_field_object)) lipid_class_field_object["value"] = 0;
                        
                        lipid_class_field_object["value"] = !has_partial_lipid_class;
                    }
                }
            }
            try {
                document.getElementById("result_box").innerHTML = innerHTML;
            }
            catch (e){
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
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=add_class_form&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}
