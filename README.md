Bobros
======
_Making your life a bit more beautiful_

```shell
pip install bobros
bobros --help
```

`bobros` is a tool for setting the background colour for files in PyCharm project
navigator.

It was mainly created for working with Django projects where you can have lots
of app folders, all of which may contain files with identical names like `views`
or `models`, etc. It's much easier to work with them when you can easily 
tell them apart and can easily see where one app ends and another one begins in
your project navigation panel. Colour-coding the app folders makes that task a
lot easier.

However, it turned out that doing that using the standard PyCharm mechanisms is
not that easy. You have to navigate through several settings tabs and do a lot
of clicking and typing. Well, there must be a better way!

Bobros takes a simple config and generates the correct xml files to make your
project files colour-coded. It also supports different colour-themes. 

Sample config file (i.e. `my_config.yml`):
```yaml    
themes:
    dark: # defines colours for a theme named "dark", names can be arbitrary
        one: aabb00 # defines colour "one" to have the hex value of aabb00
        two: bbaa00 # defines colour "two"
    light: # defines colours for a theme named "light". Should contain the same colours as other themes
        one: 99ff88
        two: 9988ee

items: # defines colours for the items on disk
    my_file.py: one
    my_file_2.py: two
    my_folder: one
```

Some special values: 

* `~` The "home" folder: in Django projects the settings folder by default has 
  the same name as the project folder. It's nice to have the settings folder 
  the same colour in all your projects

* `Problems`, `Non-Project Files` special names used by Idea for files/folders
  containing errors or not belonging to the current project
  
To apply a theme in a config, run the following from the root folder of your
project:

```shell
bobros charm my_config.yml -t dark
```

You could also have a less fancy config, without themes:

```yaml    
colors:
    one: aabb00
    two: bbaa00

items:
    my_file.py: one
    my_file_2.py: two
    my_folder: one
```

To apply this config, run 

```shell
bobros charm my_config.yml
```

It is an error to try to apply a config with themes and not providing a theme
name on the command line (i.e. the `-t` option), to specify a non-existing 
theme or to use a config without themes and providing the `-t` option on the 
command line.

Generating colours
------------------
I like my files to have colours of the same saturation and luminance, but 
of different hues, so bobros has a command to generate such colours from a
given initial colour: 

```shell
bobros make-colors b1e3be --points 10
```

This will generate 10 such colours, you can then copy the values to your 
config file and assign them to your items.

Checking configs
----------------
You can run 
```shell
bobross check my_config.yml
```
from the root of a PyCharm (or Idea) project. For now, it will check if the 
config specifies files that do not exist in the actual project.
