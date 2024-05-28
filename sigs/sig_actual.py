import os
import xml.etree.ElementTree as ET
import re
#Doc
from docxtpl import DocxTemplate, InlineImage
from docxcompose.composer import Composer
from docx import Document
from docx.shared import Inches
from unidecode import unidecode

def _combine_all_docx(filePathMaster, filePathsList, finalPath) -> None:
    number_of_sections = len(filePathsList)
    master = Document(filePathMaster)
    composer = Composer(master)
    for i in range(0, number_of_sections):
        doc_temp = Document(filePathsList[i])
        composer.append(doc_temp)

    composer.save(finalPath)

def get_sigs_actual(subareaPath) -> None:

    #Getting list of node codes
    listFiles = os.listdir(subareaPath)
    skeletonFile = [file for file in listFiles if file.endswith(".inpx")][0]
    skeletonPath = os.path.join(subareaPath, skeletonFile)

    tree = ET.parse(skeletonPath)
    network_tag = tree.getroot()

    listCodeNodes = []
    for node_tag in network_tag.findall("./nodes/node"):
        uda_tag = node_tag.find("./uda")
        listCodeNodes.append(uda_tag.attrib['value'])

    #Getting list of .png files
    pngList_by_Code = {}
    for nodeCode in listCodeNodes:
        pngList_by_Code[nodeCode] = []

    pattern = r"([A-Z]+-[0-9]+)"
    actualPath = os.path.join(subareaPath,"Actual")
    for tipicidad in ["Tipico"]:
        tipicidadPath = os.path.join(actualPath, tipicidad)
        scenariosList = os.listdir(tipicidadPath)
        scenariosList = [file for file in scenariosList if not file.endswith(".ini")]
        for scenario in scenariosList:
            scenarioPath = os.path.join(tipicidadPath, scenario)
            scenarioContent = os.listdir(scenarioPath)
            if not scenario in ['HPM','HPT','HPN']: continue
            scenarioContent = [file for file in scenarioContent if file.endswith(".png")]
            for pngFile in scenarioContent:
                if re.search(pattern, pngFile):
                    pngList_by_Code[pngFile[:-4]].append(os.path.join(scenarioPath, pngFile))

    dictCode = {}
    for code, listPathsPNGs in pngList_by_Code.items():
        dictTurns = {}
        for pathPNG in listPathsPNGs:
            pathPNG_parts = pathPNG.split("\\")
            scenarioName = pathPNG_parts[-2]
            if scenarioName == 'HPM': turno = 'Mañana'
            elif scenarioName == 'HPT': turno = 'Tarde'
            elif scenarioName == 'HPN': turno = 'Noche'
            else: print(f"Error: No se encontró ningún escenario de HPM, HPT o HPN: {pathPNG}")
            texto = f"Tiempo de ciclo y fases semafóricas en el Turno {turno} de la intersección {code}"
            pathImage = pathPNG
            dictTurns[turno] = (texto, pathImage)
        dictCode[code] = dictTurns

    #Creating individual images with references
    imagesDirectory = os.path.join(subareaPath, "Imagenes")
    if not os.path.exists(imagesDirectory): os.mkdir(imagesDirectory)

    listWordPaths = []
    for code, dictTurns in dictCode.items():
        for turno in ["Mañana", "Tarde", "Noche"]:
            text, pathImg = dictTurns[turno]
            doc_template = DocxTemplate("./templates/template_tablas.docx")
            newImage = InlineImage(doc_template, pathImg, width=Inches(6))
            doc_template.render({"texto": text, "tabla": newImage})
            turno_text = unidecode(turno)
            finalPath = os.path.join(imagesDirectory, f"{code}_{turno_text}.docx")
            doc_template.save(finalPath) #TODO: <---- Este estaba comentando, parace que este código no esta completo.
            listWordPaths.append(finalPath)
    
    sigactual_path = os.path.join(subareaPath, "Tablas", "SigActual.docx")
    
    filePathMaster = listWordPaths[0]
    filePathList = listWordPaths[1:]

    _combine_all_docx(filePathMaster, filePathList, sigactual_path)

    return sigactual_path