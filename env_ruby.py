import ssh
import k2_env as K2

# configuration
LC="ruby"
APP_PORT = "3000"
APP_CONTAINER_NAME = "syscalls-ruby-unicorn"
APP_INSTALL_WITH_CMD = f'docker run -e K2_GROUP_NAME={K2.K2_GROUP_NAME} -v /opt/k2root:/opt/k2root/ -v /opt/k2root/k2root/collectors:/opt/k2-ic -e K2_OPTS=/opt/k2root/k2root/collectors/k2-ruby-agent -e K2_HOME=/opt/k2root -itd -p {APP_PORT}:3000 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}'
APP_INSTALL_WITHOUT_CMD = f'docker run -itd -p {APP_PORT}:3000 --name {APP_CONTAINER_NAME} k2cyber/test_application:{APP_CONTAINER_NAME}'
WITH_YANDEX_NAME = "yandex-ruby-with"
WITHOUT_YANDEX_NAME = "yandex-ruby-without"
YANDEX_WITH_DIR = "/root/longevity/ruby/with"
YANDEX_WITHOUT_DIR = "/root/longevity/ruby/without"
WITH_MACHINE = ssh.User("192.168.5.68","root","k2cyber")
WITHOUT_MACHINE = ssh.User("192.168.5.66","root","k2cyber")
LOAD_MACHINE = ssh.User("192.168.5.62","root","k2cyber")
FIRST_CURL = f'curl --location --request GET "http://localhost:{APP_PORT}"'
APP_DETECT_TXT = "Starting factory"
LONGEVITY_TIME = "100, 201h"