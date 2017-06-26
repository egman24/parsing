# https://neo4j.com/developer/python/#neo4j-python-driver

from neo4j.v1 import GraphDatabase, basic_auth
from datetime import datetime

driver = GraphDatabase.driver("bolt://localhost:32777", auth=basic_auth("neo4j", "12345"))

# cypher :: String, {} -> <Record n=<Node id=0 labels={} properties={}>>
def cypher(query, params):
	session = driver.session()
	result = session.run(query, params)
	session.close()
	return result

# for record in EPODataImport.cypher('MATCH (n) RETURN n'):
#   print("%s" % (record))
# # <Record n=<Node id=0 labels={'Test'} properties={}>>

# TODO: add type as Label instead of property?

def create_us_document(typeof, reference, dnum, docnumber, kind, datepublished, status, country, title, abstract, filedate, issuedate, prioritydate, claims, description):
  now = datetime.today().isoformat()

  query = '''
    MERGE (parent:Doc { doc_number: {docnumber} })
    CREATE (doc:Member { _type: {type}, _imported_at: {imported_at}, reference: {reference}, doc_number: {docnumber}, kind: {kind}, country: {country}, dnum: {dnum}, datepublished: {datepublished}, status: {status}, title: {title}, abstract: {abstract}, filedate: {filedate}, issuedate: {issuedate}, prioritydate: {prioritydate}, claims: {claims}, description: {description} }) 
    CREATE (doc)-[:VERSION]->(parent)
    RETURN parent, doc
  '''

  params = { 
    "type": typeof, 
    "imported_at": now, 
    "reference": reference, 
    "dnum": dnum, 
    "docnumber": docnumber, 
    "kind": kind, 
    "datepublished": datepublished, 
    "status": status, 
    "country": country, 
    "title": title, 
    "abstract": abstract, 
    "filedate": filedate, 
    "issuedate": issuedate, 
    "prioritydate": prioritydate, 
    "claims": ''.join(claims), 
    "description": description 
    }

  return cypher(query, params)

def create_document(typeof, reference, dnum, docnumber, kind, datepublished, status, country, title, abstract, filedate, issuedate, prioritydate):
  now = datetime.today().isoformat()

  query = '''
    MERGE (parent:Doc { doc_number: {docnumber} })
    CREATE (doc:Member { _type: {type}, _imported_at: {imported_at}, reference: {reference}, doc_number: {docnumber}, kind: {kind}, country: {country}, dnum: {dnum}, datepublished: {datepublished}, status: {status}, title: {title}, abstract: {abstract}, filedate: {filedate}, issuedate: {issuedate}, prioritydate: {prioritydate} })
    CREATE (doc)-[:VERSION]->(parent)
    RETURN parent, doc
  '''

  params = { 
    "type": typeof, 
    "imported_at": now, 
    "reference": reference, 
    "dnum": dnum, 
    "docnumber": docnumber, 
    "kind": kind, 
    "datepublished": datepublished, 
    "status": status, 
    "country": country, 
    "title": title, 
    "abstract": abstract, 
    "filedate": filedate, 
    "issuedate": issuedate, 
    "prioritydate": prioritydate 
    }

  return cypher(query, params)

def add_citation(citer_doc_number, cited_doc_number, country, kind, date_publ, date_file, date_issue, date_priority):
  now = datetime.today().isoformat()

  # (citer:Doc) should already exist
  # (parent:Doc) may exist
  # (cited:Member) may exist
  # add new version relationship from (cited:Doc)-[:VERSION]->(parent:Doc) 
  # add citation relationship from (citer:Doc)-[:CITES]->(parent:Doc)

  query = '''
     MATCH (citer:Doc)
     WHERE citer.doc_number = {citer_id}
     MERGE (parent:Doc { doc_number: {cited_id} })
     MERGE (cited:Member { _type: "Citation", _imported_at: {imported_at}, doc_number: {cited_id}, country: {country}, kind: {kind} })
     CREATE (cited)-[:VERSION]->(parent)
     MERGE (citer)-[citation:CITES]->(parent)
     ON CREATE SET citation.imported = {imported}, citation.date_publ = {date_publ}, citation.date_file = {date_file}, citation.date_issue = {date_issue}, citation.date_priority = {date_priority}
     ON MATCH SET citation.imported = citation.imported + {imported_at}
     RETURN citer, cited, citation
  '''

  params = { 
    "imported": [now], 
    "imported_at": now, 
    "citer_id": citer_doc_number, 
    "cited_id": cited_doc_number, 
    "country": country, 
    "kind": kind, 
    "date_publ": date_publ, 
    "date_file": date_file, 
    "date_issue": date_issue, 
    "date_priority": date_priority 
    }

  return cypher(query, params)  

