var ILSGreenHeader = "#7EBA28";
var ILSGreenRow = "#E5F1D4";
var ArrowInactiveColor = "#ccc";

class TableView extends HTMLElement {
    constructor() {
        super();
        this.content = [];
        this.column_labels = [];
        this.filters = [];
        this.table = document.createElement("table");
        this.table.style = "width: 100%; margin: 0px; padding: 0px;";
        this.table.setAttribute("cellspacing", "0px");
        this.table.setAttribute("border", "0px");
        this.sort_arrows = [];
        this.sorting = [];
        this.current_sorting = -1;
        this.column_sizes = [];
        this.thead = document.createElement("thead");
        this.tbody = document.createElement("tbody");
        this.align = [];
    }
    
    resize(){
        this.tbody.style.height = (this.parentNode.offsetHeight - 1.5 * this.thead.offsetHeight) + "px";
        if (this.tbody.childNodes.length > 0){
            var i = 0;
            for (var child of this.thead.firstChild.children){
                this.tbody.firstChild.children[i].style.width = child.offsetWidth + "px";
                i++;
            }
        }
    }
    
    
    connectedCallback() {
        if (!this.hasAttribute("columns")) return;
        
        var enable_sort = [];
        this.column_labels = this.getAttribute("columns").split("|");
        for (var c of this.column_labels){
            this.filters.push("");
            enable_sort.push(true);
            this.align.push("left");
        }
        this.append(this.table);
        this.table.append(this.thead);
        
        if (this.hasAttribute("fixedHeight")){
            window.addEventListener('resize', (event) => {
                this.resize();
            }, true);
            this.tbody.style.overflowY = "auto";
            this.tbody.style.position = "absolute";
        }
        
        if (this.hasAttribute("size")) {
            for (var size of this.getAttribute("size").split("|")){
                var num = parseInt(size);
                if (!isNaN(num)) this.column_sizes.push(size);
            }
        }
        
        if (this.hasAttribute("sort")){
            var i = 0;
            for (var s of this.getAttribute("sort").split("|")){
                if (s != "1" && i < enable_sort.length){
                    enable_sort[i] = false;
                }
                i++;
            }
        }
        
        var aligns = {"l": "left", "c": "center", "r": "right"};
        if (this.hasAttribute("align")){
            var i = 0;
            for (var s of this.getAttribute("align").split("|")){
                if (i < this.align.length && (s in aligns)){
                    this.align[i] = aligns[s];
                }
                i++;
            }
        }
        
        var tr_col_obj = document.createElement("tr");
        this.thead.append(tr_col_obj);
        var col = 0;
        for (var col_name of this.column_labels){
            var th_obj = document.createElement("th");
            tr_col_obj.append(th_obj);
            th_obj.setAttribute("align", "center");
            if (col < this.column_sizes.length) th_obj.style.width = this.column_sizes[col] + "%";
            th_obj.innerHTML = col_name;
            th_obj.style.color = "white";
            th_obj.style.fontSize = "18px";
            th_obj.style.backgroundColor = ILSGreenHeader;
            if (enable_sort[col]) th_obj.innerHTML += "&nbsp;&nbsp;";
            
            var div_asc = document.createElement("div");
            if (enable_sort[col]) th_obj.append(div_asc);
            div_asc.style.display = "inline";
            div_asc.style.color = ArrowInactiveColor;
            div_asc.style.cursor = "pointer";
            div_asc.style.fontSize = "14px";
            div_asc.col = col;
            div_asc.content = this;
            div_asc.setAttribute("onclick", "this.content.sortASC(" + col + ");");
            div_asc.innerHTML = "\u25B2";
            
            var div_desc = document.createElement("div");
            if (enable_sort[col]) th_obj.append(div_desc);
            div_desc.style.display = "inline";
            div_desc.style.color = ArrowInactiveColor;
            div_desc.style.cursor = "pointer";
            div_desc.style.fontSize = "14px";
            div_desc.style.margin = "0px 0px 0px -3px";
            div_desc.col = col;
            div_desc.content = this;
            div_desc.setAttribute("onclick", "this.content.sortDESC(" + col + ");");
            div_desc.innerHTML = "\u25BC";
            
            this.sort_arrows.push([div_asc, div_desc]);
            this.sorting.push(0);
            col++;
        }
        
        var tr_filter_obj = document.createElement("tr");
        this.thead.append(tr_filter_obj);
        col = 0;
        for (var filter_val of this.filters){
            var td_filter_obj = document.createElement("td");
            tr_filter_obj.append(td_filter_obj);
            td_filter_obj.style.padding = "0px";
            td_filter_obj.style.backgroundColor = ILSGreenHeader;
            
            if (enable_sort[col]) {
                var input_filter_obj = document.createElement("input");
                td_filter_obj.append(input_filter_obj);
                input_filter_obj.type = "text";
                input_filter_obj.style.width = "100%";
                input_filter_obj.style.padding = "2px 0px";
                input_filter_obj.value = filter_val;
                input_filter_obj.content = this;
                input_filter_obj.col = col++;
                input_filter_obj.onkeyup = this.setFilter;
            }
            else {
                td_filter_obj.innerHTML = "&nbsp;";
            }
        }
        this.table.append(this.tbody);
        
        this.updateTable();
        if (this.hasAttribute("fixedHeight")) this.resize();
    }
    
