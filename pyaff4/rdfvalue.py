# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.

"""RDF Values are responsible for serialization."""
import urlparse
import rdflib
import urllib

import posixpath

from pyaff4 import registry

# pylint: disable=protected-access


class RDFValue(object):
    datatype = ""

    def __init__(self, initializer=None):
        self.Set(initializer)

    def GetRaptorTerm(self):
        return rdflib.Literal(self.SerializeToString(),
                              datatype=self.datatype)

    def SerializeToString(self):
        return ""

    def UnSerializeFromString(self, string):
        raise NotImplementedError

    def Set(self, string):
        raise NotImplementedError

    def __str__(self):
        return self.SerializeToString()

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.SerializeToString())


class RDFBytes(RDFValue):
    value = ""
    datatype = rdflib.XSD.hexBinary

    def SerializeToString(self):
        return self.value.encode("hex")

    def UnSerializeFromString(self, string):
        self.Set(string.decode("hex"))

    def Set(self, data):
        self.value = data

    def __eq__(self, other):
        if isinstance(other, RDFBytes):
            return self.value == other.value


class XSDString(RDFValue):
    datatype = rdflib.XSD.string

    def SerializeToString(self):
        return self.value.encode("utf8")

    def UnSerializeFromString(self, string):
        self.Set(string.decode("utf8"))

    def Set(self, data):
        self.value = unicode(data)

    def __unicode__(self):
        return unicode(self.value)


class XSDInteger(RDFValue):
    datatype = rdflib.XSD.integer

    def SerializeToString(self):
        return str(self.value)

    def UnSerializeFromString(self, string):
        self.Set(int(string))

    def Set(self, data):
        self.value = int(data)

    def __eq__(self, other):
        if isinstance(other, XSDInteger):
            return self.value == other.value
        return self.value == other

    def __int__(self):
        return self.value


class URN(RDFValue):

    @classmethod
    def FromFileName(cls, filename):
        return cls("file:" + urllib.pathname2url(filename))

    @classmethod
    def NewURNFromFilename(cls, filename):
        return cls("file:" + urllib.pathname2url(filename))

    def ToFilename(self):
        components = self.Parse()
        if components.scheme == "file":
            return components.path

    def GetRaptorTerm(self):
        return rdflib.URIRef(self.SerializeToString())

    def SerializeToString(self):
        components = self.Parse()
        return urlparse.urlunparse(components)

    def UnSerializeFromString(self, string):
        self.Set(int(string))

    def Set(self, data):
        if isinstance(data, URN):
            self.value = data.value
        else:
            self.value = str(data)

    def Parse(self):
        components = urlparse.urlparse(self.value)
        normalized_path = posixpath.normpath(components.path)
        if normalized_path == ".":
            normalized_path = ""

        components = components._replace(path=normalized_path)
        if not components.scheme:
            components = components._replace(scheme="file")

        return components

    def Scheme(self):
        components = self.Parse()
        return components.scheme

    def Append(self, component, quote=True):
        components = self.Parse()
        if quote:
            component = urllib.quote(component)

        new_path = posixpath.normpath(posixpath.join(
            components.path, component))

        components = components._replace(path=new_path)

        return URN(urlparse.urlunparse(components))

    def RelativePath(self, urn):
        value = self.SerializeToString()
        urn_value = str(urn)
        if urn_value.startswith(value):
            return urn_value[len(value):]

    def __repr__(self):
        return "<%s>" % self.SerializeToString()


registry.RDF_TYPE_MAP.update({
    rdflib.XSD.hexBinary: RDFBytes,
    rdflib.XSD.string: XSDString,
    rdflib.XSD.integer: XSDInteger,
    rdflib.XSD.int: XSDInteger,
    rdflib.XSD.long: XSDInteger,
    })
