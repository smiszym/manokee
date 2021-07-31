# ET.indent() will be available from Python 3.9; until then, I use
# the implementation from http://effbot.org/zone/element-lib.htm#prettyprint
# below.
# (see https://bugs.python.org/issue14465)
def ET_indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            ET_indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
