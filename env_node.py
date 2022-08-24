import ssh
import k2_env as K2

# configuration
LC="node"
APP_PORT = "8080"
APP_CONTAINER_NAME = "k2-node-vulnerable-per-v16"
APP_INSTALL_WITH_CMD = f"docker run --net=host -v /opt/k2root:/opt/k2root:z -e K2_GROUP_NAME={K2.K2_GROUP_NAME} -itd -p {APP_PORT}:8080 --name {APP_CONTAINER_NAME} k2cyber/test_application:syscall_node_v16_with"
APP_INSTALL_WITHOUT_CMD = f'docker run --net=host -itd -p {APP_PORT}:8080 --name {APP_CONTAINER_NAME} k2cyber/test_application:syscall_node_v16_without'
WITH_YANDEX_NAME = "yandex-node-with"
WITHOUT_YANDEX_NAME = "yandex-node-without"
YANDEX_WITH_DIR = "/root/longevity/node/with"
YANDEX_WITHOUT_DIR = "/root/longevity/node/without"
WITH_MACHINE = ssh.User("192.168.5.88","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.89","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = f'curl --location --request GET "http://localhost:{APP_PORT}/ssrf/request?payload=localhost:8080"'
APP_DETECT_TXT = "App started at 8080 port"
LONGEVITY_TIME = "200, 201h"