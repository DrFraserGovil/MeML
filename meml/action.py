import re
import hashlib
ACTION_RE = re.compile(r"^\s*((?:@\w+\s*/\s*)*@\w+)\s+(.*)$")
ADJECTIVES = [
    'Amiable', 'Bouncy', 'Breezy', 'Bright', 'Clever', 
    'Crisp', 'Dandy', 'Dapper', 'Eager', 'Easy', 'Fizzy', 'Fluffy', 'Fresh', 
    'Gentle', 'Glad', 'Gleeful', 'Grand', 'Groovy', 'Handy', 'Happy', 'Hardy', 
    'Humble', 'Jaunty', 'Jolly', 'Keen', 'Kind', 'Light', 'Lively', 
    'Lush', 'Mellow', 'Merry', 'Neat', 'Nifty', 'Noble', 'Peppy', 
    'Placid', 'Plucky', 'Polite', 'Posh', 'Quaint', 'Quirky', 'Radiant', 'Snappy', 'Snug', 'Spiffy', 'Spry', 'Stellar', 'Sunny', 'Sweet', 
    'Tidy', 'Upbeat', 'Vivid', 'Zesty', 'Zingy'
]

ANIMALS = [
    'Alpaca', 'Badger', 'Beetle', 'Bilby', 'Bunny', 'Cat', 'Crab', 
    'Deer', 'Dolphin', 'Duck', 'Eland', 'Finch', 'Frog', 'Gecko', 'Goat', 
    'Gull', 'Hamster', 'Heron', 'Hippo', 'Jerboa', 'Koala', 'Lamb', 
    'Lark', 'Lemur', 'Mink', 'Mole', 'Moth', 'Mouse', 'Newt', 'Otter', 
    'Owl', 'Panda', 'Puffin', 'Quail', 'Quokka', 'Seal', 'Sheep', 
    'Shrew', 'Sloth', 'Snail', 'Stoat', 'Swan', 'Tapir', 'Toad', 'Turtle', 
    'Vole', 'Whale', 'Wombat', 'Zebra', 'Robin', 'Pippin', 'Chick', 'Pony', 
    'Fawn', 'Sardine', 'Newt'
]
class ActionSet:
    def __init__(self,committee,actions):
        
        team_tasks = {}      
        individual_tasks = {}
        # person_to_teams = {} # Person object -> set of "Team Names"
        for topic, block in actions:

            for line in block.Elements:
                match = ACTION_RE.search(line.Text)
                if match:
                    kl = [r.strip() for r in match.group(1).split("/")]
                    people = committee.MatchSet(kl)
                    task_text = match.group(2).strip()
                    
                    if len(people) == 1:
                        person = people[0].FullName
                        individual_tasks.setdefault(person,[[],[]])[0].append(task_text)
                    else:
                        team_id = "".join(sorted(kl))
                        hash_val = int(hashlib.md5(team_id.encode()).hexdigest(), 16)
                        team_name =  f"Team {ADJECTIVES[hash_val % len(ADJECTIVES)]} {ANIMALS[hash_val % len(ANIMALS)]}"
                        for person in people:
                            individual_tasks.setdefault(person.FullName,[[],[]])[1].append(team_name)
                        team_tasks.setdefault(team_name, [[],[p.Name for p in people]])[0].append(task_text)
                else:
                    # Fallback for action-typed lines that didn't match the @key pattern
                    team_tasks.setdefault("General Actions", [[],[None]])[0].append(line.Text.strip())
        
        self.Team = team_tasks
        self.Individual = individual_tasks
    def Texify(self):
        s = ""
        #do teams first
        if "General Actions" in self.Team:
            s += "\\team{General Tasks}{}{"
            for item in self.Team["General Actions"][0]:
                s += "\n" + item
            s += "}"
            self.Team.pop("General Actions")

        teams = sorted(self.Team.keys())
        for team in teams:
            s += f"\n\\team{{{team}}}{{{", ".join(self.Team[team][1])}}}{{{
                "\n".join([f"\\item {r}" for r in self.Team[team][0] ])
            }}}"
        
        
        people = list(self.Individual.keys())
        people.sort(key=lambda name: name.split(" ")[-1].lower())
        
        for person in people:
            s += f"\n\\individual{{{person}}}{{{
                ", ".join([r[5:] for r in self.Individual[person][1]])
            }}}{{{
                "\n".join([f"\\item {r}" for r in self.Individual[person][0] ])
            }}}"

        return s