import re

# Node types
class Literal:
    __slots__ = ('ch',)
    def __init__(self, ch):
        self.ch = ch
    def __repr__(self):
        return f"Literal({self.ch!r})"

class Any:
    __slots__ = ()
    def __repr__(self):
        return "Any"

class Star:
    __slots__ = ()
    def __repr__(self):
        return "Star"

class Group:
    __slots__ = ('alts',)
    def __init__(self, alts):
        self.alts = alts  # list of list of nodes
    def __repr__(self):
        return f"Group({self.alts})"

def parse(pattern):
    i = 0
    n = len(pattern)
    
    def parse_escape():
        nonlocal i
        if i < n and pattern[i] == '\\':
            i += 1
            if i >= n:
                raise ValueError("Trailing backslash")
            ch = pattern[i]
            i += 1
            return Literal(ch)
        return None
    
    def parse_element():
        nonlocal i
        if i >= n:
            return None
        # Check for escape first
        if pattern[i] == '\\':
            return parse_escape()
        c = pattern[i]
        if c == '?':
            i += 1
            return Any()
        elif c == '*':
            i += 1
            return Star()
        elif c == '{':
            return parse_group()
        else:
            i += 1
            return Literal(c)
    
    def parse_group():
        nonlocal i
        if i >= n or pattern[i] != '{':
            raise ValueError("Expected '{'")
        i += 1
        alts = []
        current_alt = []
        while True:
            if i >= n:
                raise ValueError("Unclosed group")
            c = pattern[i]
            if c == '}':
                i += 1
                alts.append(current_alt)
                break
            elif c == ',':
                i += 1
                alts.append(current_alt)
                current_alt = []
            else:
                elem = parse_element()
                if elem is None:
                    raise ValueError("Invalid element in group")
                current_alt.append(elem)
        return Group(alts)
    
    # Parse top-level sequence
    nodes = []
    while i < n:
        elem = parse_element()
        if elem is not None:
            nodes.append(elem)
    return nodes

def node_to_regex(node):
    if isinstance(node, Literal):
        # Escape special regex characters
        return re.escape(node.ch)
    elif isinstance(node, Any):
        return '.'
    elif isinstance(node, Star):
        return '.*'
    elif isinstance(node, Group):
        alt_regexes = []
        for alt in node.alts:
            alt_regex = ''.join(node_to_regex(n) for n in alt)
            alt_regexes.append(alt_regex)
        # Join alternatives with '|', wrap in parentheses
        return '(' + '|'.join(alt_regexes) + ')'
    else:
        raise TypeError(f"Unknown node type: {type(node)}")

def nodes_to_regex(nodes):
    return ''.join(node_to_regex(n) for n in nodes)

def matches(pattern, text):
    nodes = parse(pattern)
    regex_str = nodes_to_regex(nodes)
    regex = re.compile(regex_str)
    return bool(regex.fullmatch(text))

def shortest_prefix_match(pattern, text):
    # Try L from 0 to len(text)
    for L in range(len(text) + 1):
        if matches(pattern, text[:L]):
            return L
    return -1

# If run as script, maybe test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pat = sys.argv[1]
        txt = sys.argv[2] if len(sys.argv) > 2 else ""
        print(shortest_prefix_match(pat, txt))
