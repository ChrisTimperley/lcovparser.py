# -*- coding: utf-8 -*-
"""Provides a mechanism for parsing LCOV .info files."""
import typing as t

import attr

__version__ = '0.0.1'


@attr.s(auto_attribs=True, slots=True, frozen=True)
class Function:
    name: str
    line: int
    executions: t.Optional[int]


@attr.s(auto_attribs=True, slots=True)
class Record:
    test: t.Optional[str]
    filename: str
    lines: t.Mapping[int, int]
    functions: t.Set[Function]


# http://ltp.sourceforge.net/test/coverage/lcov.readme.php#6
def _parse_line(line: str) -> None:
    # end_of_record

    directive, _, content = line.partition(':')

    # TN:<test name>
    if directive == 'TN':
        test = content

    # SF:<absolute path to the source file>
    elif directive == 'SF':
        filename = content

    # FN:<line number of function start>,<function name>
    elif directive == 'FN':
        args = content.split(',')
        line_no = int(args[0])
        function_name = args[1]

    # DA:<line number>,<execution count>[,<checksum>]
    elif directive == 'DA':
        args = content.split(',')
        line_no = int(args[0])
        num_executions = int(args[1])

    # LH:<number of lines with a non-zero execution count>
    elif directive == 'LH':
        lines_hit = int(content)

    #  LF:<number of instrumented lines>
    elif directive == 'LF':
        raise

    # FNDA:<execution count>,<function name>
