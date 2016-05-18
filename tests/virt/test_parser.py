from vadvisor.virt.parser import parse_domain_xml
import json


def test_xml():
    result = parse_domain_xml(open("tests/virt/vm.xml").read())
    assert result == json.loads(open("tests/virt/vm.json").read())
