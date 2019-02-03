# py

This is [@honzajavorek](https://github.com/honzajavorek/)'s experimental playground for the next generation of the [python.cz](https://github.com/pyvec/python.cz/) website.

## Status

[![CircleCI](https://circleci.com/gh/honzajavorek/py/tree/master.svg?style=svg)](https://circleci.com/gh/honzajavorek/py/tree/master) [![Codecov](https://codecov.io/gh/honzajavorek/py/branch/master/graph/badge.svg)](https://codecov.io/gh/honzajavorek/py)

## Fundamental changes

- The [honzajavorek/py](https://github.com/honzajavorek/py) repository is not a direct fork of [pyvec/python.cz](https://github.com/pyvec/python.cz/). It has a common git commit history with it, but several large directories have been nuked:
    - `talks`
    - `files`
    - `identity`
    - `pythoncz/static/talks`
    - `pythoncz/static/photos`
- If anything good comes out of the development, [@honzajavorek](https://github.com/honzajavorek/) will donate the code to the [@pyvec](https://github.com/pyvec/) organization and we can have community talks on whether we want to switch the source for the python.cz domain. As this isn't a fork, there will never be a Pull Request back to [pyvec/python.cz](https://github.com/pyvec/python.cz/).
- The project uses [CircleCI](http://circleci.com/) as it has a lot of features, supports fanning out individual builders, supports crontab syntax in the config, and runs the builds at once without waiting.
- The project uses [Now](https://zeit.co/now) for deployments as it supports redirects and various other features. There is a custom deployment script in the CLI, which once could graduate into an integral part of [Elsa](https://github.com/pyvec/elsa/).
- The project structure is broken down to separate data builders and the website, with the intention to keep maintainable testability, clear interfaces, and to have the simplest code possible. With such separation it's also easy to develop the site locally with only a certain part of the site backed by real data. (Addressing [#279](https://github.com/pyvec/python.cz/issues/279))

## License

[MIT](LICENSE)
