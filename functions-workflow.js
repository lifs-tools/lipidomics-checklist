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



function update_main_forms(){
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            var new_main_form_button = document.getElementById("new_main_form");
            
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                if (response_text == "ErrorCodes.NO_WORDPRESS_CONNECTION"){
                    new_main_form_button.disabled = true;
                    alert("Please login or sign in to use the reporting function.");
                    window.location.replace("/reporting_checklist");
                }
                else {
                    print_error(response_text);
                }
                return;
            }
            document.getElementById("viewtable").resetTable();
                
            new_main_form_button.disabled = false;
            var response = null;
            try {
                response = JSON.parse(response_text);
            }
            catch(err){
                print_error(err);
                return;
            }
            
            
            var tt_id = 0;
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
                
                table_row.push([row["type"]]);
                table_row.push([row["date"]]);
                
                var trb = [];
                table_row.push(trb);
                
                /*
                if (("owner" in row) && row["owner"] == 1){
                    var img_share = document.createElement("img");
                    trb.push(img_share);
                    //img_share.setAttribute("onclick", "show_checklist('" + row["entry_id"] + "');");
                    img_share.src = connector_path + "/images/share.png";
                    img_share.title = "Share report";
                    img_share.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                }
                else {
                    var img_fill = document.createElement("img");
                    trb.push(img_fill);
                    img_fill.style = "min-width: 25px; padding-right: 5px; box-sizing: border-box;";
                }*/
                
                if (row["status"] == "partial"){
                    var img_fill1 = document.createElement("img");
                    trb.push(img_fill1);
                    img_fill1.style = "min-width: 25px; padding-right: 5px; box-sizing: border-box;";
                    
                    var img_continue = document.createElement("img");
                    trb.push(img_continue);
                    img_continue.setAttribute("onclick", "show_checklist('" + row["entry_id"] + "');");
                    img_continue.src = connector_path + "/images/pencil.png";
                    img_continue.title = "Continue report";
                    img_continue.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    var img_fill2 = document.createElement("img");
                    trb.push(img_fill2);
                    img_fill2.style = "min-width: 24px; padding-right: 5px; box-sizing: border-box;";
                    
                    var img_fill3 = document.createElement("img");
                    trb.push(img_fill3);
                    img_fill3.style = "min-width: 24px; padding-right: 5px; box-sizing: border-box;";
                
                    
                    var img_dump = document.createElement("img");
                    trb.push(img_dump);
                    img_dump.setAttribute("onclick", "export_report('" + row["entry_id"] + "');");
                    img_dump.src = connector_path + "/images/floppy.png";
                    img_dump.title = "Dump report in JSON format";
                    img_dump.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    var img_del = document.createElement("img");
                    trb.push(img_del);
                    img_del.setAttribute("onclick", "delete_main_form(" + "'" + row["title"] + "', '" + row["entry_id"] + "');");
                    img_del.src = connector_path + "/images/trashbin.png";
                    img_del.title = "Delete report";
                    img_del.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                }
                else if (row["status"] == "published") {
                    var div_doi = document.createElement("div");
                    trb.push(div_doi);
                    div_doi.setAttribute("class", "lipidomics-forms-tooltip-frame");
                    div_doi.style = "padding-right: 5px; box-sizing: border-box;";
                    div_doi.innerHTML = "<img src=\"" + connector_path + "/images/globe.png\" style=\"cursor: pointer; height: 20px;\" onmouseout=\"reset_tooltip('" + tt_id + "');\" onclick=\"copy_link('" + row["entry_id"] + "', " + tt_id + ");\"><span class=\"lipidomics-forms-tooltip-text\" id=\"lipidomics-forms-tooltip-" + tt_id + "\">Copy the DOI to clipboard</span></img>";
                    tt_id++;
                    
                    
                    var img_fill1 = document.createElement("img");
                    trb.push(img_fill1);
                    img_fill1.style = "min-width: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    var img_copy = document.createElement("img");
                    trb.push(img_copy);
                    img_copy.setAttribute("onclick", "copy_main_form('" + row["entry_id"] + "');");
                    img_copy.src = connector_path + "/images/recycle.png";
                    img_copy.title = "Copy report";
                    img_copy.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    
                    var img_download = document.createElement("img");
                    trb.push(img_download);
                    img_download.setAttribute("onclick", "download_pdf('" + row["entry_id"] + "');");
                    img_download.src = connector_path + "/images/pdf.png";
                    img_download.title = "Download report";
                    img_download.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                
                    
                    var img_dump = document.createElement("img");
                    trb.push(img_dump);
                    img_dump.setAttribute("onclick", "export_report('" + row["entry_id"] + "');");
                    img_dump.src = connector_path + "/images/floppy.png";
                    img_dump.title = "Dump report in JSON format";
                    img_dump.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    
                    var img_fill2 = document.createElement("img");
                    trb.push(img_fill2);
                    img_fill2.style = "min-width: 22px; padding-right: 5px; box-sizing: border-box;";
                }
                else {
                    var img_copy = document.createElement("img");
                    trb.push(img_copy);
                    img_copy.setAttribute("onclick", "publish_data = ['" + row["title"] + "', '" + row["entry_id"] + "']; document.getElementById('lipidomics-forms-publishing-info-box').showModal(); document.getElementById('publish-verify-year').value = '';");
                    img_copy.src = connector_path + "/images/check.png";
                    img_copy.title = "Publish report, click here for more information";
                    img_copy.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    
                    var img_update = document.createElement("img");
                    trb.push(img_update);
                    img_update.setAttribute("onclick", "show_checklist('" + row["entry_id"] + "');");
                    img_update.src = connector_path + "/images/pencil.png";
                    img_update.title = "Update report";
                    img_update.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    
                    var img_copy = document.createElement("img");
                    trb.push(img_copy);
                    img_copy.setAttribute("onclick", "copy_main_form('" + row["entry_id"] + "');");
                    img_copy.src = connector_path + "/images/recycle.png";
                    img_copy.title = "Copy report";
                    img_copy.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    
                    var img_download = document.createElement("img");
                    trb.push(img_download);
                    img_download.setAttribute("onclick", "download_pdf('" + row["entry_id"] + "');");
                    img_download.src = connector_path + "/images/pdf.png";
                    img_download.title = "Download report";
                    img_download.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                
                    
                    var img_dump = document.createElement("img");
                    trb.push(img_dump);
                    img_dump.setAttribute("onclick", "export_report('" + row["entry_id"] + "');");
                    img_dump.src = connector_path + "/images/floppy.png";
                    img_dump.title = "Dump report in JSON format";
                    img_dump.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                    
                    
                    var img_del = document.createElement("img");
                    trb.push(img_del);
                    img_del.setAttribute("onclick", "delete_main_form('" + row["title"] + "', '" + row["entry_id"] + "');");
                    img_del.src = connector_path + "/images/trashbin.png";
                    img_del.title = "Delete report";
                    img_del.style = "cursor: pointer; height: 20px; padding-right: 5px; box-sizing: border-box;";
                }
                
                document.getElementById("viewtable").addRow(table_row);
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_main_forms";
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
    
    update_published_reports();
}







