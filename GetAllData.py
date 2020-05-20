
#from bs4 import BeautifulSoup
from owlready2 import get_ontology
from collections import defaultdict
from SPARQLWrapper import SPARQLWrapper, JSON
import csv
import pandas as pd

#from sklearn.metrics import f1_score


def get_DBpedia_Inistances(file):
    ClassesList=[]
    with open(file, newline='') as f:
        for row in csv.reader(f):
            for i in row:
                ClassesList.append(i)

    classId = 0
    df = pd.DataFrame(columns=['ClassID', 'URI', 'Class_Name', 'Number_of_Instances', 'Instances_Names'])
    df.set_index(['ClassID'])

    sparq1 = SPARQLWrapper("http://dbpedia.org/sparql")
    for className in ClassesList:
        MyList = []
        queryString = """
                             SELECT ?name
                             WHERE{ ?entity a <http://dbpedia.org/ontology/%s>.
                             ?entity rdfs:label ?name.
                             Filter (lang(?name)="en")}""" % (className)
        sparq1.setQuery(queryString)
        sparq1.setReturnFormat(JSON)
        results = sparq1.query().convert()

        for r in results["results"]["bindings"]:
            MyList.append(r["name"]["value"])

        for i in range(len(MyList)):
            MyList[i] = MyList[i].replace(' ', '_')

        Inames = ' | '.join(MyList)
        classId += 1
        classURI = 'http://dbpedia.org/ontology/' + className
        totalNumOfInstances = len(MyList)
        df = df.append(
            {'ClassID': classId, 'URI': classURI, 'Class_Name': className, 'Number_of_Instances': totalNumOfInstances,
             'Instances_Names': Inames}, ignore_index=True)

        df.to_csv('DBlist.csv', index=False, encoding='utf-8')


def read_ontology(path):
    onto = get_ontology(path)
    onto.load()

    # Read classes
    classes = []
    for cl in onto.classes():
        classes.append(str(cl).split('.')[1].lower())

    return classes

def get_nell_classes(path):
    cols = ["Entity", "Relation", "Value"]
    iterator = pd.read_csv(path, delimiter='\t', chunksize=20000, usecols=cols)
    MyList = []
    for df_ in iterator:
        tmp_df = df_.pipe(lambda x: x[x.Relation == "generalizations"])
        MyList += [tmp_df.copy()]

    FinalList = pd.concat(MyList)
    df = pd.DataFrame(columns=['URI', 'Class_Name', 'Number_of_Instances', 'Instances_Names'])
    df['Class_Name'] = FinalList['Entity']
    df['Instances_Names'] = FinalList['Value']

    df['Class_Name'] = df['Class_Name'].str.rsplit(":", 1).str[1]  # apply(lambda x: x.split(':')[2])
    df['Instances_Names'] = df['Instances_Names'].apply(lambda x: x.split(':')[1])
    df = df.groupby(['Instances_Names'])['Class_Name'].apply(' | '.join).reset_index()
    for i in df:
        df['Number_of_Instances'] = df['Class_Name'].str.split('|').str.len()
    URI = 'http://rtw.ml.cmu.edu/rtw/kbbrowser/pred:'
    for i in df:
        df['URI'] = URI + df['Instances_Names']
    df.columns = ['Class_Name', 'Instances_Names', 'Number_of_Instances', 'URI']


    #classes = df['Instances_Names'].to_list()
    #return classes
    df.to_csv('Nell_Instances.csv', index=True)

def match(source, target):
    # a very simple label matcher:
    alignment = []

    label_to_uri = defaultdict(list)

    pairs = zip(source, target)
    alignment = [[a, b] for a in source
              for b in target if a == b]


      #     label_to_uri[str(i)].append(i)
    #alignment=any(x != y for x, y in pairs)
    #for i in target:
     #   if isinstance(i, str) and i in label_to_uri:
      #      for one_uri in label_to_uri:
               # alignment.append((one_uri, str(i), '=', 1.0))

    return alignment

def main():
    AllClasses=read_ontology('dbpedia_2016-10.owl')
    print(AllClasses)
    print(len(AllClasses))

    classes=get_nell_classes('NELL.08m.1115.esv.csv')
    print(classes)
    print(len(classes))

    A=match(AllClasses,classes)

    for i in A:
        print (i)
    print (len(A))




    get_nell_classes('NELL.08m.1115.esv.csv')


get_DBpedia_Inistances('ClassList.csv')