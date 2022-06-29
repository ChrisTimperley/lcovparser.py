# -*- coding: utf-8 -*-
"""Provides a mechanism for parsing LCOV .info files."""
from __future__ import annotations

import typing as t

import attr

__version__ = '0.0.1'


@attr.s(auto_attribs=True, slots=True)
class Function:
    """Provides coverage information for a function."""
    name: str
    line: int
    executions: t.Optional[int] = attr.ib(default=None)


@attr.s(auto_attribs=True, slots=True)
class Record:
    """Provides coverage information for a source file."""
    filename: str
    test: t.Optional[str] = attr.ib(default=None)
    lines: t.MutableMapping[int, int] = attr.ib(factory=dict)
    functions: t.MutableMapping[str, Function] = attr.ib(factory=dict)

    def add_function(self, function: Function) -> None:
        """Add a function to this record."""
        if function.name in self.functions:
            raise ValueError(
                f"function already contained in record: {function.name}",
            )
        self.functions[function.name] = function


@attr.s(auto_attribs=True, slots=True)
class Report(t.Mapping[str, Record]):
    """Report provides coverage information from an lcov report."""
    _filename_to_record: t.Mapping[str, Record]

    def __getitem__(self, filename: str) -> Record:
        return self._filename_to_record[filename]

    def __iter__(self) -> t.Iterator[str]:
        yield from self._filename_to_record

    def __len__(self) -> int:
        return len(self._filename_to_record)

    @classmethod
    def build(cls, records: t.Collection[Record]) -> Report:
        """Construct a report from a collection of records."""
        filename_to_record = {record.filename: record for record in records}
        return Report(filename_to_record)


def parse_file(
    filename: str,
    *,
    ignore_incorrect_counts: bool = False,
) -> Report:
    """Parse a given lcov file."""
    with open(filename, "r") as fh:
        contents = fh.read()
    return parse_text(contents, ignore_incorrect_counts=ignore_incorrect_counts)


def parse_text(
    contents: str,
    *,
    ignore_incorrect_counts: bool = False,
) -> Report:
    """Parse the text contents of an lcov file."""
    return parse_lines(contents.splitlines(), ignore_incorrect_counts=ignore_incorrect_counts)


def parse_lines(
    lines: t.List[str],
    *,
    ignore_incorrect_counts: bool = False,
) -> Report:
    """Parse the lines of an lcov file."""
    records: t.List[Record] = []
    line_iterator: t.Iterator[str] = iter(lines)
    while True:
        maybe_next_record = _parse_next_record(line_iterator, ignore_incorrect_counts=ignore_incorrect_counts)
        if maybe_next_record:
            records.append(maybe_next_record)
        else:
            break
    return Report.build(records)


def _parse_next_record(
    lines: t.Iterator[str],
    *,
    ignore_incorrect_counts: bool = False,
) -> t.Optional[Record]:
    # http://ltp.sourceforge.net/test/coverage/lcov.readme.php#6
    # are there no more records in this file?
    try:
        line = next(lines)
    except StopIteration:
        return None

    # SF:<absolute path to the source file>
    directive, _, content = line.strip().partition(':')
    if directive != "SF":
        raise ValueError(f"expected record to begin with SF (actual: {line})")
    record = Record(filename=content)

    # parse each line until we reach the end of the record
    for line in lines:
        line = line.strip()

        if line == "end_of_record":
            return record

        directive, _, content = line.partition(':')

        # TN:<test name>
        if directive == "TN":
            record.test = content

        # FNF:<number of functions instrumented>
        elif directive == "FNF" and not ignore_incorrect_counts:
            expected_functions_instrumented = int(content)
            actual_functions_instrumented = len(record.functions)
            if expected_functions_instrumented != actual_functions_instrumented:
                raise ValueError(
                    f"unexpected FNF count (actual: {actual_functions_instrumented}; "
                    f"expected: {expected_functions_instrumented})",
                )

        # FNH:<number of functions executed in current record>
        elif directive == "FNH" and not ignore_incorrect_counts:
            expected_functions_executed = int(content)
            actual_functions_executed = sum(
                1 for function in record.functions.values() if function.executions and function.executions > 0
            )
            if expected_functions_executed != actual_functions_executed:
                raise ValueError(
                    f"unexpected FNH count (actual: {actual_functions_executed}; "
                    f"expected: {expected_functions_executed})",
                )

        # FN:<line number of function start>,<function name>
        elif directive == 'FN':
            args = content.split(',')
            assert len(args) == 2
            function = Function(name=args[1], line=int(args[0]))
            record.add_function(function)

        # FNDA:<execution count>,<function name>
        elif directive == "FNDA":
            args = content.split(',')
            assert len(args) == 2
            record.functions[args[1]].executions = int(args[0])

        # LH:<number of lines with a non-zero execution count>
        elif directive == "LH" and not ignore_incorrect_counts:
            expected_lines_hit = int(content)
            actual_lines_hit = sum(1 for count in record.lines.values() if count > 0)
            if expected_lines_hit != actual_lines_hit:
                raise ValueError(
                    f"unexpected LH count (actual: {actual_lines_hit}; "
                    f"expected: {expected_lines_hit})",
                )

        # LF:<number of instrumented lines>
        elif directive == "LF" and not ignore_incorrect_counts:
            expected_lines_instrumented = int(content)
            actual_lines_instrumented = len(record.lines)
            if expected_lines_instrumented != actual_lines_instrumented:
                raise ValueError(
                    f"unexpected LF count (actual: {actual_lines_instrumented}; "
                    f"expected: {expected_lines_instrumented})",
                )

        # DA:<line number>,<execution count>[,<checksum>]
        elif directive == 'DA':
            args = content.split(',')
            assert len(args) > 1 and len(args) < 3
            line_no = int(args[0])
            num_executions = int(args[1])
            if line_no in record.lines:
                raise ValueError(f"duplicate DA entry for line: {line_no}")
            record.lines[line_no] = num_executions

        else:
            raise ValueError(f"failed to parse line in record: {line}")

    return record
