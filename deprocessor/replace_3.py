import re
import subprocess
import itertools
import signal
import sys
import os
from itertools import chain
from pathlib import Path
from multiprocessing import Pool
from pprint import pprint
import json

jprint = lambda x: print(json.dumps(x, default=repr, indent=4))

dsl_text = r"""
# Beginning of file
REGEX BOF ^(?<!\n) END

# one or more tab/space characters
REGEX spaces (?:[ \t]+) END

"""[1:].strip()




# ## Global Helpers ## #
LINE_START_REGEX = re.compile(r'^(?=.)', re.MULTILINE)
LEAD_TRAIL_SPACE_REGEX = re.compile(r'(^[ \t]+)|([ \t]+$)', re.MULTILINE)


def add_excerpt(s, excerpt):
    return msg + ':\n' + LINE_START_REGEX.sub('    ', excerpt)


def ExceptionWithExcerpt(msg, excerpt, ex=Exception):
    raise ex(add_excerpt(msg, excerpt))


def to_regex(m):
    if m.strip() == '':
        msg = "Will not compile an empty match"
        raise ExceptionWithExcerpt(msg, repr(m))

    result = re.compile(m, re.MULTILINE | re.VERBOSE)

    if result.match('') and result.search('abcedfg', 1):
        msg = "Dangerous regex. Aborting"
        raise ExceptionWithExcerpt(msg, repr(m))

    return result


def strip_lines(s):
    return LEAD_TRAIL_SPACE_REGEX.sub('', s).strip()


# ## DSL Logic ## #
dsl = [
     r"""
        {clearspaces}?
        (?P<type> \# ) .*
        {clearspaces}?
     """,
    r"""
    (
        (?P<type> REGEX )
        {clearspaces}
        (?P<name> {word})
        {clearspaces}
        (?P<pattern> (.|\n)+?)
        {clearspaces}
        END
        {clearspaces}?
    )
    """,
    r"""
    (
        (?P<type> EXCLUDE_PATH )
        {clearspaces}
        (?P<pattern> (.|\n)+?)
        {clearspaces}
        END
        {clearspaces}?
    )
    """,
    r"""
    (
        (?P<type> (((PRE|POST)_)?REPLACE))
        {clearspaces}
        (?P<pattern>   (.|\n)+? )
        {clearspaces}
        WITH
        {clearspaces}
        (?P<replacement> (.|\n)+? )
        {clearspaces}
        END
        {clearspaces}?
    )
    """,
    r"""
    (
        (?P<type> (((PRE|POST)_)?DEFINE))
        {spaces}
        (?P<macro> .+)
        {clearspaces}?
    )
    """,
    r"""
    (
        (?P<type> (((PRE|POST)_)?UNDEFINE))
        {spaces}
        (?P<macro> .+)
        {clearspaces}?
    )
    """
]