function update_published_reports(){
    return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                if (response_text == "ErrorCodes.NO_WORDPRESS_CONNECTION"){
                    alert("Please login or sign in to use the reporting function.");
                    window.location.replace("/reporting_checklist");
                }
                else {
                    print_error(response_text);
                }
                return;
            }
            
            document.getElementById("publishtable").resetTable();
            var response = null;
            try {
                response = JSON.parse(response_text);
            }
            catch(err){
                print_error(err);
                return;
            }
            
            var tt_id = 0;
            for (var i = 0; i < response.length; ++i){
                var row = response[i];
                if (!("entry_id" in row) || !("title" in row) || !("type" in row) || !("author" in row) || !("date" in row)){
                    continue;
                }
                
                var table_row = [];
                table_row.push([row["title"]]);
                table_row.push([row["author"]]);
                table_row.push([row["type"]]);
                table_row.push([row["date"]]);
                
                var trb = [];
                table_row.push(trb);
            
                var img_download = document.createElement("img");
                trb.push(img_download);
                img_download.setAttribute("onclick", "download_pdf('" + row["entry_id"] + "');");
                img_download.src = connector_path + "/images/pdf.png";
                img_download.title = "Download report";
                img_download.style = "cursor: pointer; height: 20px;";
                
                
                document.getElementById("publishtable").addRow(table_row);
            }
        }
    }
    var request_url = connector_path + "/connector.php?command=get_published_forms";
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
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            document.getElementById("lipidomics-forms-tooltip-" + tt_id).innerHTML = "DOI copied to clipboard";
            navigator.clipboard.writeText(response_text);
        }
    }
    var request_url = connector_path + "/connector.php?command=get_public_link&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function delete_main_form(workflow_title, entry_id){
    if (!confirm("Do you want to delete the report '" + workflow_title + "'? After deletion, it cannot be restored.")) return;
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            update_main_forms();
        }
    }
    var request_url = connector_path + "/connector.php?command=delete_main_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function download_pdf(entry_id){
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("waiting_field").showModal();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            document.getElementById("waiting_field").close();
            
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes") || response_text.substring(response_text.length - 4) != ".pdf"){
                print_error(response_text);
                return;
            }
            const tempLink = document.createElement('a');
            tempLink.style.display = 'none';
            tempLink.href = response_text;
            tempLink.setAttribute('download', "report.pdf");
            tempLink.setAttribute('target', '_blank');
            document.body.appendChild(tempLink);
            tempLink.click();
            document.body.removeChild(tempLink);
        }
    }
    var request_url = connector_path + "/connector.php?command=get_pdf&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}


