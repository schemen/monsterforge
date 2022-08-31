# Changelog

## 1.9.0(2022-08-31)

### New
* Cavalry mode. This mode prints the creature on a rectangular base. Mostly for war-gaming.

## 1.8.2(2022-09-03)

### Hotfix
* PDF size is now handled correctly, including a print margin
* Update django


## 1.8.1(2022-05-18)

### Hotfix
* Fix dtype issues when generating images

## 1.8.0(2022-05-18)

### New
* Add the possibility to change the creature background color. Default remains white.
* Added color selection tools to the classic builder as well as the Quickbuilder

### Improvements
* Transparent PNGs have their transparency replaced with the chosen background color.
* Applied a fix where enumeration doesn't apply correctly in the Quickbuilder and sometimes in the classic builder

## 1.7.0(2022-05-18)

### New
* Rearrange how images and nameboxes are sorted on a mini significantly increasing creature image size
  * Before, the namebox size has always been substracted from max_height in any configuration. Now, it will use that space for the image to maximise the size. If a namebox is requested, it will use available space first (max_height) and if not, it'll shrink the image to fit. Now, all space is optimally used and the minis are standardized in size.

## 1.6.5(2022-05-18)

### Improvements
* Image size and creature size are bigger now.
* If you choose a bigger paper size (A4 or Tabloid), Large, Huge and Gargantuan Minis are full height sized. Width is always correct of course.
* Improved the handling of creature position for cleaner minis and better size adjustments (Walking, Hovering, Flying)

## 1.6.4(2022-05-16)

### Improvements
* Added initial wave of unit tests
* Improved error handling, messages

## 1.6.3(2022-05-12)

### Improvements
* Improved english
* Improved descriptions
* Decreased docker image size by 200MB

## 1.6.2(2022-05-11)

### New
* Quickbuilder video added

### Improvements
* Small text tweaks and improvements

## 1.6.1(2022-05-11)

### Hotfix
* Hotfix for the classic minibuilder is released

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
