# Environment specific configuration

By default `gamma-config` only loads the YAML files _in the config folder roots_.
Loading YAML files in subfolders is controlled by the meta entry `include_subfolders`.

The default value looks like this.

```yaml
include_folders: !expr env.get('ENVIRONMENT', '').strip().split()
```

This means that _space separated_ names representing subfolders can provided in the
`ENVIRONMENT` variable, and their contents will be loaded and merged. This allow you to
put you environment specific overrides inside `test`, `prod` however you like.

A sample structure may look like this:

```
config
├── 00-meta.yaml
├── 10-sample.yaml
├── 11-sample-override.yaml
└── prod
    └── 70-sample.yaml
```

You may provide your own `00-meta.yaml` file to override the `include_folders`
configuration.

## Environment variables and dotenv (.env) support

With built-in support for environment specific configuration, the need for
environment variables in parameterization should be kept to a minimum.
Prefer directly writing YAML config instead.


That said, so called `.env` files are a simple way to provide parameters to your
application by automatically loading environment variables. Combined with the `!env`
tag, you directly load them into your config object.

`gamma-config` will automatically load these files located at the project root, in this
order:

-   `.env`
-   `config.env` _(deprecated)_
-   `config.local.env` _(deprecated)_

!!! warn
    Existing env vars are not replaced. So system env vars override those in `.env`
    file, and `.env` vars override `config.*` vars.

!!! note
    For consistency with other projects that default to loading `.env` files, we're
    are deprecating support for loading custom `config.env` and `config.local.env`
    environment variables.

### Handling secrets

Secrets and credentials **should never be committed to the Git repo**! In this case,
environment variables can be a simple solution. During development you can place your
credentials in the Git-ignored `.env` file to avoid committing them.
