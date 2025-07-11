from .home import ducksite_home_view # noqa: F401
from .about import ducksite_about_view # noqa: F401
from .contact import ducksite_contact_view # noqa: F401
from .static import ducksite_staticfiles_view # noqa: F401
from .speedtest import ducksite_speedtest_view # noqa: F401


__all__ = [
    "ducksite_home_view",
    "ducksite_about_view",
    "ducksite_contact_view",
    "ducksite_staticfiles_view",
    "ducksite_speedtest_view",
]
