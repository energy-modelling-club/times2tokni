# -*- coding: utf-8 -*-
"""
Created on Fri Nov 30

author: tilseb@dtu.dk

TODO: encoding for messy=False not working!
"""

# import required packages
import pandas as pd
import json
import glob
import os



# directories
dirs = ['input', 'output']
for i in dirs:
    if not os.path.exists(i):
        os.makedirs(i)


# unicode encoding
enc = 'utf-8'


# INCLUDE REGIONS: True/False
include_regions = False


# MESSY JSON: True/False
messy = True


# list of indictor groups that have wrong algebraic sign
l_as = pd.read_csv('input/algebraic_sign_switch.csv', encoding=enc)
l_as = l_as.indicatorGroup.tolist()


# load line to bar translation table and make dictionary
l2b = pd.read_csv('input/line2bar_combinations.csv', encoding=enc, index_col=0)
dict_l2b = l2b.bar_indicator.to_dict()


# load indicator group to multiplier translation table and make dictionary
i2m = pd.read_csv('input/share_calculation.csv', encoding=enc)


# get list of all input data files with certain file name extension
idf_ex = '.xls'
path_list = glob.glob('input/*' + idf_ex)


def run_script(file_path):

    # get sheet names from excel input data file, define name and file extension
    xl = pd.ExcelFile(file_path)
    idf_n = file_path.split('\\')[1].split('.')[0]
    sheet_names = xl.sheet_names
    if 'Sheet1' in sheet_names: sheet_names.remove('Sheet1')
    col_names = ['scenario', 'region', 'indicatorGroup', 'year', 'total']


    # load data from all sheets into one dataframe
    data = pd.DataFrame()
    for i in sheet_names:
        df = pd.read_excel(xl,
                           sheet_name=i,
                           skiprows=3,
                           encoding=enc,
                           sort=False)
        df = df.dropna(axis=1, how='all')
        chartTitle = df.iloc[0,0].split(': ')[1]
        lable = df.iloc[1,0].split(': ')[1]
        df.columns = list(df.iloc[2,:])
        if 'Region' not in df: df.insert(1, 'region', 'missing')
        df.columns = col_names
        df = df.iloc[3:,:]
        df['indicator'] = i
        df['chartName'] = i
        df['chartTitle'] = chartTitle
        df['lable'] = lable
        data = data.append(df, ignore_index=True)


    # drop nan from dataframe
    data = data.dropna()


    # convert strings with digits to integers
    data.year = pd.to_numeric(data.year, errors='ignore', downcast='integer')


    # check if regions exist, else remove from the category list
    cats = ['region','indicator','indicatorGroup']
    if not include_regions:
        del data['region']
        cats.remove('region')


    # combine charts
    data.loc[(data.chartName == '_Miljø og energi afgifter2'),
             'chartName'] = '_Miljø og energi afgifter'
    data.loc[(data.chartTitle == '_Miljø og energi afgifter2'),
             'chartName'] = '_Miljø og energi afgifter'


    # make auxiliary dataframes
    cols = data.columns[data.columns.isin(cats)].tolist()
    df1 = data[cols].drop_duplicates().reset_index(drop=True)
    df2 = data[['year']].drop_duplicates().reset_index(drop=True)
    df3 = data[['scenario']].drop_duplicates().reset_index(drop=True)
    df1['total'] = 0
    df2['total'] = 0
    df3['total'] = 0


    # change algebraic sign for selected indicator groups
    for i in l_as:
        data.loc[data.indicatorGroup.str.contains(i), 'total'] *= -1


    # calculate share per scenario and year
    data['multiplier'] = data.indicatorGroup
    for i in i2m.sheet_name.unique():
        dict_i2m = i2m[i2m.sheet_name==i].set_index(['indicatorGroup']).multiplier.to_dict()
        data.multiplier.replace(dict_i2m, inplace=True)
    data.loc[(data.multiplier.str.isnumeric()==False), 'multiplier'] = 0
    data['total_multiplied'] = data.total * data.multiplier

    for i in i2m.sheet_name.unique():
        if i in data.chartName:
            data.loc[(data.chartName==i),
                     'total'] = (data[data.chartName==i]\
                                 .groupby(['scenario','year'])\
                                 .total_multiplied.transform(lambda x: x / x.sum()))


    # safe meta information
    scnNames = data.scenario.unique()


    # create min and max values per chart name, title and lable for y axis
    data['minY'] = data.total
    data.loc[data.minY > 0, 'minY'] = 0
    data['maxY'] = data.total
    charts = data.groupby(['chartName',
                           'chartTitle',
                           'lable']).agg({'minY':'min','maxY':'max'})
    charts = charts.reset_index().to_dict('records')


    # create charts text file
    with open('output/' + idf_n + 'charts.txt', 'w', encoding=enc) as file:
        text = ''
        for i in charts:
            text += ("<StackedBarChart chartName='" + i['chartName'] +
                     "' chartTitle='" + i['chartTitle'] +
                     "' selectedScenario={selectedScenario} " +
                     "selectedScenario2={selectedScenario2} " +
                     "combinedChart={false} label='" + i['lable'] +
                     "' minY={'" + str(int(i['minY']-.5)) +
                     "'} maxY={'" + str(int(i['maxY']+.5)) + "'} />" + '\n')
        file.write(text)


    # create scenarioOptions json file
    if include_regions: regNames = data.region.unique()
    with open('output/' + idf_n + 'scenarioCombinations.json', 'w',
              encoding=enc) as file:
        text1 = ''
        count1 = 0
        for i in scnNames:
            i = i.replace("_", " ")
            text1 += ("{ \"id\": " + str(count1) +
                     ", \"name\": \"" + i +
                     "\", \"short_description\": \"" + i +
                     "\", \"ultra_short_description\": \"" + '' + "\" }," + '\n')
            count1 += 1
        text2 = ''
        count2 = 0
        if include_regions:
            for i in regNames:
                i = i.replace("_", " ")
                text2 += ("{ \"id\": " + str(count2) +
                         ", \"name\": \"" + i +
                         "\", \"country\": \"" + i +
                         "\", \"short_description\": \"" + i +
                         "\", \"ultra_short_description\": \"" + i + "\" }," +'\n')
                count2 += 1
        text = ("export default {scenarioCombinations : {" +
                "scenarioOptions : [" + '\n' +
                text1[:-2] + '\n' +
                "]," + '\n' +
                "regionOptions : [" + '\n' +
                text2[:-2] + '\n' +
                "]}}")
        file.write(text)


    # populate for missing periods
    res = pd.merge(df1, df2, on='total')
    res = pd.merge(df3, res, on='total')
    data = data.append(res, ignore_index=True, sort=True)


    # check if regions exist, else remove from the category list
    cats = ['scenario',
            'indicator',
            'region',
            'indicatorGroup',
            'year']
    if not include_regions: cats.remove('region')


    # group by categories and sum the total
    data = data.groupby(cats)['total'].sum().reset_index()


    if 'line' in idf_n:
        l = data.copy()
        l.indicator.replace(dict_l2b, inplace=True)
    else:
        s = data


    # data for line plot
    #lines = l2b.index.tolist()
    #l = data[data.indicator.str.contains('|'.join(lines))]
    #l = data[data.indicatorGroup=='CO2 budget']


    # data for stacked barplot
    #s = data.copy()
    #s.indicator.replace(dict_l2b, inplace=True)
    # s = data[data.indicatorGroup!='CO2 budget']


    # function to convert the dataframe to json and saves it to output
    def create_json(df, name):
        """
        Creates customized json file from a pandas dataframe and saves it with the
        selected naming.
        """

        d = df.reset_index()

        d = d.groupby(cats[:-1]).apply(lambda x: x[['year',
                                            'total']]\
                                       .to_dict('r'))\
                                       .reset_index()\
                                       .rename(columns={0:'indicatorGroupValues'})

        d = d.groupby(cats[:-2]).apply(lambda x: x[['indicatorGroup',
                                            'indicatorGroupValues']]\
                                       .to_dict('r'))\
                                       .reset_index()\
                                       .rename(columns={0:'indicatorGroups'})

        if include_regions:
            d = d.groupby(cats[:-3]).apply(lambda x: x[['region',
                                                'indicatorGroups']]\
                                           .to_dict('r'))\
                                           .reset_index()\
                                           .rename(columns={0:'regions'})

            d = d.groupby(cats[:-4]).apply(lambda x: x[['indicator',
                                                'regions']]\
                                            .to_dict('r'))\
                                            .reset_index()\
                                            .rename(columns={0:'indicators'})

        else:
            d = d.groupby(cats[:-3]).apply(lambda x: x[['indicator',
                                                'indicatorGroups']]\
                                           .to_dict('r'))\
                                           .reset_index()\
                                           .rename(columns={0:'indicators'})

        d['scenarios'] = 'scenarios'
        d = d.groupby(['scenarios']).apply(lambda x: x[['scenario',
                                            'indicators']]\
                                           .to_dict('r'))\
                                           .reset_index()\
                                           .rename(columns={0:'data'})
        d = d.set_index('scenarios')


        with open('output/' + name + '.js', 'w+', encoding=enc) as file:
            d.to_json(file, force_ascii=False)


        if messy:
            js_str = open('output/' + name + '.js', 'r', encoding=enc).read()
            open('output/' + name + '.js', 'w', encoding=enc)\
            .write('export default ' + js_str)
        else:
            js_str = open('output/' + name + '.js', 'r', encoding=enc).read()
            with open('output/' + name + '.js', 'w', encoding=enc) as file:
                js_str = json.dumps(json.loads(js_str), indent=2)
                file.write('export default ' + js_str)


    # create stacked barplot json and save it
    if 's' in locals():
        name = 'stackedBar' + idf_n
        create_json(s, name)


    # create stacked barplot json and save it
    if 'l' in locals():
        name = 'line' + idf_n
        create_json(l, name)


# run script for each input data file
for file_path in path_list:
    run_script(file_path)


# end
# -----------------------------------------------------------------------------