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
  return cypher(
    ('MERGE (parent:Doc { doc_number: {docnumber} })'
     'CREATE (doc:Member { _type: {type}, _imported_at: {imported_at}, reference: {reference}, doc_number: {docnumber}, kind: {kind}, country: {country}, dnum: {dnum}, datepublished: {datepublished}, status: {status}, title: {title}, abstract: {abstract}, filedate: {filedate}, issuedate: {issuedate}, prioritydate: {prioritydate}, claims: {claims}, description: {description} })' 
     'CREATE (parent)<-[:VERSION]-(doc)'
     'RETURN parent, doc'), 
    { "type": typeof, "imported_at": datetime.today().isoformat(), "reference": reference, "dnum": dnum, "docnumber": docnumber, "kind": kind, "datepublished": datepublished, "status": status, "country": country, "title": title, "abstract": abstract, "filedate": filedate, "issuedate": issuedate, "prioritydate": prioritydate, "claims": ''.join(claims), "description": description }
  )

def create_document(typeof, reference, dnum, docnumber, kind, datepublished, status, country, title, abstract, filedate, issuedate, prioritydate):
  return cypher(
    ('MERGE (parent:Doc { doc_number: {docnumber} })'
     'CREATE (doc:Member { _type: {type}, _imported_at: {imported_at}, reference: {reference}, doc_number: {docnumber}, kind: {kind}, country: {country}, dnum: {dnum}, datepublished: {datepublished}, status: {status}, title: {title}, abstract: {abstract}, filedate: {filedate}, issuedate: {issuedate}, prioritydate: {prioritydate} })' 
     'CREATE (parent)<-[:VERSION]-(doc)'
     'RETURN parent, doc'), 
    { "type": typeof, "imported_at": datetime.today().isoformat(), "reference": reference, "dnum": dnum, "docnumber": docnumber, "kind": kind, "datepublished": datepublished, "status": status, "country": country, "title": title, "abstract": abstract, "filedate": filedate, "issuedate": issuedate, "prioritydate": prioritydate }
  )

def add_citation(citer_doc_number, cited_doc_number, country, kind, date_publ, date_file, date_issue, date_priority):
  now = datetime.today().isoformat()
  return cypher(
    ('MATCH (citer:Doc)'
     'WHERE citer.doc_number = {citer_id}'
     'MERGE (parent:Doc { doc_number: {cited_id} })'
     'MERGE (cited:Member { _type: "Citation", _imported_at: {imported_at}, doc_number: {cited_id}, country: {country}, kind: {kind} })'
     'CREATE (parent)<-[:VERSION]-(cited)'
     'MERGE (citer)-[citation:CITES]->(parent)'
     'ON CREATE SET citation.imported = {imported}, citation.date_publ = {date_publ}, citation.date_file = {date_file}, citation.date_issue = {date_issue}, citation.date_priority = {date_priority}'
     'ON MATCH SET citation.imported = citation.imported + {imported_at}'
     'RETURN citer, cited, citation'),
    { "imported": [now], "imported_at": now, "citer_id": citer_doc_number, "cited_id": cited_doc_number, "country": country, "kind": kind, "date_publ": date_publ, "date_file": date_file, "date_issue": date_issue, "date_priority": date_priority } 
  )  

def add_classification(classified_doc_number, section, classification, subclass, maingroup, subgroup, date_publ, date_file, date_issue, date_priority):
  now = datetime.today().isoformat()
  return cypher(
    ('MATCH (classified:Doc)'
     'WHERE classified.doc_number = {classified_id}'
     'MERGE (classification:Classification { section: {section}, class: {classification}, subclass: {subclass}, maingroup: {maingroup}, subgroup: {subgroup} })'
     'ON CREATE SET classification._imported_at = {imported_at}'
     'MERGE (classification)-[classify:CLASSIFIES]->(classified)'
     'ON CREATE SET classify.imported = {imported}, classify.date_publ = {date_publ}, classify.date_file = {date_file}, classify.date_issue = {date_issue}, classify.date_priority = {date_priority}'
     'ON MATCH SET classify.imported = classify.imported + {imported_at}'
     'RETURN classified, classification, classify'),
    { "imported": [now], "imported_at": now, "classified_id": classified_doc_number, "section": section, "classification": classification, "subclass": subclass, "maingroup": maingroup, "subgroup": subgroup, "date_publ": date_publ, "date_file": date_file, "date_issue": date_issue, "date_priority": date_priority } 
  )

