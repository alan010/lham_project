<?php
$VERSION_INFO_FILE = "/usr/local/ldapHostAccountManagement/agent/agent_version.ini";
$CHECK_SUCESS_FLAG = "VERSION_CHECK_SUCCESS";
$AGENT_PROGRAM_FILE = "/usr/local/ldapHostAccountManagement/agent/pub/lham_agent";

require_once("basic/basic.php");

/*
function file_download($file_path) {
	$file=fopen($file_path,"r");
	header("Content-Type: application/octet-stream");
	header("Accept-Ranges: bytes");
	header("Accept-Length: ".filesize($file_path));
	header("Content-Disposition: attachment; filename=lham_agent");
	echo fread($file,filesize($file_path));
	fclose($file);
}
*/
$host_ip=htmlspecialchars($_GET["myPrimeIP"]);
//$host_cert=htmlspecialchars($_GET["myCert"]);

if ( preg_match("/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/", $host_ip) === 1 ) {
	if (($validate_result = validateHost($host_ip)) == "host_valid") {
		echo "$CHECK_SUCESS_FLAG\n";
		echo shell_exec("/bin/cat " . $VERSION_INFO_FILE);
	} else echo "$validate_result\n";
} else echo "ERROR: bad_request\n";
?>
