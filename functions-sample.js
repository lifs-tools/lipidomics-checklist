
var sample_field_object = null;
var has_partial_samples = false;
var checkbox_list_sample = [];
var checkbox_selection_sample = [];

function show_sample_selector(){
    update_load_sample_forms();
    
    window.addEventListener('resize', function(event) {
        document.getElementById("viewtable-import-sample").style.height =  String(document.getElementById("class_selector_inner").clientHeight) + "px";
    }, true);
    
    document.getElementById("sample_selector_wrapper").showModal();
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
    document.getElementById("sample_selector_wrapper").close();
}


function update_sample_forms() {
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    checkbox_selection_sample = [];
    
    
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
                
                var chb_entry = document.createElement("input");
                chb_entry.type = "checkbox";
                chb_entry.id = row["entry_id"];
                table_row.push([chb_entry]);
                checkbox_selection_sample.push(chb_entry);
                
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






function sample_mass_action(){
    var select_obj = document.getElementById("mass_action_samples");
    
    if (checkbox_selection_sample.length == 0 || select_obj == undefined || select_obj.selectedIndex == 0) return;
    
    var sample_entry_ids = [];
    for (var checkbox of checkbox_selection_sample){
        if (checkbox.checked) sample_entry_ids.push(checkbox.id);
    }
    
    if (sample_entry_ids.length == 0) return;
    
    action_name = select_obj.options[select_obj.selectedIndex].value;
    if (action_name == "Export to file"){
        export_samples(entry_id, sample_entry_ids);
    }
    else if (action_name == "Delete"){
        delete_selected_sample_forms(sample_entry_ids);
    }
}




function select_all_samples(checked_type){
    for (var checkbox of checkbox_selection_sample){
        checkbox.checked = checked_type;
    }
}





function preview_sample_form(entry_id){
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("waiting_field").showModal();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            document.getElementById("waiting_field").close();
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            document.getElementById("preview_sample").showModal();
            
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





function export_samples(report_entry_id, sample_entry_ids){
    if (report_entry_id == undefined || report_entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("waiting_field").showModal();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            document.getElementById("waiting_field").close();
            
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
    var request_url = "";
    if (sample_entry_ids == undefined){
        request_url = connector_path + "/connector.php?command=export_samples&entry_id=" + encodeURIComponent(report_entry_id);
    }
    else {
        request_url = connector_path + "/connector.php?command=export_selected_samples&report_entry_id=" + encodeURIComponent(report_entry_id) + "&sample_entry_ids=" + encodeURIComponent(sample_entry_ids.join(";"));
    }
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}





function show_samples_importer(){
    document.getElementById("import_samples_from_file_form").showModal();
    document.getElementById("sample_file_upload").value = null;
}



function hide_samples_importer(){
    document.getElementById("import_samples_from_file_form").close();
}




function upload_samples(entry_id, force_upload){
    if (force_upload == undefined) force_upload = false;
    document.getElementById("import_samples_from_file_form").close();
    
    if (entry_id == undefined || entry_id.length == 0){
        return;
    }
    
    
    var files = document.getElementById("sample_file_upload");
    if (files.files.length == 0){
        alert("Warning: no file selected for upload!");
        return;
    }
    
    document.getElementById("waiting_field").showModal();
    
    var file = files.files[0];
    var reader = new FileReader();
    reader.onload = function(){
        var xmlhttp_request = new XMLHttpRequest();
        xmlhttp_request.onreadystatechange = function() {
            if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
                document.getElementById("waiting_field").close();
                
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





function delete_selected_sample_forms(sample_entry_ids){
    refresh_sample_view();
    if (!confirm("Do you really want to delete the selected sample type?")) return;
    
    if (sample_field_object != null) update_tableview(sample_field_object);
    if (sample_entry_ids == undefined || sample_entry_ids.length == 0) return;
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
    var request_url = connector_path + "/connector.php?command=delete_selected_sample_forms&entry_ids=" + encodeURIComponent(sample_entry_ids.join(";"));
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
