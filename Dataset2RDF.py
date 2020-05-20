
from rdflib import Graph, Dataset, URIRef, Literal, Namespace, RDF, XSD
from rdflib.namespace import OWL, RDF, RDFS
from iribaker import to_iri
import  pandas as pd
import logging
from parse import *

def main():
    #reading dataset from csv
    fileName="DBlist.csv"
    df=pd.read_csv(fileName)

    # A namespace for our resources
    data = 'http://dbpedia.org/ontology/resource/'
    DATA = Namespace(data)

    # A namespace for the schema (Classes)
    schema = 'http://dbpedia.org/ontology/'
    CLASS = Namespace(schema)

    # Creating a graph
    graph = Graph()
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)

    logging.info("Reading all data from " + fileName)
    for j in range(len(df)):

        #adding classes to the graph
        classN = URIRef(to_iri(schema + df.loc[j,'Class_Name']))
        name = Literal(df.loc[j,'Class_Name'], datatype=XSD['string']) #the class name label

        graph.add((classN, RDF.type, OWL.Class))
        graph.add((classN, RDF.type, RDFS.Class))
        graph.add((classN, RDFS.label, name))



        # in case their are no instances (only DBpedia)
        if df.loc[j,'Number_of_Instances'] == 0:
            pass
        else:
            MyList = df.loc[j,'Instances_Names'].split('|')

        # adding instances of a class to the graph
        for c in range(len(MyList)):

            MyList[c]= MyList[c].strip(' " ').replace(" ' ",'')
            instance = URIRef(to_iri(data + MyList[c]))
            graph.add((instance, RDF.type, classN ))
            instanceLabel=Literal(MyList[c], datatype=XSD['string']) #creating the label
            graph.add((instance, RDFS.label,instanceLabel))



    outFile = 'TestCase/DBpedia.xml'
    logging.info("Writing the graph to " + outFile)

    with open(outFile, 'wb') as f:
        graph.serialize(f, format='xml')

def listCountClass(path):

    logging.info("getting all classes from " + path)

    Document_graph = Graph()
    Document_graph.parse(path)
    logging.info("Read source with %s triples.", len(Document_graph))
    classes = []
    count = 0
    for s, p, o in Document_graph.triples((None, RDF.type, None)):
        classes.append(o)
    s=set(classes)
    print(s)
    print(len(s))

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    main()
    #listCountClass('TestCase/NELL.rdf')
