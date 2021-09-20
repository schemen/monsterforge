# Changelog


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
