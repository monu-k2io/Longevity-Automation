import ssh
import k2_env as K2

# configuration
LC="go"
APP_PORT = "8084"
APP_CONTAINER_NAME = "syscall-go"
APP_INSTALL_WITH_CMD = f"docker run -itd -v /opt/k2root:/opt/k2root -p {APP_PORT}:8084 -e K2_GROUP_NAME={K2.K2_GROUP_NAME} --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}"
APP_INSTALL_WITHOUT_CMD = f'docker run -itd -p {APP_PORT}:8084 -e K2_NULL=true --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}'
WITH_YANDEX_NAME = "yandex-go-with"
WITHOUT_YANDEX_NAME = "yandex-go-without"
YANDEX_WITH_DIR = "/root/longevity/go/with"
YANDEX_WITHOUT_DIR = "/root/longevity/go/without"
WITH_MACHINE = ssh.User("192.168.5.142","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.143","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = f'curl --location --request GET "http://localhost:{APP_PORT}"'
APP_DETECT_TXT = "connection accepted from"
LONGEVITY_TIME = "200, 201h"