from xml.etree.ElementTree import XMLParser


class GuestXmlParser:

    int_tags = ["currentMemory", "memory"]
    int_attribs = ["index", "port", "startport", "vram"]

    def __init__(self):
        self.json = {}
        self.stack = [self.json]

    def start(self, tag, attrib):
        self.tag = tag
        for attr in self.int_attribs:
            if attrib.get(attr):
                attrib[attr] = int(attrib[attr])
        if tag == "devices":
            self.stack[-1][tag] = []
            self.stack.append(self.stack[-1][tag])
        elif tag == "emulator":
            self.stack[-2][tag] = attrib
            self.stack.append(attrib)
        elif isinstance(self.stack[-1], dict):
            self.stack[-1][tag] = attrib
            self.stack.append(attrib)
        else:
            device = {"family": tag}
            device.update(attrib)
            self.stack[-1].append(device)
            self.stack.append(device)

    def end(self, tag):
        self.stack.pop()

    def data(self, data):
        if data and data.strip():
            if self.tag in self.int_tags:
                self.stack[-1]["value"] = int(data)
            else:
                self.stack[-1]["value"] = data

    def close(self):
        return self.json


def parse_domain_xml(xml):
    target = GuestXmlParser()
    parser = XMLParser(target=target)
    parser.feed(xml)
    return parser.close()
