import tempfile
import pexpect

class User:
  def __init__(self, i, u, p):
    self.ip = i
    self.username = u
    self.password = p

def doSSH(user: User, cmd, bg_run=False):                                                                                                 
    """SSH'es to a host using the supplied credentials and executes a command.                                                                                                 
    Throws an exception if the command doesn't return 0.                                                                                                                       
    bgrun: run command in the background"""                                                                                                                               
    try:
        options = '-q -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -oPubkeyAuthentication=no'                                                                         
        if bg_run:                                                                                                                                                         
            options += ' -f'                                                                                                                                   
        ssh_cmd = 'ssh %s@%s %s "%s"' % (user.username, user.ip, options, cmd)      
        # print(ssh_cmd)                                                                                                                 
        out = driver(user,ssh_cmd)
    except Exception as e:
        out = e
        print(out)
    finally:
        # print(out)
        return out

def doSCP(user: User, file, dir, toServer=True):
    try: 
        if toServer:
            scp_cmd = 'scp %s %s@%s:%s' % (file, user.username, user.ip, dir)
        else:
            scp_cmd = 'scp %s@%s:%s %s' % (user.username, user.ip, dir, file)
        # print(scp_cmd)                                                                                                           
        out =  driver(user,scp_cmd)
    except Exception as e:
        out = e
        print(out)
    finally:
        # print(out)
        return out

def driver(user: User, cmd, timeout=600):
    fname = tempfile.mktemp()                                                                                                                                                  
    fout = open(fname, 'w')                                                                                                                                                    
                                                                                                                                                                               
    child = pexpect.spawnu(cmd, timeout=timeout)  #spawnu for Python 3                                                                                                                          
    child.expect(['[pP]assword: '])                                                                                                                                                                                                                                                                                               
    child.sendline(user.password)                                                                                                                                                   
    child.logfile = fout                                                                                                                                                
    child.expect(pexpect.EOF)                                                                                                                                                  
    child.close()                                                                                                                                                              
    fout.close()                                                                                                                                                               
                                                                                                                                                                                                                                                                                                                        
    fin = open(fname, 'r')                                                                                                                                                     
    stdout = fin.read()                                                                                                                                                        
    fin.close()                                                                                                                                                                
                                                                                                                                                                               
    if 0 != child.exitstatus:                                                                                                                                                  
        raise Exception(stdout)                                                                                                                                                
                                                                                                                                                                  
    return stdout