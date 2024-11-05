<?php




////////////////////////////////////////////////////////////////////////////
// read in config file
////////////////////////////////////////////////////////////////////////////
$conf_file_path = "db/ChecklistConfig.py";

try {
    $conf_file = fopen($conf_file_path, "r") or die("Unable to open file!");
    $conf_data = fread($conf_file, filesize($conf_file_path));
    fclose($conf_file);
}
catch(Exception $e){
    echo("ErrorCodes.CONFIG_EXCEPTION");
    exit();
}

$conf_data = explode("\n", $conf_data);
$config = array();

foreach ($conf_data as $row){
    $pos = strpos($row, "#");
    if ($pos === false) $pos = strlen($row);
    $substr = substr($row, 0, $pos);
    if (strlen($substr) == 0) continue;
    
    $tokens = explode("=", $substr);
    if (sizeof($tokens) != 2) continue;

    $key = trim($tokens[0], " ");
    $value = trim($tokens[1], " ");
    
    if ($key[0] == "'") $key = trim($key, "'");
    else if ($key[0] == "\"") $key = trim($key, "\"");
    
    if ($value[0] == "'") $value = trim($value, "'");
    else if ($value[0] == "\"") $value = trim($value, "\"");
    
    $config[$key] = $value;
}

if (!isset($config["machine"])){
    echo("ErrorCodes.CONFIG_CONTENT_EXCEPTION");
    exit();
}


if ($config["machine"] != "home"){
    
    try {
        // initialize wordpress to get access to user id
        include "../wp-load.php";
        
        if (!function_exists('get_current_user_id') || get_current_user_id() == 0) {
            echo("ErrorCodes.NO_WORDPRESS_CONNECTION");
            exit();
        }    
    }
    catch(Exception $e){
        echo("ErrorCodes.WORDPRESS_EXCEPTION");
        exit();
    }
}



////////////////////////////////////////////////////////////////////////////
// get all GET and POST variables
////////////////////////////////////////////////////////////////////////////
$request = array();
foreach($_GET as $key => $val) {
    array_push($request, "$key=" . rawurlencode($val));
}
foreach($_POST as $key => $val) {
    array_push($request, "$key=" . urlencode($val));
}

////////////////////////////////////////////////////////////////////////////
// collect all information for the request
////////////////////////////////////////////////////////////////////////////
if (!isset($_SERVER['REMOTE_ADDR'])) {
    $_SERVER['REMOTE_ADDR'] = '127.0.0.1';
}
array_push($request, "ip=" . rawurlencode($_SERVER['REMOTE_ADDR']));
if (!isset($_SERVER['HTTP_USER_AGENT'])) {
    $_SERVER['HTTP_USER_AGENT'] = 'CLI';
}
array_push($request, "user_agent=" . rawurlencode($_SERVER['HTTP_USER_AGENT']));
$user_id = 0;
if ($config["machine"] != "home"){
    $user_uuid = !empty( $_COOKIE['_wpfuuid'] ) ? $_COOKIE['_wpfuuid'] : "";
    array_push($request, "user_uuid=" . $user_uuid);
    array_push($request, "uid=" . get_current_user_id());
    $user_id = get_current_user_id();
}
else {
    array_push($request, "user_uuid=" . rawurlencode("3e599f6d-476d-4d52-8e19-3ffe6ef7555d"));
    array_push($request, "uid=2");
    $user_id = 2;
}

// if the request is too big, write in file and send over the filename
$request_join = join("&", $request);
if (strlen($request_join) > 65536){
    $file_name = 'db/request-' . $user_id . '.txt';
    file_put_contents($file_name, $request_join);
    $request_join = "request_file=" . $file_name;
}




////////////////////////////////////////////////////////////////////////////
// send request
////////////////////////////////////////////////////////////////////////////
exec("/usr/bin/python3 FormsManager.py \"" . $request_join . "\" 2>&1", $out, $result);
echo($out[0]);


?>
