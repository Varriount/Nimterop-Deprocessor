import shlex
import subprocess
import regex as re
import os
from itertools import chain

from . import regexes

# ## Helper functions ## #
# Exception helpers
def add_example(msg, excerpt):
    return msg + ':\n' + regexes.line_start_regex.sub('    ', excerpt)


def ExampleError(msg, excerpt, ex=Exception):
    raise ex(add_example(msg, excerpt))


# Read/write helpers
def read_files(paths):
    for path in paths:
        # Read in the data
        try:
            with open(path, 'r') as fh:
                data = fh.read()
        except:
            print(f'Could not read contents of {path}')
            continue

        yield path, data


def write_files(path_data_pairs):
    for path, data in path_data_pairs:
        with open(path, 'w') as fh:
            data = fh.write(data)


def write_file(path, data):
    try:
        with open(path, 'w') as fh:
            data = fh.write(data)
    except:
        print(f"Unable to write to file {path}")


def append_file(path, data):
    with open(path, 'a+') as fh:
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

    def repl_hook(m):
        if False:
            append_file(path + '.repl', '\n'.join([
                'Match'  , m[0],
                'Pattern', m.re.pattern,
                'Start'  , str(m.start()),
                'End'    , str(m.end()),
                '\n'
            ]))
        return m.expand(replacement)

    for path, data in file_data:
        for index, (regex, replacement) in enumerate(subs):
            data = regex.sub(repl_hook, data)
            subs_used[index] = True
        
        yield path, data

    # for index, used in enumerate(subs_used):
    #     if not used:
    #         print(add_example(
    #             "Warning, replacement not used:",
    #             repr(subs[index])
    #         ))


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


def preprocess_files(args, paths):
    # Run the preprocessor
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
            "-fms-compatibility-version=19.26.28806",
            '-Wno-builtin-macro-redefined',
            '-Wno-comment',
            '-Wno-macro-redefined',
            '-Wno-pragma-once-outside-header',
            '-Wno-extra-tokens',
            '-Wno-nonportable-include-path',
            '-Wno-invalid-token-paste',
            *args,
            *paths
        ],
        capture_output = True,
        print_stdout = False,
        print_stderr = False
    )

    if clang.stderr:
        print(clang.stderr)
    if clang.returncode != 0:
        print(f"Preprocess failed for {paths[0]}. Wrote error to file")
        write_file(paths[0], clang.stderr + '\n' + clang.stdout)
        return

    for file, data in dejoin_files(clang.stdout):
        yield file, data


def nimterop_files(
        paths,
        defines,
        undefines,
        suffixes,
        prefixes,
        type_map,
        identifier_map):
    # Run the preprocessor
    from_list = lambda arg, li: chain.from_iterable(
        (arg, c)
        for c in li
    )
    from_dict = lambda arg, di: chain.from_iterable(
        (arg, f'{k}={v}')
        for k, v in di.items()
    )

    common_args = [
        '--debug'     ,
        '--noHeader'  ,
        '--pnim'      ,
        '--preprocess',
        '--convention', 'stdcall',
        '--mode'      , 'c',
        *from_list('--defines', defines),
        *from_list('--prefix', prefixes),
        *from_list('--suffix', suffixes),
        *from_dict('--replace', identifier_map),
        *from_dict('--typeMap', type_map),
    ]

    environ = {k: v for k, v in os.environ.items()}

    write_file('toast_args.cfg', ' '.join(common_args))

    for header_path in paths:
        nim_path = re.sub(r'\.[^.]+$', '.nim', header_path)

        args = [
            'toast.exe',
            '--output', nim_path,
            'toast_args.cfg',
            header_path,
        ]
        # print(args)
        toast = run_process(
            args = args,
            env  = environ,
            capture_output = True,
            print_stdout = False,
            print_stderr = False
        )

        # if toast.stderr:
        #     print(toast.stderr)

        if toast.returncode != 0:
            print(f"Toast failed for {header_path}. Wrote error to file")
            write_file(header_path, f'{args}\n{toast.stderr}\n{toast.stdout}')
            # raise Exception("Toast failed")

        yield nim_path
    

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


def dejoin_files(joined_data):
    marker_regex = re.compile('\n//FILE_MARKER (.*)')

    position = 0
    while position < len(joined_data):
        # Find the next file marker
        marker = marker_regex.search(joined_data, position)
        if marker is None:
            return None

        marker_start = marker.start()
        marker_end   = marker.end()
        path  = marker.group(1)

        file_data = joined_data[position:marker_start]
        yield path, file_data
        position = marker_end
