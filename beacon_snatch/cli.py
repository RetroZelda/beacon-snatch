
import logging
import getpass
import click
import cmd
import os
import re

from . import helpers
from .series import BeaconSeries
from .content import BeaconContent
from .authentication import BeaconAuthentication

LOG_LEVELS = ["DEBUG", "VERBOSE", "INFO", "WARNING", "ERROR", "CRITICAL"]

class BeaconSnatchCLI:
    def __init__(self, cache, output):
        self.cache_dir = os.path.expanduser(cache or helpers.DEFAULT_CACHE)
        self.output_dir = os.path.expanduser(output or helpers.DEFAULT_OUTPUT)
        self.auth = BeaconAuthentication(email=None, password=None, cookies_file=f"{self.cache_dir}/{helpers.COOKIE_NAME}")

        # generally just caching. Should prolly do something better eventually
        self.series_list = None
        self.series_info_cache = {}
        self.content_info_cache = {}

    def authenticate(self):
        if self.auth.IsAuthenticated:
            print(f"Authenticated as: {self.auth.username}")
            return

        self.auth.email = input("Enter your Beacon Email: ").strip()
        self.auth.password = getpass.getpass("Enter your Beacon Password: ").strip()

        self.auth.authenticate(force=True)

    def list_series(self):
        if self.series_list is None:
            self.series_list = BeaconSeries.get_all_series(self.auth)

        for num, series_id in enumerate(self.series_list):
            print(f"{num}) {series_id}")

    def series_info(self, series_id):
        logging.info(f"Fetching information for series {series_id}...")

        series_info = self.series_info_cache.get(series_id)
        if not series_info:
            series_info = BeaconSeries.create(self.auth, series_id)
            if series_info is not None:
                self.series_info_cache[series_id] = series_info

                for content in series_info.content:
                    self.content_info_cache[content.slug] = content

        if series_info:
            print(f"\tid:\n\t\t{series_info.id}")
            print(f"\ttitle:\n\t\t{series_info.title}")
            print(f"\tdescription:\n\t\t{series_info.description}")
            print(f"\tseries_url:\n\t\t{series_info.series_url}")
            print(f"\tcontent count:\n\t\t{len(series_info.content)}")
        else:
            print(f"Invalid series \"{series_id}\".")

    def series_list_content(self, series_id):
        logging.info(f"Fetching information for series {series_id}...")

        series_info = self.series_info_cache.get(series_id)
        if not series_info:
            series_info = BeaconSeries.create(self.auth, series_id)
            if series_info is not None:
                self.series_info_cache[series_id] = series_info

                for content in series_info.content:
                    self.content_info_cache[content.slug] = content

        if series_info:
            print(f"\tcontent_id\t:\tcontent_title")
            for content in series_info.content:
                print(f"\t{content.slug}\t:\t{content.title}")
        else:
            print(f"Invalid series \"{series_id}\".")

    def series_download(self, series_id):
        logging.info(f"Downloading series {series_id}...")
        series_info = self.series_info_cache.get(series_id)
        if not series_info:
            series_info = BeaconSeries.create(self.auth, series_id)
            if series_info is not None:
                self.series_info_cache[series_id] = series_info

                for content in series_info.content:
                    self.content_info_cache[content.slug] = content

        if series_info:
            for content in series_info.content:
                content.download(content.video_and_audio_streams[0], self.output_dir)
        else:
            print(f"Invalid series \"{series_id}\".")

    def content_info(self, content_id):
        logging.info(f"Fetching information for content {content_id}...")

        content_info = self.content_info_cache.get(content_id)
        if not content_info:
            content_info = BeaconContent.create(self.auth, content_id)
            if content_info is not None:
                self.content_info_cache[content_id] = content_info

        if content_info:
            print(f"\tid:\n\t\t{content_info.slug}") # display the slug as the id because whatever
            print(f"\ttitle:\n\t\t{content_info.title}")
            print(f"\tdescription:\n\t\t{re.sub('\n', '\n\t\t', content_info.description)}")
            print(f"\tduration:\n\t\t{content_info.duration}")
            #print(f"\tslug:\n\t\t{content_info.slug}")
            print(f"\tpublishedDate:\n\t\t{content_info.publishedDate}")
        else:
            print(f"Invalid content \"{content_id}\".")


    def content_download(self, content_id):
        logging.info(f"Downloading content {content_id}...")

        content_info = self.content_info_cache.get(content_id)
        if not content_info:
            content_info = BeaconContent.create(self.auth, content_id)
            if content_info is not None:
                self.content_info_cache[content_id] = content_info

        if content_info:
            content_info.download(content_info.video_and_audio_streams[0], self.output_dir)
        else:
            print(f"Invalid content \"{content_id}\".")

    def set_output(self, output_dir):
        logging.info(f"Setting output directory to {output_dir}...")
        helpers.set_output_directory(output_dir)

    def clear_cookies(self):
        self.auth.clear_cookies()
        logging.info("Cookies cleared.")

    def show_info(self):
        print(f"\tAuthenticated as: {self.auth.username}")
        print(f"\tCache Directory:\n\t\t{self.cache_dir}")
        print(f"\tOutput Directory:\n\t\t{self.output_dir}")
    
    def run(self):        
        running = True
        while running:
            user_input = input("> ").strip().lower()
            if not user_input:
                continue  # Skip empty inputs
            
            # Split the input by space
            parts = user_input.split(" ")
            command = parts[0]
            args = parts[1:]  # This will be a list of arguments

            if command == "info":
                self.show_info()
            elif command == "authenticate":
                self.authenticate()
            elif command == "set" and len(parts) > 1 and parts[1] == "output":
                self.set_output(" ".join(args[1:]))  # Pass the arguments as a single string if needed
            elif command == "clear" and len(parts) > 1 and parts[1] == "cookies":
                self.clear_cookies()
            elif command == "help":
                self.display_help()
            elif command == "exit":
                running = False
            else:
                if self.auth is None or not self.auth.IsAuthenticated:
                    print('Not authenticated. Use "help" to know what to do.')
                elif command == "list" and len(parts) > 1 and parts[1] == "series":
                    self.list_series(args)
                elif command == "series" and len(parts) > 1:
                    sub_command = parts[1]
                    if sub_command == "info":
                        self.series_info(args)
                    elif sub_command == "list" and len(parts) > 2 and parts[2] == "content":
                        self.series_list_content(args)
                    elif sub_command == "download":
                        self.series_download(args)
                elif command == "content" and len(parts) > 1:
                    sub_command = parts[1]
                    if sub_command == "info":
                        self.content_info(args)
                    elif sub_command == "download":
                        self.content_download(args)
                else:
                    print(f'Unknown command: {command}. Use "help" to know what to do.')

