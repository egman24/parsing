# import pdb; pdb.set_trace()

import DataImport
import functools
import itertools
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
def tree(xmlstring):
    return etree.fromstring(xmlstring, etree.XMLParser(encoding='utf-8', recover=True, attribute_defaults=True, load_dtd=True))
    # return etree.parse(filename, etree.XMLParser(encoding='utf-8', recover=True, dtd_validation=True))

#########
# parse #
#########


def buildclassificationlocarno(element):
    classification = element.find('main-classification').text
    return {
        'class': classification[0:2],
        'subclass': classification[2:]
    }


def buildclassificationnational(element):
    classification = element.find('main-classification').text
    return {
        'class': classification[0:3].replace(' ', ''),
        'subclass': classification[3:].replace(' ', '')
    }


def buildcpctext(element):
    # TODO: if this is needed, find proper documentation
    classification = element.find('classification-cpc-text').text
    return {}


def buildclassificationipcrorcpc(element):
    return {
        'section': maybe(element).find('section').text.or_else(''),
        'class': maybe(element).find('class').text.or_else(''),
        'subclass': maybe(element).find('subclass').text.or_else(''),
        'main-group': maybe(element).find('main-group').text.or_else(''),
        'subgroup': maybe(element).find('subgroup').text.or_else(''),
        'ipc-version-indicator': maybe(element).find('ipc-version-indicator').find('date').text.or_else(''),
        'classification-level': maybe(element).find('classification-level').text.or_else(''),
        'symbol-position': maybe(element).find('symbol-position').text.or_else(''),
        'classification-value': maybe(element).find('classification-value').text.or_else(''),
        'action-date': maybe(element).find('action-date').find('date').text.or_else(''),
        'classification-status': maybe(element).find('classification-status').text.or_else(''),
        'classification-data-source': maybe(element).find('classification-data-source').text.or_else(''),
        'generating-office-country': maybe(element).find('generating-office').find('country').text.or_else('')
    }


def classificationlocarno(elements):
    return fmap(buildclassificationlocarno, elements)


def classificationnational(elements):
    return fmap(buildclassificationnational, elements)


def cpctext(elements):
    return fmap(buildcpctext, [])


def classificationipcrorcpc(elements):
    return fmap(buildclassificationipcrorcpc, elements)


def classifications(classification_locarno, classification_national, cpc_text, classification_ipcr, classification_cpc):
    return classificationlocarno(classification_locarno) + classificationnational(classification_national) + cpctext(cpc_text) + classificationipcrorcpc(classification_ipcr) + classificationipcrorcpc(classification_cpc)


def description(descriptionelements):
    return fmap(lambda desc: etree.tostring(desc, encoding='unicode'), descriptionelements)


def buildclaim(claim):
    return maybe(claim).find('claim-text').text.or_else('')


def claims(claimelements):
    return fmap(buildclaim, claimelements)


def buildcitation(patcit):
    return {
        'country': maybe(patcit).find('document-id').find('country').text.or_else(''),
        'doc-number': maybe(patcit).find('document-id').find('doc-number').text.or_else(''),
        'kind': maybe(patcit).find('document-id').find('kind').text.or_else(''),
        'name': maybe(patcit).find('document-id').find('name').text.or_else(''),
        'date': maybe(patcit).find('document-id').find('date').text.or_else('')
    }


def citations(citationelements):
    return fmap(buildcitation, citationelements)


def buildassigneeaddress(address):
    return {
        'city': maybe(address).find('city').text.or_else(''),
        'state': maybe(address).find('state').text.or_else(''),
        'country': maybe(address).find('country').text.or_else('')
    }


def buildassignees(assignee):
    if assignee.find('addressbook') is not None:
        return {
            'orgname': maybe(assignee).find('addressbook').find('orgname').text.or_else(''),
            'role': maybe(assignee).find('addressbook').find('role').text.or_else(''),
            'address': buildassigneeaddress(assignee.find('addressbook').find('address')) if assignee.find('addressbook').find('address') is not None else ''
        }
    else:
        return {
            'orgname': maybe(assignee).find('orgname').text.or_else(''),
            'role': maybe(assignee).find('role').text.or_else('')
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
        'applicants': partiesapplicants(partieselement.find('us-applicants')),
        'inventors': partieselement.find('inventors'),
        'agents': partieselement.find('agents')
    }


