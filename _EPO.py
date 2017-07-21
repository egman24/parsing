import EPOParser
import EPODataImport

from pprint import pprint

# import pdb; pdb.set_trace()

# cp ../../../../EPO* .
# python
# import EPO
# EPO.run()

# example: EP15174580A1 ([20]15[0]174580)
# XML                          | Espace                                   | Doors
#--------------------------------------------------------------------------------------------
# ep-patent-document { id }    | applicationnumber EP20150174580 20150630 |
# ?                            | prioritynumber    EP20150174580 20150630 |
# doc-number                   | publicationnumber (search field)         | main patent search

# MATCH (n) RETURN length(COLLECT(distinct n.applicationnumber))
# MATCH (n) RETURN COUNT(n)
# MATCH (n) WHERE NOT EXISTS(n.docnumber) RETURN COUNT(n)
# MATCH (n)-[r]-() WHERE NOT EXISTS(n.docnumber) RETURN n, count(r) as rel_count ORDER BY rel_count DESC

# example: EP0427889 (doc-number?) difference in app/priority
# prioritynumber: US19890437442 19891115
# applicationumber: EP19890123253 19891215

# ex. multiple priority dates
# 'document': {'id': 'EP03798911B1', 'file': 'EP03798911NWB1.xml', 'lang': 'de', 'country': 'EP', 'doc-number': '1546074', 'kind': 'B1', 'date-publ': '20170125', 'status': 'n', 'dtd-version': 'ep-patent-document-v1-5'},
# 'filedate': '20030918',
# 'issuedate': '20170125',
# 'prioritydate': ['20020927', '20021001'],

# majority are double bond, some single, some triple, one instance > 3
# MATCH (n) RETURN n LIMIT 900 (fullscreen zoom out, up setting limit)
# MATCH (n) RETURN COUNT(n)
# MATCH ()-[r]->() RETURN COUNT(r)

# single: sr-pcit000*
# double: (ep-reference-list) ref-pcit000* & (inline in description) pcit000*
# >= 3: ref and standard with different numbers

# single bond
# MATCH (n) WHERE n.id = 'EP15003455A1' RETURN n

# double bond/triple bond
# MATCH (n) WHERE n.id = 'EP14883916A1' RETURN n

# many bond (> 3)
# MATCH (n) WHERE n.id = 'EP14883612A1' RETURN n
# MATCH (n) WHERE n.id = 'EP15174347A1' RETURN n

# citing more than one that is present in dataset
# MATCH (n) WHERE n.id = 'JP2008175717A' RETURN n
# MATCH (n) WHERE n.id = 'EP1503940B1' RETURN n
# MATCH (n) WHERE n.id = 'US2007118745A1' RETURN n
# docnumber3112431
# <id> 19344
# MATCH (n) WHERE n.applicationnumber = 'EP16176302A1' RETURN n

# same with difference in abstract and id
# EP15020106A1 & EP15020107A1
# EP15174581A1 & EP15174580A1

# TODO: add time to citations somehow?
# TODO: send sentinel None instead of empty string, in DataImport add attribute if not None
# TODO: build up query strings during inital run and run seperately?


def cleanup(x): print(x)


def to_database(metadata):
    print('------------------------------------------------')
    pprint(metadata)

    # {'id': 'EP14883349A1', 'file': 'EP14883349NWA1.xml', 'lang': 'en', 'country': 'EP', 'doc-number': '3112982', 'kind': 'A1', 'date-publ': '20170104', 'status': 'n', 'dtd-version': 'ep-patent-document-v1-5'}
    document = metadata.get('document', {})
    # [{'id': 'ref-pcit0001', 'dnum': 'JP2006266451A'}]
    citations = metadata.get('citations', [])
    identifier = document.get('id', '')
    country = document.get('country', '')
    docnumber = document.get('doc-number', '')
    kind = document.get('kind', '')
    datepublished = document.get('date-publ', '')
    status = document.get('status', '')
    title = metadata.get('title', '')
    abstract = ''.join(metadata.get('abstract', []))
    filedate = metadata.get('filedate', '')
    issuedate = metadata.get('issuedate', '')
    prioritydate = metadata.get('prioritydate', '')

    EPODataImport.create_document('fulltext', identifier, docnumber, kind, datepublished,
                                  status, country, title, abstract, filedate, issuedate, prioritydate)

    # TODO: find clean way to make sure this is always a list during the parse process...
    if isinstance(citations, list):
        for citation in citations:
            EPODataImport.add_citation(identifier, citation.get(
                'dnum', ''), citation.get('id', ''), citation.get('url', ''))
    else:
        EPODataImport.add_citation(identifier, citations.get(
            'dnum', ''), citations.get('id', ''), citations.get('url', ''))

    print('------------------------------------------------')
    print('\n')


def run(): EPOParser.run('index.xml', './DTDS/ep-patent-document-v1-5.dtd',
                         EPOParser.fields, {}, to_database, cleanup)


def clear(): EPODataImport.clear()
