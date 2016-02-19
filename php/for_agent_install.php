<?php

require_once("basic/basic.php");

$host_name=htmlspecialchars($_GET["whoami"]);
$pass_phrase=htmlspecialchars($_GET["passwd_phrase"]);

$correct_pass_phrase="THIS_IS_LHAM_AGENT_INSTALL_OR_UPDATE_SCRIPT-HELLO_GOD";

$agent_source=WORK_DIR . "/agent/source-release/lham_agent.py";

function release_agent($agent_source) {
    $random_str_1=strval(rand(1,9999));
    $random_str_2=strval(rand(1,9999));
    $random_str_3=strval(rand(1,9999));
    $tmp_release_dir=WORK_DIR . "/agent/pub/tmp_release/$random_str_1/$random_str_2/$random_str_3";

    mkdir($tmp_release_dir, 0755, true);
    copy($agent_source, $tmp_release_dir . "/lham_agent.py");
    
    $release_url = "/agent/pub/tmp_release/$random_str_1/$random_str_2/$random_str_3/lham_agent.py";
    return $release_url;
}


$host_validate=validateHostByHostname($host_name);  
if($host_validate == "host_valid") {
    if ($pass_phrase == $correct_pass_phrase) {
        $agent_download=release_agent($agent_source);
        echo "AGENT_INSTALL_REQUEST_ACCEPTED\n";
        echo "$agent_download\n";
    } else {
	echo "ERROR: pass_phrase error\n"; 
    }
} else {
    echo "$host_validate\n";
} 

?>
