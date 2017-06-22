# import pdb; pdb.set_trace()

import DataImport
from pprint import pprint

from lxml import etree
import itertools
import functools
from pymaybe import maybe

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

from multiprocessing import Process

def spawn(parse, tree, callback): 
  proc = Process(target=parse, args=(tree, callback))
  proc.start()
  proc.join()

###########
# helpers # 	
###########

# tree :: String -> Tree
def tree(xmlstring):
  return etree.fromstring(xmlstring, etree.XMLParser(encoding='utf-8', recover=True, attribute_defaults=True, load_dtd=True))
  #return etree.parse(filename, etree.XMLParser(encoding='utf-8', recover=True, dtd_validation=True))

#########
# parse #
#########

def description(descriptionelement):
	return etree.tostring(descriptionelement, encoding='unicode')

def buildclaim(claim):
	return claim.find('claim-text').text if claim.find('claim-text') is not None else ''

def claims(claimelements):
	return fmap(buildclaim, claimelements)

def buildcitation(patcit):
	return {
	  'country': patcit.find('document-id').find('country').text if patcit.find('document-id').find('country') is not None else '',
	  'doc-number': patcit.find('document-id').find('doc-number').text if patcit.find('document-id').find('doc-number') is not None else '',
	  'kind': patcit.find('document-id').find('kind').text if patcit.find('document-id').find('kind') is not None else '',
	  'name': patcit.find('document-id').find('name').text if patcit.find('document-id').find('name') is not None else '',
	  'date': patcit.find('document-id').find('date').text if patcit.find('document-id').find('date') is not None else '',
	}

def citations(citationelements):
  return fmap(buildcitation, citationelements)

def buildassigneeaddress(address):
	return {
	  'city': address.find('city').text if address.find('city') is not None else '',
	  'state': address.find('state').text if address.find('state') is not None else '',
	  'country': address.find('country').text if address.find('country') is not None else ''
	}

def buildassignees(assignee):
	if assignee.find('addressbook') is not None:
		return {
		  'orgname': assignee.find('addressbook').find('orgname').text if assignee.find('addressbook').find('orgname') is not None else '',
		  'role': assignee.find('addressbook').find('role').text if assignee.find('addressbook').find('role') is not None else '',
		  'address': buildassigneeaddress(assignee.find('addressbook').find('address')) if assignee.find('addressbook').find('address') is not None else ''
		}
	else:	
		return {
		  'orgname': assignee.find('orgname').text if assignee.find('orgname') is not None else '',
		  'role': assignee.find('role').text if assignee.find('role') is not None else ''
		}

def assignees(assigneeelements):
	return fmap(buildassignees, assigneeelements)

def partiesapplicants(applicants):
  return applicants		

def partiesinventors(inventors):
  return inventors

def partiesagents(agents):
  return agents  

def parties(partieselement):
	return { 
	  'applicants': partieselement.find('us-applicants'), 
	  'inventors': partieselement.find('inventors'), 
	  'agents': partieselement.find('agents') 
	}

def abstract(sections):
	return ''.join(fmap(lambda section: etree.tostring(section, encoding='unicode'), sections))

def publication_reference(reference):
  return {
    'country': reference.find('document-id').find('country').text if reference.find('document-id').find('country') is not None else '',
    'doc-number': reference.find('document-id').find('doc-number').text if reference.find('document-id').find('doc-number') is not None else '',
    'kind': reference.find('document-id').find('kind').text if reference.find('document-id').find('kind') is not None else '',
    'date': reference.find('document-id').find('date').text if reference.find('document-id').find('date') is not None else '',
  }

def application_reference(reference):
  return {
    'appl-type': reference.attrib.get('appl-type', ''),
    'country': reference.find('document-id').find('country').text if reference.find('document-id').find('country') is not None else '',
    'doc-number': reference.find('document-id').find('doc-number').text if reference.find('document-id').find('doc-number') is not None else '',
    'date': reference.find('document-id').find('date').text if reference.find('document-id').find('date') is not None else '',
  }

def parse(tree, callback):
	doc_attrs = tree.xpath('/*[starts-with(name(), "us-patent-")]')[0].attrib
	callback({
	  'publication-reference': publication_reference(tree.xpath('//publication-reference')[0]),
	  'application-reference': application_reference(tree.xpath('//application-reference')[0]),
	  'state': doc_attrs.get('id', ''),
	  'title': tree.xpath('//invention-title')[0].text,
	  'country': doc_attrs.get('country', ''),
	  'status': doc_attrs.get('status', ''),
	  'date-publ': doc_attrs.get('date-publ', ''),
	  'abstract': abstract(tree.xpath('//abstract/p')),
	  'series': tree.xpath('//us-application-series-code')[0].text,
	  'description': description(tree.xpath('//description')[0]),
	  'claims': claims(tree.xpath('//claim')),
	  'citations': citations(tree.xpath('//patcit')), # also //nplcit
	  'assignees': assignees(tree.xpath('//assignee')),
	  'parties': parties(tree.xpath('//us-parties')[0])
	})

def parsedocuments(filename, typeof, parser, callback):
  with open(filename, 'r') as file:
	  for key,group in itertools.groupby(file, lambda line: line.startswith('<?xml version="1.0" encoding="UTF-8"?>')):
		  if not key:
		  	tree = etree.fromstring(''.join(list(group)))
		  	spawn(parser, tree, callback(typeof))

##############
# processing #
############## 	

def to_database(typeof):
	return lambda metadata: _to_database(typeof, metadata)

def _to_database(typeof, metadata):
	print('------------------------------------------------')
	pprint(metadata)

	date_publ = metadata['date-publ']
	status = metadata['status']
	title = metadata['title']
	abstract = metadata['abstract']
	citations = metadata['citations']
	claims = metadata['claims']

	description = metadata['description']

	publication_reference = metadata['publication-reference']
	application_reference = metadata['application-reference']

	DataImport.create_us_document(typeof, 'publication', '', publication_reference.get('doc-number', ''), publication_reference.get('kind', ''), date_publ, status, publication_reference.get('country', ''), title, abstract, '', '', '', claims, description)
	#DataImport.create_document(typeof, 'application', '', application_reference.get('doc-number', ''), '', date_publ, status, application_reference.get('country', ''), title, abstract, '', '', '')

	for citation in citations:
		DataImport.add_citation(publication_reference.get('doc-number', ''), citation.get('doc-number', ''), citation.get('country', ''), citation.get('kind', ''), date_publ, '', '', '')
		DataImport.add_citation(application_reference.get('doc-number', ''), citation.get('doc-number', ''), citation.get('country', ''), citation.get('kind', ''), date_publ, '', '', '')

	print('------------------------------------------------')
	print('\n')

def run(filename, typeof):
	parsedocuments(filename, typeof, parse, to_database)

def run_bib(filename):
	run(filename, 'US_Bibliographic')

def run_full(filename):
	run(filename, 'US_Fulltext')	
