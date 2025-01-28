#!/usr/bin/env python
"""
Main entry to Duck command-line tool.
"""
import os
import sys
import argparse
import subprocess
from functools import partial

from duck.cli.commands.extra import (
    CollectStaticCommand,
    CollectScriptsCommand,
    MakeBlueprintCommand,
)


EXAMPLES = """
Examples:
    python -m duck runserver -a 127.0.0.1 -p 8000
    python -m duck makeproject myproject -d ./projects
    python -m duck ssl-gen
    python -m duck django migrate
    python -m duck collectstatic
"""

def create_temp_settings_py(_dir: str = "."):
    """
    Creates temporary empty settings.py file.
    """
    file = os.path.join(_dir, "settings.py")
    if not os.path.isfile(file):
        with open(file, "a"):
            pass


def remove_temp_settings_py(_dir: str = "."):
    """
    Removes temporary empty settings.py file.
    """
    file = os.path.join(_dir, "settings.py")
    if os.path.isfile(file):
        with open(file, "r") as fd:
            if not fd.read():
                os.unlink(file)  # remove file if empty.


def run_sub_command(command):
    """
    Runs the command as a child process using subprocess.call
    """
    try:
        subprocess.call(command, start_new_session=True)
    except KeyboardInterrupt:
        pass


def runserver(parsed_args: argparse.Namespace) -> None:
    """
    Starts the Duck production or development server.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments from the command line.

    Notes:
        - If the file argument is provided and args like domain, port and address are also provided, an error is raised.
    """
    settings_module = parsed_args.settings

    if settings_module:
        os.environ["DUCK_SETTINGS_MODULE"] = settings_module

    from duck.app import (
        App,  # Import after DUCK_SETTINGS_MODULE is set to avoid errors.
    )

    address = (parsed_args.address
               or "0.0.0.0")  # Default to "0.0.0.0" if not provided
    port = parsed_args.port or 8000  # Default to port 8000 if not provided
    domain = (parsed_args.domain
              or "localhost")  # Default to None if not provided
    uses_ipv6 = parsed_args.ipv6
    main_py = parsed_args.file

    if main_py:
        # file containing app instance provided
        if not main_py.endswith(".py"):
            raise TypeError(
                "File provided as the main python file has invalid extension, should be a .py file."
            )

        if not os.path.isfile(main_py):
            raise FileNotFoundError(
                "Main python file which the app resides not found.")

        assert (
            not parsed_args.address and not parsed_args.port
            and not parsed_args.domain
        ), "Cannot explicitly provide address, port and domain if --file argument is present."
        command = ["python", main_py]
        command.extend(["--reload"]) if "--reload" in sys.argv else None
        run_sub_command(command)  # run command as child process
    else:
        application = App(
            addr=address,
            port=port,
            domain=domain,
            uses_ipv6=True if uses_ipv6 else False,
        )
        application.run(
        )  # if --reload arg in sys.argv, app will be restarted nomatter if run was called instead.


def makeproject(parsed_args: argparse.Namespace) -> None:
    """
    Creates a new Duck project structure.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments from the command line.
    """
    create_temp_settings_py(
    )  # create temp settings file to avoid SettingsError. (if necessary)

    from duck.logging import console
    from duck.setup.makeproject import makeproject
    
    name = parsed_args.args[0]
    destination_dir = parsed_args.dest or "."
    destination_dir = os.path.abspath(destination_dir)
    overwrite = parsed_args.overwrite
    mini = parsed_args.mini
    full = parsed_args.full
    project_type = "normal"

    if bool(mini):
        project_type = "mini"

    if bool(full):
        project_type = "full"

    console.log(
        f'Creating Duck {project_type.title()} Project' if project_type != "normal"
        else f'Creating Duck Project',
        level=console.DEBUG,
    )

    try:
        makeproject(
            name,
            destination_dir,
            overwrite_existing=bool(overwrite),
            project_type=project_type,
        )  # create project
        
        # Log something to the console
        console.log(
            f'Project "{name}" created in directory "{destination_dir}"',
            custom_color=console.Fore.GREEN,
        )
    except FileExistsError:
        console.log(
            f'Project with name "{name}" already exists in destination directory: {destination_dir}',
            level=console.WARNING,
        )
        overwrite = input(
            "\nDo you wish to overwrite the existing project (y/N): ")

        print()

        if overwrite.lower().startswith("y"):
            makeproject(name,
                        destination_dir,
                        overwrite_existing=True,
                        project_type=project_type)
            console.log(
                f'Project "{name}" created in directory "{destination_dir}"',
                custom_color=console.Fore.GREEN,
            )
        else:
            console.log("Cancelled project creation!", level=console.DEBUG)

    except Exception as e:
        console.log(f"Error: {str(e)}", level=console.ERROR)
        raise e

    finally:
        remove_temp_settings_py(
        )  # remove temp settings.py if it has been created in the first place.


