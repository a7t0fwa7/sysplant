#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
import argparse

from sysplant.utils.loggerSingleton import LoggerSingleton
from sysplant.constants import DESC_HEADER, FANCY_HEADER
from sysplant.generator import Generator

if __name__ == "__main__":
    # Set default level
    log_level = logging.INFO

    # Init logger Singleton
    logger = LoggerSingleton(log_level)

    parser = argparse.ArgumentParser(description=DESC_HEADER)

    # Verbose choice
    shout_level = parser.add_mutually_exclusive_group()
    shout_level.add_argument(
        "--debug", action="store_true", help="Display all DEBUG messages upon execution"
    )
    shout_level.add_argument(
        "--verbose",
        action="store_true",
        help="Display all INFO messages upon execution",
    )
    shout_level.add_argument(
        "--quiet",
        action="store_true",
        help="Remove all messages upon execution",
    )

    parser.add_argument(
        "-i",
        "--iterator",
        help="Select syscall iterator (Default: canterlot)",
        choices=["freshy", "heaven", "hell", "halos", "tartarus", "canterlot"],
        default="canterlot",
    )
    parser.add_argument(
        "-r",
        "--resolver",
        help="Select syscall resolver (Default: random)",
        choices=["basic", "random"],
        default="random",
    )
    parser.add_argument(
        "-s",
        "--stub",
        help="Select syscall stub (Default: indirect)",
        choices=["direct", "indirect"],
        default="indirect",
    )

    syscalls = parser.add_mutually_exclusive_group()
    syscalls.add_argument(
        "-p",
        "--preset",
        help='Preset functions ("all", "donut", "common")',
        choices=["all", "donut", "common"],
        required=False,
    )
    syscalls.add_argument(
        "-f", "--functions", help="Comma-separated functions", required=False
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path for NIM generated file",
        required=True,
    )

    args = parser.parse_args()

    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    if args.quiet:
        log_level = logging.CRITICAL

    # Update log level if necessary
    logger.log_level = log_level

    logger.info(FANCY_HEADER, stripped=True)

    try:
        # Set syscall to generate
        if args.preset:
            args.syscalls = args.preset
        elif args.functions:
            args.syscalls = args.functions.split(",")
        else:
            raise ValueError(
                "Please specify which function to evade using --preset or --functions"
            )

        engine = Generator()
        engine.generate(
            iterator=args.iterator,
            resolver=args.resolver,
            stub=args.stub,
            syscalls=args.syscalls,
            output=args.output,
        )
    except Exception as err:
        logger.critical(err)
