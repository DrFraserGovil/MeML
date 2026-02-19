import re

HEADER_RE = re.compile(r'^([=\-\+\*#]{2,})\s*(.+?)\s*\1$')


def detectHeader(line,headerCatalogue):
    match = HEADER_RE.match(line)
    if match:
        decoration = match.group(1)
        title = match.group(2)

        if decoration in headerCatalogue:
            level = headerCatalogue.index(decoration)
            headerCatalogue[:] = headerCatalogue[:level + 1]
        else:
            headerCatalogue.append(decoration)
            level = len(headerCatalogue)-1

        return True, title, level,decoration

    else:
        return False, None,None,None
    
typeMenu = {"*": "bullet","!":"action",">":"decision","+":"addition","#":"section","$":"summary","?":"question"}
#don't forget to add them to the primary marker regex below
invertedMenu = {v: k for k, v in typeMenu.items()}
invertedMenu["text"] = ""


def LineWrapper(mode,type,level):
    wrap = ["\t"*(level+2),""]
    delim = "\n"
    perwrap = ["",""]
    if mode == "tex":
        delim = "\n\n"
    if type == "bullet":
        if mode == "mtg":
            wrap = ["\t"*(level+2)+"*"*(level+1)+" ",""]
            delim = "\n"+"\t"*(level+2)+"+ "
        if mode == "tex":
            wrap = ["\\item ",""]
            delim = "\n\n"
    if type == "action":
        if mode == "mtg":
             wrap = ["\t"*(level+2)+"!"*(level+1)+" ",""]
        if mode == "tex":
            wrap = ["\\action{","}"]
    if type == "decision":
        if mode == "mtg":
             wrap = ["\t"*(level+2)+">"*(level+1)+" ",""]
        if mode == "tex":
            wrap = ["\\decision{","}"]
    if type == "question":
        if mode == "mtg":
            wrap = ["\t"*(level+2)+"?"*(level+1)+" ",""]
        if mode == "tex":
            perwrap = ["\\question{","}"]
    if type == "summary":
        if mode == "mtg":
            wrap = ["\t"*(level+2)+"$"*(level+1)+" ",""]
        if mode == "tex":
            wrap = ["\\summary{","}"]
    return wrap,delim,perwrap
def BlockWrapper(mode,type,bullet):
    wrap = ["",""]
    delim = "\n"
    if type == "bullet" and mode == "tex":
        wrap = [f"\\begin{{{bullet}}}",f"\\end{{{bullet}}}"]


    return wrap,delim
class Line:
    def __init__(self,rawline=None,cataglogue=[],lineNo=0):
        if not rawline:
            self.Blank = True
            self.Text = ""
            return
        self.Number = lineNo
        self.Blank = False
        self.Type = "text"
        self.Level = None
        self.Appended = []
        self.IsFirstBullet = False
        isheader,title,level,symbol = detectHeader(rawline,cataglogue)

        if isheader:
            self.Type = "header"
            self.Text = title
            self.Level = level
            self.Symbol = symbol
        else:
            match = re.match(r'^([*!>+#?$]+)\s*(.*)', rawline)
            if match:
                markers, contents = match.groups()
                primary_marker = markers[0]
                self.Type = typeMenu.get(primary_marker, "text")
                if self.Type == "bullet":
                    self.Level = len(markers) - 1
                else:
                    self.Level = 0
                self.Text = contents
            else:
                self.Level = 0
                self.Text = rawline

    def GetBulletType(self):
        self.IsFirstBullet = True
        regex = r"\[([^\]]+)\](.*)$"
        match = re.match(regex, self.Text)
        code = match.group(1).lower() if match else None
        if code in ["enum","describe"]:
            self.Text = match.group(2)
            self.BulletCode = code.upper()
            if code == "enum":
                return "enumerate"
            else:
                return "description"
        else:
            self.BulletCode = None
            return "itemize"
    def absorb(self,line,delimiter=" "):
        if self.Blank:
            self.Text = line.Text
            self.Blank = False
        else:
            self.Text = f"{self.Text}{delimiter}{line.Text}"
    def getPreambleCommand(self,cmds):
        if ":" not in self.Text:
            return None
        else:
            cmd,val = self.Text.split(":",1)
            cmd = cmd.strip().lower()
            
            if cmd in cmds:
                self.Text = val.strip()
                return cmd
            else:
                #non-argument line which has a colon in it: just insert it into previous argument
                return None
    def Feed(self,line):
        self.Appended.append(line.Text)
    def GetText(self,mode,type=None):
        if self.Blank or (type is not None and self.Type != type):
            return ""
        wrap,delimiter,perwrap = LineWrapper(mode,self.Type,self.Level)
        if self.IsFirstBullet and self.BulletCode and mode == "mtg":
            wrap[0] = wrap[0] + f"[{self.BulletCode}]"

        s = wrap[0] + delimiter.join([perwrap[0] + r + perwrap[1] for r in [self.Text] + self.Appended]) + wrap[1]
        return s

