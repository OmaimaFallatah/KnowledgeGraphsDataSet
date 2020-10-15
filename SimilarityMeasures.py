import collections
import itertools
import random

import pandas as pd
import pysolr

from BaseLinesExp import *


# Search for a source class
# Source KG dataframe conatain all the data about that KG
# SolrCore this the core of the target knowledge graphs
def searchForClass(SourceClassName, SourceKG, solrCore):
    #QueryDF = QueryDF.set_index('Class_Name')
    i = 1
    myRandom = 22

    final = []
    while i <= 40:
        num = SourceKG.loc[SourceClassName, 'Number_of_Instances']
        MyList = SourceKG.loc[SourceClassName, 'Instances_Names'].split('|')

        if num < myRandom:
             myRandom = myRandom-14
        for c in range(len(MyList)):
            MyList[c] = MyList[c].strip('_').replace(':', '')
        Rlist = ' '.join(random.sample(MyList, myRandom))
        results = solrCore.search('Instances_Names: %s' % (Rlist), rows=3)
        for result in results:
            final.append(result['Class_Name'][0])
        i += 1
    # print(final)
    return final

# This method mange all the search processes
def SearchSetting(SourceKG, SourceClassList, SolrCore):


    SourceKG = SourceKG.set_index('Class_Name')
    result = pd.DataFrame(columns=['Source_Class', 'Target_Class'])
    CandList = []
    alignment = []
    for c in range(len(SourceClassList)):
        FinalList = []

        loopCount = 0
        while loopCount <= 15 and len(FinalList) < 3:
            FinalList = searchForClass(SourceClassList[c], SourceKG, SolrCore)
            loopCount += 1

        if loopCount > 15 and len(FinalList) != 0:
            for l in range(len(FinalList)):
                CandList.append(tuple([SourceClassList[c]] + [FinalList[l].lower()]))
                if (levenshtein.normalized_similarity(SourceClassList[c], FinalList[l].lower()) > 0.4):
                    alignment.append((getNellURI(SourceClassList[c]), getDBpediaURI(FinalList[l])))
        else:
            counter = collections.Counter(FinalList)
            if len(counter) == 1:
                CandList.append(tuple([SourceClassList[c]] + [FinalList[0].lower()]))
                if (levenshtein.normalized_similarity(SourceClassList[c], FinalList[0].lower()) > 0.4):
                    alignment.append((getNellURI(SourceClassList[c]), getDBpediaURI(FinalList[0])))
            elif len(counter) == 2:  # we have two matching classes one repeated
                for i in counter.most_common(2):
                    CandList.append(tuple([SourceClassList[c]] + [i[0].lower()]))
                    if (levenshtein.normalized_similarity(SourceClassList[c], i[0].lower()) > 0.4):
                        alignment.append((getNellURI(SourceClassList[c]), getDBpediaURI(i[0])))
            elif len(counter) >= 3:# If we have 3 or more element
                for i in counter.most_common(3):
                    CandList.append(tuple([SourceClassList[c]] + [i[0].lower()]))
                    if (levenshtein.normalized_similarity(SourceClassList[c], i[0].lower()) > 0.4):
                        alignment.append((getNellURI(SourceClassList[c]), getDBpediaURI(i[0])))
    return alignment

# Returns pairs of similar classes names based on edit distance (Lev)
def get_Name_Similarity(Source, Target):
    alignment=[]
    for i in range(len(Source)):
        for j in range(len(Target)):
            if (levenshtein.normalized_similarity(Source[i].lower(), Target[j].lower()) > 0.4):
                alignment.append(tuple([Source[i]] + [Target[j]]))

    outputfile = 'Label_matcher_alignment.xml'
    write_Mapping(outputfile, alignment)
    return alignment

def isequal(a, b):
   try:
      return a.upper() == b.upper()
   except AttributeError:
     return a == b

