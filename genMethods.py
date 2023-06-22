import os
import glob
from lxml import etree as ET
import csv
import javalang
import json
import random

def removeSrcmlTags(srcmlOpt):
    tree = ET.fromstring(srcmlOpt)
    text_nodes = tree.xpath("//text()")
    source_code = "".join(text for text in text_nodes)
    return source_code

def extract_method_srcml_inheritance(file_path, class_name, method_name):
    srcml_output = os.path.splitext(file_path)[0] + ".xml"
    os.system(f"srcml {file_path} -o {srcml_output}")    
    with open(srcml_output, "rb") as file:
        srcml_output = file.read()
    tree = ET.fromstring(srcml_output)
    namespace = {'src': 'http://www.srcML.org/srcML/src'}

    class_elements = tree.xpath(f'//src:class[src:name="{class_name}"]', namespaces=namespace)
    if not class_elements:
        print(f"No class named '{class_name}' found.")
        return None
    class_element = class_elements[0]

    # Try to find the method in the class
    method_elements = class_element.xpath(f'.//src:function[src:name="{method_name}"]', namespaces=namespace)
    if method_elements:
        code_block = ET.tostring(method_elements[0], encoding='unicode', with_tail=False).strip()
        code_block = removeSrcmlTags(code_block)
        return code_block

    # If the method is not found, check if the class extends from another class
    extends_elements = class_element.xpath('.//src:super_list/src:extends', namespaces=namespace)
    if extends_elements:
        # If the class does extend from another class, attempt to find the method in the parent class
        parent_class_name = extends_elements[0].xpath('.//src:name', namespaces=namespace)[0].text
        return extract_method_srcml_inheritance(file_path, parent_class_name, method_name)
    else:
        # If the class does not extend from another class, return a message indicating that the method was not found
        print(f"Method '{method_name}' not found in class '{class_name}' or any parent classes.")
        return None

def extract_method_srcml_no_inheritance(file_path, method_name):
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
        with open(file_name, "r", encoding='utf-8', errors='ignore') as file:
            java_code = file.read()
        tree = javalang.parse.parse(java_code)
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            if any(isinstance(annotation, javalang.tree.Annotation) and annotation.name == 'Test' for annotation in node.annotations) and 'abstract' not in node.modifiers:
                methodNames.append(node.name)
    except Exception as e:
        message = "Failed to read "+ file_name +"\n"+str(e)
        print(message)
        appendFile("output/log.txt",message)
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
        if modulePath.startswith("/"):
            modulePath = modulePath[1:]
        projectName = getProjName(gitURL)
        if modulePath == "":
            absolutePath = projectName+"/src/test/java"
        else:
            absolutePath = projectName+"/"+modulePath+"/src/test/java"
        fileList = list_java_files(absolutePath)
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
                methodCode = extract_method_srcml_no_inheritance(filePath,method)
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
                message = "failed to generate method file for "+ method+" at "+filePath +"\n"+str(e)
                print(message)
                appendFile("output/log.txt",message)
    return newCSV
    
def generateFileListCSV(csv_data):
    csv_data = [["project_name","modulePath","filePath","method","methodFileName"]] + csv_data
    fileName = os.path.join("output","fileList.csv")
    createCSV(fileName,csv_data)

def populateData(data,projectName,module,mPath,isArray=True):
    projects = data.keys()
    if projectName not in projects:
        if isArray:
            data[projectName]={module:[mPath]}
        else:
            data[projectName]={module:mPath}
        return data
    modules = data[projectName]
    if module not in modules.keys():
        if isArray:
            data[projectName][module]=[mPath]
        else:
            data[projectName][module]=mPath
        return data
    if isArray:
        data[projectName][module].append(mPath)
    else:
        data[projectName][module]=mPath
    return data

def generate_random_lists(input_list,start=5,end=1000,step=5):
    output = {}
    for i in range(start, min(len(input_list), end+1), step):
        output[i] = random.sample(input_list, k=i)    
    return output

