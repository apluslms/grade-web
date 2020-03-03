/* global module, require, process, __dirname, console */
/* jshint globalstrict: true */
'use strict';

const fs = require('fs');
const nj = require('nunjucks');
const baseDir = __dirname;

const res = JSON.parse(fs.readFileSync(__dirname + '/' + process.argv[2], 'utf8'));

nj.configure(__dirname, { autoescape: true });
console.log(nj.render('wdio-render.html', res));

const counter = (sum, test) => sum + 1;
const isOk = (test) => (
  test.error === undefined
  && (test.result === undefined || test.result == 'success')
);
const maxPoints = res.suites.reduce(
  (s, suite) => s + suite.tests.reduce(counter, 0),
  0
);
const points = res.suites.reduce(
  (s, suite) => s + suite.tests.filter(isOk).reduce(counter, 0),
  0
);
console.log(`\nTotalPoints: ${points}\nMaxPoints: ${maxPoints}\n`);
