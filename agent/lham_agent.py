#! /usr/bin/python

#------ LDAP-host-account-management client info
MY_ROLE = "client" #can be: 'client','jumper','directLogin'
MY_VERSION = "0.5.5"

#LHAM_HOST = "lham.dianshang.wanda.cn"
LHAM_HOST = "10.209.11.12"
LHAM_PORT = "11306"
#LHAM_PORT_FOR_CLIENT_UPDATE = "11307"
URL_PREFIX_users = "http://%s:%s/query_host.php?myPrimeIP=" % (LHAM_HOST,LHAM_PORT)
URL_PREFIX_pubkey = "http://%s:%s/request_pubkey.php?" % (LHAM_HOST,LHAM_PORT)
URL_PREFIX_feedback = "http://%s:%s/get_feedback.php?" % (LHAM_HOST,LHAM_PORT)
URL_PREFIX_versionCheck = "http://%s:%s/version_check.php?" % (LHAM_HOST,LHAM_PORT)
RUN_INTERVAL = 5 #minutes interval running in crontab.
QUERY_VALIDATION_FLAG="LHAM_BASE_USER_FOR_HOST_ACCOUNT_QUERY_VALIDATION"

#------ local environment
WORKDIR = "/usr/local/lham_agent"
DATADIR = WORKDIR + '/data'
DATAFILE = DATADIR + "/lham_agent.data"
DELETED_RECORD = DATADIR + "/deleted_record.data"
LOG = "/var/log/lham_agent.log"
REMOVE_DIR="/tmp/lham_agent_for_file_rm"

import os, sys, time
import platform, re

def timer(type='log'):
    if type == 'log':
        return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
    elif type == 'stamp':
        return time.strftime("%Y%m%d%H%M%S",time.localtime(time.time()))
    else:
        return "NULL_TIME"

def loger(content, type="INFO"):
    if type == "ERROR":
        print "%s [ERROR] %s" % (timer('log'),content)
    else: 
        print "%s [INFO] {%s}" % (timer('log'),content)

def crontabCheck():
    return os.system("cat /etc/crontab | grep '%s/%s' > /dev/null" % (WORKDIR,os.path.basename(sys.argv[0])))

def safeRmFile(file_or_dir_path):
    if not os.path.isdir(REMOVE_DIR):
        os.system('mkdir -p  ' + REMOVE_DIR)
    rename_base=os.path.basename(file_or_dir_path)
    time_stamp=timer('stamp')
    rec_code = os.system('mv %s %s' % (file_or_dir_path, REMOVE_DIR + '/' + rename_base + '_' + time_stamp))
    return rec_code
    

def initWork():
    os.system("mkdir -p %s" % (DATADIR,))
    os.system("mkdir -p %s" % (REMOVE_DIR,))
    os.system("chmod 0700 %s" % (DATADIR,))
    os.system("cp -f %s %s" % (sys.argv[0],WORKDIR)) 
    loger('init: making workdir complete.')

    #ret_code = crontabCheck()
    #if ret_code == 256:
    #    os.system("echo '*/%s * * * * root /usr/bin/python2.6 %s/%s %s >> %s 2>&1' >> /etc/crontab" % (RUN_INTERVAL,WORKDIR,os.path.basename(sys.argv[0]),MY_ROLE,LOG))
    #    loger("init: adding crontab complete.")
    #elif ret_code == 0:
    #    loger("init: crontab for this program already exists.")

    ret_code = os.system("rpm -qa | grep ^curl- > /dev/null")
    if ret_code == 256:
        ret_code2 = os.system("yum install -y curl")
        if ret_code2 != 0:
            loger("curl: not available and installing by yum failed!","ERROR")
            sys.exit(1)
    loger("init: Initializing of lham_agent complete.")

def getOSVersion():
    vender_reg  = re.compile('^CentOS')
    centos7_reg = re.compile('^7')
    centos6_reg = re.compile('^6')

    if vender_reg.search(platform.linux_distribution()[0]) != None :
        if centos7_reg.search(platform.linux_distribution()[1]) != None:
            return 'Centos7'
        elif centos6_reg.search(platform.linux_distribution()[1]) != None:
            return 'Centos6'
        else:
            loger('getOSVersion: Not supported OS version: ' + platform.linux_distribution()[1] + '. Only Centos6/7 supported.', 'ERROR')
            sys.exit(1)
    else:
        loger('getOSVersion: Not supported OS: ' + platform.linux_distribution()[0] + '. Only Centos6/7 supported.', 'ERROR')
        sys.exit(1)
    

