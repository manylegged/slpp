import re

ERRORS_unexp_end_string = u'Unexpected end of string while parsing Lua string.',
ERRORS_unexp_end_table = u'Unexpected end of table while parsing Lua string.',
ERRORS_mfnumber_minus = u'Malformed number (no digits after initial minus).',
ERRORS_mfnumber_dec_point = u'Malformed number (no digits after decimal point).',
ERRORS_mfnumber_sci = u'Malformed number (bad scientific format).',

CONST_quotes = '"\'['
CONST_num = set('eExX.-+ABCDEFabcdef0123456789')

class ParseError(Exception):
    pass


class SLPP:

    def __init__(self):
        self.text = ''
        self.ch = ''
        self.at = 0
        self.len = 0
        self.depth = 0
        self.newline = '\n'
        self.tab = '  '

    def decode(self, text):
        if not text or not isinstance(text, basestring):
            return
        #FIXME: only short comments removed
        reg = re.compile('--.*$', re.M)
        text = reg.sub('', text, 0)
        self.text = text
        self.at, self.ch, self.depth = 0, '', 0
        self.len = len(text)
        self.next_chr()
        result = self.value()
        return result

    def encode(self, obj):
        if not obj:
            return
        self.depth = 0
        return self.__encode(obj)

    def __encode(self, obj):
        s = ''
        tab = self.tab
        newline = self.newline
        tp = type(obj)
        if isinstance(obj, basestring):
            s += '"%s"' % obj.replace(r'"', r'\"')
        elif tp in [int, float, long, complex]:
            s += str(obj)
        elif tp is bool:
            s += str(obj).lower()
        elif tp in [list, tuple, dict]:
            self.depth += 1
            if len(obj) == 0 or ( tp is not dict and len(filter(
                    lambda x:  type(x) in (int,  float,  long) \
                    or (isinstance(x, basestring) and len(x) < 10),  obj
                )) == len(obj) ):
                newline = tab = ''
            dp = tab * self.depth
            sep = '%s%s' % (newline, dp) if len(obj) > 4 else ""
            s += sep + "{"
            js = ', ' + sep
            if tp is dict:
                s += js.join([self.__encode(v) if type(k) is int \
                              else '%s = %s' % (k, self.__encode(v)) \
                              for k, v in obj.iteritems()
                          ])
            else:
                s += js.join([self.__encode(el) for el in obj])
            self.depth -= 1
            s += "}"
        elif tp is set:
            return "|".join(obj)
        return s

    def white(self):
        while self.ch:
            if self.ch.isspace():
                self.next_chr()
            else:
                break

    def next_chr(self):
        if self.at >= self.len:
            self.ch = None
            return None
        self.ch = self.text[self.at]
        self.at += 1
        return True

    def value(self):
        self.white()
        if not self.ch:
            return
        elif self.ch == '{':
            return self.object()
        if self.ch == "[":
            self.next_chr()
        if self.ch.isdigit() or self.ch == '-':
            return self.number()
        elif self.ch in CONST_quotes:
            return self.string(self.ch)
        return self.word()

    def string(self, end=None):
        s = ''
        start = self.ch
        if end == '[':
            end = ']'
        if start in ['"',  "'",  '[']:
            while self.next_chr():
                if self.ch == end:
                    self.next_chr()
                    if start != "[" or self.ch == ']':
                        return s
                if self.ch == '\\' and start == end:
                    self.next_chr()
                    if self.ch != end:
                        s += '\\'
                s += self.ch
        print ERRORS_unexp_end_string

    def object(self):
        o = {}
        k = ''
        idx = 0
        numeric_keys = False
        self.next_chr()
        if self.ch and self.ch == '}':
            self.white()
            self.next_chr()
            return o #Exit here
        else:
            while self.ch:
                self.white()
                if self.ch == '{':
                    o[idx] = self.object()
                    idx += 1
                    continue
                elif self.ch == '}':
                    self.next_chr()
                    if k:
                       o[idx] = k
                    if not numeric_keys and all(isinstance(key, int) for key in o):
                        ar = []
                        for key in o:
                           ar.insert(key, o[key])
                        o = ar
                    return o #or here
                else:
                    if self.ch == ',':
                        self.next_chr()
                        continue
                    else:
                        k = self.value()
                        if self.ch == ']':
                            numeric_keys = True
                            self.next_chr()
                    self.white()
                    if self.ch == '=':
                        self.next_chr()
                        self.white()
                        o[k] = self.value()
                        idx += 1
                        k = ''
                    elif self.ch == ',':
                        self.next_chr()
                        self.white()
                        o[idx] = k
                        idx += 1
                        k = ''
        print ERRORS_unexp_end_table #Bad exit here

    def word(self):
        s = ''
        if self.ch != '\n':
          s = self.ch
        while self.next_chr():
            if self.ch.isalnum():
                s += self.ch
            else:
                if re.match('^true$', s, re.I):
                    return True
                elif re.match('^false$', s, re.I):
                    return False
                elif s == 'nil':
                    return None
                elif '|' in s:
                    return set(s.split('|'))
                return str(s)

    def number(self):
        n = ''
        while self.ch:
            if self.ch in CONST_num:
                n += self.ch
                self.next_chr()
            else:
                break
        if "." in n:
            return float(n)
        else:
            return int(n, 0)

slpp = SLPP()

__all__ = ['slpp']
