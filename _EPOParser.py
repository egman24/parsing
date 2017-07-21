from lxml import etree
import os
import zipfile
from shutil import copyfile
import datetime
import functools


def fmap(fn, coll):
    return functools.reduce(lambda acc, val: acc + [fn(val)], coll, [])


def ffilter(predicate_fn, coll):
    return functools.reduce(lambda acc, val: (acc + [val]) if predicate_fn(val) else acc, coll, [])


def fcreduce(fn, acc):
    return lambda coll: functools.reduce(fn, coll, acc)


def fcmap(fn):
    return lambda coll: functools.reduce(lambda acc, val: acc + [fn(val)], coll, [])


def fcfilter(predicate_fn):
    return lambda coll: functools.reduce(lambda acc, val: (acc + [val]) if predicate_fn(val) else acc, coll, [])


def fzip(coll1, coll2):
    return list(zip(coll1, coll2))


def fcompose(*functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)

###########
# helpers #
###########


def marker(id):
    return id + '-parsecomplete'

# from_element :: markup | attrib | text -> Element -> {} | String


def from_element(info):
    if info == 'markup':
        return lambda el: etree.tostring(el, encoding='unicode')
    else:
        return lambda el: getattr(el, info)

# tree :: String -> Tree


def tree(filename):
    return etree.parse(filename, etree.XMLParser(encoding='utf-8', recover=True, attribute_defaults=True, load_dtd=True))
    # return etree.parse(filename, etree.XMLParser(encoding='utf-8', recover=True, dtd_validation=True))

# get_file_info :: String -> [(filename, file-location)]


def get_file_info(index_filename):
    return fzip(
        fmap(from_element('text'), get_element(
            tree(index_filename), '//filename')),
        fmap(from_element('text'), get_element(
            tree(index_filename), '//file-location'))
    )

# get_element :: Tree, xpath -> [Element]


def get_element(tree, element_path):
    return tree.xpath(element_path)

# get_metadata :: Tree, xpath, attrib | text, String -> [] | [(alias, tag, {} | String)]


def get_metadata(tree, element_path, info, alias):
    return fmap(lambda el: (alias, el.tag, from_element(info)(el)), get_element(tree, element_path))


def format(acc, result_set):
    alias = result_set[0][0]
    if len(result_set) == 1:
        acc[alias] = result_set[0][2]
    else:
        attrs = [attr for *_, attr in result_set]
        acc[alias] = attrs
    return acc

# parse :: Tree, [[ xpath, attrib | text, String ]] -> { alias: {} | String) }


def parse(tree, fields):
    return fcompose(
        fcreduce(format, {}),
        fcfilter(lambda x: bool(x)),
        fcmap(lambda field: get_metadata(tree, field[0], field[1], field[2]))
    )(fields)

##############
# processing #
##############


def process(fields, state, callback, xml_file, archive_file):
    if not os.path.isfile(marker(xml_file)):

        zipfile.ZipFile(archive_file, "r").extract(xml_file)

        # add validation/testing

        metadata = parse(tree(xml_file), fields())

        callback(metadata)

        # gives us a durable state if the script breaks and reruns
        completefile = open(marker(xml_file), "w")
        completefile.write(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # gives us a final built object for logging/reporting,
        # may not want if it is too large in memory!
        state[archive_file] = metadata

        os.remove(xml_file)


def traverse(file_info, dtd_path, fields, state, callback):
    initial_path = os.getcwd()
    work_path = file_info[1].replace('\\', '/')[1:]
    archive_file = file_info[0]
    xml_file = file_info[0].replace('zip', 'xml')

    copyfile(dtd_path, work_path + '/ep-patent-document-v1-5.dtd')

    os.chdir(work_path)
    # print(os.getcwd())
    process(fields, state, callback, xml_file, archive_file)
    os.chdir(initial_path)


def fields():
    return [
        # kind code, id, doc-number, country
        ['//ep-patent-document', 'attrib', 'document'],
        ['//B541[text()="en"]/following-sibling::B542[1]', 'text', 'title'],
        ['//abstract/p', 'markup', 'abstract'],
        ['//B220/date', 'text', 'filedate'],
        ['//B405/date', 'text', 'issuedate'],
        ['//B320/date', 'text', 'prioritydate'],
        #['//patcit/document-id/doc-number', 'text', 'citations'],
        ['//description//patcit', 'attrib', 'citations']
    ]

# ✓ Title
# ✓ Abstract
# * Claims
# * Descriptions
# * “Publication number” (published=US app; granted=US/international patent)
# ✓ Date
#   ✓ File date (American patents)
#   ✓ Issue date (when it is made public)
#   ✓ Priority date (maybe only American patents)
# * Inventors
# * Assignees
# * Classification(s)
# ✓ Kind
# ✓ Country
# ✓ Citations (patcit)
# * Family Id


def run(index_path, dtd_path, fields, state, callback_each, callback_all):
    for file_info in get_file_info(index_path):
        traverse(file_info, dtd_path, fields, state, callback_each)
    callback_all(state)

#########
# TODO: #
#########

# https://github.com/egman24/coshx-python/pull/1

# 20170602165016 this parser only handles fulltext documents, not bibliographic/backfile

# https://github.com/mismcam/doors/blob/docker/apache/app/doors/scripts/updates/run_update.py#L151

#################
# use and notes #
#################

# the family id and some other data is in backfile/bibliographic, need the combination of both


'''
? --> 
EPO dir --> 
parse & transform & validate & cleanup (what triggers it to begin?) --> 
kafka (document by document) --> 
database
'''

# import EPOParser
# from pprint import pprint

# EPOParser.run('index.xml', EPOParser.fields, {}, lambda x: x, lambda x: x)
# EPOParser.run('index.xml', EPOParser.fields, {}, pprint, pprint)
# EPOParser.run('index.xml', EPOParser.fields, {}, toQueue, cleanup)

# metadata per document

'''
[
  ('ep-patent-document', 'ep-patent-document', {'id': 'EP15754492A1', 'file': '15754492.5', 'lang': 'en', 'country': 'EP', 'doc-number': '3111592', 'kind': 'A1', 'date-publ': '20170104', 'status': 'n', 'dtd-version': 'ep-patent-document-v1-5'}), 
  ('nametocallit', 'B001EP', 'ATBECHDEDKESFRGBGRITLILUNLSEMCPTIESILTLVFIROMKCYALTRBGCZEEHUPLSKBAHRIS..MTNORSMESM..................')
]
'''

# toQueue :: metadata -> ()
# sideeffect of sending to queue, maybe logging print for verbosity?

# capture doc id globally and state of document (kind code)... provide with each payload

# no webservice to just pull xml programatically, need the filesystem dirs and unzips?
# if needed, which part/parts should be threaded? the traversal? first get all paths, then spawn unzip(parse) for each


# parts that can be parallelized, threaded?
# processing/callbacks that can be sent IN to change the behavior at the callsite
# ...

# error handling along the way, duplicate checking, state checking (add or update)