def getPrimeIP():
    os_version = getOSVersion()
    if os_version == 'Centos6':
        tmp_f = os.popen("ifconfig  |  awk -F'addr:' '/inet addr:10.*Bcast.*Mask/ {print $2}' | awk '{print $1}'")
    elif os_version == 'Centos7':
        tmp_f = os.popen("ifconfig | grep 'inet.*netmask.*broadcast' | awk -F'inet ' '{print $2}' | awk '{print $1}'")
    first_ip = tmp_f.readline().strip()

    return first_ip

def fileObjectToList(fileObj):
    file_list = []
    while True:
        line = fileObj.readline()
        if line == "":
            break
        file_list.append(line.strip())
        
    return file_list
    
    
def getChange(myIP):
    tmp_f = os.popen("curl -s '%s%s'" % (URL_PREFIX_users,myIP))
    user_list = fileObjectToList(tmp_f)
    if QUERY_VALIDATION_FLAG in user_list:
        user_list.remove(QUERY_VALIDATION_FLAG)
    else:
        loger('get change: LDAP query failed!',"ERROR") 
        sys.exit(1)

    if not os.path.isfile(DATAFILE):
        old_user_list = []
    else:
        old_f = open(DATAFILE)
        old_user_list =  fileObjectToList(old_f)

    dict_change = {"newUserList":user_list,"delete":[],"add":[]}
    for newuser in user_list:
        if not newuser in old_user_list:
            dict_change["add"].append(newuser)
    for olduser in old_user_list:
        if not olduser in user_list:
            dict_change["delete"].append(olduser)
        
    return dict_change

def addNewUser(user_list):
    for user in user_list:
        ret_code = 0
        ret_code += os.system("groupadd  %s" % (user,))
        ret_code += os.system("useradd %s -g %s -m -d /home/%s -s /bin/bash" % (user,user,user))
        if ret_code == 0:
            loger("add user: '%s'" % (user,))
        if ret_code == 18:
            loger("add user: '%s' already existed.")
        os.system("chown -R %s:%s /home/%s" % (user,user,user))

def deleteUser(user_list):
    deleted_record_f = open(DELETED_RECORD,'a')
    for user in user_list:
        ret_code = os.system("userdel  %s" % (user,))
        if ret_code == 0:
            deleted_record_f.write("%s\n" % (user,))
            loger("delete user: '%s'" % (user,))
            #loger("delete user: homedir '/home/%s' will be deleted at 02:00 am next day." % (user,))
        elif ret_code == 1536 and os.path.isdir('/home/%s' % (user,)):
            deleted_record_f.write("%s\n" % (user,))
            loger("delete user: '%s' user not exist, but its'homedir does. This homedir will be deleted at 02:00 am next day." % (user,))
        elif ret_code == 2048:
            deleted_record_f.write("%s\n" % (user,))
            os.system("ps aux | grep sshd | grep -v '/usr/sbin/sshd' | egrep '%s(@| )' | awk '{print \"kill -9 \" $2}' | sh" % (user,))
            ret_code = os.system("userdel  %s" % (user,))
            if ret_code == 0:
                loger("delete user: '%s'" % (user,))
            else:
                loger("delete user: '%s' failed with error number: %d" % (user,ret_code), 'ERROR')
    deleted_record_f.close()
    os.system('chmod 0600 %s' % (DELETED_RECORD,))

def deleteUserHomeDir(time_start):
    current_hour = time_start.split()[1].split(':')[0]  
    current_min  = time_start.split()[1].split(':')[1]
    if current_hour == "02" and int(current_min) < RUN_INTERVAL and os.path.isfile(DELETED_RECORD):
        users_list_f = open(DELETED_RECORD)
        users_list = fileObjectToList(users_list_f)
        for user in users_list:
            user_homedir = '/home/%s' % (user,)
            if os.path.isdir(user_homedir):
                ret_code = safeRmFile(user_homedir)
                if ret_code == 0:
                    loger("delete homeDir: '%s'" % (user_homedir,))
            else:
                loger("delete homeDir: '%s' not exits." % (user_homedir,) )
        users_list_f.close()
        safeRmFile(DELETED_RECORD)

def replaceDataFile(change_dict):
    if change_dict["add"] != [] or change_dict["delete"] != []:
        new_data_f = open(DATAFILE,'w')
        for i in change_dict['newUserList']:
            new_data_f.write('%s\n' % (i,))
        new_data_f.close()
        os.system('chmod 0600 %s' % (DATAFILE,))

