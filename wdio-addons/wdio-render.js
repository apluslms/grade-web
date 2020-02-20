/* global module, require, __dirname, console */
/* jshint globalstrict: true */
'use strict';

const fs = require('fs');
const nj = require('nunjucks');
const baseDir = __dirname;

const res = JSON.parse(fs.readFileSync(__dirname + '/wdio-0-0-json-reporter.log', 'utf8'));

nj.configure(__dirname, { autoescape: true });
console.log(nj.render('wdio-render.html', res));

const counter = (sum, test) => sum + 1;
const maxPoints = res.suites.reduce((s, suite) => s + suite.tests.reduce(counter, 0), 0);
const points = res.suites.reduce((s, suite) => s + suite.tests.filter((test) => test.error === undefined).reduce(counter, 0), 0);
console.log(`\nTotalPoints: ${points}\nMaxPoints: ${maxPoints}\n`);
