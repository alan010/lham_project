<?php

require_once("basic/basic.php");

$host_ip=htmlspecialchars($_GET["myPrimeIP"]);
$host_name=htmlspecialchars($_GET["whoami"]);
if ( preg_match("/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/", $host_ip) === 1 ) {
	queryHost($host_ip,"manager");  //by now, only 'manager' supported. If want to query another host attr, please rewrite the function.
} else if ($host_name != "") {
	queryHostByHostname($host_name,"manager");
} else echo "ERROR: bad_request\n";

?>
