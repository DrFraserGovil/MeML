import meml.people
import re
from meml.util import *
import meml.date
import meml.parser
import hashlib
import meml.action
import meml.output
class Meeting:
    def __init__(self,filepath):
        self.RequiresRewrite = True
        self.Members = meml.people.Committee()
        self.ParseFile(filepath)

        if self.RequiresRewrite:
            meml.output.ToMeML(self,filepath)

    def ParseFile(self,path):

        inPreamble = True

        headerSymbols = []
        body = []
        preamble = []
        with open(path,'r') as f:
            lineCount = 0
            for line in f:
                lineCount+=1
                clean_line = sanitize(line)
                if not clean_line:
                    continue

                line = meml.parser.Line(clean_line,headerSymbols,lineCount)
                inPreamble = inPreamble and not (line.Type == "header") and not (line.Type == "section")

                if inPreamble:
                    preamble.append(line)
                else:
                    body.append(line)

        self.ParsePreamble(preamble)

        self.ParseBody(body)

    def ParseBody(self,lines):
        self.Topics = []
        idx = 0
        while idx < len(lines):
            if lines[idx].Type == "header":
                topic,idx = meml.parser.ParseTopic(idx,lines)
                self.Topics.append(topic)
            elif lines[idx].Type == "section":
                topic,idx = meml.parser.ParseTopic(idx,lines,"General")
                self.Topics.append(topic)
            idx += 1
        
        # for  in lines:
        #     if line.Type == "header":
        #         if topic:
        #             self.Topics.append(topic)
        #         topic = meml.parser.Topic(line.Text)
        #     elif topic:
        #         topic.ParseLine(line)
        # if topic:
        #     self.Topics.append(topic)

    def ParsePreamble(self,lines):
        met =[]
        handlers = {
            "title": self._title,
            "date": self._date,
            "save": self._save,
            "attend": self._attend,
            "mentioned":self._mentioned,
            "extra": self._extra,
            "missing": self._missing,
            "absent": self._missing,
        }

        met = {}
        for cmd in handlers:
            met[cmd] = meml.parser.Line()

        prev_cmd = None
        for line in lines:
            cmd = line.getPreambleCommand(handlers.keys())
            if cmd:
                met[cmd].absorb(line)
                prev_cmd = cmd
            else:
                if prev_cmd:
                    met[prev_cmd].absorb(line)

        for cmd in met.keys():
            if not met[cmd].Blank:
                handlers[cmd](met[cmd])
            # handlers[cmd](met[cmd])

    def _title(self,value):
        if value.Blank:
            self.Title = "Meeting"
        else:
            self.Title = value.Text

    def _missing(self,line):
        pattern = re.compile(r'(@\w+)(?:\s*\(([^)]*)\))?(?:\s*\[([^\]]*)\])?')
        keys = []
        decs = []
        reasons = []

        for match in pattern.finditer(line.Text):
            key = match.group(1)
            declare= match.group(2) # This will be None if no () found
            reason = match.group(3) # This will be None if no [] found
            keys.append(key)
            decs.append(declare.strip() if declare else None)
            reasons.append(reason.strip() if reason else None)

        self.Members.FlagSick(keys,decs,reasons)

    def _mentioned(self,line):
        if not line.Blank:
            self.Members.AddPeople(line.Text,"Mentioned")

    def _save(self,line):
        if not line.Blank:
            self.RequiresRewrite = True

    def _attend(self,line):
        if not line.Blank:
            self.Members.AddPeople(line.Text,"Attend")
    
    def _extra(self,line):
        if not line.Blank:
            self.Members.AddPeople(line.Text,"Extra")
    
    def _date(self,line):
        if line.Blank:
            self.Date = None
        else:
            self.Date = meml.date.Date(line.Text)
            self.RequiresRewrite = self.RequiresRewrite or self.Date.WasParsed

    def Get(self,thing):
        actions = []
        for topic in self.Topics:
            actions += topic.Get(thing)
        return actions

    def GetActions(self,mode="tex"):
        actions = self.Get("action")

        A = meml.action.ActionSet(self.Members,actions)
        
        if mode == "tex":
            return A.Texify()
        return actions
    
    def GetSummary(self,mode="tex"):
        

        def group_summaries(summaries, default_topic):
            block_pattern = re.compile(r'^\s*\[([^\]]+)\](.*)', re.DOTALL)
            
            grouped_data = {}
            current_topic = default_topic
            
            grouped_data[current_topic] = []

            for item in summaries:
                match = block_pattern.match(item)
                
                if match:
                    current_topic = match.group(1).strip()
                    content = match.group(2).strip()
                    
                    if current_topic not in grouped_data:
                        grouped_data[current_topic] = []
                    
                    if content:
                        grouped_data[current_topic].append(content)
                else:
                    grouped_data[current_topic].append(item)
                    
            return grouped_data
        
        summary = self.Get("summary")
        names = [r[0] for r in summary]
        unique = set(names)
        if len(unique) == 0:
            return None
        s = ""

      
        textList = {}
        for topic in unique:
            idxs = [i for i,x in enumerate(names) if  x == topic]
            for idx in idxs:
                text = summary[idx][1].GetText(mode)
                summaries = re.findall(r'\\summary\{([^}]+)\}', text)
                q = group_summaries(summaries,topic)
                
                for key in q:
                    textList.setdefault(key,[]) 
                    textList[key] += q[key]


        for t in textList:
            if len(textList[t]) > 0:
                s += f"\n\\summaryBlock{{{t}}}{{{"\n\n".join(textList[t])}}}"
        return s