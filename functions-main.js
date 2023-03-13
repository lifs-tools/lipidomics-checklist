var stored_id = null;
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
