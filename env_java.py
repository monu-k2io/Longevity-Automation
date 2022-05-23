import ssh
import k2_env as K2

# configuration
INSTANA_CONTAINER_NAME = "instana/agent"
INSTANA_CMD = 'docker run --detach --name instana-agent --volume /var/run/docker.sock:/var/run/docker.sock --volume /dev:/dev --volume /sys:/sys --volume /var/log:/var/log --privileged --net=host --pid=host --ipc=host --env="INSTANA_AGENT_KEY=i6anpVVIQPyPvPqdcKxM8w" --env="INSTANA_AGENT_ENDPOINT=saas-us-west-2.instana.io" --env="INSTANA_AGENT_ENDPOINT_PORT=443" instana/agent'
K2_INSTALL_CMD = f"bash {K2.DIR}/k2install/k2install.sh -i micro-agent"
APP_INSTALL_WITH_CMD = "docker run -itd -v /opt/k2root:/opt/k2root -e K2_OPTS=' -javaagent:/opt/k2root/k2root/collectors/k2-java-agent.jar' -e K2_GROUP_NAME=IAST -e JAVA_TOOL_OPTIONS='-Xms4g -Xmx4g' -p 8080:8080 --name syscalls-java k2cyber/test_application:k2-java-vulnerable-perf"
APP_INSTALL_WITHOUT_CMD = "docker run -itd -e JAVA_TOOL_OPTIONS='-Xms4g -Xmx4g' -p 8080:8080 --name syscall_java k2cyber/test_application:k2-java-vulnerable-perf"
APP_CONTAINER_NAME = "k2-java-vulnerable-perf"
WITH_YANDEX_NAME = "yandex-java-with"
WITHOUT_YANDEX_NAME = "yandex-java-without"
YANDEX_WITH_DIR = "/root/longevity/java/with"
YANDEX_WITHOUT_DIR = "/root/longevity/java/without"
WITH_MACHINE = ssh.User("192.168.5.247","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.248","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = "curl -X GET 'http://localhost:8080/rce?arg=.%2F%20%3B%20echo%20%24%28pwd%29' -H  'accept: */*'"
APP_DETECT_TXT = "Started K2JavaVulnerablePerfApplication"
APP_PORT = "8080"