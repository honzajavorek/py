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
- The project uses [CircleCI](http://circleci.com/) as it has a lot of features, supports fanning out individual builders, supports crontab syntax in the config, and runs the builds at once without waiting.
- The project uses [Now](https://zeit.co/now) for deployments as it supports redirects and various other features. There is a custom deployment script in the CLI to pioneer the best way how to automatically deploy to Now - see [pyvec/elsa#61](https://github.com/pyvec/elsa/issues/61).
- The project structure is broken down to separate page builders and the website, with the intention to keep maintainable testability, clear interfaces, and to have the simplest code possible. With such separation it's also easy to develop the site locally with only a certain part of the site backed by real data. (Addressing [#279](https://github.com/pyvec/python.cz/issues/279))
- The main purpose of the python.cz website is now defined as an _aggregator_. It should be a place where all the diversity of the Czech Python community's activities federates and where individual projects can be discovered:

    - python.cz doesn't _contain_ job posts, it _aggregates_ job boards
    - python.cz doesn't _contain_ events, it _aggregates_ events
    - python.cz doesn't _contain_ study materials, it _links_ to them
    - python.cz doesn't _contain_ Czech articles about Python, it _aggregates_ them

## Files structure explained

- `build` - a directory with the static HTML output intended to get deployed
- `pythoncz` - a root Python package of the project
    - `cli` - the CLI implementation
    - `pages` - individual python.cz pages
    - `static` - static files
    - `templates` - templates for the page views
    - `__init__.py` - where the Flask app is instantiated and configured
    - `__main__.py` - where the CLI is instantiated
    - `data.py` - utilities to save and load static data for pages in a uniform way

## Pages

Each package in the `pages` directory is responsible for a single _page_ of the python.cz website. A page is a logical concept. It can include multiple _routes_ as far as their content is backed by the same data. As an example, the `events` page takes care of following routes:

- `/events/`
- `/events.ics`
- `/events.json`

A minimal page can be as simple as having only the `views.py` file with Flask routes (see the `index` page). A complex, data-backed page has several mandatory parts:

1. `__main__.py` - Page builder, which can be ran separately as a script (`pipenv run build events`), produces static, serializable data as an output (`data_events.json`), and uses `pythoncz.data.save_data()` to save them. Builder should contain all dirty side effects: network, filesystem, etc. It stays untested.
1. `views.py` - Routes, which use `pythoncz.data.load_data()` to compose their context for the templates, and which are allowed to contain only presentational logic. They stay untested.
1. `__init__.py` - A library of [pure functions](https://en.wikipedia.org/wiki/Pure_function), which are used by the page builder or the routes to do their job. These functions are supposed to be easy to understand and should be 100% tested.
1. `test_*.py` or `tests/test_*.py` - Tests for the library functions
1. `*_data.json` - Throwaway files of serialized data. Product of the page builders, input for the routes. If they're not present, `pythoncz.data.load_data()` only warns and allows the routes to render with empty data.

When adding new pages, don't forget to import their views at the bottom of the `pythoncz/__init__.py` file. Also don't forget to add the page builder to the CI configuration.

Such structure decouples the process of getting the data from their presentation on the website. It also decouples hard-to-test side effects from the pure testable core, where the business logic is. With the library functions tested by automated unit tests, it's not such a big deal to rely on manual testing of the page builder and visual testing of the website.

The architecture is _inspired_ by:

- [Brandon Rhodes: The Clean Architecture in Python](https://www.youtube.com/watch?v=DJtef410XaM)
- [Gary Bernhardt: Boundaries](https://www.destroyallsoftware.com/talks/boundaries)

## Aggregating pages

What if there's a page which needs data from a different page? If it's only for presentational purposes (`index` displaying latest articles and events), it can `pythoncz.data.load_data()` from various places, no problem. The path to the data file is explicit and not bound to the package where the calling view is.

If the page builder could benefit from seeing other page's data file, then it should restrain from doing so. It's very unlikely two pages will need the _very same_ data. Even if they ask from the same sources, they probably still need different data. Dependenices between page builders ruin the whole thing. With them, you need to pay attention to order of the builders, you cannot run them in parallel on CI, etc. I'd say little redundancy in corner cases isn't bad if it allows for decoupling things. Just let every builder to request their sources and restrain them from looking over the fence to their neighbor's data.

## Tests

There is no `tests` directory. Tests stay with the code to support their discoverability and maintainability of clear boundaries between individual parts of the code.

If one tests file is enough, call it `test_*.py` and put it alongside your code. If you need fixtures or more files, create an _ad-hoc_ `tests` directory and put the `test_*.py` files and fixtures inside.

## CLI

- `pipenv run test` - runs the test suite
- `pipenv run serve` - dynamically serves the Flask website
- `pipenv run build` - builds all pages and the static website
- `pipenv run build events` - builds only data for the 'events' page
- `pipenv run build web` - builds only the static website
- `pipenv run deploy` - deploys contents of the `build` directory to [Now](https://zeit.co/now), aliasing to https://pythoncz.now.sh/
- `pipenv run deploy foo` - deploys contents of the `build` directory to [Now](https://zeit.co/now), aliasing to `https://pythoncz-foo.now.sh/`

## Development workflow

1. Think about what data you're going to need in your views.
1. Prototype a builder for your page. Run it with `pipenv run build <name>` and see what it does. Generate a data file and see what's in it. Do not clutter the data file with anything which isn't valuable for the views! If it's ever needed in the future, somebody will add it.
1. Clean up the builder code to contain only dirty, shell-like, I/O-heavy stuff, and put everything else into pure functions with clear arguments and return values. Put the functions into `__init__.py` and test them.
1. Add views. If they need to reshuffle the data to display them, or to do anything else with them before returning the HTTP response, and it won't fit into one or two lines, extract it as a pure function in `__init__.py` and test it. Your views should be as slim as possible, taking care exclusively of the HTTP mechanics and presentational response rendering.
1. Check whether `pipenv run build <name>` does what you want, whether `pipenv run serve` displays what you want, whether `pipenv run test` passes. If it does, you're done!

## Future

If anything good comes out of the development, [@honzajavorek](https://github.com/honzajavorek/) will donate the code to the [@pyvec](https://github.com/pyvec/) organization and we can have community talks on whether we want to switch the source for the python.cz domain. As this isn't a clean fork, there will never be a Pull Request back to [pyvec/python.cz](https://github.com/pyvec/python.cz/).

## License

[MIT](LICENSE)
