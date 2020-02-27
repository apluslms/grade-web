Grading environment for web exercises.

Tags
----

The last part of a tag, such as `-3.0` matches the extended grading-base:tag.
There is also few additional versions of the image:

* `wdio-*` includes nodejs, chrome and wdio on top of the base


Utility commands
----------------

In addition to [grading-base](https://github.com/apluslms/grading-base),
this container provides following utilities.

* `wdio/run-wdio-tests`

  Runs an http server in the working directory. Then, executes [wdio](https://webdriver.io/)
  tests from `/exercise/test*.js` that the exercise must provide. The results are
  rendered in HTML and captured for feedback & points.

* `wdio/run-mocha-tests`

  Executes [mocha](https://mochajs.org) tests from `/submission/test*.js`
  (note that you may have to link the necessary tests from /exercise/ before).
  The results are rendered in HTML and captured for feedback & points.

* `import html_checks`

  Import in python3 code. See the code for common static checks related to HTML, CSS and JS.

* `python3 -m html_checks cmd arguments...`

  Simple sanity checks can be run from command line and `sys.exit == 0` communicates success.

  * `js_parse file_name [function function_name]`
