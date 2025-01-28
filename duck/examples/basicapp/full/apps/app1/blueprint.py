"""
Module for route arrangements using RouteBlueprint. This acts as a set of routes, much like how Flask's blueprints organize routes in a module.

Example:
	Products = RouteBlueprint(name="products", urlpatterns=...)

Notes:
    - Make sure include this blueprint in settings like so:
    
    # settings.py
    
    ROUTE_BLUEPRINTS = [
        "apps.app1.blueprint.Products"
        # other blueprints here
    ]
"""
