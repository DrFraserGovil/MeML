# MeML: The **Me**eting **M**arkup **L**anguage

MeML is a markup language designed for typesetting meeting agendas, and the resulting minutes in the same document. 

The language is designed to make it easy to track assigned actions, open questions and decisions made during a meeting.

## MeML Modes

A single MeML document can be compiled in three distinct modes:



| Mode    	| Compiler Command |Description      	|  Renders...|
|---------	|---|--------------------------------------------------------------------	| ---|
| Agenda  	| `-a, --agenda` | Used for creating a basic outline of matters *which will be* discussed. | Only elements in the #Agenda block.   	|
| Chair   	| `-c, --chair` | Used for appending extra  notes to *guide what is* discussed. | Elements in the #Agenda block **and** those in the #Chair block.	|
| Minutes 	| `--notes, --minutes, -n, -m` (default) |Used for creating a summary of of *what was* discussed. | Only elements in the #Minutes (or #Notes) block.|


## MeML Syntax 

MeML is largely indifferent to whitespace - any leading or trailing whitespace is trimmed during processing. Linebreaks are used to indicate the transition from one element to the next.

### Header Metadata
Every MeML file begins with a metadata block which defines the 'who, what and when'. Each metadata is prefixed by one of the following commands, followed by a colon.

* **Title:** The name of the meeting. Will appear in large text at the top of the document.
* **Date:** Formatted as DD/MM/YYYY, or as '@TODAY', '@YESTERDAY', or arithmatic operations: '@TODAY - 2' will render as 2 days before the current date. 
> ### Important
> The compiler replaces the @DATE command in the source file with the rendered date, preventing the meeting date changing depending on when it was compiled.
* **Attend** A space-delimited list of people invited to the meeting, following the 'Person syntax' (see below)
* **Extra** A list of people (in Person Syntax) who attended, but were not invited (this field is used only in Minutes-mode)
* **Mentioned** A list of people (in Person Syntax) who were not present or invited, but who are referred to 
* **Missing** A list of people (using their assigned keys) who did not attend. An optional absence reason can be added by appending ```[absence reason]``` to the key.

> ### Note
> Linebreaks do not automatically terminate a header block. All data is assumed to belong to the previous header block, until a line which behins with a new header block is encountered.

### Person Syntax

People can be declared using the following syntax:

``` @KEY (Full name [organisation]/nickname)```

The KEY is used to identify the individual; when the document is compiled, all references to `@KEY` will be replaced with the associated nickname. The Fullname and organisation will be used only during the 'roll-call' portion of the rendered document. 

The full name, nickname and organisation cannot contain the following characters: `()[]/`. The Key may contain only alphanumeric characters.

### Body Elements

MeML uses a tiered heirarchy to organise content:

* **Sections** are defined using an RST-like syntax. They are defined by wrapping the title of the section in matching pairs of characters from the following list: (`=`, `+`, `-`, `#`). There is no pre-determined order, the first-used character defines the first level of nesting, with each successive dissimilar level defining a new level.
* **Blocks** are defined using a single `#` character. Blocks control which content is visible when in each 'mode'. The following (case-insensitive) blocks are available:
    * `# Agenda` used for items which appear on the agenda, and the chair's agenda.
    * `# Chair` used for items which appear after the agenda items on the chair's copy. Useful for detailing in more detail what the chair wishes to discuss. 
    * `# Minutes` used for items which appear on the minutes of the meeting.
    * `# Notes` equivalent to `# Minutes`



> ### Note
> A MeML document is written in an `asynchronous' manner - the agenda for one section is written next to the minutes, before beginning the next section, even when the agenda was written before the minutes.

Each line of text within a block then contains an arbitrary number of *markers*, which delineate the items within that block. Each marker is used to identify a different type of element:

| Marker 	| Name       	| Description                                                                                    	|
|--------	|------------	|------------------------------------------------------------------------------------------------	|
| (None) 	| Plain Text 	| A plain text block, rendered in normal LaTeX paragraph mode.                                   	|
| *      	|  List Item 	| A new element in a bullet-pointed list. Lists can be artbirarily nested by chaining * symbols. 	|
| !      	| Action     	| A new task assigned to an individual. See `Action syntax' below.                               	|
| ?      	| Query      	| An open question which needs to be resolved                                                    	|
| >      	| Decision   	| A finalized decision or logistical change                                                      	|
| $         | Summary       | A summary of the topic discussed, grouping together disparate thoughts                            |
| +      	| Append     	| Appends the line of text to the previous marker, inserting a line break between them. Useful for multi-line list items, for example.           	|

