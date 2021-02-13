# -*- coding: utf-8 -*-
"""Provides a mechanism for parsing LCOV .info files."""
import typing as t
import sys
import attr

__version__ = '0.0.1'


@attr.s(auto_attribs=True, slots=True)
class Function:
    name: str
    line: int
    executions: int = 0


@attr.s(auto_attribs=True, slots=True, frozen=True)
class Branch:
    block_number: int
    branch_number: int
    line: int
    executions: t.Optional[int]


@attr.s(auto_attribs=True, slots=True)
class Totals:
    total_functions: int = 0
    hit_functions: int = 0
    total_branches: int = 0
    hit_branches: int = 0
    total_lines: int = 0
    hit_lines: int = 0


@attr.s(auto_attribs=True, slots=True, repr=False)
class Record:
    test: t.Optional[str] = ''
    filename: str = ''
    lines: t.Mapping[int, int] = attr.Factory(dict)
    functions: t.Mapping[str, Function] = attr.Factory(dict)
    branches: t.Set[Branch] = attr.Factory(set)
    totals: Totals = Totals()

    def __repr__(self) -> str:
        s = f"Filename: {self.filename}, "

        ts = self.totals
        s += "Line coverage %.2f%%, Function coverage %.2f%%, Branch coverage %.2f%%" \
                %    (float(ts.hit_lines)*100/float(ts.total_lines),
                     float(ts.hit_functions)*100/float(ts.total_functions),
                     float(ts.hit_branches)*100/float(ts.total_branches))
        return s


# http://ltp.sourceforge.net/test/coverage/lcov.readme.php#6
# http://ltp.sourceforge.net/coverage/lcov/geninfo.1.php
def _parse_line(line: str, record: t.Optional[Record] = None
               ) -> t.Tuple[t.Optional[Record], bool]:
    """
    accepts a record currently under process, and returns
    the updated record and whether at the end of the record.
    """

    line = line.strip()

    # end_of_record
    if line == "end_of_record":
        return record, True

    if not record:
        record = Record()

    print(line)
    partitions = line.split(':')
    assert len(partitions) >= 2
    directive = partitions[0]
    content = ''.join(partitions[1:])

    # TN:<test name>
    if directive == 'TN':
        record.test = content

    # SF:<absolute path to the source file>
    elif directive == 'SF':
        record.filename = content

    # FN:<line number of function start>,<function name>
    elif directive == 'FN':
        args = content.split(',')
        line_no = int(args[0])
        function_name = args[1]
        function = Function(function_name, line_no)
        record.functions[function_name] = function

    # FNDA:<execution count>,<function name>
    elif directive == 'FNDA':
        args = content.split(',')
        execution_no = int(args[0])
        function_name = args[1]
        record.functions[function_name].executions = execution_no

    # FNF:<number of functions found>
    elif directive == "FNF":
        record.totals.total_functions = int(content)
    
    # FNH:<number of function hit>
    elif directive == "FNH":
        record.totals.hit_functions = int(content)

    # BRDA:<line number>,<block number>,<branch number>,<taken>
    elif directive == "BRDA":
        args = content.split(',')
        assert len(args) == 4
        line_no = int(args[0])
        block_no = int(args[1])
        branch_no = int(args[2])
        taken = None if args[3] == '-' else int(args[3])
        record.branches.add(Branch(block_no, branch_no, line_no, taken))

    # BRF:<number of branches found>
    elif directive == "BRF":
        record.totals.total_branches = int(content)

    # BRH:<number of branches hit>
    elif directive == "BRH" or directive == "BFH":
        record.totals.hit_branches = int(content)

    # DA:<line number>,<execution count>[,<checksum>]
    elif directive == 'DA':
        args = content.split(',')
        line_no = int(args[0])
        num_executions = int(args[1])
        record.lines[line_no] = num_executions

    # LF:<number of instrumented lines>
    elif directive == 'LF':
        record.totals.total_lines = int(content)

    # LH:<number of lines with a non-zero execution count>
    elif directive == 'LH':
        record.totals.hit_lines = int(content)

    return record, False


def parse_lcove(filename: str) -> t.Mapping[str, Record]:


    all_records = {}
    with open(filename, 'r') as f:
        record = None
        for l in f:
            record, done = _parse_line(l, record)
            if done:
                all_records[record.filename] = record
                record = None
    print(all_records['/ros_ws/src/navigation/move_base/src/move_base.cpp'])


if __name__=="__main__":
    assert len(sys.argv) == 2

    parse_lcove(sys.argv[1])
