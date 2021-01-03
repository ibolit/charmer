#!/usr/bin/env python3
import re
from collections import defaultdict
from pathlib import Path

from click import echo, secho
from colour import Color
from ruamel.yaml import YAML
import click
from xml.etree import ElementTree as et


class Charmer:
    def __init__(self):
        self.project = Project()
        self.predefined_patterns = None

    def parse_config(self, config):
        with open(config) as infile:
            yaml = YAML()
            return yaml.load(infile)

    def check_config(self, config):
        config = self.parse_config(config)
        disk_items = [x.name for x in self.project.root.iterdir()]
        conf_items = config.get('items', {})
        if None in conf_items:
            conf_items[self.project.name] = None
            conf_items.pop(None, None)
            conf_items.pop('Problems', None)
            conf_items.pop('Non-Project Files', None)
        conf_items = list(conf_items.keys())

        missing_on_disk = set()

        for item in conf_items:
            if item not in disk_items:
                missing_on_disk.add(item)

        secho('Items in config and not on disk', fg='red', err=True)
        for i in missing_on_disk:
            echo(i)

    def prepare_scopes(self, config, theme=None):
        config = self.parse_config(config)
        file_colors = FileColors(self.project)
        colors = self.get_colors(config, theme)
        print(colors)
        ret = defaultdict(list)
        for file_path, color in config.get('items', {}).items():
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

    def get_colors(self, config, theme):
        has_themes = 'themes' in config
        if theme is not None and not has_themes:
            raise RuntimeError('Theme option provided, but config does NOT contain themes')
        if theme is None and has_themes:
            raise RuntimeError('Theme option NOT provided, but config contains themes')
        if theme:
            try:
                colors = config['themes'][theme]
            except KeyError:
                raise RuntimeError(f'{theme}: Theme not found in config')
        else:
            colors = config.get('colors', {})
        if 'default' not in colors:
            colors['default'] = 'ff5555'
        return colors

    def export(self, config):
        d = self.project.make_yaml_from_project()
        yaml = YAML()
        def tr(s):
            lines = s.split('\n')
            for i, line in enumerate(lines[1:], start=1):
                if (not line.startswith(' ')) and i < len(lines) - 1:
                    lines[i] = f'\n{line}'
                else:
                    lines[i] = line.replace("!!null '': ", "~: ")
            return '\n'.join(lines)

        with open(config, 'w') as outfile:
            yaml.dump(d, stream=outfile, transform=tr)


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

        return {'colors': colours, 'items': file_colors}

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
         'using the specified CONFIG.'
)
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['app'] = Charmer()


@cli.command(help='Generate the pycharm xml configs.')
@click.argument('config', type=click.Path())
@click.option('-t', '--theme', type=click.STRING, help='Which theme to use. Config must specify themes.')
@click.pass_context
def charm(ctx, config, theme):
    try:
        ctx.obj['app'].prepare_scopes(config, theme)
    except (KeyboardInterrupt, InterruptedError):
        raise
    except RuntimeError as e:
        echo('; '.join((str(x) for x in e.args)), err=True)


@cli.command(help='Check the config file')
@click.pass_context
@click.argument('config', type=click.Path())
def check(ctx, config):
    ctx.obj['app'].check_config(config)


@cli.command(help="Generate config file from project's xmls")
@click.pass_context
@click.argument('config', type=click.Path())
def export(ctx, config):
    ctx.obj['app'].export(config)


@cli.command(
    help='Generate hex colour values, same saturation and luminance, different hues. '
         'The hues are equally spaced.')
@click.argument('hex_color', type=click.STRING)
@click.option('--points', default=10, help='How many colour values to generate')
def make_colors(hex_color, points):
    c = Color(f'#{hex_color}')
    for i in range(points):
        hue = c.hue + i / points
        if hue > 1:
            hue = hue - 1
        cl = Color(hue=hue, saturation=c.saturation, luminance=c.luminance)
        echo(cl.hex_l[1:])


if __name__ == "__main__":
    cli(obj={})
