
var sample_field_object = null;
var has_partial_samples = false;


function show_sample_selector(){
    update_load_sample_forms();
    
    window.addEventListener('resize', function(event) {
        document.getElementById("sample_forms_table").style.height = String(document.getElementById("control-buttons-sample").clientHeight * 0.75) + "px";
    }, true);
    
    document.getElementById("grey_background").style.display = "block";
    document.getElementById("sample_selector_wrapper").style.display = "block";
    document.getElementById("sample_forms_table").style.height = String(document.getElementById("control-buttons-sample").clientHeight * 0.75) + "px";
}


function update_load_sample_forms(){
    refresh_sample_view();
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("sample_forms_table").innerHTML = "";
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            var innerHTML = "";
            var post = 1;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    var response = JSON.parse(response_text);
                    innerHTML += "<table cellspacing='0' cellpadding='10' style='width: 100%'>";
                    innerHTML += "<tr><th style='width: 3%; border-bottom: 3px solid black;'>&nbsp;</th>";
                    innerHTML += "<th style='width: 90%; border-bottom: 3px solid black;'>Sample</th>";
                    innerHTML += "<th style='border-bottom: 3px solid black;'>Selection</th></tr>";
                    
                    response.sort(function(a, b){
                        return a["title"] > b["title"];
                    });
                    
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("title" in row)){
                            echo("Error");
                            return;
                        }
                        
                        innerHTML += "<tr><td>" + String(post++) + ") </td>";
                        innerHTML += "<td>" + row["title"] + "</td>";
                        innerHTML += "<td><input type='checkbox' id='" + row["entry_id"] + "' class='check_sample'></input></td>";
                        innerHTML += "</tr>";
                    }
                    
                    
                    innerHTML += "</table>";
                }
            }
            document.getElementById("sample_forms_table").innerHTML = innerHTML;
        }
    }
    var request_url = connector_path + "/connector.php?command=get_all_sample_forms";
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function select_sample_selector(){
    close_sample_selector();
    refresh_sample_view();
    
    if (entry_id == undefined || entry_id.length == 0) return;
    
    var checked_entries = document.getElementsByClassName("check_sample");
    var sample_entry_ids = [];
    for (var i = 0; i < checked_entries.length; ++i){
        var dom = checked_entries[i];
        if (dom.checked){
            sample_entry_ids.push(dom.id);
        }
    }
    if (sample_entry_ids.length == 0) return;
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            update_sample_forms();
        }
    }
    var request_url = connector_path + "/connector.php";
    xmlhttp_request.open("POST", request_url, false);
    xmlhttp_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlhttp_request.send("command=import_sample_forms&entry_id=" + encodeURIComponent(entry_id) + "&sample_entry_ids=" + encodeURIComponent(sample_entry_ids.join("|")));
}


function close_sample_selector(){
    document.getElementById("grey_background").style.display = "none";
    document.getElementById("sample_selector_wrapper").style.display = "none";
}


function update_sample_forms() {
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            var innerHTML = "";
            var post = 1;
            
            if (response_text.length > 0){
                
                if (!response_text.startsWith("ErrorCodes")){
                    has_partial_samples = false;
                    var response = JSON.parse(response_text);
                    innerHTML += "<table cellspacing='0' cellpadding='10' style='width: 100%'>";
                    innerHTML += "<tr><th style='width: 3%;'>&nbsp;</th>";
                    innerHTML += "<th style='width: 70%;'>Sample set name / Sample type </th>";
                    innerHTML += "<th style='width: 11%;'>Status</th>";
                    innerHTML += "<th style='width: 11%;'>Actions</th></tr>";
                    
                    response.sort(function(a, b){
                        return b["date_modified"] - a["date_modified"];
                    });
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("entry_id" in row) || !("title" in row) || !("status" in row)){
                            echo("Error");
                            return;
                        }
                        
                        innerHTML += "<tr><td>" + String(post++) + ") </td>";
                        if (row["status"] == "partial"){
                            has_partial_samples = true;
                            innerHTML += "<td>" + row["title"] + "<font color='red'>*</font></td><td>" + row["status"] + "</td>";
                            innerHTML += "<td><img src='" + connector_path + "/pencil.png' style='cursor: pointer; height: 20px;'  onclick=\"refresh_sample_view(); show_samplelist('" + row["entry_id"] + "');\" title='Continue' />&nbsp;";
                        }
                        else {
                            innerHTML += "<td>" + row["title"] + "</td><td>" + row["status"] + "</td>";
                            innerHTML += "<td><img src='" + connector_path + "/pencil.png' style='cursor: pointer; height: 20px;' onclick=\"refresh_sample_view(); show_samplelist('" + row["entry_id"] + "');\" title='Update sample type' />&nbsp;";
                            innerHTML += "<img src='" + connector_path + "/recycle.png' style='cursor: pointer; height: 20px;' onclick=\"copy_sample_form('" + row["entry_id"] + "');\" title='Copy sample type' />&nbsp;";
                        }
                        innerHTML += "<img title='Delete sample type' src='" + connector_path + "/trashbin.png' style='cursor: pointer; height: 20px;' onclick=\"refresh_sample_view(); delete_sample_form('" + row["title"] + "', '" + row["entry_id"] + "');\" /></td>";
                        innerHTML += "</tr>";
                    }

                    innerHTML += "</table>";
                
                    if (sample_field_object != null){
                        if (!("value" in sample_field_object)) sample_field_object["value"] = 0;
                        
                        sample_field_object["value"] = !has_partial_samples;
                    }
                }
            }
            try {
                document.getElementById("result_box_samples").innerHTML = innerHTML;
            }
            catch (e){
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_sample_forms&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}



function refresh_sample_view(){
    if (sample_field_object != null) update_tableview(sample_field_object);
}




function delete_sample_form(sample_type, entry_id){
    refresh_sample_view();
    if (!confirm("Do you really want to delete '" + sample_type + "' type?")) return;
    
    if (sample_field_object != null) update_tableview(sample_field_object);
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_sample_forms();
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=delete_sample_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function copy_sample_form( entry_id){
    refresh_sample_view();
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0 && !response_text.startsWith("ErrorCodes")){
                update_sample_forms();
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=copy_sample_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function register_new_sample_form(){
    refresh_sample_view();
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_sample_forms();
                    show_samplelist(response_text);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=add_sample_form&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}
