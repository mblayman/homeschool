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

Note: `pygraphviz` requires `graphviz`
so you may need to install that first.
On homebrew on a Mac,
you can install that tool
with `brew install graphviz`.

```bash
$ pip install -r requirements-dev.txt
$ pip install -r requirements.txt
```

Install [Heroku CLI tools](https://devcenter.heroku.com/articles/heroku-cli).

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

## Forums

* https://forums.welltrainedmind.com/
* https://forum.memoriapress.com/

## Market Research

This is my analysis of the market
to assess the features and positioning
of what is available.

* Google Classroom
* Homeschool Helper - iPad/Android app. Seems defunct. https://play.google.com/store/apps/details?id=com.homeschoolerhub.llc&hl=en_US&gl=US
* Homeschool Tracker - https://www.homeschooltracker.com/
* Homeschool Minder - https://www.homeschoolminder.com/
* Homeschool Planet - https://homeschoolplanet.com/
* Homeschool Skedtrack - http://www.homeschoolskedtrack.com/HomeSchool/displayLogin.do
* Charlotte Mason Organizer - https://simplycharlottemason.com/store/cm-organizer/
* Lessontrek - https://lessontrek.com/
* Scholaric - https://www.scholaric.com/marketing
* Homeschooling Records - https://homeschoolingrecords.com/default.aspx
* Homeschool Manager - https://homeschoolmanager.com/
* Homeschool Day Book - http://www.homeschooldaybook.com/
* Well Planned Gal - https://shop.wellplannedgal.com/index.php/shop/well-planned-day-online.html
* Homeschool Reporting Online - https://homeschoolreporting.com/
* My School Year - https://www.myschoolyear.com/
