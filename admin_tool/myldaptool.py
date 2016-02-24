#! /usr/bin/python

#--------------------- global variables ----------------------------------

#ldap connection info
LDAPHOST = "127.0.0.1"
LDAPPORT = "389"
LDAP_BINDDN = "cn=wdAdmin,dc=wanda,dc=cn"
LDAP_BINDPW = "WDlham318296"
LDAP_BASEDN = "dc=wanda,dc=cn"

USER_BASEDN = "ou=users,%s" % (LDAP_BASEDN,) 
HOST_BASEDN = "ou=machines,%s" % (LDAP_BASEDN,)

# default password for all user newly added.
default_user_passwd_for_add = "123456"

# Flag used by lham_agent to confirm host_account query is valid.
host_account_query_validation_flag = 'LHAM_BASE_USER_FOR_HOST_ACCOUNT_QUERY_VALIDATION' 
lham_base_user = "uid=%s,ou=users,dc=wanda,dc=cn" % (host_account_query_validation_flag,) 

#key_path for php to distribute public or private key to client host.
default_key_path = "/usr/local/ldapHostAccountManagement/pubkey"
make_key_tool = "/usr/local/ldapHostAccountManagement/bin/keygen.exp"


import sys, os, time, re


def usage():
    print   """
======================================
usage:
    ---- search:
    %s search user <uid>|@all [<attr_name>]   
    %s search host <host_ip>|@all [<attr_name>]        
                    # To search user or host filtered by uid or host_ip.
                    # If '@all' provided instead of <uid> or <host_ip>, all user or host entries will be displayed.
                    # <attr_name> is an optional argument, if not provided, all attributes of this matched entry will be desplayed.  
                        
    ---- add:
    %s add user <uid>               
    %s add user <uid>,<department>
    %s add user <uid>,<department>,<higher_department>,...
                    # To add a user entry into a department which it belongs to. If no department assigned, 
                      add this user to top entry for users: 'ou=users,dc=wanda,dc=cn'.
                    # If only one department assigned, this tool will make a search to find out the dn of this department. If 
                      multi-search-result return, ERROR occured, and you must assign full ou-path of the department.
                    # If two or more departments assigned, it will be considered the full ou-path to 'ou=users,dc=wanda,dc=cn'.
    %s add host <host_ip>,<host_name> 
    %s add host <host_ip>,<host_name>,<host_group>
                    # To add a host entry with a host_group. Unlike users, no department in hosts side. All
                      hosts are one-level sub entries to 'ou=machines,dc=wanda,dc=cn'. But we can assign a 
                      host group tag to a host entry.
    %s add ou ou=xxx,ou=xxx,ou=wanda,ou=cn
                    # To add new ou

    ---- delete:
    %s delete user <uid>            # To delete a user entry, filtered by uid.
    %s delete host <host_ip>        # To delete a host entry, filtered by host_ip.

    ---- modify:
    %s modify user|host <uid>|<host_ip> replace <attr>:<new_value>
    %s modify user|host <uid>|<host_ip> add <attr>:<new_value>
    %s modify user|host <uid>|<host_ip> delete <attr>:(<old_value>|*)
                    # For attr_delete, '<attr>:*' will delete all values about this attribute.

    ---- addHostUser:
    %s addHostUser <uid> <host_ip> [sudoer]
                    # Add a user to a host, so that he can login to that host. If "sudoer" provided, this user will acquire root privilege.
                      If no entry exist for this user, this operation failed with an error prompt.
    ---- deleteHostUser:
    %s deleteHostUser <uid> <host_ip> [sudoer]
                    # Delete a user from a host, entry for the user is not deleted. If no such user for this host, an error prompt.
                      If "sudoer" provided, only remove the root privilege for that host, which means user still can login to that host 
                      with no root privilege.
    ---- searchHostUser:
    %s searchHostUser <uid>
                    #To search which host contain this user. Matched hosts return with dn and ip.
    ---- addTunnelKey:
    %s addTunnelKey <uid> <key_file_path>
                    # add a pubkey provided by user itself, which used to login to a tunnel host.
    
======================================""" % (sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0])

def getRoleType(roleInput):
    if roleInput == "user":
        return USER_BASEDN,"uid"
    elif roleInput == "host":
        return HOST_BASEDN,"ipNetworkNumber"
    elif roleInput == "ou":
        return USER_BASEDN,"ou"
    else:
        print "\nERROR: wrong role type assigned with the second argument."
        sys.exit(1)
    
