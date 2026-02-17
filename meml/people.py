import re
PEOPLE_RE = re.compile(r'(@\w+)\s*\(([^/)]+)(?:/([^)]+))?\)')
class Committee:
    def __init__(self):
        self.Members = []


    def AddPeople(self,line,activator):
        matches = PEOPLE_RE.findall(line)
        if not matches:
            print(f"Warning: {activator} line found but no valid people parsed")
            return ""

        for key,full,nick in matches:
            p = Person(key,full,nick,activator.lower()=="attend",activator.lower()!="mentioned")
            self.Members.append(p)

    

    def MatchSet(self,keys):
        matching = []
        
        for key in keys:
            matching.append(self.Match(key))
            
        return matching 
    def Match(self,key):
        for person in self.Members:
            if person.Key == key:
                return person
        print(f"Could not locate the individual assigned the key '{key}', a temporary membership has been created")
        clearname = key.replace("@","")
        tmp = Person(key,clearname)
        tmp.SetExtra()
        self.Members.append(tmp)
        return self.Members[-1]
    
    def FlagSick(self,keys,declarations,reasons):
        for i,key in enumerate(keys):
            for person in self.Members:
                if person.Key == key:
                    person.SetSick(reasons[i])
                    continue
            searcher = key
            if reasons[i]:
                searcher += f"({declarations[i]})"
            matches = PEOPLE_RE.findall(searcher)
            for key,full,nick in matches:
                p = Person(key,full,nick,True)
                p.SetSick(reasons[i])
                self.Members.append(p)
    
    def ResolveNames(self,text):
        def replace_match(match):
            full_key = match.group(0)

            #guard against tex primitives being reassigned
            if full_key in ["@maketitle","@title","@date"]:
                return full_key
            person = self.Match(full_key)
            
            return person.Name
            
        # Matches '@' followed by word characters
        pattern = r"@\w+"

        return re.sub(pattern, replace_match, text)
class Person:
    def __init__(self,key,full_name,nickname=None,isInvited=True,isThere=True):
        self.Key = key
        self.FullName = full_name
        self.IsPresent = isThere
        if nickname:
            self.Name = nickname
            self.HasNickname = True
        else:
            clean_name = re.sub(r'\[.*?\]', '', self.FullName)
            self.Name = clean_name.strip()
            self.HasNickname = False
        self.Invited = isInvited
        self.Sick = False
        self.SicknessReason = None
        self.gap = " "*max(1,5-len(self.Key))
    def Rewrite(self):
        
        if self.HasNickname:
            return f"{self.Key}{self.gap}({self.FullName}/{self.Name})"
        else:
            return f"{self.Key}{self.gap}({self.FullName})"
    def SetExtra(self):
        self.Invited = False
    def SetSick(self,reason):
        self.Sick = True
        self.isThere = False
        self.SicknessReason = reason
    def SickName(self):
        r = self.FullName
        if self.SicknessReason:
            r += f" ({self.SicknessReason})"
        return r