
var sample_field_object = null;
var has_partial_samples = false;
var checkbox_list_sample = [];

function show_sample_selector(){
    update_load_sample_forms();
    
    window.addEventListener('resize', function(event) {
        document.getElementById("viewtable-import-sample").style.height =  String(document.getElementById("class_selector_inner").clientHeight) + "px";
    }, true);
    
    document.getElementById("grey_background").style.display = "block";
    document.getElementById("sample_selector_wrapper").style.display = "block";
    document.getElementById("viewtable-import-sample").resize();
}


function update_load_sample_forms(){
    refresh_sample_view();
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            document.getElementById("viewtable-import-sample").resetTable();
            var response = JSON.parse(response_text);
            
            for (var i = 0; i < response.length; ++i){
                var row = response[i];
                if (!("title" in row) || !("entry_id" in row)){
                    echo("Error");
                    return;
                }
                
                var table_row = [];
                table_row.push([row["title"]]);
                
                var checkbox_obj = document.createElement("input");
                checkbox_obj.type = "checkbox";
                checkbox_obj.setAttribute("id", row["entry_id"]);
                table_row.push([checkbox_obj]);
                checkbox_list_sample.push(checkbox_obj);
                
                document.getElementById("viewtable-import-sample").addRow(table_row);
            }
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
    
    var sample_entry_ids = [];
    for (var checkbox_obj of checkbox_list_sample){
        if (checkbox_obj.checked) sample_entry_ids.push(checkbox_obj.id);
    }
    checkbox_list_sample = [];
    if (sample_entry_ids.length == 0) return;
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
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
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            if (document.getElementById("viewtable-sample") == undefined) return;
            
            document.getElementById("viewtable-sample").resetTable();
                
            has_partial_samples = false;
            var response = JSON.parse(response_text);
            
            for (var i = 0; i < response.length; ++i){
                var row = response[i];
                if (!("entry_id" in row) || !("title" in row) || !("status" in row)){
                    echo("Error");
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
                    img_continue.setAttribute("onclick", "refresh_sample_view(); show_samplelist('" + row["entry_id"] + "');");
                    img_continue.src = connector_path + "/images/pencil.png";
                    img_continue.title = "Continue sample type";
                    img_continue.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                }
                else {
                    
                    var img_update = document.createElement("img");
                    trb.push(img_update);
                    img_update.setAttribute("onclick", "refresh_sample_view(); show_samplelist('" + row["entry_id"] + "');");
                    img_update.src = connector_path + "/images/pencil.png";
                    img_update.title = "Update sample type";
                    img_update.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                    
                    var img_preview = document.createElement("img");
                    trb.push(img_preview);
                    img_preview.setAttribute("onclick", "preview_sample_form('" + row["entry_id"] + "');");
                    img_preview.src = connector_path + "/images/eye.png";
                    img_preview.title = "Preview";
                    img_preview.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                    
                    var img_copy = document.createElement("img");
                    trb.push(img_copy);
                    img_copy.setAttribute("onclick", "copy_sample_form('" + row["entry_id"] + "');");
                    img_copy.src = connector_path + "/images/recycle.png";
                    img_copy.title = "Copy sample type";
                    img_copy.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                }
                    
                    
                var img_delete = document.createElement("img");
                trb.push(img_delete);
                img_delete.setAttribute("onclick", "refresh_sample_view(); delete_sample_form('" + row["title"] + "', '" + row["entry_id"] + "');");
                img_delete.src = connector_path + "/images/trashbin.png";
                img_delete.title = "Delete sample type";
                img_delete.style = "cursor: pointer; height: 20px;";
                
                document.getElementById("viewtable-sample").addRow(table_row);
            }
        
            if (sample_field_object != null){
                if (!("value" in sample_field_object)) sample_field_object["value"] = 0;
                sample_field_object["value"] = !has_partial_samples;
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





function preview_sample_form(entry_id){
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("grey_background").style.display = "block";
    document.getElementById("waiting_field").style.display = "block";
    
    window.addEventListener('resize', function(event) {
        document.getElementById("preview_sample").style.top = "calc(50% - " + Math.floor(window.innerHeight * 0.4).toString() + "px)";
        document.getElementById("preview_sample").style.height = Math.floor(window.innerHeight * 0.8) + "px";
        document.getElementById("preview_sample_content").style.height = Math.floor(window.innerHeight * 0.8 - 100) + "px";
    }, true);
    
    document.getElementById("preview_sample").style.top = "calc(50% - " + Math.floor(window.innerHeight * 0.4).toString() + "px)";
    document.getElementById("preview_sample").style.height = Math.floor(window.innerHeight * 0.8) + "px";
    document.getElementById("preview_sample_content").style.height = Math.floor(window.innerHeight * 0.8 - 100) + "px";
    
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            document.getElementById("waiting_field").style.display = "none";
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                document.getElementById("grey_background").style.display = "none";
                return;
            }
            document.getElementById("preview_sample").style.display = "block";
            
            titles = [];
            report_fields = [];
            create_preview(JSON.parse(response_text), titles, report_fields);
            titles = ["Sample"];
            
            var sample_set = "";
            var sample_origin = "";
            var sample_type = "";
            
            for (var row of report_fields[0]){
                if (row[0] == "Sample set name") sample_set = row[1];
                else if (row[0] == "Sample origin") sample_origin = row[1];
                else if (row[0] == "Sample type") sample_type = row[1];
            }
            if (sample_set.length > 0 && sample_origin.length > 0 && sample_type.length > 0){
                titles[0] = sample_set + " / " + sample_origin + " / " + sample_type;
                report_fields[0] = report_fields[0].slice(3, report_fields[0].length);
            }
            
            document.getElementById("preview_sample_content").innerHTML = "";
            document.getElementById("preview_sample_content").appendChild(create_preview_table(titles, report_fields));
        }
    }
    var request_url = connector_path + "/connector.php?command=get_form_content&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}





