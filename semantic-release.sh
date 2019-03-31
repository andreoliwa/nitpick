#!/usr/bin/env bash
# https://github.com/semantic-release/semantic-release/blob/master/docs/recipes/travis.md
npm install -g @semantic-release/changelog @semantic-release/git @semantic-release/exec
npx semantic-release -d