def add_classification(classified_doc_number, section, classification, subclass, maingroup, subgroup, date_publ, date_file, date_issue, date_priority):
  now = datetime.today().isoformat()

  # (classified:Doc) should already exist
  # (classification:Classification) may exist
  # add new classification relationship from (classification:Classification)-[:CLASSIFIES]->(classified:Doc)

  query = '''
    MATCH (classified:Doc)
    WHERE classified.doc_number = {classified_id}
    MERGE (classification:Classification { section: {section}, class: {classification}, subclass: {subclass}, maingroup: {maingroup}, subgroup: {subgroup} })
    ON CREATE SET classification._imported_at = {imported_at}
    MERGE (classification)-[classify:CLASSIFIES]->(classified)
    ON CREATE SET classify.imported = {imported}, classify.date_publ = {date_publ}, classify.date_file = {date_file}, classify.date_issue = {date_issue}, classify.date_priority = {date_priority}
    ON MATCH SET classify.imported = classify.imported + {imported_at}
    RETURN classified, classification, classify
  '''

  params = { 
    "imported": [now], 
    "imported_at": now, 
    "classified_id": classified_doc_number, 
    "section": section, 
    "classification": classification, 
    "subclass": subclass, 
    "maingroup": maingroup, 
    "subgroup": subgroup, 
    "date_publ": date_publ, 
    "date_file": date_file, 
    "date_issue": date_issue, 
    "date_priority": date_priority 
  }

  return cypher(query, params)

def add_assignee(assigned_doc_number, name, eponumber, reference, crossreference, date_publ, date_file, date_issue, date_priority):
  now = datetime.today().isoformat()

  query = '''
    MATCH (assigned:Doc)
    WHERE assigned.doc_number = {assigned_id}
    MERGE (assignee:Assignee { name: {name}, eponumber: {eponumber}, reference: {reference}, crossreference: {crossreference} })
    ON CREATE SET assignee._imported_at = {imported_at}
    MERGE (assignee)-[assign:ASSIGNED_TO]->(assigned)
    ON CREATE SET assign.imported = {imported}, assign.date_publ = {date_publ}, assign.date_file = {date_file}, assign.date_issue = {date_issue}, assign.date_priority = {date_priority}
    ON MATCH SET assign.imported = assign.imported + {imported_at}
    RETURN assignee, assigned, assign
  '''

  params = { 
    "imported": [now], 
    "imported_at": now, 
    "assigned_id": assigned_doc_number, 
    "name": name, 
    "eponumber": eponumber, 
    "reference": reference, 
    "crossreference": crossreference, 
    "date_publ": date_publ, 
    "date_file": date_file, 
    "date_issue": date_issue, 
    "date_priority": date_priority 
  }

  return cypher(query, params)

def add_family_member(typeof, family_id, doc_number, country, kind, is_representative=''):
  now = datetime.today().isoformat()

  application_query = '''
    MERGE (family:Family { id: {family_id} })
    MERGE (member:Member { _type: {type}, _imported_at: {imported_at}, doc_number: {doc_number}, country: {country}, kind: {kind}, is_representative: {is_representative} })
    MERGE (parent:Doc { doc_number: {doc_number} })
    CREATE (member)-[:VERSION]->(parent)
    MERGE (parent)-[of:MEMBER_OF]->(family)
    ON CREATE SET of.imported = {imported}
    ON MATCH SET of.imported = of.imported + {imported_at}
    RETURN member, of, family
  '''

  publication_query = '''
    MERGE (family:Family { id: {family_id} })
    MERGE (member:Member { _type: {type}, _imported_at: {imported_at}, doc_number: {doc_number}, country: {country}, kind: {kind} })
    MERGE (parent:Doc { doc_number: {doc_number} })
    CREATE (member)-[:VERSION]->(parent)
    MERGE (parent)-[of:MEMBER_OF]->(family)
    ON CREATE SET of.imported = {imported}
    ON MATCH SET of.imported = of.imported + {imported_at}
    RETURN member, of, family
  '''

  query = '''
    MERGE (family:Family { id: {family_id} })
    MERGE (member:Member { _type: {type}, _imported_at: {imported_at}, doc_number: {doc_number}, country: {country}, kind: {kind} })
    MERGE (parent:Doc { doc_number: {doc_number} })
    CREATE (member)-[:VERSION]->(parent)
    MERGE (parent)-[of:MEMBER_OF]->(family)
    ON CREATE SET of.imported = {imported}
    ON MATCH SET of.imported = of.imported + {imported_at}
    RETURN member, of, family
  '''

  params = { 
    "type": typeof, 
    "imported": [now], 
    "imported_at": now, 
    "family_id": family_id, 
    "doc_number": doc_number, 
    "country": country, 
    "kind": kind, 
    "is_representative": is_representative 
  }

  if typeof == 'Application':
    return cypher(application_query, params)
  elif typeof == 'Publication':
    return cypher(publication_query, params)
  else: 
    return cypher(query, params)

def clear():
  return cypher(
    'MATCH (n) DETACH DELETE n',
    {}
  ) 

if __name__ == "__main__":
	print('test!')