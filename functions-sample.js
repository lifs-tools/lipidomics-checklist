


window.addEventListener('resize', function(event) {
    document.getElementById("sample_forms_table").style.height = String(document.getElementById("control-buttons-sample").clientHeight * 0.75) + "px";
}, true);


function show_sample_selector(update_interval_sample){
    update_load_sample_forms(update_interval_sample);
    document.getElementById("grey_background").style.display = "block";
    document.getElementById("sample_selector_wrapper").style.display = "block";
    document.getElementById("sample_forms_table").style.height = String(document.getElementById("control-buttons-sample").clientHeight * 0.75) + "px";
}



function update_load_sample_forms(update_interval_sample){
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("sample_forms_table").innerHTML = "";
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            var innerHTML = "";
            var post = 1;
            if (response_text.length > 0){
                if (response_text.startsWith("ErrorCodes")){
                    console.log("Error");
                    clearInterval(update_interval_sample);
                }
                else {
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
                        innerHTML += "<td><input type='checkbox' id='" + row["enc_entry"] + "' class='check_sample'></input></td>";
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
    
    if (entry_id == undefined || entry_id.length == 0) return;
    
    var checked_entries = document.getElementsByClassName("check_sample");
    var sample_entry_ids = [];
    for (var i = 0; i < checked_entries.length; ++i){
        var dom = checked_entries[i];
        if (dom.checked){
            sample_entry_ids.push(dom.id);
        }
    }
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (response_text.startsWith("ErrorCodes")){
                    console.log("Error");
                    clearInterval(update_interval_sample);
                }
                else {
                    update_sample_forms(update_interval_sample);
                }
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=import_sample_forms&entry_id=" + encodeURIComponent(entry_id) + "&sample_entry_ids=" + sample_entry_ids.join("|");
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
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
                
                if (response_text.startsWith("ErrorCodes")){
                    clearInterval(update_interval_sample);
                }
                else {
                    var response = JSON.parse(response_text);
                    innerHTML += "<table cellspacing='0' cellpadding='10' style='width: 100%'>";
                    innerHTML += "<tr><th style='width: 3%;'>&nbsp;</th>";
                    innerHTML += "<th style='width: 70%;'>Sample set name / Sample type </th>";
                    innerHTML += "<th style='width: 11%;'>Status</th>";
                    innerHTML += "<th style='width: 11%;'>Action</th>";
                    innerHTML += "<th style='width: 5%;'>&nbsp;</th></tr>";
                    
                    response.sort(function(a, b){
                        return b["date_modified"] - a["date_modified"];
                    });
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("link" in row) || !("title" in row) || !("status" in row)){
                            echo("Error");
                            return;
                        }
                        
                        var date_mod = new Date(row["date_modified"] * 1000);
                        innerHTML += "<tr><td>" + String(post++) + ") </td>";
                        innerHTML += "<td>" + row["title"] + "</td><td>" + row["status"] + "</td>";
                        if (row["status"] == "partial"){
                            innerHTML += "<td><button onclick=\"parent.show_samplelist('" + row["link"] + "&workflow_type=sample');\">Continue</button></td>";
                        }
                        else {
                            innerHTML += "<td alt='Copy sample type form'><button onclick='copy_sample_form(" + update_interval_sample + ", " + '"' + row["enc_entry"] + '"' + ");' />Copy form</button></td>";
                        }
                        innerHTML += "<td align='center' alt='Delete sample type'><img src='" + connector_path + "/trashbin.png' style='cursor: pointer; height: 18px;' onclick='delete_sample_form(" + update_interval_sample + ", " + '"' + row["title"] + '"' + ", " + '"' + row["enc_entry"] + '"' + ");' /></td>";
                        innerHTML += "</tr>";
                    }

                    innerHTML += "</table>";
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
    console.log(request_url);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function delete_sample_form(update_interval_sample, sample_type, entry_id){
    if (!confirm("Do you really want to delete '" + sample_type + "' type?")) return;
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_sample_forms(update_interval_sample);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=delete_sample_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}

var update_interval_sample = 0;
async function start_interval_sample(update_interval_sample){
    await new Promise(resolve => setTimeout(resolve, 100));
    update_interval_sample = setInterval(update_sample_forms, 3000);
    update_sample_forms(update_interval_sample);
}




function copy_sample_form(update_interval_sample, entry_id){
    
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0 && !response_text.startsWith("ErrorCodes")){
                update_sample_forms(update_interval_sample);
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=copy_sample_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}




function register_new_sample_form(update_interval_sample){
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_sample_forms(update_interval_sample);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=add_sample_form&main_entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}
