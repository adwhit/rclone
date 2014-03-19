import re
from pygments import highlight
import pygments.lexers as lexers
from pygments.formatters import HtmlFormatter

class CodeFormatter():
    aliases = {
            "lisp": "common-lisp",
            "objective": "objective-c",
            "javascript": "javascript"
            }

    def __init__(self, raw, lang):
        self.raw = raw
        self.language = lang.strip().lower()
        self._codesnippets = []
        self._presnippets = []
        self._htmllist = []
        self._html = None
        self._css = None

    @property
    def html(self):
        if self._htmllist:
            return "\n".join(self._htmllist)

    def langsniffer(self, lang):
        for (key, value) in CodeFormatter.aliases.items():
            if key in lang:
                return value
        return "c"

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
            self._htmllist.append((start.start(),end.end(),"<pre id=output>" + snippet + "</pre>"))

    def fill_html_list(self):
        l = sorted(self._htmllist)
        #prelude
        bound = len(l)
        if bound > 0:
            bit = self.raw[0:l[0][0]].strip()
            if bit:
                bit = md_format(bit)
                l.append((0,l[0][0],bit))
            for i in range(0,bound-1):
                start = l[i][1]
                end = l[i+1][0]
                bit = self.raw[start:end].strip()
                if bit:
                    bit = md_format(bit)
                    l.append((start, end, bit))
            #epilogue
            bit = self.raw[l[bound-1][1]:].strip()
            if bit:
                bit = md_format(bit)
                l.append((l[bound-1][1],len(self.raw),bit))
        else:
             self._htmllist = [self.raw]
        self._htmllist = sorted(l)

    def pygmentise(self, snippet):
        formatter = HtmlFormatter()
        if self.language in CodeFormatter.aliases:
            lang = CodeFormatter.aliases[lang]
        else:
            lang = self.language
        try:
            lexer = lexers.get_lexer_by_name(lang)
        except lexers.ClassNotFound:
            lexer = lexers.get_lexer_by_name(self.langsniffer(lang))
            print("Warning: lexer %s not found. Using lexer %s" % (self.language, lexer))
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

def md_format(text, task=None):
    """Markdown formatting substitution. Possibly inefficient"""
    text = text.replace("{{out}}", "<h4>Output</h4>")
    text = re.sub("{{trans\|(.*)}}", "<h4>Translation of \g<1></h4>", text)
    text = re.sub("===(.*)===", "<h4>\g<1><h4>", text)
    text = re.sub("==(.*)==", "<h3>\g<1><h3>", text)
    text = re.sub("\n+", "<br>", text)
    text = re.sub("{{libheader\|(\w*)}}", "Library: \g<1>", text)
    if task:
        #text = re.sub("{{task}}", "<h3>%s<h3>" % task, text)
        text = re.sub("{{task(\|.*)?}}", "<h3>%s</h3>" % task, text)


    # ==HEADER2==
    # ===HEADER3===
    # {{task}}
    return text 
    
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