function export_report(entry_id){
    if (entry_id == undefined || entry_id.length == 0) return;
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
            tempLink.setAttribute('download', "report.json");
            tempLink.setAttribute('target', '_blank');
            document.body.appendChild(tempLink);
            tempLink.click();
            document.body.removeChild(tempLink);
        }
    }
    var request_url = connector_path + "/connector.php?command=export_report&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}



function publish(){
    document.getElementById("lipidomics-forms-publishing-info-box").close();
    if (publish_data.length < 2) return;
    
    workflow_title = publish_data[0];
    entry_id = publish_data[1];
    publish_data = [];
    
    if (entry_id == undefined || entry_id.length == 0) return;
    var xmlhttp_request = new XMLHttpRequest();
    document.getElementById("lipidomics-forms-publishing-info-box").close();
    
    if (document.getElementById("publish-verify-year").value != new Date().getFullYear().toString()){
        alert("The verification year was incorrect. Please type in the correct verification year in order to continue the publication process.");
        return;
    }
    
    document.getElementById("waiting_field").showModal();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            document.getElementById("waiting_field").close();
            
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                if (response_text.startsWith("ErrorCodes.REPORT_NOT_CREATED")){
                    alert("Before publishing, please download and review the report.");
                }
                else if (response_text.startsWith("ErrorCodes.PUBLISHING_FAILED")){
                    msg = "Unfortunately, the publishing process failed. We apologize for inconvenience. Please get in contact with the administrators and provide the following message: \n\n" + response_text;
                    alert(msg);
                }
                else {
                    print_error(response_text);
                }
                return;
            }
            
            update_main_forms();
            
            var xmlhttp_m = new XMLHttpRequest();
            xmlhttp_m.open("GET", "https://lifs-tools.org/matomo/matomo.php?idsite=15&rec=1&e_c=" + current_version + "&e_a=report_published", true);
            xmlhttp_m.send();
        }
    }
    var request_url = connector_path + "/connector.php?command=publish&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}





