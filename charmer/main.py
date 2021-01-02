#!/usr/bin/env python3
import re
from collections import defaultdict
from pathlib import Path
from ruamel.yaml import YAML
import click
from xml.etree import ElementTree as et


class Charmer:
    def __init__(self, config):
        self.project = Project()
        self.predefined_patterns = None
        self.config = self.parse_config(config)

    def parse_config(self, config):
        with open(config) as infile:
            yaml = YAML()
            return yaml.load(infile)

    def check_config(self):
        disk_items = [x.name for x in self.project.root.iterdir()]
        conf_items = self.config.get('items', {})
        if None in conf_items:
            conf_items[self.project.name] = None
            del conf_items[None]
            del conf_items['Problems']
            del conf_items['Non-Project Files']
        conf_items = list(conf_items.keys())

        missing_on_disk = set()

        for item in conf_items:
            if item not in disk_items:
                missing_on_disk.add(item)

        print('Items in config and not on disk')
        for i in missing_on_disk:
            print(f'    • {i}')


    def prepare_scopes(self):
        file_colors = FileColors(self.project)
        colors = self.config.get('colors', {})
        colors['default'] = 'ff5555'
        ret = defaultdict(list)
        for file_path, color in self.config.get('items', {}).items():
            color_key = color if color in colors else 'default'
            if file_path is None:
                file_path = self.project.name
            if file_path in ['Problems', 'Non-Project Files']:
                file_colors.add_color(colors[color], for_scope=file_path)
                continue

            ret[color_key].append(file_path)

        for color_name, paths in ret.items():
            scope = Scope(color_name, self.project, paths)
            scope.write_scope()
            file_colors.add_color(colors[color_name], for_scope=scope.name)
        file_colors.write()


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
                ret[self.remove_project_name(colour.attrib['scope'])] = colour.attrib['color']
        return ret

    def parse_existing_colous(self):
        ret = {}
        for file in self.iter_scope_files():
            xml = et.parse(file)
            root = xml.getroot()
            for element in root.findall('scope'):
                print('name', element.attrib['name'])
                patterns = element.attrib['pattern'].split('||')
                patterns = set((x.rstrip('/*') for x in patterns))
                patterns = [y[2] for y in (x.partition(':') for x in patterns)]

                for pattern in patterns:
                    ret[pattern] = self.remove_project_name(element.attrib['name'])
        return ret

    def remove_project_name(self, s):
        return s.replace(f'{self.name}_', '')

    def make_yaml_from_project(self):
        """make yaml from project"""
        colours = self.parse_existing_files()
        file_colors = self.parse_existing_colous()

        new_file_colors = {}
        new_file_colors[None] = file_colors[self.name]
        del file_colors[self.name]
        for k, v in sorted(file_colors.items()):
            new_file_colors[k] = v
        file_colors = new_file_colors

        def tr(s):
            lines = s.split('\n')
            for i, line in enumerate(lines[1:], start=1):
                if (not line.startswith(' ')) and i < len(lines) - 1:
                    lines[i] = f'\n{line}'
                else:
                    lines[i] = line.replace("!!null '': ", "~: ")
            return '\n'.join(lines)

        d = {'colors': colours, 'items': file_colors}
        yaml = YAML()
        with open('output.yml', 'w') as outfile:
            yaml.dump(d, stream=outfile, transform=tr)

    def iter_scope_files(self):
        for file in (self.idea_dir / 'scopes').iterdir():
            if file.is_file():
                yield file


class Scope:
    def __init__(self, name, project, paths):
        self.patterns = []
        self.name = "charmer_{}".format(name)
        # Remove project from here and maybe add scopes to the project
        self.project = project
        self.xml = """<component name="DependencyValidationManager">
      <scope name="{name}" pattern="{pattern}" />
</component>"""
        self.special = False
        for path in paths:
            self.add_entry(path)

    def add_entry(self, path):
        if isinstance(path, Path):
            rel_path = path.relative_to(self.project.root)
            if str(rel_path).startswith(".."):
                print("Folder not inside the project: {}".format(rel_path))
        else:
            rel_path = path
        self._add_pattern(rel_path)

    def _add_pattern(self, rel_path):
        pattern = "file[{project_name}]:{path}".format(
            project_name=self.project.name, path=rel_path
        )
        self.patterns.append(pattern)
        if isinstance(rel_path, str) or rel_path.is_dir():
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


@click.group(
    'charmer',
    help='Add colour to the files and folders in your PyCharm project '
         'using the specified CONFIG'
)
@click.argument('config', type=click.Path())
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj['app'] = Charmer(config)


@cli.command(help='Generate the pycharm xml configs')
@click.pass_context
def charm(ctx):
    ctx.obj['app'].prepare_scopes()


@cli.command(help='Check the config file')
@click.pass_context
def check(ctx):
    ctx.obj['app'].check_config()


if __name__ == "__main__":
    cli(obj={})
