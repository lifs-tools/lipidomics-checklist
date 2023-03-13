<?php
/*
try {
    // initialize wordpress to get access to user id
    include "wp_init.php";
    
    if (!function_exists('get_current_user_id') || get_current_user_id() == 0) {
        echo(-1);
        exit();
    }    
}
catch(Exception $e){
    echo(-1);
    exit();
}
*/

// get all GET and POST variables
$request = array();
foreach($_GET as $key => $val) {
    array_push($request, "$key=" . urlencode($val));
}
foreach($_POST as $key => $val) {
    array_push($request, "$key=" . urlencode($val));
}



array_push($request, "ip=" . urlencode($_SERVER['REMOTE_ADDR']));
array_push($request, "user_agent=" . urlencode($_SERVER['HTTP_USER_AGENT']));
#$user_uuid = !empty( $_COOKIE['_wpfuuid'] ) ? $_COOKIE['_wpfuuid'] : "";
array_push($request, "user_uuid=3e599f6d-476d-4d52-8e19-3ffe6ef7555d");
#array_push($request, "uid=" . get_current_user_id());
array_push($request, "uid=944");


exec("/usr/bin/python3 forms-manager.py \"" . join("&", $request) . "\" 2>&1", $out, $result);
echo($out[0]);
#echo(join("&", $request));
#echo($_POST["command"])

?>
