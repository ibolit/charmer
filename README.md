Bobros
======
_Making your life a bit more beautiful_

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

Sample config file::
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