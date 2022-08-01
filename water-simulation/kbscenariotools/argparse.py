import argparse


def add_default_args(
    parser: argparse.ArgumentParser, scenario_id=False, trace_id=False
) -> None:
    """Adds the default arguments to the parser (as mentioned in the README.md)"""
    ...
    parser.add_argument(
        "--endpoint",
        help="API endpoint to use with the script",
        type=str,
        action="store",
        default="http://localhost:8000/",
    )
    parser.add_argument(
        "--user",
        help="Provide the user for login at the endpoint",
        type=str,
        action="store",
        default="",
    )
    parser.add_argument(
        "--password",
        help="Provide the password for login at the endpoint",
        type=str,
        action="store",
        default="",
    )
    if scenario_id or trace_id:
        parser.add_argument(
            "--scenario",
            help="ID of the scenario to use",
            type=str,
            action="store",
            required=True,
        )
        if trace_id:
            parser.add_argument(
                "--trace",
                help="ID of the trace to use",
                type=str,
                action="store",
                required=True,
            )
