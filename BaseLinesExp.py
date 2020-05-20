
from rdflib import Graph, URIRef, RDFS, RDF
from mappingFormats import *
from parse import *
import logging
from bs4 import BeautifulSoup
from sklearn.metrics import *
from textdistance import *

def getAllClasses(source, target):
    logging.info("Loading classes from  " + source)

    Document_graph = Graph()
    Document_graph.parse(source)

    logging.info("Read source with %s triples.", len(Document_graph))
    SourceClasses = []

    for s, p, o in Document_graph.triples((None, RDF.type, None)):
        SourceClasses.append(GetClassLabel(o))

    logging.info("Loading classes from  " + target)

    Document_graph = Graph()
    Document_graph.parse(target)

    logging.info("Read source with %s triples.", len(Document_graph))
    TargetClasses = []

    for s, p, o in Document_graph.triples((None, RDF.type, None)):
        TargetClasses.append(GetClassLabel(o))


    alignment = []
    logging.info("Matching classes based on name similarity ")
    for i in set(SourceClasses):
        for j in set(TargetClasses):
            if i == j:
                alignment.append((getNellURI(i), getDBpediaURI(j), '=', 1.0))


    outputfile='Label_matcher_alignment.xml'

    write_Mappings(outputfile,alignment)
    Evaluator(outputfile)

    Lev_Similarity(list(set(SourceClasses)) ,list(set(TargetClasses)))
    Evaluator('Lev_matcher_alignment.xml')

def Lev_Similarity(source, target):
    CandidateList=[]
    alignment=[]
    for i in range(len(source)):
        for j in range(len(target)):
            if (levenshtein.normalized_similarity(source[i].lower(), target[j].lower()) > 0.4):
                alignment.append((getNellURI(source[i]) , getDBpediaURI(target[j]), '=', 1.0))

    outputfile = 'Lev_matcher_alignment.xml'

    write_Mappings(outputfile, alignment)

def GetClassLabel(URIString):
    Label = URIString.split('/')[-1]
    return Label.lower()

def getNellURI(name):
    return 'http://rtw.ml.cmu.edu/rtw/kbbrowser/pred:' + name

def getDBpediaURI(name):
    return 'http://dbpedia.org/ontology/' + name




def get_mappings(filename):
    mappings = []

    with open(filename) as f:
        soup = BeautifulSoup(f, 'xml')

    cells = soup.find_all('Cell')

    for cell in cells:
        entity1 = cell.find('entity1').attrs['rdf:resource'].split(':')[2]
        entity2 = cell.find('entity2').attrs['rdf:resource'].split('/')[-1].lower()
        mappings.append((entity1, entity2))

    return mappings

def Evaluator(alignment_file):
    matcher_result=get_mappings(alignment_file)
    correct_mapping=get_mappings('SmallTestCase/reference.xml')

    logging.info("Evaluating the result of Label matcher")

    percision=  len(set(matcher_result).intersection(set(correct_mapping)))/ len(matcher_result)
    recall= len(set(matcher_result).intersection(set(correct_mapping)))/ len(correct_mapping)

    print("The percision is ", percision)
    print("The recall is ", recall)

    #print(precision_score (set(correct_mapping) , set(matcher_result),average='micro'))

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    source='SmallTestCase/NELL.xml'
    target='SmallTestCase/DBpedia.xml'
    getAllClasses(source,target)
