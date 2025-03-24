#!/usr/bin/env python
"""
Main entry to Duck command-line tool.
"""
import sys
import click
import os

from duck.version import server_version
from duck.logging import console
from duck.art import duck_art_small

from duck.cli.commands.collectstatic import CollectStaticCommand
from duck.cli.commands.collectscripts import CollectScriptsCommand
from duck.cli.commands.makeproject import MakeProjectCommand
from duck.cli.commands.makeblueprint import MakeBlueprintCommand
from duck.cli.commands.django import DjangoCommand
from duck.cli.commands.runserver import RunserverCommand
from duck.cli.commands.runtests import RuntestsCommand
from duck.cli.commands.ssl_gen import SSLGenCommand


EXAMPLES = f"""
Examples:
    python -m duck runserver -a 127.0.0.1 -p 8000
    python -m duck makeproject myproject -d ./projects
    python -m duck ssl-gen
    python -m duck django migrate
    python -m duck collectstatic
    python -m duck collectscripts
    
{console.Fore.YELLOW}Commands requiring execution inside the project directory
or with DUCK_SETTINGS_MODULE set: {console.Style.RESET_ALL}
   
   duck collectstatic ...
   duck collectscripts ...
   duck django ...
   duck ssl-gen ...
   duck runserver ... (Use --file or --settings to bypass this requirement)

"""

@click.group(invoke_without_command=True)
@click.option('-V', '--version', is_flag=True, help="Show the version and exit.")
@click.pass_context
def cli(ctx, version):
    """
    Duck CLI - Manage your projects with ease.
    """
    # Add current directory to python path
    curdir = os.path.abspath('.')
    sys.path.insert(0, curdir)
    
    if version:
        # Show the version
        click.echo(server_version)
    elif not ctx.invoked_subcommand:
        # Print usage if no subcommands are invoked
        click.echo(click.style(duck_art_small, fg='green', bold=True))
        click.echo(ctx.get_help())
        click.echo(EXAMPLES)


@cli.command()
@click.option('--skip-confirmation', is_flag=True, default=False, help="Skip confirmation prompts")
def collectstatic(skip_confirmation):
    """Collect static files from blueprint directories."""
    CollectStaticCommand.main(skip_confirmation)


@cli.command()
@click.option('--skip-confirmation', is_flag=True, default=False, help="Skip confirmation prompts")
def collectscripts(skip_confirmation):
    """Collect React scripts for the frontend."""
    CollectScriptsCommand.main(skip_confirmation)


@cli.command(help="Create a Duck project")
@click.argument("name")
@click.option("-d", "--dest", default=".", help="The destination directory to place the project (default: current directory)")
@click.option("-O", "--overwrite", is_flag=True, help="Overwrite an existing project.")
@click.option('--mini', 'project_type', flag_value="mini", help="Create project with minimum files and configuration")
@click.option('--full', 'project_type', flag_value="full", help="Create project with complete files and configuration.")
@click.option('--project_type', default='normal', type=click.Choice(["normal", "full", "mini"]), help="Specify project type")
def makeproject(name, dest, overwrite, project_type):
    """Create a new project whether it's a normal, full or a mini project."""
    MakeProjectCommand.main(name, dest_dir=dest, overwrite_existing=overwrite, project_type=project_type)


@cli.command(help="Create a Duck blueprint directory structure")
@click.argument("name")
@click.option("-d", "--dest", help="Destination for blueprint creation.")
@click.option("-O", "--overwrite", is_flag=True, help="Overwrite an existing blueprint.")
def makeblueprint(name, dest, overwrite):
   """
   Create a new Blueprint for organizing routes, similar to Flask's Blueprint system.
   """
   MakeBlueprintCommand.main(name, destination=dest, overwrite_existing=overwrite)


@cli.command(help="Execute Django management commands for your project")
@click.argument('args', nargs=-1)  # Accept multiple arguments
def django(args):
    """Run Django-related commands in your project."""
    DjangoCommand.main()


@cli.command(help="Start the development/production server")
@click.option("-a","--address", default="0.0.0.0", help="The address to bind the server to (default: 0.0.0.0)")
@click.option("-p", "--port", type=int, default=8000, help="The port to listen on (default: 8000)")
@click.option( "-d", "--domain", default=None, help="The domain name for the server (optional)")
@click.option("-s", "--settings", default=None, help="The settings module to use (optional)")
@click.option("-f", "--file", default=None, help="The main python file containing app instance (optional)")
@click.option("--ipv6", is_flag=True, default=False, help="Run application using IPV6 (optional)")
@click.option("--reload", is_flag=True, default=False, help="Run application in reload state. Application will run as if it was restarted (optional)")
@click.option("-dj", "--use-django", is_flag=True, default=False, help="Run application along with Django server. This overrides setting USE_DJANGO in settings.py (optional)")
def runserver(address, port, domain, settings, ipv6, file, reload, use_django):
    """Run the development or production server."""
    if use_django:
        os.environ.setdefault("DUCK_USE_DJANGO", "true")
        
    RunserverCommand.main(
        address=address,
        port=port,
        domain=domain,
        settings_module=settings,
        mainfile=file,
        uses_ipv6=ipv6,
        reload=reload)


@cli.command(help="Run default tests using unittest module")
def runtests():
    """Run pre-built Duck tests."""
    RuntestsCommand.main()


@cli.command(help="Generate a self-signed SSL certificate")
def ssl_gen():
    """Generate self-signed SSL certificate."""
    SSLGenCommand.main()


if __name__ == "__main__":
    cli()