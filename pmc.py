import json
import ssl
import requests

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context
search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc" \
             "&term=%28Jost%2C+Stephanie%5BAuthor%5D%29+OR+%28Reeves%2C+R+Keith%5BAuthor%5D%29&retmode=json&retmax=500" \
             "&tool=reevestool&email=kylekroll@outlook.com"
pmc_ids = requests.get(search_url)
pmc_ids = pmc_ids.json()

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&retmode=json&tool=my_tool&email=my_email@example.com&id="
detailed_url = f"{url}{','.join(pmc_ids['esearchresult']['idlist'])}"
details = requests.get(detailed_url).json()
for id in details['result']['uids']:
    #authors = details['result'][id]['authors']
    #authors = [x['name'].replace(" ",", ") for x in details['result'][id]['authors']]
    #print(authors)
    #print(details['result'][id]['title'])
    for item in details['result'][id]['articleids']:
        if item['idtype'] == 'doi':
            print(item['value'])
#print(json.dumps(details, indent=4))