def ssl_gen(parsed_args: argparse.Namespace) -> None:
    """
    Generates self-signed SSL certificates.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments from the command line.
    """
    from duck.logging import console
    from duck.utils.ssl import generate_server_cert

    try:
        generate_server_cert()
    except Exception as e:
        console.log(f"Error: {str(e)}", level=console.ERROR)
        sys.exit(2)


def django_command(parsed_args: argparse.Namespace) -> None:
    """
    Executes Django management commands.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments from the command line.
    """
    from duck.backend.django.bridge import DUCK_APP_MODULE
    from duck.settings import SETTINGS
    from duck.utils.path import joinpaths

    python_path = SETTINGS["PYTHON_PATH"]
    django_app_home = DUCK_APP_MODULE.__path__[0]

    command = [python_path, joinpaths(django_app_home, "manage.py")]
    command_args = parsed_args.args
    command.extend(command_args)
    subprocess.call(command)


def runtests(parsed_args: argparse.Namespace) -> None:
    """
    Runs Duck default tests using unittest module.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments from the command line.
    """
    from duck.storage import duck_storage

    python_path = "python"
    tests_dir = os.path.join(duck_storage, "tests")
    subprocess.call([
        python_path,
        "-m",
        "unittest",
        "discover",
        "-s",
        tests_dir,
        "-p",
        "test_*.py",
        "-t",
        tests_dir,
    ])


def subcommand_error_handler(parser, error_message):
    """
    Custom error handler to print subcommand usage and error messages.

    Args:
        parser (argparse.ArgumentParser): The argument parser for the subcommand.
        error_message (str): The error message to display.
    """
    sys.stderr.write(f"\nError: {error_message}\n")
    sys.exit(2)


