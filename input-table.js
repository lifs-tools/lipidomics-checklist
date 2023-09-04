class InputTable extends HTMLElement {
    constructor() {
        super();
        this.data = [];
        this.column_labels = [];
        this.input_fields = [];
        this.table = document.createElement("table");
        this.table.style = "margin: 0px; border-radius: 5px; border: 0px; width: 60%;";
        this.suggestions = [];
    }
    
    connectedCallback() {
        if (!this.hasAttribute("columns")) return;
        if (!this.hasAttribute("value")) this.setAttribute("value", "");
        this.append(this.table);
        
        this.column_labels = this.getAttribute("columns").split("|");
        var l = this.column_labels.length;
        this.suggestions = new Array(l);
        this.suggestions.fill(0, 0, l);
        
        if (this.getAttribute("value").length > 0){
            var cnt = 0;
            for (var content of this.getAttribute("value").split("|")){
                if (cnt % l == 0){
                    var arr = new Array(l);
                    arr.fill("", 0, l);
                    this.data.push(arr);
                    
                }
                this.data[this.data.length - 1][cnt % l] = content;
                cnt++;
            }
        }
        this.renderTable();
    }
    
    
    addSuggestions(index, suggestion_list){
        if (0 <= index && index < this.suggestions.length){
            this.suggestions[index] = suggestion_list;
            this.renderTable();
        }
    }
    
    
    updateTable(){
        var val = [];
        for (var row of this.data){
            val.push(row.join("|"));
        }
        this.setAttribute("value", val.join("|"));
        var event = new Event('change');
        this.dispatchEvent(event);
    }
    
    
    addRow(){
        var l = this.obj.column_labels.length;
        var arr = new Array(l);
        arr.fill("", 0, l);
        this.obj.data.push(arr);
        this.obj.updateTable();
        this.obj.renderTable();
    }
    
    removeRow(){
        this.obj.data.splice(this.row_num, 1);
        this.obj.updateTable();
        this.obj.renderTable();
    }
    
    updateText(){
        this.obj.data[this.row_num][this.cell_num] = encodeURIComponent(this.value);
        this.obj.updateTable();
    }
    
    updateTextObj(obj, field){
        obj.data[field.row_num][field.cell_num] = encodeURIComponent(field.value);
        obj.updateTable();
    }
    
    
    renderTable() {
        this.table.innerHTML = "";
        var tr_col_obj = document.createElement("tr");
        this.table.append(tr_col_obj);
        for (var col_name of this.column_labels){
            var th_obj = document.createElement("th");
            tr_col_obj.append(th_obj);
            th_obj.innerHTML = col_name;
        }
        var th_obj_del = document.createElement("th");
        tr_col_obj.append(th_obj_del);
        th_obj_del.innerHTML = "&nbsp;";
            
        var row_num = 0;
        for (var row of this.data){
            var tr_obj = document.createElement("tr");
            this.table.append(tr_obj);
            var cell_num = 0;
            tr_obj.style = "border: 0px;"
            for (var cell of row){
                var td_obj = document.createElement("td");
                tr_obj.append(td_obj);
                td_obj.style = "border: 0px none; padding: 0px;"
                var div_obj = document.createElement("div");
                td_obj.append(div_obj);
                div_obj.setAttribute("class", "suggestion-div");
                
                var input_obj = document.createElement("input");
                div_obj.append(input_obj);
                input_obj.type = "text";
                input_obj.value = decodeURIComponent(cell);
                input_obj.obj = this;
                input_obj.row_num = row_num;
                input_obj.cell_num = cell_num;
                input_obj.onchange = this.updateText;
                input_obj.style = "padding: 2px 0 2px 0; border: 1px solid #ccc; border-radius: 2px; width: 98%";
                if (this.suggestions[cell_num] != 0){
                    var parent_obj = input_obj;
                    var suggestion_field = document.createElement("ul");
                    suggestion_field.setAttribute("class", "suggestion-field");
                    suggestion_field.style = "position: absolute; z-index: 1000;"
                    div_obj.appendChild(suggestion_field);
                    
                    for (var suggestion of this.suggestions[cell_num]){
                        var suggestion_cell = document.createElement("li");
                        suggestion_field.appendChild(suggestion_cell);
                        suggestion_cell.innerHTML = suggestion;
                        suggestion_cell.ref = parent_obj;
                        suggestion_cell.inputTable = this;
                        suggestion_cell.setAttribute("class", "suggestion-cell");
                        suggestion_cell.setAttribute("onclick", "this.ref.value = this.innerHTML; this.inputTable.updateTextObj(this.inputTable, this.ref);");
                    }
                    
                    var cell_number = cell_num;
                    var div = div_obj;
                }
                cell_num++;
            }
            var td_obj_del = document.createElement("td");
            tr_obj.append(td_obj_del);
            td_obj_del.width = "0px";
            var img_obj = document.createElement("img");
            td_obj_del.append(img_obj);
            td_obj_del.style = "border: 0px none; padding: 0px;"
            img_obj.src = "/lipidomics-checklist/images/trashbin.png";
            img_obj.style = "cursor: pointer; height: 20px";
            img_obj.obj = this;
            img_obj.row_num = row_num;
            img_obj.onclick = this.removeRow;
            row_num++;
        }
        
        var tr_add = document.createElement("tr");
        this.table.append(tr_add);
        var td_add = document.createElement("td");
        td_add.style = "padding: 2px 2px 0 0;";
        tr_add.append(td_add);
        td_add.setAttribute("colspan", "" + (this.column_labels.length + 1));
        
        
        var img_add = document.createElement("img");
        td_add.append(img_add);
        img_add.src = "/lipidomics-checklist/images/plus.png";
        img_add.style = "cursor: pointer; height: 20px";
        img_add.obj = this;
        img_add.onclick = this.addRow;
    }
}
customElements.define("input-table", InputTable);
