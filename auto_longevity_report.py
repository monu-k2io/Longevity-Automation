from ast import arg
import os
import concurrent.futures
import sys
from tokenize import String
import plot
import ssh

# PHP
WITH_MACHINE = ssh.User("192.168.5.132","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.133","root","k2cyber")

def getContainer(user: ssh.User,oFile):
    print(f"Detecting running syscall_php container at {user.ip}...")
    cmd = "docker ps -a | grep 'k2-php-vulnerable-perf' | cut -b 1-4"
    # print(cmd)
    id=ssh.doSSH(user,cmd)
    id=id.replace("\n","")
    print("Detected:: ",id)
    if id!="" and id!=None:
        return getCSVFile(user,id,oFile)
    else:
        print("No running container found.")
        return getCSVFile(user,id,oFile)
        return False

def manageCSV(iFile: str):
    print("Modifying and calculating data...")
    tempFile = open("rss_"+iFile, 'w+' )
    tempFile.write("A,B,C,D,E,F,G\n") # names given to columns in csv file respectively
    avgProc = 0
    avgMem = 0
    with open(iFile, 'r') as fp:
        for c, line in enumerate(fp):
            xx = newLine = ""
            if(not(line and line.strip())):
                continue
            tempLine = line.split(" ")
            proc = int(tempLine[0])
            valInMB = int(tempLine[1])/1024
            avgProc += proc
            avgMem += valInMB
            # newLine=line.replace("\n","")+" "+str(valInMB)+"\n"
            newLine=line.replace("\n","")+" "+str(valInMB)+" "+str(valInMB/proc)+"\n"
            xx=newLine.replace(" ",",")
            tempFile.write(xx)
        # print('Total Lines', c + 1)
    fp.close()
    tempFile.close()
    if os.path.exists(iFile):
        os.remove(iFile)

    with open(r"rss_"+iFile, 'r') as fp:
        for count, line in enumerate(fp):
            pass
    # print('Total Lines', count + 1)
    fp.close()
    avgMem=round(avgMem/count)
    avgProc=round(avgProc/count)
    print("Completed!")
    displayFileName = iFile.replace(".csv","")
    print("\n %s agent"%(displayFileName))
    print("======================")
    print(f"Average RSS consumed by all the processes {displayFileName} agent = ",str(avgMem))
    print(f"Average process spawned in {displayFileName} agent case = ",str(avgProc))
    print(f"Average RSS used per process {displayFileName} agent = ",str(avgMem/avgProc))
    print("======================\n")
    return True

def getCSVFile(user: ssh.User,id,oFile):
    print(f"Started copying file from container to {user.ip}...")
    cmd = "docker cp "+id+":/rss/rss_longevity.txt "+oFile
    # print(cmd)
    ssh.doSSH(user,cmd)
    print("Completed!")

    print(f"Started copying file from {user.ip} to local machine...")
    out = ssh.doSCP(user,oFile,f"/root/{oFile}",False)
    # print(out)

    # data=ssh.doSSH(user,f"cat {oFile}")
    # if os.path.exists(oFile):
    #     os.remove(oFile)
    # f = open(oFile, "w")
    # # print(data)
    # f.write(data)
    # f.close()
    print("Completed!")
    return manageCSV(oFile)

# with
argv = sys.argv[1:]
print(argv)
print(f"*** Make sure VPN is connected ***")

# print(f"\n## WITH AGENT")
# threadFiringWith = threading.Thread(target=getContainer,args=(withMachine,"with.csv"))
# print(f"\n## WITHOUT AGENT")
# threadFiringWithout = threading.Thread(target=getContainer,args=(withoutMachine,"without.csv"))

# threadFiringWith.start()
# threadFiringWithout.start()

# outWith = threadFiringWith.join()
# outWithout = threadFiringWithout.join()
with concurrent.futures.ThreadPoolExecutor() as executor:
    futureWith = executor.submit(getContainer, WITH_MACHINE, "with.csv")
    futureWithout = executor.submit(getContainer, WITHOUT_MACHINE, "without.csv")
    outWith = futureWith.result()
    outWithout = futureWithout.result()

print("Data collected successfully!!")

if outWith and outWithout:
    if len(argv) == 2:
        # (WITH,WITHOUT)
        plot.plotGraph("PHP-RSS","Time","RSS","RSS vs Time",'C','F',redLabel=argv[0],blueLabel=argv[1])
        plot.plotGraph("PHP-RSS-per-process","Time","RSS per-process","RSS (per-process) vs Time",'C','G',redLabel=argv[0],blueLabel=argv[1])
        plot.plotGraph("PHP-Process","Time","Process count","Process count vs Time",'C','A',redLabel=argv[0],blueLabel=argv[1])
    else:
        plot.plotGraph("PHP-RSS","Time","RSS","RSS vs Time",'C','F')
        plot.plotGraph("PHP-RSS-per-process","Time","RSS per-process","RSS (per-process) vs Time",'C','G')
        plot.plotGraph("PHP-Process","Time","Process count","Process count vs Time",'C','A')