function register_new_main_form(){
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            update_main_forms();
            show_checklist(response_text);
            
            var xmlhttp_m = new XMLHttpRequest();
            xmlhttp_m.open("GET", "https://lifs-tools.org/matomo/matomo.php?idsite=15&rec=1&e_c=" + current_version + "&e_a=new_report", true);
            xmlhttp_m.send();
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





function copy_main_form(entry_id){
    if (!window.confirm("Do you want to copy the complete workflow?")) return;
    var xmlhttp_request = new XMLHttpRequest();
    
    xmlhttp_request.onreadystatechange = function() {
        if (xmlhttp_request.readyState == 4 && xmlhttp_request.status == 200) {
            response_text = xmlhttp_request.responseText;
            if (response_text.length == 0 || response_text.startsWith("ErrorCodes")){
                print_error(response_text);
                return;
            }
            
            update_main_forms();
        }
    }
    var request_url = connector_path + "/connector.php?command=copy_main_form&entry_id=" + encodeURIComponent(entry_id);
    xmlhttp_request.open("GET", request_url);
    xmlhttp_request.send();
}



function workflow_select_selector(){
    register_new_main_form();
    workflow_close_selector();
}


function workflow_close_selector(){
    document.getElementById("workflow_selector").close();
}







function upload_report(){
    document.getElementById("report_importer_form").close();    
    
    var files = document.getElementById("report_file_upload");
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
                    if (response_text.startsWith("ErrorCodes.ERROR_ON_DECODING_FORM")){
                        alert("It seems that the json file is broken or not a json file at all. Please check.");
                    }
                    else {
                        print_error(response_text);
                    }
                    return;
                }
                
                update_main_forms();
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
        var request = "command=import_report&content=" + encodeURIComponent(tokens[1]);
        xmlhttp_request.send(request);
    }
    reader.readAsDataURL(file);
}



