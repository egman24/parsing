# import pdb; pdb.set_trace()

import DataImport
import functools
import os
import zipfile

from datetime import datetime
from lxml import etree
from multiprocessing import Process
from pprint import pprint
from pymaybe import maybe
from shutil import copyfile


def fmap(fn, coll):
  return functools.reduce(
    lambda acc, val: acc + [fn(val)], coll, []
  )


def ffilter(predicate_fn, coll):
  return functools.reduce(
    lambda acc, val: (acc + [val]) if predicate_fn(val) else acc, coll, []
  )


def fcreduce(fn, acc):
  return lambda coll: functools.reduce(fn, coll, acc)


def fcmap(fn):
  return lambda coll: functools.reduce(
    lambda acc, val: acc + [fn(val)], coll, []
  )


def fcfilter(predicate_fn):
  return lambda coll: functools.reduce(
    lambda acc, val: (acc + [val]) if predicate_fn(val) else acc, coll, []
  )


def fzip(coll1, coll2):
  return list(zip(coll1, coll2))


def fcompose(*functions):
  return functools.reduce(
    lambda f, g: lambda x: f(g(x)), functions, lambda x: x
  )  


def spawn(parse, tree, callback): 
  proc = Process(target=parse, args=(tree, callback))
  proc.start()
  proc.join()

###########
# helpers #   
###########

# tree :: String -> Tree
def tree(filename):
  return etree.parse(filename, etree.XMLParser(encoding='utf-8', recover=True, attribute_defaults=True, load_dtd=True))
  #return etree.parse(filename, etree.XMLParser(encoding='utf-8', recover=True, dtd_validation=True))

def marker(id):
  return id + '-parsecomplete'  

# from_element :: markup | attrib | text -> Element -> {} | String
def from_element(info):
  return lambda el: getattr(el, info)

# get_element :: Tree, xpath -> [Element]
def get_element(tree, element_path):
  return tree.xpath(element_path)

# get_file_info :: String -> [(filename, file-location)]
def get_file_info(index_filename):
  return fzip(
    fmap(from_element('text'), get_element(tree(index_filename), '//filename')),
    fmap(from_element('text'), get_element(tree(index_filename), '//file-location'))
  )

#########
# parse #
#########

def buildassignees(assignee):
	return {
	  'name': maybe(assignee).find('snm').text.or_else(''),
	  'epo-number': maybe(assignee).find('iid').text.or_else(''),
	  'reference': maybe(assignee).find('irf').text.or_else(''),
	  'cross-reference': maybe(assignee).find('syn').text.or_else('')
	}

def assignees(doc):
	applicants = doc.xpath('//B710/B711')
	grantees = doc.xpath('//B730/B731')
	return fmap(buildassignees, (applicants + grantees))

def buildclassifications(classification):
  # From publication week 01-2006, 
  # we will only use tag B510EP for the new (IPCR) coding 
  return { 
    'section': classification.text[0].strip(), 
    'class': classification.text[1:3].strip(),
    'subclass': classification.text[3].strip(),
    'main-group': classification.text[4:8].strip(),
    'subgroup': classification.text[9:15].strip(),
    'ipc-version-indicator': classification.text[19:27].strip(), 
    'classification-level': classification.text[27].strip(),
    'symbol-position': classification.text[28].strip(),
    'classification-value': classification.text[29].strip(),
    'action-date': classification.text[30:38].strip(),
    'classification-status': classification.text[38].strip(),
    'classification-data-source': classification.text[39].strip(),
    'generating-office-country': classification.text[40:42].strip()
  }

def classifications(doc):
	codes = ffilter(lambda x: len(x.text) > 41, doc.xpath('//classification-ipcr/text'))
	return fmap(buildclassifications, codes)

def buildcitations(patcit):
  return { 
    'dnum': patcit.attrib.get('dnum', ''), 
    'country': maybe(patcit).find('document-id').find('country').text.or_else(''),
    'doc-number': maybe(patcit).find('document-id').find('doc-number').text.or_else(''), 
    'kind': maybe(patcit).find('document-id').find('kind').text.or_else('')   
  }

