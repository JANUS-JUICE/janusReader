import rich_click as click
from rich.console import Console
from JanusReader.core import JanusReader, __version__
from pathlib import Path

click.rich_click.TEXT_MARKUP = "rich"

progEpilog = (
    "- For any information or suggestion please contact "
    "[bold magenta][link=mailto:Romolo.Politi@inaf.it]"
    "Romolo.Politi@inaf.it[/link][/bold magenta]"
)
click.rich_click.FOOTER_TEXT = progEpilog
click.rich_click.HEADER_TEXT = f"JANUS Data Reader, version [blue]{__version__}[/blue]"

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "-a", "--all", is_flag=True, help="Print all the informations", default=False
)
@click.version_option(version=__version__)
@click.option("-d", "--debug", is_flag=True, help="Debug mode", default=False)
@click.option(
    "-s",
    "--show-skipped-process",
    "proc",
    is_flag=True,
    help="Show the processing steps",
    default=False,
)
def action(filename, all: bool, debug: bool, proc: bool):
    console = Console()
    filename = Path(filename)
    data = JanusReader(filename, console=console, debug=debug)
    if proc:
        if data.skippedCalibrationSteps:
            console.print(data.skippedCalibrationSteps.Show())
        else:
            if data.fileName.suffix == ".dat":
                console.print("No calibration steps skipped")
            else:
                console.print("[yellow]]Not a calibrated data file[/yellow]")
    else:
        data.Show(all=all)
    pass
