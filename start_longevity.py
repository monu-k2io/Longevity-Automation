import datetime
import getopt
import logging
import os
import re
import sys
import threading
import time
import numpy as np

import pandas as pd
import ssh
import k2_env as K2

sleep = 10
interval = 18

def detectContainer(env, user: ssh.User, containerName, c=0):
    try:
        count = c
        id = ""
        
        Logger.info(f"Detecting running {containerName} container at {user.ip} at {count*sleep}sec",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        # cmd = "docker ps -a | grep '%s' | awk '{print $1}'" % (containerName)
        cmd = "docker ps -a | grep '%s' | cut -b 1-5" % (containerName)
        id=ssh.doSSH(user,cmd)
        id=id.replace("\n","").replace("\r","")
        if id!="" and id!=None:
            Logger.info(f"{containerName} started successfully at {user.ip} after {count*sleep}sec",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return True

        count+=1
        time.sleep(sleep)
        if count > interval:
            Logger.warning(f"No running container found at {user.ip} after {count*sleep}sec",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return False
        return detectContainer(env,user,containerName,count)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False

def detectContainerFromLogs(env,user: ssh.User, id, detect_txt, c=0):
    try:
        count = c
        
        Logger.info(f"Detecting running container with ID {id} at {user.ip} at {count*sleep}sec",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        cmd = "docker logs '%s'" % (id)
        out=ssh.doSSH(user,cmd)
        out=out.replace("\n","").replace("\r","")
        if detect_txt in out:
            Logger.info(f"Container with ID {id} started successfully at {user.ip} after {count*sleep}sec",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return True

        count+=1
        time.sleep(sleep)
        if count > interval:
            Logger.warning(f"No running container found at {user.ip} after {count*sleep}sec",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return False
        return detectContainerFromLogs(env,user,id,detect_txt,count)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False

def getAndRemoveContainer(env, user: ssh.User,containerName,remove=True):
    try:
        Logger.info(f"Checking for running {containerName} container at {user.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        # cmd = "docker ps -a | grep '%s' | awk '{print $1}'" % (containerName)
        cmd = "docker ps -a | grep '\<%s\>' | cut -b 1-5" % (containerName)
        # print(cmd)
        id=""
        id=ssh.doSSH(user,cmd)
        id=id.replace("\n","").replace("\r","")
        out=re.findall("[^\s]+", id)
        if len(out) > 1:
            return True, None

        if id!="" and id!=None:
            Logger.info("Detected:: %s"%(id),extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            if remove:
                cmd = "docker rm -f %s" % (id)
                out=ssh.doSSH(user,cmd)
                Logger.info(f"Container {containerName} stopped.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                return True, id
            else:
                return False, id
        else:
            Logger.warning(f"No running container found with {containerName}.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return True, None
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False, None

def attachApplication(env,user: ssh.User,id):
    try:
        Logger.info(f"Started application attachment...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        cmd = f"docker exec {id} bash -c 'bash /opt/k2root/k2root/collectors/k2-php-agent/k2_php_agent_install_script.sh --allow-server-restart=TRUE'"
        # print(cmd)
        out = ssh.doSSH(user,cmd)
        out=out.replace("\n","").replace("\r","")
        if "PHP collector for apache server activated" in out:
            Logger.info(f"PHP collector for apache server activated.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return True
        else:
            Logger.error(f"PHP agent attachment failled!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return False
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False

def startRSSMonitor(env,user: ssh.User,id):
    try:
        Logger.info(f"Starting RSS monitoring in {id} container at {user.ip}...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        cmd = f"docker exec -d {id} bash -c 'cd rss; nohup bash rss.sh &> output & sleep 1'"
        # print(cmd)
        ssh.doSSH(user,cmd)
        Logger.info("RSS monitoring Started!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        makeRequest(env,user)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def makeRequest(env,user: ssh.User):
    try:
        out=ssh.doSSH(user,env.FIRST_CURL)
        Logger.info("First request fired!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def startWith(env,withMachine):
    try:
        if getAndRemoveContainer(env,withMachine,env.INSTANA_CONTAINER_NAME):
            Logger.info(f"Launching instana agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            ssh.doSSH(withMachine,env.INSTANA_CMD)
            if detectContainer(env,withMachine,env.INSTANA_CONTAINER_NAME):
                ssh.doSSH(withMachine,f"rm -rfR {K2.DIR}; mkdir {K2.DIR}; ls {K2.DIR}")
                Logger.info(f"Downloading k2 agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                ssh.doSSH(withMachine,f"cd {K2.DIR}; wget -O vm-all.zip '{K2.K2_CLOUD}/centralmanager/api/{K2.K2_VERSION}/help/installers/{K2.K2_BUILD}/download/{K2.USER_ID}/{K2.REF_TOKEN}/vm-all?isDocker=true&groupName={K2.K2_GROUP_NAME}&agentDeploymentEnvironment={K2.K2_DEPLOYMENT_ENV}&pullPolicyRequired=false'")
                Logger.info("Download complete!\nUnzipping...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                ssh.doSSH(withMachine,f"cd {K2.DIR}; unzip vm-all.zip")
                Logger.info("Unzipping complete!\nValidating config...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                updateAgentConfig(env,f".agent.properties.{env.LC}",f".agent.properties.{env.LC}.tmp")
                if K2.VALIDATOR_IP != "":
                    updateEnvConfig(env,f"env.properties.{env.LC}",f"env.properties.{env.LC}.tmp")
                Logger.info("Validated!!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

                Logger.info(f"Launching k2 agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                ssh.doSSH(withMachine,K2.K2_INSTALL_CMD)
                Logger.info(f"K2 agent started.\nStarting application with k2 agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                time.sleep(30)
                appStatus, appContainerId = getAndRemoveContainer(env,withMachine,env.APP_CONTAINER_NAME)
                if appStatus:
                    id=ssh.doSSH(withMachine,env.APP_INSTALL_WITH_CMD)
                    id=id.replace("\n","").replace("\r","")
                    out=re.findall("[^\s]+", id)
                    # print(out)
                    # if len(out) > 1:
                    #     endTime = datetime.datetime.now() + datetime.timedelta(minutes=5)
                    #     while True:
                    #         if datetime.datetime.now() >= endTime:
                    #             break
                    #         appStatus, id = getAndRemoveContainer(env,withMachine,env.APP_CONTAINER_NAME,False)
                    #         # print(id)
                    #         if id!=None:
                    #             id=id.replace("\n","").replace("\r","")
                    #             break
                    if len(out) > 1:
                        appStatus, id = getAndRemoveContainer(env,withMachine,env.APP_CONTAINER_NAME,False)
                        if id!=None:
                            id=id.replace("\n","").replace("\r","")
                    if id!="" and id!=None:
                        Logger.info("Detected:: %s"%(id),extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                        if detectContainerFromLogs(env,withMachine,id,env.APP_DETECT_TXT):
                            if env.LC == "php":
                                if attachApplication(env,withMachine,id):
                                    startRSSMonitor(env,withMachine,id)
                                else:
                                    Logger.error("Agent attachment failed!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                            else:
                                makeRequest(env,withMachine)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def startWithout(env,withoutMachine):
    try:
        if getAndRemoveContainer(env,withoutMachine,env.INSTANA_CONTAINER_NAME):
            Logger.info(f"Launching instana agent on {withoutMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            ssh.doSSH(withoutMachine,env.INSTANA_CMD)
            if detectContainer(env,withoutMachine,env.INSTANA_CONTAINER_NAME):
                Logger.info(f"Starting application without k2 agent on {withoutMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                appStatus, appContainerId = getAndRemoveContainer(env,withoutMachine,env.APP_CONTAINER_NAME)
                if appStatus:
                    id=ssh.doSSH(withoutMachine,env.APP_INSTALL_WITHOUT_CMD)
                    id=id.replace("\n","").replace("\r","")
                    out=re.findall("[^\s]+", id)
                    if len(out) == 1 and id!="" and id!=None:
                        Logger.info("Detected:: %s"%(id),extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                        if detectContainerFromLogs(env,withoutMachine,id,env.APP_DETECT_TXT):
                            if env.LC == "php":
                                startRSSMonitor(env,withoutMachine,id)
                            else:
                                makeRequest(env,withoutMachine)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def startRequestFiring(env,machine,containerName,dir):
    try:
        if getAndRemoveContainer(env,machine,containerName):
            Logger.info(f"Starting {containerName} container at {machine.ip}...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            cmd = f"cd {dir}; docker run -itd -v $(pwd):/var/loadtest -v $SSH_AUTH_SOCK:/ssh-agent -e SSH_AUTH_SOCK=/ssh-agent --net host --name {containerName} direvius/yandex-tank"
            # print(cmd)
            ssh.doSSH(machine,cmd)
            print("Started!")
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def updateAgentConfig(env, fileName, tmpName):
    try:
        out = ssh.doSCP(env.WITH_MACHINE,tmpName,f"{K2.DIR}/k2install/.agent.properties",False)
        # print(out)
        
        if os.path.exists(fileName):
            os.remove(fileName)
        with open(tmpName, 'r+') as fp:
            f = open(fileName, "w")
            for c, line in enumerate(fp):
                if "prevent_web_agent_image=" in line and f"{K2.IMAGE}" not in line:
                    Logger.debug("%s--->Update"%c,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                    line = "prevent_web_agent_image=%s\n"%(K2.IMAGE)
                if "micro_agent_image=" in line and f"{K2.IMAGE}" not in line:
                    Logger.debug("%s--->Update"%c,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                    line = "micro_agent_image=%s\n"%(K2.IMAGE)
                if "prevent_web_agent_image_tag=" in line and f"{K2.VALIDATOR_TAG}" not in line:
                    Logger.debug("%s--->Update"%c,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                    line = "prevent_web_agent_image_tag=%s\n"%(K2.VALIDATOR_TAG)
                if "micro_agent_image_tag=" in line and f"{K2.MICROAGENT_TAG}" not in line:
                    Logger.debug("%s--->Update"%c,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                    line = "micro_agent_image_tag=%s\n"%(K2.MICROAGENT_TAG)
                f.write(line)
            
            if os.path.exists(tmpName):
                os.remove(tmpName) 
            f.close()
        fp.close()
        
        out2 = ssh.doSCP(env.WITH_MACHINE,fileName,f"{K2.DIR}/k2install/.agent.properties")
        # print(out2)
        if os.path.exists(fileName):
            os.remove(fileName)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def updateEnvConfig(env, fileName, tmpName):
    try:
        out = ssh.doSCP(env.WITH_MACHINE,tmpName,f"{K2.DIR}/k2install/env.properties",False)
        # print(out)
        
        if os.path.exists(fileName):
            os.remove(fileName)
        with open(tmpName, 'r+') as fp:
            f = open(fileName, "w")
            for c, line in enumerate(fp):
                if "k2_agent_validator_endpoint" in line and f"{K2.VALIDATOR_IP}" not in line:
                    # print("%s--->Update"%c)
                    line = "k2_agent_validator_endpoint=ws://%s:54321\n"%(K2.VALIDATOR_IP)
                if "k2_agent_resource_endpoint" in line and f"{K2.VALIDATOR_IP}" not in line:
                    # print("%s--->Update"%c)
                    line = "k2_agent_resource_endpoint=http://%s:54322\n"%(K2.VALIDATOR_IP)
                f.write(line)
            
            if os.path.exists(tmpName):
                os.remove(tmpName) 
            f.close()
        fp.close()
        
        out2 = ssh.doSCP(env.WITH_MACHINE,fileName,f"{K2.DIR}/k2install/env.properties")
        # print(out2)
        if os.path.exists(fileName):
            os.remove(fileName)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def updateLoadFile(env, user: ssh.User, dir, fileName, tmpName):
    try:
        out = ssh.doSCP(env.LOAD_MACHINE,tmpName,f"{dir}/load.yaml",False)
        # print(out)

        if os.path.exists(fileName):
            os.remove(fileName)
        with open(tmpName, 'r+') as fp:
            f = open(fileName, "w")
            for c, line in enumerate(fp):
                if "address:" in line and f"{user.ip}:{env.APP_PORT}" not in line:
                    # print("%s--->Update"%c)
                    line = "  address: %s:%s # [Target's address]:[target's port]\n"%(user.ip,env.APP_PORT)
                if "schedule:" in line and f"{env.LONGEVITY_TIME}" not in line:
                    # print("%s--->Update"%c)
                    line = "    schedule: const(%s) # starting from 1rps growing linearly to 10rps during 10 minutes\n"%(env.LONGEVITY_TIME)
                f.write(line)
            
            if os.path.exists(tmpName):
                os.remove(tmpName) 
            f.close()
        fp.close()
        
        out2 = ssh.doSCP(env.LOAD_MACHINE,fileName,f"{dir}/load.yaml")
        # print(out2)
        if os.path.exists(fileName):
            os.remove(fileName)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def cleanMachine(env,user: ssh.User):
    try:
        cmd = f"docker rm -f $(docker ps -aq) && rm -rf /opt/k2root && rm -rf {K2.DIR}"
        doClean(env,user,cmd)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def doClean(env,user: ssh.User, cmd):
    try:
        Logger.info("Cleaning up %s..."%user.ip,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        # print(cmd)
        ssh.doSSH(user,cmd)
        Logger.info(f"{user.ip} is Cleaned!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def doCleanUp(env):
    # clean apps and k2
    cleanMachine(env,env.WITH_MACHINE)
    if not withOnly:
        cleanMachine(env,env.WITHOUT_MACHINE)
    # clean yandex
    getAndRemoveContainer(env,env.LOAD_MACHINE, env.WITH_YANDEX_NAME)
    if not withOnly:
        getAndRemoveContainer(env,env.LOAD_MACHINE, env.WITHOUT_YANDEX_NAME)
    # clean yandex logs
    doClean(env,env.LOAD_MACHINE,f"rm -rf {env.YANDEX_WITH_DIR}/logs/* && rm -rf {env.YANDEX_WITHOUT_DIR}/logs/*")

def startValidatorAndDb(user: ssh.User):
    try:
        cmd = f"docker rm -f $(docker ps -aq) && docker rmi {K2.IMAGE}:{K2.VALIDATOR_TAG} && rm -rf /opt/k2root && rm -rf {K2.DIR}"
        ssh.doSSH(user,cmd)

        db_cmd = "bash /root/kishan/v2-install-scripts/install-db-prod.sh"
        ic_cmd = f"bash /root/kishan/v2-install-scripts/install-validator-prod.sh public {K2.VALIDATOR_TAG} {K2.K2_GROUP_NAME}"
        if "k2cloud210" in K2.K2_CLOUD:
            db_cmd = "bash /root/kishan/v2-install-scripts/install-db.sh"
            ic_cmd = f"bash /root/kishan/v2-install-scripts/install-validator.sh private {K2.VALIDATOR_TAG} {K2.K2_GROUP_NAME}"
        
        out=ssh.doSSH(user,db_cmd)
        Logger.info(f"{user.ip} started ArangoDB!",extra={"ext":threading.current_thread().name,"lc":f"{K2.VALIDATOR_TAG}".upper()})
        out=ssh.doSSH(user,ic_cmd)
        Logger.info(f"{user.ip} started {K2.VALIDATOR_TAG}!",extra={"ext":threading.current_thread().name,"lc":f"{K2.VALIDATOR_TAG}".upper()})
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":f"{K2.VALIDATOR_TAG}".upper()})
    

def pickEnv():
    global lc, withOnly
    clean = False
    withOnly = False
    lc = None
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "l:c:hw",["language=","clean=","help="])
    except:
        showHelp()
        return

    for opt, arg in opts:
        if opt in ['-l','--language']:
            lc = arg.split(",")
        if opt in ['-c','--clean']:
            lc = arg.split(",")
            clean = True
        if opt in ['-w','--with']:
            withOnly = True
    print("ENV:: %s %s %s"%(lc,clean,withOnly))

    # global env
    if not K2.VALIDATOR_IP == "":
        startValidatorAndDb(ssh.User(K2.VALIDATOR_IP,"root","k2cyber"))
        Logger.info(f"Sleeping for 1 minute to start validator at {K2.VALIDATOR_IP}",extra={"ext":"Monu Lakshkar","lc":"K2"})
        time.sleep(60)

    if "all" in lc:
        threading.Thread(target=animate).start()

    if "node" in lc or "all" in lc:
        import env_node
        node = threading.Thread(target=printInfo,args=(env_node,clean,))
        node.start()
        # node.join()
    if "java" in lc or "all" in lc:
        import env_java
        java = threading.Thread(target=printInfo,args=(env_java,clean,))
        java.start()
        # java.join()
    if "python" in lc or "all" in lc:
        import env_python
        python = threading.Thread(target=printInfo,args=(env_python,clean,))
        python.start()
        # python.join()
    if "php" in lc or "all" in lc:
        import env_php
        php = threading.Thread(target=printInfo,args=(env_php,clean,))
        php.start()
        # php.join()
    if "go" in lc or "all" in lc:
        import env_go
        go = threading.Thread(target=printInfo,args=(env_go,clean,))
        go.start()
        # go.join()
    if "ruby" in lc or "all" in lc:
        import env_ruby
        ruby = threading.Thread(target=printInfo,args=(env_ruby,clean,))
        ruby.start()
        # ruby.join()
    if "all" in lc:
        node.join()
        java.join()
        python.join()
        php.join()
        go.join()
        ruby.join()
        global done 
        done = True
    if not pd.Series(np.array(lc)).isin(np.array(["node","java","php","python","go","ruby","all"])).any():
        showHelp()

def printInfo(env,clean): 
    print("\n{:<40} {:<40}".format("Lanaguage collector :: ",env.LC.upper()))
    print("{:<40} {:<40}".format("Machine with K2 :: ",env.WITH_MACHINE.ip))
    print("{:<40} {:<40}".format("Machine without K2 :: ",env.WITHOUT_MACHINE.ip))
    print("{:<40} {:<40}".format("K2 agent install command:: ",K2.K2_INSTALL_CMD))
    print("{:<40} {:<40}".format("K2 Cloud:: ",K2.K2_CLOUD))
    print("{:<40} {:<40}".format("K2 Version:: ",K2.K2_VERSION))
    print("{:<40} {:<40}".format("Validator IP:: ",f'{K2.VALIDATOR_IP if K2.VALIDATOR_IP!="" else env.WITH_MACHINE.ip} (make sure validator is in running state)'))
    print("{:<40} {:<40}".format("Validator:: ",K2.VALIDATOR_TAG))
    print("{:<40} {:<40}".format("Microagent:: ",K2.MICROAGENT_TAG))
    print("{:<40} {:<40}".format("App:: ",env.APP_CONTAINER_NAME))
    # print(lc, len(lc))
    if  len(lc)==1 and "all" not in lc:
        answer = input("Continue (y/yes or n/no)?\t\t")
    else:
        answer = "yes"
        print("Press ^C (within 30sec) to stop if values are not as per requirement!")
        time.sleep(30)
    if answer in ['y', 'yes']:
        if clean:
            doCleanUp(env)
        else:
            if lc!='all':
                threading.Thread(target=animate).start()
            doCleanUp(env)
            if lc!='all':
                start = threading.Thread(target=startUp,args=(env,))
                start.start()
                start.join()
                global done
                done = True
            else:
                startUp(env)
    else:
        print("Update these values in respective env file!")

#here is the animation
def animate():
    global done 
    done = False
    while not done:
        sys.stdout.write('\rloading | ')
        time.sleep(0.07)
        sys.stdout.write('\rloading / ')
        time.sleep(0.08)
        sys.stdout.write('\rloading - ')
        time.sleep(0.07)
        sys.stdout.write('\rloading \\ ')
        time.sleep(0.07)

def showHelp():
    print(f"\nUsage: \033[1;33mpython3 {os.path.basename(__file__)} <OPTIONS>\u001b[0m")
    print("\033[1;34m\nOPTIONS:\u001b[0m")
    print("{:<35} {:<40}".format("\033[4;32m-l/--language <argument>\u001b[0m","\033[1;29mStart longevity for specified language"))
    print("{:<30} {:<40}".format("","Valid argument with -l are: (you can pass comma(,) seperated values)"))
    print("{:<35} {:<40}".format("","node - to start longevity for Node agent"))
    print("{:<35} {:<40}".format("","python - to start longevity for Python agent"))
    print("{:<35} {:<40}".format("","java - to start longevity for Java agent"))
    print("{:<35} {:<40}".format("","php - to start longevity for PHP agent"))
    print("{:<35} {:<40}".format("","go - to start longevity for GO agent"))
    print("{:<35} {:<40}".format("","all - to start longevity for all mentioned agents\u001b[0m"))
    print("{:<35} {:<40}".format("\033[4;32m-c/--clean <argument>\u001b[0m","\033[1;29mClean longevity setup for specified language"))
    print("{:<30} {:<40}".format("","Valid argument with -c are: (you can pass comma(,) seperated values)"))
    print("{:<35} {:<40}".format("","node - to clean longevity setup for Node agent"))
    print("{:<35} {:<40}".format("","python - to clean longevity setup for Python agent"))
    print("{:<35} {:<40}".format("","java - to clean longevity setup for Java agent"))
    print("{:<35} {:<40}".format("","php - to clean longevity setup for PHP agent"))
    print("{:<35} {:<40}".format("","go - to clean longevity setup for GO agent"))
    print("{:<35} {:<40}".format("","all - to clean longevity setup for all mentioned agents\u001b[0m"))

def startUp(env):
    threadWith = threading.Thread(target=startWith,args=(env,env.WITH_MACHINE,))
    if not withOnly:
        threadWithout = threading.Thread(target=startWithout,args=(env,env.WITHOUT_MACHINE,))

    threadWith.start()
    if not withOnly:
        threadWithout.start()

    threadWith.join()
    if not withOnly:
        threadWithout.join()
    Logger.info("Longevity application setup complete!!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

    Logger.info("Updating load.yaml file...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    threadFileWith = threading.Thread(target=updateLoadFile,args=(env,env.WITH_MACHINE,env.YANDEX_WITH_DIR,f"load_with_{env.LC}.yaml",f"temp_with{env.LC}.yaml"))
    if not withOnly:
        threadFileWithout = threading.Thread(target=updateLoadFile,args=(env,env.WITHOUT_MACHINE,env.YANDEX_WITHOUT_DIR,f"load_without_{env.LC}.yaml",f"temp_without_{env.LC}.yaml"))

    threadFileWith.start()
    if not withOnly:
        threadFileWithout.start()

    threadFileWith.join()
    if not withOnly:
        threadFileWithout.join()

    Logger.info("Starting request firing...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    threadFiringWith = threading.Thread(target=startRequestFiring,args=(env,env.LOAD_MACHINE,env.WITH_YANDEX_NAME,env.YANDEX_WITH_DIR))
    if not withOnly:
        threadFiringWithout = threading.Thread(target=startRequestFiring,args=(env,env.LOAD_MACHINE,env.WITHOUT_YANDEX_NAME,env.YANDEX_WITHOUT_DIR))

    threadFiringWith.start()
    if not withOnly:
        threadFiringWithout.start()

    threadFiringWith.join()
    if not withOnly:
        threadFiringWithout.join()
    
    Logger.info("Longevity started successfully!!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

if __name__ == "__main__":
    print(f"*** Make sure VPN is connected ***")
    logging.basicConfig(filename=f"longevity.log",format='%(asctime)s [%(levelname)s] :%(lc)s: - [%(ext)s] - %(message)s',filemode='w')
    # Creating an object
    global Logger
    Logger = logging.getLogger()
    # Setting the threshold of logger to DEBUG
    Logger.addHandler(logging.StreamHandler(sys.stdout))
    Logger.setLevel(logging.DEBUG)
    print("\033[1;34mCheck automation logs at\u001b[0m: \033[4;31mlongevity.log\u001b[0m")
    Logger.info(f"Longevity Log file Initialised at {datetime.datetime.now()}",extra={"ext":"Monu Lakshkar","lc":"K2"})
    try:
        pickEnv()
    except Exception as e:
        Logger.error(e,extra={"ext":"Monu Lakshkar","lc":"K2"})