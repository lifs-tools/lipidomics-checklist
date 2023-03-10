var sample_table_view = "<label class=\"wpforms-field-label\">Sample types</label>  \
<div id=\"grey_background\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 110; background-color: rgba(0, 0, 0, 0.4); display: none;\"></div> \
<div id=\"sample_selector_wrapper\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 120; display: none;\"> \
    <div id=\"sample_selector_wrapper\" style=\"top: 15%; left: 25%; width: 50%; height: 70%; position: fixed; background: white; border-radius: 5px;\"> \
        <div id=\"control-buttons-sample\" style=\"width: 100%; height: 100%; position: relative;\"> \
            <table style=\"width: 100%; height: 100%; border: 1px solid black;\" cellpadding=\"10px\" id=\"table_wrapper\"> \
                <tr><td style=\"width: 100%;\"><b style=\"font-size: 20px;\">Registered sample types to workflows</b></td></tr> \
                <tr><td style=\"width: 100%; height: 80%;\" valign=\"top\" align=\"center\"> \
                    <div id=\"sample_forms_table\" style=\"overflow-y: auto;\"></div> \
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
    <div id=\"new_sample_form\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"register_new_sample_form(update_interval_sample);\">Add sample type</div>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <div id=\"new_sample_form\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"show_sample_selector(update_interval_sample);\">Load registered sample</div> \
</div> \
<div id=\"result_box_samples\"></div>";


var lipid_class_table_view = "<label class=\"wpforms-field-label\">Lipid Classes</label> \
<div id=\"grey_background_class\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 110; background-color: rgba(0, 0, 0, 0.4); display: none;\"></div> \
    <div id=\"class_selector_wrapper\" style=\"top: 0px; left: 0px; width: 100%; height: 100%; position: fixed; z-index: 120; display: none;\"> \
        <div id=\"class_selector_wrapper\" style=\"top: 15%; left: 25%; width: 50%; height: 70%; position: fixed; background: white; border-radius: 5px;\"> \
            <div id=\"control-buttons\" style=\"width: 100%; height: 100%; position: relative;\"> \
                <table style=\"width: 100%; height: 100%; border: 1px solid black;\" cellpadding=\"10px\" id=\"table_wrapper\"> \
                    <tr><td style=\"width: 100%;\"><b style=\"font-size: 20px;\">Registered Lipid classes to workflows</b></td></tr> \
                    <tr><td style=\"width: 100%; height: 80%;\" valign=\"top\" align=\"center\"> \
                        <div id=\"class_forms_table\" style=\"overflow-y: auto;\"></div> \
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
    <div id=\"new_class_form\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"register_new_class_form(update_interval_lipid_class);\">Add lipid class</div>&nbsp;&nbsp;/&nbsp;&nbsp; \
    <div id=\"new_class_form\" style=\"cursor: pointer; color: #0000ff; display: inline-block;\" onclick=\"show_class_selector(update_interval_lipid_class);\">Load registered lipid classes</div> \
</div> \
<div id=\"result_box\"></div>";

var registered_tables = {"sample": sample_table_view, "lipid-class": lipid_class_table_view};
