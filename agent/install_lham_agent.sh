#! /bin/bash

server_ip='10.209.11.12'   #This will be configure in config_file at later version.
server_api_port='11306'    #This will be configure in config_file at later version.
run_interval=10            #Minutes. This will be configure in config_file at later version.
agent_role="client"        #This will be aborted when client_role can be stored in ldap.


whoami=`/bin/hostname`

WORK_DIR=/tmp/tmp_for_install_lham_agent

api_url="http://${server_ip}:${server_api_port}/for_agent_install.php"
download_succ_report="http://${server_ip}:${server_api_port}/for_agent_install_clean_cache.php"
passwd_phrase='THIS_IS_LHAM_AGENT_INSTALL_OR_UPDATE_SCRIPT-HELLO_GOD'

function pre_work() {
    mkdir -p $WORK_DIR
}

function end_work() {
    cd ~
    rm -rf $WORK_DIR
    exit 0
}

function get_agent_source() {
    curl_result=`curl -s -m 3 "${api_url}?whoami=${whoami}&passwd_phrase=${passwd_phrase}"`
    curl_result_1=`echo $curl_result | awk '{print $1}'`
    curl_result_2=`echo $curl_result | awk '{print $2}'`

    if [ "$curl_result_1" == "AGENT_INSTALL_REQUEST_ACCEPTED" ]; then
        cd $WORK_DIR
        wget -q "http://${server_ip}:${server_api_port}/$curl_result_2"
        if [ -f ./lham_agent.py ]; then
            curl -s -m 3 "${download_succ_report}?whoami=${whoami}&cache_path=$curl_result_2"
        else
            echo "===> ERROR: agent resource download error."
            end_work
        fi
    else
        echo "===> ERROR: Lham server refuse this install request."
        end_work
    fi
}

function compile_agent() {
    cd $WORK_DIR
    /usr/bin/python -m py_compile lham_agent.py

    if [ -f ./lham_agent.pyc ]; then
        mv lham_agent.pyc lham_agent
    else
        echo "===> ERROR: lham_agent compile failed"
        end_work
    fi
}

function install_agent() {
    if [ -f /usr/local/lham_agent/lham_agent ]; then
        rm -f /usr/local/lham_agent/lham_agent
    fi
    cd $WORK_DIR
    /usr/bin/python lham_agent $agent_role
}

function download_run_script() {
    cd $WORK_DIR
    wget -q "http://${server_ip}:${server_api_port}/agent/pub/run_lham_agent.sh"
    chmod 0700 run_lham_agent.sh
    cp -af run_lham_agent.sh /usr/local/lham_agent/
}

#-------------- main -------------------

pre_work
get_agent_source
compile_agent
install_agent
download_run_script
end_work
