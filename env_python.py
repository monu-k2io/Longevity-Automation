import ssh
import k2_env as K2

# configuration
INSTANA_CONTAINER_NAME = "instana/agent"
INSTANA_CMD = 'docker run --detach --name instana-agent --volume /var/run/docker.sock:/var/run/docker.sock --volume /dev:/dev --volume /sys:/sys --volume /var/log:/var/log --privileged --net=host --pid=host --ipc=host --env="INSTANA_AGENT_KEY=i6anpVVIQPyPvPqdcKxM8w" --env="INSTANA_AGENT_ENDPOINT=saas-us-west-2.instana.io" --env="INSTANA_AGENT_ENDPOINT_PORT=443" instana/agent'
K2_INSTALL_CMD = f"bash {K2.DIR}/k2install/k2install.sh -i micro-agent"
APP_INSTALL_WITH_CMD = "docker run -v /opt/k2root:/opt/k2root:z -e K2_OPTS='-m k2_python_agent' -e PYTHONPATH=/opt/k2root/k2root/collectors/k2-python-agent/lib/site-packages -e K2_GROUP_NAME=IAST -itd -p 8000:8000 --name syscalls_python k2cyber/test_application:syscalls_python"
APP_INSTALL_WITHOUT_CMD = "docker run -itd -p 8000:8000 --name syscalls_python k2cyber/test_application:syscalls_python"
APP_CONTAINER_NAME = "syscalls_python"
WITH_YANDEX_NAME = "yandex-python-with"
WITHOUT_YANDEX_NAME = "yandex-python-without"
YANDEX_WITH_DIR = "/root/longevity/python/with"
YANDEX_WITHOUT_DIR = "/root/longevity/python/without"
WITH_MACHINE = ssh.User("192.168.5.138","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.136","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = 'curl "http://localhost:8000/file/file_view_read"'
APP_DETECT_TXT = "Starting development server"
APP_PORT = "8000"