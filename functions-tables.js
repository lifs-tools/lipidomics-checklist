
class TableView extends HTMLElement {
    constructor() {
        super();
        this.content = [];
        this.column_labels = [];
        this.filters = [];
        this.table = document.createElement("table");
        this.table.style = "width: 100%; margin: 0px; border-radius: 5px;";
        this.tr_objects = [];
        this.sort_arrows = [];
        this.sorting = [];
        this.current_sorting = -1;
        this.column_sizes = [];
    }
    
    connectedCallback() {
        if (!this.hasAttribute("columns")) return;
        
        var enable_sort = [];
        this.column_labels = this.getAttribute("columns").split("|");
        for (var c of this.column_labels){
            this.filters.push("");
            enable_sort.push(true);
        }
        this.append(this.table);
        this.style.overflow = "auto";
        this.style.display = "block";
        
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
        
        var tr_col_obj = document.createElement("tr");
        this.table.append(tr_col_obj);
        var col = 0;
        for (var col_name of this.column_labels){
            var th_obj = document.createElement("th");
            tr_col_obj.append(th_obj);
            if (col < this.column_sizes.length) th_obj.style.width = this.column_sizes[col] + "%";
            th_obj.innerHTML = col_name;
            if (enable_sort[col]) th_obj.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;";
            
            var div_asc = document.createElement("div");
            if (enable_sort[col]) th_obj.append(div_asc);
            div_asc.style.display = "inline";
            div_asc.style.color = "#ccc";
            div_asc.style.cursor = "pointer";
            div_asc.col = col;
            div_asc.content = this;
            div_asc.setAttribute("onclick", "this.content.sortASC(" + col + ");");
            div_asc.innerHTML = "\u25B2";
            
            var div_desc = document.createElement("div");
            if (enable_sort[col]) th_obj.append(div_desc);
            div_desc.style.display = "inline";
            div_desc.style.color = "#ccc";
            div_desc.style.cursor = "pointer";
            div_desc.col = col;
            div_desc.content = this;
            div_desc.setAttribute("onclick", "this.content.sortDESC(" + col + ");");
            div_desc.innerHTML = "\u25BC";
            
            this.sort_arrows.push([div_asc, div_desc]);
            this.sorting.push(0);
            col++;
        }
        
        var tr_filter_obj = document.createElement("tr");
        this.table.append(tr_filter_obj);
        col = 0;
        for (var filter_val of this.filters){
            var td_filter_obj = document.createElement("td");
            tr_filter_obj.append(td_filter_obj);
            td_filter_obj.style.padding = "0px";
            
            if (enable_sort[col]) {
                var input_filter_obj = document.createElement("input");
                td_filter_obj.append(input_filter_obj);
                input_filter_obj.type = "text";
                input_filter_obj.style.width = "100%";
                input_filter_obj.style.padding = "0px";
                input_filter_obj.value = filter_val;
                input_filter_obj.content = this;
                input_filter_obj.col = col++;
                input_filter_obj.onkeyup = this.setFilter;
            }
            else {
                td_filter_obj.innerHTML = "&nbsp;";
            }
        }
        
        this.updateTable();
    }
    
    resetTable(){
        this.content = [];
        for (var tr_object of this.tr_objects){
            this.table.removeChild(tr_object);
        }
        this.tr_objects = [];
        this.updateTable();
    }
    
    addRow(row){
        this.content.push(row);
        this.updateTable();
    }
    
    setFilter(){
        this.content.filters[this.col] = this.value.toLowerCase();
        this.content.updateTable();
    }
    
