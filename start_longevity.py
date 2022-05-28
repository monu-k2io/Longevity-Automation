import datetime
import getopt
from glob import glob
import logging
import os
import re
import sys
import threading
import time
import ssh
from ssh_session import Terminal
import k2_env as K2

def detectContainer(env,session: Terminal, user: ssh.User, containerName):
    try:
        endTime = datetime.datetime.now() + datetime.timedelta(minutes=15)
        count = 1
        id = ""
        while True:
            if datetime.datetime.now() >= endTime:
                break
            Logger.info(f"Detecting running {containerName} container at {user.ip}... {count}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            # cmd = "docker ps -a | grep '%s' | awk '{print $1}'" % (containerName)
            cmd = "docker ps -a | grep '%s' | cut -b 1-5" % (containerName)
            id=session.execute(cmd)
            id=id.replace("\n","").replace("\r","")
            if id!="" and id!=None:
                Logger.info(f"{containerName} started successfully.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                return True
            count+=1
            time.sleep(30)
        Logger.warning("No running container found.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False

def detectContainerFromLogs(env,session: Terminal,user: ssh.User, id, detect_txt):
    try:
        endTime = datetime.datetime.now() + datetime.timedelta(minutes=15)
        count = 1
        while True:
            if datetime.datetime.now() >= endTime:
                break
            Logger.info(f"Detecting running {id} container at {user.ip}... {count}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            cmd = "docker logs '%s'" % (id)
            out=session.execute(cmd)
            out=out.replace("\n","").replace("\r","")
            if detect_txt in out:
                Logger.info(f"{id} started successfully.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                return True
            count+=1
            time.sleep(30)
        Logger.warning("No running container found.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False

def getAndRemoveContainer(env,session: Terminal, user: ssh.User,containerName,remove=True):
    try:
        Logger.info(f"Detecting running {containerName} container at {user.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        # cmd = "docker ps -a | grep '%s' | awk '{print $1}'" % (containerName)
        cmd = "docker ps -a | grep '\<%s\>' | cut -b 1-5" % (containerName)
        # print(cmd)
        id=""
        id=session.execute(cmd)
        id=id.replace("\n","").replace("\r","")
        out=re.findall("[^\s]+", id)
        if len(out) > 1:
            return True, None

        if id!="" and id!=None:
            Logger.info("Detected:: %s"%(id),extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            if remove:
                cmd = "docker rm -f %s" % (id)
                out=session.execute(cmd)
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

def attachApplication(env,session:Terminal,user: ssh.User,id):
    try:
        Logger.info(f"Started application attachment...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        cmd = f"docker exec {id} bash -c 'bash /opt/k2root/k2root/collectors/k2-php-agent/k2_php_agent_install_script.sh --allow-server-restart=TRUE'"
        # print(cmd)
        out = session.execute(cmd)
        out=out.replace("\n","").replace("\r","")
        if "PHP collector for apache server activated" in out:
            Logger.info(f"PHP collector for apache server activated.",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            return True
        else:
            return False
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        return False

def startRSSMonitor(env,session:Terminal,user: ssh.User,id):
    try:
        Logger.info(f"Starting RSS monitoring in {id} container at {user.ip}...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        cmd = f"docker exec -d {id} bash -c 'cd rss; nohup bash rss.sh &> output & sleep 1'"
        # print(cmd)
        session.execute(cmd)
        Logger.info("RSS monitoring Started!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        makeRequest(env,session,user)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def makeRequest(env,session:Terminal,user: ssh.User):
    try:
        out=session.execute(env.FIRST_CURL)
        Logger.info("First request fired!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def startWith(env,withMachine):
    try:
        session = Terminal.login(withMachine)
        if getAndRemoveContainer(env,session,withMachine,env.INSTANA_CONTAINER_NAME):
            Logger.info(f"Launching instana agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            session.execute(env.INSTANA_CMD)
            if detectContainer(env,session,withMachine,env.INSTANA_CONTAINER_NAME):
                session.execute(f"rm -rfR {K2.DIR}; mkdir {K2.DIR}; ls {K2.DIR}")
                Logger.info(f"Downloading k2 agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                session.execute(f"cd {K2.DIR}; wget -O vm-all.zip '{K2.K2_CLOUD}/centralmanager/api/{K2.K2_VERSION}/help/installers/{K2.K2_BUILD}/download/{K2.USER_ID}/{K2.REF_TOKEN}/vm-all?isDocker=true&groupName={K2.K2_GROUP_NAME}&agentDeploymentEnvironment={K2.K2_DEPLOYMENT_ENV}&pullPolicyRequired=false'")
                Logger.info("Download complete!\nUnzipping...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                session.execute(f"cd {K2.DIR}; unzip vm-all.zip")
                Logger.info("Unzipping complete!\nValidating config...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                updateAgentConfig(env,f".agent.properties.{env.LC}",f".agent.properties.{env.LC}.tmp")
                if K2.VALIDATOR_IP != "":
                    updateEnvConfig(env,f"env.properties.{env.LC}",f"env.properties.{env.LC}.tmp")
                Logger.info("Validated!!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

                Logger.info(f"Launching k2 agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                session.execute(env.K2_INSTALL_CMD)
                Logger.info(f"K2 agent started.\nStarting application with k2 agent on {withMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                appStatus, appContainerId = getAndRemoveContainer(env,session,withMachine,env.APP_CONTAINER_NAME)
                if appStatus:
                    id=session.execute(env.APP_INSTALL_WITH_CMD)
                    id=id.replace("\n","").replace("\r","")
                    out=re.findall("[^\s]+", id)
                    # print(out)
                    if len(out) > 1:
                        endTime = datetime.datetime.now() + datetime.timedelta(minutes=5)
                        while True:
                            if datetime.datetime.now() >= endTime:
                                break
                            appStatus, id = getAndRemoveContainer(env,session,withMachine,env.APP_CONTAINER_NAME,False)
                            # print(id)
                            if id!=None:
                                id=id.replace("\n","").replace("\r","")
                                break
                    if id!="" and id!=None:
                        Logger.info("Detected:: %s"%(id),extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                        if detectContainerFromLogs(env,session,withMachine,id,env.APP_DETECT_TXT):
                            if env.LC == "php":
                                if attachApplication(env,session,withMachine,id):
                                    startRSSMonitor(env,session,withMachine,id)
                            else:
                                makeRequest(env,session,withMachine)
        session.logout()
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def startWithout(env,withoutMachine):
    try:
        session = Terminal.login(withoutMachine)
        if getAndRemoveContainer(env,session,withoutMachine,env.INSTANA_CONTAINER_NAME):
            Logger.info(f"Launching instana agent on {withoutMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            session.execute(env.INSTANA_CMD)
            if detectContainer(env,session,withoutMachine,env.INSTANA_CONTAINER_NAME):
                Logger.info(f"Starting application without k2 agent on {withoutMachine.ip}",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                appStatus, appContainerId = getAndRemoveContainer(env,session,withoutMachine,env.APP_CONTAINER_NAME)
                if appStatus:
                    id=session.execute(env.APP_INSTALL_WITHOUT_CMD)
                    id=id.replace("\n","").replace("\r","")
                    out=re.findall("[^\s]+", id)
                    if len(out) == 1 and id!="" and id!=None:
                        Logger.info("Detected:: %s"%(id),extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
                        if detectContainerFromLogs(env,session,withoutMachine,id,env.APP_DETECT_TXT):
                            if env.LC == "php":
                                startRSSMonitor(env,session,withoutMachine,id)
                            else:
                                makeRequest(env,session,withoutMachine)
        session.logout()
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

def startRequestFiring(env,machine,containerName,dir):
    try:
        session = Terminal.login(machine)
        if getAndRemoveContainer(env,session,machine,containerName):
            Logger.info(f"Starting {containerName} container at {machine.ip}...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
            cmd = f"cd {dir}; docker run -itd -v $(pwd):/var/loadtest -v $SSH_AUTH_SOCK:/ssh-agent -e SSH_AUTH_SOCK=/ssh-agent --net host --name {containerName} direvius/yandex-tank"
            # print(cmd)
            session.execute(cmd)
            print("Started!")
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    finally:
        session.logout()


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
        session = Terminal.login(user)
        cmd = f"docker rm -f $(docker ps -aq) && rm -rf /opt/k2root && rm -rf {K2.DIR}"
        doClean(env,session,user,cmd)
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        session.logout()

def doClean(env,session: Terminal,user: ssh.User, cmd):
    try:
        Logger.info("Cleaning up %s..."%user.ip,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
        # print(cmd)
        # ssh.doSSH(user,cmd)
        session.execute(cmd)
        Logger.info(f"{user.ip} is Cleaned!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    except Exception as e:
        Logger.error(e,extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    finally:
        session.logout()

def doCleanUp(env):
    # clean apps and k2
    cleanMachine(env,env.WITH_MACHINE)
    cleanMachine(env,env.WITHOUT_MACHINE)
    # clean yandex
    session = Terminal.login(env.LOAD_MACHINE)
    getAndRemoveContainer(env,session,env.LOAD_MACHINE, env.WITH_YANDEX_NAME)
    getAndRemoveContainer(env,session,env.LOAD_MACHINE, env.WITHOUT_YANDEX_NAME)
    # clean yandex logs
    doClean(env, session, env.LOAD_MACHINE,f"rm -rf {env.YANDEX_WITH_DIR}/logs/* && rm -rf {env.YANDEX_WITHOUT_DIR}/logs/*")



def pickEnv():
    global lc
    clean = False
    lc = None
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "l:c:h",["language=","clean=","help="])
    except:
        showHelp()
        return

    for opt, arg in opts:
        if opt in ['-l','--language']:
            lc = arg
        if opt in ['-c','--clean']:
            lc = arg
            clean = True

    # global env
    if lc=='all':
        threading.Thread(target=animate).start()

    if lc=="node" or lc=="all":
        import env_node
        node = threading.Thread(target=printInfo,args=(env_node,clean,))
        node.start()
        # node.join()
    if lc=="java" or lc=="all":
        import env_java
        java = threading.Thread(target=printInfo,args=(env_java,clean,))
        java.start()
        # java.join()
    if lc=="python" or lc=="all":
        import env_python
        python = threading.Thread(target=printInfo,args=(env_python,clean,))
        python.start()
        # python.join()
    if lc=="php" or lc=="all":
        import env_php
        php = threading.Thread(target=printInfo,args=(env_php,clean,))
        php.start()
        # php.join()
    if lc=='all':
        node.join()
        java.join()
        python.join()
        php.join()
        global done 
        done = True
    if lc not in ["node","java","php","python","all"]:
        showHelp()

def printInfo(env,clean): 
    print("\n{:<40} {:<40}".format("Lanaguage collector :: ",env.LC.upper()))
    print("{:<40} {:<40}".format("Machine with K2 :: ",env.WITH_MACHINE.ip))
    print("{:<40} {:<40}".format("Machine without K2 :: ",env.WITHOUT_MACHINE.ip))
    print("{:<40} {:<40}".format("K2 agent install command:: ",env.K2_INSTALL_CMD))
    print("{:<40} {:<40}".format("K2 Cloud:: ",K2.K2_CLOUD))
    print("{:<40} {:<40}".format("K2 Version:: ",K2.K2_VERSION))
    print("{:<40} {:<40}".format("Validator IP:: ",f'{K2.VALIDATOR_IP if K2.VALIDATOR_IP!="" else env.WITH_MACHINE.ip} (make sure validator is in running state)'))
    print("{:<40} {:<40}".format("Validator:: ",K2.VALIDATOR_TAG))
    print("{:<40} {:<40}".format("Microagent:: ",K2.MICROAGENT_TAG))
    print("{:<40} {:<40}".format("App:: ",env.APP_CONTAINER_NAME))
    if lc != 'all':
        answer = input("Continue (y/yes or n/no)?\t\t")
    else:
        answer = "yes"
        print("Press ^C (within 30sec) to stop if values are not as per requirement!")
        time.sleep(30)
    if answer in ['y', 'yes']:
        if lc!='all':
            threading.Thread(target=animate).start()
        if clean:
            doCleanUp(env)
        else:
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
    print("{:<30} {:<40}".format("","Valid argument with -l are:"))
    print("{:<35} {:<40}".format("","node - to start longevity for Node agent"))
    print("{:<35} {:<40}".format("","python - to start longevity for Python agent"))
    print("{:<35} {:<40}".format("","java - to start longevity for Java agent"))
    print("{:<35} {:<40}".format("","php - to start longevity for PHP agent\u001b[0m"))
    print("{:<35} {:<40}".format("\033[4;32m-c/--clean <argument>\u001b[0m","\033[1;29mClean longevity setup for specified language"))
    print("{:<30} {:<40}".format("","Valid argument with -c are:"))
    print("{:<35} {:<40}".format("","node - to clean longevity setup for Node agent"))
    print("{:<35} {:<40}".format("","python - to clean longevity setup for Python agent"))
    print("{:<35} {:<40}".format("","java - to clean longevity setup for Java agent"))
    print("{:<35} {:<40}".format("","php - to clean longevity setup for PHP agent\u001b[0m"))

def startUp(env):
    threadWith = threading.Thread(target=startWith,args=(env,env.WITH_MACHINE,))
    threadWithout = threading.Thread(target=startWithout,args=(env,env.WITHOUT_MACHINE,))

    threadWith.start()
    threadWithout.start()

    threadWith.join()
    threadWithout.join()
    Logger.info("Longevity application setup complete!!",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})

    Logger.info("Updating load.yaml file...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    threadFileWith = threading.Thread(target=updateLoadFile,args=(env,env.WITH_MACHINE,env.YANDEX_WITH_DIR,f"load_with_{env.LC}.yaml",f"temp_with{env.LC}.yaml"))
    threadFileWithout = threading.Thread(target=updateLoadFile,args=(env,env.WITHOUT_MACHINE,env.YANDEX_WITHOUT_DIR,f"load_without_{env.LC}.yaml",f"temp_without_{env.LC}.yaml"))

    threadFileWith.start()
    threadFileWithout.start()

    threadFileWith.join()
    threadFileWithout.join()

    Logger.info("Starting request firing...",extra={"ext":threading.current_thread().name,"lc":env.LC.upper()})
    threadFiringWith = threading.Thread(target=startRequestFiring,args=(env,env.LOAD_MACHINE,env.WITH_YANDEX_NAME,env.YANDEX_WITH_DIR))
    threadFiringWithout = threading.Thread(target=startRequestFiring,args=(env,env.LOAD_MACHINE,env.WITHOUT_YANDEX_NAME,env.YANDEX_WITHOUT_DIR))

    threadFiringWith.start()
    threadFiringWithout.start()

    threadFiringWith.join()
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
    print("Check automation logs at: longevity.log")
    Logger.info("Longevity Log file Initialised!!",extra={"ext":"Monu Lakshkar","lc":"K2"})
    try:
        pickEnv()
    except Exception as e:
        Logger.error(e,extra={"ext":"Monu Lakshkar","lc":"K2"})