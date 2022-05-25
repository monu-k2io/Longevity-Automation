import ssh
import k2_env as K2

# configuration
INSTANA_CONTAINER_NAME = "instana/agent"
INSTANA_CMD = 'docker run --detach --name instana-agent --volume /var/run/docker.sock:/var/run/docker.sock --volume /dev:/dev --volume /sys:/sys --volume /var/log:/var/log --privileged --net=host --pid=host --ipc=host --env="INSTANA_AGENT_KEY=i6anpVVIQPyPvPqdcKxM8w" --env="INSTANA_AGENT_ENDPOINT=saas-us-west-2.instana.io" --env="INSTANA_AGENT_ENDPOINT_PORT=443" instana/agent'
K2_INSTALL_CMD = f"bash {K2.DIR}/k2install/k2install.sh -i micro-agent"
APP_INSTALL_WITH_CMD = f"docker run -v /opt/k2root:/opt/k2root:z -e K2_OPTS='--require /opt/k2root/k2root/collectors/k2-njs-agent' -e K2_GROUP_NAME={K2.K2_GROUP_NAME} -itd -p 8080:8080 --name syscall_node k2cyber/test_application:k2-node-vulnerable-per-v16"
APP_INSTALL_WITHOUT_CMD = 'docker run -itd -p 8080:8080 --name syscall_node k2cyber/test_application:k2-node-vulnerable-per-v16'
APP_CONTAINER_NAME = "k2-node-vulnerable-per-v16"
WITH_YANDEX_NAME = "yandex-node-with"
WITHOUT_YANDEX_NAME = "yandex-node-without"
YANDEX_WITH_DIR = "/root/longevity/node/with"
YANDEX_WITHOUT_DIR = "/root/longevity/node/without"
WITH_MACHINE = ssh.User("192.168.5.89","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.88","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = 'curl --location --request GET "http://localhost:8080/ssrf/request?payload=localhost:8080"'
APP_DETECT_TXT = "App started at 8080 port"
APP_PORT = "8080"
LONGEVITY_TIME = "200, 60h"