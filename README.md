# homeschool

An app for homeschool planning

## Setup

Create a virtual environment.

```bash
$ python -m venv venv
```

Activate the virtual environment.

```bash
$ source venv/bin/activate
```

Install developer and application packages.

```bash
$ pip install -r requirements-dev.txt
$ pip install -r requirements.txt
```

Install [Herok CLI tools](https://devcenter.heroku.com/articles/heroku-cli).

Bootstrap the local database.

```bash
$ ./manage.py migrate
```

Create a superuser account.

```bash
$ ./manage.py createsuperuser
```

Start the local web server.

```bash
$ make
```