var workflow_content = "<div style=\"display: inline-block;\"> \
        <div id=\"new_main_form\" style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none;\" onclick=\"document.getElementById('workflow_selector').showModal();\">New Report</div> \
        </div><p /> \
        <h3>Own Report List</h3> \
        <view-table id=\"viewtable\" columns=\"Report&nbsp;title|Report&nbsp;type|Creation&nbsp;date|Actions\" size='40|20|20|20' sort='1|1|1|0' align='l|l|l|c' ></view-table><br /> \
        <font color='red'><b>*</b></font> Status: partial \
        <div style='display: none;'> \
            <p />&nbsp;<p />&nbsp;<p />&nbsp;<p /> \
            <h3>General List of Published Reports</h3> \
            <view-table id=\"publishtable\" columns=\"Title|Principle&nbsp;investigator|Report&nbsp;type|Creation&nbsp;date|Actions\" size='30|30|20|15|5' sort='1|1|1|1|0' align='l|l|l|l|c' ></view-table><br /> \
        </div> \
     \
    <dialog id=\"lipidomics-forms-publishing-info-box\" style=\"font-size: 18px; background-color: white; border-radius: 5px;\"> \
    <table style=\"width: 600px; height: 700px; margin: 0px; border: 0px;\" cellspacing='0px' cellpadding='0px' style='margin: 0px;'><tr><td colspan='2' style='background-color: #e0f1c7; padding: 15px 25px 5px 25px;'> \
    <font size='+3'><b>Publication information</b></font></td></tr> \
    <tr height='88%'><td height='88%' colspan='2' valign='top' style='padding: 5px 25px 5px 25px;'>Please read the following information carefully: \
    <ul class='lipidomics-forms-publishing-ul'> \
    <li class='lipidomics-forms-publishing-li'>Your report will be published <b>freely available</b> on the <a href='https://zenodo.org' target='_blank'>Zenodo</a> platform</li> \
    <li class='lipidomics-forms-publishing-li'>Your report will <b>receive a DOI</b></li> \
    <li class='lipidomics-forms-publishing-li'>It will be published under the <i>Creative Commons Attribution 4.0 International</i> license</li> \
    <li class='lipidomics-forms-publishing-li'>The following information will be submitted, too: <ul><li class='lipidomics-forms-publishing-li'>Principal investigator</li><li class='lipidomics-forms-publishing-li'>Institution</li><li class='lipidomics-forms-publishing-li'>Title of the report</li></ul></li> \
    <li class='lipidomics-forms-publishing-li'>The process is <b>irreversible</b>, due to the DOI registration</li> \
    <li class='lipidomics-forms-publishing-li'>There are no fees or additional costs for you</li> \
    <li class='lipidomics-forms-publishing-li'>The publication can take up to one minute, please be patient</li> \
    </ul> \
    <p align='justify'> \
    Therefore, we recommend to publish your report after your manuscript was accepted by a journal for publication in order to provide the DOI(s) in the final manuscript version. In order to proceed the publication, type the current year into the following text field and click on the 'OK, publish' button.</td></tr> \
    <tr><td  height='10%' valign='bottom' align='left' style='border: 0px; padding: 5px 25px 25px 25px;'>Current year:&nbsp;&nbsp;<input type='text' id='publish-verify-year' size=5 /></td> \
    <td height='10%' valign='bottom' align='right' style='border: 0px; padding: 5px 25px 25px 25px;'> \
    <button onclick='document.getElementById(\"lipidomics-forms-publishing-info-box\").close();'>&nbsp;&nbsp;&nbsp;&nbsp;Cancel&nbsp;&nbsp;&nbsp;&nbsp;</button>&nbsp;&nbsp;&nbsp;<button onclick='publish();'>&nbsp;OK, publish&nbsp;</button></td></tr></table> \
    </dialog> \
    <dialog id=\"workflow_selector\" style=\"border-radius: 5px;\"> \
        <table style=\"width: 576px; height: 265px; border: 0px;\"> \
            <tr></tr> \
            <tr><td style=\"width: 100%; height: 80%; border-top: 0px;\" colspan=\"2\" valign=\"top\" align=\"left\"> \
                <table cellpadding=\"10px\"> \
                    <tr><td colspan=\"2\"><b style=\"font-size: 20px;\">Select your new report type</b></td></tr> \
                    <tr><td><input type=\"radio\" id=\"radio_direct_infusion\" name=\"workflow_type_field\" value=\"workflow_direct_infusion\" checked></td> \
                    <td><label for=\"radio_direct_infusion\" style=\"font-size: 20px;\">Direct Infusion</label></td></tr> \
                    <tr><td><input type=\"radio\" id=\"radio_separation\" name=\"workflow_type_field\" value=\"workflow_separation\"></td> \
                    <td><label for=\"radio_separation\" style=\"font-size: 20px;\">Separation</label></td></tr> \
                    <tr><td><input type=\"radio\" id=\"radio_imaging\" name=\"workflow_type_field\" value=\"workflow_imaging\"></td> \
                    <td><label for=\"radio_imaging\" style=\"font-size: 20px;\">Imaging</label></td></tr> \
                </table> \
            </td></tr> \
            <tr><td align=\"left\" valign=\"bottom\" style=\"padding: 10px; border-top: 0px;\"> \
                    <div style=\"padding: 10px 15px; user-select: none; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"document.getElementById('workflow_selector').close(); document.getElementById('report_file_upload').value = null; document.getElementById('report_importer_form').showModal();\">Import report</div> \
                </td> \
                <td align=\"right\" valign=\"bottom\" style=\"padding: 10px; border-top: 0px;\"> \
                    <div style=\"padding: 10px 15px; user-select: none; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"workflow_select_selector();\">Select</div>&nbsp;&nbsp; \
                    <div style=\"padding: 10px 15px; user-select: none; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"workflow_close_selector();\">Cancel</div> \
                </td> \
            </tr> \
        </table> \
    </dialog> \
    <dialog id=\"report_selector\" style=\"border-radius: 5px;\"> \
    </dialog> \
    <dialog id='report_importer_form' style=\"background: white; border-radius: 5px;\"> \
        <table style='width: 400px; height: 100px; border: 0px; margin: 0px;'> \
            <tr style='vertical-align: middle; background-color: rgba(0,0,0,0) !important;'> \
                <td width='100%' height='100%' style='border: 0px; vertical-align: middle;' align='center' valign='middle'> \
                    Select a report file (*.json) for upload: <p /> \
                    <input type='file' id='report_file_upload' accept='.json' style='border: 0px;'></input><p />&nbsp;<p /> \
                </td> \
            </tr> \
            <tr> \
                <td align='right'> \
                    <div style=\"padding: 10px 15px; user-select: none; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"upload_report();\">Upload report</div>&nbsp;&nbsp; \
                    <div style=\"padding: 10px 15px; user-select: none; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"document.getElementById('report_importer_form').close(); document.getElementById('workflow_selector').showModal();\">Cancel</div> \
                </td> \
            </tr> \
        </table> \
    </dialog> \
    </p> \
    <p>&nbsp;<br />&nbsp;<br />&nbsp;<br /> \
    </p>";
