# Environment specific configuration

By default `gamma-config` only load the YAML files _in the root of the config folder_.
Loading YAML files in subfolders is controlled by the `include_subfolders` entry
in the `config/00-meta.yaml` file.

The meta file generated by the `scaffold` command looks like this:

```yaml
include_folders:
    - !env ENVIRONMENT|None
```

This will load a subfolder named after the `ENVIROMENT` env variable. This allow you
to put you environment specific overrides inside `test`, `prod` however you like.

A sample structure may look like this:

```
config
├── 00-meta.yaml
├── 10-sample.yaml
├── 11-sample-override.yaml
└── prod
    └── 70-sample.yaml
```

## dotenv (.env) support

So called `.env` files are a simple way to provide parameters to your application by
automatically loading environment variables. Combined with the `!env` tag, you directly
load them into your config object.

`gamma-config` will automatically load two files located at the project root, in order
of precedence:

-   `config.local.env`
-   `config.env`

!> We recommend you adding `*.local.*` to your `.gitignore` file

!> With native environment specific support, the need for environment variables in
parameterization is minimized, prefer directly writing YAML config instead.

Secrets and credentials are another thing. Due to their sensitvity, even during
development, you **should never commit credentials to Git repo**! In this particular
case, environment variables can be a simple solution. Make sure to place your local
credentials in the `config.local.env` file to avoid commiting them.