def citations(doc):
  patcits = doc.xpath('//ep-reference-list/p/ul/li/patcit')
  return fmap(buildcitations, patcits)

def abstract(sections):
  return ''.join(fmap(lambda section: etree.tostring(section, encoding='unicode'), sections))

def parse(tree, callback):
  doc_attrs = tree.attrib
  callback({
    'dnum': doc_attrs.get('id', ''),
    'country': doc_attrs.get('country', ''),
    'doc-number': doc_attrs.get('doc-number', ''),
    'kind': doc_attrs.get('kind', ''),
    'date-publ': doc_attrs.get('date-publ', ''),
    'status': doc_attrs.get('status', ''),
    'abstract': abstract(tree.xpath('//abstract/p')),
    'date-file': tree.xpath('//B220/date')[0].text if len(tree.xpath('//B220/date')) > 0 else '',
    'date-issue': tree.xpath('//B405/date')[0].text if len(tree.xpath('//B405/date')) > 0 else '',
    'date-priority': tree.xpath('//B320/date')[0].text if len(tree.xpath('//B320/date')) > 0 else '',
    'citations': citations(tree),
    'classifications': classifications(tree),
    'assignees': assignees(tree)
  })   

def parsedocument(callback):
  return lambda tree: spawn(parse, tree, callback)

def parsedocuments(xml_file, each_callback): 
  docs = tree(xml_file).xpath('//ep-patent-document')
  return fcmap(parsedocument(each_callback))(docs)

##############
# processing #
##############   

def to_database(metadata):
  print('------------------------------------------------')
  pprint(metadata)

  dnum = metadata['dnum']
  doc_number = metadata['doc-number']
  kind = metadata['kind']
  date_publ = metadata['date-publ']
  status = metadata['status']
  country = metadata['country']
  abstract = metadata['abstract']
  date_file = metadata['date-file']
  date_issue = metadata['date-issue']
  date_priority = metadata['date-priority']
  citations = metadata['citations']
  classifications = metadata['classifications']
  assignees = metadata['assignees']

  DataImport.create_document('FullText', '?', dnum, doc_number, kind, date_publ, status, country, '', abstract, date_file, date_issue, date_priority)

  for citation in citations:
    DataImport.add_citation(doc_number, citation.get('doc-number', ''), citation.get('country', ''), citation.get('kind', ''), date_publ, date_file, date_issue, date_priority)

  for classification in classifications:
    DataImport.add_classification(doc_number, classification.get('section', ''), classification.get('class', ''), classification.get('subclass', ''), classification.get('main-group', ''), classification.get('subgroup', ''), date_publ, date_file, date_issue, date_priority)

  for assignee in assignees:
    DataImport.add_assignee(doc_number, assignee.get('name', ''), assignee.get('epo-number', ''), assignee.get('reference', ''), assignee.get('cross-reference', ''), date_publ, date_file, date_issue, date_priority)

  print('------------------------------------------------')
  print('\n') 

def process(callback, xml_file, archive_file):
  if not os.path.isfile(marker(xml_file)):

    zipfile.ZipFile(archive_file, "r").extract(xml_file)
    
    # add validation/testing
    parsedocuments(xml_file, callback)
    
    # gives us a durable state if the script breaks and reruns
    completefile = open(marker(xml_file),"w") 
    completefile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    os.remove(xml_file)  

def traverse(file_info, dtd_info, callback):
  initial_path = os.getcwd()
  work_path = file_info[1].replace('\\', '/')[1:]
  archive_file = file_info[0]
  xml_file = file_info[0].replace('zip', 'xml')
 
  copyfile('./DTDS/' + dtd_info, work_path + '/' + dtd_info)

  os.chdir(work_path)
  #print(os.getcwd())
  process(callback, xml_file, archive_file)
  os.chdir(initial_path) 

def _run(xml_file, callback):
  parsedocument(xml_file, callback)

def _run_all(index_path, dtd_file, callback_each):
  for file_info in get_file_info(index_path):
    traverse(file_info, dtd_file, callback_each) 

def run(file = None):
  if file:
    _run(file, to_database)
  else:
    _run_all('index.xml', 'ep-patent-document-v1-5.dtd', to_database)  