function export_samples(entry_id){
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("grey_background").style.display = "block";
    document.getElementById("waiting_field").style.display = "block";
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            document.getElementById("grey_background").style.display = "none";
            document.getElementById("waiting_field").style.display = "none";
            
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            const tempLink = document.createElement('a');
            tempLink.style.display = 'none';
            tempLink.href = response_text;
            tempLink.setAttribute('download', "Sample-list.xlsx");
            tempLink.setAttribute('target', '_blank');
            document.body.appendChild(tempLink);
            tempLink.click();
            document.body.removeChild(tempLink);
        }
    }
    var request_url = connector_path + "/connector.php?command=export_samples&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}





function show_samples_importer(){
    document.getElementById("grey_background").style.display = "block";
    document.getElementById("import_samples_from_file_form").style.display = "block";
    document.getElementById("sample_file_upload").value = null;
}



function hide_samples_importer(){
    document.getElementById("grey_background").style.display = "none";
    document.getElementById("import_samples_from_file_form").style.display = "none";
}




function upload_samples(entry_id, force_upload){
    if (force_upload == undefined) force_upload = false;
    document.getElementById("grey_background").style.display = "block";
    
    document.getElementById("import_samples_from_file_form").style.display = "none";
    if (entry_id == undefined || entry_id.length == 0){
        document.getElementById("grey_background").style.display = "none";
        return;
    }
    document.getElementById("waiting_field").style.display = "block";
    
    
    var files = document.getElementById("sample_file_upload");
    if (files.files.length == 0){
        alert("Warning: no file selected for upload!");
        document.getElementById("grey_background").style.display = "none";
        return;
    }
    
    
    var file = files.files[0];
    var reader = new FileReader();
    reader.onload = function(){
        var xmlhttp_request = new XMLHttpRequest();
        xmlhttp_request.onreadystatechange = function() {
            if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
                document.getElementById("grey_background").style.display = "none";
                document.getElementById("waiting_field").style.display = "block";
                
                response_text = xmlhttp_request.responseText;
                if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                    print_error(response_text);
                    return;
                }
                else if (!force_upload && response_text.startsWith("Warning")){
                    if (confirm(response_text + "\n\nDo you want to continue the import which includes partial sample forms?")){
                        upload_samples(entry_id, true);
                        return;
                    }
                }
                update_sample_forms();
            }
        }
        
        var tokens = reader.result.split("base64,");
        if (tokens.length != 2){
            print_error("Read file encoding not base 64.");
            return;
        }
        
        var request_url = connector_path + "/connector.php";
        xmlhttp_request.open("POST", request_url);
        xmlhttp_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        var request = "command=import_samples" + (force_upload ? "&force_upload=1" : "") + "&entry_id=" + encodeURIComponent(entry_id) + "&content=" + encodeURIComponent(tokens[1]);
        xmlhttp_request.send(request);
    }
    reader.readAsDataURL(file);
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
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
                    
            update_sample_forms();
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
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            update_sample_forms();
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
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            update_sample_forms();
            show_samplelist(response_text);
        }
    }
    var request_url = connector_path + "/connector.php?command=add_sample_form&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}
