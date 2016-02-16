#! /bin/bash

LDAPHOST="127.0.0.1"
LDAPPORT="389"
LDAP_BINDDN="cn=wdAdmin,dc=wanda,dc=cn"
LDAP_BINDPW="WDlham318296"
LDAP_BASEDN="dc=wanda,dc=cn"

backup_path=/usr/local/ldap_backup/
time_stamp=`date +'%Y%m%d%H%M%S'`


ldapsearch -x -D "$LDAP_BINDDN" -w "$LDAP_BINDPW" -b "$LDAP_BASEDN" -s sub >  $backup_path/lham_db_backup.${time_stamp}.ldif
