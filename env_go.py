import ssh
import k2_env as K2

# configuration
LC="go"
INSTANA_CONTAINER_NAME = "instana/agent"
INSTANA_CMD = 'docker run --detach --name instana-agent --volume /var/run/docker.sock:/var/run/docker.sock --volume /dev:/dev --volume /sys:/sys --volume /var/log:/var/log --privileged --net=host --pid=host --ipc=host --env="INSTANA_AGENT_KEY=i6anpVVIQPyPvPqdcKxM8w" --env="INSTANA_AGENT_ENDPOINT=saas-us-west-2.instana.io" --env="INSTANA_AGENT_ENDPOINT_PORT=443" instana/agent'
APP_CONTAINER_NAME = "syscall-go"
APP_INSTALL_WITH_CMD = f"docker run -itd -v /opt/k2root:/opt/k2root -p 8084:8084 -e K2_GROUP_NAME={K2.K2_GROUP_NAME} -e K2_BRANCH={K2.K2_BRANCH} --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}"
APP_INSTALL_WITHOUT_CMD = f'docker run -itd -p 8084:8084 -e K2_NULL=true --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}'
WITH_YANDEX_NAME = "yandex-go-with"
WITHOUT_YANDEX_NAME = "yandex-go-without"
YANDEX_WITH_DIR = "/root/longevity/go/with"
YANDEX_WITHOUT_DIR = "/root/longevity/go/without"
WITH_MACHINE = ssh.User("192.168.5.142","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.143","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = 'curl --location --request GET "http://localhost:8084"'
APP_DETECT_TXT = "connection accepted from"
APP_PORT = "8084"
LONGEVITY_TIME = "200, 201h"