class InteractiveCLI(cmd.Cmd):
    intro = "Welcome to Beacon Snatch Interactive CLI. Type help to list commands.\n"
    prompt = "(Beacon) > "

    def __init__(self, cli_context):
        super().__init__()
        self.cli_context = cli_context

    def default(self, line):
        try:
            # ensure we dont recursivly handle interactive mode
            parts = line.split()
            filtered_parts = [part for part in parts if part.lower() != "interactive"]
            if len(filtered_parts) > 0:
                result = cli.main(args=filtered_parts, prog_name="beacon_snatch", standalone_mode=False, obj=self.cli_context.obj)
        except SystemExit:
            # Prevent cmd from exiting due to click's SystemExit
            pass
        except Exception as e:
            print(f"Error: {str(e)}")

    def do_help(self, arg):
        """Display the same help text as Click"""
        # Get Click's help text and print it
        click.echo(cli.get_help(self.cli_context))

    def do_exit(self, arg):
        """Exit the CLI"""
        print("Goodbye!")
        return True
    
@click.group()
@click.option("--log-level", default="INFO", type=click.Choice(LOG_LEVELS), help="Set the logging level.")
@click.option("--cache", help="Path to the cache directory. If empty, a default will be used.")
@click.option("--output", help="Path to save downloads. If empty, a default will be used.")
@click.pass_context
def cli(ctx, log_level, cache, output):
    """CLI Interface to Snatch from Beacon"""
    if ctx.obj is None:
        logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
        ctx.obj = BeaconSnatchCLI(cache, output)

@cli.command()
@click.pass_obj
def authenticate(cli):
    """Authenticate with Beacon using your credentials."""
    cli.authenticate()

@cli.command()
@click.pass_obj
def list_series(cli):
    """List all available series on Beacon."""
    cli.list_series()

@cli.command()
@click.argument("series_id")
@click.pass_obj
def series_info(cli, series_id):
    """Get detailed information about a specific series."""
    cli.series_info(series_id)

@cli.command()
@click.argument("series_id")
@click.pass_obj
def series_list_content(cli, series_id):
    """Get basic information for each content in a series."""
    cli.series_list_content(series_id)

@cli.command()
@click.argument("series_id")
@click.pass_obj
def series_download(cli, series_id):
    """Download all content from a specific series."""
    cli.series_download(series_id)

@cli.command()
@click.argument("content_id")
@click.pass_obj
def content_info(cli, content_id):
    """Get detailed information about specific content."""
    cli.content_info(content_id)

@cli.command()
@click.argument("content_id")
@click.pass_obj
def content_download(cli, content_id):
    """Download specific content by content ID."""
    cli.content_download(content_id)

@cli.command()
@click.argument("output_dir")
@click.pass_obj
def set_output(cli, output_dir):
    """Set the directory where downloaded files will be saved."""
    cli.set_output(output_dir)

@cli.command()
@click.pass_obj
def clear_cookies(cli):
    """Clear the stored authentication cookies."""
    cli.clear_cookies()

@cli.command()
@click.pass_obj
def info(cli):
    """View configuration info for the current session."""
    cli.show_info()

@cli.command()
def exit():
    """Exit the CLI interface."""
    click.echo("Goodbye!")
    raise SystemExit(0)

@cli.command()
@click.pass_context
def interactive(ctx):
    """Start the interactive CLI mode."""
    InteractiveCLI(ctx).cmdloop()

def main():
    logging.addLevelName(helpers.LOG_VERBOSE, helpers.LOG_VERBOSE_NAME)
    
    cli()

if __name__ == "__main__":
    main()