    resetTable(){
        this.content = [];
        this.tbody.innerHTML = "";
        this.updateTable();
    }
    
    addRow(row){
        this.content.push(row);
        this.updateTable();
    }
    
    setFilter(){
        this.content.filters[this.col] = this.value.toLowerCase();
        if (this.content.filters[this.col] == "dadjoke"){
            this.value = "";
            this.content.filters[this.col] = "";
            var dadjokes = ["Why is 6 afraid of 7? Because 7 8 9!",
                         "No matter how kind you are, german children are 'Kinder'!",
                         "I only know 25 letters of the alphabet. I don't know y.",
                         "Why do seagulls fly over the sea? Because if they flew over the bay, we'd call them baygels.",
                         "I am doing now a sea food diet: every time I see food, I eat it.",
                         "Sweet dreams are made of cheese, who am I to diss a brie. I chadder the world and the feta cheese. Everybody's looking for sour cream.",
                         "How do you call 8 hobbits? A hobbyte!",
                         "I only seem to get sick on weekdays. I must have a weekend immune system.",
                         "What's the favorite key on a keyboard for a pirate? It's the C.",
                         "There are only 10 types of people, these who understand binary and the others.",
                         "Applied so hard, and got so far. But in the end, I wasn't even hired. - Linkedin Park"];
            
            alert(dadjokes[Math.floor((Math.random() * dadjokes.length))]);
        }
        
        this.content.updateTable();
    }
    
    sortASC(col){
        var s = this.sorting[col];
        for (var i = 0; i < this.sort_arrows.length; ++i){
            this.sort_arrows[i][0].style.color = ArrowInactiveColor;
            this.sort_arrows[i][1].style.color = ArrowInactiveColor;
            this.sorting[i] = 0;
        }
        
        if (s != 1){
            this.sort_arrows[col][0].style.color = "black";
            this.sorting[col] = 1;
            this.current_sorting = col;
        }
        else {
            this.current_sorting = -1;
        }
        this.updateTable();
    }
    
    sortDESC(col){
        var s = this.sorting[col];
        for (var i = 0; i < this.sort_arrows.length; ++i){
            this.sort_arrows[i][0].style.color = ArrowInactiveColor;
            this.sort_arrows[i][1].style.color = ArrowInactiveColor;
            this.sorting[i] = 0;
        }
        
        if (s != -1){
            this.sort_arrows[col][1].style.color = "black";
            this.sorting[col] = -1;
            this.current_sorting = col;
        }
        else {
            this.current_sorting = -1;
        }
        this.updateTable();
    }
    
    updateTable(){
        // clear table
        var view_content = [];
        this.tbody.innerHTML = "";
        
        var num_cols = this.column_labels.length;
        
        // filter rows
        for (var row of this.content){
            var add_row = true;
            var col = -1;
            for (var filter_val of this.filters){
                col++;
                if (filter_val.length == 0) continue;
                if (col >= row.length) {
                    add_row = false;
                    break;
                }
                var cell = row[col];
                
                
                var filter_matches = false;
                for (var entry of cell){
                    if (typeof(entry) === "string" && entry.toLowerCase().indexOf(filter_val) > -1){
                        filter_matches = true;
                        break;
                    }
                }
                add_row &= filter_matches;
            }
            
            if (add_row){
                var new_row = [];
                var col = 0;
                for (var cell of row){
                    if (col >= num_cols) break;
                    
                    var td_obj = document.createElement("td");
                    new_row.push(td_obj);
                    for (var entry of cell){
                        td_obj.append(entry);
                        td_obj.setAttribute("align", this.align[col]);
                        td_obj.style = "padding: 3px 0 3px 0;";
                    }
                    col++;
                }
                while (col++ < num_cols){
                    var td_empty = document.createElement("td");
                    new_row.push(td_empty);
                    td_empty.innerHTML = "&nbsp;";
                }
                view_content.push(new_row);
            }
        }
        
        
        // sort rows
        if (this.current_sorting != -1){
            view_content.sort((row_one, row_two) => {
                if (this.sorting[this.current_sorting] < 0){
                    return row_one[this.current_sorting].innerHTML.toLowerCase() < row_two[this.current_sorting].innerHTML.toLowerCase();
                }
                else {
                    return row_one[this.current_sorting].innerHTML.toLowerCase() > row_two[this.current_sorting].innerHTML.toLowerCase();
                }
                return 0;
            });
        }
        
        
        // adding rows into the table
        var col = 0;
        for (var row of view_content){
            var tr_obj = document.createElement("tr");
            tr_obj.style.backgroundColor = "red";
            this.tbody.append(tr_obj);
            tr_obj.style.fontWeight = "normal";
            //var bg_color = ((++col) & 1) ? "white" : "#f4f4f4";
            var bg_color = ((++col) & 1) ? "white" : ILSGreenRow;
            for (var cell of row){
                tr_obj.append(cell);
                cell.style.backgroundColor = bg_color;
            }
        }
        
        if (this.hasAttribute("fixedHeight")) this.resize();
    }
}
customElements.define("view-table", TableView);








