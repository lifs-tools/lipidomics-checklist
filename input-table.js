class InputTable extends HTMLElement {
    constructor() {
        super();
        this.data = [];
        this.column_labels = [];
        this.input_fields = [];
        this.table = document.createElement("table");
        this.table.style = "border: 1px solid #ccc; border-radius: 5px; width: 100%; max-width: 60%;";
    }
    
    updateTable(){
        var val = [];
        for (var row of this.data){
            val.push(row.join("|"));
        }
        this.value = val.join("|");
        this.onchange();
    }
    
    connectedCallback() {
        if (!this.hasAttribute("columns")) return;
        if (!this.hasAttribute("value")) return;
        this.append(this.table);
        
        this.column_labels = this.getAttribute("columns").split("|");
        
        if (this.getAttribute("value").length > 0){
            var cnt = 0;
            var l = this.column_labels.length;
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
        this.obj.data[this.row_num][this.cell_num] = this.value;
        this.obj.updateTable();
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
            for (var cell of row){
                var td_obj = document.createElement("td");
                tr_obj.append(td_obj);
                var input_obj = document.createElement("input");
                td_obj.append(input_obj);
                input_obj.type = "text";
                input_obj.value = cell;
                input_obj.obj = this;
                input_obj.row_num = row_num;
                input_obj.cell_num = cell_num;
                input_obj.onchange = this.updateText;
                input_obj.style = "width: 98%;";
                cell_num++;
            }
            var td_obj_del = document.createElement("td");
            tr_obj.append(td_obj_del);
            var img_obj = document.createElement("img");
            td_obj_del.append(img_obj);
            img_obj.src = "/lipidomics-checklist/trashbin.png";
            img_obj.height = "20";
            img_obj.style = "cursor: pointer;";
            img_obj.obj = this;
            img_obj.row_num = row_num;
            img_obj.onclick = this.removeRow;
            row_num++;
        }
        
        var tr_add = document.createElement("tr");
        this.table.append(tr_add);
        var td_add = document.createElement("td");
        tr_add.append(td_add);
        td_add.colspan = this.column_labels.length + 1;
        
        
        var img_add = document.createElement("img");
        td_add.append(img_add);
        img_add.src = "/lipidomics-checklist/plus.png";
        img_add.height = "20";
        img_add.style = "cursor: pointer;";
        img_add.obj = this;
        img_add.onclick = this.addRow;
    }
}
customElements.define("input-table", InputTable);
