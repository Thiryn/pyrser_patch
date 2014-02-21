import unittest
from pyrser.type_checking.signature import *
from pyrser.type_checking.scope import *
from pyrser.type_checking.type import *


class InternalType_Test(unittest.TestCase):

    def test_symbol_01_symbolpatch(self):
        """
        Test of symbol mangling redefinition.
        For custom language due to multi-inheritance order resolution
        (python MRO), just use follow the good order. Overloads first.
        """
        class MySymbol(Symbol):
            def show_name(sig: Symbol):
                return "cool " + sig.name

            def internal_name(sig: Symbol):
                return "tjrs " + sig.name

        class MySignature(MySymbol, Signature):
            pass
        s = MySignature('funky', 'bla', 'blu')
        self.assertEqual(s.show_name(), 'cool funky',
                         "Bad symbol patching in type_checking")
        self.assertEqual(s.internal_name(), 'tjrs funky',
                         "Bad symbol patching in type_checking")

    def test_scope_01_pp(self):
        """
        Test pretty Printing
        """
        var = Signature('var1', 'int')
        f1 = Signature('fun1', 'int', '')
        f2 = Signature('fun2', 'int', 'int')
        f3 = Signature('fun3', 'int', 'int', 'double')
        tenv = Scope(sig=[var, f1, f2, f3])
        self.assertEqual(str(var), "var var1 : int",
                         "Bad pretty printing of type")
        self.assertEqual(str(f1), "fun fun1 : () -> int",
                         "Bad pretty printing of type")
        self.assertEqual(str(f2), "fun fun2 : (int) -> int",
                         "Bad pretty printing of type")
        self.assertEqual(str(f3), "fun fun3 : (int, double) -> int",
                         "Bad pretty printing of type")
        self.assertEqual(str(tenv), """scope :
    fun fun1 : () -> int
    fun fun2 : (int) -> int
    fun fun3 : (int, double) -> int
    var var1 : int
""", "Bad pretty printing of type")
        t1 = Type('t1')
        self.assertEqual(str(t1), "type t1", "Bad pretty printing of type")
        t1.add(Signature('fun1', 'a', 'b'))
        self.assertEqual(str(t1), """type t1 :
    fun t1.fun1 : (b) -> a
""", "Bad pretty printing of type")

    def test_scope_02_setop(self):
        """
        Test Scope common operation
        """
        var = Signature('var1', 'int')
        tenv = Scope(sig=var)
        self.assertIn(Signature('var1', 'int'), tenv,
                      "Bad __contains__ in type_checking.Scope")
        tenv.add(Signature('fun1', 'int', 'float', 'char'))
        self.assertIn(Signature('fun1', 'int', 'float', 'char'), tenv,
                      "Bad __contains__ in type_checking.Scope")
        ## inplace modification
        # work with any iterable
        tenv |= [Signature('fun2', 'int', 'int')]
        self.assertIn(Signature('fun2', 'int', 'int'), tenv,
                      "Bad __contains__ in type_checking.Scope")
        # work with any iterable
        tenv |= {Signature('fun3', 'int', 'int')}
        self.assertIn(Signature('fun3', 'int', 'int'), tenv,
                      "Bad __contains__ in type_checking.Scope")
        # retrieves past signature
        v = tenv.get(var.internal_name())
        self.assertEqual(id(v), id(var), "Bad get in type_checking.Scope")
        # intersection_update, only with Scope
        tenv &= Scope(sig=Signature('var1', 'int'))
        v = tenv.get(var.internal_name())
        self.assertNotEqual(id(v), id(var), "Bad &= in type_checking.Scope")
        # difference_update, only with Scope
        tenv |= [Signature('fun2', 'int', 'int'),
                 Signature('fun3', 'char', 'double', 'float')]
        tenv -= Scope(sig=Signature('var1', 'int'))
        self.assertNotIn(Signature('var1', 'int'), tenv,
                         "Bad -= in type_checking.Scope")
        # symmetric_difference_update, only with Scope
        tenv ^= Scope(sig=[Signature('var2', 'double'),
                      Signature('fun2', 'int', 'int'),
                      Signature('fun4', 'plop', 'plip', 'ploum')])
        self.assertIn(Signature('fun4', 'plop', 'plip', 'ploum'), tenv,
                      "Bad ^= in type_checking.Scope")
        self.assertNotIn(Signature('fun2', 'int', 'int'), tenv,
                         "Bad ^= in type_checking.Scope")
        ## binary operation
        # |
        tenv = Scope(sig=[Signature('tutu', 'toto', 'tata'),
                     Signature('tutu', 'int', 'char')]) |\
            Scope(sig=Signature('blam', 'blim')) |\
            Scope(sig=Signature('gra', 'gri', 'gru'))
        self.assertIn(Signature('tutu', 'toto', 'tata'), tenv,
                      "Bad | in type_checking.Scope")
        self.assertIn(Signature('gra', 'gri', 'gru'), tenv,
                      "Bad | in type_checking.Scope")
        # &
        tenv = Scope(sig=[Signature('tutu', 'toto', 'tata'),
                     Signature('tutu', 'int', 'char')]) &\
            Scope(sig=[Signature('blam', 'blim'),
                  Signature('tutu', 'toto', 'tata')])
        self.assertIn(Signature('tutu', 'toto', 'tata'), tenv,
                      "Bad & in type_checking.Scope")
        self.assertEqual(len(tenv), 1, "Bad & in type_checking.Scope")
        # -
        tenv = Scope(sig=[Signature('tutu', 'toto', 'tata'),
                     Signature('tutu', 'int', 'char')]) -\
            Scope(sig=Signature('tutu', 'int', 'char'))
        self.assertIn(Signature('tutu', 'toto', 'tata'), tenv,
                      "Bad - in type_checking.Scope")
        self.assertEqual(len(tenv), 1, "Bad - in type_checking.Scope")
        # ^
        tenv1 = Scope(sig=[Signature('tutu', 'toto', 'tata'),
                      Signature('tutu', 'int', 'char'),
                      Signature('gra', 'gru')])
        tenv2 = Scope(sig=[Signature('blim', 'blam', 'tata'),
                      Signature('f', 'double', 'char'),
                      Signature('gra', 'gru'),
                      Signature('v', 'd')])
        tenv = tenv1 ^ tenv2
        self.assertEqual(len(tenv), 5, "Bad ^ in type_checking.Scope")
        self.assertIn(Signature('tutu', 'toto', 'tata'), tenv,
                      "Bad ^ in type_checking.Scope")
        self.assertNotIn(Signature('gra', 'gru'), tenv,
                         "Bad ^ in type_checking.Scope")

    def test_scope_03_overload(self):
        # test get by symbol name
        tenv = Scope(sig=[Signature('tutu', 'tata'),
                     Signature('plop', 'plip'),
                     Signature('tutu', 'lolo')])
        tenv |= Scope(sig=[Signature('plop', 'gnagna'),
                      Signature('tutu', 'int', 'double')])
        trest = tenv.get_by_symbol_name('tutu')
        self.assertIn(Signature('tutu', 'tata'), trest,
                      "get_by_symbol_name in type_checking.Scope")
        self.assertIn(Signature('tutu', 'lolo'), trest,
                      "get_by_symbol_name in type_checking.Scope")
        self.assertIn(Signature('tutu', 'int', 'double'), trest,
                      "get_by_symbol_name in type_checking.Scope")
        self.assertNotIn(Signature('plop', 'gnagna'), trest,
                         "get_by_symbol_name in type_checking.Scope")
        # test get by return type
        tenv = Scope(sig=[Signature('tutu', 'int'),
                     Signature('plop', 'plip'),
                     Signature('tutu', 'int', '')])
        tenv |= Scope(sig=[Signature('plop', 'int'),
                      Signature('tutu', 'int', 'double', 'int')])
        trest = tenv.get_by_return_type('int')
        self.assertIn(Signature('tutu', 'int'), trest,
                      "Bad get_by_return_type in type_checking.Scope")
        self.assertIn(Signature('plop', 'int'), trest,
                      "Bad get_by_return_type in type_checking.Scope")
        trest = tenv.get_by_return_type('int').get_by_symbol_name('tutu')
        self.assertNotIn(Signature('plop', 'int'), trest,
                         "Bad get_by_return_type in type_checking.Scope")
        # test get by params
        f = Scope(sig=[Signature('f', 'void', 'int'),
                  Signature('f', 'int', 'int', 'double', 'char'),
                  Signature('f', 'double', 'int', 'juju')])
        f |= Scope(sig=Signature('f', 'double', 'char', 'double', 'double'))
        p1 = Scope(sig=[Signature('a', 'int'), Signature('a', 'double')])
        p2 = Scope(sig=[Signature('b', 'int'), Signature('b', 'double')])
        p3 = Scope(sig=[Signature('c', 'int'), Signature('c', 'double'),
                   Signature('c', 'char')])
        (trestf, trestp) = f.get_by_params(p1, p2, p3)
        self.assertIn(Signature('f', 'int', 'int', 'double', 'char'), trestf,
                      "Bad get_by_params in type_checking.Scope")
        self.assertEqual(len(trestf), 1,
                         "Bad get_by_params in type_checking.Scope")
        self.assertEqual(len(trestp), 3,
                         "Bad get_by_params in type_checking.Scope")
        a = trestp.get_by_symbol_name('a')
        self.assertEqual(len(a), 1,
                         "Bad get_by_params in type_checking.Scope")
        sa = next(iter(a.values()))
        self.assertEqual(sa.tret, "int",
                         "Bad get_by_params in type_checking.Scope")
        b = trestp.get_by_symbol_name('b')
        self.assertEqual(len(b), 1,
                         "Bad get_by_params in type_checking.Scope")
        sb = next(iter(b.values()))
        self.assertEqual(sb.tret, "double",
                         "Bad get_by_params in type_checking.Scope")
        c = trestp.get_by_symbol_name('c')
        self.assertEqual(len(c), 1,
                         "Bad get_by_params in type_checking.Scope")
        sc = next(iter(c.values()))
        self.assertEqual(sc.tret, "char",
                         "Bad get_by_params in type_checking.Scope")