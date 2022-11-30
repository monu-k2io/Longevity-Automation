from env_java import LONGEVITY_TIME
import ssh
import k2_env as K2

# configuration
LC="python"
APP_PORT = "8000"
APP_CONTAINER_NAME = "syscalls_python"
APP_INSTALL_WITH_CMD = f"docker run -v /opt/k2root:/opt/k2root:z -e K2_OPTS='-m k2_python_agent' -e PYTHONPATH=/opt/k2root/k2root/collectors/k2-python-agent/lib/site-packages -e K2_GROUP_NAME={K2.K2_GROUP_NAME} -itd -p {APP_PORT}:8000 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}"
APP_INSTALL_WITHOUT_CMD = f"docker run -e K2_OPTS='' -itd -p {APP_PORT}:8000 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}"
WITH_YANDEX_NAME = "yandex-python-with"
WITHOUT_YANDEX_NAME = "yandex-python-without"
YANDEX_WITH_DIR = "/root/longevity/python/with"
YANDEX_WITHOUT_DIR = "/root/longevity/python/without"
WITH_MACHINE = ssh.User("192.168.5.138","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.135","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = f'curl "http://localhost:{APP_PORT}/file/file_view_read"'
APP_DETECT_TXT = "Starting development server"
LONGEVITY_TIME = "200, 201h"