class DSL():
    dsl_matchers = [
        to_regex(
            s.format(
                spaces=r'(?:[ ]+)', 
                clearspaces=r'(?:\s+)',
                word=r'(?:\w+)'
            )
        ) for s in dsl
    ]

    def gather_statements(self, text):
        # Find all the statements
        position = 0
        while position < len(text):
            # Get the next statement match
            match = None

            for matcher in self.dsl_matchers:
                match = matcher.match(text, position)
                if match is not None:
                    position = match.end()
                    break

            if match is None:
                msg = f"Couldn't find a match at position {position}."
                msg += f"Mis-match starts at {repr(text[position:position+5])}"
                raise Exception(msg)

            yield match.groupdict() 


    def process_statements(self, raw_statements):
        # Regexes must be processed before replacements, since replacements
        # use them.
        self.regexes = {
            r['name']: r['pattern']
            for r in raw_statements['REGEX']
        }

        # Replacements
        raw_statements['PRE_REPLACE']  += raw_statements['REPLACE']
        raw_statements['POST_REPLACE'] += raw_statements['REPLACE']

        r = lambda rs: [
            (
                to_regex(r['pattern'].format(**self.regexes)),
                strip_lines(r['replacement'])
            )
            for r in raw_statements[rs]
        ]

        self.pre_replacements = r('PRE_REPLACE')
        self.post_replacements = r('POST_REPLACE')


        # Defines
        raw_statements['PRE_DEFINE']    += raw_statements['DEFINE']
        raw_statements['POST_DEFINE']   += raw_statements['DEFINE']

        r = lambda rs: [
            '#define ' + d['macro']
            for d in raw_statements[rs]
        ]

        self.pre_defines = r('PRE_DEFINE')
        self.post_defines = r('POST_DEFINE')


        # Defines
        raw_statements['PRE_UNDEFINE']  += raw_statements['UNDEFINE']
        raw_statements['POST_UNDEFINE'] += raw_statements['UNDEFINE']

        r = lambda rs: [
            '#undef ' + d['macro']
            for d in raw_statements[rs]
        ]

        self.pre_undefines = r('PRE_UNDEFINE')
        self.post_undefines = r('POST_UNDEFINE')

        # Path exclusions
        self.exclude_paths = [
            to_regex(p['pattern']) for p in raw_statements['EXCLUDE_PATH']
        ]


    def __init__(self, text):
        # print() ; print(self.dsl_matchers)
        raw_statements = {
            "REGEX"         : [],
            "EXCLUDE_PATH"  : [],
            #
            "REPLACE"       : [],
            "PRE_REPLACE"   : [],
            "POST_REPLACE"  : [],
            #
            "DEFINE"        : [],
            "PRE_DEFINE"    : [],
            "POST_DEFINE"   : [],
            #
            "UNDEFINE"      : [],
            "PRE_UNDEFINE"  : [],
            "POST_UNDEFINE" : [],
            '#'             : []
        }

        for raw_statement in self.gather_statements(text):
            statement_type = raw_statement['type']
            raw_statements[statement_type].append(raw_statement)

        # Process raw statements
        self.process_statements(raw_statements)




# ## Pipeline ## #

# Read/write helpers
def read_files(paths):
    for path in paths:
        # Read in the data
        with open(path, 'r') as fh:
            data = fh.read()

        yield path, data


def write_files(path_data_pairs):
    for path, data in path_data_pairs:
        with open(path, 'w') as fh:
            data = fh.write(data)


def write_file(path, data):
    with open(path, 'w') as fh:
        data = fh.write(data)


# Process helpers
def run_process(*args, print_stdout=True, print_stderr=True, **kwargs):
    def _print(arg):
        if arg: print(arg)

    internal_kwargs = dict(text=True)
    print_func      = lambda x: x

    if print_stdout and print_stderr:
        print_func = lambda x: _print(x.stdout.rstrip())
        internal_kwargs['stdout'] = subprocess.PIPE
        internal_kwargs['stderr'] = subprocess.STDOUT
    elif print_stdout:
        print_func = lambda x: _print(x.stdout.rstrip())
        internal_kwargs['capture_output'] = True
    elif print_stderr:
        print_func = lambda x: _print(x.stderr.rstrip())
        internal_kwargs['capture_output'] = True

    result = subprocess.run(*args, **kwargs, **internal_kwargs)
    print_func(result)
    return result




# ## Steps ## #
def sub_file_data(subs, file_data):
    subs = list(subs)
    subs_used = [False]*len(subs)

    for path, data in file_data:
        for index, (regex, replacement) in enumerate(subs):
            data = regex.sub(replacement, data)
            subs_used[index] = True
        
        yield path, data

    for index, used in enumerate(subs_used):
        if not used:
            print(add_excerpt(
                "Warning, replacement not used:",
                subs[index]
            ))


def remove_sections(start_marker, end_marker, file_data):
    for path, data in file_data:
        count = 0
        while True:
            start_pos = data.find(start_marker)
            if start_pos < 0:
                break

            end_pos = data.find(end_marker, start_pos + len(start_marker))
            if end_pos < 0:
                print(f"Unbalanced marker found in {path}. File written to.")
                write_file(path, data)
                break

            count += 1
            data = data[: start_pos] + data[end_pos + len(end_marker) :]

        # print("Removed", count, "sections from", path)
        yield path, data


