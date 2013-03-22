# This pass is for debug only
from pyrser import meta
from pyrser import parsing


@meta.add_method(parsing.Parser)
def dumpParseTree(self):
    res = "{"
    for k, v in self.rules.items():
        if isinstance(v, ParserTree):
            res += "\n\t{} : {}\t,".format(repr(k), v.dumpParseTree(1))
        else:
            res += "\n\t{} : {},".format(repr(k), repr(v))
    res += "\n}"
    return res


@meta.add_method(parsing.Rule)
def dumpParseTree(self, level=0):
    return "{}{}".format('\t' * level, self.name)


@meta.add_method(parsing.Hook)
def dumpParseTree(self, level=0):
    return "{}#{}".format('\t' * level, self.name)


@meta.add_method(parsing.Call)
def dumpParseTree(self, level=0):
    #TODO(iopi): think to remap methods to hooks
    if self.callObject == parsing.Parser.readRange:
        return "{}'{}'..'{}'".format(
            '\t' * level, self.params[0], self.params[1])
    elif self.callObject == parsing.Parser.readChar:
        return "{}'{}'".format('\t' * level, self.params[0])
    elif self.callObject == parsing.Parser.readText:
        return "{}\"{}\"".format('\t' * level, self.params[0])
    elif self.callObject == parsing.Parser.readInteger:
        return "{}#num".format('\t' * level)
    elif self.callObject == parsing.Parser.readIdentifier:
        return "{}#id".format('\t' * level)
    else:
        res = "{}#call: {} (".format('\t' * level, self.callObject.__name__)
        res += ", ".join(["{}".format(repr(param)) for param in self.params])
        res += ")"
        return res


@meta.add_method(parsing.Scope)
def dumpParseTree(self, level=0):
    res = "\n{}[{}\n".format('\t' * (level + 1), self.begin.dumpParseTree(0))
    res += self.clause.dumpParseTree(level + 1)
    res += "\n{}]{}\n".format('\t' * (level + 1), self.end.dumpParseTree(0))
    return res


@meta.add_method(parsing.Capture)
def dumpParseTree(self, level=0):
    res = "\n{}[\n".format('\t' * level)
    res += self.clause.dumpParseTree(level + 1)
    res += "\n{}] : {}\n".format('\t' * level, self.tagname)
    return res


@meta.add_method(parsing.Seq)
def dumpParseTree(self, level=0):
    return ' '.join(
        [clause.dumpParseTree(level + 1) for clause in self.clauses])


@meta.add_method(parsing.Alt)
def dumpParseTree(self, level=0):
    indent = '\t' * level
    res = "\n{}  {}".format(indent, self.clauses[0].dumpParseTree(0))
    if len(self.clauses) > 1:
        res += "\n{}| ".format(indent)
    res += "\n{}| ".format('\t' * level).join(
        [clause.dumpParseTree(0) for clause in self.clauses[1:]])
    return res


@meta.add_method(parsing.RepOptional)
def dumpParseTree(self, level=0):
    res = ("\n{}[\n".format('\t' * level))
    res += self.clause.dumpParseTree(level + 1)
    res += ("\n{}]?\n".format('\t' * level))
    return res


@meta.add_method(parsing.Rep0N)
def dumpParseTree(self, level=0):
    res = ("\n{}[\n".format('\t' * level))
    res += self.clause.dumpParseTree(level + 1)
    res += ("\n{}]*\n".format('\t' * level))
    return res


@meta.add_method(parsing.Rep1N)
def dumpParseTree(self, level=0):
    res = ("\n{}[\n".format('\t' * level))
    res += self.clause.dumpParseTree(level + 1)
    res += ("\n{}]+\n".format('\t' * level))
    return res
