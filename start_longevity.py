import datetime
import getopt
import os
import re
import sys
import threading
import time
import ssh

def detectContainer(user: ssh.User, containerName):
    endTime = datetime.datetime.now() + datetime.timedelta(minutes=15)
    count = 1
    id = ""
    while True:
        if datetime.datetime.now() >= endTime:
            break
        print(f"Detecting running {containerName} container at {user.ip}... ",count)
        cmd = "docker ps -a | grep '%s' | awk '{print $1}'" % (containerName)
        id=ssh.doSSH(user,cmd)
        id=id.replace("\n","")
        if id!="" and id!=None:
            print(f"{containerName} started successfully.")
            return True
        count+=1
    print("No running container found.")
    return False

def detectContainerFromLogs(user: ssh.User, id, detect_txt):
    endTime = datetime.datetime.now() + datetime.timedelta(minutes=15)
    count = 1
    while True:
        if datetime.datetime.now() >= endTime:
            break
        print(f"Detecting running {id} container at {user.ip}... ",count)
        cmd = "docker logs '%s'" % (id)
        out=ssh.doSSH(user,cmd)
        out=out.replace("\n","")
        if detect_txt in out:
            print(f"{id} started successfully.")
            return True
        count+=1
    print("No running container found.")
    return False

def getAndRemoveContainer(user: ssh.User,containerName,remove=True):
    print(f"Detecting running {containerName} container at {user.ip}")
    cmd = "docker ps -a | grep '%s' | awk '{print $1}'" % (containerName)
    # print(cmd)
    id=""
    id=ssh.doSSH(user,cmd)
    id=id.replace("\n","")
    out=re.findall("[^\s]+", id)
    if len(out) > 1:
        return True, None

    if id!="" and id!=None:
        print("Detected:: ",id)
        if remove:
            cmd = f"docker rm -f {id}"
            out=ssh.doSSH(user,cmd)
            print(f"Container {containerName} stopped.", out)
            return True, id
        else:
            return False, id
    else:
        print(f"No running container found with {containerName}.")
        return True, None

def attachApplication(user: ssh.User,id):
    print(f"Started application attachment...")
    cmd = f"docker exec {id} bash -c 'bash /opt/k2root/k2root/collectors/k2-php-agent/k2_php_agent_install_script.sh --allow-server-restart=TRUE'"
    # print(cmd)
    out = ssh.doSSH(user,cmd)
    out=out.replace("\n","")
    if "PHP collector for apache server activated" in out:
        print(f"PHP collector for apache server activated.")
        return True
    else:
        return False

def startRSSMonitor(user: ssh.User,id):
    print(f"Starting RSS monitoring in {id} container at {user.ip}...")
    cmd = f"docker exec -d {id} bash -c 'cd rss; nohup bash rss.sh &> output & sleep 1'"
    # print(cmd)
    ssh.doSSH(user,cmd)
    print("RSS monitoring Started!")
    makeRequest(user)

def makeRequest(user: ssh.User):
    out=ssh.doSSH(user,env.FIRST_CURL)
    print("First request fired!")

def startWith(withMachine):
    print(f"\n## WITH AGENT")
    if getAndRemoveContainer(withMachine,env.INSTANA_CONTAINER_NAME):
        print(f"Launching instana agent on {withMachine.ip}")
        ssh.doSSH(withMachine,env.INSTANA_CMD)
        if detectContainer(withMachine,env.INSTANA_CONTAINER_NAME):
            print(f"Launching k2 agent on {withMachine.ip}")
            ssh.doSSH(withMachine,env.K2_INSTALL_CMD)
            print(f"K2 agent started.\nStarting application with k2 agent on {withMachine.ip}")
            appStatus, appContainerId = getAndRemoveContainer(withMachine,env.APP_CONTAINER_NAME)
            if appStatus:
                id=ssh.doSSH(withMachine,env.APP_INSTALL_WITH_CMD)
                id=id.replace("\n","")
                out=re.findall("[^\s]+", id)
                # print(out)
                if len(out) == 1 and id!="" and id!=None:
                    print("Detected:: ",id)
                    if detectContainerFromLogs(withMachine,id,env.APP_DETECT_TXT):
                        if lang == "php":
                            if attachApplication(withMachine,id):
                                startRSSMonitor(withMachine,id)
                        elif lang == "node" or lang == "python":
                            makeRequest(withMachine)

def startWithout(withoutMachine):
    print(f"\n## WITHOUT AGENT")
    if getAndRemoveContainer(withoutMachine,env.INSTANA_CONTAINER_NAME):
        print(f"Launching instana agent on {withoutMachine.ip}")
        ssh.doSSH(withoutMachine,env.INSTANA_CMD)
        if detectContainer(withoutMachine,env.INSTANA_CONTAINER_NAME):
            print(f"Starting application without k2 agent on {withoutMachine.ip}")
            appStatus, appContainerId = getAndRemoveContainer(withoutMachine,env.APP_CONTAINER_NAME)
            if appStatus:
                id=ssh.doSSH(withoutMachine,env.APP_INSTALL_WITHOUT_CMD)
                id=id.replace("\n","")
                out=re.findall("[^\s]+", id)
                if len(out) == 1 and id!="" and id!=None:
                    print("Detected:: ",id)
                    if detectContainerFromLogs(withoutMachine,id,env.APP_DETECT_TXT):
                        if lang == "php":
                            startRSSMonitor(withoutMachine,id)
                        elif lang == "node" or lang == "python":
                            makeRequest(withoutMachine)