var sample_table_view = "<div id=\"sample_selector_wrapper\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 120; display: none;\"> \
    <div id=\"sample_selector_wrapper\" style=\"top: 15%; left: 25%; width: 50%; height: 70%; position: fixed; background: white; border-radius: 5px; border: 1px solid black;\"> \
        <div id=\"control-buttons-sample\" style=\"width: 100%; height: 100%; position: relative;\"> \
            <table style=\"width: 100%; margin: 0px; height: 100%; border: inherit;\" cellpadding=\"10px\"> \
                <tr style='background-color: rgba(0, 0, 0, 0) !important;'><td style=\"width: 100%; border: 0px;\"><b style=\"font-size: 20px;\">Select sample types from other reports for import</b></td></tr> \
                <tr><td style=\"width: 100%; border: 0px; height: 80%;\" id='sample_selector_inner' valign=\"top\" align=\"center\"> \
                    <view-table id='viewtable-import-sample' columns='Sample|Selection' size='95|5' sort='1|0' align='l|c' fixedHeight ></view-table> \
                </td></tr> \
                <tr><td style='border: 0px;' align=\"right\" valign=\"bottom\"> \
                    <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"select_sample_selector();\">Select</div>&nbsp;&nbsp; \
                    <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"close_sample_selector();\">Cancel</div> \
                </td></tr> \
            </table> \
        </div> \
    </div> \
</div> \
<div id='preview_sample' style=\"top: calc(50% - 350px); left: 15%; width: 70%; height: 700px; position: fixed; display: none; background: white; border: 1px solid black; z-index: 120; border-radius: 5px;\"> \
<div style='width: 100%; text-align: right;'><img src='" + connector_path + "/images/close-x.png' style='cursor: pointer; padding: 3px;' onclick='document.getElementById(\"preview_sample\").style.display = \"none\"; document.getElementById(\"grey_background\").style.display = \"none\";' /> \
</div> \
<div id='preview_sample_content' style='width: 100%; height: calc(100% - 50px); box-sizing: border-box; padding: 50px; overflow-y: auto;'></div> \
</div> \
<div id='import_samples_from_file_form' style=\"top: calc(50% - 100px); left: 35%; width: 30%; height: 200px; position: fixed; display: none; background: white; border: 1px solid black; z-index: 120; border-radius: 5px;\"> \
<table width='100%' style='border: 0px; margin: 0px;' height='100%'><tr style='vertical-align: middle; background-color: rgba(0,0,0,0) !important;'><td width='100%' height='100%' style='border: 0px; vertical-align: middle;' align='center' valign='middle'> \
Select a spreadsheet file for upload: <p /> \
<input type='file' id='sample_file_upload' accept='.xlsx'></input><p /> \
<button onclick='upload_samples(entry_id);'>Upload file</button>&nbsp;&nbsp;<button onclick='hide_samples_importer();'>Cancel</button> \
</td></tr></table></div> \
<div style=\"display: inline-block;\"> \
    <a id=\"new_sample_form\" title=\"You can create a completely new sample entry\" style=\"cursor: pointer; display: inline-block;\" onclick=\"register_new_sample_form();\">Add sample type</a>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <a id=\"import_sample_form\" title=\"You can import sample entries from your other reports\" style=\"cursor: pointer; display: inline-block;\" onclick=\"show_sample_selector();\">Import registered sample</a>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <a id=\"export_sample_forms\" title=\"You can export sample entries into a spreadsheet file\" style=\"cursor: pointer; display: inline-block;\" onclick=\"export_samples(entry_id);\">Export samples to file</a>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <a id=\"upload_sample_forms\" title=\"You can import sample entries from a spreadsheet file\" style=\"cursor: pointer; display: inline-block;\" onclick=\"show_samples_importer();\">Import samples from file</a> \
</div> \
<view-table id='viewtable-sample' columns='Sample set name / Sample type|Status|Actions' size='70|10|10' sort='1|1|0' align='l|l|c' ></view-table>";