def preprocess_files(args, file_data):
    # Run the preprocessor
    for path, data in file_data:
        clang = run_process(
            [
                'clang',
                '--preprocess',
                '--no-line-commands',
                '--comments',
                '--comments-in-macros',
                # '-U__has_attribute',
                # '-U__has_builtin',
                # '-U__has_feature',
                # '-U__has_declspec_attribute',
                # '-U__has_extension',
                # '-U__has_warning',
                '-Wno-builtin-macro-redefined',
                '-Wno-comment',
                '-Wno-macro-redefined',
                '-Wno-pragma-once-outside-header',
                '-Wno-extra-tokens',
                *args,
                '-'
            ],
            input        = data,
            capture_output = True,
            print_stdout = False,
            print_stderr = False
        )

        if clang.stderr or clang.returncode != 0:
            # print(clang.stderr)
            print(f"Preprocess failed for {path}. Wrote error to file")
            write_file(path, clang.stderr + '\n' + clang.stdout)
            continue

        yield path, clang.stdout
    

def reformat_files(paths):
    # Run the formatter
    clang = run_process(
        ['clang-format', '-i', *paths],
    )


def c2nim_files(paths):
    # print(f"Starting c2nim {paths[0]}")
    c2nim = run_process(
        ['c2nim', *paths],
    )


#


def worker(dsl, paths):
    pre_macros = '\n'.join(chain(dsl.pre_defines, dsl.pre_undefines))
    post_macros = '\n'.join(chain(dsl.post_defines, dsl.post_undefines))

    include_match = r"""
        ^       # Beginning of line
        [ \t]*  # Spaces
        [#]     # Macro start
        [ \t]*  # Spaces
        include
        [ \t]*  # Spaces
        (
            (<[^>]+>) |
            ("[^"]+")
        )
    """

    include_replacement = strip_lines(r"""
        //INCLUDE_MARKER
        {pre_macros}
        \g<0>
        {post_macros}
        //INCLUDE_MARKER
    """.format(**locals()))

    declude_match = r"""
        //INCLUDE_MARKER \n
        (.|\n)*?         
        //INCLUDE_MARKER
    """

    include_sub = [(to_regex(include_match), include_replacement)]
    declude_sub = [(to_regex(declude_match), r'\n')]

    # Read files in
    file_data = read_files(paths)

    # Perform initial replacements
    file_data = sub_file_data(dsl.pre_replacements, file_data)

    # Add macros around includes
    file_data = sub_file_data(include_sub, file_data)

    # Preprocess files
    file_data = preprocess_files([], file_data)

    # Remove includes
    # file_data = sub_file_data(declude_sub, file_data)

    # Remove includes 
    file_data = remove_sections('//INCLUDE_MARKER', '//INCLUDE_MARKER', file_data)

    # Perform post replacements
    file_data = sub_file_data(dsl.post_replacements, file_data)

    # Write files out
    write_files(file_data)


if __name__ != "__main__":
    prev = signal.getsignal(signal.SIGINT)

    def handler(*args, **kwargs):
        os.kill(os.getppid(), signal.SIGINT)
        prev(*args, **kwargs)
        sys.exit(1)

    signal.signal(signal.SIGINT, handler)



else:
    dsl = DSL(dsl_text)
    # jprint(dsl.replacements)


    PATH_LIST = [
        '.\\' + str(p)
        for p in Path("./output").rglob('*.h')
        if not any(
            regex.search(str(p)) for regex in dsl.exclude_paths
        )
    ]

    PATH_CHUNKS = [
        PATH_LIST[i::200]
        for i in range(0, 200)
    ]

    POOL = Pool(4)

    try:
        print("Running workers")
        POOL.starmap(
            worker,
            ((dsl, chunk) for chunk in PATH_CHUNKS)
        )

        # print("Running Formatter")
        # POOL.map(
        #     reformat_files,
        #     PATH_CHUNKS
        # )

        print("Running C2Nim")
        POOL.map(
            c2nim_files,
            PATH_CHUNKS
        )

    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        POOL.terminate()
    else:
        POOL.close()