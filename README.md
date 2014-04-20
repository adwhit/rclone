Rosetta Clone
=============

Improved UI for browsing the [Rosetta Code](http://www.rosettacode.org) website.

To be hosted [here](http://www.rosettaclone.org) (use AWS).

Screenshot: ![shot](misc/Screenshot04182014.jpg) 

TODO:
-----

Easier:

- proper configuration script (for downloading and parsing database)
- Improve markdown parsing
- upload to AWS
- About page

More tricky:

- Tidy up code (MVC)
- Make RESTful ("www.rosettaclone.org/Append/Python/Haskell")
- Unit tests
- Make website "responsive" (i.e. javascript) 
- Statistics page


XXX:
----
- Parsing does not handle templates
- Parser confused by "twin" headers (eg =={{header|C}} / {{header|C++}}== )
- Forward slashes in tasks must be removed
- Better initialisation 
