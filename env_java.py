import ssh
import k2_env as K2

# configuration
LC="java"
APP_PORT = "8080"
APP_CONTAINER_NAME = "k2-java-vulnerable-perf"
APP_INSTALL_WITH_CMD = f"docker run -itd -v /opt/k2root:/opt/k2root -e K2_OPTS=' -javaagent:/opt/k2root/k2root/collectors/k2-java-agent.jar' -e K2_GROUP_NAME={K2.K2_GROUP_NAME} -e JAVA_TOOL_OPTIONS='-Xms900m -Xmx1g' -p {APP_PORT}:8080 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}"
APP_INSTALL_WITHOUT_CMD = f"docker run -itd -e JAVA_TOOL_OPTIONS='-Xms900m -Xmx1g' -p {APP_PORT}:8080 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}"
WITH_YANDEX_NAME = "yandex-java-with"
WITHOUT_YANDEX_NAME = "yandex-java-without"
YANDEX_WITH_DIR = "/root/longevity/java/with"
YANDEX_WITHOUT_DIR = "/root/longevity/java/without"
WITH_MACHINE = ssh.User("192.168.5.247","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.248","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = f"curl -X GET 'http://localhost:{APP_PORT}/rce?arg=.%2F%20%3B%20echo%20%24%28pwd%29' -H  'accept: */*'"
APP_DETECT_TXT = "Started K2JavaVulnerablePerfApplication"
LONGEVITY_TIME = "200, 201h"