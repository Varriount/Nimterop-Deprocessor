"""
Defines a DSL that can be used to describe parameters and actions to take on
header files.
"""

import regex as re

from . import regexes

# Note, this heavily uses "function-call" shorthand
# provided by regexes.to_regex
_dsl = regexes.to_regex(r"""
    (?(DEFINE)
        # Divider for syntactical elements
        (?P<syntax_edge> \s+ )

        # Divider for statements
        (?P<statement_edge> (?:
            # A syntax edge
            (
                [[syntax-edge]]
            ) |
            # A comment
            (
                (?<!
                    ( $ | [^\\] ) # A non-backslash
                    ( (\\){2}   ) # An even number of backslashes
                )
                [#] .* 
            ) |
            (*FAIL)
        )+ )

        # A "joining" character
        (?P<join> [ _-]+ )

        # Non-greedy all
        (?P<ng_all>
            (?: . | \n )+?
        )

        # A word
        (?P<word> \w+ )
    )

    [[statement_edge]]?
    (
    (
        (?P<kind> EXCLUDE [[join]] PATH )
        [[syntax-edge]]
        (?P<value> [[ng_all]] )
        [[syntax-edge]]
        END
    ) |
    (
        (?P<kind> DEFINE )
        [[syntax-edge]]
        (?P<value> [[ng_all]] )
        [[syntax-edge]]
        END
    ) |
    (
        (?P<kind> UNDEFINE )
        [[syntax-edge]]
        (?P<value> [[ng_all]] )
        [[syntax-edge]]
        END
    ) |
    (
        (?P<kind> STRIP ( [[join]] ( SUFFIX | PREFIX ) )? )
        [[syntax-edge]]
        (?P<value> .+ )
    ) |
    (
        (?P<kind> MAP [[join]] TYPE )
        [[syntax-edge]]
        (?P<key> [[ng_all]] )
        [[syntax-edge]]
        TO
        [[syntax-edge]]
        (?P<value> [[ng_all]] )
        [[syntax-edge]]
        END
    ) |
    (
        (?P<kind> REWRITE [[join]] TOKEN )
        [[syntax-edge]]
        (?P<key> [[ng_all]] )
        [[syntax-edge]]
        TO
        [[syntax-edge]]
        (?P<value> [[ng_all]] )
        [[syntax-edge]]
        END
    ) |
    (
        (?P<kind> REGEX )
        [[syntax-edge]]
        (?P<key> [[word]] )
        [[syntax-edge]]
        IS
        [[syntax-edge]]
        (?P<value> [[ng_all]] )
        [[syntax-edge]]
        END
    ) |
    (
        (?P<kind> ( ( PRE | POST ) [[join]] )? REPLACE )
        [[syntax-edge]]
        (?P<pattern> [[ng_all]] )
        [[syntax-edge]]
        WITH
        [[syntax-edge]]
        (?P<replacement> [[ng_all]] )
        [[syntax-edge]]
        END
    ) |


    (*FAIL)
    )

    [[statement_edge]]?
""")


class DSL():
    statement_kinds = [
        'EXCLUDE_PATH',
        'DEFINE',
        'UNDEFINE',
        'STRIP',
        'STRIP_SUFFIX',
        'STRIP_PREFIX',
        'MAP_TYPE',
        'REWRITE_TOKEN',
        'REGEX',
        'REPLACE',
        'PRE_REPLACE',
        'POST_REPLACE',
    ]

    def __init__(self, text):
        statements = {k: [] for k in self.statement_kinds}

        for statement in self.gather_statements(text):
            kind = re.sub('[-_ ]', '_', statement['kind'])
            statements[kind].append(statement)

        self.process_statements(statements)


    def gather_statements(self, text):
        """
        Iterate over the input text and yield statement matches.
        The first match is expected to occur at the beginning of the input text,
        and subsequent matches are expected to occur immediately after each other
        (there can be no "gaps" in the text that match no statement).
        """
        position = 0
        while position < len(text):
            # Get the next statement match
            match = _dsl.match(text, pos=position)

            if match is None:
                end_position = min(
                    text.find('\n', position) + 1,
                    len(text)
                )
                msg = f"Couldn't find a match at position {position}."
                msg += f"Mis-match starts at {repr(text[position:end_position])}"
                raise ValueError(msg)

            position = match.end()
            yield match.groupdict() 


    def process_statements(self, raw_statements):
        def rinsort(l):
            l.sort(reverse = True)
            return l

        ## EXCLUDE PATH
        self.exclude_paths = [
            regexes.to_regex(r['value'])
            for r in raw_statements['EXCLUDE_PATH']
        ]

        ## DEFINE
        self.defines = [
            rs['value']
            for rs in raw_statements['DEFINE']
        ]
        print("Defines", self.defines)

        ## UNDEFINE
        self.undefines = [
            rs['value']
            for rs in raw_statements['UNDEFINE']
        ]
        print("Undefines", self.undefines)

        ## STRIP
        raw_statements['STRIP_SUFFIX'] += raw_statements['STRIP']
        raw_statements['STRIP_PREFIX'] += raw_statements['STRIP']

        r = lambda rs: rinsort([
            rs['value']
            for rs in raw_statements[rs]
        ])

        self.suffixes = r('STRIP_SUFFIX')
        self.prefixes = r('STRIP_PREFIX')

        ## MAP TYPE
        self.type_map = dict(rinsort([
            (rs['key'], rs['value'])
            for rs in raw_statements['MAP_TYPE']
        ]))

        ## MAP IDENTIFIER
        self.identifier_map = dict(rinsort([
            (rs['key'], rs['value'])
            for rs in raw_statements['REWRITE_TOKEN']
        ]))

        ## REGEX
        # Regexes must be processed before replacements, since replacements
        # use them.
        self.regexes = {
            r['key']: r['value']
            for r in raw_statements['REGEX']
        }

        ## REPLACE
        raw_statements['PRE_REPLACE']  += raw_statements['REPLACE']
        raw_statements['POST_REPLACE'] += raw_statements['REPLACE']

        r = lambda rs: [
            (
                regexes.to_regex(r['pattern'].format(**self.regexes)),
                regexes.strip_lines(r['replacement'])
            )
            for r in raw_statements[rs]
        ]

        self.pre_replacements = r('PRE_REPLACE')
        print(f'self.pre_replacements = {self.pre_replacements}')
        self.post_replacements = r('POST_REPLACE')
        print(f'self.post_replacements = {self.post_replacements}')

