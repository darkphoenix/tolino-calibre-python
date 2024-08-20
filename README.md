Access to tolino cloud with Python 3 and Calibre
================================================

**TolinoCloud** is an inofficial implementation of the tolino cloud
web reader REST API.

**tolino-calibre-sync** is a fork that uses the tolino API to sync an entire
Calibre library into the tolino cloud - this includes all books in epub
format, most of the metadata from the Calibre library that tolino supports,
the cover images from Calibre, and the creation of a collection in tolino
for every series created in Calibre.

The *tolino ebook reader* is sold by several different partners, most
of them based in Germany, e.g. Thalia or Hugendubel.

The tolino reader comes with its own cloud storage service.

Run by Telekom / T-Systems, the tolino cloud is used to both

- store / backup ebooks purchased by the user

and

- allow the user to upload / sync own files to the user's device(s)

Users can manage their purchased ebooks and uploads through a web
interface, the tolino web reader, which is a HTML5/javascript
application within the user's browser.

Getting started with syncing your library
=========================================
Setting this script up currently requires some added preparation, this will
hopefully improve in the future.  A full Calibre installation is required, as well as a
Python installation with the requests module installed.  On Windows, installing
Python 3.9 from the Windows Store is probably the easiest option.  requests can be installed using the following command:
```
pip install -r requirements.txt
```
Afterwards, download or git clone this repository to a location of your choice.  Rename tolinoclientrc to .tolinoclientrc, then adjust the values in it using any text editor - user and password are your credentials with your tolino reseller, partner is your reseller's ID (see further down this document for a list of IDs). Set dbpath to the full path to your Calibre Library, and libpath to the Python installation you set up earlier - on Windows, this is probably C:\Users\YOURNAME\AppData\Local\Programs\Python\Python39\Lib\site-packages (substitute your username), on Linux it is likely /usr/lib/python3/dist-packages, but may vary depending on the distribution.  Now open a terminal in the directory you unpacked tolino-calibre-sync (on Windows, Shift+right click, then select "Open PowerShell Window here") and type
```
calibre-debug tolino-calibre-sync.py --
```
and hopefully, you'll see tolino-calibre-sync going through your library one by one and uploading them to the tolino cloud.  On subsequent runs only books that were added to Calibre or removed from tolino will be uploaded again.  If you changed things in your Calibre library (replaced covers, changed any metadata except the title, or created a series), you may want to use the --force-covers, --force-meta, or --force-collections flags - in that case, just append them to the command after the --, but be aware that doing so will likely mess up your tolino's order of "recent" books as all books that had their data updated (even if it did not change) will be brought to the front.  Also keep in mind that the full title is currently the only thing used to match books to their counterparts in the tolino cloud, so changing the title will spawn duplicates and two books with the exact same title cannot coexist.

Command line client to tolino cloud
===================================

**tolinoclient.py** executes the web reader's REST API commands
to allow scripted access to a few very basic commands:

- list ebooks / uploads
- upload a file to the user's personal tolino cloud storage
- download a file from the tolino cloud
- delete an ebook / upload
- list devices connected to an account
- unregister a device from an account
- upload cover images
- update metadata for a book
- add books to collections

Status
======

**It may be buggy. Bad things might happen. You were warned.**

Works with these partners:
- Thalia.de (3)
- Thalia.at (4)
- Buch.de (6)
- books.ch / orellfuessli.ch (8)
- Hugendubel.de (13) (currently non-functional)
- Osiander.de (23)
- Buecher.de (30)

(More may be added in the future.)

Tested with Linux and Windows. Patches welcome. Handle with care.

Workaround for auth issues
=====
Currently, some tolino providers are usiing heavy-handed bot blocking
on their authentication servers.  This will break this script.  As a
workaround, I implemented a method to use existing auth credentials
instead of having the script sign in itself.  To do this, open the web
reader, and *before* you sign in, open "Inspect element" and go to the
network tab.  Now sign in as normal, then search for the request to
a document called "registerhw" (most browsers have a search field at the
top).  Click that request, scroll down to "request headers", and use
the content of "hardware_id" as the user name.  Now search for "token", and
copy the "refresh_token" from the response.  Also set use_device = true in
the configuration, and make sure to use the correct partner ID you used to
sign in.  Do not sign out in the browser.  tolino-calibre-sync will now use
this session to synchronise.

To-Do
=====

Better error handling.

More REST API calls (e.g. more collection features).

Support for more resellers.

Hey, tolino developers at Telekom / T-Systems, please look at
the comments in tolinocloud.py. It'd be really nice to get the
specifications for the REST API. Thanks!

Command Line Completion
=======================

If you like command line completion [fish](https://fishshell.com/), you can copy the file `tolinoclient.py.fish` into `~/.config/fish/completions/` (create the directory if needed).

License
=======

**tolino-calibre-sync** is distributed under the terms of the
[GNU Lesser General Public License 2.1](http://www.gnu.org/licenses/lgpl-2.1.txt).
