#!/usr/bin/env python3
import re
from pathlib import Path
import yaml
import click
from xml.etree import ElementTree as et


class Charmer:
    def __init__(self, config):
        self.config = None
        self.project = Project()
        self.file_colors = FileColors(self.project)
        # self.file_colors = None
        self.predefined_patterns = None
        self.parse_config(config)

    def parse_config(self, config):
        with open(config) as infile:
            self.config = yaml.load(infile)
        self.predefined_patterns = self.get_predefined_patterns()

    def get_predefined_patterns(self):
        ret = []
        for scope_name, definitions in self.config.items():
            if scope_name.startswith("_"):
                if scope_name == "_home":
                    ret.append(self.project.name)
                continue
            for folder in definitions.get("folders", []):
                ret.append(folder)
        return ret

    def make_scopes(self):
        colors = self.config.get("_other_colors")
        if not colors:
            return
        counter = 0
        for f in Path.iterdir(self.project.root):
            if f.name.startswith("."):
                continue
            if f not in self.predefined_patterns:
                scope = Scope(f.name, self.project)
                scope.add_entry(f)
                self.file_colors.add_color(colors[counter], for_scope=scope.name)
                scope.write_scope()
                counter += 1
                counter = counter % len(colors)

    def make_predefined_scopes(self):
        for scope_name, definitions in self.config.items():
            if scope_name.startswith("_"):
                definitions = self.special_definitions(scope_name, definitions)
                if not definitions:
                    continue
            scope_name = "charmer_{}".format(scope_name)
            scope = Scope(scope_name, self.project)
            for folder in definitions["folders"]:
                scope.add_entry(folder)
                self.file_colors.add_color(definitions["color"], for_scope=scope_name)
            scope.write_scope()

    def special_definitions(self, scope_name, definitions):
        if scope_name == "_home":
            definitions["folders"] = [self.project.name]
        else:
            definitions = None
        return definitions


class Project:
    def __init__(self):
        self.root = Path.cwd()
        if not self.is_project():
            raise RuntimeError("Current directory is not a pycharm or idea project")
        self.name = self.get_project_name()
        self.idea_dir = self.root / ".idea"
        self.scopes_dir = self.idea_dir / "scopes"
        self.scopes_dir.mkdir(exist_ok=True)

    def is_project(self):
        for f in self.root.iterdir():
            if f.name == ".idea" and f.is_dir():
                return True
        return False

    def get_project_name(self):
        try:
            name_path = self.root / ".idea" / ".name"
            with open(name_path) as name_file:
                return name_file.read().strip()
        except FileNotFoundError:
            return self.root.name

    def parse_existing_files(self):
        """Find existing scopes and colours and read them in"""
        try:
            xml = et.parse(self.idea_dir / 'fileColors.xml')
        except FileNotFoundError:
            return {}
        ret = {}
        root = xml.getroot()
        for element in root.findall('component'):
            if element.attrib.get('name') != 'SharedFileColors':
                continue
            for colour in element.findall('fileColor'):
                ret[colour.attrib['scope']] = colour.attrib['color']
        return ret

    def parse_existing_colous(self):
        for file in self.iter_scope_files():
            xml = et.parse(file)
            root = xml.getroot()
            for element in root.findall('scope'):
                print('name', element.attrib['name'])

    def iter_scope_files(self):
        for file in (self.idea_dir / 'scopes').iterdir():
            if file.is_file() and file.name in ['charmer_one.xml']:
                yield file






class Scope:
    def __init__(self, name, project):
        self.patterns = []
        self.name = name
        self.project = project
        self.xml = """<component name="DependencyValidationManager">
      <scope name="{name}" pattern="{pattern}" />
    </component>"""

    def add_entry(self, path):
        if isinstance(path, Path):
            rel_path = path.relative_to(self.project.root)
            if str(rel_path).startswith(".."):
                print("Folder not inside the project: {}".format(rel_path))
        else:
            rel_path = path

        self._add_pattern(rel_path)
        if isinstance(rel_path, str) or rel_path.is_dir():
            self._add_pattern(rel_path, recursive=True)

    def _add_pattern(self, rel_path, recursive=False):
        pattern = "file[{project_name}]:{path}".format(
            project_name=self.project.name, path=rel_path
        )
        if recursive:
            pattern = "{}//*".format(pattern)
        self.patterns.append(pattern)

    def write_scope(self):
        scope_savable_name = re.sub("^\.", "_", self.name)
        scope_file_name = self.project.scopes_dir / "{}.xml".format(scope_savable_name)
        with open(scope_file_name, "w") as outfile:
            outfile.write(self.xml.format(
                name=self.name, pattern="||".join(self.patterns)
            ))


class FileColors:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="SharedFileColors">
    <fileColor scope="Problems" color="Rose" />
    <fileColor scope="Non-Project Files" color="eaeaea" />
{}
  </component>
</project>
    """

    colour_entry = '    <fileColor scope="{}" color="{}" />'

    def __init__(self, project):
        self.project = project
        self.colors = {}


    def add_color(self, color, *, for_scope):
        self.colors[for_scope] = color


    def write(self):
        with open(self.project.idea_dir/"fileColors.xml", "w") as outfile:
            outfile.write(FileColors.xml.format(
                "\n".join([
                    FileColors.colour_entry.format(*x) for x in self.colors.items()
                ])
            ))


@click.command(
    "charmer",
    help="Add colour to the files and folders in your PyCharm project "
         "using the specified CONFIG"
)
@click.argument("config", type=click.Path())
def main(config):
    c = Charmer(config)
    c.make_predefined_scopes()
    c.make_scopes()
    c.file_colors.write()


if __name__ == "__main__":
    main(None)
