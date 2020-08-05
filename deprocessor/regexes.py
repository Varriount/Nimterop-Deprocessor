import regex as re
from functools import partial


# ## Convenience regexes ## #

line_start_regex = re.compile(
    r'^(?=.)',
    re.MULTILINE | re.VERBOSE
)




# ## Regex processing ## #

def _partial_compile(method_name, pattern, *args, **kwargs):
    regex = re.compile(pattern, re.MULTILINE | re.VERBOSE)
    method = getattr(regex, method_name)
    return partial(method, *args, **kwargs)


_compile_substitution = partial(_partial_compile, 'sub')


strip_lines = _compile_substitution(
    r'(^\s+)|(\s+$)|(\n)',
    r''
)


_expand_call_shorthand = _compile_substitution(
    r'\[\[([-_\w]+)\]\]',
    lambda m: f"(?&{m[1].replace('-', '_')})"
)

def change_extension(string, new_extension):
    return re.sub(r'\.[^.]$', new_extension, string)

def to_regex(pattern):
    # Sanity check the pattern
    if pattern.strip() == '':
        msg = "Will not compile an empty match"
        raise ExceptionWithExcerpt(msg, repr(pattern))

    # Perform shorthand expansion
    regex = _expand_call_shorthand(pattern)
    regex = re.compile(regex, re.MULTILINE | re.VERBOSE)

    if regex.match('') and regex.search('abcedfg', 1):
        msg = "Dangerous regex. Aborting"
        raise ExceptionWithExcerpt(msg, repr(regex))

    return regex