def getClassURI(d):
    df = pd.read_csv('DBlist.csv')
    DbURI='http://dbpedia.org/ontology/'
    for i in range(len(df)):
        if (isequal(d, df.loc[i,'Class_Name'])):
            return DbURI+df.loc[i,'Class_Name']

def GS_Prep(FinalDF):
    GS = pd.DataFrame(columns=['KG1_NELL', 'URI1', 'KG2_DBpedia', 'URI2', 'Relation'])
    nellURI = 'http://rtw.ml.cmu.edu/rtw/kbbrowser/pred:'
    for i in range(len(FinalDF)):
        nURI = nellURI + FinalDF.loc[i, 'Class_Pair'][0]
        dURI = getClassURI(FinalDF.loc[i, 'Class_Pair'][1])
        GS = GS.append(
            {'KG1_NELL': FinalDF.loc[i, 'Class_Pair'][0], 'URI1': nURI, 'KG2_DBpedia': FinalDF.loc[i, 'Class_Pair'][1],
             'URI2': dURI}, ignore_index=True)
    GS.to_csv('testGS.csv')

# This combines the two similarity measures - (name + instance)
def main():
    df = pd.read_csv('DBlist.csv')
    df2 = pd.read_csv('NellList.csv')
    DBlist = df['Class_Name'].to_list()
    NList = df2['Class_Name'].to_list()
    N = []
    D = []
    for j in range(len(NList)):
        N.append(NList[j].lower())

    for j in range(len(DBlist)):
        D.append(DBlist[j].lower())

    StrSim=get_Name_Similarity(N,D)


    c = list(list(itertools.product(N, D)))
    FinalDF = pd.DataFrame(columns=['Class_Pair', 'Name_Similarity', 'Instance_Similarity'])
    FinalDF['Class_Pair'] = c

    for i in range(len(FinalDF)):
        for j in range(len(StrSim)):
            if FinalDF.loc[i, 'Class_Pair'] == StrSim[j]:
                FinalDF.loc[i, 'Name_Similarity'] = 1


    solr = pysolr.Solr('http://localhost:8983/solr/Dbpedia')
    InistanceSim=SearchSetting(df2, NList,solr)
    for i in range(len(FinalDF)):
        for j in range(len(InistanceSim)):
            if FinalDF.loc[i, 'Class_Pair'] == InistanceSim[j]:
                FinalDF.loc[i, 'Instance_Similarity1'] = 1

    for i in range(len(FinalDF)):
        if FinalDF.loc[i, 'Name_Similarity'] != 1 and FinalDF.loc[i, 'Instance_Similarity'] != 1:
            FinalDF = FinalDF.drop(i)

    FinalDF = FinalDF.reset_index()
    GS_Prep(FinalDF)
    outputfile = 'Combined_matcher_alignment.xml'

    write_Mapping(outputfile, InistanceSim)

    #Evaluator(outputfile)

# Only measure instance similarity
def main2():
    df = pd.read_csv('DBlist.csv')
    df2 = pd.read_csv('NellList.csv')
    DBlist = df['Class_Name'].to_list()
    NList = df2['Class_Name'].to_list()
    N = []
    D = []
    for j in range(len(NList)):
        N.append(NList[j].lower())

    for j in range(len(DBlist)):
        D.append(DBlist[j].lower())

    c = list(list(itertools.product(N, D)))
    FinalDF = pd.DataFrame(columns=['Class_Pair', 'Name_Similarity', 'Instance_Similarity1'])
    FinalDF['Class_Pair'] = c

    # the solr core for the target knowledge graph
    solr = pysolr.Solr('http://localhost:8983/solr/DBpedia')
    InistanceSim = SearchSetting(df2, NList, solr)

    outputfile = 'Inistance_matcher_alignment.xml'

    write_Mapping(outputfile, InistanceSim)

    #Evaluator(outputfile)


if __name__ == "__main__":
   # logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    main()
