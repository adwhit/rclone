import re
from pygments import highlight
import pygments.lexers as lexers
from pygments.formatters import HtmlFormatter


class CodeFormatter():

    def __init__(self, raw, lang):
        self.raw = raw
        self.language = lang
        self._codesnippets = []
        self._presnippets = []
        self._htmllist = []
        self._html = None
        self._css = None

    @property
    def html(self):
        if self._htmllist:
            return "\n".join(self._htmllist)


    def get_code_snippets(self):
        codestart = re.finditer("<lang ([^>]+)>", self.raw)
        codeend = re.finditer("</lang>", self.raw)
        for (start, end) in zip(codestart, codeend):
            #self.languague = start.groups(0)[0].strip().lower()
            snippet = self.raw[start.end():end.start()]
            self._codesnippets.append(snippet)
            snippet = self.pygmentise(snippet)
            self._htmllist.append((start.start(), end.end(), snippet))

    def get_pre_snippets(self):
        prestart = re.finditer("<pre>", self.raw)
        preend = re.finditer("</pre>", self.raw)
        for (start, end) in zip(prestart, preend):
            snippet = self.raw[start.end():end.start()]
            self._presnippets.append(snippet)
            self._htmllist.append((start.start(),end.end(),"<pre>" + snippet + "</pre>"))

    def fill_html_list(self):
        l = sorted(self._htmllist)
        #prelude
        bit = self.raw[0:l[0][0]]
        bound = len(l)
        if bit:
            bit = "<p>" + bit + "<p>"
            l.append((0,l[0][0],bit))
        for i in range(0,bound-1):
            start = l[i][1]
            end = l[i+1][0]
            bit = self.raw[start:end]
            if bit:
                bit = "<p>" + bit + "<p>"
                l.append((start, end, bit))
        #epilogue
        bit = self.raw[l[bound-1][1]:]
        if bit:
            bit = "<p>" + bit + "<p>"
            l.append((l[bound-1][1],len(self.raw),bit))
        self._htmllist = sorted(l)

    def pygmentise(self, snippet):
        formatter = HtmlFormatter(source = self.language)
        try:
            lexer = lexers.get_lexer_by_name(self.language)
        except lexers.ClassNotFound:
            lexer = lexers.guess_lexer(snippet)
        return highlight(snippet, lexer, formatter)

    def format(self):
        self.get_code_snippets()
        self.get_pre_snippets()
        self.fill_html_list()
        return self.html

    @property
    def html(self):
        if self._html is None:
            self._html = "\n".join([snip[2] for snip in self._htmllist])
        return self._html

    @property
    def css(self):
        if self._css is None:
            self._css = HtmlFormatter().get_style_defs(".highlight")
        return self._css

def formatter(text, lang):
    ct = CodeFormatter(text, lang)
    ct.format()
    return(ct.html, ct.css)
    
def main(path):
    with open(path) as f:
        text = f.read()
    (body, css) = formatter(text, "")
    header = "<html><head>"
    cssheader = "<style type=\"text/css\">"
    cssfooter = "</style>"
    bodyheader = "</head><body>"
    bodyfooter = "</body>"
    footer = "</html>"
    print("".join([header,cssheader,css,cssfooter,bodyheader,body,bodyfooter,footer]))


if __name__== "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Please provide file path")
        sys.exit(1)
    main(sys.argv[1])
