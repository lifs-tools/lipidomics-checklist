
var lipid_class_field_object = null;
var has_partial_lipid_class = false;
var checkbox_list_lipid_class = [];
var checkbox_selection_lipid_class = [];

function show_class_selector(){
    update_load_class_forms();
    
    window.addEventListener('resize', function(event) {
        document.getElementById("viewtable-import-lipid-class").style.height = String(document.getElementById("class_selector_inner").clientHeight) + "px";
    }, true);
    
    document.getElementById("class_selector_wrapper").showModal();
    document.getElementById("viewtable-import-lipid-class").resize();
}


function update_load_class_forms(){
    refresh_lipid_class_view();
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    checkbox_list_lipid_class = [];
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            document.getElementById("viewtable-import-lipid-class").resetTable();
            
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            var response = JSON.parse(response_text);
            
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
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            update_class_forms();
        }
    }
    var request_url = connector_path + "/connector.php";
    xmlhttp_request.open("POST", request_url, false);
    xmlhttp_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlhttp_request.send("command=import_class_forms&entry_id=" + encodeURIComponent(entry_id) + "&class_entry_ids=" + encodeURIComponent(class_entry_ids.join("|")));
    
}


function close_class_selector(){
    document.getElementById("class_selector_wrapper").close();
}


function update_class_forms() {
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    checkbox_selection_lipid_class = [];
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            if (document.getElementById("viewtable-lipid-class") == undefined) return;
            
            document.getElementById("viewtable-lipid-class").resetTable();
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
                    has_partial_lipid_class = true;
                    
                    var img_continue = document.createElement("img");
                    trb.push(img_continue);
                    img_continue.setAttribute("onclick", "refresh_lipid_class_view(); show_lipid_classlist('" + row["entry_id"] + "');");
                    img_continue.src = connector_path + "/images/pencil.png";
                    img_continue.title = "Continue lipid class";
                    img_continue.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                }
                else {
                    var img_update = document.createElement("img");
                    trb.push(img_update);
                    img_update.setAttribute("onclick", "refresh_lipid_class_view(); show_lipid_classlist('" + row["entry_id"] + "');");
                    img_update.src = connector_path + "/images/pencil.png";
                    img_update.title = "Update lipid class";
                    img_update.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                    
                    var img_preview = document.createElement("img");
                    trb.push(img_preview);
                    img_preview.setAttribute("onclick", "preview_lipid_class_form('" + row["entry_id"] + "');");
                    img_preview.src = connector_path + "/images/eye.png";
                    img_preview.title = "Preview";
                    img_preview.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                    
                    var img_copy = document.createElement("img");
                    trb.push(img_copy);
                    img_copy.setAttribute("onclick", "copy_class_form('" + row["entry_id"] + "');");
                    img_copy.src = connector_path + "/images/recycle.png";
                    img_copy.title = "Copy lipid class";
                    img_copy.style = "cursor: pointer; height: 20px; padding-right: 5px;";
                }
                var img_delete = document.createElement("img");
                trb.push(img_delete);
                img_delete.setAttribute("onclick", "refresh_lipid_class_view(); delete_class_form('" + row["title"] + "', '" + row["entry_id"] + "');");
                img_delete.src = connector_path + "/images/trashbin.png";
                img_delete.title = "Delete lipid class";
                img_delete.style = "cursor: pointer; height: 20px;";
                
                var chb_entry = document.createElement("input");
                chb_entry.type = "checkbox";
                chb_entry.id = row["entry_id"];
                table_row.push([chb_entry]);
                checkbox_selection_lipid_class.push(chb_entry);
                
                
                
                document.getElementById("viewtable-lipid-class").addRow(table_row);
            }
            
            if (lipid_class_field_object != null){
                if (!("value" in lipid_class_field_object)) lipid_class_field_object["value"] = 0;
                lipid_class_field_object["value"] = !has_partial_lipid_class;
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_class_forms&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function select_all_lipid_classes(checked_type){
    for (var checkbox of checkbox_selection_lipid_class){
        checkbox.checked = checked_type;
    }
}



function lipid_class_mass_action(){
    var select_obj = document.getElementById("mass_action_lipid_class");
    
    if (checkbox_selection_lipid_class.length == 0 || select_obj == undefined || select_obj.selectedIndex == 0) return;
    
    var lipid_class_entry_ids = [];
    for (var checkbox of checkbox_selection_lipid_class){
        if (checkbox.checked) lipid_class_entry_ids.push(checkbox.id);
    }
    
    if (lipid_class_entry_ids.length == 0) return;
    
    action_name = select_obj.options[select_obj.selectedIndex].value;
    if (action_name == "Export to file"){
        export_lipid_class(entry_id, lipid_class_entry_ids);
    }
    else if (action_name == "Delete"){
        delete_selected_class_forms(lipid_class_entry_ids);
    }
}



function preview_lipid_class_form(entry_id){
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
            document.getElementById("preview_lipid_class").showModal();
            
            var tmp_titles = [];
            var titles = [];
            var report_fields = [];
            create_preview(JSON.parse(response_text), tmp_titles, report_fields);
            
            var lipid_class_prefix = "Lipid class";
            
            for (var i = 0; i < tmp_titles.length; ++i){
                var tmp_report_field = report_fields[i];
                var tmp_title = tmp_titles[i];
    
                
                var lipid_class = "";
                var polarity = "negative";
                var adduct_pos = "";
                var adduct_neg = "";
                for (var tmp_rep_field of tmp_report_field){
                    if (tmp_rep_field[0] == "Lipid class") lipid_class = tmp_rep_field[1];
                    else if (tmp_rep_field[0] == "Polarity mode") polarity = tmp_rep_field[1].toLowerCase();
                    else if (tmp_rep_field[0] == "Type of positive (precursor)ion") adduct_pos = tmp_rep_field[1];
                    else if (tmp_rep_field[0] == "Type of negative (precursor)ion") adduct_neg = tmp_rep_field[1];
                }
                
                if (lipid_class.length > 0 && (adduct_pos.length > 0 || adduct_neg.length > 0)){
                    lipid_class_prefix = lipid_class + ((polarity == "positive") ? adduct_pos : adduct_neg);
                }
                
                titles.push(lipid_class_prefix + " / " + tmp_title);
            }
            
            document.getElementById("preview_lipid_class_content").innerHTML = "";
            document.getElementById("preview_lipid_class_content").appendChild(create_preview_table(titles, report_fields));
        }
    }
    var request_url = connector_path + "/connector.php?command=get_form_content&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function export_lipid_class(report_entry_id, lipid_class_entry_ids){
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
            tempLink.setAttribute('download', "Lipid-class-list.xlsx");
            tempLink.setAttribute('target', '_blank');
            document.body.appendChild(tempLink);
            tempLink.click();
            document.body.removeChild(tempLink);
        }
    }
    
    var request_url = "";
    if (lipid_class_entry_ids == undefined){
        request_url = connector_path + "/connector.php?command=export_lipid_class&entry_id=" + encodeURIComponent(report_entry_id);
    }
    else {
        request_url = connector_path + "/connector.php?command=export_selected_lipid_classes&report_entry_id=" + encodeURIComponent(report_entry_id) + "&lipid_class_entry_ids=" + encodeURIComponent(lipid_class_entry_ids.join(";"));
    }
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}





