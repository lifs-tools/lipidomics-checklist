var hashcode = 0;
var connector_path = "/lipidomics-checklist";
var publish_data = [];

String.prototype.hashCode = function() {
  var hash = 0, i, chr;
  if (this.length === 0) return hash;
  for (i = 0; i < this.length; i++) {
    chr   = this.charCodeAt(i);
    hash  = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
};

function update_main_forms(update_interval){
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            var innerHTML = "";
            var for_hashcode = "";
            var new_main_form_button = document.getElementById("new_main_form");
            var post = 1;
            if (response_text.length > 0){
                if (response_text.startsWith("ErrorCodes") || response_text == -1){
                    if (!new_main_form_button.disabled){
                        new_main_form_button.disabled = true;
                        alert("Please login or sign in to use the reporting function.");
                        window.location.replace("/reporting_checklist");
                    }
                }
                else {
                    new_main_form_button.disabled = false;
                    var response = JSON.parse(response_text);
                    innerHTML += "<table cellspacing=\"0\" cellpadding=\"10\">";
                    innerHTML += "<tr><th style=\"border-bottom: 3px solid black;\">&nbsp;</th>";
                    innerHTML += "<th style=\"border-bottom: 3px solid black;\">Workflow title</th>";
                    innerHTML += "<th style=\"border-bottom: 3px solid black;\">Workflow type</th>";
                    innerHTML += "<th style=\"border-bottom: 3px solid black;\">Creation date</th>";
                    innerHTML += "<th style=\"border-bottom: 3px solid black;\">Actions</th></tr>";
                    
                    response.sort(function(a, b){
                        return b["date"] - a["date"];
                    });
                    
                    var tt_id = 0;
                    for (var i = 0; i < response.length; ++i){
                        var row = response[i];
                        if (!("entry_id" in row) || !("title" in row) || !("status" in row)){
                            echo("Error");
                            return;
                        }
                        
                        for_hashcode += row["date"];
                        innerHTML += "<tr><td>" + String(post++) + ") </td>";
                        innerHTML += "<td>" + row["title"];
                        if (row["status"] == "partial"){
                            innerHTML += "<font color='red'><b>*</b></font>";
                        }
                        
                        innerHTML += "</td><td>" + row["type"] + "</td><td>" + row["date"] + "</td>";
                        for_hashcode += row["title"] + row["status"];
                        innerHTML += "<td align=\"center\" valign=\"middle\">";
                        
                        if (row["status"] == "partial"){
                            innerHTML += "<img onclick=\"show_checklist('" + row["entry_id"] + "')\" src=\"" + connector_path + "/pencil.png\" title=\"Continue report\" style=\"cursor: pointer; height: 20px;\" />";
                            
                            innerHTML += "&nbsp;<img src='" + connector_path + "/trashbin.png'  title='Delete report' style='cursor: pointer;  height: 20px;' onclick=\"delete_main_form(" + update_interval + ", " + "'" + row["title"] + "', '" + row["entry_id"] + "');\" />";
                            for_hashcode += row["title"];
                        }
                        else if (row["status"] == "published") {
                            innerHTML += "&nbsp;<div class='lipidomics-forms-tooltip-frame'><img src=\"" + connector_path + "/globe.png\" style=\"cursor: pointer;  height: 20px;\" onmouseout=\"reset_tooltip('" + tt_id + "');\" onclick=\"copy_link('" + row["entry_id"] + "', " + tt_id + ");\"><span class=\"lipidomics-forms-tooltip-text\" id=\"lipidomics-forms-tooltip-" + tt_id + "\">Copy the DOI to clipboard</span></img></div>";
                            tt_id++;
                            
                            innerHTML += "&nbsp;<img src=\"" + connector_path + "/recycle.png\" title=\"Reuse report\" style=\"cursor: pointer;  height: 20px;\" onclick=\"copy_main_form(" + update_interval + ", '" + row["entry_id"] + "');\" />";
                            
                            innerHTML += "&nbsp;<img src=\"" + connector_path + "/pdf.png\" title=\"Download report\" style=\"cursor: pointer; height: 20px;\" onclick=\"download_pdf(" + update_interval + ", '" + row["entry_id"] + "');\" />";
                        }
                        else {
                            innerHTML += "<img src=\"" + connector_path + "/check.png\" title=\"Publish report, click for more information\" style=\"cursor: pointer; height: 20px;\" onclick=\"publish_data = [" + update_interval + ", '" + row["title"] + "', '" + row["entry_id"] + "']; document.getElementById('grey_background_index').style.display = 'block';  document.getElementById('lipidomics-forms-publishing-info-box').style.display = 'block'; document.getElementById('publish-verify-year').value = '';\" />";
                            
                            innerHTML += "&nbsp;<img onclick=\"show_checklist('" + row["entry_id"] + "')\" src=\"" + connector_path + "/pencil.png\" title=\"Update report\" style=\"cursor: pointer; height: 20px;\" />";
                            
                            innerHTML += "&nbsp;<img src=\"" + connector_path + "/recycle.png\" title=\"Reuse report\" style=\"cursor: pointer; height: 20px;\" onclick=\"copy_main_form(" + update_interval + ", '" + row["entry_id"] + "');\" />";
                            
                            innerHTML += "&nbsp;<img src=\"" + connector_path + "/pdf.png\" title=\"Download report\" style=\"cursor: pointer; height: 20px;\" onclick=\"download_pdf(" + update_interval + ", '" + row["entry_id"] + "');\" />";
                            
                            innerHTML += "&nbsp;<img src='" + connector_path + "/trashbin.png'  title='Delete report' style='cursor: pointer; height: 20px;' onclick=\"delete_main_form(" + update_interval + ", " + "'" + row["title"] + "', '" + row["entry_id"] + "');\" />";
                        }
                        innerHTML += "</td></tr>";
                    }
                    
                    innerHTML += "</table><font color='red'><b>*</b></font> Status: partial";
                }
            }
            var tmp_hashcode = for_hashcode.hashCode();
            if (hashcode != tmp_hashcode){
                document.getElementById("main_forms_table").innerHTML = innerHTML;
                hashcode = tmp_hashcode;
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_main_forms";
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function reset_tooltip(tt_id){
    document.getElementById("lipidomics-forms-tooltip-" + tt_id).innerHTML = "Copy the DOI to clipboard";
}


function copy_link(entry_id, tt_id) {
    var xmlhttp_request = new XMLHttpRequest();
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            var response_text = xmlhttp_request.responseText;
            if (response_text.length > 0 && !response_text.startsWith("ErrorCodes")){
                document.getElementById("lipidomics-forms-tooltip-" + tt_id).innerHTML = "DOI copied to clipboard";
                navigator.clipboard.writeText(response_text);
            }
            else {
                msg = "Oh no, an error occurred... Anyway, we apologize for inconvenience. Please get in contact with the administrator and provide the following message: \n\n" + response_text;
                alert(msg);
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_public_link&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


var update_interval = 0;
function start_interval(update_interval){
    update_interval = setInterval(function(){
        update_main_forms(update_interval);
    }, 2000);
    update_main_forms(update_interval);
}
start_interval(update_interval);


function delete_main_form(update_interval, workflow_title, entry_id){
    if (!confirm("Do you want to delete the report '" + workflow_title + "'? After deletion, it cannot be restored.")) return;
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_main_forms(update_interval);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=delete_main_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function download_pdf(update_interval, entry_id){
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("grey_background_index").style.display = "block";
    document.getElementById("waiting_field").style.display = "block";
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            document.getElementById("grey_background_index").style.display = "none";
            document.getElementById("waiting_field").style.display = "none";
            if (response_text.length > 0){
                if (response_text.substring(response_text.length - 4) === ".pdf"){
                    const tempLink = document.createElement('a');
                    tempLink.style.display = 'none';
                    tempLink.href = response_text;
                    tempLink.setAttribute('download', "report.pdf");
                    tempLink.setAttribute('target', '_blank');
                    document.body.appendChild(tempLink);
                    tempLink.click();
                    document.body.removeChild(tempLink);
                }
                else {
                    msg = "Oh no, an error occurred... Anyway, we apologize for inconvenience. Please get in contact with the administrator and provide the following message: \n\n" + response_text;
                    alert(msg);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=get_pdf&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}



function publish(){
    document.getElementById("lipidomics-forms-publishing-info-box").style.display = "none";
    if (publish_data.length < 3) return;
    
    update_interval = publish_data[0];
    workflow_title = publish_data[1];
    entry_id = publish_data[2];
    publish_data = [];
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    if (document.getElementById("publish-verify-year").value != new Date().getFullYear().toString()){
        document.getElementById("grey_background_index").style.display = "none";
        document.getElementById("waiting_field").style.display = "none";
        alert("Incorrect verification.");
        return;
    }
    
    document.getElementById("waiting_field").style.display = "block";
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            document.getElementById("grey_background_index").style.display = "none";
            document.getElementById("lipidomics-forms-publishing-info-box").style.display = "none";
            document.getElementById("waiting_field").style.display = "none";
            if (response_text.length > 0){
                if (!response_text.startsWith("ErrorCodes")){
                    update_main_forms(update_interval);
                }
                else if (response_text.startsWith("ErrorCodes.REPORT_NOT_CREATED")){
                    alert("Before publishing, please download and review the report.");
                }
                else if (response_text.startsWith("ErrorCodes.PUBLISHING_FAILED")){
                    msg = "Unfortunately, the publishing process failed. We apologize for inconvenience. Please get in contact with the administrators and provide the following message: \n\n" + response_text;
                    alert(msg);
                }
                else {
                    msg = "Oh no, an error occurred... Anyway, we apologize for inconvenience. Please get in contact with the administrators and provide the following message: \n\n" + response_text;
                    alert(msg);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=publish&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}





function register_new_main_form(update_interval){
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            
            if (response_text.length > 0){
                if (response_text.startsWith("ErrorCodes")){
                    console.log("Error");
                    clearInterval(update_interval);
                }
                
                else {
                    update_main_forms(update_interval);
                    show_checklist(response_text);
                }
            }
            
        }
    }
    
    var workflow_type = "";
    if (document.getElementById("radio_direct_infusion").checked) workflow_type = "di";
    else if (document.getElementById("radio_separation").checked) workflow_type = "sep";
    else if (document.getElementById("radio_imaging").checked) workflow_type = "img";
    var request_url = connector_path + "/connector.php?command=add_main_form&workflow_type=" + workflow_type;
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}





function copy_main_form(update_interval, entry_id){
    if (!window.confirm("Do you want to copy the complete workflow?")) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            
            if (response_text.length > 0){
                if (response_text.startsWith("ErrorCodes")){
                    console.log("Error");
                    clearInterval(update_interval);
                }
                
                else {
                    update_main_forms(update_interval);
                }
            }
            
        }
    }
    var request_url = connector_path + "/connector.php?command=copy_main_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function workflow_show_selector(){
    document.getElementById("grey_background_index").style.display = "block";
    document.getElementById("workflow_selector").style.display = "block";
    var workflow_selector = document.getElementById("workflow_selector_wrapper").offsetHeight;
    var window_height = window.innerHeight;
    document.getElementById("workflow_selector_wrapper").style.top = String((window_height - workflow_selector) / 2) + "px";
}



function workflow_select_selector(){
    register_new_main_form(update_interval);
    workflow_close_selector();
}


function workflow_close_selector(){
    document.getElementById("grey_background_index").style.display = "none";
    document.getElementById("workflow_selector").style.display = "none";
}

window.addEventListener('resize', function(event) {
    var workflow_selector = document.getElementById("workflow_selector_wrapper").offsetHeight;
    var window_height = window.innerHeight;
    document.getElementById("workflow_selector_wrapper").style.top = String((window_height - workflow_selector) / 2) + "px";
}, true);


var workflow_content = "<div style=\"display: inline-block;\"> \
        <div id=\"new_main_form\" style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none;\" onclick=\"workflow_show_selector();\">New workflow</div> \
        </div><p /> \
        <div id=\"main_forms_table\"></div> \
     \
    <div id=\"grey_background_index\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 110; background-color: rgba(0, 0, 0, 0.4); display: none;\"> \
    <div id=\"waiting_field\" style=\"top: calc(50% - 28px); left: calc(50% - 58px); position: absolute; background-color: white; border: 1px solid black; display: none;\"><img style=\"display: inline; padding-left: 50px; padding-right: 50px; padding-top: 20px; padding-bottom: 20px;\" src=\"/lipidomics-checklist/loader.gif\" /></div></div> \
    <div id=\"lipidomics-forms-publishing-info-box\" class=\"lipidomics-forms-publishing-info-box\"> \
    <table width='100%' height='100%' cellspacing='0px' cellpadding='0px'><tr><td style='background-color: #e0f1c7; padding: 5px 25px 5px 25px;'> \
    <font size='+3'><b>Publication information</b></font></td></tr> \
    <tr height='88%'><td height='88%' valign='top' style='padding: 5px 25px 5px 25px;'>Please read the following information carefully: \
    <ul> \
    <li class='lipidomics-forms-publishing-li'>Your report will be published <b>freely available</b> on the <a href='https://zenodo.org' target='_blank'>Zenodo</a> platform</li> \
    <li class='lipidomics-forms-publishing-li'>Your report will <b>receive a DOI</b></li> \
    <li class='lipidomics-forms-publishing-li'>It will be published under the <i>Creative Commons Attribution 4.0 International</i> license</li> \
    <li class='lipidomics-forms-publishing-li'>The following information will be submitted, too: <ul><li class='lipidomics-forms-publishing-li'>Principal investigator</li><li class='lipidomics-forms-publishing-li'>Institution</li><li class='lipidomics-forms-publishing-li'>Title of the report</li></ul></li> \
    <li class='lipidomics-forms-publishing-li'>The process is <b>irreversible</b>, due to the DOI registration</li> \
    <li class='lipidomics-forms-publishing-li'>There are no fees or additional costs for you</li> \
    </ul> \
    <p align='justify'> \
    Therefore, we recommend to publish your report after your manuscript was accepted by a journal for publication in order to provide the DOI(s) in the final manuscript version. In Order to proceed the publication, type the current year into the following text field and click on the 'OK, publish' button.</p> \
    Current year: <input type='text' id='publish-verify-year' size=5 /> \
    </td></tr> \
    <tr height='10%'><td height='10%' valign='bottom' align='right' style='padding: 5px 25px 25px 25px;'> \
    <button onclick='document.getElementById(\"grey_background_index\").style.display = \"none\"; document.getElementById(\"lipidomics-forms-publishing-info-box\").style.display = \"none\";'>&nbsp;&nbsp;&nbsp;&nbsp;Cancel&nbsp;&nbsp;&nbsp;&nbsp;</button>&nbsp;&nbsp;&nbsp;<button onclick='publish();'>&nbsp;OK, publish&nbsp;</button></td></tr></table> \
    </div> \
    <div id=\"workflow_selector\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 120; display: none;\"> \
        <div id=\"workflow_selector_wrapper\" style=\"left: 35%; width: 30%; position: fixed; background: white; border-radius: 5px;\"> \
            <div id=\"workflow_control_buttons\" style=\"width: 100%; height: 100%; position: relative;\"> \
                <table style=\"width: 100%; height: 100%; border: 1px solid black; \" cellspacing=\"10px\"  id=\"workflow_table_wrapper\"> \
                    <tr></tr> \
                    <tr><td style=\"width: 100%; height: 80%;\" valign=\"top\" align=\"left\"> \
                        <table cellpadding=\"10px\"> \
                          <tr><td colspan=\"2\"><b style=\"font-size: 20px;\">Select your new workflow type</b></td></tr> \
                          <tr><td><input type=\"radio\" id=\"radio_direct_infusion\" name=\"workflow_type_field\" value=\"workflow_direct_infusion\" checked></td> \
                          <td><label for=\"radio_direct_infusion\" style=\"font-size: 20px;\">Direct Infusion</label></td></tr> \
                          <tr><td><input type=\"radio\" id=\"radio_separation\" name=\"workflow_type_field\" value=\"workflow_separation\"></td> \
                          <td><label for=\"radio_separation\" style=\"font-size: 20px;\">Separation</label></td></tr> \
                          <tr><td><input type=\"radio\" id=\"radio_imaging\" name=\"workflow_type_field\" value=\"workflow_imaging\" disabled></td> \
                          <td><label for=\"radio_imaging\" style=\"font-size: 20px;\">Imaging</label></td></tr> \
                        </table> \
                    </td></tr> \
                    <tr><td align=\"right\" valign=\"bottom\" style=\"padding: 10px;\"> \
                        <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"workflow_select_selector();\">Select</div>&nbsp;&nbsp; \
                        <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"workflow_close_selector();\">Cancel</div> \
                    </td></tr> \
                </table> \
            </div> \
        </div> \
    </div> \
    </p> \
    <p>&nbsp;<br />&nbsp;<br />&nbsp;<br /> \
    </p>";
