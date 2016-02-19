<?php

require_once("basic/basic.php");

$host_name=htmlspecialchars($_GET["whoami"]);
$cache_path=htmlspecialchars($_GET["cache_path"]);



function clean_cache($path) {
    unlink($path);

    $dir_name=dirname($path);
    for($i=1; $i<=3; $i++) {
        rmdir($dir_name);
	$dir_name=dirname($dir_name);
    }

}

$host_validate=validateHostByHostname($host_name);  
if($host_validate == "host_valid") {
    clean_cache(WORK_DIR . $cache_path);
}
?>
