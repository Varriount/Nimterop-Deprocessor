def add_example(s, excerpt):
    return msg + ':\n' + LINE_START_REGEX.sub('    ', excerpt)


def ExampleError(msg, excerpt, ex=Exception):
    raise ex(add_excerpt(msg, excerpt))