def add_assignee(assigned_doc_number, name, eponumber, reference, crossreference, date_publ, date_file, date_issue, date_priority):
  now = datetime.today().isoformat()
  return cypher(
    ('MATCH (assigned:Doc)'
     'WHERE assigned.doc_number = {assigned_id}'
     'MERGE (assignee:Assignee { name: {name}, eponumber: {eponumber}, reference: {reference}, crossreference: {crossreference} })'
     'ON CREATE SET assignee._imported_at = {imported_at}'
     'MERGE (assignee)-[assign:ASSIGNED_TO]->(assigned)'
     'ON CREATE SET assign.imported = {imported}, assign.date_publ = {date_publ}, assign.date_file = {date_file}, assign.date_issue = {date_issue}, assign.date_priority = {date_priority}'
     'ON MATCH SET assign.imported = assign.imported + {imported_at}'
     'RETURN assignee, assigned, assign'),
    { "imported": [now], "imported_at": now, "assigned_id": assigned_doc_number, "name": name, "eponumber": eponumber, "reference": reference, "crossreference": crossreference, "date_publ": date_publ, "date_file": date_file, "date_issue": date_issue, "date_priority": date_priority } 
  )

def add_family_member(typeof, family_id, doc_number, country, kind, is_representative=''):
  now = datetime.today().isoformat()
  if typeof == 'Application':
    return cypher(
      ('MERGE (family:Family { id: {family_id} })'
       'MERGE (member:Member { _type: {type}, _imported_at: {imported_at}, doc_number: {doc_number}, country: {country}, kind: {kind}, is_representative: {is_representative} })'
       'MERGE (parent:Doc { doc_number: {doc_number} })'
       'CREATE (parent)<-[:VERSION]-(member)'
       'MERGE (parent)-[of:MEMBER_OF]->(family)'
       'ON CREATE SET of.imported = {imported}'
       'ON MATCH SET of.imported = of.imported + {imported_at}'
       'RETURN member, of, family'),
      { "type": typeof, "imported": [now], "imported_at": now, "family_id": family_id, "doc_number": doc_number, "country": country, "kind": kind, "is_representative": is_representative } 
    )
  elif typeof == 'Publication':
    return cypher(
      ('MERGE (family:Family { id: {family_id} })'
       'MERGE (member:Member { _type: {type}, _imported_at: {imported_at}, doc_number: {doc_number}, country: {country}, kind: {kind} })'
       'MERGE (parent:Doc { doc_number: {doc_number} })'
       'CREATE (parent)<-[:VERSION]-(member)'
       'MERGE (parent)-[of:MEMBER_OF]->(family)'
       'ON CREATE SET of.imported = {imported}'
       'ON MATCH SET of.imported = of.imported + {imported_at}'
       'RETURN member, of, family'),
      { "type": typeof, "imported": [now], "imported_at": now, "family_id": family_id, "doc_number": doc_number, "country": country, "kind": kind } 
    )
  else: 
    return cypher(
      ('MERGE (family:Family { id: {family_id} })'
       'MERGE (member:Member { _type: {type}, _imported_at: {imported_at}, doc_number: {doc_number}, country: {country}, kind: {kind} })'
       'MERGE (parent:Doc { doc_number: {doc_number} })'
       'CREATE (parent)<-[:VERSION]-(member)'
       'MERGE (parent)-[of:MEMBER_OF]->(family)'
       'ON CREATE SET of.imported = {imported}'
       'ON MATCH SET of.imported = of.imported + {imported_at}'
       'RETURN member, of, family'),
      { "type": typeof, "imported": [now], "imported_at": now, "family_id": family_id, "doc_number": doc_number, "country": country, "kind": kind } 
    ) 

def clear():
  return cypher(
    'MATCH (n) DETACH DELETE n',
    {}
  ) 

if __name__ == "__main__":
	print('test!')