The Action, Query and Decision elements exhibit special behaviour when within a *Minutes* block. In addition to being including in the sequential list, they are aggregated at the top of the document in coloured boxes, allowing a high-level review of the meeting, distinct from the minutes.

> ### Note
> All text is passed verbatim into a latex compiler. Additional formatting is therefore achieved by using the associated latex commands. The following command would create a new action, assigned to @JFG, with the word 'task' in boldface.
>
> ``` ! @JFG Create a new \textbf{task}```


### Action Syntax & Teams

The action element (`!`) can be assigned to people in the meeting (or those who have been included via the ```Mentioned``` metadata). The syntax for doing so is:

``` ! @Key1/ @Key2/ @Key3 /... (etc) Action instructions```

That is, a slash-delimited list of keys before the action instruction is interpreted as being the individuals two whom a task has been assigned. 

In the summary of the assigned tasks at the top of the document, tasks are grouped according to who has been assigned them. 

If only one person is assigned a task, then a dedicated section (using their full name) is created, with each task assigned to a element of a numbered list. If multiple people are assigned a task, then the group is assigned a random *Team Name*, and tasks grouped into that team.

If an individual has both individual tasks, and team tasks, then an additional note is inserted into their section, informing them which teams they are members of.

## The MeML Compiler

We provide a compiler for MeML: ```memlmake```.

To run the compiler, ensure that it is on $PATH. The syntax is:

```
memlmake [filename] [-cmna] [--all] [-h] [-o [destination]]
```

| Option 	| Alias     	| Function                                 	|
|--------	|-----------	|------------------------------------------	|
| -h        |  --help       | Opens the help menu                       |
| -a     	| --agenda  	| Activates *Agenda Mode*                  	|
| -c     	| --chair   	| Activates *Chair Mode*                   	|
| -m     	| --minutes 	| Activates *Minutes Mode*                 	|
| -n     	| --notes   	| Alias for -m                             	|
| --all  	|           	| Activates all 3 modes                    	|
| -o     	| --output   	| Defines the output directory or filename 	|

### Output

The output of the compiler is a number PDF documents. The name and location of the files depends on the modes activated, and the value passed to `-o`:

1. **If `-o` is omitted:** The output file(s) will be created in the same directory, and have the same name as the input file - but with the file extension replaced by `.pdf`.
2. **If `-o` points to a directory:** The directory will be created if it does not already, and an output file (with the same name as the input file, but a `.pdf` extension) will be written there.
3. **If `-o` is a full file path** If the parent directory does not exist, then it is created. The output file is then saved exactly with the provided name.

Regardless of the output name, one file is generated for each active Mode - the filename is appended by either `_agenda`, `_chair` or `_minutes` as appropriate.

### Compatibility

`memlmake` is a python script, developed on Python 3.12, and has not been tested on other versions. It requires at least Python 3.8 to run.

The only external library required is `jinja2` (at least 3.1.2, included in the `requirements.txt` file).

`memlmake` generates LaTeX code, and then calls the standard `pdflatex` compiler, directing it to generate an output file as defined 


### MeML-rewriting

When called, the MeML compiler also re-writes the source document. This enables it to resolve date commands (such as @TODAY) to `lock in' the date - and ensures that the meeting date then doesn't move with each compilation. It also standardises the layout and format.


## VSCode Integration

We also provide a VSCode plugin, in the `meml-extension` directory. This can be manually installed by typing `Ctrl+Shift+P`, then navigating to `Developer: Install Extension From Location`, and installing `meml-extension`.

The extension provides syntax highlighting for the various marker lines, and a `Smart Enter' feature which automatially inserts the previous marker to enable quick note-taking (type enter again to clear the line).

