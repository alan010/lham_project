<?php

require_once("config.php");

function validateUser($uid_input) {
        $ldap_conn = ldap_connect(LDAP_HOST,LDAP_PORT);
        if(ldap_bind($ldap_conn,LDAP_BINDDN,LDAP_BINDPW)) {
                if ($result_object = ldap_search($ldap_conn,USER_BASE_DN,"(uid=$uid_input)",array('uid'))) {
                        $info = ldap_get_entries($ldap_conn,$result_object);
                        if ($info['count'] !== 0 ) {
                                //echo $info[0]['uid'][0] . "\n";
                                return "user_valid";
                        } else return "ERROR: user_invalid"; 
                } else return "ERROR: user_query_error";
        } else return "ERROR: ldap_service_error";

} // validateUser() complete.

function validateHost($ip_input) {
        $ldap_conn = ldap_connect(LDAP_HOST,LDAP_PORT);
        if(ldap_bind($ldap_conn,LDAP_BINDDN,LDAP_BINDPW)) {
                if ($result_object = ldap_search($ldap_conn,HOST_BASE_DN,"(ipNetworkNumber=$ip_input)",array('ipNetworkNumber'))) {
                        $info = ldap_get_entries($ldap_conn,$result_object);
                        if ($info['count'] !== 0 ) {
                                //echo $info[0]['uid'][0] . "\n";
                                return "host_valid";
                        } else return "ERROR: host_invalid"; 
                } else return "ERROR: host_query_error";
        } else return "ERROR: ldap_service_error";

} // validateHost() complete. 'will be aborted'

function validateHostByHostname($hostname_input) {
        $ldap_conn = ldap_connect(LDAP_HOST,LDAP_PORT);
        if(ldap_bind($ldap_conn,LDAP_BINDDN,LDAP_BINDPW)) {
                if ($result_object = ldap_search($ldap_conn,HOST_BASE_DN,"(cn=$hostname_input)",array('cn'))) {
                        $info = ldap_get_entries($ldap_conn,$result_object);
                        if ($info['count'] !== 0 ) {
                                //echo $info[0]['uid'][0] . "\n";
                                return "host_valid";
                        } else return "ERROR: host_invalid"; 
                } else return "ERROR: host_query_error";
        } else return "ERROR: ldap_service_error";

} // validateHostbyHostname() complete.

function queryHost($host_ip,$host_attr) {
        $ldap_conn = ldap_connect(LDAP_HOST,LDAP_PORT);
        if(ldap_bind($ldap_conn,LDAP_BINDDN,LDAP_BINDPW)) {
                if ($result_object = ldap_search($ldap_conn,HOST_BASE_DN,"(ipNetWorkNumber=$host_ip)",array($host_attr))) {
                        $info = ldap_get_entries($ldap_conn,$result_object);
                        if ($info['count'] == 0 ) {
				echo "ERROR: host_invalid";
                        } else if($info['count'] == 1) {
				if (($user_count = $info[0][$host_attr]["count"]) >= 1){
					for($i=0; $i<$user_count; $i++) {
						$user_dn_split = preg_split('/[=,]+/',$info[0][$host_attr][$i]);
						echo $user_dn_split[1] . "\n";
					}
				} else echo "ERROR: bad_host_entry";
			} else echo "ERROR: ip_not_uniq_in_ldap"; 
                } else echo"ERROR: host_query_error";
        } else echo "ERROR: ldap_service_error";
}

function queryHostByHostname($hostname,$host_attr) {
        $ldap_conn = ldap_connect(LDAP_HOST,LDAP_PORT);
        if(ldap_bind($ldap_conn,LDAP_BINDDN,LDAP_BINDPW)) {
                if ($result_object = ldap_search($ldap_conn,HOST_BASE_DN,"(cn=$hostname)",array($host_attr))) {
                        $info = ldap_get_entries($ldap_conn,$result_object);
                        if ($info['count'] == 0 ) {
				            echo "ERROR: host_invalid";
                        } else if($info['count'] == 1) {
				            if (($user_count = $info[0][$host_attr]["count"]) >= 1){
					            for($i=0; $i<$user_count; $i++) {
						            $user_dn_split = preg_split('/[=,]+/',$info[0][$host_attr][$i]);
						            echo $user_dn_split[1] . "\n";
					            }
				            } else echo "ERROR: bad_host_entry";
			            } else echo "ERROR: hostname_not_uniq_in_ldap"; 
                } else echo"ERROR: host_query_error";
        } else echo "ERROR: ldap_service_error";
}

?>
