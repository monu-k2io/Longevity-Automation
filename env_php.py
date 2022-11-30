import ssh
import k2_env as K2

# configuration
LC="php"
APP_PORT = "80"
# k2-php-vulnerable-perf syscall_php_coredump php_syscall_valgrind
APP_CONTAINER_NAME = "k2-php-vulnerable-perf"
# --privileged --cap-add=SYS_PTRACE --security-opt seccomp=unconfined 
APP_INSTALL_WITH_CMD = f'docker run -v /opt/k2root:/opt/k2root:z -e K2_GROUP_NAME="{K2.K2_GROUP_NAME}" -itd -p {APP_PORT}:80 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}'
APP_INSTALL_WITHOUT_CMD = f'docker run -itd -p {APP_PORT}:80 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}'
WITH_YANDEX_NAME = "yandex-php-with"
WITHOUT_YANDEX_NAME = "yandex-php-without"
YANDEX_WITH_DIR = "/root/longevity/php/with"
YANDEX_WITHOUT_DIR = "/root/longevity/php/without"
WITH_MACHINE = ssh.User("192.168.5.133","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.132","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = f'curl --location --request GET "http://localhost:{APP_PORT}/syscall-app/file-access-read.php?page=../../../../etc/passwd"'
APP_DETECT_TXT = "Apache server started"
LONGEVITY_TIME = "200, 201h"