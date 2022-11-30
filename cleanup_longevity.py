from asyncio import Future
from collections import OrderedDict
import datetime
import json
import logging
import sys
import concurrent.futures
import paramiko

from k2_env import VALIDATOR_IP

def getSSHclient(hostname, hostip, hostpassword, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=hostip, username=hostname, password=hostpassword)
        
        stdin, stdout, stderr = client.exec_command(command)
        return client
    except Exception as  e:
        Logger.exception("ERROR while executing command on Host {}".format(e))
        return False, e

def execute_on_host(client, command):
    try:
        stdin, stdout, stderr = client.exec_command(command)
        value = stdout.read().decode("latin-1", "ignore").strip()
        error = stderr.read().decode("latin-1", "ignore").strip()
        if type(value) == bytes:
            value = value.decode("latin-1", "ignore")
        elif type(error) == bytes:
            error = error.decode("latin-1", "ignore")
        if len(error) > 0:
            return False, value + error
        return True, value
    except Exception as e:
        Logger.exception("ERROR while executing command on Host {}".format(e))
        return False, e

def cleanYandex(client, ip):
    try:
        for lang in LC:
            cmd = "docker rm -f $(docker ps -a --format 'table {} {}' | grep 'yandex-{}-{}*' | awk {})".format("{{.ID}}","{{.Names}}",lang,VALIDATOR_BUILD,"'{print $1}'")
            result, output = execute_on_host(client,cmd)
            if result:
                cmd = "rm -rf /root/longevity/{}/*/logs".format(lang)
                result, output = execute_on_host(client,cmd)
                if not result:
                    Logger.debug("{} is not Cleaned! Reason: {}".format(ip,output))
                    Logger.error("{} is not Cleaned!".format(ip))
                    return False
            else:
                Logger.debug("{} is not Cleaned! Reason: {}".format(ip,output))
                Logger.error("{} is not Cleaned!".format(ip))
                return False
        return True
    except Exception as e:
        Logger.error(e)
        return False

def cleanAgent(client, ip):
    try:
        cmd = "docker rm -f $(docker ps -a --format 'table {{.ID}} {{.Names}}' | grep 'k2-validator\|k2-db\|k2-micro-agent' | awk '{print $1}')"
        result, output = execute_on_host(client,cmd)
        if result:
            Logger.info(f"Agent is removed on {ip}!")
            return cleanK2home(client, ip)
        else:
            Logger.debug("Agent is not removed on {}! Reason: {}".format(ip,output))
            Logger.error("Agent is not removed on {}!".format(ip))
            return False
    except Exception as e:
        Logger.error(e)
        return False

def cleanK2home(client, ip):
    try:
        cmd = "rm -rf /opt/k2root"
        result, output = execute_on_host(client,cmd)
        if result:
            Logger.info(f"K2_HOME is Cleaned on {ip}!")
            return True
        else:
            Logger.debug("K2_HOME is not cleaned on {}! Reason: {}".format(ip,output))
            Logger.error("K2_HOME is not cleaned on {}!".format(ip))
            return False
    except Exception as e:
        Logger.error(e)
        return False

def cleanMachine(client, ip):
    try:
        for lang in LC:
            cmd = "docker rm -f $(docker ps -a | grep 'ic-{}.*|ic-{}.*' | awk {})".format(APP_CONFIG[lang]['application'],APP_CONFIG[lang]['application_without_agent'],"'{print $1}'")
            result, output = execute_on_host(client,cmd)
            if result:
                Logger.info("{} on {} is removed!".format(lang,ip))
            else:
                Logger.debug("{} on {} is not removed! Reason: {}".format(lang,ip,output))
                Logger.error("{} on {} is not removed!".format(lang,ip))
        return True
    except Exception as e:
        Logger.error(e)
        return False

def run(client, ip):
    Logger.info(f"Cleaning host {ip}")
    return cleanMachine(client, ip)

if __name__ == "__main__":
    APP_CONFIG = []
    LC = "java,node".split(",")
    YANDEX_IP = "192.168.5.62"
    VALIDATOR_IP = "192.168.5.132"
    VALIDATOR_BUILD = "111"
    VM_IPS = "192.168.5.138,192.168.5.141".split(',')

    with open("./app_config.json", encoding="UTF-8") as f:
       APP_CONFIG = json.load(f, object_pairs_hook=OrderedDict)
    # print(APP_CONFIG['node'])

    print(f"*** Cleaning up the longevity test setup ***")
    logging.basicConfig(filename=f"longevity_cleanup.log",format='%(asctime)s [%(levelname)s] - %(message)s',filemode='w')
    # Creating an object
    global Logger
    Logger = logging.getLogger()
    # Setting the threshold of logger to DEBUG
    Logger.addHandler(logging.StreamHandler(sys.stdout))
    Logger.setLevel(logging.INFO)
    Logger.info(f"Started Cleaning Up The Longevity Test Setup at {datetime.datetime.now()}",extra={"ext":"Monu Lakshkar","lc":"K2"})
    try:
        thread = [Future[bool]] * len(VM_IPS)
        executor = concurrent.futures.ThreadPoolExecutor(200)
        for id,ip in enumerate(VM_IPS):
            client = getSSHclient("root",ip,"k2cyber","ls")
            thread[id] = executor.submit(run, client, ip)
        for id,ip in enumerate(VM_IPS):
            if thread[id].result():
                Logger.info("Successfully cleaned {}!".format(ip))
            else:
                Logger.error("Failed on host {}!".format(ip))

        client1 = getSSHclient("root",YANDEX_IP,"k2cyber","ls")
        yandex = executor.submit(cleanYandex, client1, YANDEX_IP)
        if yandex.result():
            Logger.info("Successfully cleaned Yandex {}!".format(YANDEX_IP))
        else:
            Logger.error("Yandex clean up failed on host {}!".format(YANDEX_IP))

        if VALIDATOR_IP!="":
            client2 = getSSHclient("root",VALIDATOR_IP,"k2cyber","ls")
            agent = executor.submit(cleanAgent, client2, VALIDATOR_IP)
            if agent.result():
                Logger.info("Successfully cleaned Agent {}!".format(VALIDATOR_IP))
            else:
                Logger.error("Agent clean up failed on host {}!".format(VALIDATOR_IP))
    except Exception as e:
        Logger.error(e)