var lipid_class_table_view = "<div id=\"class_selector_wrapper\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 120; display: none;\"> \
        <div id=\"class_selector_wrapper\" style=\"top: 15%; left: 25%; width: 50%; height: 70%; position: fixed; background: white; border-radius: 5px; border: 1px solid black;\"> \
            <div id=\"control-buttons\" style=\"width: 100%; height: 100%; position: relative;\"> \
                <table style=\"width: 100%; margin: 0px; height: 100%; border: inherit;\" cellpadding=\"10px\"> \
                    <tr style='background-color: rgba(0, 0, 0, 0) !important;'><td style=\"width: 100%; border: 0px;\"><b style=\"font-size: 20px;\">Select lipid classes from other reports for import</b></td></tr> \
                    <tr><td style=\"width: 100%; border: 0px; height: 80%;\" id='class_selector_inner' valign=\"top\" align=\"center\"> \
                        <view-table id='viewtable-import-lipid-class' columns='Report Title|Lipid class|Modification date|Selection' size='35|30|30|5' sort='1|1|1|0' style=\"overflow-y: auto;\" align='l|l|l|c' fixedHeight ></view-table> \
                    </td></tr> \
                    <tr><td style='border: 0px;' align=\"right\" valign=\"bottom\"> \
                        <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"select_class_selector();\">Select</div>&nbsp;&nbsp; \
                        <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"close_class_selector();\">Cancel</div> \
                    </td></tr> \
                </table> \
            </div> \
        </div> \
    </div> \
<div id='preview_lipid_class' style=\"top: calc(50% - 350px); left: 15%; width: 70%; height: 700px; position: fixed; display: none; background: white; border: 1px solid black; z-index: 120; border-radius: 5px;\"> \
<div style='width: 100%; text-align: right;'><img src='" + connector_path + "/images/close-x.png' style='cursor: pointer; padding: 3px;' onclick='document.getElementById(\"preview_lipid_class\").style.display = \"none\"; document.getElementById(\"grey_background\").style.display = \"none\";' /> \
</div> \
<div id='preview_lipid_class_content' style='width: 100%; height: calc(100% - 50px); box-sizing: border-box; padding: 50px; overflow-y: auto;'></div> \
</div> \
<div id='import_lipid_class_from_file_form' style=\"top: calc(50% - 100px); left: 35%; width: 30%; height: 200px; position: fixed; display: none; background: white; border: 1px solid black; z-index: 120; border-radius: 5px;\"> \
<table width='100%' style='border: 0px; margin: 0px;' height='100%'><tr style='vertical-align: middle; background-color: rgba(0,0,0,0) !important;'><td width='100%' height='100%' style='border: 0px; vertical-align: middle;' align='center' valign='middle'> \
Select a spreadsheet file for upload: <p /> \
<input type='file' id='lipid_class_file_upload' accept='.xlsx'></input><p /> \
<button onclick='upload_lipid_class(entry_id);'>Upload file</button>&nbsp;&nbsp;<button onclick='hide_lipid_class_importer();'>Cancel</button> \
</td></tr></table></div> \
<div style=\"display: inline-block;\"> \
    <a id=\"new_class_form\" title=\"You can create a completely new lipid class entry\" style=\"cursor: pointer; display: inline-block;\" onclick=\"register_new_class_form();\">Add lipid class</a>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <a id=\"new_class_form\" title=\"You can import lipid class entries from your other reports\" style=\"cursor: pointer; display: inline-block;\" onclick=\"show_class_selector();\">Import registered lipid classes</a>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <a id=\"export_lipid_class_forms\" title=\"You can export lipid class entries into a spreadsheet file\" style=\"cursor: pointer; display: inline-block;\" onclick=\"export_lipid_class(entry_id);\">Export lipid classes to file</a>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <a id=\"upload_lipid_class_forms\" title=\"You can import lipid_class entries from a spreadsheet file\" style=\"cursor: pointer; display: inline-block;\" onclick=\"show_lipid_class_importer();\">Import lipid classes from file</a> \
</div> \
<div id=\"result_box\"></div>\
<view-table id='viewtable-lipid-class' columns='Lipid class|Status|Actions' size='70|10|10' sort='1|1|0' align='l|l|c' ></view-table>";

var registered_tables = {"sample": sample_table_view, "lipid-class": lipid_class_table_view};