    sortASC(col){
        var s = this.sorting[col];
        for (var i = 0; i < this.sort_arrows.length; ++i){
            this.sort_arrows[i][0].style.color = "#ccc";
            this.sort_arrows[i][1].style.color = "#ccc";
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
            this.sort_arrows[i][0].style.color = "#ccc";
            this.sort_arrows[i][1].style.color = "#ccc";
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
        for (var tr_object of this.tr_objects){
            this.table.removeChild(tr_object);
        }
        this.tr_objects = [];
        
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
                    if (typeof(entry) === "string" && entry.toLowerCase().search(filter_val) > -1){
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
                        td_obj.style = "padding: 5px 2px 5px 2px;";
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
            view_content.sort((a, b) => {
                if (this.sorting[this.current_sorting] < 0){
                    return a[this.current_sorting].innerHTML.toLowerCase() < b[this.current_sorting].innerHTML.toLowerCase();
                }
                else {
                    return a[this.current_sorting].innerHTML.toLowerCase() > b[this.current_sorting].innerHTML.toLowerCase();
                }
                return 0;
            });
        }
        
        
        // adding rows into the table
        var col = 0;
        for (var row of view_content){
            var tr_obj = document.createElement("tr");
            this.table.append(tr_obj);
            this.tr_objects.push(tr_obj);
            var bg_color = ((++col) & 1) ? "white" : "#f4f4f4";
            for (var cell of row){
                tr_obj.append(cell);
                cell.style.backgroundColor = bg_color;
            }
        }
    }
}
customElements.define("view-table", TableView);








var sample_table_view = "<div id=\"grey_background\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 110; background-color: rgba(0, 0, 0, 0.4); display: none;\"></div> \
<div id=\"sample_selector_wrapper\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 120; display: none;\"> \
    <div id=\"sample_selector_wrapper\" style=\"top: 15%; left: 25%; width: 50%; height: 70%; position: fixed; background: white; border-radius: 5px;\"> \
        <div id=\"control-buttons-sample\" style=\"width: 100%; height: 100%; position: relative;\"> \
            <table style=\"width: 100%; margin: 0px; height: 100%; border: 1px solid black;\" cellpadding=\"10px\"> \
                <tr><td style=\"width: 100%;\"><b style=\"font-size: 20px;\">Registered sample types to workflows</b></td></tr> \
                <tr><td style=\"width: 100%; height: 80%;\" valign=\"top\" align=\"center\"> \
                    <view-table id='viewtable-import-sample' columns='Sample|Selection' size='95|5' sort='1|0' ></view-table> \
                </td></tr> \
                <tr><td align=\"right\" valign=\"bottom\"> \
                    <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"select_sample_selector();\">Select</div>&nbsp;&nbsp; \
                    <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"close_sample_selector();\">Cancel</div> \
                </td></tr> \
            </table> \
        </div> \
    </div> \
</div> \
<div style=\"display: inline-block;\"> \
    <a id=\"new_sample_form\" title=\"You can create a completely new sample entry\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"register_new_sample_form();\">Add sample type</a>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <a id=\"new_sample_form\" title=\"You can import sample entries from your other reports\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"show_sample_selector();\">Import registered sample</a> \
</div> \
<view-table id='viewtable-sample' columns='Sample set name / Sample type|Status|Actions' size='70|10|10' sort='1|1|0' ></view-table>";


var lipid_class_table_view = "<div id=\"grey_background_class\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 110; background-color: rgba(0, 0, 0, 0.4); display: none;\"></div> \
    <div id=\"class_selector_wrapper\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 120; display: none;\"> \
        <div id=\"class_selector_wrapper\" style=\"top: 15%; left: 25%; width: 50%; height: 70%; position: fixed; background: white; border-radius: 5px;\"> \
            <div id=\"control-buttons\" style=\"width: 100%; height: 100%; position: relative;\"> \
                <table style=\"width: 100%; margin: 0px; height: 100%; border: 1px solid black;\" cellpadding=\"10px\"> \
                    <tr><td style=\"width: 100%;\"><b style=\"font-size: 20px;\">Registered Lipid classes to workflows</b></td></tr> \
                    <tr><td style=\"width: 100%; height: 80%;\" valign=\"top\" align=\"center\"> \
                        <view-table id='viewtable-import-lipid-class' columns='Report Title|Lipid class|Modification date|Selection' size='45|30|20|5' sort='1|1|1|0' style=\"overflow-y: auto;\" ></view-table> \
                    </td></tr> \
                    <tr><td align=\"right\" valign=\"bottom\"> \
                        <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"select_class_selector();\">Select</div>&nbsp;&nbsp; \
                        <div style=\"padding: 10px 15px; font-size: 1em; color: #333; font-family: Arial; background-color: #eee; cursor: pointer; display: inline; border: 1px solid #ddd; border-radius: 3px;\" onmouseover=\"this.style.backgroundColor = '#ddd';\" onmouseleave=\"this.style.backgroundColor = '#eee';\" onclick=\"close_class_selector();\">Cancel</div> \
                    </td></tr> \
                </table> \
            </div> \
        </div> \
    </div> \
<div style=\"display: inline-block;\"> \
    <div id=\"new_class_form\" title=\"You can create a completely new lipid class entry\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"register_new_class_form();\">Add lipid class</div>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <div id=\"new_class_form\" title=\"You can import lipid class entries from your other reports\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"show_class_selector();\">Import registered lipid classes</div> \
</div> \
<div id=\"result_box\"></div>\
<view-table id='viewtable-lipid-class' columns='Lipid class|Status|Actions' size='70|10|10' sort='1|1|0' ></view-table>";

var registered_tables = {"sample": sample_table_view, "lipid-class": lipid_class_table_view};
