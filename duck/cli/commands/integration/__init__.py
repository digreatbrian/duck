"""
Module containing add-django command class.
"""
import os
import sys
import shutil
import pathlib

from duck.logging import console
from duck.utils.dateutils import gmt_date
from duck.storage import duck_storage


MANAGE_PY_CONTENT = '''
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{django_mainapp_name}.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

'''.lstrip()

EXECUTION_CONFIG_CONTENT = '''
# Execution configuration for Django integration generated on {date}
# This includes basic details regarding the last Django integration.
# {topcomment}

# Name of the Django main/root application
main_app_name = "{django_mainapp_name}"

# Django project path
project_path = "{project_path}"
'''.lstrip()

ASGI_PY_CONTENT = '''
"""
ASGI config for duckapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{django_mainapp_name}.settings")

def get_asgi_application():
    from .old.asgi import application
    return application

application = get_asgi_application()
'''.lstrip()

WSGI_PY_CONTENT = '''
"""
WSGI config for duckapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{django_mainapp_name}.settings")

def get_wsgi_application():
    from .old.wsgi import application
    return application

application = get_wsgi_application()
'''.lstrip()


def ignore_pycache(dir_path, contents):
    """
    Ignore __pycache__ directories during copy.
    """
    # Exclude any __pycache__ directories
    return {
        name
        for name in contents
        if (pathlib.Path(dir_path) / name).is_dir() and name == "__pycache__"
    }


def copy_template_settings_and_urls(settings_py: str, urls_py: str) -> None:
    """
    Copies template settings and URLs files to the given destination paths.

    Args:
        settings_py (str): Destination path for the new settings.py file.
        urls_py (str): Destination path for the new urls.py file.
    """
    current_dir = pathlib.Path(__file__).parent

    source_settings = current_dir / "_django_settings.py"
    source_urls = current_dir / "_django_urls.py"

    shutil.copy(source_settings, settings_py)
    shutil.copy(source_urls, urls_py)


def move_settings_py(src, dest):  
        """  
        Move settings.py to 'old' directory but make some modifications to the destination file.  
        """  
        with open(src, "r") as settings_fd:  
            lines = settings_fd.readlines()  
          
        for line in lines:  
            if line.startswith("BASE_DIR"):  
                # Modify BASE_DIR  
                index = lines.index(line)  
                newline = "BASE_DIR = Path(__file__).resolve().parent.parent.parent"  
                lines[index] = newline  
                break  
          
        # Write modified settings content  
        with open(dest, "w") as fd:  
            fd.write(''.join(lines))  
              
        # Delete source settings  
        os.unlink(src)

        
