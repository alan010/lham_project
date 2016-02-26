<?php

#------ ldap connection info -----
define("LDAP_HOST" , "127.0.0.1");
define("LDAP_PORT" , "389");
define("LDAP_BINDDN" , "cn=wdAdmin,dc=wanda,dc=cn");
define("LDAP_BINDPW" , "WDlham318296");
define("LDAP_BASE_DN" , "dc=wanda,dc=cn");
define("USER_BASE_DN" , "ou=users," . LDAP_BASE_DN);
define("HOST_BASE_DN" , "ou=machines," . LDAP_BASE_DN);

#------ local environment -------
define("WORK_DIR", "/usr/local/ldapHostAccountManagement");
define("KEY_GEN_DIR",WORK_DIR . "/pubkey");

?>
