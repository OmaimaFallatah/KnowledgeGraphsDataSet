import itertools
import pysolr
import pandas as pd
import random
import collections
from textdistance import *
from mappingFormats import *

def searchForClass(cName,QueryDF):
    i = 1
    myRandom = 20
    solr = pysolr.Solr('http://localhost:8983/solr/Dbpedia') #this the core of the target knowledge graphs

    final = []
    while i <= 60:
        MyList = []
        MyList = QueryDF.loc[cName, 'Instances_Names'].split('|')
        num = QueryDF.loc[cName, 'Number_of_Instances']
        if num < myRandom:
             #pass
             myRandom = myRandom-12
        for c in range(len(MyList)):
            MyList[c] = MyList[c].strip('_').replace(':', '')
        Rlist = ' '.join(random.sample(MyList, myRandom))
        results = solr.search('Instances_Names: %s' % (Rlist), rows=3)
        for result in results:
            final.append(result['Class_Name'][0])
        i += 1
    # print(final)
    return final


def SearchSetting(QueryDF, QueryClassList):


    QueryDF = QueryDF.set_index('Class_Name')
    result = pd.DataFrame(columns=['Source_Class', 'Target_Class'])
    CandList = []

    #QueryClassList=['sidebar_individual','sidebar_novel', 'sidebar_planet',"uss", "decade_nav","planet_ordinals"]
    for c in range(len(QueryClassList)):
        FinalList = []
        loopCount = 0  # I want to do 3 attempt before giving up search for a match
        while loopCount <= 15 and len(FinalList) < 3:
            FinalList = searchForClass(QueryClassList[c], QueryDF)
            loopCount += 1

        if loopCount > 15 and len(FinalList) != 0:
            # print ('I only found those :(', FinalList)
            for l in range(len(FinalList)):
                CandList.append(tuple([QueryClassList[c]] + [FinalList[l].lower()]))
            # if we are giving up

        else:  # we have 3 or more element
            counter = collections.Counter(FinalList)
            if len(counter) == 1:
                # print ('Yay we have a match for ' + NClassList[c] , counter)
                # print (FinalList, loopCount)
                CandList.append(tuple([QueryClassList[c]] + [FinalList[0].lower()]))
            elif len(counter) == 2:  # we have two matching classes one repeated
                # print ('MM we have two matches for ' + NClassList[c] , counter)
                for i in counter.most_common(2):
                    CandList.append(tuple([QueryClassList[c]] + [i[0].lower()]))
            elif len(counter) >= 3:
                # print ('Yay we have 3 match for ' + NClassList[c] , counter.most_common(3))
                for i in counter.most_common(3):
                    CandList.append(tuple([QueryClassList[c]] + [i[0].lower()]))
    return CandList

def get_Name_Similarity(N, D):
    CandidateList=[]
    alignment=[]
    for i in range(len(N)):
        for j in range(len(D)):
            if (levenshtein.normalized_similarity(N[i].lower(), D[j].lower()) > 0.4):
                # CandidateList.append([ NList[i], DBlist[j]])
                CandidateList.append(tuple([N[i]] + [D[j]]))
                alignment.append((N[i], N[j], '=', 1.0))

    outputfile = 'Lev_matcher_alignment.xml'

    write_Mappings(outputfile, CandidateList)
    return CandidateList

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
        # for j in FinalDF.loc[i,'Class_Pair']:
        # print FinalDF.loc[i,'Class_Pair'][0], FinalDF.loc[i,'Class_Pair'][1]
        nURI = nellURI + FinalDF.loc[i, 'Class_Pair'][0]
        dURI = getClassURI(FinalDF.loc[i, 'Class_Pair'][1])
        GS = GS.append(
            {'KG1_NELL': FinalDF.loc[i, 'Class_Pair'][0], 'URI1': nURI, 'KG2_DBpedia': FinalDF.loc[i, 'Class_Pair'][1],
             'URI2': dURI}, ignore_index=True)
    GS.to_csv('testGS.csv')

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

    #DBlist=['musicsong','actor', 'conference',"airport", "placeofworship","restaurant"]
    InistanceSim=SearchSetting(df2, NList)
    for i in range(len(FinalDF)):
        for j in range(len(InistanceSim)):
            if FinalDF.loc[i, 'Class_Pair'] == InistanceSim[j]:
                FinalDF.loc[i, 'Instance_Similarity'] = 1

    for i in range(len(FinalDF)):
        if FinalDF.loc[i, 'Name_Similarity'] != 1 and FinalDF.loc[i, 'Instance_Similarity'] != 1:
            FinalDF = FinalDF.drop(i)

    FinalDF = FinalDF.reset_index()
    GS_Prep(FinalDF)

if __name__ == "__main__":
    #logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    main()