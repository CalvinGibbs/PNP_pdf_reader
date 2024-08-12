from pypdf import PdfReader
from pathlib import Path
import os
import logging
import json
import sys

"""
Just some text to test change for git
"""

log = logging.getLogger("")
log.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

log.addHandler(handler)

class PnpSlipScraper:
    def __init__(self, folder):
        self._folder = folder
        
        self._inputFolder = f"{self._folder}/inputFolder"
        if not Path(self._inputFolder).exists():
            os.mkdir(self._inputFolder)

        self._outputFolder = f"{self._folder}/doneFolder"
        if not Path(self._outputFolder).exists():
            os.mkdir(self._outputFolder)
        
    @property
    def getFolder(self):
        return self._folder
    
    def generateCsv(self, data):
        
        csvFileData = "id,date,payee,amount,notes\n"
        id = 0
        for item in data:
            for x in data[item]:
                if x == "Total":
                    continue
                csvFileData += f"{id},{item.split(' ')[0]},"
                name = data[item][x]["Name"]
                total = data[item][x]["Total"]
                notes = f"Vitality: {data[item][x]['Vitality Health Food Item']} "
                notes += f"Zero Rated: {data[item][x]['Zero-Rated']} "
                notes += f"Cash Off: {data[item][x]['Cash-off']}"
                
                csvFileData += f"{name},{total},{notes}\n"
                id += 1
                
        with open(f"{self._folder}/test.csv", 'w') as f:
            f.write(csvFileData)
        
        
    def scrapeFolder(self):
        all_items = {}
        files = os.listdir(self._folder)

        if len(files) == 0:
            print("Input folder empty or misconfigured")
            sys.exit()
        
        files = [file for file in files if ".pdf" in file]
        
        for i, file in enumerate(files):
            
            fullPath = f"{self._folder}/{file}" 
            
            item = self.scrapeFdfFile(fullPath)
            # will only be one item
            for k, v in item.items():
                all_items[k] = v
                break
            
            os.replace(fullPath, f"{self._outputFolder}/{k}.pdf")
        
        if Path(self._folder, "output.json").exists():
            with open(Path(self._folder, "output.json"), 'r') as f:
                data = json.loads(f.read())
        
        else:
            data = {}
        
        for item in all_items:
            data[item] = all_items[item]
        
        with open(Path(self._folder, "output.json"), 'w') as f:
            f.write(json.dumps(data, indent=4))
        
        #self.generateCsv(data)
        return data
        
        
    def scrapeFdfFile(self, file):
        
        if not Path(file).exists():
            log.info(f"File: {file} does not exist")
            return None
        
        reader = PdfReader(file)

        items = {}
        date = ""
        
        index = 0
        flagFinished = False
        flagNoMoreItems = False
        for p, page in enumerate(reader.pages):
            text = page.extract_text()
            lines = text.split('\n')
            
            if flagFinished:
                break

            for i, line in enumerate(lines):
                if p < 1 and i <= 4:
                   continue
                
                if "DUE VAT INCL" in line:
                    slip_item = [item for item in line.split(' ') if item != '']
                    items['Total'] = float(slip_item[len(slip_item)-1].replace(',', ''))
                    flagNoMoreItems = True
                    
                
                if "@" in line:
                    continue
                
                if "cash-off" in line:
                    continue
                
                if "----------------------------------------" in line:
                    date = lines[i+1].split(' ')
                    date = f"{date[len(date)-2]} {date[len(date)-1].replace(':', '_')}"
                    flagFinished = True

                slip_item = [item for item in line.split(' ') if item != '']
                if not flagNoMoreItems:
                    try:
                        zero_rated = False
                        Vitality = False
                        if "#V" in slip_item[len(slip_item)-1]:
                            zero_rated = True
                            Vitality = True
                            price = float(slip_item[len(slip_item)-1].split("#V")[0])

                        elif "#" in slip_item[len(slip_item)-1]:
                            price = float(slip_item[len(slip_item)-1].split('#')[0])
                            zero_rated = True

                        elif "V" in slip_item[len(slip_item)-1]:
                            price = float(slip_item[len(slip_item)-1].split('V')[0])
                            Vitality = True

                        else:
                            if '@' in lines[i+1]:
                                raise Exception("Price on next line")
                            price = float(slip_item[len(slip_item)-1])


                        if "cash-off" in lines[i+1]:
                            cash_off = [item for item in lines[i+1].split(' ') if item != '']
                            cash_off = abs(float(cash_off[len(cash_off)-1]))
                        else:
                            cash_off = 0
                        
                        name = " ".join(item for x, item in enumerate(slip_item) if x!=len(slip_item)-1)
                        
                        quantity = 1
                        total = price
                            
                    except Exception:

                        # Price on next line
                        name = " ".join(item for item in slip_item)
                        next_line = [item for item in lines[i+1].split(' ') if item != '']
                        
                        zero_rated = False
                        Vitality = False
                        if "#V" in next_line[3]:
                            zero_rated = True
                            Vitality = True
                            total = float(next_line[3].split("#V")[0])
                            
                        elif "#" in next_line[3]:
                            total = float(next_line[3].split('#')[0])
                            zero_rated = True
                            
                        elif "V" in next_line[3]:
                            total = float(next_line[3].split('V')[0])
                            Vitality = True
                            
                        else:
                            total = float(next_line[3])
                        
                        quantity = float(next_line[0])
                        price = float(next_line[2])
                        
                        
                        if "cash-off" in lines[i+2]:
                            cash_off = [item for item in lines[i+2].split(' ') if item != '']
                            cash_off = abs(float(cash_off[len(cash_off)-1]))
                        else:
                            cash_off = 0
                        
                    

                    items[index] = {
                        "Name": name,
                        "Quantity": quantity,
                        "Price": price,
                        "Total": total,
                        "Cash-off": cash_off,
                        "Zero-Rated": zero_rated,
                        "Vitality Health Food Item": Vitality
                    }
                    index += 1
                    
                    
            
        return {date: items}
    
def main():
    cwd = os.getcwd()
    with open(f"{cwd}/config.json", 'r') as f:
        config = json.loads(f.read())
    
    scraper = PnpSlipScraper(config['folder'])
    
    help = """
    q: Quit application
    sf: Srape Input folder
    csv: Generate csv file
    gf: Get folder location
    h: Print Help
    """
    
    items = None
    log.info(help)
    while True:
        inpt = input("Enter command: ")
        if inpt == 'q':
            break
        elif inpt == 'h':
            log.info(help)
        elif inpt == 'sf':
            items = scraper.scrapeFolder()
            log.info("Done scraping\n")
        elif inpt == 'csv':
            if items == None:
                log.warning("You have not gotten any data yet. Please use command [sf] to scrape the folder\n")
                continue
            scraper.generateCsv(items)
            log.info("Done generating csv\n")
        elif inpt == 'gf':
            log.info(f"Folder: '{scraper.getFolder}'\n")
        
    log.info("Exiting...")
    
    
if __name__ == "__main__":
    main()