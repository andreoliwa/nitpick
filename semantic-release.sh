#!/usr/bin/env bash
# https://github.com/semantic-release/semantic-release/blob/master/docs/recipes/travis.md
# Use nvm to install and use the Node LTS version (nvm is installed on all Travis images)
nvm install lts/*
npx semantic-release -d