def getUserDnForAdd(id):
    id_list = id.strip().split(',')
    if len(id_list) == 1:
        tmp_dn = 'uid=%s,%s' % (id_list[0],USER_BASEDN)
    elif len(id_list) == 2:
        ou_dn_search = myldapsearch("ou",id_list[1],"dn",True)
        if ou_dn_search == []:
            print "\nERROR: not such department: %s" % (id_list[1],)
            sys.exit(1)
        else:
            ou_dn_search.remove("")
            if len(ou_dn_search) == 1:
                tmp_dn = 'uid=%s,%s' % (id_list[0],ou_dn_search[0].split(':')[1].strip()) 
            else:
                print "ERROR: assigned department is not uniq: "
                for i in ou_dn_search:
                    print i
                sys.exit(1)
    else:
        tmp_dn = 'uid=%s' % (id_list[0],)
        for i in range(1,len(id_list)):
            tmp_dn += ',ou=%s' % (id_list[i],) 
        tmp_dn += ("," + USER_BASEDN)

    return tmp_dn,id_list[0]

def getHostDnForAdd(id):
    id_list = id.strip().split(',')
    if len(id_list) == 1:
        print "\nERROR: need both <host_ip> and <host_name>. "
        sys.exit(1)
    elif len(id_list) == 2:
        return id_list[0],id_list[1]
    elif len(ld_list) == 3:
        print "Note: host_group not supported yet. Please wait for the next version."
        return id_list[0],id_list[1]
        
    
def getNextUidnumber():
    tmp_f = os.popen("ldapsearch -LLL -x -h %s -p %s -w %s -D '%s' -b %s '(%s=*)'" % (LDAPHOST, LDAPPORT, LDAP_BINDPW, LDAP_BINDDN, USER_BASEDN, "uidNumber") + " | awk -F':' '/^uidNumber/ {print $2}' | sort -n | tail -1")
    return_str = tmp_f.readline().strip()
    if return_str == "":
        return 1000
    else:
        return int(return_str) + 1

def myRegMatch(reg_str, target_str):
    reg_obj = re.compile("^ [^ ].*$")
    if reg_obj.search(target_str) != None:
        return 1
    else:
        return 0 

def myldapsearch(role_type, id, attr='',no_print=False):
    role = getRoleType(role_type)
    if id == '@all':
        id = "*"
    tmp_f = os.popen("ldapsearch -LLL -x -h %s -p %s -w %s -D '%s' -b %s '(%s=%s)' %s" % (LDAPHOST, LDAPPORT, LDAP_BINDPW, LDAP_BINDDN, role[0], role[1], id, attr))
    tmp_f_list = []
    while True:
        line = tmp_f.readline()
        if line == '':
            break
        if no_print == False:
            print line.rstrip()
        tmp_f_list.append(line.rstrip())

    tmp_f_list_return = []
    for i in tmp_f_list:
        if myRegMatch("^ [^ ].*$", i) == 1:
            tmp_f_list_return[-1] += i.strip()
        else:
            tmp_f_list_return.append(i)
    return tmp_f_list_return

def writeTmpLdif(file_list):
    tmp_f_path = 'tmp_%s.ldif' % (str(time.time()))
    tmp_f = open(tmp_f_path,'w')
    for line in file_list:
        tmp_f.write(line+'\n')
    tmp_f.close()
    return tmp_f_path
    
    

def myldapadd(role_type,id):
    if role_type == "user":
        userDn = getUserDnForAdd(id)
        nextUidNum = getNextUidnumber()
        ldif_temp = [
            "dn: %s" % (userDn[0]),
            "objectclass: inetOrgPerson",
            "objectclass: posixAccount",
            "objectclass: shadowAccount",
            "uid: %s" % (userDn[1],),
            "cn: %s" % (userDn[1],),
            "sn: %s" % (userDn[1],),
            "uidNumber: %d" % (nextUidNum,),
            "gidNumber: %d" % (nextUidNum,),
            "userPassword: %s" % (default_user_passwd_for_add,),
            "homeDirectory: /home/%s" % (userDn[1],),
            "loginShell: /bin/bash" ]
    elif role_type == "host":
        hostInfo = getHostDnForAdd(id)
        ldif_temp = [
            "dn: cn=%s,%s" % (hostInfo[1],HOST_BASEDN),
            "objectclass: ipNetwork",
            "ipNetworkNumber: %s" % (hostInfo[0],),
            "cn: %s" % (hostInfo[1],),
            "manager: %s" % (lham_base_user,) ]
    elif role_type == "ou":
        ou_id=id.split(',')[0].split('=')[1]
        ou_dn=id
        ldif_temp = [
            "dn: %s" % (ou_dn,),
            "objectclass: organizationalUnit",
            "ou: %s" % (ou_id,) ]
    else:
        print "\nERROR: wrong role_type assigned with the second argument."
        sys.exit(1)

    tmp_f_path = writeTmpLdif(ldif_temp)
    os.system("ldapadd -x -h %s -p %s -w %s -D '%s' -f %s" % (LDAPHOST, LDAPPORT, LDAP_BINDPW, LDAP_BINDDN, tmp_f_path))
    os.system("rm -f " + tmp_f_path)

