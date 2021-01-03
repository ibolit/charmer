import pytest

from bobros.main import Project


@pytest.mark.skip
def test_project():
    p = Project()
    ret = p.parse_existing_files()
    expected = {
        'Problems': 'Rose',
        'Non-Project Files': 'eaeaea',
        'charmer_one': 'ff9922',
        'charmer__home': 'ae9eff',
        'charmer.egg-info': 'cee1ff',
        'charmer': 'ffcece',
        'setup.py': 'ffe5ce',
        'dark.yml~': 'fffbce',
        'config.yml': 'e4ffce'}
    assert expected == ret

@pytest.mark.skip()
def test_file_colours():
    p = Project()
    ret = p.parse_existing_colous()
    print(ret)


def test_gen_yaml():
    p = Project()
    p.make_yaml_from_project()