class Block:
    def __init__(self,firstLine=None):
        self.IsBlank = True
        if firstLine:
            self.Feed(firstLine)


    def Feed(self,line):

        if self.IsBlank:
            if line.Type == "addition":
                print(f"Invalid addition-append on line: {line.Number}")
                print("Line will be omitted from output")
                return True
            self.IsBlank = False
            self.Type = line.Type
            if self.Type == "bullet":
                self.BulletType = line.GetBulletType()
            self.Level = line.Level
            self.Elements = [line]
            return True
        

        if line.Type == "addition":
            self.Elements[-1].Feed(line)
            return True
        if line.Type != self.Type:
            return False
        
        if self.Level == line.Level:
            self.Elements.append(line)
            return True
        
        if self.Level > line.Level:
            return False
        else:
            if self.Elements[-1].Level == line.Level or isinstance(self.Elements[-1],Block):
                self.Elements[-1].Feed(line)
            else:
                # reach here if level differential, and block does not have inner blocks

                    if line.Level != self.Elements[-1].Level + 1:
                        print(f"Non-continous level change detected in line {line.Number}")
                        print("Nesting level will be automatically corrected")
                    #     line.Level = self.Level + 1
                    self.Elements.append(Block(line))
            return True
    def GetText(self,mode,type=None):
        # print("Getting text for block",self.Level,mode)
        wrap,delim = BlockWrapper(mode,self.Type,self.BulletType)
        s = wrap[0] + (f"% level {self.Level}\n" if mode=="tex" else "")
        for el in self.Elements:
            s += el.GetText(mode,type)
            if len(s) > 0 and s[-1] != delim:
                s += delim
        s += wrap[1]  + (f"% level {self.Level}\n" if mode=="tex" else "")
        # print("Finished block",self.Level,mode)
        return s

class Section:
    def __init__(self,title):
        if title.lower() == "notes":
            title = "minutes"
        self.Type = title.lower()
        self.Blocks = []

    def Feed(self,line):
        if self.Blocks and self.Blocks[-1].Feed(line):
            return
        self.Blocks.append(Block(line))
    def GetText(self,mode,indent=0,type=None):
        text = "".join([r.GetText(mode,type) for r in self.Blocks])
        if indent == 0:
            return text
        
        t = text.split("\n")
        indent = "\t"*indent
        return indent + ("\n" + indent).join(t) 
class Topic:
    def __init__(self,title,level,symbol="--"):
        # print(title)
        self.Title = title
        self.Level = level
        self.SubTopics = []
        self.Sections = {}
        self.Symbol = symbol
        # print(self.Title,self.Level)
    def AddSection(self,section):
        if section.Type not in self.Sections:
            self.Sections[section.Type] = section

    def Get(self,thing,root=""):
        collect = []
        if "minutes" in self.Sections:
            for block in self.Sections["minutes"].Blocks:
                if block.Type == thing:
                    collect.append([root+self.Title,block])
        for topic in self.SubTopics:
            collect += topic.Get(thing,self.Title+": ")
        return collect

def ParseTopic(idx,lines,spoof=None):
    if not spoof:
        t = Topic(lines[idx].Text,lines[idx].Level,lines[idx].Symbol)
        idx+=1
    else:
        t = Topic(spoof,0)
    while idx < len(lines):
        if lines[idx].Type == "header":
            if lines[idx].Level <= t.Level:
                return t,idx-1
            else:
                sub_t,idx = ParseTopic(idx,lines)
                t.SubTopics.append(sub_t)  
        elif lines[idx].Type == "section":
            # t.AddSection(lines[idx].Text) 
            sec,idx = ParseSection(idx,lines)
            t.AddSection(sec)
        idx += 1
    return t,idx

def ParseSection(idx,lines):
    s = Section(lines[idx].Text)
    idx += 1
    while idx < len(lines):
        if lines[idx].Type in ["header","section"]:
            return s,idx-1
        else:
            s.Feed(lines[idx])
        idx += 1
    return s,idx
    