def getMethodList4RandOrder(csv_data):
    data = {}
    for row in csv_data:
        projectName = getProjName(row[0])
        module = row[3]
        filePath = row[4]
        methods = row[5].split(":")
        filePath = filePath.replace(projectName+"/"+module+"/src/test/java/","")
        filePath = filePath.replace(".java","")
        filePath = filePath.replace("/",".")
        for method in methods:
            mPath = filePath+"."+method
            data = populateData(data,projectName,module,mPath)
    return data

def generateRandomOrder(rand_data):
    data={}
    for proj in rand_data.keys():
        modules=rand_data[proj]
        for mod in modules.keys():
            mList = rand_data[proj][mod]
            randomLists = generate_random_lists(mList)
            data=populateData(data,proj,mod,randomLists,False)
    return data

def writeRandomOrders(data):
    writeFile("output/randomOrders.txt",json.dumps(data,indent=4))

def readFile(fileName):
    with open(fileName, 'r') as file:
        contents = file.read()
    return contents


def generateFilePath(projectName,modulePath,method):
    if method == "":
        return ""
    if modulePath != "":
        filePath = projectName+"/"+modulePath+"/src/test/java"
    else:
        filePath = projectName+"/src/test/java"
    fileName = method[:method.rfind(".")]
    className = fileName[fileName.rfind(".")+1:]
    fileName = fileName.replace(".","/")
    fileName = fileName+".java"
    filePath=filePath+"/"+fileName
    methodName = method[method.rfind(".")+1:]
    code = extract_method_srcml_inheritance(filePath,className,methodName)
    #code = extract_method_srcml_no_inheritance(filePath,methodName)
    return "\""+code+"\""


def generateMethodCodes4OrgCsv(fileName):
    data = []
    org_csv = readCSV(fileName)
    for row in org_csv:
        gitURL = row[0]+".git"
        projName = getProjName(gitURL)
        sha=row[1]
        module=row[2]
        if module.startswith("."):
            module=module[1:]
        if module.startswith("/"):
            module=module[1:]
        victim=row[3]
        polluter=row[4]
        cleaner=row[5]
        type=row[6]
        print("processing original csv: "+ ",".join(row))
        try:
            vMethod = generateFilePath(projName,module,victim)
            pMethod = generateFilePath(projName,module,polluter)
            cMethod = generateFilePath(projName,module,cleaner)
            data.append([gitURL,sha,module,victim,polluter,cleaner,type,vMethod,pMethod,cMethod])
        except Exception as e:
            message = "Failed to generate:" +",".join(row)+"\n"+str(e)
            print(message)
            print(e)
            appendFile("output/log_processOrgCSV.txt",message)
            appendFile("output/failedOrgCSV.csv",",".join(row))
    return data

def generateProcessedOrgCsv(csv_data):
    csv_data = [["gitURL","sha","module","victim","polluter","cleaner","type","victim_code","polluter_code","cleaner_code"]] + csv_data
    fileName = os.path.join("output","processedOrgCsv.csv")
    createCSV(fileName,csv_data)

if __name__ == "__main__":
    mkdir("output")
    csv_data = readCSV("UniqueProjects.csv")
    filesList = getFilesList(csv_data)
    methodsList = getMethodsList(filesList)
    methodList4RandOrder= getMethodList4RandOrder(methodsList)
    randomOrder = generateRandomOrder(methodList4RandOrder)
    writeRandomOrders(randomOrder)    
    generateMethodListCSV(methodsList)
    fileNamesList=generateMethodFiles(methodsList)
    generateFileListCSV(fileNamesList)
    processedOrgCsv = generateMethodCodes4OrgCsv("all-polluter-cleaner-info-combined-filtered-fp.csv")
    #processedOrgCsv = generateMethodCodes4OrgCsv("failedOrgCSV.csv")
    generateProcessedOrgCsv(processedOrgCsv)
