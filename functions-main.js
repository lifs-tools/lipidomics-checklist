var stored_id = null;
var current_version = 0;

function print_error(error_message){
    msg = "Oh no, an error occurred... Anyway, we apologize for inconvenience. Please get in contact with the administrators and provide the following message: \n\n" + error_message;
    alert(msg);
}


function get_current_version(){
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            current_version = xmlhttp_request.responseText;
        }
    }
    var request_url = connector_path + "/connector.php?command=get_current_version";
    xmlhttp_request.open("GET", request_url, false);
    xmlhttp_request.send();
}


function show_checklist(eid){
    workflow_type = 'checklist';
    entry_id = eid;
    document.getElementById("checklist-form").innerHTML = checklist_content;
    request_form_content();
    document.getElementById("workflow-list").style.display = "none";
    document.getElementById("checklist-form").style.display = "block";
}


function hide_checklist(){
    document.getElementById("workflow-list").style.display = "block";
    document.getElementById("checklist-form").style.display = "none";
    update_main_forms();
}


function show_samplelist(eid){
    stored_id = entry_id;
    workflow_type = 'sample';
    entry_id = eid;
    document.getElementById("workflow-list").style.display = "none";
    document.getElementById("checklist-form").style.display = "block";
    document.getElementById("checklist-form").innerHTML = checklist_content;
    request_form_content();
}


function hide_samplelist(){
    workflow_type = 'checklist';
    entry_id = stored_id;
    document.getElementById("checklist-form").innerHTML = checklist_content;
    request_form_content();
}


function show_lipid_classlist(eid){
    stored_id = entry_id;
    workflow_type = 'lipid-class';
    entry_id = eid;
    document.getElementById("workflow-list").style.display = "none";
    document.getElementById("checklist-form").style.display = "block";
    document.getElementById("checklist-form").innerHTML = checklist_content;
    request_form_content();
}


function hide_lipid_classlist(){
    workflow_type = 'checklist';
    entry_id = stored_id;
    document.getElementById("checklist-form").innerHTML = checklist_content;
    request_form_content();
}
