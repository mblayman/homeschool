# homeschool

An app for homeschool planning

## Setup

### Python

`uv` is required.

### JavaScript

Node.js is required.

```bash
brew install nodejs
```

Install JS packages to get Tailwind CSS.

```bash
npm i
```

### Deployment

Install [Heroku CLI tools](https://devcenter.heroku.com/articles/heroku-cli).

Bootstrap the local database.

```bash
$ uv run manage.py migrate
```

Create a superuser account.

```bash
$ uv run manage.py createsuperuser
```

Start the local web server.

```bash
$ make
```

## Docker Compose

Tricky problems require better debugging tools.
This command will get db data from Heroku
to inspect issues:

`mylocaldb` is needed because the pull needs the db not to exist so I can't use
the default `postgres` db that is already in the postgres image.

```bash
$ heroku pg:pull HEROKU_PG_NAME postgres://postgres:postgres@localhost:5432/mylocaldb --app APP
heroku pg:pull HEROKU_POSTGRESQL_ROSE_URL postgres://postgres:postgres@localhost:5432/mylocaldb
# Needs createdb on path
```

Analyzing image contents:

```
alias dive="docker run -ti --rm  -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive"
dive klakegg/hugo:0.101.0
```

### uv

Since my macOS version is so old, psycopg doesn't have a binary package.
This causes uv (and pip!) to break.
Because of that, I'm forced to use uv through the Docker image,
but there are some settings needed to get around the fact that image doesn't install
packages in a place writeable by the app user.

Here's an example:

```
UV_PROJECT_ENVIRONMENT=/tmp/uv-venv uv add -n --dev 'types-toml==0.10.8.20240310'
```

## Cloud Migration

Current strategy for migrating the database

1. Turn on maintenance mode via Heroku dashboard.
2. Confirm app is offline.
3. Clear Postgres docker container content.
4. Start Postgres docker container.
5. Get production database dump via `heroku pg:pull`
6. From the web container with the DATABASE_URL pointing at Postgres, run: `./manage.py dumpdata -o production.json`
7. Stop Docker Compose.
8. Switch to SQLite as the DATABASE_URL.
9. Start Docker Compose and allow migrations to run.
10. From Django shell, remove all `ContentType` records to avoid integrity errors. `ContenType.objects.all().delete()`.
11. From container shell, `./manage.py loaddata production.json`
12. `kamal app stop` to stop the staging site.
13. scp production db to /var/db
14. chown db to app user and replace existing app.
15. `kamal app boot` to restart.
16. Verify via customer impersonation that data is valid for my family.
17. Remove CNAME record for www subdomain. (Value was: `transparent-dinosaur-0xw2wzz66pp8iu7q49k1ayac.herokudns.com`)
18. Add A record for www subdomain.
19. Wait until dig returns the expected IP address.
20. Update kamal config to change from `staging` to `www`.
21. Deploy.
22. Verify site is live at the www subdomain.

### Server config

1. Add ssh keys.
2. Turn off passworth auth

```
/etc/ssh/sshd_config
PasswordAuthentication no
systemctl restart ssh
```

3. Firewall stuff.

```
ufw allow OpenSSH
ufw default deny incoming
ufw enable
```

## Market Research

This is my analysis of the market
to assess the features and positioning
of what is available.

Research plan:
Sign up for a service trial
to test out the account.
Share findings on forums
to solicit feedback.

Measurement criteria:

* Price
* Features
* Quality

[Well Trained Mind reference analysis](https://docs.google.com/spreadsheets/d/1SroV3KdUshFIQMOEKfVDtv5zwmcylL6OHfewTuaeJRo/edit?usp=sharing)

### Product Matrix

| Product | Business Model | Price | Reviewed |
| --- | --- | --- | --- |
| CM Organizer | Freemium | $7.95 / month | 2/1/21 |
| Google Classroom | Free | $0 | 3/12/21 |
| Homeschool Manager | Subscription | $5.99 / month | 3/13/21 |
| Homeschool Minder | Subscription | $4.99 / month | 5/3/21 |
| Homeschool Planet | Subscription | $7.95 / month | 5/20/21 |

### Homeschool Planet

https://homeschoolplanet.com/

"Synchronize your home, school, and work into a single place"

* Landing page
  * Email list capture
* Pricing
  * 30 day trial
  * $69.95 / year
  * $7.95 / month
* Social Media
  * Heavy activity on Facebook (at least daily)
  * Pinterest
  * YouTube to host help docs
  * Instagram
  * Blog (infrequent posts - handful per year, guest posts)
* Marketplace
  * Other vendors provide lesson plans
* Features
  * Daily digest email
  * Text messaging
  * Widgets with the calendar
  * Assignment == School Desk Task
  * Grades have different types and calculations
  * Tracks attendance
  * Tracks resources
  * Profiles (pictures, emails for sending digests, phone number for text messages)
  * Lookup widget (embedded search of other services)
* Testimonials
  * User reviews (but they are old! 2017!)
  * Featured reviews (appear "fresh" from 2019, but are recycled old reviews),
    seems shady
  * Lots of undated testimonials (current user reviews?)

Forum topics:

* https://forums.welltrainedmind.com/topic/701712-best-family-calendarorganizer-app/ compat with Google Calendar
* https://forums.welltrainedmind.com/topic/683608-6th-grade-2019-2020/ winner in comparison
* https://forums.welltrainedmind.com/topic/574023-need-to-simplify-school/ student access
* https://forums.welltrainedmind.com/topic/670110-reviews-on-open-tent-academy-writing-classes/ mentioned putting in schedule
* https://forums.welltrainedmind.com/topic/658388-were-starting-to-hate-math-mammoth/ lesson plan
* https://forums.welltrainedmind.com/topic/539500-onenote-vs-homeschool-planet/ gushing for planet
* https://forums.welltrainedmind.com/topic/558061-homeschool-planet-users-help-a-newbie-out/ support question
* https://forums.welltrainedmind.com/topic/540597-homeschool-tracker-online-vs-homeschool-planet/ beating homeschool tracker
* https://forums.welltrainedmind.com/topic/481657-homeschool-planet-anyone-trying-it/ beta review 2013
* https://forums.welltrainedmind.com/topic/684121-homeschool-planet-coupon-code/ looking for coupon code
* https://forums.welltrainedmind.com/topic/618353-homeschool-planner-and-how-do-you-plan/ product plug
* https://forums.welltrainedmind.com/topic/666654-mid-year-shakeup/ trialing
* https://forums.welltrainedmind.com/topic/521718-digital-planner-for-looping-schedule/ looping schedule question w/ no response
* https://forums.welltrainedmind.com/topic/540799-which-online-planner-will-let-me-bump-two-ways/ bump work to another day
* https://forums.welltrainedmind.com/topic/681351-educents-shutting-down-changing-direction/ comparison

### Homeschool Reporting Online

https://homeschoolreporting.com/

Forum topics:

Nothing found.

### Homeschool Skedtrack

http://www.homeschoolskedtrack.com/HomeSchool/displayLogin.do

Forum topics:

* https://forums.welltrainedmind.com/topic/109604-anyone-use-homeschool-skedtrack/ discussion of site
* https://forums.welltrainedmind.com/topic/521718-digital-planner-for-looping-schedule/ looping questions
* https://forums.welltrainedmind.com/topic/540598-lets-share-how-we-set-up-onenote/ onenote replacing skedtrack
* https://forums.welltrainedmind.com/topic/265754-gradingrecord-keepingtranscripts/ looking for tools 2011
* https://forums.welltrainedmind.com/topic/109114-free-curriculum-list/ curriculum list 2009
* https://forums.welltrainedmind.com/topic/337281-if-you-have-a-long-loop-schedule-for-your-homeschool-can-you-share/ looping schedule topic
* https://forums.welltrainedmind.com/topic/397457-scholaric-or-homeschool-tracker-plus/ tool comparison
* https://forums.welltrainedmind.com/topic/401214-which-homeschool-planners-allow-you-to-print-like-this/ printing schedules
* https://forums.welltrainedmind.com/topic/338659-if-youve-done-both-mfw-and-hod/ preparing schedules
* https://forums.welltrainedmind.com/topic/586966-how-do-you-schedule-your-180-days/ planning many days in advance
* https://forums.welltrainedmind.com/topic/449025-is-there-has-planner-app/?tab=comments looking for ipad app
* https://forums.welltrainedmind.com/topic/665813-opinions-on-memoria-press-core-curriculum/ product plug

### Homeschool Tracker

https://www.homeschooltracker.com/

Forum topics:

* https://forums.welltrainedmind.com/topic/383203-edu-track-vs-homeschool-tracker/ vs EduTrack 2012
* https://forums.welltrainedmind.com/topic/23954-homeschool-tracker-questions/ HST vs HST+ 2008
* https://forums.welltrainedmind.com/topic/540597-homeschool-tracker-online-vs-homeschool-planet/ vs planet 2015
* https://forums.welltrainedmind.com/topic/254395-record-keeping-homeschool-tracker-and-ipad/ ipad
* https://forums.welltrainedmind.com/topic/54161-homeschool-tracker-question/ questions about product 2008
* https://forums.welltrainedmind.com/topic/397457-scholaric-or-homeschool-tracker-plus/ vs Scholaric 2012
* https://forums.welltrainedmind.com/topic/186110-whats-a-good-homeschool-planner/ product plug 2010
* https://forums.welltrainedmind.com/topic/5826-do-you-find-lesson-planning-software-useful-any-for-mac-users-other-suggestions/ product plug
* https://forums.welltrainedmind.com/topic/265754-gradingrecord-keepingtranscripts/ product plug
* https://forums.welltrainedmind.com/topic/401214-which-homeschool-planners-allow-you-to-print-like-this/ print question
* https://forums.welltrainedmind.com/topic/649011-do-you-lesson-plan/ product plug
* https://forums.welltrainedmind.com/topic/249069-transcript-for-7th-and-8th-grade/ passing reference
* https://forums.welltrainedmind.com/topic/109114-free-curriculum-list/ product plug 2009
* https://forums.welltrainedmind.com/topic/683608-6th-grade-2019-2020/ tried but planet won 2019
* https://forums.welltrainedmind.com/topic/637551-is-classical-conversations-a-cultor-productor/ for transcripts 2017
* https://forums.welltrainedmind.com/topic/8909-how-much-is-too-much-or-not-enough/ product plug 2008
* https://forums.welltrainedmind.com/topic/129844-homeschool-tracker-question/?tab=comments#comment-1222284 question about product
* https://forums.welltrainedmind.com/topic/203459-terribly-embarrassed-herewhyhow-do-you-create-lesson-plans/ product plug
* https://forums.welltrainedmind.com/topic/222511-ambleside-online/ for printing
* https://forums.welltrainedmind.com/topic/341507-wondering-about-tearing-up-workbooks-vs-leaving-them-whole/ product plug
* https://forums.welltrainedmind.com/topic/111220-baffled-by-michael-clay-thompson-la/ lesson plans
* https://forums.welltrainedmind.com/topic/100480-ambleside-online-users/ product plug
* https://forums.welltrainedmind.com/topic/84644-need-ideas-for-tracking/?tab=comments#comment-828678 product plug

### Homeschooling Records

https://homeschoolingrecords.com/default.aspx

Forum topics:

Nothing found.

### Lessontrek

https://lessontrek.com/

Forum topics:

* https://forums.welltrainedmind.com/topic/618353-homeschool-planner-and-how-do-you-plan/ former user 2016
* https://forums.welltrainedmind.com/topic/688779-how-do-i-make-a-custom-planner/?tab=comments#comment-8402441 asked about usage

### My School Year

https://www.myschoolyear.com/

Forum topics:

Nothing found.

### Scholaric

https://www.scholaric.com/marketing

Forum topics:

* https://forums.welltrainedmind.com/topic/397457-scholaric-or-homeschool-tracker-plus/ vs HST+ 2012
* https://forums.welltrainedmind.com/topic/423847-scholaric-review-and-giveaway/ product plug 2012
* https://forums.welltrainedmind.com/topic/675595-grading-software/ product plug grading software 2018
* https://forums.welltrainedmind.com/topic/540799-which-online-planner-will-let-me-bump-two-ways/ product plug 2015
* https://forums.welltrainedmind.com/topic/401214-which-homeschool-planners-allow-you-to-print-like-this/ for printing 2012
* https://forums.welltrainedmind.com/topic/297229-scholaric-vs-skedtrack-for-planning/?tab=comments#comment-2986890 vs skedtrack 2011
* https://forums.welltrainedmind.com/topic/481657-homeschool-planet-anyone-trying-it/ vs planet 2013
* https://forums.welltrainedmind.com/topic/521718-digital-planner-for-looping-schedule/ looping question
* https://forums.welltrainedmind.com/topic/640723-do-you-use-a-planner-of-some-sort/ planner question 2017
* https://forums.welltrainedmind.com/topic/618353-homeschool-planner-and-how-do-you-plan/ product comparison 2016
* https://forums.welltrainedmind.com/topic/624024-record-keeping-for-relaxed-homeschooling-with-larger-families/ large family 2016
* https://forums.welltrainedmind.com/topic/611151-truthquest-vs-veritas-press-self-paced-history/ product plug 2016
* https://forums.welltrainedmind.com/topic/477446-little-known-secret-curric-to-try/ product plug 2013
* https://forums.welltrainedmind.com/topic/358659-ipads-for-homeschooling/ product plug 2012
* https://forums.welltrainedmind.com/topic/343523-well-my-paces-curriculum-came-today/ product plug 2012
* https://forums.welltrainedmind.com/topic/449025-is-there-has-planner-app/?tab=comments ipad 2012
* https://forums.welltrainedmind.com/topic/376514-curious-about-winter-promise/ product plug 2012

### Well Planned Gal

https://shop.wellplannedgal.com/index.php/shop/well-planned-day-online.html

* https://forums.welltrainedmind.com/topic/393417-ultimate-homeschool-planner-vs-well-planned-day/ product comparison 2012
* https://forums.welltrainedmind.com/topic/195695-anyone-try-the-well-planned-day-planners/ paper? 2010
* https://forums.welltrainedmind.com/topic/186110-whats-a-good-homeschool-planner/ product comparison 2010
* https://forums.welltrainedmind.com/topic/618353-homeschool-planner-and-how-do-you-plan/ product comparison 2016
* https://forums.welltrainedmind.com/topic/481657-homeschool-planet-anyone-trying-it/ vs planet 2013
* https://forums.welltrainedmind.com/topic/415058-ipad-users-homeschool-helper-app/ ipad 2012

### Audience

Things to try:

* Google Adwords keyword planner
* followerwonk.com
* Topsy Analytics to check social mentions?
* Ahrefs Site Explorer to see referral traffic for other sites
* BuzzSumo for Twitter analysis
* Homeschool magazines? Is that a thing?
* Amazon reviews of homeschool stuff
* Reddit has a homeschool subreddit
* Popular homeschool blogs to contact?
* Homeschool podcasts?
* Monthly webinars?

### Future

* Dunning - Don't make customer sign in to update card info
* Dunning - Don't email until the card has actually failed (wait until 3rd reattempt or 5 days)
* Dunning - Email multiple times. It's ok. People miss stuff.
* Churn Buster if crazy popular by some remote chance
* Make Annual <-> Monthly up/downgrade not hard

### Persona

This is an exercise to build a reasonable persona
of the ideal customer for School Desk
as suggested in SaaS Marketing Essentials.

Hannah Homeschooler:

* Hannah is a 30 - 45 year old woman.
* She is educated and a self-starter (fiercely independent).
* Hannah has two children.
* Hannah lives in a suburban area or small to mid-size city.
* Her time is constrained while balancing home obligations with child education.
* Hannah has a fondness for paper for keeping records.
  Before finding School Desk,
  she was starting to hit the limits of her process
  and was looking for a way to save time.
* Hannah wants full control of *what* she teaches her children,
  but would like some tools that can take out the drudgery
  of building weekly schedules for school.
* After using School Desk,
  Hannah benefits from the automatically generated schedules
  that show *her* material
  in a timeframe that fits the constraints
  that she specified to School Desk.
* School Desk makes it painless to stay on top of homeschool
  so that she focus her attention on other parts of her life.

### Product Position

What's the point? Why would Hannah want to use School Desk?
Is it control? Is it time saving?

What is the benefit?

* "Take Control of Your Homeschool Plan"
* "Save Time Building Your Homeschool Plan"
* "Focus on Your School, Let Us Handle the Schedule"
* Stop swimming in spreadsheets
* Not an airplane cockpit

Customer answer: The key benefit is simplicity.
