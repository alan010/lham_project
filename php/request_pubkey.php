<?php

require_once("basic/basic.php");

function deliverPubkey($uid_input, $host_role) {
	$private_key_path = KEY_GEN_DIR . "/$uid_input/id_rsa_$uid_input";
	$public_key_path  = KEY_GEN_DIR . "/$uid_input/id_rsa_$uid_input.pub";
	if($host_role === "jumper") {
		if(is_file($private_key_path)) {
			echo "private_key_for_user: $uid_input\n";
			echo shell_exec("/bin/cat " . $private_key_path);
		} else {
			echo "ERROR: private_key missing on server for user: $uid_input\n";
		}
	} else if($host_role == "client") {
		if (is_file($public_key_path)) {
			echo "public_key_for_user: $uid_input\n";
			echo shell_exec("/bin/cat " . $public_key_path);	
		} else {
			echo "ERROR: public_key missing on server for user: $uid_input\n";
		}
	} else echo "ERROR: bad_request\n";
}

function deliverTunnelKey($uid_input, $host_role) {
	$tunnel_pubkey_path = KEY_GEN_DIR . "/$uid_input/tunnel_$uid_input.pub";
	if(($host_role === "jumper") or ($host_role === "directLogin")) {
		if(is_file($tunnel_pubkey_path)) {
			echo "tunnel_key_for_user: $uid_input\n";
			echo shell_exec("/bin/cat " . $tunnel_pubkey_path);
		} else echo "ERROR: tunnel_key missing for user: $uid_input\n";
	} else echo "ERROR: bad_request\n";
	
}


#----------------- main -------------------

//$myIdInfo=htmlspecialchars($_GET["myIdInfo"]);
$pubKeyUser=trim(htmlspecialchars($_GET["pubKeyUser"]));
$hostRole = trim(htmlspecialchars($_GET["hostRole"]));
$keyType  = trim(htmlspecialchars($_GET["keyType"]));

if ($pubKeyUser == "" or $hostRole == "" or $keyType == "") echo "ERROR: bad_request\n";  
else if (($validate_result = validateUser($pubKeyUser)) === "user_valid") {
	if ($keyType === "serverKey") { 
		deliverPubkey($pubKeyUser,$hostRole);
	} else if ($keyType === "tunnelKey") {
		deliverTunnelKey($pubKeyUser,$hostRole);
	} else echo "ERROR: bad_key_type\n";
} else echo "$validate_result\n";

?>
