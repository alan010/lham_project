<?php

require_once("basic/basic.php");

$host_ip=htmlspecialchars($_GET["myPrimeIP"]);
if ( preg_match("/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/", $host_ip) === 1 ) {
	queryHost($host_ip,"manager");  //by now, only 'manager' supported. If want to query another host attr, please rewrite the function.
} else echo "ERROR: bad_request\n";

?>
