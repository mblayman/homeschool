# homeschool

An app for homeschool planning

## Setup

### Python

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

PostgreSQL can be installed with `brew install postgresql`.

```bash
$ pip install -r requirements-dev.txt
$ pip install -r requirements.txt
```

I had some trouble getting pygraphviz to compile
and needed to include some library paths.
Here's what I needed locally.

```bash
CFLAGS="-I/opt/homebrew/Cellar/graphviz/5.0.0/include" \
LDFLAGS="-L/opt/homebrew/Cellar/graphviz/5.0.0/lib" \
pip install -r requirements-dev.txt -r requirements.txt
```

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

## Docker Compose

Tricky problems require better debugging tools.
This command will get db data from Heroku
to inspect issues:

```bash
$ heroku pg:pull HEROKU_PG_NAME postgres://postgres:postgres@localhost:5432/mylocaldb --app APP
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

### Charlotte Mason Organizer

https://simplycharlottemason.com/store/cm-organizer/

* Pitch: Homeschool organizer for those using the Charlotte Mason method.
* The service seems centered around picking specific books
  and adding them to the schedule.
  Books are considered "resources."
* Offers Progress, Attendance, and Bibliography reports
* Share resources with other CM organizer users (paid feature)
* Fetches book information by ISBN
* Resources are attached to "subjects."
* Resources are broken up on the scheduler by "divisions" (e.g., chapters)
  and called "assignments."
* Assignments can be partially completed and marked as "worked on."
* Filters on daily view.

Forum topics:

* https://forums.welltrainedmind.com/topic/147177-simply-charlotte-mason-or-ambleside/ mentioned in passing
* https://forums.welltrainedmind.com/topic/83407-classically-donethinking-charlotte-mason/ likes adding books to organizer
* https://forums.welltrainedmind.com/topic/105037-tell-me-about-the-dvd-seminar-from-simply-charlotte-mason/ uses organizer to add in non-school stuff too like chores
* https://forums.welltrainedmind.com/topic/93216-curricula-questions-about-1st-grade-ds-hf-autism-adhd/ product plug
* https://forums.welltrainedmind.com/topic/511101-question-for-those-that-like-circe-etc/ "splurging on it". Likes that you can miss a day and not have to manually tweak things.

### Google Classroom

https://classroom.google.com/h

* For Teachers, Students, and Parents/Guardians
* Class announcements
* Respond to student posts
* Integration with Google Drive
* Google Worksplace for Education for extra privacy controls
* Define "Rubrics" to tell students how work is graded
* Students see their grades and can submit assignments
* Private messages between teachers and students
* Scheduling abilities of Google Calendar
* Class questions

Forum topics:

* https://forums.welltrainedmind.com/topic/701747-does-anyone-use-google-classroom/ good for assignments, good for lots of kids, student accounts
* https://forums.welltrainedmind.com/topic/702154-attaching-audio-files-to-assignments-in-google-classroom/ attaching audio files to assignments
* https://forums.welltrainedmind.com/topic/698379-public-school-teachers-who-are-losing-it/ use in a public school
* https://forums.welltrainedmind.com/topic/586061-math-textbooks-not-used-in-school-anymore/ use in a middle school
* https://forums.welltrainedmind.com/topic/656644-8th-grade-more-independent/ product plug

### Homeschool Manager

https://homeschoolmanager.com/

* Pricing: $5.99 / month OR $49 / year
* Starts with student setup
* Video help for onboarding
* School Year is bound to student (behaves like Grade Level)
* Drag and drop functionality for task management
* Quick add task feature
* Grade stuff, different task types, grade calculator, grade scales
* Define types of tasks, task weighting for grades
* Volunteer hours tracking
* Book list tracking
* Dashboard to track what's overdue (necessary because tasks are pinned to dates)
* Report cards and past history
* Transcripts
* Attendance and time tracking
* Family logins to allow others to login in with a restricted account
* Click tracking with clicky.com
* JavaScript (Angular?) app so most of the links don't show where a user is about to go.
* Missing many of the empty states on pages

Onboarding

* Simple form to sign up. No credit card.
* Create school and student.
  On first page, sticky footer with "Create my school" CTA.
  Add multiple students in first step.
* Land on students page with warnings that each student doesn't have a school year set up.
* Multi-step wizard to create a school year for a student.
  * School Year == Grade Level
  * Subject == Course, grading and scheduling can be done off platform.
    Quite quick to add multiple subjects for a school year.
    Subject don't default to running on certain days. Must always pick.
    Subjects can run on a monthly schedule.
  * Step 3 is the scheduling for each Subject
* Received a Welcome Email that includes links to help, link to Facebook group, share link
* Day +1, start of a drip campaign explaining the service.

UI

Top nav:

* Left side: Dashboard and Students
* Right side: Help, link to Vimeo video help, account drop down

Dashboard:

* Low information initially
* Links to student pages of various types

Accounts section:

* Divided into tabs to separate topics.
* School info, contact info, subscription, holidays, tasks & weighting, grading scales, logins

Student index:

* I can't quickly look at the week view for both of my students at the same time.

Student section:

* Schedule
  * Task entry doesn't work if school year starts in the future.
    This is not obvious.
  * Tasks are draggable to different days.
    Tasks dragged to "Next week" move to the same day on the following week.
* Gradebook
* Book list
* Documents
  * This is a section for generating documents.
    These are reports in formats like PDF and XSLX
* Admin
  * School years
  * Grade scale
  * Volunteer hours - quick add form

Forum topics: Nothing found.

### Homeschool Minder

https://www.homeschoolminder.com/

* From 2012
* Pricing $4.99 / month OR $39.99 / year (free trial, length not on homepage)
* Broken blog
* Primary features from intro video
  * Scheduler (Calendar)
  * Gradebook
  * Lesson plans
  * Skill tracking
  * Student records
  * Reports
* Grade scales - users can define the numbers and symbols used
* Calendar has some pretty deep recurrence features
* Lesson plans
  * a way to group and sub-divide activities within a course.
  * Tied to a course and term (i.e., intended to be time bound)
* Skills
  * Skills track activities within a course too, but are not time bound
  * A group of Skills is a Standard
* Student Information
  * Tracks a bunch of personal identification (:grimacing:)
  * Can add aribtrary custom fields and values
  * Tracks contact information
  * Tracks standardized test scores
  * Tracks "Readings" aka a book list
  * Tracks community service information
* Reports
  * Lots of different report choices
  * All seem to be generated PDFs
* Student Logins
  * Students get a mostly read only view, but can complete tasks.
* School Years require terms and courses must be added to a term.
* Students are added to courses via a Registration
  * It looks like a registration is needed per course (whoa, heavy).
* The service can track any random events on the calendar.
* Assignments have customizable categories.
* Sign up experience
  * Sign up directly from landing page
  * Dumps into an intro flow popover
    * Step 1: Long (7 minute) intro video
    * Step 2: Asks for a bunch of teacher settings
    * Step 3: Sets up a year and some terms based on pre-configured dates
    * Step 4: Create student
    * Step 5: Create courses
    * Step 6: Weird old message about getting docs together and a "beta"
      (what? This isn't 2012 any more)
    * Land on an empty calendar after filling out details
  * Received welcome email
  * Discovered from settings page that the trial is 30 days long

UI

* Main section: Student Planner
  * Calendar
    * One student at a time
    * Add items from the calendar
    * Highly interactive
    * Week view expands into hourly view
  * Skills
    * A bit confusing to add a standard, then add a skill.
* Only other tab: "Resources" - unclickable and "coming soon"
* Secondary tabs
  * Settings
  * Help - links out to /docs
  * Log out


Forum topics:

* https://forums.welltrainedmind.com/topic/481657-homeschool-planet-anyone-trying-it/ mentioned in comparison 2013
* https://forums.welltrainedmind.com/topic/683608-6th-grade-2019-2020/ mentioned in comparison 2019

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
