from xml.sax.saxutils import quoteattr




def get_file_header():
    return """<?xml version=\"1.0\" encoding=\"utf-8\"?>
    <rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment"
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:xsd="http://www.w3.org/2001/XMLSchema#">
<Alignment>
  <xml>yes</xml>
  <level>0</level>
  <type>??</type>"""

def get_mapping_format(source, target,relation , measure):
    return """
  <map>
    <Cell>
      <entity1 rdf:resource=%s/>
      <entity2 rdf:resource=%s/>
      <relation>%s</relation>
      <measure rdf:datatype="xsd:float">%.1f</measure>
    </Cell>
  </map>""" %(quoteattr(source), quoteattr(target), relation, float(measure))
#(quoteattr(source), quoteattr(target), relation, measure)

def _get_file_footer():
    return """
  </Alignment>
</rdf:RDF>
"""

def write_Mappings(file, mapping):
    #df=pd.read_csv(alignments)
    #df=df.drop_duplicates(subset=['Class_Name_1', 'Class_Name_2'], keep='first')

    with open(file, 'w', encoding='utf-8') as Myfile:
        Myfile.write(get_file_header())
        for source, target, relation, measure in mapping:
            Myfile.write(get_mapping_format(source, target, relation, measure))
        Myfile.write(_get_file_footer())