def abstract(sections):
    return ''.join(fmap(lambda section: etree.tostring(section, encoding='unicode'), sections))


def publication_reference(reference):
    return {
        'country': maybe(reference).find('document-id').find('country').text.or_else(''),
        'doc-number': maybe(reference).find('document-id').find('doc-number').text.or_else(''),
        'kind': maybe(reference).find('document-id').find('kind').text.or_else(''),
        'date': maybe(reference).find('document-id').find('date').text.or_else('')
    }


def application_reference(reference):
    return {
        'appl-type': reference.attrib.get('appl-type', ''),
        'country': maybe(reference).find('document-id').find('country').text.or_else(''),
        'doc-number': maybe(reference).find('document-id').find('doc-number').text.or_else(''),
        'date': maybe(reference).find('document-id').find('date').text.or_else(''),
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
        'description': maybe(description(tree.xpath('//description')))[0].or_else(''),
        'claims': claims(tree.xpath('//claim')),
        'citations': citations(tree.xpath('//patcit')),  # also //nplcit
        'assignees': assignees(tree.xpath('//assignee')),
        'parties': parties(tree.xpath('//us-parties')[0]),
        'classifications': classifications(
            tree.xpath('//classification-locarno'),
            tree.xpath('//classification-national'),
            tree.xpath('//classification-cpc-text'),
            tree.xpath('//classification-ipcr'),
            tree.xpath('//classification-cpc')
        )
    })


def parsedocuments(filename, typeof, parser, callback):
    with open(filename, 'r') as file:
        for key, group in itertools.groupby(file, lambda line: line.startswith('<?xml version="1.0" encoding="UTF-8"?>')):
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
    claims = metadata['claims']
    citations = metadata['citations']
    assignees = metadata['assignees']
    classifications = metadata['classifications']

    description = metadata['description']

    publication_reference = metadata['publication-reference']
    application_reference = metadata['application-reference']

    DataImport.create_us_document(typeof, 'publication', '', publication_reference.get('doc-number', ''), publication_reference.get(
        'kind', ''), date_publ, status, publication_reference.get('country', ''), title, abstract, '', '', '', claims, description)
    #DataImport.create_document(typeof, 'application', '', application_reference.get('doc-number', ''), '', date_publ, status, application_reference.get('country', ''), title, abstract, '', '', '')

    for citation in citations:
        DataImport.add_citation(publication_reference.get('doc-number', ''), citation.get(
            'doc-number', ''), citation.get('country', ''), citation.get('kind', ''), date_publ, '', '', '')
        DataImport.add_citation(application_reference.get('doc-number', ''), citation.get(
            'doc-number', ''), citation.get('country', ''), citation.get('kind', ''), date_publ, '', '', '')

    for assignee in assignees:
        # TODO: can we rely on assignees alone, or should we test and use parties/applicants if needed?
        DataImport.add_assignee(publication_reference.get(
            'doc-number', ''), assignee.get('orgname', ''), '', '', '', date_publ, '', '', '')
        DataImport.add_assignee(application_reference.get(
            'doc-number', ''), assignee.get('orgname', ''), '', '', '', date_publ, '', '', '')

    for classification in classifications:
        DataImport.add_classification(publication_reference.get('doc-number', ''), classification.get('section', ''), classification.get(
            'class', ''), classification.get('subclass', ''), classification.get('main-group', ''), classification.get('subgroup', ''), date_publ, '', '', '')
        DataImport.add_classification(application_reference.get('doc-number', ''), classification.get('section', ''), classification.get(
            'class', ''), classification.get('subclass', ''), classification.get('main-group', ''), classification.get('subgroup', ''), date_publ, '', '', '')

    print('------------------------------------------------')
    print('\n')


def run(filename, typeof):
    parsedocuments(filename, typeof, parse, to_database)


def run_bib(filename):
    run(filename, 'US_Bibliographic')


def run_full(filename):
    run(filename, 'US_Fulltext')
