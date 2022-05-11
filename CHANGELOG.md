# Changelog

## 1.6.0(2022-05-11)

### New
* The Quickbuilder beta is released!
  * Since this does not require an account, temporary accounts are deprecated and will be disabled in the future
  * If you want to keep your collections, make sure you convert to a real account

## 1.5.0(2022-05-04)

### New
* Instead of a ZIP file containing images, Monsterforge generates a PDF to print directly

### Improvements
* English has been improved

## 1.4.7(2022-05-04)

### Improvements
* Improve the /minis/ redirect
* Add robots.txt to protect authenticated views

## 1.4.6(2022-05-03)

### Hotfix
* More CR/CreatureType hotfixes

## 1.4.5(2022-05-03)

### Hotfix
* Fix the creature form

## 1.4.4(2022-05-03)

### Improvements
* Change some descriptions
* Smaller UI improvements
* Prevent signed in users from signup and temp account creation
* Remove D&D Agnostic data from creatures, this tool serves all
  * Create CR is no longer available as setting
  * Creature Type is no longer available as setting
  * This allows Monsterforge to be slimmer

## 1.4.3(2022-05-03)

### Improvements
* More descriptive title and meta description


## 1.4.2(2022-05-03)

### Improvements
* Redirect "minis/" to / for people that still the old url somewhere

## 1.4.1(2022-05-03)

### Improvements
* Remove "minis/" sub-url for cleaner urls

## 1.4.0(2022-04-29)

### Features
* First iteration of account management via profile page
  * You can change your password
  * You can delete your account which will delete all of your data

## 1.3.6(2022-04-25)

### Improvements
* Bump Django to fix CVE #55

## 1.3.5(2022-03-16)

### Improvements
* Update several dependencies

## 1.3.4(2022-01-13)

### Improvements
* Bump Django to fix CVE #51

## 1.3.3(2022-01-13)

### Improvements
* Update several dependencies


## 1.3.2(2021-09-22)

### Improvements
* Added Plausible Insights (Default=False)

## 1.3.1(2021-09-21)

### Improvements (So pretty!)
* Added new images on the Index page that better show the results
* Update sidebar image to better represent a forge

## 1.3.0(2021-09-20)

### Improvements
* Fixed many bugs with the DDB Importer (See #41)
* DDB Importer can now handle homebrewed monsters
* Log DDB URLs for better debugging

## 1.2.0 (2021-09-14)

### Improvements

* Code refactoring and cleanup
* Migrate to Django 3.2 (From Django 2.2)
* Enhance RPG Agnostic aspect 
* Several bugfixes
* Dependency updates

## 1.1.1 (2021-08-19)

### Improvements

* Circular minis now have a rectangular guiding lines, this will help crafting it in the end. Cut the Mini and glue it then cut the circle out.

### Other

* Updated the Readme
* Monsterforge is now it's own root

## 1.1.0 (2021-08-18)

### Improvements

* Refactored how images are processed and served, reducing server overhead
* Implemented some basic image caching for each requested build
* Add Link to Changelog notes in footer

## 1.0.7 (2021-08-17)

### fixes

* Fixed a problem where printing Names resulted in a 500 Error (#31)

## 1.0.6 (2021-08-05)

### fixes

* Significantly reduce image size
* Use github actions and registry
* Fix DDBs wrongly defined SRD monster image URL

## 1.0.5 (2021-08-05)

### features

* Add stats command

## 1.0.3 (2021-03-18)

### Fixes

* Update Django dependency due to CVEs

## 1.0.1 (2021-03-18)

### Fixes

* Properly handle deleted objects and cascading

## 1.0.0 (2021-03-17)

### Happy 1.0 release

* Updated the domain from dndbox.com to dice.quest
* Added changelog
* Start using tags for better release management
* Add version display to web