function show_lipid_class_importer(){
    document.getElementById("import_lipid_class_from_file_form").showModal();
    document.getElementById("lipid_class_file_upload").value = null;
}



function hide_lipid_class_importer(){
    document.getElementById("import_lipid_class_from_file_form").close();
}




function upload_lipid_class(entry_id, force_upload){
    if (force_upload == undefined) force_upload = false;
    
    document.getElementById("import_lipid_class_from_file_form").close();
    
    if (entry_id == undefined || entry_id.length == 0){
        return;
    }
    
    
    var files = document.getElementById("lipid_class_file_upload");
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
                    if (confirm(response_text + "\n\nDo you want to continue the import which includes partial lipid class forms?")){
                        upload_lipid_class(entry_id, true);
                        return;
                    }
                }
                update_class_forms();
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
        var request = "command=import_lipid_class" + (force_upload ? "&force_upload=1" : "") + "&entry_id=" + encodeURIComponent(entry_id) + "&content=" + encodeURIComponent(tokens[1]);
        xmlhttp_request.send(request);
    }
    reader.readAsDataURL(file);
}




function delete_class_form(lipid_class, entry_id){
    refresh_lipid_class_view();
    if (!confirm("Do you really want to delete '" + lipid_class + "' class?")) return;
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                    print_error(response_text);
                    return;
            }
            
            update_class_forms();
        }
    }
    var request_url = connector_path + "/connector.php?command=delete_class_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function delete_selected_class_forms(lipid_class_entry_ids){
    refresh_lipid_class_view();
    if (!confirm("Do you really want to delete the selected lipid classes?")) return;
    
    if (lipid_class_entry_ids == undefined || lipid_class_entry_ids.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                    print_error(response_text);
                    return;
            }
            
            update_class_forms();
        }
    }
    var request_url = connector_path + "/connector.php?command=delete_selected_class_forms&entry_ids=" + encodeURIComponent(lipid_class_entry_ids.join(";"));
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function copy_class_form(entry_id){
    refresh_lipid_class_view();
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            update_class_forms();
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
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
                
            update_class_forms();
            show_lipid_classlist(response_text);
        }
    }
    var request_url = connector_path + "/connector.php?command=add_class_form&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}
