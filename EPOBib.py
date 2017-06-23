# import pdb; pdb.set_trace()

import DataImport
from pprint import pprint

from datetime import datetime

from lxml import etree
import functools
from pymaybe import maybe

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

from multiprocessing import Process

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

#########
# parse #
#########

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

def classifications(bibliographic):
	ipcr = bibliographic.find('{http://www.epo.org/exchange}classifications-ipcr')
	ipcrs = fmap(lambda x: x.find('text'), ipcr.findall('classification-ipcr'))
	return fmap(buildclassifications, ipcrs)

def buildeachcitation(citations, data):
	doc = data.get('doc')
	dnum = data.get('dnum', '')
	dnumtype = data.get('dnum-type', '')
	docid = doc.attrib.get('doc-id', '')
	country = maybe(doc).find('country').text.or_else('')
	docnumber = maybe(doc).find('doc-number').text.or_else('')
	kind = maybe(doc).find('kind').text.or_else('')
	name = maybe(doc).find('name').text.or_else('')
	date = maybe(doc).find('date').text.or_else('')
	citation = { 'dnum': dnum, 'dnum-type': dnumtype, 'doc-id': docid, 'country': country, 'doc-number': docnumber, 'kind': kind, 'name': name, 'date': date }
	return citations.append(citation)

def buildcitations(citations):
	return lambda data: buildeachcitation(citations, data)

def citations(bibliographic):
	citations = []
	referencescited = bibliographic.findall('{http://www.epo.org/exchange}references-cited')
	citation = fmap(lambda x: x.findall('{http://www.epo.org/exchange}citation'), referencescited)
	patcit = fmap(lambda x: fmap(lambda y: y.findall('patcit'), x), citation)
	documentid = fmap(lambda x: fmap(lambda y: fmap(lambda z: fmap(lambda doc: { 'doc': doc, 'dnum': z.attrib.get('dnum', ''), 'dnum-type': z.attrib.get('dnum-type', '') }, z.findall('document-id')), y), x), patcit)
	fmap(lambda x: fmap(lambda y: fmap(lambda z: fmap(buildcitations(citations), z), y), x), documentid)
	return citations

def inventor(format, sequence, inv):
	if format == 'docdb':
		return { 'name': maybe(maybe(inv.find('{http://www.epo.org/exchange}inventor-name')).find('name')).text, 'residence': maybe(maybe(inv.find('residence')).find('country')).text, 'sequence': sequence }
	elif format == 'docdba':
	  return { 'name': maybe(maybe(inv.find('{http://www.epo.org/exchange}inventor-name')).find('name')).text, 'sequence': sequence }
	else:
	  return {}

def applicant(format, sequence, app):
	if format == 'docdb':
		return { 'name': maybe(maybe(app.find('{http://www.epo.org/exchange}applicant-name')).find('name')).text, 'residence': maybe(maybe(app.find('residence')).find('country')).text, 'sequence': sequence }
	elif format == 'docdba':
	  return { 'name': maybe(maybe(app.find('{http://www.epo.org/exchange}applicant-name')).find('name')).text, 'sequence': sequence }
	else:
	  return {}	  

def partyreducer(acc, val, doc):
	format = val.attrib.get('data-format', '')
	acc[format] = doc(format, val.attrib.get('sequence', ''), val)
	return acc

def partyinventor(inventors):
	return fcreduce(lambda acc, val: partyreducer(acc, val, inventor), {})(inventors)

def partyapplicant(applicants):
	return fcreduce(lambda acc, val: partyreducer(acc, val, applicant), {})(applicants)

def partyinventors(inventors):
	return fmap(lambda x: partyinventor(x.findall('{http://www.epo.org/exchange}inventor')), inventors)

def partyapplicants(applicants):
	return fmap(lambda x: partyapplicant(x.findall('{http://www.epo.org/exchange}applicant')), applicants)

def parties(bibliographic):
	party = bibliographic.find('{http://www.epo.org/exchange}parties')
	applicants = maybe(party).findall('{http://www.epo.org/exchange}applicants').or_else([])
	inventors = maybe(party).findall('{http://www.epo.org/exchange}inventors').or_else([])
	return { 'applicants': partyapplicants(applicants), 'inventors': partyinventors(inventors) }

def reference(format, doc):
	if format == 'docdb':
		return { 'country': doc.find('country').text, 'doc-number': doc.find('doc-number').text, 'kind': doc.find('kind').text }
	elif format == 'epodoc':
	  return { 'doc-number': doc.find('doc-number').text }
	else:
	  return {}  

def applicationreferencesreducer(acc, val):
	format = val.attrib.get('data-format', '')
	representatitve = val.attrib.get('is-representative', '')
	ref = reference(format, val.find('document-id'))
	ref['is-representative'] = representatitve
	acc[format] = ref
	return acc

def applicationreferences(references):
	return fcreduce(applicationreferencesreducer, {})(references)	  	

