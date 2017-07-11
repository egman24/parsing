import DataImport
import math
import random
import uuid

get_doc_number = lambda: str(uuid.uuid4().int)
get_kind = lambda: random.choice(['A1', 'A'])
get_country = lambda: random.choice(['EP', 'JP', 'US'])
get_date = lambda: '20170201'
get_assignee = lambda: random.choice(['A Corp.', 'B Inc.', 'C Corp.', 'D Inc.', 'F Corp.', 'G Inc.'])

def create(related_count):
  focus_document = create_document()
  create_citations_random(focus_document, related_count)
  return focus_document['doc_number']

def create_document():
  kind = get_kind()
  doc_number = get_doc_number()
  country = get_country()
  dnum = country + doc_number + kind
  print('creating document: ' + doc_number)
  document = DataImport.create_document('Test', '?', dnum, doc_number, kind, get_date(), 'n', country, '', '', get_date(), get_date(), get_date())
  return document.data()[0]['doc'].properties

def create_assignee(assigned_document):
  DataImport.add_assignee(assigned_document['doc_number'], get_assignee(), '12345', '?', '?', get_date(), get_date(), get_date(), get_date())
  return assigned_document

def create_citation(citer_document, cited_document):
  print('creating citation: ' + citer_document['doc_number'] + '->' + cited_document['doc_number'])
  DataImport.add_citation(citer_document['doc_number'], cited_document['doc_number'], citer_document['country'], citer_document['kind'], citer_document['datepublished'], citer_document['filedate'], citer_document['issuedate'], citer_document['prioritydate'])

def create_citations_structured(focus_document):  
  docs = [create_document() for _ in range(random.randint(1, 10))]
  out = [[focus_document]]
  for i in range(len(docs)):
    out[i][1] = docs[i]
    out[i + 1] = [docs[i]]

def create_citations_random(focus_document, related_count = 10):
  number_of_documents = random.randint(1, related_count)
  print(str(number_of_documents) + ' related documents')
  related_documents = [create_document() for _ in range(number_of_documents)]
  # 1, 2, 4, 8, 16, 32, 64
  # need multiple passes (2) to get composite scores like (3, 5, ...) and (3 or 4) to get composite scores like 7, 14, 15
  print('starting pass 1...')
  [create_morph_relation(focus_document, create_assignee(citation_document)) for citation_document in related_documents]
  print('starting pass 2...')
  [create_morph_relation(focus_document, citation_document) for citation_document in random.sample(related_documents, math.floor(number_of_documents / 2))]
  print('starting pass 3...')
  [create_morph_relation(focus_document, citation_document) for citation_document in random.sample(related_documents, math.floor(number_of_documents / 4))]
  print('starting pass 4...')
  [create_morph_relation(focus_document, citation_document) for citation_document in random.sample(related_documents, math.floor(number_of_documents / 8))]
  
def create_morph_relation(subject_document, member_document):
  relations = [
    create_grandchild, 
    create_sibling, 
    create_married, 
    create_grandchild, 
    create_child, 
    create_parent, 
    #create_self
  ]
  random.choice(relations)(subject_document, member_document)

def create_grandchild(subject_document, member_document):
  link_document = create_document()
  create_citation(member_document, link_document)
  create_citation(link_document, subject_document)

def create_sibling(subject_document, member_document):
  link_document = create_document()
  create_citation(link_document, subject_document)
  create_citation(link_document, member_document)

def create_married(subject_document, member_document):
  link_document = create_document()
  create_citation(subject_document, link_document)
  create_citation(member_document, link_document)

def create_grandparent(subject_document, member_document):
  link_document = create_document()
  create_citation(subject_document, link_document)
  create_citation(link_document, member_document)

def create_child(subject_document, member_document):
  create_citation(member_document, subject_document)

def create_parent(subject_document, member_document):
  create_citation(subject_document, member_document)

def create_self(subject_document, member_document):
  create_citation(subject_document, subject_document)