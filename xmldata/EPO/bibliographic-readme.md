14.7 DOCDB - EPO worldwide bibliographic database

DOCDB- EPO worldwide bibliographic database is a front file in an XML format of our master documentation database with worldwide coverage containing bibliographic data, abstracts and citations (but no full text). This is a front file, back file data is available under Docdb Back file folder or by request we can also deliver it on a USB to your address.

https://publication.epo.org/raw-data/product?productId=23

DOCUMENTATION: http://documents.epo.org/projects/babylon/eponet.nsf/0/6266D96FAA2D3E6BC1257F1B00398241/$File/T09.01_ST36_User_Documentation_vs_2.5.7_en.pdf

----

docdb_xml_201701_Amend_001.zip -->

docdb_xml_201701_Amend_001
  Root
    DOC
      data_coverage_201701_Amend_001.csv
      DOCDB-201701-Amend-PubDate20161230AndBefore-AP-0001.zip
        DOCDB-201701-Amend-PubDate20161230AndBefore-AP-0001.xml
      DOCDB-201701-Amend-PubDate20161230AndBefore-AR-0001.zip
      DOCDB-201701-Amend-PubDate20161230AndBefore-AT-0001.zip
      ...
      statistics_201701_Amend_001.csv
    DTDS
      datatypes.dtd
      docdb-entities.dtd
      docdb-package-v1.1.dtd
      exchange-documents-v2.5.6.xsd
      xlink.xsd
      xml.xsd
      XMLSchema.dtd
    index.xml

----    

{http://www.epo.org/exchange}exchange-documents                 (1)
  {http://www.epo.org/exchange}exchange-document                (*)
    {http://www.epo.org/exchange}bibliographic-data             (1)
      {http://www.epo.org/exchange}publication-reference        (*)  data-format="docdb|epodoc"
        document-id (docdb)                                     (1 per publication-reference?)
          <country>AP</country>
          <doc-number>895</doc-number>
          <kind>A</kind>
          <date>20001117</date>
        document-id (epodoc)
          <doc-number>AP895</doc-number>
      {http://www.epo.org/exchange}classification-ipc           (1)
      {http://www.epo.org/exchange}classifications-ipcr         (1)
      {http://www.epo.org/exchange}patent-classifications       (1)
      {http://www.epo.org/exchange}application-reference        (*)
      {http://www.epo.org/exchange}priority-claims              (1)
      {http://www.epo.org/exchange}parties                      (1)
        {http://www.epo.org/exchange}applicants                 (1)
          {http://www.epo.org/exchange}applicant                (*)  sequence="1|2|..." data-format="docdb|docdba"
            <exch:applicant-name> (docdb)
              <name>TELECOMM EQUIPMENT CORP</name>
            </exch:applicant-name>
            <residence>
              <country>US</country>
            </residence>
            <exch:applicant-name> (docdba)
              <name>TELECOMMUNICATIONS EQUIPMENT CORPORATION</name>
            </exch:applicant-name>
        {http://www.epo.org/exchange}inventors                  (1)
          {http://www.epo.org/exchange}inventor                 (*)  sequence="1|2|..." data-format="docdb|docdba" 
            <exch:inventor-name> (docdb)
              <name>WONG THOMAS T Y</name>
            </exch:inventor-name>
            <residence>
              <country>US</country>
            </residence>     
            <exch:inventor-name> (docdba)
              <name>WONG THOMAS T Y</name>
            </exch:inventor-name>                 
      {http://www.epo.org/exchange}invention-title              (1)  lang="en" data-format="docdba"
      {http://www.epo.org/exchange}dates-of-public-availability (1)
      {http://www.epo.org/exchange}references-cited             (1|0)
        {http://www.epo.org/exchange}citation                   (*)  cited-phase="SEA" sequence="1|2|..."
          patcit                                                (1 per citation?)  num="2" dnum="US3883872A" dnum-type="publication number"
            document-id                                         (1 per patcit?)  doc-id="313395104" 
              <country>US</country>
              <doc-number>3883872</doc-number>
              <kind>A</kind>
              <name>FLETCHER JAMES C ADMINISTRATOR</name>
              <date>19750513</date>
    {http://www.epo.org/exchange}abstract                       (1|0)  lang="en" data-format="docdba" abstract-source="national office"
      {http://www.epo.org/exchange}p                            (1|*)
    {http://www.epo.org/exchange}patent-family                  (1)
      {http://www.epo.org/exchange}family-member                (*)
        {http://www.epo.org/exchange}application-reference      (*)  data-format="docdb|epodoc" is-representative="NO|YES (not on epodoc)"
          document-id (docdb)                                   (1 per application-reference?)
            <country>CA</country>
            <doc-number>337421</doc-number>
            <kind>A</kind> 
          document-id (epodoc)
            <doc-number>CA19790337421</doc-number>  
        {http://www.epo.org/exchange}publication-reference      (*) data-format="docdb|epodoc" sequence="1|2|... (docdb/epodoc pairs)"    
          document-id (docdb)                                   (1 per publication-reference?)
            <country>CA</country>
            <doc-number>1148636</doc-number>
            <kind>A</kind> 
          document-id (epodoc)
            <doc-number>CA1148636</doc-number>  

----

DOCDB-201701-Amend-PubDate20161230AndBefore-AP-0001.xml (example: includes 2 of many exchange documents)

biliographic aka 'create-ammend-delete'

exch:exchange-documents (single xml with many children documents)


is-representative : canonical patent of family 