def feedbackForJumper(user_id):
    if MY_ROLE == "jumper":
        tmp_f = os.popen("curl -s '%s%s'" % (URL_PREFIX_feedback, "jmpFeedback=PRIVATE_KEY_RECEIVED_SUCCESS&userid=" + user_id))
        return_list = fileObjectToList(tmp_f)
        if return_list == []:
            return False
        elif return_list[0] == "PRIVATE_KEY_DELIVER_COMPLETE":
            return True
        else:
            return False
    else:
        return True

def getPubKey(user_id, key_type):
    tmp_f = os.popen("curl -s -m 5 '%s%s'" % (URL_PREFIX_pubkey,"pubKeyUser=%s&hostRole=%s&keyType=%s" % (user_id,MY_ROLE,key_type)))
    return_list = fileObjectToList(tmp_f)
    return_list_len = len(return_list)
    if return_list_len == 0:
        loger("getPubKey: server no response, user: " + user_id, "ERROR")
        return False
    else:
        return_status = return_list[0]
        return_key = return_list[1:]
        if "ERROR" in return_status:
            loger("getPubKey: server refuse with message '%s'" % (return_status,), "ERROR")  
            return False
        elif return_key == []:
            loger("getPubKey: content of key lost", "ERROR")
            return False
        elif "private_key_for_user" in return_status:
            return "private_key_for_user",return_key
        elif "tunnel_key_for_user" in return_status:
            return "tunnel_key_for_user",return_key
        elif "public_key_for_user" in return_status:
            return "public_key_for_user",return_key
        else:
            loger("getPubKey: bad server response.","ERROR")
            return False

def writeKey(user_id,key_type_str,key_content_list):
    key_dir = "/home/%s/.ssh" % (user_id,)
    key_path = ""
    if not os.path.isdir(key_dir):
        os.system("mkdir -p %s && chmod 0700 %s" % (key_dir,key_dir))
    if key_type_str == "private_key_for_user" and MY_ROLE == "jumper":
        key_path = key_dir + '/id_rsa'  
        open_flag = 'w'
        file_mask = '0400'
    elif key_type_str == "tunnel_key_for_user" and ( MY_ROLE == "jumper" or MY_ROLE == "directLogin" ):
        key_path = key_dir + '/authorized_keys'
        open_flag = 'a'
        file_mask = "0644"
    elif key_type_str == "public_key_for_user" and MY_ROLE == "client" :
        key_path = key_dir + "/authorized_keys"
        open_flag = 'a'
        file_mask = "0644"

    if key_path != "":
        key_f = open(key_path,open_flag)
        for line in key_content_list:
            key_f.write(line + '\n')
        key_f.close()
        os.system("chown -R %s:%s %s" % (user_id,user_id,key_dir))
        os.system("chmod %s %s" % (file_mask, key_path))

def keyContentCompare(key_server_side,key_client_side):
    """ 
    If content of local key is not right according to key got from lham server, return True.
    If not, return False.
    """
    len_server_key = len(key_server_side)
    len_client_key = len(key_client_side)
    ret_code = True
    if len_client_key >= len_server_key:
        for i in range(len_client_key - len_server_key + 1):
            if key_client_side[i:(i+len_server_key)] == key_server_side:
                ret_code = False
                break
    return ret_code

def localPubkeyCheck():
    tmp_f = open(DATAFILE)
    local_users = fileObjectToList(tmp_f)   
    key_path = ""
    tunnel_key_path = ""
    for user in local_users:
        if MY_ROLE == 'client':
            key_path = "/home/%s/.ssh/authorized_keys" % (user,)
        elif MY_ROLE == "jumper":
            key_path = "/home/%s/.ssh/id_rsa" % (user,)
            tunnel_key_path = "/home/%s/.ssh/authorized_keys" % (user,)
        elif MY_ROLE == "directLogin":
            tunnel_key_path = "/home/%s/.ssh/authorized_keys" % (user,)

        if key_path != "":
            key_ret = getPubKey(user,"serverKey")
            if key_ret != False:
                if not os.path.isfile(key_path):
                    loger("localPubkeyCheck: no key for user '%s', try to get key from lham_server..... " % (user,))
                    writeKey(user,key_ret[0],key_ret[1])
                    loger("getPubKey: key for user '%s' restored successfully." % (user,) )
                else:
                    key_local_f = open(key_path)
                    key_local_list = fileObjectToList(key_local_f) 
                    if keyContentCompare(key_ret[1],key_local_list): 
                        loger("localPubkeyCheck: key for user '%s' is invalid. Now updating....." % (user,))
                        writeKey(user,key_ret[0],key_ret[1])
                        loger("getPubKey: key for user '%s' updated successfully." % (user,) )
        if tunnel_key_path != "":
            tunnel_key_ret = getPubKey(user,"tunnelKey")
            if tunnel_key_ret != False:
                if not os.path.isfile(tunnel_key_path):
                    loger("localPubkeyCheck: no tunnel_key for user '%s', try to get tunnel_key from lham_server..... " % (user,))
                    writeKey(user,tunnel_key_ret[0],tunnel_key_ret[1])
                    loger("getPubKey: tunnel_key for user '%s' restored successfully." % (user,) )
                else:
                    tunnel_key_local_f = open(tunnel_key_path)
                    tunnel_key_local_list = fileObjectToList(tunnel_key_local_f) 
                    if keyContentCompare(tunnel_key_ret[1],tunnel_key_local_list): 
                        loger("localPubkeyCheck: tunnel_key for user '%s' is invalid. Now updating....." % (user,))
                        writeKey(user,tunnel_key_ret[0],tunnel_key_ret[1])
                        loger("getPubKey: tunnel_key for user '%s' updated successfully." % (user,) )