def myldapdelete(role_type,id):
    tmp_list = myldapsearch(role_type, id)
    if tmp_list != []:
        this_dn = tmp_list[0].split(':')[1].strip()
        print this_dn
        if raw_input('Do you really want to delete this entry? [y/n] ') in 'yY':
            os.system("ldapdelete -x -h %s -p %s -w %s -D '%s' %s" % (LDAPHOST, LDAPPORT, LDAP_BINDPW, LDAP_BINDDN, this_dn))
        else:
            print "OK, no change!"
    else:
        print "no entry found with this: %s" % (id,)

def myldapmodify(role_type,id,modify_type,modify_attr):
    attr_list = modify_attr.split(':')
    attr_name = attr_list[0].strip()
    if len(attr_list) >=2:
        attr_value = ''.join(attr_list[1:]).strip()
    else:
        print "\nERROR: wrong attr provided."
        sys.exit(1)

    this_entry = myldapsearch(role_type,id,'dn',True)
    if this_entry == []:
        print "\nERROR: not such entry!"
        sys.exit(1)
    if not modify_type in ['replace','add','delete']:
        print "\nERROR: wrong attr provided."
        sys.exit(1)

    for this_dn in this_entry:
        if this_dn != '':
            ldap_modify = [
                this_dn,
                "changetype: modify",
                "%s: %s" % (modify_type, attr_name), 
                "%s: %s" % (attr_name, attr_value) ] 
            if modify_type == 'delete' and attr_value == "*":
                ldap_modify.pop()
            
            ldif_path = writeTmpLdif(ldap_modify)
            os.system("ldapmodify -x -h %s -p %s -w %s -D '%s' -f %s" % (LDAPHOST, LDAPPORT, LDAP_BINDPW, LDAP_BINDDN, ldif_path))
            os.system("rm -f " + ldif_path)

def modifyHostUser(user_id, host_ip,addOrDelete):
    user_entry = myldapsearch("user",user_id,'dn',True)
    if user_entry == []:
        print "\nERROR: invalid_user: %s" % (user_id,)
        sys.exit(1)
    user_dn = user_entry[0].split(':')[1].strip()
    myldapmodify("host", host_ip, addOrDelete, "manager: %s" % (user_dn,))  

    #make keyPair for user.
    user_key_path    = default_key_path + '/' + user_id
    user_private_key = user_key_path + '/' + 'id_rsa_' + user_id
    user_public_key  = user_private_key + '.pub'

    if addOrDelete == "add" and (not os.path.isfile(user_public_key)):
        print "making rsa-key-pair for user '%s'......" % (user_id,)
        if not os.path.isdir(user_key_path):
            os.system("mkdir %s && chmod 0700 %s && chown lham:lham %s" % (user_key_path,user_key_path,user_key_path))
        else:
            os.system("/bin/rm -f %s/id_rsa_*" % (user_key_path,))

        os.system("/usr/bin/expect %s %s > /dev/null" % (make_key_tool,user_id))
        if os.path.isfile(user_private_key) and os.path.isfile(user_public_key):
            os.system("chown lham:lham %s/id_rsa_* " % (user_key_path,))
            print "making rsa-key-pair for user succeed!"
        else:
            print "ERROR: making rsa-key-pair for user failed!!!"

