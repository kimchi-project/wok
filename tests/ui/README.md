# Wok E2E Tests

The tests are located in `tests/ui`. You should go to the directory to start them
```
$ cd tests/ui
```

## How to run

First you need to install all dependencies, start Wok server and run the tests

### Optional: install a virtual environment

```
$ python3 -m venv .env
$ source .env/bin/activate
```

### Install deps
```
$ pip install -r requirements.txt
```

### Install Browser

This tests expect Google Chrome installed. Visit https://www.google.com/chrome/ for info

### Start wok server

```
$ python src/wokd
```

### Run in headless mode
The script expect some environment variables to run wok tests, which are:

```
Expect environment variables:
USERNAME: username for the host   default: root
PASSWORD: password for the host
HOST: host for wok             default: localhost
PORT: port for wok             default: 8001
```

So, if you are running against a remote host:

```
$ HOST=<HOST> ./run_tests.sh
Type password for host USER@HOST

```

### Run in debug mode
If you use the command above, the browser will no be visible for you.

To see the browser action, add the variable `DEBUG`

```
$ HOST=<HOST> DEBUG=true ./run_tests.sh
Type password for host USER@HOST

```