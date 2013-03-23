from pyrser.parsing.parserBase import BasicParser
from pyrser.parsing.node import Node


class ParserTree:
    """Dummy Base class for all parse tree classes.

    common property:
        pt if contain a ParserTree
        ptlist if contain a list of ParserTree
    """
    pass


class Seq(ParserTree):
    """A B C bnf primitive as a functor."""

    def __init__(self, *ptlist: ParserTree):
        ParserTree.__init__(self)
        if len(ptlist) == 0:
            raise TypeError()
        self.ptlist = ptlist

    def __call__(self, parser: BasicParser) -> bool:
        for pt in self.ptlist:
            parser.skip_ignore()
            if not pt(parser):
                return False
        return True


class Scope(ParserTree):
    """functor to wrap SCOPE/rule directive or just []."""

    def __init__(self, begin: Seq, end: Seq, pt: Seq):
        ParserTree.__init__(self)
        self.begin = begin
        self.end = end
        self.pt = pt

    def __call__(self, parser: BasicParser) -> Node:
        if not self.begin(parser):
            return False
        res = self.pt(parser)
        if not self.end(parser):
            return False
        return res


class Call(ParserTree):
    """Functor wrapping a BasicParser method call in a BNF clause."""

    def __init__(self, callObject, *params):
        ParserTree.__init__(self)
        #TODO(bps): fix the function vs. method mess
        import types
        if isinstance(callObject, types.MethodType):
            self.callObject = callObject.__func__
        else:
            self.callObject = callObject
        self.params = params

    def __call__(self, parser: BasicParser) -> Node:
        return self.callObject(parser, *self.params)


class CallTrue(Call):
    """Functor to wrap arbitrary callable object in BNF clause."""

    def __call__(self) -> Node:
        self.callObject(*self.params)
        return True


class Capture(ParserTree):
    """Functor to handle capture variables."""

    def __init__(self, tagname: str, pt: ParserTree):
        ParserTree.__init__(self)
        if not isinstance(tagname, str) or len(tagname) == 0:
            raise TypeError("Illegal tagname for capture")
        self.tagname = tagname
        self.pt = pt

    def __call__(self, parser: BasicParser) -> Node:
        if parser.begin_tag(self.tagname):
            parser.push_rule_nodes()
            parser.rulenodes[-1][self.tagname] = Node()
            res = self.pt(parser)
            parser.pop_rule_nodes()
            if res and parser.end_tag(self.tagname):
                text = parser.get_tag(self.tagname)
                # wrap it in a Node instance
                if type(res) is bool:
                    res = Node(res)
                #TODO(iopi): should be a future capture object for multistream
                # capture
                if not hasattr(res, 'value'):
                    res.value = text
                parser.rulenodes[-1][self.tagname] = res
                return res
        return False


class Alt(ParserTree):
    """A | B bnf primitive as a functor."""

    def __init__(self, *ptlist: Seq):
        ParserTree.__init__(self)
        self.ptlist = ptlist

    def __call__(self, parser: BasicParser) -> Node:
        for pt in self.ptlist:
            parser._stream.save_context()
            parser.skip_ignore()
            res = pt(parser)
            if res:
                parser._stream.validate_context()
                return res
            parser._stream.restore_context()
        return False


class RepOptional(ParserTree):
    """[]? bnf primitive as a functor."""
    def __init__(self, pt: Seq):
        ParserTree.__init__(self)
        self.pt = pt

    def __call__(self, parser: BasicParser) -> bool:
        parser.skip_ignore()
        self.pt(parser)
        return True


class Rep0N(ParserTree):
    """[]* bnf primitive as a functor."""

    #TODO(iopi): at each turn, pop/push rulenodes
    def __init__(self, pt: Seq):
        ParserTree.__init__(self)
        self.pt = pt

    def __call__(self, parser: BasicParser) -> bool:
        parser.skip_ignore()
        while self.pt(parser):
            parser.skip_ignore()
        return True


class Rep1N(ParserTree):
    """[]+ bnf primitive as a functor."""

    #TODO(iopi): at each turn, pop/push rulenodes
    def __init__(self, pt: Seq):
        ParserTree.__init__(self)
        self.pt = pt

    def __call__(self, parser: BasicParser) -> bool:
        parser.skip_ignore()
        if self.pt(parser):
            parser.skip_ignore()
            while self.pt(parser):
                parser.skip_ignore()
            return True
        return False


class Rule(ParserTree):
    """Call a rule by its name."""

    #TODO(iopi): Handle additionnal value
    def __init__(self, name: str):
        ParserTree.__init__(self)
        self.name = name

    def __call__(self, parser: BasicParser) -> Node:
        return parser.eval_rule(self.name)


class Hook(ParserTree):
    """Call a hook by his name."""

    def __init__(self, name: str, param: [(object, type)]):
        ParserTree.__init__(self)
        self.name = name
        # compose the list of value param, check type
        for v, t in param:
            if type(t) is not type:
                raise TypeError("Must be pair of value and type (i.e: int, "
                                "str, Node)")
        self.param = param

    def __call__(self, parser: BasicParser) -> bool:
        valueparam = []
        for v, t in self.param:
            if t is Node:
                import weakref
                valueparam.append(weakref.proxy(parser.rulenodes[-1][v]))
            elif type(v) is t:
                valueparam.append(v)
            else:
                raise TypeError("Type mismatch expected {} got {}".format(
                    t, type(v)))
        return parser.eval_hook(self.name, valueparam)