def clientUpdate(prime_ip):
    """
    Try to update myself if newer version released at the lham server.
    """
    tmp_f = os.popen("curl -s -m 5 '%s%s'" % (URL_PREFIX_versionCheck,"myPrimeIP=%s" % (prime_ip,)))
    return_list = fileObjectToList(tmp_f)
    return_list_len = len(return_list)
    if return_list_len == 0:
        loger('clientUpdate: server no response.',"ERROR")
        sys.exit(1)
    elif return_list_len != 2 or return_list[0] != "VERSION_CHECK_SUCCESS":
        loger('clientUpdate: version_check failed!',"ERROR")
        sys.exit(1)
    else:
        current_release_version_string = return_list[1]
        current_release_version_string_ls = current_release_version_string.split('-')
        if len(current_release_version_string_ls) != 2 or current_release_version_string_ls[0] != "lham_agent":
            loger("clientUpdate: version_string return from server looks illegal: " + current_release_version_string,"ERROR")
            sys.exit(1)
        else:
            current_release_version=current_release_version_string_ls[1]

    my_version_int=int(''.join(MY_VERSION.split('.')))
    current_release_version_int=int(''.join(current_release_version.split('.')))
    if my_version_int < current_release_version_int:
        os.system("wget -w 10 -O %s --quiet http://%s:%s/agent/pub/lham_agent" % (WORKDIR + '/' + current_release_version, LHAM_HOST, LHAM_PORT) )
        if os.path.isfile(WORKDIR + '/' + current_release_version):
            data = open(WORKDIR + '/' + current_release_version).read()
            if len(data) == 0:
                loger('clientUpdate: update failed, no data got from lham server.','ERROR')
                sys.exit(1)

            safeRmFile=(WORKDIR + "/lham_agent")
            return_code = os.system("mv %s %s && chmod 0600 %s" % ( WORKDIR + '/' + current_release_version,
                                          WORKDIR + "/lham_agent",
                                          WORKDIR + "/lham_agent"))
            if return_code == 0:
                loger('clientUpdate: Successfully updated to version: ' +  current_release_version_int) 
            else:
                loger('clientUpdate: update failed.',"ERROR")
                

                    

#===================================== main =====================================

if __name__ == "__main__":
    start_time = timer('log')
    my_prime_ip = getPrimeIP()
    if my_prime_ip == '':
        loger("no ip available!","ERROR")
        sys.exit(1)

    ### Determine role type.
    if len(sys.argv) != 2:
        loger("Program launch error, need a role type.", "ERROR")
        sys.exit(1)
    elif sys.argv[1] in ['-v', '--version']:
        print MY_VERSION
        sys.exit(0)
    elif sys.argv[1] == "--update":
        clientUpdate(my_prime_ip)
        sys.exit(0)

    MY_ROLE = sys.argv[1]
    if not MY_ROLE in ['client', 'jumper', 'directLogin']:
        loger("Program launch error, role type not support: '%s'." % (MY_ROLE,), "ERROR")
        sys.exit(1)

    ### initializing
    if not ( os.path.isdir(WORKDIR) and os.path.isdir(DATADIR) ):
        initWork()

    ### working
    changing = getChange(my_prime_ip)
    addNewUser(changing["add"])
    #deleteUserHomeDir(start_time)  # run this before deleteUser() so that homedir-deleting will be done in next day.
    deleteUser(changing["delete"])
    replaceDataFile(changing)
    if os.path.isfile(DATAFILE):
        localPubkeyCheck() #check current users' key, if missing, try to get it from lham_server.
    