class DjangoAddCommand:
    # django-add command
    
    @classmethod
    def setup(cls):
        # Setup before command execution
        pass
        
    @classmethod
    def main(
        cls,
        django_project_path: str,
        django_project_mainapp_name: str = None,
        destination_name: str = "duckapp"
    ):
        """
        Integrates an existing Django project into a Duck project.
        
        This method prepares a Django project to work within the Duck framework by extracting
        the main application, copying configuration files, and adapting the project structure.
        
        Args:
            django_project_path (str): Absolute path to the root directory of the existing Django project.
            django_project_mainapp_name (str): Name of the main application within the Django project.
                If None, the name will be inferred from the Django project directory.
            destination_name (str): Name of the destination Duck project. If None, it defaults to
                the name of the Django project directory. Defaults to "duckapp"
        
        Raises:
            FileNotFoundError: If the provided Django project path or main app directory does not exist.
            ValueError: If required files like settings.py or urls.py are missing or malformed.
        """
        cls.setup()
        cls.integrate_django(
            django_project_path,
            django_project_mainapp_name,
            destination_name,
        )
        
    @classmethod
    def integrate_django(
        cls,
        django_project_path: str,
        django_project_mainapp_name: str = None,
        destination_name: str = "duckapp",
     ):
        """
        Integrates an existing Django project into a Duck project.
        
        This method prepares a Django project to work within the Duck framework by extracting
        the main application, copying configuration files, and adapting the project structure.
        
        Args:
            django_project_path (str): Absolute path to the root directory of the existing Django project.
            django_project_mainapp_name (str): Name of the main application within the Django project.
                If None, the name will be inferred from the Django project directory.
            destination_name (str): Name of the destination Duck project. If None, it defaults to
                the name of the Django project directory. Defaults to "duckapp"
        
        Raises:
            FileNotFoundError: If the provided Django project path or main app directory does not exist.
            ValueError: If required files like settings.py or urls.py are missing or malformed.
        """
        # Check if existing Django project already exists in Duck
        from duck.settings import SETTINGS
        
        base_dir = pathlib.Path(str(SETTINGS['BASE_DIR'])).resolve()
        
        # Source settings
        django_project_path = pathlib.Path(django_project_path)
        django_project_mainapp_name = django_project_mainapp_name or django_project_path.name
        django_project_mainapp_dir = django_project_path / django_project_mainapp_name
        
        # Destination settings
        django_destination_name = destination_name or django_project_path.name
        django_destination_path = base_dir / f"backend/django/{django_destination_name}"
        django_destination_mainapp_dir = django_destination_path / django_project_mainapp_name
        django_destination_old_dir = django_destination_mainapp_dir / "old"
        django_destination_manage_py = django_destination_path / "manage.py"
        django_destination_asgi_py = django_destination_mainapp_dir / "asgi.py"
        django_destination_wsgi_py = django_destination_mainapp_dir / "wsgi.py"
        
        console.log("🚀 Starting Django integration process...\n", custom_color=console.Fore.GREEN)

        if not django_project_path.exists():
            console.log_raw(f"❌ Provided Django project path '{django_project_path}' does not exist.", level=console.ERROR)
            return
        
        if not django_project_mainapp_dir.exists():
            console.log_raw(f"❌ Main application directory '{django_project_mainapp_dir}' not found in the provided Django project.", level=console.ERROR)
            return
        
        if django_destination_path.exists():
            console.log_raw(f"⚠️ Destination directory '{django_destination_path}' already exists.\n", level=console.WARNING)
            choice = input("Do you want to overwrite the existing project? [y/N]: ")
            console.log_raw('')  # Print a newline
        
            if not choice.lower().startswith('y'):
                console.log_raw("❗ Django integration cancelled by user.\n", level=console.WARNING)
                return
        
        # Proceed with integration
        console.log(f"📁 Copying Django project to 'backend/django/{django_destination_name}'...\n", level=console.DEBUG)
        
        shutil.copytree(
            django_project_path,
            django_destination_path,
            ignore=ignore_pycache,
            dirs_exist_ok=True
        )
        
        console.log(f"📂 Creating backup directory at '{django_destination_old_dir}'...\n", level=console.DEBUG)
        os.makedirs(str(django_destination_old_dir), exist_ok=True)
        
        console.log("🔄 Backing up original settings.py, asgi.py, wsgi.py, and urls.py to 'old' directory...\n", level=console.DEBUG)
        urls_py = django_destination_mainapp_dir / "urls.py"  
        settings_py = django_destination_mainapp_dir / "settings.py"  
        asgi_py = django_destination_mainapp_dir / "asgi.py"  
        wsgi_py = django_destination_mainapp_dir / "wsgi.py"  
        files = {urls_py, settings_py, asgi_py, wsgi_py}  
        
        # Move or modify config files
        for file in files:
            if file.exists():
                if file.name == "settings.py":
                    console.log(f"✏️ Modifying and moving '{file.name}' to 'old' directory...\n", level=console.DEBUG)
                    move_settings_py(file, django_destination_old_dir / file.name)
                else:
                    console.log(f"📦 Moving '{file.name}' to 'old' directory...\n", level=console.DEBUG)
                    shutil.move(file, django_destination_old_dir / file.name)
            else:
                console.log(f"⚠️ File '{file.name}' not found. Skipping backup.", level=console.WARNING)
        
        console.log("🛠️ Rewriting manage.py, asgi.py, and wsgi.py for integrated Django project...\n", level=console.DEBUG)
        
        with open(django_destination_manage_py, "w") as fd:
            fd.write(MANAGE_PY_CONTENT.format(django_mainapp_name=django_destination_mainapp_dir.name))
        
        with open(django_destination_asgi_py, "w") as fd:
            fd.write(ASGI_PY_CONTENT.format(django_mainapp_name=django_destination_mainapp_dir.name))
        
        with open(django_destination_wsgi_py, "w") as fd:
            fd.write(WSGI_PY_CONTENT.format(django_mainapp_name=django_destination_mainapp_dir.name))
        
        console.log("📝 Writing new settings.py and urls.py files...\n", level=console.DEBUG)
        copy_template_settings_and_urls(settings_py, urls_py)
        
        execution_config_path = django_destination_old_dir / "exec_config.py"
        console.log(f"💾 Saving execution config to '{execution_config_path}'...\n")
        
        with open(execution_config_path, "w") as fd:
            fd.write(
                EXECUTION_CONFIG_CONTENT.format(
                    date=gmt_date(),
                    topcomment=f"Don't forget to set DJANGO_SETTINGS_MODULE to 'backend.django.{django_destination_name}.{django_destination_mainapp_dir.name}.settings' in your Duck settings file.",
                    django_mainapp_name=django_destination_mainapp_dir.name,
                    project_path=os.path.abspath(django_project_path),
                )
            )
        
        init_path = django_destination_old_dir / "__init__.py"
        console.log(f"📄 Creating '__init__.py' at '{init_path}'...\n")
        with open(init_path, "w") as fd:
            fd.write('')
            
        # Final logging after Django integration
        console.log_raw(
            "\n✅ Django integration completed successfully.\n"
            "   Your original 'settings.py' and 'urls.py' have been backed up to the 'old/' directory.\n",
            level=console.INFO,
            custom_color=console.Fore.GREEN,
        )
        
        console.log_raw(
            "🔜️ Next Steps:\n"
            " - In your Duck `settings.py`, set `DJANGO_SIDE_URLS = ['.*']` to route all requests to Django by default.\n"
            " - Optionally, configure `DUCK_EXPLICIT_URLS` with specific URL patterns if you want Duck to handle certain routes.\n",
            level=console.WARNING,
        )
        
        console.log_raw(
            "🚀 To test the integration:\n"
            " - Run the Duck server with the `-dj` flag.\n"
            " - Or, set `USE_DJANGO = True` in your Duck `settings.py`.\n",
            level=console.WARNING,
        )
        
        console.log_raw(
            "🔧 Ensure your Duck `settings.py` includes:\n"
            f" - `DJANGO_SETTINGS_MODULE = 'backend.django.{django_destination_name}.{django_destination_mainapp_dir.name}.settings'`\n"
            " - Verify the copied Django settings file matches your project requirements.\n",
            level=console.WARNING,
        )
        
        console.log(
            "🎉 Django integration complete (100%)!",
            level=console.INFO,
            custom_color=console.Fore.MAGENTA,
        )
        