def main() -> None:
    """
    Entry point for the Duck command-line tool.
    """
    parser = argparse.ArgumentParser(
        prog="duck",
        description="Duck command-line tool",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show the current Duck version.",
    )
    
    # Disable default help and usage
    subparsers = parser.add_subparsers(dest="subcommand", help="Available sub-commands")
    
    def main_command(parsed_args: argparse.Namespace) -> None:
        """
        Runs default main Duck command.

        Args:
            parsed_args (argparse.Namespace): Parsed arguments from the command line.
        """
        if parsed_args.version:
            from duck.version import server_version
            print(server_version)
        else:
            parser.print_help()
            print(EXAMPLES)

    parser.set_defaults(func=main_command)
    parser.error = partial(subcommand_error_handler, parser)
    
    # Runserver subcommand
    runserver_parser = subparsers.add_parser(
        "runserver",
        help="Start the development/production server"
    )
    runserver_parser.add_argument(
        "-a",
        "--address",
        help="The address to bind the server to (default: 0.0.0.0)",
    )
    runserver_parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="The port to listen on (default: 8000)")
    runserver_parser.add_argument(
        "-d",
        "--domain",
        help="The domain name for the server (optional)",
     )
    runserver_parser.add_argument(
        "-s",
        "--settings",
        help="The settings module to use (optional)",
     )
    runserver_parser.add_argument(
        "-f",
        "--file",
        help="The main py file containing app instance (optional)",
    )
    runserver_parser.add_argument(
        "--ipv6",
        help="Run application using IPV6 (optional)",
        action="store_true",
    )
    runserver_parser.add_argument(
        "--reload",
        help="Run application in reload state. App will run as if it was restarted (optional)",
        action="store_true",
    )
    runserver_parser.set_defaults(func=runserver)
    runserver_parser.error = partial(subcommand_error_handler, runserver_parser)

    # Make project subcommand
    makeproject_parser = subparsers.add_parser(
        "makeproject",
        help="Create a Duck project",
    )
    makeproject_parser.add_argument(
        "args",
        nargs=1,
        help="The name of the project to create.",
    )
    makeproject_parser.add_argument(
        "-d",
        "--dest",
        help="The destination directory to place the project (default: current directory).",
    )
    makeproject_parser.add_argument(
        "-O",
        "--overwrite",
        action="store_true",
        help="Overwrite an existing project.",
    )
    makeproject_parser.add_argument(
        "--mini",
        help="Create project with minimum files and configuration.",
        action="store_true",
    )
    makeproject_parser.add_argument(
        "--full",
        help="Create project with complete files and configuration.",
        action="store_true",
    )
    makeproject_parser.set_defaults(func=makeproject)
    makeproject_parser.error = partial(subcommand_error_handler, makeproject_parser)
    
    # Make blueprint subcommand
    makeblueprint_parser = subparsers.add_parser(
        "makeblueprint",
        help="Create a Duck blueprint directory structure",
    )
    makeblueprint_parser.add_argument(
        "args",
        nargs=1,
        help="The name of the blueprint to create.",
    )
    makeblueprint_parser.add_argument(
        "-d",
        "--dest",
        help="The destination directory to place the blueprint (default: current directory).",
    )
    makeblueprint_parser.add_argument(
        "-O",
        "--overwrite",
        action="store_true",
        help="Overwrite an existing blueprint.",
    )
    makeblueprint_parser.set_defaults(func=MakeBlueprintCommand.main)
    makeblueprint_parser.error = partial(subcommand_error_handler, makeblueprint_parser)
    
    # SSL generation subcommand
    ssl_gen_parser = subparsers.add_parser(
        "ssl-gen",
        help="Generate a self-signed SSL certificate",
    )
    ssl_gen_parser.set_defaults(func=ssl_gen)
    ssl_gen_parser.error = partial(subcommand_error_handler, ssl_gen_parser)

    # Django subcommand
    django_parser = subparsers.add_parser(
        "django",
        help="Execute Django management commands",
    )
    django_parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the Django management command",
    )
    django_parser.set_defaults(func=django_command)
    django_parser.error = partial(subcommand_error_handler, django_parser)

    # Collectstatic subcommand
    collectstatic_parser = subparsers.add_parser(
        "collectstatic",
        help="Collect all static files from blueprint base directories.",
    )
    collectstatic_parser.add_argument(
        "-y",
        "--skip-confirmation",
        action="store_true",
        help="Skip confirmation inputs.",
    )
    collectstatic_parser.set_defaults(func=CollectStaticCommand.main)
    collectstatic_parser.error = partial(subcommand_error_handler, collectstatic_parser)
    
    # Collectscripts subcommand
    collectscripts_parser = subparsers.add_parser(
        "collectscripts",
        help="Collect all frontend scripts to appropriate destination.",
    )
    collectscripts_parser.add_argument(
        "-y",
        "--skip-confirmation",
        action="store_true",
        help="Skip confirmation inputs.",
    )
    collectscripts_parser.set_defaults(func=CollectScriptsCommand.main)
    collectscripts_parser.error = partial(subcommand_error_handler, collectscripts_parser,)

    # Runtests subcommand
    runtests_parser = subparsers.add_parser(
        "runtests",
        help="Run default tests using unittest module",
     )
    runtests_parser.set_defaults(func=runtests)
    runtests_parser.error = partial(subcommand_error_handler, runtests_parser)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