def addUserPubkeyToTunnel(user_id, key_path):
    if myldapsearch("user", user_id, "dn", True) == []:
        print "\nERROR: invalid user!"
        sys.exit(1)
    if os.path.isfile(key_path):
        tunnel_key_dir  = default_key_path + '/' + user_id
        tunnel_key_path = default_key_path + '/' + user_id + '/tunnel_' + user_id + '.pub'
        if not os.path.isdir(tunnel_key_dir):
            os.system("mkdir %s && chmod 0700 %s && chown lham:lham  %s" % (tunnel_key_dir,tunnel_key_dir,tunnel_key_dir))
        if os.path.isfile(tunnel_key_path):
            print "Note: tunnel_%s.pub already exists!" % (user_id,)
            if raw_input("remove the old one? [y/n] ") in 'yY':
                os.system("rm -f %s" % (tunnel_key_path))
            else:
                print "OK, no change."
                sys.exit(0)
        tmp_key_fl = open(key_path)
        tmp_key_fl_list = tmp_key_fl.readlines()
        if len(tmp_key_fl_list) == 0:
            print "\nERROR: input key file is empty." 
            sys.exit(1)
        elif len(tmp_key_fl_list) == 1:
            os.system("cp %s %s" % (key_path,tunnel_key_path)) 
        else:
            tmp_keygen_file = "ssh_keygen_tmp_file_9087u83746rtfgar78yuhd72"
            rtcd = os.system("ssh-keygen -i -f %s > %s" % (key_path,tmp_keygen_file))
            if rtcd != 0:
                os.system("rm -f " + tmp_keygen_file)
                print "\nERROR: invalid public key."
                sys.exit(1)
            os.system("mv %s %s" % (tmp_keygen_file, tunnel_key_path))
        os.system("chmod 0644 %s && chown lham:lham %s" % (tunnel_key_path,tunnel_key_path))
        print "tunnel_key: %s successfully generated." % (tunnel_key_path)
    else:
        print "\nERROR: Invalid input file."
        sys.exit(1)

def searchHostUser(user_id):
    user_dn = myldapsearch("user",user_id,"dn",True)
    if user_dn == []:
        print "\nERROR: user invalid."
        sys.exit(1)
    user_dn.remove("")
    if len(user_dn) != 1:
        print "\nERROR: more than one user entry found."
        sys.exit(1)
    user_dn_abs=user_dn[0].split(':')[1].strip()
    os.system("ldapsearch -LLL -x -h %s -p %s -w %s -D '%s' -b %s '(%s=%s)' %s" % (LDAPHOST, LDAPPORT, LDAP_BINDPW, LDAP_BINDDN, HOST_BASEDN, "manager", user_dn_abs, "ipNetworkNumber"))
    
        

#=================== main ====================

if __name__ == '__main__':
    arg_len = len(sys.argv)
    if arg_len < 3:
        usage()
        sys.exit(1)
    if arg_len == 3 and sys.argv[1] == "searchHostUser":
        searchHostUser(sys.argv[2])
    elif sys.argv[1] == "search":
        if arg_len == 4:
            myldapsearch(sys.argv[2], sys.argv[3])
        elif arg_len == 5:
            myldapsearch(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "add":
        myldapadd(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "delete":
        myldapdelete(sys.argv[2], sys.argv[3]) 
    elif sys.argv[1] == "modify":
        if arg_len != 6:
            print "\nERROR: wrong usage with modify operation."
            sys.exit(1)
        myldapmodify(sys.argv[2], sys.argv[3],sys.argv[4],sys.argv[5])
    elif sys.argv[1] == "addHostUser":
        if len(sys.argv) == 5 and sys.argv[4] == "sudoer":
            #addHostUser(sys.argv[2], sys.argv[3],True)
            print "Sudoer not support yet! Please wait for the next version."
        else:
            modifyHostUser(sys.argv[2], sys.argv[3],"add")
        
    elif sys.argv[1] == "deleteHostUser":
	if arg_len < 4:
            usage()
            sys.exit(1)
        to_delete_user=sys.argv[2]
        target_host=sys.argv[3]
        print "===> Warning: All things about user '%s' will delete on target host '%s'." % (to_delete_user, target_host)
        answer=raw_input("Do really want to delete '%s' on host '%s'? [y/n]" % (to_delete_user, target_host))
        if answer == 'y' or answer == 'Y':
            if len(sys.argv) == 5 and sys.argv[4] == "sudoer":
                #deleteHostUser(sys.argv[2], sys.argv[3],True)
                print "Sudoer not support yet! Please wait for the next version."
            else:
                modifyHostUser(sys.argv[2], sys.argv[3],"delete")
        else:
            print "===> OK. deleteHostUser abort."
            sys.exit(0)
    elif sys.argv[1] == "addTunnelKey":
        addUserPubkeyToTunnel(sys.argv[2],sys.argv[3])
    else:
        usage()
        