def publicationreferencesreducer(acc, val):
	format = val.attrib.get('data-format', '')
	sequence = val.attrib.get('sequence', '')
	ref = reference(format, val.find('document-id'))
	x = acc.get(format, {})
	x[sequence] = ref
	acc[format] = x 
	return acc

def publicationreferences(references):
	return fcreduce(publicationreferencesreducer, {})(references)

def familymembers(family):
  members = maybe(family).findall('{http://www.epo.org/exchange}family-member').or_else([])
  return fmap(lambda x: { 'application-references': applicationreferences(x.findall('{http://www.epo.org/exchange}application-reference')), 'publication-references': publicationreferences(x.findall('{http://www.epo.org/exchange}publication-reference')) }, members)

# compose:
#	fcfilter(lambda x: bool(x))
# fcreduce... put into structure...

def parse(tree, callback):
	doc_attrs = tree.attrib
	bibliographic = tree.find('{http://www.epo.org/exchange}bibliographic-data')
	family = tree.find('{http://www.epo.org/exchange}patent-family')
	title = bibliographic.findall('{http://www.epo.org/exchange}invention-title')
	callback({
	  'title': fmap(lambda x: { 'title': x.text, 'lang': x.attrib.get('lang', ''), 'data-format': x.attrib.get('data-format', '') }, title),
	  'country': doc_attrs.get('country', ''),
	  'status': doc_attrs.get('status', ''),
	  # identical to <doc-number> in <publication-reference> (http://documents.epo.org/projects/babylon/eponet.nsf/0/6266D96FAA2D3E6BC1257F1B00398241/$File/T09.01_ST36_User_Documentation_vs_2.5.7_en.pdf)
	  'doc-number': doc_attrs.get('doc-number', ''),
	  # identical to <kind> in <publication-reference> (http://documents.epo.org/projects/babylon/eponet.nsf/0/6266D96FAA2D3E6BC1257F1B00398241/$File/T09.01_ST36_User_Documentation_vs_2.5.7_en.pdf)
	  'kind': doc_attrs.get('kind', ''),
	  # 5.3.1. Attribute "doc-id" (http://documents.epo.org/projects/babylon/eponet.nsf/0/6266D96FAA2D3E6BC1257F1B00398241/$File/T09.01_ST36_User_Documentation_vs_2.5.7_en.pdf)
	  'doc-id': doc_attrs.get('doc-id', ''),
	  'date-publ': doc_attrs.get('date-publ', ''),
	  'family-id': doc_attrs.get('family-id', ''),
	  'family-members': familymembers(family),
	  'parties': parties(bibliographic),
	  'citations': citations(bibliographic),
	  'classifications': classifications(bibliographic)
	})   

def parsedocument(callback):
	return lambda tree: spawn(parse, tree, callback)

def parsedocuments(xml_file, each_callback): 
	docs = tree(xml_file).xpath('//*[local-name()="exchange-document"]')
	return fcmap(parsedocument(each_callback))(docs)

##############
# processing #
############## 		

def to_database(metadata):
	print('------------------------------------------------')
	pprint(metadata)

	doc_number = metadata['doc-number']
	kind = metadata['kind']
	date_publ = metadata['date-publ']
	status = metadata['status']
	country = metadata['country']
	title = metadata['title'][0].get('title', '') if len(metadata['title']) > 0 else '' 

	family_id = metadata['family-id']
	family_members = metadata['family-members']
	citations = metadata['citations']	
	classifications = metadata['classifications']

	DataImport.create_document('Bibliographic', '?', '', doc_number, kind, date_publ, status, country, title, '', '', '', '')

	for citation in citations:
		DataImport.add_citation(doc_number, citation.get('doc-number', ''), citation.get('country', ''), citation.get('kind', ''), date_publ, '', '', '')

	for classification in classifications:
		DataImport.add_classification(doc_number, classification.get('section', ''), classification.get('class', ''), classification.get('subclass', ''), classification.get('main-group', ''), classification.get('subgroup', ''), date_publ, '', '', '')

	#EPODataImport.add_family_member('Bibliographic', family_id, doc_number, country, kind)

	for member in family_members:
		application = member['application-references']['docdb']
		DataImport.add_family_member('FamilyApplication', family_id, application['doc-number'], application['country'], application['kind'], application['is-representative'])

		publication = member['publication-references']['docdb']
		for sequence, document in publication.items():
			DataImport.add_family_member('FamilyPublication', family_id, document['doc-number'], application['country'], application['kind'])

	print('------------------------------------------------')
	print('\n')

def _run(xml_file, each_callback): 
	parsedocuments(xml_file, each_callback)

def _run_all(index_path, dtd_path, callback_each):
	print('TODO: implement _run_all')

def run(file = None):
	if file:
		_run(file, to_database)
	else:
		_run_all('index.xml', './DTDS/ep-patent-document-v1-5.dtd', to_database)
