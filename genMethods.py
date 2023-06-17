import os
import glob
from lxml import etree as ET
import csv
import javalang

def removeSrcmlTags(srcmlOpt):
    tree = ET.fromstring(srcmlOpt)
    text_nodes = tree.xpath("//text()")
    source_code = "".join(text for text in text_nodes)
    return source_code

def extract_method_srcml(file_path, method_name):
    srcml_output = os.path.splitext(file_path)[0] + ".xml"
    os.system(f"srcml {file_path} -o {srcml_output}")    
    with open(srcml_output, "rb") as file:
        srcml_output = file.read()
    tree = ET.fromstring(srcml_output)
    namespace = {'src': 'http://www.srcML.org/srcML/src'}
    method_element = tree.xpath(f'//src:function[src:name="{method_name}"]', namespaces=namespace)[0]
    code_block = ET.tostring(method_element, encoding='unicode', with_tail=False).strip()
    code_block = removeSrcmlTags(code_block)    
    return code_block

def readCSV(input_file):
    with open(input_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        csv_data = [row for row in reader]
    return csv_data

def getMethods(file_name):
    methodNames = []
    try:
        print("Reading file: "+file_name)
        with open(file_name, "r", encoding='utf-8') as file:
            java_code = file.read()
        tree = javalang.parse.parse(java_code)
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            if any(isinstance(annotation, javalang.tree.Annotation) and annotation.name == 'Test' for annotation in node.annotations):
                methodNames.append(node.name)
    except Exception as e:
        message = "Failed to read "+ file_name
        print(message)
        appendFile("log.txt",message)

    return methodNames

def list_java_files(directory):
    path = os.path.join(directory, '**', '*.java')
    java_files = glob.glob(path, recursive=True)
    return java_files

def getFilesList(csv_data):
    newCSV = []
    for row in csv_data:
        gitURL = row[0]
        sha = row[1]
        modulePath = row[2]
        if modulePath.startswith("."):
            modulePath = modulePath[1:]
        projectName = getProjName(gitURL)
        absolutePath =  os.path.join(projectName,modulePath,"src","test","java")
        fileList = list_java_files(absolutePath)
        print(str(absolutePath))
        for file in fileList:
            newCSV.append([projectName,gitURL,sha,modulePath,file])
    return newCSV

def getProjName(url):
    parts = url.split('/')
    project_name = parts[-1].split('.')[0]
    return project_name

def getMethodsList(csv_data):
    newCSV = []
    for row in csv_data:
        filePath = row[4]
        methods = getMethods(filePath)
        if len(methods)!=0:
            methods = ":".join(methods)
            newRow = list(row)
            newRow.append(methods)
            newCSV.append(newRow)
    return newCSV

def createCSV(csv_file,data):
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)

def writeFile(fileName,content):
    with open(fileName, 'w', encoding='utf-8') as f:
        f.write(content)

def appendFile(fileName,content):
    with open(fileName, 'a', encoding='utf-8') as f:
        f.write(content+"\n")

def generateMethodListCSV(csv_data):
    csv_data = [["project_name","git","sha","modulePath","filePath","testMethods"]] + csv_data
    fileName = os.path.join("output","methodList.csv")
    createCSV(fileName,csv_data)

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)  

def generateMethodFiles(csv_data):
    newCSV=[]
    for row in csv_data:
        methods = row[5].split(":")
        filePath = row[4]
        projectName = row[0]
        modulePath = row[3]
        outputDir = os.path.join("output",projectName,modulePath)
        mkdir(outputDir)
        for method in methods:
            print("generating method file for "+ method+" at "+filePath)
            try:
                methodCode = extract_method_srcml(filePath,method)
                testAbsolutePath = filePath.replace("src/test/java/","")
                testAbsolutePath = testAbsolutePath.replace(".java","")
                testAbsolutePath = testAbsolutePath.replace("/","_",1)
                testAbsolutePath = testAbsolutePath.replace("/",".")
                testAbsolutePath = testAbsolutePath + "#" + method + ".txt"
                outputFilePath = os.path.join(outputDir,testAbsolutePath)
                writeFile(outputFilePath,methodCode)
                newRow=[projectName,modulePath,filePath,method,testAbsolutePath]
                newCSV.append(newRow)
            except Exception as e:
                message = "failed to generate method file for "+ method+" at "+filePath
                print(message)
                appendFile("log.txt",message)
    return newCSV
    
def generateFileListCSV(csv_data):
    csv_data = [["project_name","modulePath","filePath","method","methodFileName"]] + csv_data
    fileName = os.path.join("output","fileList.csv")
    createCSV(fileName,csv_data)

if __name__ == "__main__":
    mkdir("output")
    csv_data = readCSV("UniqueProjects.csv")
    filesList = getFilesList(csv_data)
    methodsList = getMethodsList(filesList)
    generateMethodListCSV(methodsList)
    fileNamesList=generateMethodFiles(methodsList)
    generateFileListCSV(fileNamesList)
