# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import transaction

from pyramid.config import Configurator
from tzf.pyramid_yml import config_defaults

from warehouse.utils.mapper import WarehouseMapper
from warehouse.utils.static import WarehouseCacheBuster


def configure(settings=None):
    if settings is None:
        settings = {}

    config = Configurator(settings=settings)

    # Set our yml.location so that it contains all of our settings files
    config_defaults(config, ["warehouse:etc"])

    # Setup our custom view mapper, this will provide one thing:
    #   * Pass matched items from views in as keyword arguments to the
    #     function.
    config.set_view_mapper(WarehouseMapper)

    # We want to load configuration from YAML files
    config.include("tzf.pyramid_yml")

    # We'll want to use Jinja2 as our template system.
    config.include("pyramid_jinja2")

    # We also want to use Jinja2 for .html templates as well, because we just
    # assume that all templates will be using Jinja.
    config.add_jinja2_renderer(".html")

    # We'll want to configure some filters for Jinja2 as well.
    filters = config.get_settings().setdefault("jinja2.filters", {})
    filters.setdefault("readme", "warehouse.filters:readme_renderer")

    # We also want to register some global functions for Jinja
    jglobals = config.get_settings().setdefault("jinja2.globals", {})
    jglobals.setdefault("gravatar", "warehouse.utils.gravatar:gravatar")

    # We'll store all of our templates in one location, warehouse/templates
    # so we'll go ahead and add that to the Jinja2 search path.
    config.add_jinja2_search_path("warehouse:templates", name=".html")

    # Configure our transaction handling so that each request gets it's own
    # transaction handler and the lifetime of the transaction is tied to the
    # lifetime of the request.
    config.add_settings({
        "tm.manager_hook": lambda request: transaction.TransactionManager(),
    })
    config.include("pyramid_tm")

    # Register support for internationalization and localization
    config.include(".i18n")

    # Register the configuration for the PostgreSQL database.
    config.include(".db")

    # Register our session support
    config.include(".sessions")

    # Register our CSRF support
    config.include(".csrf")

    # Register our authentication support.
    config.include(".accounts")

    # Register all our URL routes for Warehouse.
    config.include(".routes")

    # Enable Warehouse to service our static files
    config.add_static_view(
        name="static",
        path="warehouse:static",
        cachebust=WarehouseCacheBuster(
            "warehouse:static/manifest.json",
            cache=not config.registry.settings["pyramid.reload_assets"],
        ),
    )

    # Scan everything for configuration
    config.scan(ignore=["warehouse.migrations.env"])

    return config
