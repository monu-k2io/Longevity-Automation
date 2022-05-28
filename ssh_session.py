from pexpect import pxssh
from models.user import User

class Terminal:
    def __init__(self, session: pxssh.pxssh):
        self._session = session

    # getter method
    def get_session(self) -> pxssh.pxssh:
        return self._session

    def login(user: User):
        try:
            s = pxssh.pxssh()
            s.login(user.ip, user.username, user.password, sync_multiplier=30)
            return Terminal(s)
        except pxssh.ExceptionPxssh as e:
            print("pxssh failed on login.")
            print(e)

    def logout(self):
        try:
            return self.get_session().logout()
        except pxssh.ExceptionPxssh as e:
            print("pxssh failed on logout.")
            print(e)

    def execute(self,cmd) -> str:
        try:
            s = self.get_session()
            # print(cmd)
            s.sendline(cmd)
            fout = open('mylog.txt','wb')
            s.logfile = fout
            s.prompt()
            stdout = str(s.before, 'utf-8').replace(cmd, "")
            # print(stdout)
            return stdout
        except pxssh.ExceptionPxssh as e:
            self.logout()
            print("pxssh failed cmd execution.")
            # print(e)
            return e