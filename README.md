datawire-cli -- the Datawire Cloud CLI
======================================

This repo contains `dwc`, the command-line interface to the Datawire Cloud. You can use `dwc` to create a new organization, log in to an existing organization, create service tokens, etc. 

Installing as a User
--------------------

To install as an end user, use:

```curl -L https://raw.githubusercontent.com/datawire/datawire-cli/master/install.sh | bash -s --```

and stand back! You should get a nice clean install of the latest and greatest.

To get started:

- `dwc -h` will give help.
- `dwc create-organization` will create a new organization for you.
- `dwc create-service` will create a service token for you.

You can find more in the `examples` folder in the `datawire-connect` repo, at

```https://github.com/datawire/datawire-connect```

Building
--------

Type `make` and stand back: we'll try to get everything rolling and build you a `dwc` locally, but if something goes wrong, we'll try to tell you how to fix it.
