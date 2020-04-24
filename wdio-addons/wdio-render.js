/* global module, require, process, __dirname, console */
/* jshint globalstrict: true */
'use strict';

const fs = require('fs');
const nj = require('nunjucks');
const baseDir = __dirname;

let path = baseDir + '/' + process.argv[2];
let logPath = process.argv[3] ? (baseDir + '/' + process.argv[3]) : undefined;
let points = 0;
let maxPoints = 0;

if (fs.existsSync(path)) {
  const res = JSON.parse(fs.readFileSync(path, 'utf8'));

  nj.configure(__dirname, { autoescape: true });
  console.log(nj.render('wdio-render.html', res));

  const passes = (test) => (
    test.error === undefined
    && (test.result === undefined || test.result != 'failed')
  );

  const pointsRegex = /.*\((\d+)p?\)$/i;
  const getPoints = (item) => {
    let result = pointsRegex.exec(item.name || item.title);
    return result ? parseInt(result[1]) : undefined;
  }

  res.suites.forEach((suite) => {
    let suitePoints = getPoints(suite);
    let suitePassed = true;
    let testCount = 0;
    let testPassedCount = 0;
    let testPoints = 0;
    let testMaxPoints = 0;

    suite.tests.forEach((test) => {
      let p = getPoints(test) || 0;
      testCount += 1;
      testMaxPoints += p;
      if (passes(test)) {
        testPassedCount += 1;
        testPoints += p;
      } else {
        suitePassed = false;
      }
    });

    if (suitePoints > 0) {
      maxPoints += suitePoints;
      if (testMaxPoints > 0) {
        points += Math.min(testPoints, suitePoints);
      } else {
        points += suitePassed ? suitePoints : 0;
      }
    } else if (testMaxPoints > 0) {
      maxPoints += testMaxPoints;
      points += testPoints;
    } else {
      maxPoints += testCount;
      points += testPassedCount;
    }
  });
} else {
  console.log('<p>Unexpected error while running tests!</p>');
  const logText = (logPath && fs.existsSync(logPath)) ? fs.readFileSync(logPath, 'utf8') : '';
  console.log('<pre>' + logText + '</pre>');
  points = 0;
  maxPoints = 1;
}

console.log(`\nTotalPoints: ${points}\nMaxPoints: ${maxPoints}\n`);
