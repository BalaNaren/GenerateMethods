import pandas as pd
def write2File(fileName,content):
    with open(fileName, 'a') as f:
        f.write(content+"\n")
def add_suffix(x):
    return str(x) + ".git"
def getProjName(url):
    parts = url.split('/')
    project_name = parts[-1].split('.')[0]
    return project_name
df = pd.read_csv('all-polluter-cleaner-info-combined-filtered-fp.csv', header=None)
df_unique = df.drop_duplicates(subset=[0, 1, 2])
df_unique[0] = df_unique[0].apply(add_suffix)
df_unique = df_unique.iloc[:, :3]
df_uniqueProj = df_unique.drop_duplicates(subset=[0, 1])
for row in df_uniqueProj.iterrows():
    row = row[1]
    gitURL = str(row[0])
    sha = str(row[1])
    projName = getProjName(gitURL)
    write2File("run.bat","git clone "+gitURL);
    write2File("run.bat","cd "+projName);
    write2File("run.bat","git checkout "+sha);
    write2File("run.bat","cd ..");
df_unique.to_csv('UniqueProjects.csv', index=False, header=False)