def startRequestFiring(machine,containerName,dir):
    if getAndRemoveContainer(machine,containerName):
        print(f"Starting {containerName} container at {machine.ip}...")
        cmd = f"cd {dir}; docker run -itd -v $(pwd):/var/loadtest -v $SSH_AUTH_SOCK:/ssh-agent -e SSH_AUTH_SOCK=/ssh-agent --net host --name {containerName} direvius/yandex-tank"
        # print(cmd)
        ssh.doSSH(machine,cmd)
        print("Started!")

def updateLoadFile(user: ssh.User, dir, fileName, tmpName):
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
            f.write(line)
        
        if os.path.exists(tmpName):
            os.remove(tmpName) 
        f.close()
    fp.close()
    
    out2 = ssh.doSCP(env.LOAD_MACHINE,fileName,f"{dir}/load.yaml")
    # print(out2)
    if os.path.exists(fileName):
        os.remove(fileName)

def cleanMachine(user: ssh.User):
    cmd = f"docker rm -f $(docker ps -aq) && rm -rf /opt/k2root"
    doClean(user,cmd)

def doClean(user: ssh.User, cmd):
    print(f"Cleaning up {user.ip}...")
    # print(cmd)
    ssh.doSSH(user,cmd)
    print(f"{user.ip} is Cleaned!")

def doCleanUp():
    # clean apps and k2
    cleanMachine(env.WITH_MACHINE)
    cleanMachine(env.WITHOUT_MACHINE)
    # clean yandex
    getAndRemoveContainer(env.LOAD_MACHINE, env.WITH_YANDEX_NAME)
    getAndRemoveContainer(env.LOAD_MACHINE, env.WITHOUT_YANDEX_NAME)
    # clean yandex logs
    doClean(env.LOAD_MACHINE,f"rm -rf {env.YANDEX_WITH_DIR}/logs/*")
    doClean(env.LOAD_MACHINE,f"rm -rf {env.YANDEX_WITHOUT_DIR}/logs/*")


def pickEnv():
    global lang
    clean = False
    lang = None
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "l:c:h",["language=","clean=","help="])
    except:
        showHelp()
        return

    for opt, arg in opts:
        if opt in ['-l','--language']:
            lang = arg
        if opt in ['-c','--clean']:
            lang = arg
            clean = True

    global env
    match lang:
        case "node":
            import env_node as env
        case "python":
            import env_python as env
        case "java":
            import env_java as env
        case "php":
            import env_php as env
        case default:
            showHelp()
            return
            
    print("\n{:<40} {:<40}".format("Lanaguage collector :: ",lang))
    print("{:<40} {:<40}".format("Machine with K2 :: ",env.WITH_MACHINE.ip))
    print("{:<40} {:<40}".format("Machine without K2 :: ",env.WITHOUT_MACHINE.ip))
    print("{:<40} {:<40}".format("K2 agent install command:: ",env.K2_INSTALL_CMD))
    print("{:<40} {:<40}".format("App:: ",env.APP_CONTAINER_NAME))
    answer = input("Continue (y/yes or n/no)?\t\t")
    if answer in ['y', 'yes']:
        if clean:
            doCleanUp()
        else:
            doCleanUp()
            startUp()
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
    print(f"\033[1;34m\nNOTE: keep the K2 agent installer in\u001b[0m \033[3;44m'/root/installer/'\u001b[0m")

def startUp():
    print(f"*** Make sure VPN is connected ***")
    threading.Thread(target=animate).start()
    threadWith = threading.Thread(target=startWith,args=(env.WITH_MACHINE,))
    threadWithout = threading.Thread(target=startWithout,args=(env.WITHOUT_MACHINE,))

    threadWith.start()
    threadWithout.start()

    threadWith.join()
    threadWithout.join()
    print("Longevity application setup complete!!")

    print("Updating load.yaml file...")
    threadFileWith = threading.Thread(target=updateLoadFile,args=(env.WITH_MACHINE,env.YANDEX_WITH_DIR,f"load_with_{lang}.yaml",f"temp_with{lang}.yaml"))
    threadFileWithout = threading.Thread(target=updateLoadFile,args=(env.WITHOUT_MACHINE,env.YANDEX_WITHOUT_DIR,f"load_without_{lang}.yaml",f"temp_without_{lang}.yaml"))

    threadFileWith.start()
    threadFileWithout.start()

    threadFileWith.join()
    threadFileWithout.join()

    print("Starting request firing...")
    threadFiringWith = threading.Thread(target=startRequestFiring,args=(env.LOAD_MACHINE,env.WITH_YANDEX_NAME,env.YANDEX_WITH_DIR))
    threadFiringWithout = threading.Thread(target=startRequestFiring,args=(env.LOAD_MACHINE,env.WITHOUT_YANDEX_NAME,env.YANDEX_WITHOUT_DIR))

    threadFiringWith.start()
    threadFiringWithout.start()

    threadFiringWith.join()
    threadFiringWithout.join()
    global done 
    done = True
    print("Longevity started successfully!!")

if __name__ == "__main__":
    pickEnv()